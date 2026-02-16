"""
Pytest configuration and shared fixtures for backend tests.

This file provides common fixtures used across all test modules.
"""
import pytest
from unittest.mock import MagicMock, Mock
from datetime import datetime, date
import pandas as pd
from sqlalchemy.orm import Session


# ===========================
# DATABASE FIXTURES
# ===========================

@pytest.fixture
def mock_db():
    """
    Mock SQLAlchemy database session for unit tests.
    Use this to avoid real database connections.
    """
    db = MagicMock(spec=Session)
    return db


@pytest.fixture
def mock_query():
    """
    Mock SQLAlchemy query object with chainable methods.
    """
    query = MagicMock()
    query.filter.return_value = query
    query.options.return_value = query
    query.join.return_value = query
    query.group_by.return_value = query
    query.order_by.return_value = query
    query.limit.return_value = query
    query.offset.return_value = query
    query.distinct.return_value = query
    query.all.return_value = []
    query.first.return_value = None
    query.scalar.return_value = 0
    query.count.return_value = 0
    return query


# ===========================
# MOCK MODEL FACTORIES
# ===========================

@pytest.fixture
def mock_employee():
    """Factory to create mock Employee objects."""
    def _create(employee_id=1, zid="Z1234", full_name="John Doe", **kwargs):
        employee = Mock()
        employee.employee_id = employee_id
        employee.zid = zid
        employee.full_name = full_name
        employee.start_date_of_working = kwargs.get('start_date', date(2020, 1, 1))
        
        # Organization relationships
        employee.sub_segment = kwargs.get('sub_segment')
        employee.project = kwargs.get('project')
        employee.team = kwargs.get('team')
        employee.role = kwargs.get('role')
        
        # Skills relationship
        employee.employee_skills = kwargs.get('employee_skills', [])
        
        # Project allocations relationship
        employee.project_allocations = kwargs.get('project_allocations', [])
        
        return employee
    return _create


@pytest.fixture
def mock_skill():
    """Factory to create mock Skill objects."""
    def _create(skill_id=1, skill_name="Python", subcategory=None, category=None, **kwargs):
        skill = Mock()
        skill.skill_id = skill_id
        skill.skill_name = skill_name
        skill.category_id = kwargs.get('category_id', 1)
        skill.subcategory_id = kwargs.get('subcategory_id', 1)
        skill.skill_description = kwargs.get('description', f"{skill_name} programming")
        
        # Relationships - use positional args if provided, otherwise kwargs
        skill.category = category if category is not None else kwargs.get('category')
        skill.subcategory = subcategory if subcategory is not None else kwargs.get('subcategory')
        
        return skill
    return _create


@pytest.fixture
def mock_employee_skill():
    """Factory to create mock EmployeeSkill objects."""
    def _create(emp_skill_id=1, employee_id=1, skill_id=1, **kwargs):
        emp_skill = Mock()
        emp_skill.emp_skill_id = emp_skill_id
        emp_skill.employee_id = employee_id
        emp_skill.skill_id = skill_id
        emp_skill.proficiency_level_id = kwargs.get('proficiency_level_id', 3)
        emp_skill.years_experience = kwargs.get('years_experience', 2)
        emp_skill.last_used = kwargs.get('last_used', 2024)
        emp_skill.interest_level = kwargs.get('interest_level', 4)
        emp_skill.last_updated = kwargs.get('last_updated', datetime(2024, 1, 1))
        
        # Relationships
        emp_skill.skill = kwargs.get('skill')
        emp_skill.proficiency_level = kwargs.get('proficiency_level')
        emp_skill.employee = kwargs.get('employee')
        
        return emp_skill
    return _create


@pytest.fixture
def mock_organization():
    """Factory to create mock organization objects (Segment, SubSegment, Project, Team, Role)."""
    def _create(obj_type="sub_segment", id=1, name="Engineering"):
        obj = Mock()
        
        if obj_type == "segment":
            obj.segment_id = id
            obj.segment_name = name
        elif obj_type == "sub_segment":
            obj.sub_segment_id = id
            obj.sub_segment_name = name
        elif obj_type == "project":
            obj.project_id = id
            obj.project_name = name
        elif obj_type == "team":
            obj.team_id = id
            obj.team_name = name
        elif obj_type == "role":
            obj.role_id = id
            obj.role_name = name
        
        return obj
    return _create


@pytest.fixture
def mock_proficiency():
    """Factory to create mock ProficiencyLevel objects."""
    def _create(level_id=3, level_name="Intermediate", **kwargs):
        prof = Mock()
        prof.proficiency_level_id = level_id
        prof.level_name = level_name
        prof.level_description = kwargs.get('description', f"{level_name} level")
        return prof
    return _create


@pytest.fixture
def mock_category():
    """Factory to create mock SkillCategory objects."""
    def _create(category_id=1, category_name="Programming"):
        category = Mock()
        category.category_id = category_id
        category.category_name = category_name
        return category
    return _create


@pytest.fixture
def mock_subcategory():
    """Factory to create mock SkillSubcategory objects."""
    def _create(subcategory_id=1, subcategory_name="Backend Development", category=None):
        subcategory = Mock()
        subcategory.subcategory_id = subcategory_id
        subcategory.subcategory_name = subcategory_name
        subcategory.category = category
        return subcategory
    return _create


# ===========================
# PAGINATION FIXTURES
# ===========================

@pytest.fixture
def mock_pagination():
    """Mock PaginationParams object."""
    def _create(page=1, size=10):
        pagination = Mock()
        pagination.page = page
        pagination.size = size
        pagination.offset = (page - 1) * size
        return pagination
    return _create


# ===========================
# DATAFRAME FIXTURES
# ===========================

@pytest.fixture
def sample_employee_df():
    """Sample employee DataFrame for import testing."""
    return pd.DataFrame({
        'ZID': ['Z1001', 'Z1002', 'Z1003'],
        'Full Name': ['Alice Smith', 'Bob Jones', 'Carol White'],
        'Role': ['Developer', 'Analyst', 'Manager'],
        'Sub-Segment': ['Engineering', 'Data', 'Management'],
        'Project': ['Project A', 'Project B', 'Project C'],
        'Team': ['Team X', 'Team Y', 'Team Z'],
        'Start Date of Working': [date(2020, 1, 15), date(2019, 5, 10), date(2021, 3, 1)]
    })


@pytest.fixture
def sample_skills_df():
    """Sample skills DataFrame for import testing."""
    return pd.DataFrame({
        'Skill': ['Python', 'SQL', 'Java', 'Excel'],
        'Category': ['Programming', 'Database', 'Programming', 'Office'],
        'Subcategory': ['Backend', 'Relational', 'Backend', 'Productivity'],
        'Proficiency': [4, 3, 2, 5],
        'Years': [3, 2, 1, 5],
        'Last Used': [2024, 2023, 2024, 2024],
        'Interest': [5, 4, 3, 4]
    })


# ===========================
# FILE SYSTEM FIXTURES
# ===========================

@pytest.fixture
def mock_excel_file(tmp_path):
    """Create a temporary Excel file for testing."""
    def _create(filename="test.xlsx", sheet_data=None):
        file_path = tmp_path / filename
        if sheet_data:
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                for sheet_name, df in sheet_data.items():
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
        return file_path
    return _create


# ===========================
# TIME FIXTURES
# ===========================

@pytest.fixture
def freeze_time(monkeypatch):
    """Fixture to freeze time for deterministic tests."""
    def _freeze(frozen_datetime=datetime(2024, 1, 1, 12, 0, 0)):
        class FrozenDatetime:
            @classmethod
            def now(cls):
                return frozen_datetime
            
            @classmethod
            def utcnow(cls):
                return frozen_datetime
        
        monkeypatch.setattr('datetime.datetime', FrozenDatetime)
        return frozen_datetime
    return _freeze
