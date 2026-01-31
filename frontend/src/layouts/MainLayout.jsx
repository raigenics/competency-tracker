import { Outlet } from 'react-router-dom';
import Sidebar from '../components/Sidebar.jsx';

const MainLayout = () => {
  return (
    <div className="flex min-h-screen bg-[#f8fafc]">
      <Sidebar />
      <main className="flex-1 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  );
};

export default MainLayout;
