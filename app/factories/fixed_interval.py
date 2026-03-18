"""Concrete slot factory: fixed-interval partitioning.

``FixedIntervalSlotFactory`` slices a doctor's availability window into equal
chunks of ``interval_minutes`` (e.g. 15 or 30 minutes), marking each chunk as
available or unavailable based on the existing booking list.

Multi-slot booking support
--------------------------
Pass ``slots_requested > 1`` to any public helper to request a consecutive
block spanning ``interval_minutes * slots_requested`` minutes.  Example::

    factory = FixedIntervalSlotFactory(interval_minutes=15)
    # Book a 45-minute block (3 consecutive 15-min slots)
    ok = factory.is_block_available(start, existing_appointments, slots_requested=3)
"""
from __future__ import annotations

import datetime
from typing import List, Tuple

from app.factories.base import DynamicSlot, SlotFactory


class FixedIntervalSlotFactory(SlotFactory):
    """Partition a time window into equal-length slots.

    Args:
        interval_minutes: Length of each individual slot in minutes (≥ 1).

    Example::

        factory = FixedIntervalSlotFactory(interval_minutes=30)
        slots = factory.generate_slots(
            start_time=datetime(2026, 3, 20, 9, 0),
            end_time=datetime(2026, 3, 20, 12, 0),
            booked_windows=[(datetime(2026, 3, 20, 10, 0), datetime(2026, 3, 20, 10, 30))],
        )
        # → 6 slots; slot at 10:00 has is_available=False
    """

    def __init__(self, interval_minutes: int = 15) -> None:
        if interval_minutes <= 0:
            raise ValueError("interval_minutes must be a positive integer.")
        self.interval_minutes = interval_minutes

    # ── Factory Method implementation ─────────────────────────────────────────

    def generate_slots(
        self,
        start_time: datetime.datetime,
        end_time: datetime.datetime,
        booked_windows: List[Tuple[datetime.datetime, datetime.datetime]],
    ) -> List[DynamicSlot]:
        """Return all fixed-length slots in [start_time, end_time).

        Slots that overlap a booked window are marked ``is_available=False``
        (they are still returned so the UI can show a full calendar grid).
        """
        if start_time >= end_time:
            return []

        delta = datetime.timedelta(minutes=self.interval_minutes)
        slots: List[DynamicSlot] = []
        current = start_time

        while current + delta <= end_time:
            slot_end = current + delta
            available = not self._overlaps(current, slot_end, booked_windows)
            slots.append(
                DynamicSlot(start_time=current, end_time=slot_end, is_available=available)
            )
            current = slot_end

        return slots

    # ── Multi-slot booking helpers ─────────────────────────────────────────────

    def slots_for_duration(self, duration_minutes: int) -> int:
        """How many individual slots does *duration_minutes* span?

        Raises ``ValueError`` if duration is not a multiple of interval.
        """
        if duration_minutes % self.interval_minutes != 0:
            raise ValueError(
                f"duration_minutes ({duration_minutes}) must be a multiple of "
                f"interval_minutes ({self.interval_minutes})."
            )
        return duration_minutes // self.interval_minutes

    def is_block_available(
        self,
        block_start: datetime.datetime,
        booked_windows: List[Tuple[datetime.datetime, datetime.datetime]],
        slots_requested: int = 1,
    ) -> bool:
        """Check whether a consecutive block of *slots_requested* slots is free.

        Args:
            block_start:      Start of the first slot in the block (UTC).
            booked_windows:   Existing bookings as (start, end) pairs.
            slots_requested:  Number of consecutive interval-length slots
                              needed (default 1 = single slot booking).

        Returns:
            ``True`` only when the entire block is conflict-free.
        """
        block_end = block_start + datetime.timedelta(
            minutes=self.interval_minutes * slots_requested
        )
        return not self._overlaps(block_start, block_end, booked_windows)

    def block_end_time(
        self, block_start: datetime.datetime, slots_requested: int = 1
    ) -> datetime.datetime:
        """Compute the end time for a multi-slot block."""
        return block_start + datetime.timedelta(
            minutes=self.interval_minutes * slots_requested
        )
