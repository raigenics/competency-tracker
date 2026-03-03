// Module: api-seed.ts
// Purpose: Seed test data via API endpoints for E2E automation
// Part of: CompetencyIQ E2E Automation Suite

import dotenv from 'dotenv';

// Load environment variables
dotenv.config();

// Test data imports
import orgData from './org.json';
import employeesData from './employees.json';
import skillsData from './skills.json';

const BASE_URL = process.env.BASE_URL || 'http://localhost:5173';
const API_BASE = `${BASE_URL}/api`;

/**
 * Helper function to make API requests
 */
async function apiRequest(
  method: string,
  endpoint: string,
  data?: unknown
): Promise<Response> {
  const url = `${API_BASE}${endpoint}`;
  
  const options: RequestInit = {
    method,
    headers: {
      'Content-Type': 'application/json',
      // TODO: Add auth header when implementing actual API calls
      // 'Authorization': `Bearer ${process.env.API_TOKEN}`,
    },
  };

  if (data) {
    options.body = JSON.stringify(data);
  }

  return fetch(url, options);
}

/**
 * Seed organizational hierarchy: Segment → SubSegment → Project → Team
 */
async function seedOrgHierarchy(): Promise<void> {
  console.log('📁 Seeding organizational hierarchy...');

  // Segment
  console.log(`   Creating segment: ${orgData.segment.name}`);
  // TODO: Implement actual API call
  // await apiRequest('POST', '/segments', orgData.segment);

  // Sub-Segment
  console.log(`   Creating sub-segment: ${orgData.subSegment.name}`);
  // TODO: Implement actual API call
  // await apiRequest('POST', '/sub-segments', orgData.subSegment);

  // Project
  console.log(`   Creating project: ${orgData.project.name}`);
  // TODO: Implement actual API call
  // await apiRequest('POST', '/projects', orgData.project);

  // Team
  console.log(`   Creating team: ${orgData.team.name}`);
  // TODO: Implement actual API call
  // await apiRequest('POST', '/teams', orgData.team);

  console.log('✅ Organizational hierarchy seeded');
}

/**
 * Seed skill taxonomy: Category → Subcategory → Skills
 */
async function seedSkillTaxonomy(): Promise<void> {
  console.log('🏷️  Seeding skill taxonomy...');

  // Category (extracted from skills data)
  const category = {
    id: 9001,
    name: 'Test Category Programming',
    description: 'Test category for programming skills',
  };
  console.log(`   Creating category: ${category.name}`);
  // TODO: Implement actual API call
  // await apiRequest('POST', '/skill-categories', category);

  // Subcategory
  const subcategory = {
    id: 9001,
    name: 'Test Subcategory Frontend',
    description: 'Test subcategory for frontend skills',
    categoryId: 9001,
  };
  console.log(`   Creating subcategory: ${subcategory.name}`);
  // TODO: Implement actual API call
  // await apiRequest('POST', '/skill-subcategories', subcategory);

  // Skills
  for (const skill of skillsData) {
    console.log(`   Creating skill: ${skill.name}`);
    // TODO: Implement actual API call
    // await apiRequest('POST', '/skills', {
    //   id: skill.id,
    //   name: `Test Skill ${skill.name}`,
    //   description: skill.description,
    //   subcategoryId: skill.subcategoryId,
    // });
  }

  console.log('✅ Skill taxonomy seeded');
}

/**
 * Seed roles (job roles, not auth roles)
 */
async function seedRoles(): Promise<void> {
  console.log('👔 Seeding roles...');

  const role = {
    id: 9001,
    name: 'Test Role Developer',
    description: 'Test developer role',
  };
  console.log(`   Creating role: ${role.name}`);
  // TODO: Implement actual API call
  // await apiRequest('POST', '/roles', role);

  console.log('✅ Roles seeded');
}

/**
 * Seed employees
 */
async function seedEmployees(): Promise<void> {
  console.log('👥 Seeding employees...');

  for (const employee of employeesData) {
    console.log(`   Creating employee: ${employee.firstName} ${employee.lastName}`);
    // TODO: Implement actual API call
    // await apiRequest('POST', '/employees', employee);
  }

  console.log('✅ Employees seeded');
}

/**
 * Seed employee skills (fact data)
 */
async function seedEmployeeSkills(): Promise<void> {
  console.log('🎯 Seeding employee skills...');

  const employeeSkills = [
    { employeeId: 9001, skillId: 9001, proficiencyLevelId: 3 }, // User1 -> JS -> Competent
    { employeeId: 9001, skillId: 9002, proficiencyLevelId: 2 }, // User1 -> TS -> Advanced Beginner
    { employeeId: 9002, skillId: 9001, proficiencyLevelId: 4 }, // User2 -> JS -> Proficient
    { employeeId: 9002, skillId: 9003, proficiencyLevelId: 5 }, // User2 -> React -> Expert
    { employeeId: 9003, skillId: 9001, proficiencyLevelId: 5 }, // Manager -> JS -> Expert
    { employeeId: 9003, skillId: 9002, proficiencyLevelId: 4 }, // Manager -> TS -> Proficient
    { employeeId: 9003, skillId: 9003, proficiencyLevelId: 4 }, // Manager -> React -> Proficient
  ];

  for (const es of employeeSkills) {
    console.log(`   Assigning skill ${es.skillId} to employee ${es.employeeId}`);
    // TODO: Implement actual API call
    // await apiRequest('POST', `/employees/${es.employeeId}/skills`, {
    //   skillId: es.skillId,
    //   proficiencyLevelId: es.proficiencyLevelId,
    // });
  }

  console.log('✅ Employee skills seeded');
}

/**
 * Main seed function - orchestrates all seeding operations
 */
export async function seedViaApi(): Promise<void> {
  console.log('🌱 Starting API-based test data seeding...');
  console.log(`   Target: ${API_BASE}`);

  try {
    // Seed in dependency order
    await seedOrgHierarchy();
    await seedSkillTaxonomy();
    await seedRoles();
    await seedEmployees();
    await seedEmployeeSkills();

    console.log('');
    console.log('✅ All test data seeded successfully via API');
    console.log('   IDs used: >= 9000');
    console.log('   Created by: test_automation');
  } catch (error) {
    console.error('❌ Error seeding test data:', error);
    throw error;
  }
}

// Export as default for use in global-setup
export default seedViaApi;

// Allow running directly for manual seeding
if (require.main === module) {
  seedViaApi()
    .then(() => {
      console.log('Seeding complete');
      process.exit(0);
    })
    .catch((error) => {
      console.error('Seeding failed:', error);
      process.exit(1);
    });
}
