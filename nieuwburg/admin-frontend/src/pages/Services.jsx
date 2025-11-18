import React, { useState, useEffect } from 'react';
import { BarLoader } from 'react-spinners';

// --- NEW: Edit Service Modal Component ---
const EditServiceModal = ({ service, allClauses, onSave, onClose, csrfToken }) => {
  const [name, setName] = useState('');
  const [time, setTime] = useState(0);
  const [selectedClauseIds, setSelectedClauseIds] = useState(new Set());
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState(null);

  // Populate form when the 'service' prop changes
  useEffect(() => {
    if (service) {
      setIsLoading(true);
      setError(null);
      
      // Fetch the full service details, including its linked clauses
      fetch(`/api/admin/service-items/${service.id}`)
        .then(res => {
          if (!res.ok) throw new Error('Failed to fetch service details');
          return res.json();
        })
        .then(data => {
          setName(data.name);
          setTime(data.estimated_time_mins);
          setSelectedClauseIds(new Set(data.linked_clause_ids));
        })
        .catch(err => setError(err.message))
        .finally(() => setIsLoading(false));
    }
  }, [service]);

  const handleCheckboxChange = (clauseId) => {
    const newSet = new Set(selectedClauseIds);
    if (newSet.has(clauseId)) {
      newSet.delete(clauseId);
    } else {
      newSet.add(clauseId);
    }
    setSelectedClauseIds(newSet);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSaving(true);
    setError(null);

    const updatedServiceData = {
      name: name,
      estimated_time_mins: parseInt(time, 10) || 0,
      linked_clause_ids: Array.from(selectedClauseIds) // Convert Set to Array
    };

    try {
      const response = await fetch(`/api/admin/service-items/${service.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken
        },
        body: JSON.stringify(updatedServiceData)
      });
      
      const result = await response.json();
      if (!response.ok) {
        throw new Error(result.message || 'Failed to save service');
      }
      onSave(result); // Pass the updated service back to the parent
    } catch (err) {
      setError(err.message);
    } finally {
      setIsSaving(false);
    }
  };

  // State for the loading spinner inside the modal
  const [isLoading, setIsLoading] = useState(true);

  return (
    <div className="modal-backdrop">
      <div className="modal-content" style={{maxWidth: '600px'}}>
        <div className="modal-header">
          <h2>Edit Service: {service.name}</h2>
          <button onClick={onClose} className="modal-close-btn">&times;</button>
        </div>
        
        {isLoading ? (
          <div style={{ padding: '40px', textAlign: 'center' }}>
            <BarLoader color="#006ac6" width="100%" />
          </div>
        ) : (
          <form onSubmit={handleSubmit}>
            <div className="modal-body">
              {error && <div className="flash error">{error}</div>}
              
              <div className="form-group">
                <label htmlFor="service_name">Service Name</label>
                <input
                  id="service_name" type="text" className="form-input"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                />
              </div>
              <div className="form-group" style={{marginTop: '15px'}}>
                <label htmlFor="service_time">Est. Time (minutes)</label>
                <input
                  id="service_time" type="number" className="form-input"
                  value={time}
                  onChange={(e) => setTime(e.target.value)}
                />
              </div>
              
              <div className="form-group" style={{marginTop: '20px'}}>
                <label>Linked T&C Clauses</label>
                <p style={{fontSize: '0.9rem', color: '#6b7280', marginTop: '-5px'}}>
                  Select which T&C snippets apply when this service is quoted.
                </p>
                <div className="checkbox-list">
                  {allClauses.length === 0 && <p>No T&C clauses found. Go to Business Settings to create them.</p>}
                  
                  {allClauses.map(clause => (
                    <label key={clause.id} className="checkbox-label">
                      <input
                        type="checkbox"
                        checked={selectedClauseIds.has(clause.id)}
                        onChange={() => handleCheckboxChange(clause.id)}
                      />
                      {clause.name}
                    </label>
                  ))}
                </div>
              </div>
            </div>
            
            <div className="modal-footer">
              <button type="button" className="cta-outline" onClick={onClose}>Cancel</button>
              <button type="submit" className="cta" disabled={isSaving} style={{marginLeft: '10px'}}>
                {isSaving ? 'Saving...' : 'Save Changes'}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};


// --- Main Services Page Component ---
function Services() {
  const [categories, setCategories] = useState([]);
  const [allClauses, setAllClauses] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [editingService, setEditingService] = useState(null); // null or service object
  const [csrfToken, setCsrfToken] = useState("");

  // Fetch all categories, items, and T&C clauses on mount
  useEffect(() => {
    const token = document.querySelector('meta[name="csrf-token"]')?.getAttribute("content");
    setCsrfToken(token || "");
  
    const fetchData = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const [categoriesRes, clausesRes] = await Promise.all([
          fetch('/api/admin/service-categories'),
          fetch('/api/admin/service-clauses')
        ]);
        
        if (!categoriesRes.ok) throw new Error('Failed to fetch services');
        if (!clausesRes.ok) throw new Error('Failed to fetch T&C clauses');
        
        const categoriesData = await categoriesRes.json();
        const clausesData = await clausesRes.json();
        
        setCategories(categoriesData);
        setAllClauses(clausesData);
      } catch (err) {
        setError(err.message);
      } finally {
        setIsLoading(false);
      }
    };
    fetchData();
  }, []);

  // Handler to update the state after saving the modal
  const handleSaveService = (updatedService) => {
    // Find the category and item and update its name
    const newCategories = categories.map(category => ({
      ...category,
      items: category.items.map(item => 
        item.id === updatedService.id ? { ...item, name: updatedService.name, estimated_time_mins: updatedService.estimated_time_mins } : item
      )
    }));
    setCategories(newCategories);
    setEditingService(null); // Close the modal
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
        <h1>Services</h1>
        <p>Manage your service items and link them to T&C clauses.</p>
        {/* We can add a "New Service" button here later */}
      </div>

      {error && <div className="flash error">{error}</div>}

      {categories.map(category => (
        <div key={category.id} className="admin-section">
          <h2>{category.name}</h2>
          <p>{category.description}</p>
          <table className="data-table">
            <thead>
              <tr>
                <th>Service Name</th>
                <th>Est. Time (Mins)</th>
                <th style={{width: '100px'}}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {category.items.length === 0 && (
                <tr><td colSpan="3">No services found in this category.</td></tr>
              )}
              {category.items.map(item => (
                <tr key={item.id}>
                  <td data-label="Name"><strong>{item.name}</strong></td>
                  <td data-label="Est. Time">{item.estimated_time_mins}</td>
                  <td data-label="Actions" className="actions-cell">
                    <button 
                      className="cta-outline-small"
                      onClick={() => setEditingService(item)}
                    >
                      Edit
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ))}

      {/* --- Render the Edit Modal --- */}
      {editingService && (
        <EditServiceModal
          service={editingService}
          allClauses={allClauses}
          onSave={handleSaveService}
          onClose={() => setEditingService(null)}
          csrfToken={csrfToken}
        />
      )}
    </div>
  );
}

export default Services;