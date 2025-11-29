import React, { useState, useEffect } from 'react';
import { getClientDashboard, getMyQuotes, getMyInvoices, getMyBookings } from '../../services/clientApi';
import './ClientDashboard.css';

const ClientDashboard = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null); // New Error State
  const [stats, setStats] = useState({ pending_quotes: 0, unpaid_invoices: 0, upcoming_jobs: 0 });
  const [profile, setProfile] = useState({ name: 'Neighbor', address: '' });
  const [quotes, setQuotes] = useState([]);
  const [invoices, setInvoices] = useState([]);
  const [bookings, setBookings] = useState([]);

  useEffect(() => {
    const fetchAllData = async () => {
      console.log("--- Dashboard: Starting Data Fetch ---");
      try {
        // Fetch all data
        const [dashboardData, quotesData, invoicesData, bookingsData] = await Promise.all([
          getClientDashboard(),
          getMyQuotes(),
          getMyInvoices(),
          getMyBookings()
        ]);

        console.log("--- Dashboard: Data Received ---", { dashboardData, quotesData, invoicesData, bookingsData });

        // Safely set state
        setStats(dashboardData?.stats || { pending_quotes: 0, unpaid_invoices: 0, upcoming_jobs: 0 });
        setProfile(dashboardData?.profile || { name: 'Neighbor', address: '' });
        setQuotes(Array.isArray(quotesData) ? quotesData : []);
        setInvoices(Array.isArray(invoicesData) ? invoicesData : []);
        setBookings(Array.isArray(bookingsData) ? bookingsData : []);

      } catch (err) {
        console.error("--- Dashboard Critical Error ---", err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchAllData();
  }, []);

  const handlePayInvoice = (invoiceId) => {
     alert(`Initiating payment for Invoice #${invoiceId}. Payment Gateway coming in Phase 4.1`);
  };

  // 1. Loading State
  if (loading) {
    return (
        <div className="client-dashboard-container" style={{textAlign: 'center', marginTop: '50px'}}>
            <h3>Loading your dashboard...</h3>
            <p>Please wait while we fetch your data.</p>
        </div>
    );
  }

  // 2. Error State
  if (error) {
    return (
        <div className="client-dashboard-container" style={{textAlign: 'center', color: 'red', marginTop: '50px'}}>
            <h3>Something went wrong</h3>
            <p>Error: {error}</p>
            <button onClick={() => window.location.reload()} className="btn-primary">Retry</button>
        </div>
    );
  }

  // 3. Success State
  return (
    <div className="client-dashboard-container">
      
      {/* HEADER */}
      <header className="client-header">
        <div>
          {/* Fix: API returns 'name', not 'first_name' */}
          <h1>Welcome back, {profile.name}!</h1> 
          <div className="subtitle">Manage your home services in one place.</div>
        </div>
        <div style={{textAlign: 'right'}}>
            <div style={{fontWeight: '600', color: '#4a5568'}}>
                {new Date().toLocaleDateString('en-ZA', { weekday: 'long', day: 'numeric', month: 'long' })}
            </div>
        </div>
      </header>

      {/* STATS */}
      <div className="stats-grid">
        <div className="stat-card">
          <h3>Action Items</h3>
          <div className="value">{stats.pending_quotes || 0}</div>
        </div>
        <div className="stat-card">
          <h3>Due Payments</h3>
          <div className="value">{stats.unpaid_invoices || 0}</div>
        </div>
        <div className="stat-card">
          <h3>Upcoming Jobs</h3>
          <div className="value">{stats.upcoming_jobs || 0}</div>
        </div>
      </div>

      {/* QUOTES TABLE */}
      <section className="dashboard-section">
        <div className="section-title">Quotes & Requests</div>
        {quotes.length === 0 ? (
          <div className="empty-state">No active quotes found.</div>
        ) : (
          <table className="client-table">
            <thead>
              <tr>
                <th>Reference</th>
                <th>Service</th>
                <th>Date</th>
                <th>Status</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {quotes.slice(0, 5).map((q, index) => (
                <tr key={q.id || index}>
                  <td>{q.display_id || '-'}</td>
                  <td>{q.service_title || 'Service'}</td>
                  <td>{q.date || '-'}</td>
                  <td>
                    <span className={`badge ${(q.status || 'draft').toLowerCase()}`}>
                      {q.status || 'Unknown'}
                    </span>
                  </td>
                  <td>
                    {q.is_actionable ? (
                        <button className="btn-pay">Review</button>
                    ) : (
                        <span style={{color: '#94a3b8', fontSize: '0.8rem'}}>View</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      {/* INVOICES TABLE */}
      <section className="dashboard-section">
        <div className="section-title">Your Invoices</div>
        {invoices.length === 0 ? (
          <div className="empty-state">No invoices yet.</div>
        ) : (
          <table className="client-table">
            <thead>
              <tr>
                <th>Invoice #</th>
                <th>Due Date</th>
                <th>Total</th>
                <th>Status</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {invoices.slice(0, 5).map((inv, index) => (
                <tr key={inv.id || index}>
                  <td>{inv.number || '-'}</td>
                  <td>{inv.due_date || '-'}</td>
                  <td>{inv.total ? `R ${inv.total.toFixed(2)}` : 'R 0.00'}</td>
                  <td>
                    <span className={`badge ${(inv.status || 'unpaid').toLowerCase()}`}>
                      {inv.status}
                    </span>
                  </td>
                  <td>
                    {inv.status === 'Unpaid' && (
                      <button 
                        className="btn-pay"
                        onClick={() => handlePayInvoice(inv.id)}
                      >
                        Pay Now
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

    </div>
  );
};

export default ClientDashboard;