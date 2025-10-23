import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';

function Invoices() {
  const [invoices, setInvoices] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchInvoices = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const response = await fetch('/api/admin/invoices'); // Fetch from the new endpoint
        if (!response.ok) {
          if (response.status === 403) {
            throw new Error('Permission denied fetching invoices.');
          }
          throw new Error(`HTTP error fetching invoices! status: ${response.status}`);
        }
        const data = await response.json();
        setInvoices(data);
      } catch (err) {
        console.error('Error fetching invoices:', err);
        setError(`Error loading invoices: ${err.message}`);
        setInvoices([]); // Clear invoices on error
      } finally {
        setIsLoading(false);
      }
    };

    fetchInvoices();
  }, []); // Run once on mount

  // Helper function to format currency
  const formatCurrency = (amount) => {
    if (amount === null || amount === undefined) return 'N/A';
    const num = parseFloat(amount);
    return isNaN(num) ? 'N/A' : `R ${num.toFixed(2)}`;
  };

  // Helper function to get status color (adjust based on your Invoice statuses)
  const getStatusClass = (status) => {
    switch (status?.toLowerCase()) {
      case 'paid': return 'status-completed'; // Green
      case 'unpaid': return 'status-scheduled'; // Blue/Default
      case 'overdue': return 'status-cancelled'; // Grey/Red
      default: return 'status-unknown'; // Default grey
    }
  };


  return (
    <div>
      <div className="admin-header">
        <h1>Invoices</h1>
        <p>View and manage client invoices.</p>
        {/* Optional: Button to create a new invoice */}
        {/* <Link to="/invoices/new" className="cta">Create New Invoice</Link> */}
      </div>

      {error && (
        <div className="flash error" style={{ marginBottom: '20px' }}>
          {error}
        </div>
      )}

      <div className="admin-section">
        <h2>All Invoices</h2>
        {isLoading ? (
          <p>Loading invoices...</p>
        ) : invoices.length > 0 ? (
          <table className="data-table">
            <thead>
              <tr>
                <th>Invoice #</th>
                <th>Client</th>
                <th>Issued</th>
                <th>Due</th>
                <th>Amount</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {invoices.map((invoice) => (
                <tr key={invoice.id}>
                  <td>{invoice.invoice_number}</td>
                  <td>
                    <Link to={`/clients/${invoice.client_id}`}>
                      {invoice.client_name}
                    </Link>
                  </td>
                  <td>{invoice.issue_date}</td>
                  <td>{invoice.due_date}</td>
                  <td>{formatCurrency(invoice.total_amount)}</td>
                  <td>
                    <span className={`booking-status ${getStatusClass(invoice.status)}`}>
                      {invoice.status}
                    </span>
                  </td>
                  <td className="action-buttons">
                    {/* Placeholder Actions */}
                    <Link to={`/invoices/view/${invoice.id}`} className="cta-outline-small">View</Link>
                    {/* <Link to={`/invoices/edit/${invoice.id}`} className="cta-outline-small">Edit</Link> */}
                    {/* Add action like "Mark Paid" if applicable */}
                    {invoice.status !== 'Paid' && (
                      <button className="cta-outline-small" style={{marginLeft: '5px'}}>Mark Paid</button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p>No invoices found.</p>
        )}
      </div>
    </div>
  );
}

export default Invoices;