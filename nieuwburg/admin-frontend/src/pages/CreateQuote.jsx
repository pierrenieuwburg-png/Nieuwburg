import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom'; // Import useLocation
import { BarLoader } from 'react-spinners';

// This is a new component for the line items
const LineItem = ({ item, index, onChange, onRemove }) => {
  return (
    <div className="line-item-row">
      <input
        type="text"
        placeholder="Description"
        value={item.description}
        onChange={(e) => onChange(index, 'description', e.target.value)}
        className="form-input"
        style={{flex: 1, marginRight: '10px'}}
      />
      <input
        type="number"
        placeholder="Qty"
        value={item.quantity}
        onChange={(e) => onChange(index, 'quantity', e.target.value)}
        className="form-input"
        style={{width: '80px', marginRight: '10px'}}
      />
      <input
        type="number"
        placeholder="Unit Price"
        value={item.unit_price}
        onChange={(e) => onChange(index, 'unit_price', e.target.value)}
        className="form-input"
        style={{width: '120px', marginRight: '10px'}}
      />
      <input
        type="text"
        readOnly
        value={`R ${(item.quantity * item.unit_price).toFixed(2)}`}
        className="form-input"
        style={{width: '120px', marginRight: '10px', background: '#f9fafb'}}
      />
      <button type="button" onClick={() => onRemove(index)} className="cta-danger-outline" style={{padding: '10px 15px'}}>X</button>
    </div>
  );
};


function CreateQuote() {
  const navigate = useNavigate();
  const location = useLocation(); // Get the location object

  // Client info
  const [clientId, setClientId] = useState(null); // For existing client
  const [guestName, setGuestName] = useState('');
  const [guestEmail, setGuestEmail] = useState('');
  const [guestPhone, setGuestPhone] = useState('');
  const [guestAddress, setGuestAddress] = useState('');

  // Financials
  const [lineItems, setLineItems] = useState([
    { description: '', quantity: 1, unit_price: 0 }
  ]);
  const [discount, setDiscount] = useState(0);

  // System state
  const [csrfToken, setCsrfToken] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // --- THIS IS THE NEW LOGIC ---
  useEffect(() => {
    // Check if we were passed data from the QuoteDetail page
    const fromRequest = location.state?.fromRequest;
    if (fromRequest) {
      const { client, request } = fromRequest;
      
      if (client.user_id) {
        // It's an existing client
        setClientId(client.user_id);
      }
      // Pre-fill all guest fields regardless
      setGuestName(client.name || '');
      setGuestEmail(client.email || '');
      setGuestPhone(client.phone || '');
      setGuestAddress(client.address || '');

      // Pre-fill the first line item with the lead's description
      setLineItems([
        { 
          description: request.full_description || request.subject || '', 
          quantity: 1, 
          unit_price: 0 
        }
      ]);
    }

    // Fetch CSRF token
    const token = document.querySelector('meta[name="csrf-token"]')?.getAttribute("content");
    setCsrfToken(token || "");
  }, [location.state]); // Re-run if location state changes

  // --- Line Item Handlers ---
  const handleLineItemChange = (index, field, value) => {
    const updatedItems = [...lineItems];
    updatedItems[index][field] = value;
    setLineItems(updatedItems);
  };

  const addLineItem = () => {
    setLineItems([...lineItems, { description: '', quantity: 1, unit_price: 0 }]);
  };

  const removeLineItem = (index) => {
    if (lineItems.length > 1) { // Always keep at least one
      const updatedItems = lineItems.filter((_, i) => i !== index);
      setLineItems(updatedItems);
    }
  };

  // --- Calculate Totals ---
  const subtotal = lineItems.reduce((acc, item) => {
    return acc + (item.quantity * item.unit_price);
  }, 0);
  const total = subtotal - discount;

  // --- Form Submission ---
  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    const quoteData = {
      client_id: clientId,
      guest_name: guestName,
      email: guestEmail,
      phone_number: guestPhone,
      address: guestAddress,
      line_items: lineItems.map(item => ({
        ...item,
        quantity: parseFloat(item.quantity) || 0,
        unit_price: parseFloat(item.unit_price) || 0
      })),
      subtotal: subtotal,
      discount: parseFloat(discount) || 0,
      total: total,
    };

    try {
      const response = await fetch('/api/admin/quotes/create', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken
        },
        body: JSON.stringify(quoteData)
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.message || 'Failed to create quote');
      }

      // Success! Go to the quotes list with a success message.
      navigate('/quotes', { 
        state: { flashMessage: { type: 'success', text: result.message } } 
      });

    } catch (err) {
      console.error("Error creating quote:", err);
      setError(err.message);
      setIsLoading(false);
    }
  };

  return (
    <div>
      <div className="admin-header">
        <h1>Create New Formal Quote</h1>
        <p>This will generate a formal, line-item quote (a `Quote` object).</p>
      </div>

      {error && <div className="flash error">{error}</div>}

      <form onSubmit={handleSubmit} className="admin-section">
        {/* Client Info Section */}
        <div className="admin-section" style={{background: '#f9fafb', border: '1px solid #e5e7eb', borderRadius: '8px'}}>
          <h2>Client Information</h2>
          <p>
            {/* We're simplifying this for now to just guest fields.
                A full implementation would have a client search.
                This pre-fills fine from the lead data. */}
          </p>
          <div className="form-grid">
            <div className="form-group">
              <label htmlFor="guestName">Client Name</label>
              <input
                id="guestName"
                type="text"
                className="form-input"
                value={guestName}
                onChange={(e) => setGuestName(e.target.value)}
                placeholder="e.g. John Doe"
              />
            </div>
            <div className="form-group">
              <label htmlFor="guestEmail">Client Email</label>
              <input
                id="guestEmail"
                type="email"
                className="form-input"
                value={guestEmail}
                onChange={(e) => setGuestEmail(e.target.value)}
                placeholder="e.g. john@example.com"
              />
            </div>
            <div className="form-group">
              <label htmlFor="guestPhone">Client Phone</label>
              <input
                id="guestPhone"
                type="tel"
                className="form-input"
                value={guestPhone}
                onChange={(e) => setGuestPhone(e.target.value)}
              />
            </div>
            <div className="form-group">
              <label htmlFor="guestAddress">Client Address</label>
              <textarea
                id="guestAddress"
                className="form-input"
                value={guestAddress}
                onChange={(e) => setGuestAddress(e.target.value)}
                rows={3}
              ></textarea>
            </div>
          </div>
        </div>

        {/* Line Items Section */}
        <div className="admin-section" style={{marginTop: '20px'}}>
          <h2>Line Items</h2>
          <div className="line-items-header" style={{display: 'flex', fontWeight: 'bold', marginBottom: '10px'}}>
            <span style={{flex: 1, marginRight: '10px'}}>Description</span>
            <span style={{width: '80px', marginRight: '10px'}}>Qty</span>
            <span style={{width: '120px', marginRight: '10px'}}>Unit Price</span>
            <span style={{width: '120px', marginRight: '10px'}}>Amount</span>
            <span style={{width: '60px'}}></span>
          </div>
          {lineItems.map((item, index) => (
            <LineItem
              key={index}
              item={item}
              index={index}
              onChange={handleLineItemChange}
              onRemove={removeLineItem}
            />
          ))}
          <button type="button" onClick={addLineItem} className="cta-outline" style={{marginTop: '10px'}}>
            + Add Line Item
          </button>
        </div>
        
        {/* Totals Section */}
        <div className="quote-totals" style={{width: '40%', marginLeft: 'auto', marginTop: '20px'}}>
          <div className="totals-row">
            <span>Subtotal</span>
            <span>R {subtotal.toFixed(2)}</span>
          </div>
          <div className="totals-row">
            <label htmlFor="discount" style={{fontWeight: 600}}>Discount</label>
            <div style={{display: 'flex', alignItems: 'center'}}>
              <span style={{marginRight: '5px'}}>R</span>
              <input
                id="discount"
                type="number"
                step="0.01"
                className="form-input"
                value={discount}
                onChange={(e) => setDiscount(e.target.value)}
                style={{width: '100px', textAlign: 'right', padding: '5px 8px'}}
              />
            </div>
          </div>
          <div className="totals-row grand-total">
            <span>TOTAL</span>
            <span>R {total.toFixed(2)}</span>
          </div>
        </div>

        {/* Submission */}
        <div style={{borderTop: '1px solid #e5e7eb', marginTop: '30px', paddingTop: '20px', textAlign: 'right'}}>
          <button type="button" onClick={() => navigate('/quotes')} className="cta-outline">
            Cancel
          </button>
          <button type="submit" className="cta" disabled={isLoading} style={{marginLeft: '10px'}}>
            {isLoading ? <BarLoader color="#fff" height={20} /> : 'Save Draft Quote'}
          </button>
        </div>
      </form>
    </div>
  );
}

export default CreateQuote;