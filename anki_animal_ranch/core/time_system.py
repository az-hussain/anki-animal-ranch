"""
Time System - Converts study activity to game time.

This module manages the game's time system, which is driven by
the user's Anki study activity. Each card answered advances
game time by 1 minute, which in turn drives animal growth, 
production, and other time-based game mechanics.

Time is derived purely from total_cards_answered - this is the
single source of truth. No separate time state is stored.
"""

from __future__ import annotations

from ..utils.logger import get_logger
from dataclasses import dataclass
from typing import TYPE_CHECKING

from .constants import (
    DAYS_PER_SEASON,
    HOURS_PER_DAY,
    MINUTES_PER_HOUR,
    MINUTES_PER_CARD,
    SEASONS_PER_YEAR,
    SEASON_ORDER,
    Events,
    Season,
)
from .event_bus import event_bus

if TYPE_CHECKING:
    pass

logger = get_logger(__name__)

# Starting time offset: 6 AM on Day 1 = 6 hours = 360 minutes
STARTING_OFFSET_MINUTES = 6 * MINUTES_PER_HOUR


@dataclass
class FarmTime:
    """
    Represents a point in time on the farm.
    
    Time is structured as:
    - Year (1+)
    - Season (Spring, Summer, Fall, Winter)
    - Day (1-7 within each season)
    - Hour (0-23)
    - Minute (0-59)
    """
    year: int = 1
    season: Season = Season.SPRING
    day: int = 1
    hour: int = 6  # Start at 6 AM
    minute: int = 0
    
    @classmethod
    def from_total_minutes(cls, total_minutes: int) -> FarmTime:
        """
        Create a FarmTime from total minutes since game start.
        
        This is the primary way to create FarmTime - derived from card count.
        
        Args:
            total_minutes: Total minutes (cards answered + starting offset)
            
        Returns:
            FarmTime representing that point in time
        """
        minute = total_minutes % MINUTES_PER_HOUR
        total_hours = total_minutes // MINUTES_PER_HOUR
        
        hour = total_hours % HOURS_PER_DAY
        total_days = total_hours // HOURS_PER_DAY
        
        # Days are 1-indexed, so day 0 = day 1
        day = (total_days % DAYS_PER_SEASON) + 1
        total_seasons = total_days // DAYS_PER_SEASON
        
        season_index = total_seasons % SEASONS_PER_YEAR
        season = SEASON_ORDER[season_index]
        
        # Years are 1-indexed
        year = (total_seasons // SEASONS_PER_YEAR) + 1
        
        return cls(
            year=year,
            season=season,
            day=day,
            hour=hour,
            minute=minute,
        )
    
    @property
    def total_minutes(self) -> int:
        """Get total minutes since game start (Year 1, Spring, Day 1, 00:00)."""
        season_index = SEASON_ORDER.index(self.season)
        
        total_days = (
            (self.year - 1) * SEASONS_PER_YEAR * DAYS_PER_SEASON +
            season_index * DAYS_PER_SEASON +
            (self.day - 1)
        )
        
        return (
            total_days * HOURS_PER_DAY * MINUTES_PER_HOUR +
            self.hour * MINUTES_PER_HOUR +
            self.minute
        )
    
    @property
    def total_hours(self) -> float:
        """Get total hours since game start."""
        return self.total_minutes / MINUTES_PER_HOUR
    
    @property
    def time_of_day(self) -> str:
        """Get a human-readable time of day."""
        if 5 <= self.hour < 12:
            return "morning"
        elif 12 <= self.hour < 17:
            return "afternoon"
        elif 17 <= self.hour < 21:
            return "evening"
        else:
            return "night"
    
    @property
    def is_daytime(self) -> bool:
        """Check if it's daytime (6 AM - 8 PM)."""
        return 6 <= self.hour < 20
    
    def format_time(self) -> str:
        """Format as HH:MM."""
        return f"{self.hour:02d}:{self.minute:02d}"
    
    def format_date(self) -> str:
        """Format as Season Day N, Year Y."""
        return f"{self.season.value.capitalize()} Day {self.day}, Year {self.year}"
    
    def format_full(self) -> str:
        """Format full date and time."""
        return f"{self.format_date()} {self.format_time()}"
    
    def copy(self) -> FarmTime:
        """Create a copy of this time."""
        return FarmTime(
            year=self.year,
            season=self.season,
            day=self.day,
            hour=self.hour,
            minute=self.minute,
        )
    
    def __str__(self) -> str:
        return self.format_full()
    
    def __repr__(self) -> str:
        return f"FarmTime({self.year}, {self.season.value}, {self.day}, {self.hour}, {self.minute})"
    
    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "year": self.year,
            "season": self.season.value,
            "day": self.day,
            "hour": self.hour,
            "minute": self.minute,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> FarmTime:
        """Deserialize from dictionary."""
        return cls(
            year=data["year"],
            season=Season(data["season"]),
            day=data["day"],
            hour=data["hour"],
            minute=data["minute"],
        )


class TimeSystem:
    """
    Manages game time derived from study activity.
    
    Time is calculated purely from total_cards_answered - this is
    the single source of truth. Each card = 1 minute of game time.
    
    60 cards = 1 hour of game time.
    1440 cards = 1 day (24 hours).
    10080 cards = 1 season (7 days).
    40320 cards = 1 year (4 seasons).
    """
    
    def __init__(self, total_cards: int = 0):
        """
        Initialize the time system.
        
        Args:
            total_cards: Initial card count (typically from farm.statistics)
        """
        self._total_cards_answered = total_cards
        self._paused = False
        # Cache the last computed time to detect changes for events
        self._last_time = self._compute_time()
    
    def _compute_time(self) -> FarmTime:
        """Compute current time from card count."""
        total_minutes = self._total_cards_answered + STARTING_OFFSET_MINUTES
        return FarmTime.from_total_minutes(total_minutes)
    
    @property
    def current_time(self) -> FarmTime:
        """Get the current farm time (derived from card count)."""
        return self._compute_time()
    
    @property
    def total_cards_answered(self) -> int:
        """Get total cards answered."""
        return self._total_cards_answered
    
    @property
    def is_paused(self) -> bool:
        """Check if time is paused."""
        return self._paused
    
    def pause(self) -> None:
        """Pause time advancement."""
        self._paused = True
        logger.debug("Time paused")
    
    def resume(self) -> None:
        """Resume time advancement."""
        self._paused = False
        logger.debug("Time resumed")
    
    def on_card_answered(self, ease: int) -> None:
        """
        Handle a card being answered.
        
        Every card advances time by 1 minute regardless of answer.
        
        Args:
            ease: The ease button pressed (1=Again, 2=Hard, 3=Good, 4=Easy)
        """
        if self._paused:
            return
        
        # Advance by 1 card = 1 minute
        self.advance_time(minutes=MINUTES_PER_CARD)
        
        # Publish card answered event
        event_bus.publish(
            Events.CARD_ANSWERED,
            ease=ease,
            minutes_advanced=MINUTES_PER_CARD,
            total_cards=self._total_cards_answered,
        )
    
    def advance_time(self, minutes: int = 0, hours: int = 0, days: int = 0) -> None:
        """
        Advance game time by the specified amount.
        
        Internally this increments the card count by the equivalent
        number of minutes.
        
        Args:
            minutes: Minutes to advance
            hours: Hours to advance
            days: Days to advance
        """
        if self._paused:
            return
        
        # Convert all to minutes (which equals cards)
        total_minutes = minutes + (hours * MINUTES_PER_HOUR) + (days * HOURS_PER_DAY * MINUTES_PER_HOUR)
        
        if total_minutes <= 0:
            return
        
        old_time = self._last_time.copy()
        
        # Increment card count
        self._total_cards_answered += total_minutes
        
        # Compute new time
        new_time = self._compute_time()
        self._last_time = new_time
        
        # Publish time advanced event
        event_bus.publish(
            Events.TIME_ADVANCED,
            old_time=old_time,
            new_time=new_time.copy(),
            minutes_advanced=total_minutes,
        )
        
        # Check for significant time changes and publish specific events
        if old_time.hour != new_time.hour:
            event_bus.publish(
                Events.HOUR_CHANGED,
                old_hour=old_time.hour,
                new_hour=new_time.hour,
                time=new_time.copy(),
            )
        
        if old_time.day != new_time.day or old_time.season != new_time.season:
            event_bus.publish(
                Events.DAY_CHANGED,
                old_day=old_time.day,
                new_day=new_time.day,
                season=new_time.season,
                time=new_time.copy(),
            )
        
        if old_time.season != new_time.season:
            event_bus.publish(
                Events.SEASON_CHANGED,
                old_season=old_time.season,
                new_season=new_time.season,
                year=new_time.year,
                time=new_time.copy(),
            )
        
        logger.debug(f"Time advanced: {old_time} -> {new_time}")
    
    def set_total_cards(self, count: int) -> None:
        """
        Set the total cards count directly (used for loading saves).
        
        Args:
            count: The card count to set
        """
        self._total_cards_answered = count
        self._last_time = self._compute_time()
        logger.info(f"Time set from {count} cards: {self._last_time}")
    
    def reset(self) -> None:
        """Reset to initial time (0 cards)."""
        self._total_cards_answered = 0
        self._last_time = self._compute_time()
        logger.info("Time system reset")
    
    # Legacy methods for backwards compatibility during transition
    def to_dict(self) -> dict:
        """Serialize the time system state (legacy, for backwards compat)."""
        return {
            "total_cards_answered": self._total_cards_answered,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> TimeSystem:
        """Deserialize time system state (legacy, for backwards compat)."""
        total_cards = data.get("total_cards_answered", 0)
        return cls(total_cards=total_cards)
