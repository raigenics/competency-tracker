import { useState } from 'react';
import { Shield, Users, FileText } from 'lucide-react';
import PageHeader from '../../components/PageHeader.jsx';
import UserManagementTab from './components/UserManagementTab.jsx';

/**
 * RBAC Admin Page - Super Admin Panel for User and Access Management
 * 
 * Features:
 * - User Management: Create users, view users with role assignments
 * - Role Assignment: Assign roles with specific scopes to users
 * - Audit Trail: View access control changes (placeholder for future)
 * 
 * Phase 1: User Management tab only (fully functional)
 */
const RbacAdminPage = () => {
  const [activeTab, setActiveTab] = useState('users');

  const tabs = [
    {
      id: 'users',
      label: 'User Management',
      icon: Users,
      description: 'Manage users and assign access roles',
      enabled: true
    },
    {
      id: 'audit',
      label: 'Audit Log',
      icon: FileText,
      description: 'View access control audit trail (coming soon)',
      enabled: false
    }
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      <PageHeader
        title="RBAC Super Admin Panel"
        subtitle="Manage users, roles, and access permissions"
        icon={Shield}
      />

      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* Tab Navigation */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 mb-6">
          <div className="border-b border-gray-200">
            <div className="flex">
              {tabs.map((tab) => {
                const Icon = tab.icon;
                const isActive = activeTab === tab.id;
                
                return (
                  <button
                    key={tab.id}
                    disabled={!tab.enabled}
                    onClick={() => tab.enabled && setActiveTab(tab.id)}
                    className={`
                      flex items-center gap-3 px-6 py-4 text-sm font-medium border-b-2 transition-colors
                      ${isActive
                        ? 'border-indigo-600 text-indigo-600 bg-indigo-50'
                        : 'border-transparent text-gray-600 hover:text-gray-800 hover:border-gray-300'
                      }
                      ${!tab.enabled && 'opacity-50 cursor-not-allowed'}
                    `}
                  >
                    <Icon className="w-5 h-5" />
                    <div className="flex flex-col items-start">
                      <span>{tab.label}</span>
                      {!tab.enabled && (
                        <span className="text-xs text-gray-400 font-normal">Coming soon</span>
                      )}
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Tab Content */}
          <div className="p-6">
            {activeTab === 'users' && <UserManagementTab />}
            
            {activeTab === 'audit' && (
              <div className="text-center py-12 text-gray-500">
                <FileText className="w-16 h-16 mx-auto mb-4 text-gray-300" />
                <h3 className="text-lg font-medium mb-2">Audit Log Coming Soon</h3>
                <p className="text-sm">
                  View comprehensive audit trail of all access control changes
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default RbacAdminPage;
