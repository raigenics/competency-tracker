import { BarChart3, Search, Layers, User, Users, Upload, Database, Shield, ChevronDown, ChevronRight, Building2, UserSquare2 } from 'lucide-react';
import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { FEATURE_FLAGS } from '../config/featureFlags';

const Sidebar = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [masterDataExpanded, setMasterDataExpanded] = useState(
    location.pathname.startsWith('/admin/master-data')
  );

  const navigationSections = [
    {
      title: 'ANALYTICS',
      items: [
        { id: 'dashboard', path: '/', icon: BarChart3, label: 'Dashboard' },
        { id: 'query', path: '/query', icon: Search, label: 'Skill Search' },
        { id: 'taxonomy', path: '/taxonomy', icon: Layers, label: 'Organizational Skill Map' },
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
        { 
          id: 'master-data', 
          icon: Database, 
          label: 'Master Data',
          hasSubmenu: true,
          submenu: [
            { id: 'skill-taxonomy', path: '/admin/master-data/skill-taxonomy', icon: Layers, label: 'Skill Taxonomy' },
            { id: 'org-hierarchy', path: '/admin/master-data/org-hierarchy', icon: Building2, label: 'Org Hierarchy' },
            { id: 'roles', path: '/admin/master-data/roles', icon: UserSquare2, label: 'Roles' }
          ]
        },
        // RBAC Admin Panel - controlled by FEATURE_FLAGS.SHOW_RBAC_ADMIN
        ...(FEATURE_FLAGS.SHOW_RBAC_ADMIN 
          ? [{ id: 'rbac-admin', path: '/rbac-admin', icon: Shield, label: 'RBAC Admin Panel' }] 
          : []
        )
      ]
    }
  ];

  const isActive = (path) => {
    if (path === '/') {
      return location.pathname === '/';
    }
    return location.pathname.startsWith(path);
  };

  const isMasterDataActive = () => {
    return location.pathname.startsWith('/admin/master-data');
  };

  const toggleMasterData = () => {
    setMasterDataExpanded(!masterDataExpanded);
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
        {navigationSections.map((section, _sectionIndex) => (
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
                item.hasSubmenu ? (
                  // Master Data with submenu
                  <div key={item.id}>
                    <button
                      onClick={toggleMasterData}
                      className={`w-full flex items-center gap-2.5 px-5 py-2.5 text-sm transition-all ${
                        isMasterDataActive() 
                          ? 'bg-[#667eea]/20 border-l-3 border-[#667eea] pl-[17px]' 
                          : 'hover:bg-white/5'
                      }`}
                    >
                      <div className="w-[18px] h-[18px] bg-white/20 rounded flex items-center justify-center flex-shrink-0">
                        <item.icon className="w-3.5 h-3.5" />
                      </div>
                      <span className="font-normal flex-1 text-left">{item.label}</span>
                      {masterDataExpanded ? (
                        <ChevronDown className="w-4 h-4 opacity-60" />
                      ) : (
                        <ChevronRight className="w-4 h-4 opacity-60" />
                      )}
                    </button>
                    {/* Submenu */}
                    {masterDataExpanded && (
                      <div className="ml-4 border-l border-white/10">
                        {item.submenu.map(subItem => (
                          <button
                            key={subItem.id}
                            onClick={() => navigate(subItem.path)}
                            className={`w-full flex items-center gap-2.5 px-5 py-2 text-sm transition-all ${
                              isActive(subItem.path) 
                                ? 'bg-[#667eea]/20 text-white' 
                                : 'text-white/70 hover:bg-white/5 hover:text-white'
                            }`}
                          >
                            <div className="w-[16px] h-[16px] bg-white/15 rounded flex items-center justify-center flex-shrink-0">
                              <subItem.icon className="w-3 h-3" />
                            </div>
                            <span className="font-normal text-[13px]">{subItem.label}</span>
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                ) : (
                  // Regular navigation item
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
                )
              ))}
            </div>
          </div>
        ))}
      </nav>
    </div>
  );
};

export default Sidebar;
