-- ============================================================
-- CompetencyIQ — Automation Test Data Cleanup Script
-- Purpose : Remove ALL test data inserted by seed.sql
-- Scope   : IDs >= 9000 | created_by = 'test_automation'
-- Run     : psql $DATABASE_URL -f cleanup.sql
-- Order   : Reverse of seed.sql (respect foreign keys)
-- ============================================================

BEGIN;

-- History tables first (no dependents)
DELETE FROM employee_skill_history
WHERE employee_id >= 9000
   OR changed_by = 'test_automation';

DELETE FROM proficiency_change_history
WHERE employee_id >= 9000
   OR changed_by = 'test_automation';

-- Fact tables
DELETE FROM employee_skills
WHERE employee_skill_id >= 9000;

DELETE FROM employee_project_allocations
WHERE allocation_id >= 9000;

-- Employees
DELETE FROM employees
WHERE employee_id >= 9000;

-- Skill aliases, embeddings, skills
DELETE FROM skill_aliases
WHERE alias_id >= 9000
   OR created_by = 'test_automation';

DELETE FROM skill_embeddings
WHERE skill_id >= 9000;

DELETE FROM skills
WHERE skill_id >= 9000;

-- Skill subcategories and categories
DELETE FROM skill_subcategories
WHERE subcategory_id >= 9000;

DELETE FROM skill_categories
WHERE category_id >= 9000;

-- Roles
DELETE FROM roles
WHERE role_id >= 9000;

-- Org hierarchy (reverse order: teams → projects → sub_segments)
-- Do NOT delete segment ID 1 — it is the live DTS segment.
DELETE FROM teams
WHERE team_id >= 9000;

DELETE FROM projects
WHERE project_id >= 9000;

DELETE FROM sub_segments
WHERE sub_segment_id >= 9000;

-- Test segments (IDs >= 9000 except the live DTS segment ID 1)
DELETE FROM segments
WHERE segment_id >= 9000;

-- Proficiency levels: NEVER delete — system reference data.

COMMIT;

-- ============================================================
-- What this script does NOT delete:
--   - segments (ID 1 = DTS — live production segment)
--   - proficiency_levels (system reference data)
--   - auth_roles, auth_scope_types (system reference data)
-- ============================================================