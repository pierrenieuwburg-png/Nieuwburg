import React, { useState } from 'react';
import { Outlet } from 'react-router-dom'; // Renders the child page
import ClientSidebar from '../components/client/ClientSidebar';
import ClientHeader from '../components/client/ClientHeader';
import './ClientLayout.css';

const ClientLayout = () => {
  const [isSidebarOpen, setIsSidebarOpen] = useState(true); // Default open on desktop

  const toggleSidebar = () => {
    setIsSidebarOpen(!isSidebarOpen);
  };

  return (
    <div className="client-layout">
      {/* 1. Sidebar (Left) */}
      <ClientSidebar isOpen={isSidebarOpen} />

      {/* 2. Main Content Area (Right) */}
      <div className={`client-main-content ${isSidebarOpen ? 'sidebar-open' : 'sidebar-closed'}`}>
        
        {/* 3. Top Header */}
        <ClientHeader toggleSidebar={toggleSidebar} />

        {/* 4. Dynamic Page Content (Home, Profile, etc.) */}
        <div className="client-page-container">
          <Outlet /> 
        </div>

      </div>
    </div>
  );
};

export default ClientLayout;