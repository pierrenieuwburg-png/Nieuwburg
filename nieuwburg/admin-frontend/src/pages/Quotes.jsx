import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom'; // Import Link

function Quotes() {
  const [quotes, setQuotes] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchQuotes = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const response = await fetch('/api/admin/quotes'); // Fetch from the new endpoint
        if (!response.ok) {
          if (response.status === 403) {
            throw new Error('Permission denied fetching quotes.');
          }
          throw new Error(`HTTP error fetching quotes! status: ${response.status}`);
        }
        const data = await response.json();
        setQuotes(data);
      } catch (err) {
        console.error('Error fetching quotes:', err);
        setError(`Error loading quotes: ${err.message}`);
        setQuotes([]); // Clear quotes on error
      } finally {
        setIsLoading(false);
      }
    };

    fetchQuotes();
  }, []); // Run once on mount

  // Helper function to format price
  const formatPrice = (price) => {
     if (price === null || price === undefined) return 'N/A';
     const num = parseFloat(price);
     return isNaN(num) ? 'N/A' : `R${num.toFixed(2)}`;
  };

  return (
    <div>
      <div className="admin-header">
        <h1>Quote Requests</h1>
        <p>View and manage all quote requests received.</p>
        {/* Optional: Add button to create a quote manually if needed */}
        {/* <button className="cta">Create New Quote</button> */}
      </div>

      {error && (
        <div className="flash error" style={{ marginBottom: '20px' }}>
          {error}
        </div>
      )}

      <div className="admin-section">
        <h2>All Quotes</h2>
        {isLoading ? (
          <p>Loading quotes...</p>
        ) : quotes.length > 0 ? (
          <table className="data-table">
            <thead>
              <tr>
                <th>Requested On</th>
                <th>Client</th>
                <th>Service</th>
                <th>Frequency</th>
                <th>Price</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {quotes.map((quote) => (
                <tr key={quote.id}>
                  <td>{quote.request_date}</td>
                  <td>
                    {/* Link to Client Detail page */}
                    <Link to={`/clients/${quote.user_id}`}>
                        <strong>{quote.client_name}</strong>
                    </Link>
                    <br />
                    <small>{quote.client_phone}</small>
                  </td>
                  <td>
                    {quote.service} ({quote.property_type})
                  </td>
                   <td>{quote.frequency}</td>
                  <td>{formatPrice(quote.total_price)}</td>
                  <td>
                    {/* Style status like in Bookings page */}
                    <span className={`booking-status status-${quote.status?.toLowerCase() || 'unknown'}`}>
                       {quote.status}
                    </span>
                  </td>
                  <td className="action-buttons">
                    {/* Add relevant actions, e.g., View Details, Edit Quote, Convert to Job */}
                    <Link to={`/quote/view/${quote.id}`} className="cta-outline-small">View</Link>
                    {/* <Link to={`/quote/edit/${quote.id}`} className="cta-outline-small">Edit</Link> */}
                    {/* Conditionally show "Schedule" if status allows */}
                    {quote.status === 'Confirmed' && (
                         <Link to={`/schedule_job/${quote.id}`} className="cta-outline-small">Schedule Job</Link>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p>No quote requests found.</p>
        )}
      </div>
    </div>
  );
}

export default Quotes;