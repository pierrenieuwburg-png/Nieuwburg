import React, { useState, useEffect } from 'react';
import { BarLoader } from 'react-spinners';

// --- Re-usable Component for the Clause Form ---
const ClauseForm = ({ currentClause, onSave, onCancel, csrfToken }) => {
  const [name, setName] = useState(currentClause.name || '');
  const [text, setText] = useState(currentClause.text || '');
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSaving(true);
    setError(null);
    
    const url = currentClause.id 
      ? `/api/admin/service-clauses/${currentClause.id}`
      : '/api/admin/service-clauses';
    const method = currentClause.id ? 'PUT' : 'POST';

    try {
      const response = await fetch(url, {
        method: method,
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({ name, text })
      });
      
      const result = await response.json();
      if (!response.ok) {
        throw new Error(result.message || 'Failed to save clause');
      }
      onSave(result); // Pass the new/updated clause back to parent
    } catch (err) {
      setError(err.message);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="admin-section" style={{background: '#f9fafb'}}>
      <h3>{currentClause.id ? 'Edit Clause' : 'Add New Clause'}</h3>
      {error && <div className="flash error">{error}</div>}
      <div className="form-group">
        <label htmlFor="clause_name">Clause Name</label>
        <input
          id="clause_name" type="text" className="form-input"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="e.g. Window Washing Liability"
        />
      </div>
      <div className="form-group" style={{marginTop: '10px'}}>
        <label htmlFor="clause_text">Clause Text</label>
        <textarea
          id="clause_text" className="form-input"
          value={text}
          onChange={(e) => setText(e.target.value)}
          rows={5}
        />
      </div>
      <div style={{textAlign: 'right', marginTop: '15px'}}>
        <button type="button" className="cta-outline" onClick={onCancel}>Cancel</button>
        <button type="submit" className="cta" disabled={isSaving} style={{marginLeft: '10px'}}>
          {isSaving ? 'Saving...' : 'Save Clause'}
        </button>
      </div>
    </form>
  );
};


// --- Main Business Settings Page ---
function BusinessSettings() {
  const [settings, setSettings] = useState({
    business_name: '',
    business_address: '',
    registration_number: '',
    default_terms: ''
  });
  const [clauses, setClauses] = useState([]);
  const [currentClause, setCurrentClause] = useState(null); // null = no form, {} = new, {id...} = editing
  
  const [csrfToken, setCsrfToken] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState(null);
  const [flashMessage, setFlashMessage] = useState(null);

  // --- Fetch initial settings and clauses data ---
  useEffect(() => {
    const fetchData = async () => {
      setIsLoading(true);
      setError(null);
      
      const token = document.querySelector('meta[name="csrf-token"]')?.getAttribute("content");
      setCsrfToken(token || "");

      try {
        const [settingsRes, clausesRes] = await Promise.all([
          fetch('/api/admin/business-settings'),
          fetch('/api/admin/service-clauses')
        ]);
        
        if (!settingsRes.ok) throw new Error('Failed to fetch settings');
        if (!clausesRes.ok) throw new Error('Failed to fetch clauses');
        
        const settingsData = await settingsRes.json();
        const clausesData = await clausesRes.json();
        
        setSettings(settingsData);
        setClauses(clausesData);
      } catch (err) {
        setError(err.message);
      } finally {
        setIsLoading(false);
      }
    };
    fetchData();
  }, []);

  // --- Handle Global Settings Form ---
  const handleChange = (e) => {
    const { name, value } = e.target;
    setSettings(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSaving(true);
    setFlashMessage(null);

    try {
      const response = await fetch('/api/admin/business-settings', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
        body: JSON.stringify(settings)
      });
      
      const result = await response.json();
      if (!response.ok) throw new Error(result.message || 'Failed to save settings');

      setSettings(result.settings);
      setFlashMessage({ type: 'success', text: result.message });
    } catch (err) {
      setError(err.message);
      setFlashMessage({ type: 'error', text: err.message });
    } finally {
      setIsSaving(false);
    }
  };

  // --- Handle Clause Library Actions ---
  const handleSaveClause = (savedClause) => {
    if (currentClause.id) {
      // It was an update
      setClauses(clauses.map(c => c.id === savedClause.id ? savedClause : c));
    } else {
      // It was a new clause
      setClauses([...clauses, savedClause]);
    }
    setCurrentClause(null); // Close the form
  };
  
  const handleDeleteClause = async (clauseId) => {
    if (!window.confirm("Are you sure you want to delete this clause?")) return;
    
    try {
      const response = await fetch(`/api/admin/service-clauses/${clauseId}`, {
        method: 'DELETE',
        headers: { 'X-CSRFToken': csrfToken }
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.message);
      
      setClauses(clauses.filter(c => c.id !== clauseId));
      setFlashMessage({ type: 'success', text: result.message });
      
    } catch (err) {
      setFlashMessage({ type: 'error', text: err.message });
    }
  };

  if (isLoading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', padding: '100px' }}>
        <BarLoader color="#006ac6" width="50%" />
      </div>
    );
  }

  return (
    <div>
      <div className="admin-header">
        <h1>Business Settings</h1>
        <p>Manage your global business information and re-usable T&C clauses.</p>
      </div>

      {flashMessage && (
        <div className={`flash ${flashMessage.type}`} style={{ marginBottom: '20px' }}>
          {flashMessage.text}
        </div>
      )}
      {error && !flashMessage && (
        <div className="flash error" style={{ marginBottom: '20px' }}>
          {error}
        </div>
      )}

      {/* --- Global Settings Form --- */}
      <form onSubmit={handleSubmit} className="admin-section">
        <h2>Global Information</h2>
        <div className="form-grid">
          <div className="form-group">
            <label htmlFor="business_name">Business Name</label>
            <input
              id="business_name" name="business_name" type="text"
              className="form-input" value={settings.business_name}
              onChange={handleChange}
            />
          </div>
          <div className="form-group">
            <label htmlFor="registration_number">Registration Number</label>
            <input
              id="registration_number" name="registration_number" type="text"
              className="form-input" value={settings.registration_number}
              onChange={handleChange}
            />
          </div>
        </div>
        <div className="form-group" style={{marginTop: '20px'}}>
          <label htmlFor="business_address">Business Address</label>
          <input
            id="business_address" name="business_address" type="text"
            className="form-input" value={settings.business_address}
            onChange={handleChange}
          />
        </div>
        <div className="form-group" style={{marginTop: '20px'}}>
          <label htmlFor="default_terms">Default Terms & Conditions</label>
          <p style={{fontSize: '0.9rem', color: '#6b7280', marginTop: '-10px'}}>
            This is the base set of terms for all new quotes.
          </p>
          <textarea
            id="default_terms" name="default_terms"
            className="form-input" rows={10}
            value={settings.default_terms}
            onChange={handleChange}
          />
        </div>
        <div style={{borderTop: '1Fpx solid #e5e7eb', marginTop: '30px', paddingTop: '20px', textAlign: 'right'}}>
          <button type="submit" className="cta" disabled={isSaving}>
            {isSaving ? 'Saving...' : 'Save Global Settings'}
          </button>
        </div>
      </form>
      
      {/* --- NEW: T&C Clause Library --- */}
      <div className="admin-section" style={{marginTop: '30px'}}>
        <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
          <h2>T&C Clause Library</h2>
          <button 
            type="button" 
            className="cta" 
            onClick={() => setCurrentClause({})}
            disabled={currentClause != null}
          >
            + Add New Clause
          </button>
        </div>
        <p style={{fontSize: '0.9rem', color: '#6b7280', marginTop: '-10px'}}>
          Create re-usable T&C snippets to link to specific services.
        </p>

        {/* --- The Add/Edit Form will appear here --- */}
        {currentClause && (
          <ClauseForm
            currentClause={currentClause}
            onSave={handleSaveClause}
            onCancel={() => setCurrentClause(null)}
            csrfToken={csrfToken}
          />
        )}
        
        {/* --- List of Existing Clauses --- */}
        <table className="data-table" style={{marginTop: '20px'}}>
          <thead>
            <tr>
              <th>Clause Name</th>
              <th>Clause Text (Snippet)</th>
              <th style={{width: '120px'}}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {clauses.length === 0 && (
              <tr><td colSpan="3">No T&C clauses created yet.</td></tr>
            )}
            {clauses.map(clause => (
              <tr key={clause.id}>
                <td data-label="Name"><strong>{clause.name}</strong></td>
                <td data-label="Snippet">{clause.text.substring(0, 75)}...</td>
                <td data-label="Actions" className="actions-cell">
                  <button 
                    type="button" 
                    className="cta-outline-small"
                    onClick={() => setCurrentClause(clause)}
                  >
                    Edit
                  </button>
                  <button 
                    type="button" 
                    className="cta-danger-outline-small"
                    onClick={() => handleDeleteClause(clause.id)}
                    style={{marginLeft: '5px'}}
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      
    </div>
  );
}

export default BusinessSettings;