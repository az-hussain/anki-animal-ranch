"""
Pytest configuration and shared fixtures.
"""

import pytest
from anki_animal_ranch.core.constants import AnimalType, BuildingType, WorkerType
from anki_animal_ranch.core.time_system import FarmTime, TimeSystem
from anki_animal_ranch.models.animal import Animal
from anki_animal_ranch.models.building import Building
from anki_animal_ranch.models.farm import Farm
from anki_animal_ranch.models.worker import Worker


@pytest.fixture
def farm() -> Farm:
    """Create a fresh farm for testing."""
    return Farm.create_new(name="Test Farm")


@pytest.fixture
def time_system() -> TimeSystem:
    """Create a fresh time system for testing."""
    return TimeSystem()


@pytest.fixture
def chicken() -> Animal:
    """Create a test chicken."""
    return Animal(type=AnimalType.CHICKEN, name="Test Chicken")


@pytest.fixture
def pig() -> Animal:
    """Create a test pig."""
    return Animal(type=AnimalType.PIG, name="Test Pig")


@pytest.fixture
def cow() -> Animal:
    """Create a test cow."""
    return Animal(type=AnimalType.COW, name="Test Cow")


@pytest.fixture
def coop() -> Building:
    """Create a test coop."""
    return Building(type=BuildingType.COOP, position=(0, 0))


@pytest.fixture
def barn() -> Building:
    """Create a test barn."""
    return Building(type=BuildingType.BARN, position=(0, 0))


@pytest.fixture
def farmhand() -> Worker:
    """Create a test farmhand worker."""
    return Worker(type=WorkerType.FARMHAND, name="Test Worker")


@pytest.fixture
def farm_time() -> FarmTime:
    """Create a default farm time."""
    return FarmTime()
