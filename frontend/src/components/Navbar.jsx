import { Layers, User } from 'lucide-react';

const Navbar = () => {
  return (
    <div className="bg-slate-900 text-white px-6 py-4 shadow-lg">
      <div className="max-w-screen-2xl mx-auto flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <Layers className="w-6 h-6 text-blue-400" />
          <div>
            <div className="font-bold text-lg">CompetencyIQ</div>
            <div className="text-xs text-slate-400">Skill Intelligence & Talent Discovery Platform</div>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
            <User className="w-4 h-4" />
          </div>
          <span className="text-sm">Admin User</span>
        </div>
      </div>
    </div>
  );
};

export default Navbar;
