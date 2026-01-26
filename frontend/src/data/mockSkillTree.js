export const mockSkillTree = [
  {
    id: 1,
    name: "Web Development",
    subcategories: [
      {
        id: 1,
        name: "Frontend Frameworks",
        skills: [
          { id: 1, name: "ReactJS", description: "Modern JavaScript library for building user interfaces", isCore: true },
          { id: 2, name: "Angular", description: "TypeScript-based web application framework", isCore: false },
          { id: 3, name: "Vue.js", description: "Progressive JavaScript framework", isCore: false },
          { id: 4, name: "Svelte", description: "Compile-time JavaScript framework", isCore: false }
        ]
      },
      {
        id: 2,
        name: "Backend Frameworks",
        skills: [
          { id: 5, name: "Node.js", description: "JavaScript runtime for server-side development", isCore: true },
          { id: 6, name: "Python FastAPI", description: "Modern Python web framework for APIs", isCore: true },
          { id: 7, name: "Django", description: "High-level Python web framework", isCore: false },
          { id: 8, name: "Express.js", description: "Minimal Node.js web application framework", isCore: false }
        ]
      },
      {
        id: 3,
        name: "Styling",
        skills: [
          { id: 9, name: "CSS", description: "Cascading Style Sheets for web styling", isCore: true },
          { id: 10, name: "SASS", description: "CSS preprocessor with additional features", isCore: false },
          { id: 11, name: "Tailwind CSS", description: "Utility-first CSS framework", isCore: false }
        ]
      }
    ]
  },
  {
    id: 2,
    name: "Cloud Computing",
    subcategories: [
      {
        id: 4,
        name: "Cloud Platforms",
        skills: [
          { id: 12, name: "AWS", description: "Amazon Web Services cloud platform", isCore: true },
          { id: 13, name: "Azure", description: "Microsoft cloud platform", isCore: false },
          { id: 14, name: "Google Cloud Platform", description: "Google cloud platform", isCore: false }
        ]
      },
      {
        id: 5,
        name: "Container Orchestration",
        skills: [
          { id: 15, name: "Kubernetes", description: "Container orchestration system", isCore: true },
          { id: 16, name: "Docker Swarm", description: "Docker's native clustering solution", isCore: false }
        ]
      }
    ]
  },
  {
    id: 3,
    name: "Programming Languages",
    subcategories: [
      {
        id: 6,
        name: "Modern Languages",
        skills: [
          { id: 17, name: "JavaScript", description: "Dynamic programming language for web development", isCore: true },
          { id: 18, name: "TypeScript", description: "Typed superset of JavaScript", isCore: true },
          { id: 19, name: "Python", description: "High-level programming language", isCore: true },
          { id: 20, name: "Java", description: "Object-oriented programming language", isCore: false }
        ]
      }
    ]
  },
  {
    id: 4,
    name: "Databases",
    subcategories: [
      {
        id: 7,
        name: "SQL Databases",
        skills: [
          { id: 21, name: "PostgreSQL", description: "Advanced open-source relational database", isCore: true },
          { id: 22, name: "MySQL", description: "Popular open-source relational database", isCore: false },
          { id: 23, name: "SQL Server", description: "Microsoft relational database system", isCore: false }
        ]
      },
      {
        id: 8,
        name: "NoSQL Databases",
        skills: [
          { id: 24, name: "MongoDB", description: "Document-oriented NoSQL database", isCore: false },
          { id: 25, name: "Redis", description: "In-memory data structure store", isCore: false }
        ]
      }
    ]
  }
];

export default mockSkillTree;
