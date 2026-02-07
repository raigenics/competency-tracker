import { BarChart3, Search, Layers, User, Users, Upload, Database, Shield } from 'lucide-react';
import { useNavigate, useLocation } from 'react-router-dom';

const Sidebar = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const navigationSections = [
    {
      title: 'ANALYTICS',
      items: [
        { id: 'dashboard', path: '/', icon: BarChart3, label: 'Dashboard' },
        { id: 'query', path: '/query', icon: Search, label: 'Capability Finder' },
        { id: 'taxonomy', path: '/taxonomy', icon: Layers, label: 'Capability Overview' },
        { id: 'profile', path: '/profile', icon: User, label: 'Employee Profile' }
      ]
    },
    {
      title: 'DATA MANAGEMENT',
      items: [
        { id: 'employees', path: '/employees', icon: Users, label: 'Employees' },
        { id: 'bulk-import', path: '/bulk-import', icon: Upload, label: 'Bulk Import' }
      ]
    },
    {
      title: 'ADMINISTRATION',
      items: [
        { id: 'master-data', path: '/master-data', icon: Database, label: 'Master Data' },
        { id: 'rbac-admin', path: '/rbac-admin', icon: Shield, label: 'RBAC Admin Panel' }
      ]
    }
  ];

  const isActive = (path) => {
    if (path === '/') {
      return location.pathname === '/';
    }
    return location.pathname.startsWith(path);
  };

  return (
    <div className="w-60 bg-[#1e293b] text-white min-h-screen flex-shrink-0">
      {/* Logo Section */}
      <div className="px-5 py-5 border-b border-white/10 mb-5">
        <h3 className="text-lg font-semibold mb-1">CompetencyIQ</h3>
        <p className="text-[11px] opacity-60">Skill Intelligence Platform</p>
      </div>

      {/* Navigation */}
      <nav className="pb-5">
        {navigationSections.map((section, sectionIndex) => (
          <div key={section.title} className="mb-6">
            {/* Section Header */}
            <div className="px-5 py-2">
              <h3 className="text-[11px] font-semibold opacity-50 uppercase tracking-wide">
                {section.title}
              </h3>
            </div>
            
            {/* Section Items */}
            <div>
              {section.items.map(item => (
                <button
                  key={item.id}
                  onClick={() => navigate(item.path)}
                  className={`w-full flex items-center gap-2.5 px-5 py-2.5 text-sm transition-all ${
                    isActive(item.path) 
                      ? 'bg-[#667eea]/20 border-l-3 border-[#667eea] pl-[17px]' 
                      : 'hover:bg-white/5'
                  }`}
                >
                  <div className="w-[18px] h-[18px] bg-white/20 rounded flex items-center justify-center flex-shrink-0">
                    <item.icon className="w-3.5 h-3.5" />
                  </div>
                  <span className="font-normal">{item.label}</span>
                </button>
              ))}
            </div>
          </div>
        ))}
      </nav>
    </div>
  );
};

export default Sidebar;
