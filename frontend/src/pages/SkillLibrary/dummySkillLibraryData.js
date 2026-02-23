/**
 * Dummy data for Skill Library page
 * Matches the exact data structure from the provided HTML wireframe
 */
export const dummySkillLibraryData = [
  {
    id: "cat-ai",
    name: "AI & Developer Productivity",
    description: "Capabilities related to AI-driven productivity, developer tooling and LLM usage.",
    subcategories: [
      { 
        id: "sub-agents", 
        name: "AI Agents & Orchestration Frameworks", 
        skills: ["LangChain", "LangGraph", "n8n", "AutoGen", "CrewAI"] 
      },
      { 
        id: "sub-coding", 
        name: "AI Coding Assistants", 
        skills: ["GitHub Copilot", "Cursor", "CodeWhisperer", "ChatGPT"] 
      },
      { 
        id: "sub-rag", 
        name: "Retrieval-Augmented Generation (RAG)", 
        skills: ["Embeddings", "Vector DBs", "Chunking", "Hybrid Search"] 
      },
    ]
  },
  {
    id: "cat-backend",
    name: "Backend Development",
    description: "Server-side development skills, API design, integration patterns.",
    subcategories: [
      { 
        id: "sub-api", 
        name: "API Engineering", 
        skills: ["REST", "GraphQL", "FastAPI", "gRPC"] 
      },
      { 
        id: "sub-db", 
        name: "Databases & Data", 
        skills: ["PostgreSQL", "SQLAlchemy", "Redis", "MongoDB"] 
      },
    ]
  },
  {
    id: "cat-frontend",
    name: "Frontend Development",
    description: "Web UI development, patterns, performance and accessibility.",
    subcategories: [
      { 
        id: "sub-react", 
        name: "React Ecosystem", 
        skills: ["React", "Vite", "React Router", "Zustand"] 
      },
      { 
        id: "sub-ui", 
        name: "UI Engineering", 
        skills: ["CSS", "Tailwind", "Accessibility", "Design Systems"] 
      },
    ]
  }
];
