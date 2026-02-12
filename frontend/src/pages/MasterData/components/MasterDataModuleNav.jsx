/**
 * MasterDataModuleNav - Left sidebar navigation for Master Data pages
 * Shows Data Modules (Skill Taxonomy, Org Hierarchy, Roles)
 */
import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';

const MasterDataModuleNav = ({ currentModule }) => {
  const navigate = useNavigate();
  const location = useLocation();

  const modules = [
    { id: 'skills', path: '/admin/master-data/skill-taxonomy', icon: '🏷️', label: 'Skill Taxonomy' },
    { id: 'org', path: '/admin/master-data/org-hierarchy', icon: '🏢', label: 'Org Hierarchy' },
    { id: 'roles', path: '/admin/master-data/roles', icon: '👤', label: 'Roles' },
  ];

  const isActive = (modulePath) => {
    return location.pathname === modulePath;
  };

  return (
    <div className="md-sidebar">
      <div className="md-sidebar-section">
        <div className="md-sidebar-title">Data Modules</div>
        {modules.map(module => (
          <button
            key={module.id}
            className={`md-nav-item ${isActive(module.path) ? 'active' : ''}`}
            onClick={() => navigate(module.path)}
          >
            <span className="icon">{module.icon}</span>
            <span>{module.label}</span>
          </button>
        ))}
      </div>
    </div>
  );
};

export default MasterDataModuleNav;
