export const mockEmployees = [
  { 
    id: 1, 
    name: "Sarah Johnson", 
    role: "Senior Frontend Developer", 
    subSegment: "Audiology", 
    project: "Patient Portal", 
    team: "Web Team",
    email: "sarah.johnson@siemens.com",
    location: "Munich, Germany",
    yearsExperience: 8,
    matchedCriteria: "4/6", 
    lastUpdated: "2024-12-01", 
    skills: [
      { skillId: 1, name: "ReactJS", proficiency: 5, category: "Frontend", years: 5, lastUsed: 2024, certified: true, lastUpdated: "2024-11-15" },
      { skillId: 2, name: "Python FastAPI", proficiency: 4, category: "Backend", years: 3, lastUsed: 2024, certified: false, lastUpdated: "2024-10-20" },
      { skillId: 3, name: "TypeScript", proficiency: 5, category: "Programming", years: 4, lastUsed: 2024, certified: false, lastUpdated: "2024-12-01" }
    ]
  },  { 
    id: 2, 
    name: "Michael Chen", 
    role: "Full Stack Engineer", 
    subSegment: "Digital Health",
    project: "Cloud Platform", 
    team: "Backend Team",
    email: "michael.chen@siemens.com",
    location: "Berlin, Germany", 
    yearsExperience: 6,
    matchedCriteria: "5/6", 
    lastUpdated: "2024-11-28", 
    skills: [
      { skillId: 4, name: "ReactJS", proficiency: 4, category: "Frontend", years: 3, lastUsed: 2024, certified: true, lastUpdated: "2024-11-20" },
      { skillId: 5, name: "Node.js", proficiency: 5, category: "Backend", years: 5, lastUsed: 2024, certified: true, lastUpdated: "2024-11-25" },
      { skillId: 6, name: "AWS", proficiency: 4, category: "Cloud", years: 3, lastUsed: 2023, certified: false, lastUpdated: "2024-10-15" }
    ]
  },
  { 
    id: 3, 
    name: "Emily Rodriguez", 
    role: "Cloud Engineer", 
    subSegment: "Audiology", 
    project: "Infrastructure", 
    team: "DevOps Team",
    email: "emily.rodriguez@siemens.com",
    location: "Princeton, USA",
    yearsExperience: 7,    matchedCriteria: "6/6", 
    lastUpdated: "2024-12-05", 
    skills: [
      { skillId: 7, name: "AWS", proficiency: 5, category: "Cloud", years: 6, lastUsed: 2024, certified: true, lastUpdated: "2024-12-01" },
      { skillId: 8, name: "Kubernetes", proficiency: 5, category: "DevOps", years: 4, lastUsed: 2024, certified: true, lastUpdated: "2024-11-28" },
      { skillId: 9, name: "Docker", proficiency: 5, category: "DevOps", years: 5, lastUsed: 2024, certified: false, lastUpdated: "2024-11-30" }
    ]
  },
  { 
    id: 4, 
    name: "David Kim", 
    role: "Backend Developer", 
    subSegment: "Digital Health", 
    project: "API Services", 
    team: "Backend Team",
    email: "david.kim@siemens.com",
    location: "Munich, Germany",
    yearsExperience: 5,    matchedCriteria: "3/6", 
    lastUpdated: "2024-11-15", 
    skills: [
      { skillId: 10, name: "Java", proficiency: 5, category: "Programming", years: 7, lastUsed: 2024, certified: true, lastUpdated: "2024-11-10" },
      { skillId: 11, name: "Spring Boot", proficiency: 5, category: "Backend", years: 6, lastUsed: 2024, certified: false, lastUpdated: "2024-11-12" },
      { skillId: 12, name: "PostgreSQL", proficiency: 4, category: "Database", years: 4, lastUsed: 2024, certified: false, lastUpdated: "2024-11-08" }
    ]
  },
  { 
    id: 5, 
    name: "Lisa Wang", 
    role: "Frontend Developer", 
    subSegment: "Diagnostics", 
    project: "Mobile App", 
    team: "Frontend Team",
    email: "lisa.wang@siemens.com",
    location: "Shanghai, China",
    yearsExperience: 4,
    matchedCriteria: "5/6", 
    lastUpdated: "2024-12-10", 
    skills: [
      { skillId: 13, name: "ReactJS", proficiency: 4, category: "Frontend", years: 3, lastUsed: 2024, certified: true, lastUpdated: "2024-12-05" },
      { skillId: 14, name: "Vue.js", proficiency: 5, category: "Frontend", years: 4, lastUsed: 2024, certified: false, lastUpdated: "2024-12-08" },      { skillId: 15, name: "TypeScript", proficiency: 4, category: "Programming", years: 2, lastUsed: 2024, certified: false, lastUpdated: "2024-12-03" }
    ]
  }
];

export default mockEmployees;
