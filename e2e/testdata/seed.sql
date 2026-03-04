


-- ============================================================
-- CompetencyIQ — Automation Test Data Seed Script
-- Purpose : Insert minimum viable test data for UI automation
-- Scope   : All IDs >= 9000 | created_by = 'test_automation'
-- Run     : psql $DATABASE_URL -f seed.sql
-- Safe    : Fully idempotent — safe to run multiple times
-- ============================================================
--
-- ⚠️  BEFORE RUNNING: verify your employees table has a 'zid'
--     column by running this in pgAdmin or psql:
--     SELECT column_name FROM information_schema.columns
--     WHERE table_name = 'employees' ORDER BY ordinal_position;
--
--     If the column is named differently (e.g. employee_code,
--     emp_zid) update the INSERT statements in Section 5 below.
-- ============================================================

BEGIN;

-- ============================================================
-- 0) PROFICIENCY LEVELS (Dreyfus Model — reference data)
-- These are likely already seeded by app migrations.
-- DO NOTHING = never overwrite existing values.
-- ============================================================

-- INSERT INTO proficiency_levels
--   (proficiency_level_id, level_name, level_description, created_at, updated_at)
-- VALUES
--   (1, 'Novice',            'Rigid adherence to rules; minimal situational perception.',       NOW(), NOW()),
--   (2, 'Advanced Beginner', 'Basic situational awareness; recognises recurring patterns.',     NOW(), NOW()),
--   (3, 'Competent',         'Plans and prioritises; copes with complexity deliberately.',      NOW(), NOW()),
--   (4, 'Proficient',        'Sees situations holistically; adjusts based on context.',         NOW(), NOW()),
--   (5, 'Expert',            'Intuitive grasp of situations; analytical only when needed.',     NOW(), NOW())
-- ON CONFLICT (proficiency_level_id) DO NOTHING;


-- ============================================================
-- 1) ORGANISATIONAL HIERARCHY
-- Segment ID 1 = 'DTS' — matches DEFAULT_DASHBOARD_CONTEXT
-- in featureFlags.js (SEGMENT_ID: 1, SCOPE_ID: 1).
-- All insight modules (Dashboard, Skill Coverage, Talent
-- Finder, Employee Directory) scope API calls to this ID.
-- Sub-segments, projects and teams are test-specific (>= 9000).
-- Insert order: segments → sub_segments → projects → teams
-- ============================================================

-- Segment (ID 1 must exist — DO NOTHING if already present)
INSERT INTO segments
  (segment_id, segment_name, created_by, created_at, updated_at, deleted_at, deleted_by)
VALUES
  (1, 'DTS', 'test_automation', NOW(), NOW(), NULL, NULL)
ON CONFLICT (segment_id) DO NOTHING;

-- Sub-Segments (2 — validates cascading filter + empty states)
INSERT INTO sub_segments
  (sub_segment_id, sub_segment_name, segment_id, created_by, created_at, updated_at, deleted_at, deleted_by)
VALUES
  (9001, 'Test SubSegment - Alpha', 1, 'test_automation', NOW(), NOW(), NULL, NULL),
  (9002, 'Test SubSegment - Beta',  1, 'test_automation', NOW(), NOW(), NULL, NULL)
ON CONFLICT (sub_segment_id) DO UPDATE
SET
  sub_segment_name = EXCLUDED.sub_segment_name,
  updated_at       = NOW(),
  deleted_at       = NULL,
  deleted_by       = NULL;

-- Projects (2 under Alpha, 1 under Beta — validates project dropdown)
INSERT INTO projects
  (project_id, project_name, sub_segment_id, created_by, created_at, updated_at, deleted_at, deleted_by)
VALUES
  (9010, 'Test Project - Phoenix', 9001, 'test_automation', NOW(), NOW(), NULL, NULL),
  (9011, 'Test Project - Atlas',   9001, 'test_automation', NOW(), NOW(), NULL, NULL),
  (9012, 'Test Project - Orion',   9002, 'test_automation', NOW(), NOW(), NULL, NULL)
ON CONFLICT (project_id) DO UPDATE
SET
  project_name    = EXCLUDED.project_name,
  sub_segment_id  = EXCLUDED.sub_segment_id,
  updated_at      = NOW(),
  deleted_at      = NULL,
  deleted_by      = NULL;

-- Teams (2 under Phoenix, 1 under Atlas, 1 under Orion)
INSERT INTO teams
  (team_id, team_name, project_id, created_by, created_at, updated_at, deleted_at, deleted_by)
VALUES
  (9020, 'Test Team - Automators', 9010, 'test_automation', NOW(), NOW(), NULL, NULL),
  (9021, 'Test Team - Validators', 9010, 'test_automation', NOW(), NOW(), NULL, NULL),
  (9022, 'Test Team - Explorers',  9011, 'test_automation', NOW(), NOW(), NULL, NULL),
  (9023, 'Test Team - Builders',   9012, 'test_automation', NOW(), NOW(), NULL, NULL)
ON CONFLICT (team_id) DO UPDATE
SET
  team_name  = EXCLUDED.team_name,
  project_id = EXCLUDED.project_id,
  updated_at = NOW(),
  deleted_at = NULL,
  deleted_by = NULL;

-- ============================================================
-- Org Structure smoke-test hierarchy  (IDs 9150-9181)
-- Used by:  e2e/tests/smoke/org-structure.spec.ts
-- Hierarchy: Digital (9150) → Web Platform (9160) → Portal v2 (9170) → Frontend/Backend Guild
--            Digital (9150) → Mobile Apps  (9161) → iOS App    (9171)
--            Operations (9151) → Cloud Ops (9162)
-- IDs chosen to avoid collision with employee/enrollment data (9001-9023)
-- ============================================================

-- Segments for Org Structure tests (upsert: restore if soft-deleted by a previous test run)
INSERT INTO segments
  (segment_id, segment_name, created_by, created_at, updated_at, deleted_at, deleted_by)
VALUES
  (9150, 'Digital',    'test_automation', NOW(), NOW(), NULL, NULL),
  (9151, 'Operations', 'test_automation', NOW(), NOW(), NULL, NULL)
ON CONFLICT (segment_id) DO UPDATE
SET
  segment_name = EXCLUDED.segment_name,
  updated_at   = NOW(),
  deleted_at   = NULL,
  deleted_by   = NULL;

-- Sub-Segments for Org Structure tests
INSERT INTO sub_segments
  (sub_segment_id, sub_segment_name, segment_id, created_by, created_at, updated_at, deleted_at, deleted_by)
VALUES
  (9160, 'Web Platform', 9150, 'test_automation', NOW(), NOW(), NULL, NULL),
  (9161, 'Mobile Apps',  9150, 'test_automation', NOW(), NOW(), NULL, NULL),
  (9162, 'Cloud Ops',    9151, 'test_automation', NOW(), NOW(), NULL, NULL)
ON CONFLICT (sub_segment_id) DO UPDATE
SET
  sub_segment_name = EXCLUDED.sub_segment_name,
  segment_id       = EXCLUDED.segment_id,
  updated_at       = NOW(),
  deleted_at       = NULL,
  deleted_by       = NULL;

-- Projects for Org Structure tests
INSERT INTO projects
  (project_id, project_name, sub_segment_id, created_by, created_at, updated_at, deleted_at, deleted_by)
VALUES
  (9170, 'Portal v2', 9160, 'test_automation', NOW(), NOW(), NULL, NULL),
  (9171, 'iOS App',   9161, 'test_automation', NOW(), NOW(), NULL, NULL)
ON CONFLICT (project_id) DO UPDATE
SET
  project_name   = EXCLUDED.project_name,
  sub_segment_id = EXCLUDED.sub_segment_id,
  updated_at     = NOW(),
  deleted_at     = NULL,
  deleted_by     = NULL;

-- Teams for Org Structure tests
INSERT INTO teams
  (team_id, team_name, project_id, created_by, created_at, updated_at, deleted_at, deleted_by)
VALUES
  (9180, 'Frontend Guild', 9170, 'test_automation', NOW(), NOW(), NULL, NULL),
  (9181, 'Backend Guild',  9170, 'test_automation', NOW(), NOW(), NULL, NULL)
ON CONFLICT (team_id) DO UPDATE
SET
  team_name  = EXCLUDED.team_name,
  project_id = EXCLUDED.project_id,
  updated_at = NOW(),
  deleted_at = NULL,
  deleted_by = NULL;


-- ============================================================
-- 2) ROLE CATALOG (job roles assigned to employees)
-- 12 roles covering enough variety to test:
--   - Role filter dropdown in Talent Finder
--   - Role mapping modal in Import Data
--   - Role dropdown in Employee Management drawer
-- ============================================================

INSERT INTO roles
  (role_id, role_name, role_description, created_by, created_at, updated_at, deleted_at, deleted_by)
VALUES
  (9030, 'Backend Engineer',    'Designs and builds server-side systems and APIs.',             'test_automation', NOW(), NOW(), NULL, NULL),
  (9031, 'Frontend Engineer',   'Builds user interfaces and client-side features.',             'test_automation', NOW(), NOW(), NULL, NULL),
  (9032, 'Full-Stack Engineer', 'Works across frontend and backend layers.',                    'test_automation', NOW(), NOW(), NULL, NULL),
  (9033, 'QA Engineer',         'Designs and executes manual and automated tests.',             'test_automation', NOW(), NOW(), NULL, NULL),
  (9034, 'DevOps Engineer',     'Manages CI/CD pipelines and cloud infrastructure.',            'test_automation', NOW(), NOW(), NULL, NULL),
  (9035, 'Engineering Manager', 'Leads engineering teams and delivery.',                        'test_automation', NOW(), NOW(), NULL, NULL),
  (9036, 'Product Manager',     'Owns product vision, roadmap and prioritisation.',             'test_automation', NOW(), NOW(), NULL, NULL),
  (9037, 'Scrum Master',        'Facilitates agile ceremonies and removes blockers.',           'test_automation', NOW(), NOW(), NULL, NULL),
  (9038, 'Solution Architect',  'Defines technical architecture across systems.',               'test_automation', NOW(), NOW(), NULL, NULL),
  (9039, 'Data Engineer',       'Builds and maintains data pipelines and warehouses.',          'test_automation', NOW(), NOW(), NULL, NULL),
  (9040, 'Tech Lead',           'Provides technical guidance and code quality oversight.',      'test_automation', NOW(), NOW(), NULL, NULL),
  (9041, 'Mobile Engineer',     'Develops iOS and Android mobile applications.',                'test_automation', NOW(), NOW(), NULL, NULL)
ON CONFLICT (role_id) DO UPDATE
SET
  role_name        = EXCLUDED.role_name,
  role_description = EXCLUDED.role_description,
  updated_at       = NOW(),
  deleted_at       = NULL,
  deleted_by       = NULL;


-- ============================================================
-- 3) SKILL TAXONOMY
-- 2 categories → 3 subcategories → 10 skills
-- Enough to validate:
--   - Tree expand/collapse in Skill Coverage
--   - Lazy-load of subcategories and skills
--   - Typeahead search in Talent Finder skill selector
--   - Proficiency breakdown chart in Skill Coverage detail
-- Insert order: categories → subcategories → skills → aliases
-- ============================================================

-- Categories
INSERT INTO skill_categories
  (category_id, category_name, category_description, created_by, created_at, updated_at, deleted_at, deleted_by)
VALUES
  (9050, 'Programming', 'Test seed — programming and development skills.', 'test_automation', NOW(), NOW(), NULL, NULL),
  (9051, 'Testing',     'Test seed — QA and test automation skills.',      'test_automation', NOW(), NOW(), NULL, NULL)
ON CONFLICT (category_id) DO UPDATE
SET
  category_name        = EXCLUDED.category_name,
  category_description = EXCLUDED.category_description,
  updated_at           = NOW(),
  deleted_at           = NULL,
  deleted_by           = NULL;


-- Subcategories
INSERT INTO skill_subcategories
  (subcategory_id, subcategory_name, subcategory_description, category_id, created_by, created_at, updated_at, deleted_at, deleted_by)
VALUES
  (9060, 'Frontend Dev',   'Test seed — UI and frontend engineering skills.', 9050, 'test_automation', NOW(), NOW(), NULL, NULL),
  (9061, 'Backend Dev',    'Test seed — server-side and API skills.',         9050, 'test_automation', NOW(), NOW(), NULL, NULL),
  (9062, 'Automation QA',  'Test seed — automation testing tools and skills.',9051, 'test_automation', NOW(), NOW(), NULL, NULL)
ON CONFLICT (subcategory_id) DO UPDATE
SET
  subcategory_name        = EXCLUDED.subcategory_name,
  subcategory_description = EXCLUDED.subcategory_description,
  category_id             = EXCLUDED.category_id,
  updated_at              = NOW(),
  deleted_at              = NULL,
  deleted_by              = NULL;



-- Skills (10 total — spread across 3 subcategories)
INSERT INTO skills
  (skill_id, skill_name, skill_description, subcategory_id, created_by, created_at, updated_at, deleted_at, deleted_by)
VALUES
  -- Frontend (subcategory 9060)
  (9070, 'JavaScript',  'JavaScript language fundamentals and ES6+.',  9060, 'test_automation', NOW(), NOW(), NULL, NULL),
  (9071, 'TypeScript',  'Type-safe superset of JavaScript.',           9060, 'test_automation', NOW(), NOW(), NULL, NULL),
  (9072, 'React',       'React library for building UIs.',             9060, 'test_automation', NOW(), NOW(), NULL, NULL),
  (9073, 'TailwindCSS', 'Utility-first CSS framework.',                9060, 'test_automation', NOW(), NOW(), NULL, NULL),

  -- Backend (subcategory 9061)
  (9074, 'Python',      'Python programming language.',                9061, 'test_automation', NOW(), NOW(), NULL, NULL),
  (9075, 'FastAPI',     'Python web framework for building APIs.',     9061, 'test_automation', NOW(), NOW(), NULL, NULL),
  (9076, 'PostgreSQL',  'Relational database system.',                 9061, 'test_automation', NOW(), NOW(), NULL, NULL),
  (9077, 'SQLAlchemy',  'Python ORM for database interactions.',       9061, 'test_automation', NOW(), NOW(), NULL, NULL),

  -- Automation QA (subcategory 9062)
  (9078, 'Playwright',  'Browser automation and E2E testing framework.',9062, 'test_automation', NOW(), NOW(), NULL, NULL),
  (9079, 'Test Design', 'Writing maintainable and reliable test cases.',9062, 'test_automation', NOW(), NOW(), NULL, NULL)
ON CONFLICT (skill_id) DO UPDATE
SET
  skill_name      = EXCLUDED.skill_name,
  skill_description = EXCLUDED.skill_description,
  subcategory_id  = EXCLUDED.subcategory_id,
  updated_at      = NOW(),
  deleted_at      = NULL,
  deleted_by      = NULL;

-- Skill Aliases
-- Prefixed with 'test_' to guarantee no collision with real data.
-- alias_text is GLOBALLY UNIQUE across the entire database.

INSERT INTO skill_aliases
  (alias_id, skill_id, alias_text, source, created_by, created_at, updated_at)
VALUES
  (9080, 9070, 'test_JS',       'seed', 'test_automation', NOW(), NOW()),
  (9081, 9071, 'test_TS',       'seed', 'test_automation', NOW(), NOW()),
  (9082, 9072, 'test_ReactJS',  'seed', 'test_automation', NOW(), NOW()),
  (9083, 9073, 'test_Tailwind', 'seed', 'test_automation', NOW(), NOW()),
  (9084, 9074, 'test_Py',       'seed', 'test_automation', NOW(), NOW()),
  (9085, 9075, 'test_FastAPI',  'seed', 'test_automation', NOW(), NOW()),
  (9086, 9078, 'test_PW',       'seed', 'test_automation', NOW(), NOW())
ON CONFLICT (alias_text) DO NOTHING;


-- ============================================================
-- 4) EMPLOYEES
--
-- ⚠️  READ THIS BEFORE RUNNING:
--
-- The ERD document does NOT list a 'zid' column but the
-- application requires ZID for search and employee management.
-- Run this query first to confirm the column name:
--
--   SELECT column_name FROM information_schema.columns
--   WHERE table_name = 'employees' ORDER BY ordinal_position;
--
-- If the column is named differently, update 'zid' below.
-- If 'zid' does NOT exist at all, remove it from the INSERT
-- and notify the dev team — the ERD document is incomplete.
--
-- 5 employees spread across 3 teams and 4 roles.
-- Enough to validate:
--   - Dashboard KPI counts (non-zero)
--   - Skill Coverage employee counts per skill
--   - Talent Finder search results and filters
--   - Employee Directory search by name and ZID
-- ============================================================
-- ============================================================
-- 4) EMPLOYEES
-- Columns per actual DB schema (ER diagram verified):
-- full_name, start_date_of_working — no hire_date, no is_manager
-- ============================================================

INSERT INTO employees
  (employee_id, zid, full_name, email,
   team_id, role_id, start_date_of_working,
   created_by, created_at, updated_at, deleted_at, deleted_by)
VALUES
  (9090, 'TEST-EMP-001', 'Alice Chen',   'test.alice@example.com', 9020, 9030, '2022-01-10', 'test_automation', NOW(), NOW(), NULL, NULL),
  (9091, 'TEST-EMP-002', 'Bob Sharma',   'test.bob@example.com',   9020, 9033, '2022-03-15', 'test_automation', NOW(), NOW(), NULL, NULL),
  (9092, 'TEST-EMP-003', 'Carol Nguyen', 'test.carol@example.com', 9021, 9031, '2021-11-01', 'test_automation', NOW(), NOW(), NULL, NULL),
  (9093, 'TEST-EMP-004', 'David Okafor', 'test.david@example.com', 9022, 9032, '2023-06-20', 'test_automation', NOW(), NOW(), NULL, NULL),
  (9094, 'TEST-EMP-005', 'Emma Patel',   'test.emma@example.com',  9023, 9035, '2020-08-05', 'test_automation', NOW(), NOW(), NULL, NULL)
ON CONFLICT (employee_id) DO UPDATE
SET
  zid                  = EXCLUDED.zid,
  full_name            = EXCLUDED.full_name,
  email                = EXCLUDED.email,
  team_id              = EXCLUDED.team_id,
  role_id              = EXCLUDED.role_id,
  start_date_of_working = EXCLUDED.start_date_of_working,
  updated_at           = NOW(),
  deleted_at           = NULL,
  deleted_by           = NULL;


-- ============================================================
-- 5) EMPLOYEE SKILLS
-- Columns per actual DB schema (ER diagram verified):
-- emp_skill_id (PK), years_experience, last_used,
-- started_learning_from, certification, comment,
-- interest_level, last_updated
-- No assessed_date, no assessor columns.
-- Proficiency levels: 1=Novice 2=Adv.Beginner 3=Competent
--                     4=Proficient 5=Expert
-- ============================================================

INSERT INTO employee_skills
  (emp_skill_id, employee_id, skill_id, proficiency_level_id,
   years_experience, last_used, started_learning_from,
   certification, comment, interest_level,
   created_by, created_at, updated_at, deleted_at, deleted_by)
VALUES
  -- Alice (9090): JavaScript=Proficient, TypeScript=Competent
  (9100, 9090, 9070, 4, 3, '2024-01-01', '2021-01-01', NULL, NULL, NULL, 'test_automation', NOW(), NOW(), NULL, NULL),
  (9101, 9090, 9071, 3, 2, '2024-01-01', '2022-01-01', NULL, NULL, NULL, 'test_automation', NOW(), NOW(), NULL, NULL),

  -- Bob (9091): Playwright=Expert, Test Design=Proficient
  (9102, 9091, 9078, 5, 4, '2024-02-01', '2020-01-01', NULL, NULL, NULL, 'test_automation', NOW(), NOW(), NULL, NULL),
  (9103, 9091, 9079, 4, 3, '2024-02-01', '2021-01-01', NULL, NULL, NULL, 'test_automation', NOW(), NOW(), NULL, NULL),

  -- Carol (9092): JavaScript=Advanced Beginner, React=Proficient
  (9104, 9092, 9070, 2, 1, '2024-01-20', '2023-01-01', NULL, NULL, NULL, 'test_automation', NOW(), NOW(), NULL, NULL),
  (9105, 9092, 9072, 4, 3, '2024-01-20', '2021-06-01', NULL, NULL, NULL, 'test_automation', NOW(), NOW(), NULL, NULL),

  -- David (9093): Python=Competent, FastAPI=Proficient
  (9106, 9093, 9074, 3, 2, '2024-03-10', '2022-03-01', NULL, NULL, NULL, 'test_automation', NOW(), NOW(), NULL, NULL),
  (9107, 9093, 9075, 4, 2, '2024-03-10', '2022-06-01', NULL, NULL, NULL, 'test_automation', NOW(), NOW(), NULL, NULL),

  -- Emma (9094): JavaScript=Expert, React=Expert
  (9108, 9094, 9070, 5, 6, '2023-12-01', '2018-01-01', NULL, NULL, NULL, 'test_automation', NOW(), NOW(), NULL, NULL),
  (9109, 9094, 9072, 5, 5, '2023-12-01', '2019-01-01', NULL, NULL, NULL, 'test_automation', NOW(), NOW(), NULL, NULL)

ON CONFLICT (emp_skill_id) DO NOTHING;

COMMIT;

-- ============================================================
-- SEED SUMMARY
-- ============================================================
-- Segment       : 1   (DTS — matches featureFlags.js)
-- Sub-segments  : 2   (IDs 9001–9002, under segment 1)
-- Projects      : 3   (IDs 9010–9012)
-- Teams         : 4   (IDs 9020–9023)
-- Roles         : 12  (IDs 9030–9041)
-- Skill Categories   : 2  (IDs 9050–9051)
-- Skill Subcategories: 3  (IDs 9060–9062)
-- Skills        : 10  (IDs 9070–9079)
-- Skill Aliases : 7   (IDs 9080–9086)
-- Employees     : 5   (IDs 9090–9094)
-- Employee Skills: 10 (IDs 9100–9109)
-- ============================================================
-- To clean up ALL test data run cleanup.sql
-- ============================================================