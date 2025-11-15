import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { BarLoader } from 'react-spinners';

// Helper to format currency
const formatPrice = (price) => {
  if (price === null || price === undefined) return 'N/A';
  const num = parseFloat(price);
  return isNaN(num) ? 'N/A' : `R ${num.toFixed(2)}`;
};

function FormalQuoteDetail() {
  const { quoteId } = useParams();
  const [quoteDetails, setQuoteDetails] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // --- Define Logo Path ---
  // We use the static path here, as it's loaded by React
  const logoUrl = "/static/img/LogoBlackWithTitle.png";

  useEffect(() => {
    const fetchQuoteDetail = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const response = await fetch(`/api/admin/quotes/formal/${quoteId}`);
        if (!response.ok) {
          if (response.status === 404) throw new Error('Formal quote not found.');
          if (response.status === 403) throw new Error('Permission denied.');
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        setQuoteDetails(data);
      } catch (err) {
        console.error('Error fetching formal quote detail:', err);
        setError(err.message);
      } finally {
        setIsLoading(false);
      }
    };

    fetchQuoteDetail();
  }, [quoteId]);

  if (isLoading) {
    return (
        <div style={{ display: 'flex', justifyContent: 'center', padding: '100px' }}>
            <BarLoader color="#006ac6" width="50%" />
        </div>
    );
  }

  if (error) {
    return (
      <div>
        <div className="admin-header">
          <h1>Error</h1>
          <Link to="/quotes" className="cta-outline">Back to Quotes</Link>
        </div>
        <div className="flash error">{error}</div>
      </div>
    );
  }

  if (!quoteDetails) {
    return <p>No quote data found.</p>;
  }

  const { client, quote, line_items } = quoteDetails;

  return (
    <>
      {/* ==================================
        == 1. THE NEW ADMIN ACTION BAR ===
        ==================================
        This stays at the top of the admin page.
      */}
      <div className="admin-header">
        <h1>Quote: {quote.quote_number}</h1>
        <div className="admin-header-actions">
          {/* --- NEW CONDITIONAL EDIT BUTTON --- */}
          {quote.status === 'Draft' && (
            <Link to={`/quotes/edit/${quote.id}`} className="cta">
              Edit Quote
            </Link>
          )}
          <Link to="/quotes" className="cta-outline" style={{marginLeft: '10px'}}>
            Back to Quotes
          </Link>
        </div>
      </div>

      {/* =====================================
        == 2. THE NEW DOCUMENT PREVIEW ===
        =====================================
        This is the new A4-style container
      */}
      <div className="quote-document-view-container">
        <div className="quote-document-page">
          
          {/* --- Document Header --- */}
          <header className="quote-doc-header">
            <div className="quote-doc-logo">
              <img src={logoUrl} alt="Nieuwburg Blitz Logo" />
            </div>
            <div className="quote-doc-title">
              <h1>QUOTE</h1>
              <p><strong>Quote Number:</strong> {quote.quote_number}</p>
              <p><strong>Date Issued:</strong> {quote.quote_date}</p>
              <p><strong>Valid Until:</strong> {quote.expiry_date}</p>
            </div>
          </header>

          {/* --- Client Parties --- */}
          <section className="quote-doc-parties">
            <div className="party-details">
              <h3>Billed To</h3>
              <strong>{client.name}</strong>
              <p>
                {client.address || 'No address provided'}
                <br />
                {client.email}
                <br />
                {client.phone}
              </p>
            </div>
            <div className="party-details" style={{textAlign: 'right'}}>
              <h3>From</h3>
              <strong>Nieuwburg Blitz</strong>
              <p>
                24 A 5, Parow Park, Balfour Street
                <br />
                Cape Town, Western Cape, 7500
              </p>
            </div>
          </section>

          {/* --- Line Items Table --- */}
          <section className="quote-doc-items">
            <table className="quote-doc-table">
              <thead>
                <tr>
                  <th>Description</th>
                  <th>Qty</th>
                  <th>Unit Price</th>
                  <th>Amount</th>
                </tr>
              </thead>
              <tbody>
                {line_items.map(item => (
                  <tr key={item.id}>
                    <td style={{whiteSpace: 'pre-wrap'}}>{item.description}</td>
                    <td>{item.quantity}</td>
                    <td>{formatPrice(item.unit_price)}</td>
                    <td className="amount">{formatPrice(item.amount)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>

          {/* --- Totals --- */}
          <section className="quote-doc-totals">
            <div className="quote-doc-totals-summary">
              <div className="totals-row">
                <span>Subtotal</span>
                <span>{formatPrice(quote.subtotal)}</span>
              </div>
              {quote.discount > 0 && (
                <div className="totals-row">
                  <span>Discount</span>
                  <span>- {formatPrice(quote.discount)}</span>
                </div>
              )}
              <div className="totals-row grand-total">
                <span>TOTAL</span>
                <span>{formatPrice(quote.total)}</span>
              </div>
            </div>
          </section>

        </div>
      </div>
    </>
  );
}

export default FormalQuoteDetail;