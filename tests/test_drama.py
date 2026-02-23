"""
Tests for Tsukuyomi Core Drama Module

Run with: python -m pytest tests/test_drama.py -v
"""

import pytest
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from tsukuyomi.narrative.events.library import EventLibrary, Event, EventCategory
from tsukuyomi.narrative.flow.branching import BranchManager
from tsukuyomi.narrative.context.context_aware import ContextAwareDramaDirector


class TestEvent:
    def test_create_event(self):
        event = Event(
            id="test_1",
            category=EventCategory.NARRATIVE,
            description="A test event"
        )
        assert event.id == "test_1"


class TestEventLibrary:
    def test_create_library(self):
        library = EventLibrary()
        assert library is not None

    def test_configure(self):
        library = EventLibrary()
        library.configure({})


class TestBranchManager:
    def test_create_manager(self):
        manager = BranchManager()
        assert manager is not None


class TestContextAwareDramaDirector:
    def test_create_director(self):
        library = EventLibrary()
        manager = BranchManager()
        director = ContextAwareDramaDirector(library, manager)
        assert director is not None

    def test_get_status(self):
        library = EventLibrary()
        manager = BranchManager()
        director = ContextAwareDramaDirector(library, manager)
        status = director.get_status()
        assert status is not None

    def test_update_sentiment(self):
        library = EventLibrary()
        manager = BranchManager()
        director = ContextAwareDramaDirector(library, manager)
        director.update_sentiment(0.5)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
