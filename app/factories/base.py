"""Abstract slot factory – Factory Method pattern.

All concrete slot factories must subclass ``SlotFactory`` and implement
``generate_slots``.  This keeps the calling service decoupled from the
specific algorithm used to carve up a doctor's availability window.
"""
from __future__ import annotations

import datetime
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Tuple


@dataclass
class DynamicSlot:
    """A single time-slot generated on-the-fly (never stored in the DB).

    Attributes:
        start_time:   UTC-aware slot start.
        end_time:     UTC-aware slot end.
        is_available: False when the window overlaps an existing booking.
    """

    start_time: datetime.datetime
    end_time: datetime.datetime
    is_available: bool = field(default=True)

    @property
    def duration_minutes(self) -> int:
        """Convenience: total minutes in this slot."""
        return int((self.end_time - self.start_time).total_seconds() / 60)


class SlotFactory(ABC):
    """Abstract Factory – *Factory Method* pattern entry-point.

    Concrete sub-classes decide *how* to partition the availability window into
    individual ``DynamicSlot`` objects.  The calling service always talks to
    this interface, so swapping the algorithm requires zero changes outside the
    factory layer.

    Usage::

        factory = FixedIntervalSlotFactory(interval_minutes=30)
        slots   = factory.generate_slots(start, end, booked_windows)
    """

    @abstractmethod
    def generate_slots(
        self,
        start_time: datetime.datetime,
        end_time: datetime.datetime,
        booked_windows: List[Tuple[datetime.datetime, datetime.datetime]],
    ) -> List[DynamicSlot]:
        """Partition [start_time, end_time) into ``DynamicSlot`` objects.

        Args:
            start_time:     Start of the doctor's availability window (UTC).
            end_time:       End   of the doctor's availability window (UTC).
            booked_windows: List of (booked_start, booked_end) tuples for
                            appointments that already exist on this day.

        Returns:
            Ordered list of ``DynamicSlot`` objects covering the whole window.
            Each slot's ``is_available`` flag is ``True`` unless it overlaps a
            booked window.
        """
        ...  # pragma: no cover

    # ── Shared helper ──────────────────────────────────────────────────────────

    @staticmethod
    def _overlaps(
        new_start: datetime.datetime,
        new_end: datetime.datetime,
        booked_windows: List[Tuple[datetime.datetime, datetime.datetime]],
    ) -> bool:
        """Return ``True`` when [new_start, new_end) overlaps any booked window.

        Conflict condition:
            new_start < existing_end  AND  new_end > existing_start
        """
        for b_start, b_end in booked_windows:
            if new_start < b_end and new_end > b_start:
                return True
        return False
