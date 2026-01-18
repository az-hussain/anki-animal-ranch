"""
Event Bus - Publish/Subscribe event system.

This module provides a centralized event system for decoupled communication
between game components. Components can publish events without knowing who
will receive them, and subscribe to events without knowing who sends them.

Usage:
    from anki_animal_ranch.core import event_bus, Events
    
    # Subscribe to an event
    def on_animal_sold(animal, price):
        print(f"Sold {animal.name} for {price}!")
    
    event_bus.subscribe(Events.ANIMAL_SOLD, on_animal_sold)
    
    # Publish an event
    event_bus.publish(Events.ANIMAL_SOLD, animal=chicken, price=100)
    
    # Unsubscribe
    event_bus.unsubscribe(Events.ANIMAL_SOLD, on_animal_sold)
"""

from __future__ import annotations

from ..utils.logger import get_logger
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Callable
from weakref import WeakMethod, ref

logger = get_logger(__name__)


# Type alias for event handlers
EventHandler = Callable[..., None]


@dataclass
class Subscription:
    """
    Represents a subscription to an event.
    
    Uses weak references to prevent memory leaks when subscribers
    are deleted without explicitly unsubscribing.
    """
    handler: EventHandler | WeakMethod | ref
    is_weak: bool = False
    priority: int = 0  # Higher priority handlers called first
    once: bool = False  # If True, automatically unsubscribe after first call
    
    def get_handler(self) -> EventHandler | None:
        """Get the actual handler, or None if the weak reference is dead."""
        if self.is_weak:
            handler = self.handler()
            return handler
        return self.handler
    
    def is_alive(self) -> bool:
        """Check if the subscription is still valid."""
        if self.is_weak:
            return self.handler() is not None
        return True


class EventBus:
    """
    Central event bus for publish/subscribe communication.
    
    Thread-safe and supports:
    - Regular and weak reference subscriptions
    - Priority ordering for handlers
    - One-shot subscriptions
    - Event history for debugging
    """
    
    def __init__(self, keep_history: bool = False, max_history: int = 100):
        """
        Initialize the event bus.
        
        Args:
            keep_history: If True, keep a history of published events
            max_history: Maximum number of events to keep in history
        """
        self._subscribers: dict[str, list[Subscription]] = defaultdict(list)
        self._keep_history = keep_history
        self._max_history = max_history
        self._history: list[tuple[str, dict[str, Any]]] = []
        self._paused = False
        self._queued_events: list[tuple[str, dict[str, Any]]] = []
    
    def subscribe(
        self,
        event: str,
        handler: EventHandler,
        *,
        weak: bool = False,
        priority: int = 0,
        once: bool = False,
    ) -> None:
        """
        Subscribe to an event.
        
        Args:
            event: The event name to subscribe to
            handler: The callback function to call when the event is published
            weak: If True, use a weak reference (handler won't prevent GC)
            priority: Higher priority handlers are called first
            once: If True, automatically unsubscribe after first call
        """
        if weak:
            # Use WeakMethod for bound methods, ref for functions
            if hasattr(handler, "__self__"):
                handler_ref = WeakMethod(handler)
            else:
                handler_ref = ref(handler)
            subscription = Subscription(handler_ref, is_weak=True, priority=priority, once=once)
        else:
            subscription = Subscription(handler, is_weak=False, priority=priority, once=once)
        
        self._subscribers[event].append(subscription)
        # Sort by priority (descending)
        self._subscribers[event].sort(key=lambda s: s.priority, reverse=True)
        
        logger.debug(f"Subscribed to '{event}': {handler.__name__}")
    
    def unsubscribe(self, event: str, handler: EventHandler) -> bool:
        """
        Unsubscribe from an event.
        
        Args:
            event: The event name to unsubscribe from
            handler: The handler to remove
            
        Returns:
            True if the handler was found and removed, False otherwise
        """
        if event not in self._subscribers:
            return False
        
        original_count = len(self._subscribers[event])
        self._subscribers[event] = [
            sub for sub in self._subscribers[event]
            if sub.get_handler() != handler
        ]
        
        removed = len(self._subscribers[event]) < original_count
        if removed:
            logger.debug(f"Unsubscribed from '{event}': {handler.__name__}")
        
        return removed
    
    def publish(self, event: str, **kwargs: Any) -> int:
        """
        Publish an event to all subscribers.
        
        Args:
            event: The event name to publish
            **kwargs: Data to pass to handlers
            
        Returns:
            Number of handlers that were called
        """
        if self._paused:
            self._queued_events.append((event, kwargs))
            return 0
        
        # Record in history
        if self._keep_history:
            self._history.append((event, kwargs))
            if len(self._history) > self._max_history:
                self._history.pop(0)
        
        if event not in self._subscribers:
            return 0
        
        # Clean up dead weak references
        self._subscribers[event] = [
            sub for sub in self._subscribers[event]
            if sub.is_alive()
        ]
        
        handlers_called = 0
        to_remove: list[Subscription] = []
        
        for subscription in self._subscribers[event]:
            handler = subscription.get_handler()
            if handler is None:
                continue
            
            try:
                handler(**kwargs)
                handlers_called += 1
                
                if subscription.once:
                    to_remove.append(subscription)
                    
            except Exception as e:
                logger.error(f"Error in handler for '{event}': {e}", exc_info=True)
        
        # Remove one-shot subscriptions
        for sub in to_remove:
            self._subscribers[event].remove(sub)
        
        logger.debug(f"Published '{event}' to {handlers_called} handlers")
        return handlers_called
    
    def publish_sync(self, event: str, **kwargs: Any) -> list[Any]:
        """
        Publish an event and collect return values from handlers.
        
        Unlike regular publish, this collects and returns handler results.
        Useful for events that need to aggregate responses.
        
        Args:
            event: The event name to publish
            **kwargs: Data to pass to handlers
            
        Returns:
            List of return values from handlers (excluding None)
        """
        if event not in self._subscribers:
            return []
        
        results = []
        for subscription in self._subscribers[event]:
            handler = subscription.get_handler()
            if handler is None:
                continue
            
            try:
                result = handler(**kwargs)
                if result is not None:
                    results.append(result)
            except Exception as e:
                logger.error(f"Error in handler for '{event}': {e}", exc_info=True)
        
        return results
    
    def has_subscribers(self, event: str) -> bool:
        """Check if an event has any subscribers."""
        return event in self._subscribers and len(self._subscribers[event]) > 0
    
    def subscriber_count(self, event: str) -> int:
        """Get the number of subscribers for an event."""
        return len(self._subscribers.get(event, []))
    
    def pause(self) -> None:
        """
        Pause event publishing.
        
        Events published while paused are queued and will be
        published when resume() is called.
        """
        self._paused = True
        logger.debug("Event bus paused")
    
    def resume(self) -> None:
        """
        Resume event publishing and publish any queued events.
        """
        self._paused = False
        
        # Publish queued events
        queued = self._queued_events.copy()
        self._queued_events.clear()
        
        for event, kwargs in queued:
            self.publish(event, **kwargs)
        
        logger.debug(f"Event bus resumed, published {len(queued)} queued events")
    
    def clear(self, event: str | None = None) -> None:
        """
        Clear subscribers.
        
        Args:
            event: If provided, clear only subscribers for this event.
                   If None, clear all subscribers.
        """
        if event is None:
            self._subscribers.clear()
            logger.debug("Cleared all event subscribers")
        else:
            self._subscribers[event].clear()
            logger.debug(f"Cleared subscribers for '{event}'")
    
    def get_history(self) -> list[tuple[str, dict[str, Any]]]:
        """Get the event history (if history keeping is enabled)."""
        return self._history.copy()
    
    def clear_history(self) -> None:
        """Clear the event history."""
        self._history.clear()


# Global event bus instance
event_bus = EventBus(keep_history=False)
