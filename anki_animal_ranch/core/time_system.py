"""
Time System - Converts study activity to game time.

This module manages the game's time system, which is driven by
the user's Anki study activity. Each card answered advances
game time by 1 minute, which in turn drives animal growth, 
production, and other time-based game mechanics.
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
    
    def __post_init__(self) -> None:
        """Validate time values."""
        self._normalize()
    
    def _normalize(self) -> None:
        """Normalize time values (handle overflow)."""
        # Normalize minutes to hours
        while self.minute >= MINUTES_PER_HOUR:
            self.minute -= MINUTES_PER_HOUR
            self.hour += 1
        while self.minute < 0:
            self.minute += MINUTES_PER_HOUR
            self.hour -= 1
        
        # Normalize hours to days
        while self.hour >= HOURS_PER_DAY:
            self.hour -= HOURS_PER_DAY
            self.day += 1
        while self.hour < 0:
            self.hour += HOURS_PER_DAY
            self.day -= 1
        
        # Normalize days to seasons
        while self.day > DAYS_PER_SEASON:
            self.day -= DAYS_PER_SEASON
            self._advance_season()
        while self.day < 1:
            self.day += DAYS_PER_SEASON
            self._retreat_season()
    
    def _advance_season(self) -> None:
        """Move to the next season."""
        current_index = SEASON_ORDER.index(self.season)
        next_index = (current_index + 1) % len(SEASON_ORDER)
        self.season = SEASON_ORDER[next_index]
        
        # If we wrapped around, increment year
        if next_index == 0:
            self.year += 1
    
    def _retreat_season(self) -> None:
        """Move to the previous season."""
        current_index = SEASON_ORDER.index(self.season)
        prev_index = (current_index - 1) % len(SEASON_ORDER)
        self.season = SEASON_ORDER[prev_index]
        
        # If we wrapped around, decrement year
        if prev_index == len(SEASON_ORDER) - 1:
            self.year = max(1, self.year - 1)
    
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
    Manages game time and its relationship to study activity.
    
    Each card answered advances game time by 1 minute.
    60 cards = 1 hour of game time.
    """
    
    def __init__(self):
        """Initialize the time system."""
        self._current_time = FarmTime()
        self._total_cards_answered = 0
        self._paused = False
    
    @property
    def current_time(self) -> FarmTime:
        """Get the current farm time (read-only copy)."""
        return self._current_time.copy()
    
    @property
    def total_cards_answered(self) -> int:
        """Get total cards answered this session."""
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
        
        self._total_cards_answered += 1
        
        # Every card advances time by MINUTES_PER_CARD (1 minute)
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
        
        Args:
            minutes: Minutes to advance
            hours: Hours to advance
            days: Days to advance
        """
        if self._paused:
            return
        
        old_time = self._current_time.copy()
        
        # Convert all to minutes
        total_minutes = minutes + (hours * MINUTES_PER_HOUR) + (days * HOURS_PER_DAY * MINUTES_PER_HOUR)
        
        if total_minutes <= 0:
            return
        
        # Apply the time change
        self._current_time.minute += total_minutes
        self._current_time._normalize()
        
        new_time = self._current_time
        
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
    
    def set_time(self, time: FarmTime) -> None:
        """
        Set the current time directly (used for loading saves).
        
        Args:
            time: The time to set
        """
        self._current_time = time.copy()
        logger.info(f"Time set to {self._current_time}")
    
    def reset(self) -> None:
        """Reset to initial time."""
        self._current_time = FarmTime()
        self._total_cards_answered = 0
        logger.info("Time system reset")
    
    def to_dict(self) -> dict:
        """Serialize the time system state."""
        return {
            "current_time": self._current_time.to_dict(),
            "total_cards_answered": self._total_cards_answered,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> TimeSystem:
        """Deserialize time system state."""
        system = cls()
        system._current_time = FarmTime.from_dict(data["current_time"])
        system._total_cards_answered = data.get("total_cards_answered", 0)
        return system
