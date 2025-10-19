import React from 'react';
import { Routes, Route } from 'react-router-dom';

import Dashboard from './pages/Dashboard';
import Applications from './pages/Applications';
import Bookings from './pages/Bookings';
import Clients from './pages/Clients';
import Staff from './pages/Staff';
import Quotes from './pages/Quotes';
import Invoices from './pages/Invoices';
import Services from './pages/Services';
import Blog from './pages/Blog';
import ActivityLog from './pages/ActivityLog';
import ClientDetail from './pages/ClientDetail';

// Placeholder for unmatched routes
const NotFound = () => <h2>Admin Page Not Found</h2>;

// Ensure NO inline const definitions exist for the imported components above
// (e.g., no line like: const Bookings = () => <h2>...</h2>;)

function App() {
  return (
    <Routes>
      <Route path="/" element={<Dashboard />} />
      <Route path="/dashboard" element={<Dashboard />} />
      <Route path="/clients" element={<Clients />} />
      <Route path="/clients/:clientId" element={<ClientDetail />} />
      <Route path="/staff" element={<Staff />} />
      <Route path="/bookings" element={<Bookings />} />
      <Route path="/applications" element={<Applications />} />
      <Route path="/quotes" element={<Quotes />} />
      <Route path="/invoices" element={<Invoices />} />
      <Route path="/services" element={<Services />} />
      <Route path="/blog" element={<Blog />} />
      <Route path="/activity-log" element={<ActivityLog />} />
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
}

export default App;