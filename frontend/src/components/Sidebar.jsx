import { BarChart3, Search, Layers, User } from 'lucide-react';
import { useNavigate, useLocation } from 'react-router-dom';

const Sidebar = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const menuItems = [
    { id: 'dashboard', path: '/', icon: BarChart3, label: 'Dashboard' },
    { id: 'query', path: '/query', icon: Search, label: 'Capability Finder' },
    { id: 'taxonomy', path: '/taxonomy', icon: Layers, label: 'Skill Taxonomy' },
    { id: 'profile', path: '/profile', icon: User, label: 'My Profile' }
  ];

  const isActive = (path) => {
    if (path === '/') {
      return location.pathname === '/';
    }
    return location.pathname.startsWith(path);
  };

  return (
    <div className="w-56 bg-white border-r border-slate-200 min-h-screen">
      <nav className="p-3 space-y-1">
        {menuItems.map(item => (          <button
            key={item.id}
            onClick={() => navigate(item.path)}
            className={`w-full flex items-center space-x-2 px-3 py-2.5 rounded-lg text-sm transition-colors ${
              isActive(item.path) 
                ? 'bg-blue-600 text-white' 
                : 'text-slate-700 hover:bg-slate-100'
            }`}
          >
            <item.icon className="w-4 h-4" />
            <span className="font-medium">{item.label}</span>
          </button>
        ))}
      </nav>
    </div>
  );
};

export default Sidebar;
