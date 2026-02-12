"""
Unit tests for taxonomy_update_service.py

Tests for:
1. update_category_name - success, not found, duplicate, empty
2. update_subcategory_name - success, not found, duplicate (scoped), empty
3. update_skill_name - success, not found, duplicate (scoped), empty
4. update_alias - success, not found, duplicate (scoped), empty
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

from app.services.master_data.taxonomy_update_service import (
    update_category_name,
    update_subcategory_name,
    update_skill_name,
    update_alias,
)
from app.services.master_data.exceptions import (
    NotFoundError,
    ConflictError,
    ValidationError,
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_category():
    """Factory to create mock Category objects."""
    def _create(category_id=1, category_name="Development", **kwargs):
        category = Mock()
        category.category_id = category_id
        category.category_name = category_name
        category.created_at = kwargs.get('created_at', datetime(2024, 1, 1))
        category.created_by = kwargs.get('created_by', 'admin')
        return category
    return _create


@pytest.fixture
def mock_subcategory():
    """Factory to create mock Subcategory objects."""
    def _create(subcategory_id=1, subcategory_name="Frontend", category_id=1, **kwargs):
        subcategory = Mock()
        subcategory.subcategory_id = subcategory_id
        subcategory.subcategory_name = subcategory_name
        subcategory.category_id = category_id
        subcategory.created_at = kwargs.get('created_at', datetime(2024, 1, 1))
        subcategory.created_by = kwargs.get('created_by', 'admin')
        return subcategory
    return _create


@pytest.fixture
def mock_skill():
    """Factory to create mock Skill objects."""
    def _create(skill_id=1, skill_name="React", subcategory_id=1, **kwargs):
        skill = Mock()
        skill.skill_id = skill_id
        skill.skill_name = skill_name
        skill.subcategory_id = subcategory_id
        skill.created_at = kwargs.get('created_at', datetime(2024, 1, 1))
        skill.created_by = kwargs.get('created_by', 'admin')
        return skill
    return _create


@pytest.fixture
def mock_alias():
    """Factory to create mock Alias objects."""
    def _create(alias_id=1, alias_text="ReactJS", skill_id=1, **kwargs):
        alias = Mock()
        alias.alias_id = alias_id
        alias.alias_text = alias_text
        alias.skill_id = skill_id
        alias.source = kwargs.get('source', 'manual')
        alias.confidence_score = kwargs.get('confidence_score', 1.0)
        alias.created_at = kwargs.get('created_at', datetime(2024, 1, 1))
        return alias
    return _create


# ============================================================================
# CATEGORY UPDATE TESTS
# ============================================================================

class TestUpdateCategoryName:
    """Tests for update_category_name function."""
    
    def test_success_update(self, mock_db, mock_category):
        """Should successfully update category name."""
        # Arrange
        category = mock_category(category_id=1, category_name="Old Name")
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            category,  # First call: find category
            None       # Second call: check duplicates
        ]
        
        # Act
        result = update_category_name(mock_db, 1, "New Name", actor="user1")
        
        # Assert
        assert result.id == 1
        assert result.name == "New Name"
        mock_db.commit.assert_called_once()
    
    def test_not_found(self, mock_db):
        """Should raise NotFoundError when category doesn't exist."""
        # Arrange
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Act & Assert
        with pytest.raises(NotFoundError) as exc_info:
            update_category_name(mock_db, 999, "New Name")
        
        assert "Category with id 999 not found" in str(exc_info.value.message)
    
    def test_duplicate_name(self, mock_db, mock_category):
        """Should raise ConflictError when name already exists."""
        # Arrange
        category = mock_category(category_id=1, category_name="Old Name")
        existing = mock_category(category_id=2, category_name="Existing Name")
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            category,  # First call: find category
            existing   # Second call: find duplicate
        ]
        
        # Act & Assert
        with pytest.raises(ConflictError) as exc_info:
            update_category_name(mock_db, 1, "Existing Name")
        
        assert "already exists" in str(exc_info.value.message)
    
    def test_empty_name(self, mock_db, mock_category):
        """Should raise ValidationError when name is empty."""
        # Arrange
        category = mock_category(category_id=1)
        mock_db.query.return_value.filter.return_value.first.return_value = category
        
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            update_category_name(mock_db, 1, "   ")
        
        assert "cannot be empty" in str(exc_info.value.message)
    
    def test_no_change_when_same_name(self, mock_db, mock_category):
        """Should return current state without commit when name unchanged."""
        # Arrange
        category = mock_category(category_id=1, category_name="Same Name")
        mock_db.query.return_value.filter.return_value.first.return_value = category
        
        # Act
        result = update_category_name(mock_db, 1, "Same Name")
        
        # Assert
        assert result.id == 1
        assert result.name == "Same Name"
        mock_db.commit.assert_not_called()


# ============================================================================
# SUBCATEGORY UPDATE TESTS
# ============================================================================

class TestUpdateSubcategoryName:
    """Tests for update_subcategory_name function."""
    
    def test_success_update(self, mock_db, mock_subcategory):
        """Should successfully update subcategory name."""
        # Arrange
        subcategory = mock_subcategory(subcategory_id=1, subcategory_name="Old Name", category_id=1)
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            subcategory,  # First call: find subcategory
            None          # Second call: check duplicates
        ]
        
        # Act
        result = update_subcategory_name(mock_db, 1, "New Name", actor="user1")
        
        # Assert
        assert result.id == 1
        assert result.name == "New Name"
        mock_db.commit.assert_called_once()
    
    def test_not_found(self, mock_db):
        """Should raise NotFoundError when subcategory doesn't exist."""
        # Arrange
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Act & Assert
        with pytest.raises(NotFoundError) as exc_info:
            update_subcategory_name(mock_db, 999, "New Name")
        
        assert "Subcategory with id 999 not found" in str(exc_info.value.message)
    
    def test_duplicate_name_in_same_category(self, mock_db, mock_subcategory):
        """Should raise ConflictError when name exists in same category."""
        # Arrange
        subcategory = mock_subcategory(subcategory_id=1, subcategory_name="Old", category_id=1)
        existing = mock_subcategory(subcategory_id=2, subcategory_name="Existing", category_id=1)
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            subcategory,  # First call: find subcategory
            existing      # Second call: find duplicate
        ]
        
        # Act & Assert
        with pytest.raises(ConflictError) as exc_info:
            update_subcategory_name(mock_db, 1, "Existing")
        
        assert "already exists" in str(exc_info.value.message)
        assert "category" in str(exc_info.value.message).lower()
    
    def test_empty_name(self, mock_db, mock_subcategory):
        """Should raise ValidationError when name is empty."""
        # Arrange
        subcategory = mock_subcategory(subcategory_id=1)
        mock_db.query.return_value.filter.return_value.first.return_value = subcategory
        
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            update_subcategory_name(mock_db, 1, "")
        
        assert "cannot be empty" in str(exc_info.value.message)


# ============================================================================
# SKILL UPDATE TESTS
# ============================================================================

class TestUpdateSkillName:
    """Tests for update_skill_name function."""
    
    def test_success_update(self, mock_db, mock_skill):
        """Should successfully update skill name."""
        # Arrange
        skill = mock_skill(skill_id=1, skill_name="Old Name", subcategory_id=1)
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            skill,  # First call: find skill
            None    # Second call: check duplicates
        ]
        
        # Act
        result = update_skill_name(mock_db, 1, "New Name", actor="user1")
        
        # Assert
        assert result.id == 1
        assert result.name == "New Name"
        mock_db.commit.assert_called_once()
    
    def test_not_found(self, mock_db):
        """Should raise NotFoundError when skill doesn't exist."""
        # Arrange
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Act & Assert
        with pytest.raises(NotFoundError) as exc_info:
            update_skill_name(mock_db, 999, "New Name")
        
        assert "Skill with id 999 not found" in str(exc_info.value.message)
    
    def test_duplicate_name_in_same_subcategory(self, mock_db, mock_skill):
        """Should raise ConflictError when name exists in same subcategory."""
        # Arrange
        skill = mock_skill(skill_id=1, skill_name="Old", subcategory_id=1)
        existing = mock_skill(skill_id=2, skill_name="Existing", subcategory_id=1)
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            skill,     # First call: find skill
            existing   # Second call: find duplicate
        ]
        
        # Act & Assert
        with pytest.raises(ConflictError) as exc_info:
            update_skill_name(mock_db, 1, "Existing")
        
        assert "already exists" in str(exc_info.value.message)
        assert "subcategory" in str(exc_info.value.message).lower()
    
    def test_empty_name(self, mock_db, mock_skill):
        """Should raise ValidationError when name is empty."""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            update_skill_name(mock_db, 1, "   ")
        
        assert "cannot be empty" in str(exc_info.value.message)


# ============================================================================
# ALIAS UPDATE TESTS
# ============================================================================

class TestUpdateAlias:
    """Tests for update_alias function."""
    
    def test_success_update_text(self, mock_db, mock_alias):
        """Should successfully update alias text."""
        # Arrange
        alias = mock_alias(alias_id=1, alias_text="Old Text", skill_id=1)
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            alias,  # First call: find alias
            None    # Second call: check duplicates
        ]
        
        # Act
        result = update_alias(mock_db, 1, alias_text="New Text", actor="user1")
        
        # Assert
        assert result.id == 1
        assert result.alias_text == "New Text"
        mock_db.commit.assert_called_once()
    
    def test_not_found(self, mock_db):
        """Should raise NotFoundError when alias doesn't exist."""
        # Arrange
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Act & Assert
        with pytest.raises(NotFoundError) as exc_info:
            update_alias(mock_db, 999, alias_text="New Text")
        
        assert "Alias with id 999 not found" in str(exc_info.value.message)
    
    def test_duplicate_text_in_same_skill(self, mock_db, mock_alias):
        """Should raise ConflictError when alias_text exists for same skill."""
        # Arrange
        alias = mock_alias(alias_id=1, alias_text="Old", skill_id=1)
        existing = mock_alias(alias_id=2, alias_text="Existing", skill_id=1)
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            alias,     # First call: find alias
            existing   # Second call: find duplicate
        ]
        
        # Act & Assert
        with pytest.raises(ConflictError) as exc_info:
            update_alias(mock_db, 1, alias_text="Existing")
        
        assert "already exists" in str(exc_info.value.message)
        assert "skill" in str(exc_info.value.message).lower()
    
    def test_empty_alias_text(self, mock_db, mock_alias):
        """Should raise ValidationError when alias_text is empty."""
        # Arrange
        alias = mock_alias(alias_id=1)
        mock_db.query.return_value.filter.return_value.first.return_value = alias
        
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            update_alias(mock_db, 1, alias_text="   ")
        
        assert "cannot be empty" in str(exc_info.value.message)
    
    def test_update_optional_fields(self, mock_db, mock_alias):
        """Should update source and confidence_score when provided."""
        # Arrange
        alias = mock_alias(alias_id=1, source="old_source", confidence_score=0.5)
        mock_db.query.return_value.filter.return_value.first.return_value = alias
        
        # Act
        result = update_alias(mock_db, 1, source="new_source", confidence_score=0.9)
        
        # Assert
        assert alias.source == "new_source"
        assert alias.confidence_score == 0.9
        mock_db.commit.assert_called_once()
