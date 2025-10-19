import React, { useState, useEffect } from 'react';

// Reusable Input Field component (optional, but good practice)
const InputField = ({ label, id, name, type = 'text', value, onChange, required = false, ...props }) => (
  <div className="form-group">
    <label htmlFor={id}>{label}</label>
    <input
      type={type}
      id={id}
      name={name}
      value={value}
      onChange={onChange}
      className="form-control"
      required={required}
      {...props}
    />
  </div>
);

// Reusable TextArea Field component (optional)
const TextAreaField = ({ label, id, name, value, onChange, required = false, rows = 3, ...props }) => (
    <div className="form-group">
        <label htmlFor={id}>{label}</label>
        <textarea
            id={id}
            name={name}
            value={value}
            onChange={onChange}
            className="form-control"
            required={required}
            rows={rows}
            {...props}
        />
    </div>
);


function AddClientModal({ isOpen, onClose, onClientAdded }) {
  const [formData, setFormData] = useState({
    full_name: '',
    email: '',
    phone_number: '',
    address: '',
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [csrfToken, setCsrfToken] = useState('');

  // Get CSRF token when component mounts (or modal opens)
  useEffect(() => {
    const token = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
    if (token) {
        setCsrfToken(token);
    } else {
        console.error("CSRF token not found in meta tag!");
        setError("Configuration error: CSRF token missing.");
    }
  }, [isOpen]); // Re-check if modal re-opens, though it shouldn't change

  // Reset form when modal opens or closes
  useEffect(() => {
    if (!isOpen) {
      setFormData({
        full_name: '',
        email: '',
        phone_number: '',
        address: '',
      });
      setError(null);
      setIsSubmitting(false);
    }
  }, [isOpen]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prevData) => ({
      ...prevData,
      [name]: value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);

    if (!csrfToken) {
        setError("Cannot submit form: CSRF token is missing.");
        setIsSubmitting(false);
        return;
    }

    try {
      const response = await fetch('/api/admin/clients', { // API endpoint from api.py
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken, // Include CSRF token
        },
        body: JSON.stringify(formData),
      });

      const result = await response.json();

      if (response.ok) {
        onClientAdded(result.message || 'Client added successfully!'); // Call parent callback
        onClose(); // Close the modal
      } else {
        setError(result.message || 'An error occurred.');
      }
    } catch (err) {
      console.error('Error submitting form:', err);
      setError('A network error occurred. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isOpen) {
    return null; // Don't render anything if the modal is closed
  }

  // Use class names similar to the original modal for styling
  return (
    <div id="add-client-modal" className="modal-overlay simple-modal" style={{ display: 'flex' }}>
      <div className="modal-content auth-modal-content" style={{ maxWidth: '500px' }}>
        <button
          id="close-add-client-modal"
          className="modal-close"
          aria-label="Close form"
          onClick={onClose}
          disabled={isSubmitting}
        >
          &times;
        </button>
        <h2 className="auth-title">Add New Client</h2>

        {error && (
          <div id="add-client-error-message" className="flash error" style={{ marginTop: 0 }}>
            {error}
          </div>
        )}

        <form id="add-client-form" className="auth-form-modal active" style={{ paddingTop: '15px' }} onSubmit={handleSubmit}>
          {/* CSRF token is sent via header, no hidden input needed unless preferred */}
          {/* <input type="hidden" name="csrf_token" value={csrfToken} /> */}

          <InputField
            label="Full Name"
            id="add-client-full_name"
            name="full_name"
            value={formData.full_name}
            onChange={handleChange}
            required
          />
          <InputField
            label="Email"
            id="add-client-email"
            name="email"
            type="email"
            value={formData.email}
            onChange={handleChange}
            required
          />
          <InputField
            label="Phone Number"
            id="add-client-phone_number"
            name="phone_number"
            type="tel"
            value={formData.phone_number}
            onChange={handleChange}
          />
          <TextAreaField
            label="Address"
            id="add-client-address"
            name="address"
            value={formData.address}
            onChange={handleChange}
            rows={3}
          />

          <button type="submit" className="cta" disabled={isSubmitting}>
            {isSubmitting ? 'Saving...' : 'Save Client'}
          </button>
        </form>
      </div>
    </div>
  );
}

export default AddClientModal;