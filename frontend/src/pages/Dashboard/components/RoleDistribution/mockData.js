/**
 * Mock data for Role Distribution component.
 * Each context level has its own mock dataset.
 */

// SEGMENT level (showing Sub-Segments)
export const SEGMENT_DATA = {
  rows: [
    {
      name: 'ADT',
      total: 54,
      roles: [
        { roleName: 'Frontend Dev', count: 12 },
        { roleName: 'Backend Dev', count: 10 },
        { roleName: 'Full Stack', count: 8 },
        { roleName: 'Cloud Eng', count: 7 },
        { roleName: 'DevOps', count: 6 },
        { roleName: 'QA Engineer', count: 5 },
        { roleName: 'Data Engineer', count: 4 },
        { roleName: 'Product Owner', count: 2 },
      ],
    },
    {
      name: 'AU',
      total: 65,
      roles: [
        { roleName: 'Frontend Dev', count: 18 },
        { roleName: 'Backend Dev', count: 15 },
        { roleName: 'Full Stack', count: 11 },
        { roleName: 'Cloud Eng', count: 8 },
        { roleName: 'DevOps', count: 6 },
        { roleName: 'QA Engineer', count: 4 },
        { roleName: 'Data Engineer', count: 2 },
        { roleName: 'Product Owner', count: 1 },
      ],
    },
    {
      name: 'eBiz',
      total: 37,
      roles: [
        { roleName: 'Backend Dev', count: 9 },
        { roleName: 'Frontend Dev', count: 7 },
        { roleName: 'Full Stack', count: 6 },
        { roleName: 'Cloud Eng', count: 5 },
        { roleName: 'DevOps', count: 4 },
        { roleName: 'QA Engineer', count: 3 },
        { roleName: 'Data Engineer', count: 2 },
        { roleName: 'Product Owner', count: 1 },
      ],
    },
    {
      name: 'eCom',
      total: 68,
      roles: [
        { roleName: 'Frontend Dev', count: 21 },
        { roleName: 'Backend Dev', count: 14 },
        { roleName: 'Full Stack', count: 11 },
        { roleName: 'Cloud Eng', count: 8 },
        { roleName: 'DevOps', count: 6 },
        { roleName: 'QA Engineer', count: 4 },
        { roleName: 'Data Engineer', count: 2 },
        { roleName: 'Product Owner', count: 1 },
        { roleName: 'Eng Manager', count: 1 },
      ],
    },
    {
      name: 'DP OPS',
      total: 26,
      roles: [
        { roleName: 'Data Engineer', count: 6 },
        { roleName: 'Backend Dev', count: 5 },
        { roleName: 'Cloud Eng', count: 5 },
        { roleName: 'Frontend Dev', count: 4 },
        { roleName: 'DevOps', count: 3 },
        { roleName: 'QA Engineer', count: 2 },
        { roleName: 'Product Owner', count: 1 },
      ],
    },
  ],
};

// SUB_SEGMENT level (showing Projects within a Sub-Segment)
export const SUB_SEGMENT_DATA = {
  ADT: {
    rows: [
      {
        name: 'Aspire',
        total: 22,
        roles: [
          { roleName: 'Frontend Dev', count: 5 },
          { roleName: 'Backend Dev', count: 4 },
          { roleName: 'Full Stack', count: 3 },
          { roleName: 'Cloud Eng', count: 3 },
          { roleName: 'DevOps', count: 3 },
          { roleName: 'QA Engineer', count: 2 },
          { roleName: 'Data Engineer', count: 1 },
          { roleName: 'Product Owner', count: 1 },
        ],
      },
      {
        name: 'Phoenix',
        total: 18,
        roles: [
          { roleName: 'Backend Dev', count: 4 },
          { roleName: 'Frontend Dev', count: 4 },
          { roleName: 'Full Stack', count: 3 },
          { roleName: 'Cloud Eng', count: 2 },
          { roleName: 'DevOps', count: 2 },
          { roleName: 'QA Engineer', count: 2 },
          { roleName: 'Data Engineer', count: 1 },
        ],
      },
      {
        name: 'Atlas',
        total: 14,
        roles: [
          { roleName: 'Frontend Dev', count: 3 },
          { roleName: 'Backend Dev', count: 2 },
          { roleName: 'Full Stack', count: 2 },
          { roleName: 'Cloud Eng', count: 2 },
          { roleName: 'DevOps', count: 1 },
          { roleName: 'QA Engineer', count: 1 },
          { roleName: 'Data Engineer', count: 2 },
          { roleName: 'Product Owner', count: 1 },
        ],
      },
    ],
  },
  AU: {
    rows: [
      {
        name: 'Bolt',
        total: 28,
        roles: [
          { roleName: 'Frontend Dev', count: 8 },
          { roleName: 'Backend Dev', count: 6 },
          { roleName: 'Full Stack', count: 5 },
          { roleName: 'Cloud Eng', count: 4 },
          { roleName: 'DevOps', count: 2 },
          { roleName: 'QA Engineer', count: 2 },
          { roleName: 'Product Owner', count: 1 },
        ],
      },
      {
        name: 'Surge',
        total: 37,
        roles: [
          { roleName: 'Frontend Dev', count: 10 },
          { roleName: 'Backend Dev', count: 9 },
          { roleName: 'Full Stack', count: 6 },
          { roleName: 'Cloud Eng', count: 4 },
          { roleName: 'DevOps', count: 4 },
          { roleName: 'QA Engineer', count: 2 },
          { roleName: 'Data Engineer', count: 2 },
        ],
      },
    ],
  },
  eBiz: {
    rows: [
      {
        name: 'Nexus',
        total: 20,
        roles: [
          { roleName: 'Backend Dev', count: 5 },
          { roleName: 'Frontend Dev', count: 4 },
          { roleName: 'Full Stack', count: 3 },
          { roleName: 'Cloud Eng', count: 3 },
          { roleName: 'DevOps', count: 2 },
          { roleName: 'QA Engineer', count: 2 },
          { roleName: 'Data Engineer', count: 1 },
        ],
      },
      {
        name: 'Vertex',
        total: 17,
        roles: [
          { roleName: 'Backend Dev', count: 4 },
          { roleName: 'Frontend Dev', count: 3 },
          { roleName: 'Full Stack', count: 3 },
          { roleName: 'Cloud Eng', count: 2 },
          { roleName: 'DevOps', count: 2 },
          { roleName: 'QA Engineer', count: 1 },
          { roleName: 'Data Engineer', count: 1 },
          { roleName: 'Product Owner', count: 1 },
        ],
      },
    ],
  },
  eCom: {
    rows: [
      {
        name: 'Prism',
        total: 35,
        roles: [
          { roleName: 'Frontend Dev', count: 11 },
          { roleName: 'Backend Dev', count: 7 },
          { roleName: 'Full Stack', count: 6 },
          { roleName: 'Cloud Eng', count: 4 },
          { roleName: 'DevOps', count: 3 },
          { roleName: 'QA Engineer', count: 2 },
          { roleName: 'Data Engineer', count: 1 },
          { roleName: 'Product Owner', count: 1 },
        ],
      },
      {
        name: 'Catalyst',
        total: 33,
        roles: [
          { roleName: 'Frontend Dev', count: 10 },
          { roleName: 'Backend Dev', count: 7 },
          { roleName: 'Full Stack', count: 5 },
          { roleName: 'Cloud Eng', count: 4 },
          { roleName: 'DevOps', count: 3 },
          { roleName: 'QA Engineer', count: 2 },
          { roleName: 'Data Engineer', count: 1 },
          { roleName: 'Eng Manager', count: 1 },
        ],
      },
    ],
  },
  'DP OPS': {
    rows: [
      {
        name: 'DataCore',
        total: 14,
        roles: [
          { roleName: 'Data Engineer', count: 4 },
          { roleName: 'Backend Dev', count: 3 },
          { roleName: 'Cloud Eng', count: 3 },
          { roleName: 'DevOps', count: 2 },
          { roleName: 'QA Engineer', count: 1 },
          { roleName: 'Product Owner', count: 1 },
        ],
      },
      {
        name: 'StreamOps',
        total: 12,
        roles: [
          { roleName: 'Data Engineer', count: 2 },
          { roleName: 'Backend Dev', count: 2 },
          { roleName: 'Cloud Eng', count: 2 },
          { roleName: 'Frontend Dev', count: 4 },
          { roleName: 'DevOps', count: 1 },
          { roleName: 'QA Engineer', count: 1 },
        ],
      },
    ],
  },
};

// PROJECT level (showing Teams within a Project)
export const PROJECT_DATA = {
  Aspire: {
    rows: [
      {
        name: 'Team Alpha',
        total: 8,
        roles: [
          { roleName: 'Frontend Dev', count: 2 },
          { roleName: 'Backend Dev', count: 2 },
          { roleName: 'Full Stack', count: 1 },
          { roleName: 'Cloud Eng', count: 1 },
          { roleName: 'DevOps', count: 1 },
          { roleName: 'QA Engineer', count: 1 },
        ],
      },
      {
        name: 'Team Beta',
        total: 7,
        roles: [
          { roleName: 'Frontend Dev', count: 2 },
          { roleName: 'Backend Dev', count: 1 },
          { roleName: 'Full Stack', count: 1 },
          { roleName: 'Cloud Eng', count: 1 },
          { roleName: 'DevOps', count: 1 },
          { roleName: 'Data Engineer', count: 1 },
        ],
      },
      {
        name: 'Team Gamma',
        total: 7,
        roles: [
          { roleName: 'Frontend Dev', count: 1 },
          { roleName: 'Backend Dev', count: 1 },
          { roleName: 'Full Stack', count: 1 },
          { roleName: 'Cloud Eng', count: 1 },
          { roleName: 'DevOps', count: 1 },
          { roleName: 'QA Engineer', count: 1 },
          { roleName: 'Product Owner', count: 1 },
        ],
      },
    ],
  },
  Phoenix: {
    rows: [
      {
        name: 'Core Team',
        total: 10,
        roles: [
          { roleName: 'Backend Dev', count: 3 },
          { roleName: 'Frontend Dev', count: 2 },
          { roleName: 'Full Stack', count: 2 },
          { roleName: 'Cloud Eng', count: 1 },
          { roleName: 'DevOps', count: 1 },
          { roleName: 'QA Engineer', count: 1 },
        ],
      },
      {
        name: 'Support Team',
        total: 8,
        roles: [
          { roleName: 'Frontend Dev', count: 2 },
          { roleName: 'Backend Dev', count: 1 },
          { roleName: 'Full Stack', count: 1 },
          { roleName: 'Cloud Eng', count: 1 },
          { roleName: 'DevOps', count: 1 },
          { roleName: 'QA Engineer', count: 1 },
          { roleName: 'Data Engineer', count: 1 },
        ],
      },
    ],
  },
  Atlas: {
    rows: [
      {
        name: 'Engineering',
        total: 9,
        roles: [
          { roleName: 'Frontend Dev', count: 2 },
          { roleName: 'Backend Dev', count: 2 },
          { roleName: 'Full Stack', count: 2 },
          { roleName: 'Cloud Eng', count: 1 },
          { roleName: 'Data Engineer', count: 1 },
          { roleName: 'QA Engineer', count: 1 },
        ],
      },
      {
        name: 'Platform',
        total: 5,
        roles: [
          { roleName: 'Frontend Dev', count: 1 },
          { roleName: 'Cloud Eng', count: 1 },
          { roleName: 'DevOps', count: 1 },
          { roleName: 'Data Engineer', count: 1 },
          { roleName: 'Product Owner', count: 1 },
        ],
      },
    ],
  },
  // Default projects for other sub-segments
  Bolt: {
    rows: [
      {
        name: 'Development',
        total: 15,
        roles: [
          { roleName: 'Frontend Dev', count: 5 },
          { roleName: 'Backend Dev', count: 4 },
          { roleName: 'Full Stack', count: 3 },
          { roleName: 'Cloud Eng', count: 2 },
          { roleName: 'QA Engineer', count: 1 },
        ],
      },
      {
        name: 'Integration',
        total: 13,
        roles: [
          { roleName: 'Frontend Dev', count: 3 },
          { roleName: 'Backend Dev', count: 2 },
          { roleName: 'Full Stack', count: 2 },
          { roleName: 'Cloud Eng', count: 2 },
          { roleName: 'DevOps', count: 2 },
          { roleName: 'QA Engineer', count: 1 },
          { roleName: 'Product Owner', count: 1 },
        ],
      },
    ],
  },
  Surge: {
    rows: [
      {
        name: 'Core Services',
        total: 20,
        roles: [
          { roleName: 'Frontend Dev', count: 6 },
          { roleName: 'Backend Dev', count: 5 },
          { roleName: 'Full Stack', count: 3 },
          { roleName: 'Cloud Eng', count: 2 },
          { roleName: 'DevOps', count: 2 },
          { roleName: 'QA Engineer', count: 1 },
          { roleName: 'Data Engineer', count: 1 },
        ],
      },
      {
        name: 'API Team',
        total: 17,
        roles: [
          { roleName: 'Frontend Dev', count: 4 },
          { roleName: 'Backend Dev', count: 4 },
          { roleName: 'Full Stack', count: 3 },
          { roleName: 'Cloud Eng', count: 2 },
          { roleName: 'DevOps', count: 2 },
          { roleName: 'QA Engineer', count: 1 },
          { roleName: 'Data Engineer', count: 1 },
        ],
      },
    ],
  },
  Nexus: {
    rows: [
      { name: 'Feature Squad', total: 12, roles: [
        { roleName: 'Backend Dev', count: 3 },
        { roleName: 'Frontend Dev', count: 3 },
        { roleName: 'Full Stack', count: 2 },
        { roleName: 'Cloud Eng', count: 2 },
        { roleName: 'DevOps', count: 1 },
        { roleName: 'QA Engineer', count: 1 },
      ]},
      { name: 'Infra Squad', total: 8, roles: [
        { roleName: 'Backend Dev', count: 2 },
        { roleName: 'Frontend Dev', count: 1 },
        { roleName: 'Full Stack', count: 1 },
        { roleName: 'Cloud Eng', count: 1 },
        { roleName: 'DevOps', count: 1 },
        { roleName: 'QA Engineer', count: 1 },
        { roleName: 'Data Engineer', count: 1 },
      ]},
    ],
  },
  Vertex: {
    rows: [
      { name: 'Backend Squad', total: 10, roles: [
        { roleName: 'Backend Dev', count: 3 },
        { roleName: 'Frontend Dev', count: 2 },
        { roleName: 'Full Stack', count: 2 },
        { roleName: 'Cloud Eng', count: 1 },
        { roleName: 'DevOps', count: 1 },
        { roleName: 'QA Engineer', count: 1 },
      ]},
      { name: 'Frontend Squad', total: 7, roles: [
        { roleName: 'Backend Dev', count: 1 },
        { roleName: 'Frontend Dev', count: 1 },
        { roleName: 'Full Stack', count: 1 },
        { roleName: 'Cloud Eng', count: 1 },
        { roleName: 'DevOps', count: 1 },
        { roleName: 'Data Engineer', count: 1 },
        { roleName: 'Product Owner', count: 1 },
      ]},
    ],
  },
  Prism: {
    rows: [
      { name: 'UI Team', total: 18, roles: [
        { roleName: 'Frontend Dev', count: 6 },
        { roleName: 'Backend Dev', count: 4 },
        { roleName: 'Full Stack', count: 3 },
        { roleName: 'Cloud Eng', count: 2 },
        { roleName: 'DevOps', count: 2 },
        { roleName: 'QA Engineer', count: 1 },
      ]},
      { name: 'Backend Team', total: 17, roles: [
        { roleName: 'Frontend Dev', count: 5 },
        { roleName: 'Backend Dev', count: 3 },
        { roleName: 'Full Stack', count: 3 },
        { roleName: 'Cloud Eng', count: 2 },
        { roleName: 'DevOps', count: 1 },
        { roleName: 'QA Engineer', count: 1 },
        { roleName: 'Data Engineer', count: 1 },
        { roleName: 'Product Owner', count: 1 },
      ]},
    ],
  },
  Catalyst: {
    rows: [
      { name: 'Growth Team', total: 17, roles: [
        { roleName: 'Frontend Dev', count: 5 },
        { roleName: 'Backend Dev', count: 4 },
        { roleName: 'Full Stack', count: 3 },
        { roleName: 'Cloud Eng', count: 2 },
        { roleName: 'DevOps', count: 2 },
        { roleName: 'QA Engineer', count: 1 },
      ]},
      { name: 'Platform Team', total: 16, roles: [
        { roleName: 'Frontend Dev', count: 5 },
        { roleName: 'Backend Dev', count: 3 },
        { roleName: 'Full Stack', count: 2 },
        { roleName: 'Cloud Eng', count: 2 },
        { roleName: 'DevOps', count: 1 },
        { roleName: 'QA Engineer', count: 1 },
        { roleName: 'Data Engineer', count: 1 },
        { roleName: 'Eng Manager', count: 1 },
      ]},
    ],
  },
  DataCore: {
    rows: [
      { name: 'Data Ops', total: 8, roles: [
        { roleName: 'Data Engineer', count: 3 },
        { roleName: 'Backend Dev', count: 2 },
        { roleName: 'Cloud Eng', count: 2 },
        { roleName: 'DevOps', count: 1 },
      ]},
      { name: 'Analytics', total: 6, roles: [
        { roleName: 'Data Engineer', count: 1 },
        { roleName: 'Backend Dev', count: 1 },
        { roleName: 'Cloud Eng', count: 1 },
        { roleName: 'DevOps', count: 1 },
        { roleName: 'QA Engineer', count: 1 },
        { roleName: 'Product Owner', count: 1 },
      ]},
    ],
  },
  StreamOps: {
    rows: [
      { name: 'Streaming', total: 7, roles: [
        { roleName: 'Data Engineer', count: 1 },
        { roleName: 'Backend Dev', count: 1 },
        { roleName: 'Cloud Eng', count: 1 },
        { roleName: 'Frontend Dev', count: 2 },
        { roleName: 'DevOps', count: 1 },
        { roleName: 'QA Engineer', count: 1 },
      ]},
      { name: 'Pipeline', total: 5, roles: [
        { roleName: 'Data Engineer', count: 1 },
        { roleName: 'Backend Dev', count: 1 },
        { roleName: 'Cloud Eng', count: 1 },
        { roleName: 'Frontend Dev', count: 2 },
      ]},
    ],
  },
};

// TEAM level (single row showing team breakdown)
export const TEAM_DATA = {
  'Team Alpha': {
    rows: [
      {
        name: 'Team Alpha',
        total: 8,
        roles: [
          { roleName: 'Frontend Dev', count: 2 },
          { roleName: 'Backend Dev', count: 2 },
          { roleName: 'Full Stack', count: 1 },
          { roleName: 'Cloud Eng', count: 1 },
          { roleName: 'DevOps', count: 1 },
          { roleName: 'QA Engineer', count: 1 },
        ],
      },
    ],
  },
  'Team Beta': {
    rows: [
      {
        name: 'Team Beta',
        total: 7,
        roles: [
          { roleName: 'Frontend Dev', count: 2 },
          { roleName: 'Backend Dev', count: 1 },
          { roleName: 'Full Stack', count: 1 },
          { roleName: 'Cloud Eng', count: 1 },
          { roleName: 'DevOps', count: 1 },
          { roleName: 'Data Engineer', count: 1 },
        ],
      },
    ],
  },
  'Team Gamma': {
    rows: [
      {
        name: 'Team Gamma',
        total: 7,
        roles: [
          { roleName: 'Frontend Dev', count: 1 },
          { roleName: 'Backend Dev', count: 1 },
          { roleName: 'Full Stack', count: 1 },
          { roleName: 'Cloud Eng', count: 1 },
          { roleName: 'DevOps', count: 1 },
          { roleName: 'QA Engineer', count: 1 },
          { roleName: 'Product Owner', count: 1 },
        ],
      },
    ],
  },
};

// Helper to get the appropriate data based on context
export const getMockData = (contextLevel, filters, dropdownData) => {
  switch (contextLevel) {
    case 'SEGMENT':
      return SEGMENT_DATA;
    
    case 'SUB_SEGMENT': {
      const subSegment = dropdownData.subSegments.find(
        s => s.id === parseInt(filters.subSegment)
      );
      const subSegmentName = subSegment?.name || 'ADT';
      return SUB_SEGMENT_DATA[subSegmentName] || SUB_SEGMENT_DATA.ADT;
    }
    
    case 'PROJECT': {
      const project = dropdownData.projects.find(
        p => p.id === parseInt(filters.project)
      );
      const projectName = project?.name || 'Aspire';
      return PROJECT_DATA[projectName] || PROJECT_DATA.Aspire;
    }
    
    case 'TEAM': {
      const team = dropdownData.teams.find(
        t => t.id === parseInt(filters.team)
      );
      const teamName = team?.name || 'Team Alpha';
      return TEAM_DATA[teamName] || TEAM_DATA['Team Alpha'];
    }
    
    default:
      return SEGMENT_DATA;
  }
};
