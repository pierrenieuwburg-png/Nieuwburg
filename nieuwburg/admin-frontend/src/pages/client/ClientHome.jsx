import React, { useState, useEffect } from 'react';
import { getClientDashboard, getMyQuotes, getMyInvoices, getMyBookings } from '../../services/clientApi';
import './ClientDashboard.css'; // Reusing your existing styles for consistency

const ClientHome = () => {
  const [loading, setLoading] = useState(true);
  const [profile, setProfile] = useState({ name: 'Neighbor' });
  const [stats, setStats] = useState({});
  const [feed, setFeed] = useState([]); // Combined activity feed

  useEffect(() => {
    const fetchAllData = async () => {
      try {
        const [dashboard, quotes, invoices, bookings] = await Promise.all([
          getClientDashboard(),
          getMyQuotes(),
          getMyInvoices(),
          getMyBookings()
        ]);

        setProfile(dashboard.profile || { name: 'Neighbor' });
        setStats(dashboard.stats || {});

        // --- MERGE DATA INTO ACTIVITY FEED ---
        const feedItems = [];

        // 1. Add Quotes
        if (Array.isArray(quotes)) {
            quotes.forEach(q => feedItems.push({
                id: `q-${q.id}`,
                type: 'quote',
                dateObj: new Date(q.sort_date || q.date),
                date: q.date,
                title: `Quote ${q.status}`,
                desc: `${q.service_title} - R${q.amount?.toFixed(2)}`,
                status: q.status,
                action: q.status === 'Sent' ? 'Review' : 'View'
            }));
        }

        // 2. Add Invoices
        if (Array.isArray(invoices)) {
            invoices.forEach(inv => feedItems.push({
                id: `i-${inv.id}`,
                type: 'invoice',
                dateObj: new Date(inv.issue_date || Date.now()), // Fallback
                date: inv.issue_date || inv.due_date,
                title: `Invoice #${inv.number}`,
                desc: `Due: ${inv.due_date} - R${inv.total?.toFixed(2)}`,
                status: inv.status,
                action: inv.status === 'Unpaid' ? 'Pay Now' : 'View'
            }));
        }

        // 3. Add Bookings
        if (Array.isArray(bookings)) {
            bookings.forEach(b => feedItems.push({
                id: `b-${b.id}`,
                type: 'booking',
                dateObj: new Date(b.date),
                date: b.date,
                title: 'Scheduled Job',
                desc: `${b.service_name} at ${b.time}`,
                status: b.status,
                action: 'Details'
            }));
        }

        // Sort by Date Descending (Newest First)
        feedItems.sort((a, b) => b.dateObj - a.dateObj);
        setFeed(feedItems);

      } catch (err) {
        console.error("Dashboard Error:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchAllData();
  }, []);

  if (loading) return <div className="p-10 text-center text-gray-500">Loading your concierge...</div>;

  return (
    <div className="client-home-view">
      
      {/* 1. HERO CARD */}
      <div className="dashboard-hero-card" style={{
          background: 'linear-gradient(135deg, #1f2937 0%, #111827 100%)',
          color: 'white',
          padding: '2.5rem',
          borderRadius: '16px',
          marginBottom: '2.5rem',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.1)'
      }}>
        <div>
            <h1 style={{margin: '0 0 0.5rem 0', fontSize: '1.8rem'}}>Good Morning, {profile.name}!</h1>
            <p style={{margin: 0, opacity: 0.9, fontSize: '1.1rem'}}>
                You have <strong>{stats.upcoming_jobs || 0}</strong> upcoming jobs and <strong>{stats.pending_quotes || 0}</strong> pending items.
            </p>
        </div>
        <button className="btn-primary" style={{
            backgroundColor: 'white', 
            color: '#111827', 
            fontWeight: 'bold', 
            padding: '0.8rem 1.5rem',
            border: 'none',
            borderRadius: '8px',
            cursor: 'pointer'
        }}>
            + Book New Service
        </button>
      </div>

      <div className="dashboard-grid" style={{display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '2rem'}}>
        
        {/* 2. MAIN FEED (Timeline) */}
        <div className="feed-section">
            <h3 className="section-title" style={{marginBottom: '1.5rem', color: '#374151'}}>Recent Activity</h3>
            
            {feed.length === 0 ? (
                <div className="empty-state">No recent activity. Time to book a clean?</div>
            ) : (
                <div className="activity-feed">
                    {feed.map((item) => (
                        <div key={item.id} className="feed-item" style={{
                            background: 'white',
                            padding: '1.25rem',
                            borderRadius: '12px',
                            marginBottom: '1rem',
                            border: '1px solid #f3f4f6',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'space-between',
                            boxShadow: '0 1px 2px rgba(0,0,0,0.05)'
                        }}>
                            <div style={{display: 'flex', alignItems: 'center', gap: '1rem'}}>
                                {/* Icon based on type */}
                                <div style={{
                                    width: '40px', height: '40px', borderRadius: '50%', 
                                    background: item.type === 'invoice' ? '#fee2e2' : item.type === 'quote' ? '#fef3c7' : '#dbeafe',
                                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                                    fontSize: '1.2rem'
                                }}>
                                    {item.type === 'invoice' ? '💳' : item.type === 'quote' ? '📄' : '🧹'}
                                </div>
                                <div>
                                    <div style={{fontWeight: '600', color: '#1f2937'}}>{item.title}</div>
                                    <div style={{fontSize: '0.9rem', color: '#6b7280'}}>{item.desc}</div>
                                </div>
                            </div>
                            
                            <div style={{textAlign: 'right'}}>
                                <span className={`badge ${item.status.toLowerCase()}`} style={{marginBottom: '0.5rem', display: 'inline-block'}}>
                                    {item.status}
                                </span>
                                <div style={{fontSize: '0.8rem', color: '#9ca3af'}}>{item.date}</div>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>

        {/* 3. SIDE WIDGETS (Stats & Upsell) */}
        <div className="widgets-section">
            <div className="stat-widget" style={{background: 'white', padding: '1.5rem', borderRadius: '12px', border: '1px solid #e5e7eb', marginBottom: '1.5rem'}}>
                <h4 style={{margin: '0 0 1rem 0', color: '#6b7280', fontSize: '0.9rem', textTransform: 'uppercase'}}>Unpaid Invoices</h4>
                <div style={{fontSize: '2.5rem', fontWeight: 'bold', color: '#111827'}}>{stats.unpaid_invoices || 0}</div>
            </div>

            <div className="stat-widget" style={{background: 'white', padding: '1.5rem', borderRadius: '12px', border: '1px solid #e5e7eb'}}>
                <h4 style={{margin: '0 0 1rem 0', color: '#6b7280', fontSize: '0.9rem', textTransform: 'uppercase'}}>BlitzCoins</h4>
                <div style={{fontSize: '2.5rem', fontWeight: 'bold', color: '#f59e0b'}}>0</div>
                <p style={{fontSize: '0.9rem', color: '#6b7280', marginTop: '0.5rem'}}>Earn rewards on every booking.</p>
            </div>
        </div>

      </div>
    </div>
  );
};

export default ClientHome;