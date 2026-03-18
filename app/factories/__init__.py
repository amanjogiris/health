"""Slot factory package.

Exports the abstract base and all concrete factory implementations so that
callers only need to import from ``app.factories``.
"""
from app.factories.base import DynamicSlot, SlotFactory
from app.factories.fixed_interval import FixedIntervalSlotFactory

__all__ = ["DynamicSlot", "SlotFactory", "FixedIntervalSlotFactory"]
