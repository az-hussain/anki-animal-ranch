"""
Tests for the Animal model.
"""

import pytest
from anki_animal_ranch.core.constants import AnimalType, GrowthStage
from anki_animal_ranch.models.animal import Animal


class TestAnimalCreation:
    """Tests for animal creation and initialization."""
    
    def test_create_chicken(self):
        """Test creating a chicken."""
        chicken = Animal(type=AnimalType.CHICKEN)
        
        assert chicken.type == AnimalType.CHICKEN
        assert chicken.maturity == 0.0
        assert chicken.health == 1.0
        assert chicken.happiness == 1.0
        assert chicken.hunger == 1.0
        assert chicken.growth_stage == GrowthStage.BABY
    
    def test_create_with_name(self):
        """Test creating an animal with a custom name."""
        chicken = Animal(type=AnimalType.CHICKEN, name="Henrietta")
        
        assert chicken.name == "Henrietta"
        assert chicken.display_name == "Henrietta"
    
    def test_display_name_fallback(self):
        """Test that display name falls back to type name."""
        chicken = Animal(type=AnimalType.CHICKEN)
        
        assert chicken.display_name == "Chicken"
    
    def test_values_clamped(self):
        """Test that values are clamped to valid ranges."""
        chicken = Animal(
            type=AnimalType.CHICKEN,
            maturity=1.5,  # Should clamp to 1.0
            health=-0.5,   # Should clamp to 0.0
        )
        
        assert chicken.maturity == 1.0
        assert chicken.health == 0.0


class TestAnimalGrowth:
    """Tests for animal growth mechanics."""
    
    def test_growth_stage_baby(self):
        """Test baby growth stage detection."""
        chicken = Animal(type=AnimalType.CHICKEN, maturity=0.0)
        assert chicken.growth_stage == GrowthStage.BABY
        
        chicken.maturity = 0.32
        assert chicken.growth_stage == GrowthStage.BABY
    
    def test_growth_stage_teen(self):
        """Test teen growth stage detection."""
        chicken = Animal(type=AnimalType.CHICKEN, maturity=0.33)
        assert chicken.growth_stage == GrowthStage.TEEN
        
        chicken.maturity = 0.65
        assert chicken.growth_stage == GrowthStage.TEEN
    
    def test_growth_stage_adult(self):
        """Test adult growth stage detection."""
        chicken = Animal(type=AnimalType.CHICKEN, maturity=0.66)
        assert chicken.growth_stage == GrowthStage.ADULT
        
        chicken.maturity = 1.0
        assert chicken.growth_stage == GrowthStage.ADULT
    
    def test_is_mature(self):
        """Test maturity detection."""
        chicken = Animal(type=AnimalType.CHICKEN, maturity=0.99)
        assert not chicken.is_mature
        
        chicken.maturity = 1.0
        assert chicken.is_mature
    
    def test_growth_over_time(self):
        """Test that animals grow when updated."""
        chicken = Animal(type=AnimalType.CHICKEN, maturity=0.0)
        initial_maturity = chicken.maturity
        
        chicken.update(hours_passed=10)
        
        assert chicken.maturity > initial_maturity
    
    def test_growth_capped_at_one(self):
        """Test that maturity doesn't exceed 1.0."""
        chicken = Animal(type=AnimalType.CHICKEN, maturity=0.99)
        
        chicken.update(hours_passed=100)
        
        assert chicken.maturity == 1.0


class TestAnimalProduction:
    """Tests for animal production mechanics."""
    
    def test_can_produce_when_mature_and_healthy(self):
        """Test that mature, healthy animals can produce."""
        chicken = Animal(type=AnimalType.CHICKEN, maturity=1.0, health=1.0)
        assert chicken.can_produce
    
    def test_cannot_produce_when_immature(self):
        """Test that immature animals cannot produce."""
        chicken = Animal(type=AnimalType.CHICKEN, maturity=0.5, health=1.0)
        assert not chicken.can_produce
    
    def test_cannot_produce_when_unhealthy(self):
        """Test that unhealthy animals cannot produce."""
        chicken = Animal(type=AnimalType.CHICKEN, maturity=1.0, health=0.2)
        assert not chicken.can_produce
    
    def test_production_timer(self):
        """Test production timing."""
        chicken = Animal(type=AnimalType.CHICKEN, maturity=1.0)
        chicken.hours_since_production = 0.0
        
        assert not chicken.can_produce_now
        
        chicken.hours_since_production = chicken.production_interval
        assert chicken.can_produce_now
    
    def test_collect_product(self):
        """Test collecting a product."""
        chicken = Animal(type=AnimalType.CHICKEN, maturity=1.0)
        chicken.hours_since_production = chicken.production_interval
        
        result = chicken.collect_product()
        
        assert result is True
        assert chicken.hours_since_production == 0.0


class TestAnimalCare:
    """Tests for animal care mechanics."""
    
    def test_feeding_increases_hunger(self):
        """Test that feeding increases hunger level."""
        chicken = Animal(type=AnimalType.CHICKEN, hunger=0.5)
        
        chicken.feed(0.3)
        
        assert chicken.hunger == 0.8
    
    def test_feeding_capped_at_one(self):
        """Test that hunger doesn't exceed 1.0."""
        chicken = Animal(type=AnimalType.CHICKEN, hunger=0.9)
        
        chicken.feed(1.0)
        
        assert chicken.hunger == 1.0
    
    def test_petting_increases_happiness(self):
        """Test that petting increases happiness."""
        chicken = Animal(type=AnimalType.CHICKEN, happiness=0.5)
        
        chicken.pet()
        
        assert chicken.happiness == 0.7
    
    def test_healing_increases_health(self):
        """Test that healing increases health."""
        chicken = Animal(type=AnimalType.CHICKEN, health=0.3)
        
        chicken.heal(0.5)
        
        assert chicken.health == 0.8
    
    def test_care_quality_calculation(self):
        """Test care quality is average of stats."""
        chicken = Animal(
            type=AnimalType.CHICKEN,
            health=0.9,
            happiness=0.6,
            hunger=0.3,
        )
        
        expected = (0.9 + 0.6 + 0.3) / 3
        assert chicken.care_quality == expected


class TestAnimalSerialization:
    """Tests for animal serialization."""
    
    def test_to_dict(self):
        """Test serialization to dictionary."""
        chicken = Animal(
            type=AnimalType.CHICKEN,
            name="Test",
            maturity=0.5,
            health=0.8,
        )
        
        data = chicken.to_dict()
        
        assert data["type"] == "chicken"
        assert data["name"] == "Test"
        assert data["maturity"] == 0.5
        assert data["health"] == 0.8
        assert "id" in data
    
    def test_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            "id": "test-id",
            "type": "chicken",
            "name": "Test",
            "maturity": 0.75,
            "health": 0.9,
            "happiness": 0.8,
            "hunger": 0.7,
            "age_hours": 100.0,
            "building_id": "building-1",
            "position": [1.0, 2.0],
            "hours_since_production": 2.0,
        }
        
        chicken = Animal.from_dict(data)
        
        assert chicken.id == "test-id"
        assert chicken.type == AnimalType.CHICKEN
        assert chicken.name == "Test"
        assert chicken.maturity == 0.75
        assert chicken.position == (1.0, 2.0)
    
    def test_round_trip(self):
        """Test that serialization is reversible."""
        original = Animal(
            type=AnimalType.PIG,
            name="Porky",
            maturity=0.5,
            health=0.9,
        )
        
        data = original.to_dict()
        restored = Animal.from_dict(data)
        
        assert restored.type == original.type
        assert restored.name == original.name
        assert restored.maturity == original.maturity
        assert restored.health == original.health
