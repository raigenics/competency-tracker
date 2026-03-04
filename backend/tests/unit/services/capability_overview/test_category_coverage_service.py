"""
Unit tests for capability_overview/category_coverage_service.py

Tests employee concentration metrics per skill category:
- Most populated category (highest employee count)
- Least populated category (lowest non-zero employee count)
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from app.services.capability_overview import category_coverage_service
from app.schemas.skill import CategoryCoverageResponse, CategoryCoverageItem


class TestGetCategoryCoverage:
    """Test the main public function get_category_coverage()."""
    
    def test_returns_complete_coverage_response(self, mock_db):
        """Should return complete CategoryCoverageResponse with most/least populated."""
        # Arrange
        mock_category_counts = {
            1: {'category_name': 'Backend Development', 'employee_count': 50},
            2: {'category_name': 'Frontend Development', 'employee_count': 30},
            3: {'category_name': 'DevOps', 'employee_count': 10}
        }
        with patch.object(category_coverage_service, '_query_employee_count_by_category', return_value=mock_category_counts):
            
            # Act
            result = category_coverage_service.get_category_coverage(mock_db)
            
            # Assert
            assert isinstance(result, CategoryCoverageResponse)
            assert result.most_populated_category.category_name == 'Backend Development'
            assert result.most_populated_category.employee_count == 50
            assert result.least_populated_category.category_name == 'DevOps'
            assert result.least_populated_category.employee_count == 10
    
    def test_handles_empty_data(self, mock_db):
        """Should handle case when no categories have employees."""
        # Arrange
        with patch.object(category_coverage_service, '_query_employee_count_by_category', return_value={}):
            
            # Act
            result = category_coverage_service.get_category_coverage(mock_db)
            
            # Assert
            assert result.most_populated_category is None
            assert result.least_populated_category is None
    
    def test_handles_single_category(self, mock_db):
        """Should handle case when only one category has employees."""
        # Arrange
        mock_category_counts = {
            1: {'category_name': 'Backend Development', 'employee_count': 25}
        }
        with patch.object(category_coverage_service, '_query_employee_count_by_category', return_value=mock_category_counts):
            
            # Act
            result = category_coverage_service.get_category_coverage(mock_db)
            
            # Assert
            assert result.most_populated_category.category_name == 'Backend Development'
            assert result.least_populated_category.category_name == 'Backend Development'
    
    def test_excludes_zero_employee_categories_from_least(self, mock_db):
        """Should exclude categories with zero employees from least populated."""
        # Arrange
        mock_category_counts = {
            1: {'category_name': 'Backend Development', 'employee_count': 50},
            2: {'category_name': 'Frontend Development', 'employee_count': 0},
            3: {'category_name': 'DevOps', 'employee_count': 10}
        }
        with patch.object(category_coverage_service, '_query_employee_count_by_category', return_value=mock_category_counts):
            
            # Act
            result = category_coverage_service.get_category_coverage(mock_db)
            
            # Assert
            # Most populated is Backend (50)
            assert result.most_populated_category.category_name == 'Backend Development'
            # Least populated should be DevOps (10), not Frontend (0)
            assert result.least_populated_category.category_name == 'DevOps'
            assert result.least_populated_category.employee_count == 10
    
    def test_preserves_category_id(self, mock_db):
        """Should preserve category_id in response items."""
        # Arrange
        mock_category_counts = {
            42: {'category_name': 'Test Category', 'employee_count': 100}
        }
        with patch.object(category_coverage_service, '_query_employee_count_by_category', return_value=mock_category_counts):
            
            # Act
            result = category_coverage_service.get_category_coverage(mock_db)
            
            # Assert
            assert result.most_populated_category.category_id == 42
