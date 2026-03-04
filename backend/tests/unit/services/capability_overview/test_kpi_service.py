"""
Unit tests for capability_overview/kpi_service.py

Tests KPI metrics for the Capability Overview page:
- Total Skills (with at least one mapped employee)
- Average Proficiency (across mapped employees)
- Total Certifications (count of non-null certification fields)
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from app.services.capability_overview import kpi_service
from app.schemas.skill import CapabilityKPIsResponse


class TestGetCapabilityKpis:
    """Test the main public function get_capability_kpis()."""
    
    def test_returns_complete_kpis_response(self, mock_db):
        """Should return complete CapabilityKPIsResponse with all fields."""
        # Arrange
        mock_subquery = MagicMock()
        with patch.object(kpi_service, '_get_scoped_employee_ids_subquery', return_value=mock_subquery), \
             patch.object(kpi_service, '_query_total_skills_with_employees', return_value=150), \
             patch.object(kpi_service, '_query_avg_proficiency', return_value=3.45), \
             patch.object(kpi_service, '_query_total_certifications', return_value=42):
            
            # Act
            result = kpi_service.get_capability_kpis(mock_db)
            
            # Assert
            assert isinstance(result, CapabilityKPIsResponse)
            assert result.total_skills == 150
            assert result.avg_proficiency == 3.45
            assert result.total_certifications == 42
    
    def test_handles_zero_data(self, mock_db):
        """Should handle case when no data exists."""
        # Arrange
        mock_subquery = MagicMock()
        with patch.object(kpi_service, '_get_scoped_employee_ids_subquery', return_value=mock_subquery), \
             patch.object(kpi_service, '_query_total_skills_with_employees', return_value=0), \
             patch.object(kpi_service, '_query_avg_proficiency', return_value=None), \
             patch.object(kpi_service, '_query_total_certifications', return_value=0):
            
            # Act
            result = kpi_service.get_capability_kpis(mock_db)
            
            # Assert
            assert result.total_skills == 0
            assert result.avg_proficiency is None
            assert result.total_certifications == 0
    
    def test_calls_all_query_functions(self, mock_db):
        """Should call all required query functions."""
        # Arrange
        mock_subquery = MagicMock()
        with patch.object(kpi_service, '_get_scoped_employee_ids_subquery', return_value=mock_subquery) as mock_scope, \
             patch.object(kpi_service, '_query_total_skills_with_employees', return_value=10) as mock_skills, \
             patch.object(kpi_service, '_query_avg_proficiency', return_value=3.0) as mock_prof, \
             patch.object(kpi_service, '_query_total_certifications', return_value=5) as mock_certs:
            
            # Act
            kpi_service.get_capability_kpis(mock_db)
            
            # Assert
            mock_scope.assert_called_once_with(mock_db)
            mock_skills.assert_called_once_with(mock_db, mock_subquery)
            mock_prof.assert_called_once_with(mock_db, mock_subquery)
            mock_certs.assert_called_once_with(mock_db, mock_subquery)


class TestQueryTotalSkillsWithEmployees:
    """Test the _query_total_skills_with_employees() function."""
    
    def test_returns_count_when_data_exists(self, mock_db):
        """Should return count of distinct skills with employees."""
        # Arrange
        mock_subquery = MagicMock()
        mock_subquery.c.employee_id = 'employee_id'
        mock_db.query.return_value.filter.return_value.scalar.return_value = 75
        
        # Act
        result = kpi_service._query_total_skills_with_employees(mock_db, mock_subquery)
        
        # Assert
        assert result == 75
    
    def test_returns_zero_when_no_data(self, mock_db):
        """Should return 0 when scalar returns None."""
        # Arrange
        mock_subquery = MagicMock()
        mock_subquery.c.employee_id = 'employee_id'
        mock_db.query.return_value.filter.return_value.scalar.return_value = None
        
        # Act
        result = kpi_service._query_total_skills_with_employees(mock_db, mock_subquery)
        
        # Assert
        assert result == 0


class TestQueryAvgProficiency:
    """Test the _query_avg_proficiency() function."""
    
    def test_returns_rounded_average(self, mock_db):
        """Should return average proficiency rounded to 2 decimal places."""
        # Arrange
        mock_subquery = MagicMock()
        mock_subquery.c.employee_id = 'employee_id'
        mock_db.query.return_value.filter.return_value.scalar.return_value = 3.456789
        
        # Act
        result = kpi_service._query_avg_proficiency(mock_db, mock_subquery)
        
        # Assert
        assert result == 3.46
    
    def test_returns_none_when_no_data(self, mock_db):
        """Should return None when no proficiency data exists."""
        # Arrange
        mock_subquery = MagicMock()
        mock_subquery.c.employee_id = 'employee_id'
        mock_db.query.return_value.filter.return_value.scalar.return_value = None
        
        # Act
        result = kpi_service._query_avg_proficiency(mock_db, mock_subquery)
        
        # Assert
        assert result is None


class TestQueryTotalCertifications:
    """Test the _query_total_certifications() function."""
    
    def test_returns_certification_count(self, mock_db):
        """Should return count of non-null certifications."""
        # Arrange
        mock_subquery = MagicMock()
        mock_subquery.c.employee_id = 'employee_id'
        mock_db.query.return_value.filter.return_value.scalar.return_value = 28
        
        # Act
        result = kpi_service._query_total_certifications(mock_db, mock_subquery)
        
        # Assert
        assert result == 28
    
    def test_returns_zero_when_no_certifications(self, mock_db):
        """Should return 0 when no certifications exist."""
        # Arrange
        mock_subquery = MagicMock()
        mock_subquery.c.employee_id = 'employee_id'
        mock_db.query.return_value.filter.return_value.scalar.return_value = None
        
        # Act
        result = kpi_service._query_total_certifications(mock_db, mock_subquery)
        
        # Assert
        assert result == 0
