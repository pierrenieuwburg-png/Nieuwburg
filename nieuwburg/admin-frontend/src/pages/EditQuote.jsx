import React, { useState, useEffect } from 'react';
import { useNavigate, useParams, Link } from 'react-router-dom';
import { BarLoader } from 'react-spinners';

// --- Re-usable Line Item Component ---
// *** MODIFIED: The 'description' input is now a textarea ***
const LineItem = ({ item, index, onChange, onRemove }) => {
  const amount = (item.quantity || 0) * (item.unit_price || 0);
  return (
    <div className="line-item-row">
      <textarea
        placeholder="Description"
        value={item.description || ''}
        onChange={(e) => onChange(index, 'description', e.target.value)}
        className="form-input" // We will style this new textarea
        rows={3} // Start with 3 rows
        style={{flex: 1, marginRight: '10px', resize: 'vertical'}}
      />
      <div className="line-item-inputs">
        <input
          type="number"
          placeholder="Qty"
          value={item.quantity || 0}
          onChange={(e) => onChange(index, 'quantity', e.target.value)}
          className="form-input"
          style={{width: '80px', marginRight: '10px'}}
        />
        <input
          type="number"
          placeholder="Unit Price"
          value={item.unit_price || 0}
          onChange={(e) => onChange(index, 'unit_price', e.target.value)}
          className="form-input"
          style={{width: '120px', marginRight: '10px'}}
        />
        <input
          type="text"
          readOnly
          value={`R ${isNaN(amount) ? '0.00' : amount.toFixed(2)}`}
          className="form-input"
          style={{width: '120px', marginRight: '10px', background: '#f9fafb'}}
        />
        <button type="button" onClick={() => onRemove(index)} className="cta-danger-outline" style={{padding: '10px 15px'}}>X</button>
      </div>
    </div>
  );
};


function EditQuote() {
  const navigate = useNavigate();
  const { quoteId } = useParams();

  // Quote-specific data
  const [clientId, setClientId] = useState(null);
  const [guestName, setGuestName] = useState('');
  const [guestEmail, setGuestEmail] = useState('');
  const [guestPhone, setGuestPhone] = useState('');
  const [guestAddress, setGuestAddress] = useState('');
  const [lineItems, setLineItems] =useState([
    { description: '', quantity: 1, unit_price: 0 }
  ]);
  const [discount, setDiscount] = useState(0);

  // *** NEW: State for locked business settings ***
  const [businessSettings, setBusinessSettings] = useState(null);

  // System state
  const [csrfToken, setCsrfToken] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [originalStatus, setOriginalStatus] = useState("");

  // --- MODIFIED: Data Fetching ---
  useEffect(() => {
    const fetchQuoteData = async () => {
      setIsLoading(true);
      setError(null);
      
      const token = document.querySelector('meta[name="csrf-token"]')?.getAttribute("content");
      setCsrfToken(token || "");

      try {
        // --- Fetch both quote and settings data in parallel ---
        const [quoteRes, settingsRes] = await Promise.all([
          fetch(`/api/admin/quotes/formal/${quoteId}`),
          fetch('/api/admin/business-settings') // New fetch call
        ]);

        if (!quoteRes.ok) {
          throw new Error(`Failed to load quote (Status: ${quoteRes.status})`);
        }
        if (!settingsRes.ok) {
          throw new Error(`Failed to load business settings (Status: ${settingsRes.status})`);
        }

        const data = await quoteRes.json();
        const settingsData = await settingsRes.json(); // New settings data
        
        // Check if quote is editable
        if (data.quote.status !== 'Draft') {
          setError(`This quote is "${data.quote.status}" and can no longer be edited.`);
          setIsLoading(false);
          return;
        }

        // --- Pre-populate state ---
        setClientId(data.client.user_id || null);
        setGuestName(data.client.name || '');
        setGuestEmail(data.client.email || '');
        setGuestPhone(data.client.phone || '');
        setGuestAddress(data.client.address || '');
        setLineItems(data.line_items.length > 0 ? data.line_items : [{ description: '', quantity: 1, unit_price: 0 }]);
        setDiscount(data.quote.discount || 0);
        setOriginalStatus(data.quote.status);
        
        // --- Set new settings state ---
        setBusinessSettings(settingsData);

      } catch (err) {
        console.error("Error fetching data:", err);
        setError(`Failed to load page: ${err.message}`);
      } finally {
        setIsLoading(false);
      }
    };

    fetchQuoteData();
  }, [quoteId]);

  // --- Line Item Handlers (no change) ---
  const handleLineItemChange = (index, field, value) => {
    const updatedItems = [...lineItems];
    updatedItems[index][field] = value;
    setLineItems(updatedItems);
  };

  const addLineItem = () => {
    setLineItems([...lineItems, { description: '', quantity: 1, unit_price: 0 }]);
  };

  const removeLineItem = (index) => {
    if (lineItems.length > 1) {
      const updatedItems = lineItems.filter((_, i) => i !== index);
      setLineItems(updatedItems);
    }
  };

  // --- Calculate Totals (no change) ---
  const subtotal = lineItems.reduce((acc, item) => {
    return acc + (parseFloat(item.quantity) || 0) * (parseFloat(item.unit_price) || 0);
  }, 0);
  const total = subtotal - (parseFloat(discount) || 0);

  // --- Form Submission (no change) ---
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
      const response = await fetch(`/api/admin/quotes/${quoteId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken
        },
        body: JSON.stringify(quoteData)
      });
      const result = await response.json();
      if (!response.ok) {
        throw new Error(result.message || 'Failed to update quote');
      }
      navigate(`/quotes/formal/${quoteId}`, { 
        state: { flashMessage: { type: 'success', text: result.message } } 
      });
    } catch (err) {
      console.error("Error updating quote:", err);
      setError(err.message);
      setIsLoading(false);
    }
  };
  
  // --- RENDER SECTION ---
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
          <h1>Edit Quote</h1>
           <Link to={`/quotes/formal/${quoteId}`} className="cta-outline">Back to Quote</Link>
        </div>
        <div className="flash error">{error}</div>
      </div>
    );
  }

  return (
    <div>
      <div className="admin-header">
        <h1>Edit Quote</h1>
        <p>You are editing a quote currently in "Draft" status.</p>
      </div>

      <form onSubmit={handleSubmit} className="admin-section">
        
        {/* Client Info Section (no change) */}
        <div className="admin-section" style={{background: '#f9fafb', border: '1px solid #e5e7eb', borderRadius: '8px'}}>
          <h2>Client Information</h2>
          <div className="form-grid">
             {/* ... form-groups for guestName, guestEmail, guestPhone, guestAddress ... */}
             <div className="form-group">
              <label htmlFor="guestName">Client Name</label>
              <input
                id="guestName" type="text" className="form-input"
                value={guestName}
                onChange={(e) => setGuestName(e.target.value)}
              />
            </div>
            <div className="form-group">
              <label htmlFor="guestEmail">Client Email</label>
              <input
                id="guestEmail" type="email" className="form-input"
                value={guestEmail}
                onChange={(e) => setGuestEmail(e.target.value)}
              />
            </div>
            <div className="form-group">
              <label htmlFor="guestPhone">Client Phone</label>
              <input
                id="guestPhone" type="tel" className="form-input"
                value={guestPhone}
                onChange={(e) => setGuestPhone(e.target.value)}
              />
            </div>
            <div className="form-group">
              <label htmlFor="guestAddress">Client Address</label>
              <textarea
                id="guestAddress" className="form-input"
                value={guestAddress}
                onChange={(e) => setGuestAddress(e.target.value)}
                rows={3}
              ></textarea>
            </div>
          </div>
        </div>

        {/* --- MODIFIED: Line Items Section --- */}
        <div className="admin-section" style={{marginTop: '20px'}}>
          <h2>Line Items</h2>
          <div className="line-items-header" style={{display: 'flex', fontWeight: 'bold', marginBottom: '10px'}}>
            <span style={{flex: 1, marginRight: '10px'}}>Description</span>
            <span style={{width: '320px'}}>Qty / Price / Actions</span>
          </div>
          {lineItems.map((item, index) => (
            <LineItem
              key={item.id || index}
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
        
        {/* Totals Section (no change) */}
        <div className="quote-totals" style={{width: '40%', marginLeft: 'auto', marginTop: '20px'}}>
           {/* ... totals-rows for Subtotal, Discount, and TOTAL ... */}
           <div className="totals-row">
            <span>Subtotal</span>
            <span>R {subtotal.toFixed(2)}</span>
          </div>
          <div className="totals-row">
            <label htmlFor="discount" style={{fontWeight: 600}}>Discount</label>
            <div style={{display: 'flex', alignItems: 'center'}}>
              <span style={{marginRight: '5px'}}>R</span>
              <input
                id="discount" type="number" step="0.01" className="form-input"
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

        {/* --- NEW: Locked Terms Section --- */}
        <div className="admin-section locked-settings-section" style={{marginTop: '30px'}}>
          <h2>Terms & Conditions (Locked)</h2>
          <p>These are your global business terms and will be automatically added to the final quote. To edit these, go to Business Settings.</p>
          <textarea
            className="form-input"
            readOnly
            disabled
            value={businessSettings?.terms_and_conditions || 'Loading...'}
            rows={8}
          />
        </div>

        {/* Submission (no change) */}
        <div style={{borderTop: '1px solid #e5e7eb', marginTop: '30px', paddingTop: '20px', textAlign: 'right'}}>
          <button type="button" onClick={() => navigate(`/quotes/formal/${quoteId}`)} className="cta-outline">
            Cancel
          </button>
          <button type="submit" className="cta" disabled={isLoading} style={{marginLeft: '10px'}}>
            {isLoading ? <BarLoader color="#fff" height={20} /> : 'Save Changes'}
          </button>
        </div>
      </form>
    </div>
  );
}

export default EditQuote;