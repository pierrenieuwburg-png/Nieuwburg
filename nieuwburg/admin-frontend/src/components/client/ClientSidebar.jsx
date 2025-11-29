import React from 'react';
import { NavLink } from 'react-router-dom';
// Using FontAwesome icons - ensure these are available or swap for your preferred icon set
import { FaHome, FaUser, FaCalendarCheck, FaHandshake, FaMapMarkerAlt, FaCreditCard, FaCoins, FaTicketAlt, FaSignOutAlt, FaQuestionCircle, FaEnvelope, FaFileContract } from 'react-icons/fa'; 
// If you don't have react-icons, standard <i> tags with FontAwesome classes work too.

import './ClientSidebar.css';

const ClientSidebar = ({ isOpen }) => {
  return (
    <aside className={`client-sidebar ${isOpen ? 'open' : 'closed'}`}>
      
      {/* Brand / Logo Area */}
      <div className="sidebar-brand">
        <img src="/static/img/LogoBlackWithTitle.png" alt="Nieuwburg Blitz" className="sidebar-logo" />
      </div>

      {/* Navigation Menu */}
      <nav className="sidebar-menu">
        <div className="menu-label">Menu</div>
        
        <NavLink to="/client/dashboard" end className={({ isActive }) => `menu-item ${isActive ? 'active' : ''}`}>
          <FaHome className="menu-icon" /> <span>Home</span>
        </NavLink>

        <NavLink to="/client/dashboard/profile" className={({ isActive }) => `menu-item ${isActive ? 'active' : ''}`}>
          <FaUser className="menu-icon" /> <span>Profile</span>
        </NavLink>

        <NavLink to="/client/dashboard/bookings" className={({ isActive }) => `menu-item ${isActive ? 'active' : ''}`}>
          <FaCalendarCheck className="menu-icon" /> <span>Bookings</span>
        </NavLink>

        <NavLink to="/client/dashboard/partners" className={({ isActive }) => `menu-item ${isActive ? 'active' : ''}`}>
          <FaHandshake className="menu-icon" /> <span>BlitzPartners</span>
        </NavLink>

        <NavLink to="/client/dashboard/locations" className={({ isActive }) => `menu-item ${isActive ? 'active' : ''}`}>
          <FaMapMarkerAlt className="menu-icon" /> <span>Locations</span>
        </NavLink>

        <div className="menu-label" style={{marginTop: '1.5rem'}}>Finance</div>

        <NavLink to="/client/dashboard/payments" className={({ isActive }) => `menu-item ${isActive ? 'active' : ''}`}>
          <FaCreditCard className="menu-icon" /> <span>Payments</span>
        </NavLink>

        <NavLink to="/client/dashboard/rewards" className={({ isActive }) => `menu-item ${isActive ? 'active' : ''}`}>
          <FaCoins className="menu-icon" style={{color: '#f59e0b'}} /> <span>BlitzCoins</span>
        </NavLink>

        <NavLink to="/client/dashboard/vouchers" className={({ isActive }) => `menu-item ${isActive ? 'active' : ''}`}>
          <FaTicketAlt className="menu-icon" /> <span>Vouchers</span>
        </NavLink>
      </nav>

      {/* Bottom Actions */}
      <div className="sidebar-footer">
        <a href="/help" className="footer-link"><FaQuestionCircle /> Help</a>
        <a href="/contact" className="footer-link"><FaEnvelope /> Contact Us</a>
        <a href="/terms" className="footer-link"><FaFileContract /> Terms</a>
        
        <a href="/auth/logout" className="sign-out-btn">
          <FaSignOutAlt /> Sign Out
        </a>
      </div>
    </aside>
  );
};

export default ClientSidebar;