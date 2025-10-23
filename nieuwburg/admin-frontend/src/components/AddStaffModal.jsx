import React, { useState, useEffect } from 'react';

// Reusable Input Field component (can reuse from AddClientModal or define here)
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

// Reusable TextArea Field component (can reuse or define here)
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


function AddStaffModal({ isOpen, onClose, onStaffAdded }) {
  const [formData, setFormData] = useState({
    full_name: '',
    email: '',
    phone_number: '',
    address: '',
    id_number: '',
    send_activation_email: true, // Default to checked
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [csrfToken, setCsrfToken] = useState('');

  // Get CSRF token
  useEffect(() => {
    const token = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
    if (token) {
        setCsrfToken(token);
    } else {
        console.error("CSRF token not found!");
        setError("Configuration error: CSRF token missing.");
    }
  }, [isOpen]);

  // Reset form when modal opens or closes
  useEffect(() => {
    if (!isOpen) {
      setFormData({
        full_name: '',
        email: '',
        phone_number: '',
        address: '',
        id_number: '',
        send_activation_email: true, // Reset checkbox state
      });
      setError(null);
      setIsSubmitting(false);
    }
  }, [isOpen]);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData((prevData) => ({
      ...prevData,
      [name]: type === 'checkbox' ? checked : value,
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

    // Ensure id_number is null if empty, or enforce length validation client-side if needed
    const dataToSend = { ...formData };
    if (!dataToSend.id_number) {
        dataToSend.id_number = null; // Send null if empty
    }

    try {
      const response = await fetch('/api/admin/staff', { // API endpoint from api.py
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken,
        },
        body: JSON.stringify(dataToSend), // Send processed data
      });

      const result = await response.json();

      if (response.ok) {
        onStaffAdded(result.message || 'Staff member added successfully!'); // Call parent callback
        onClose(); // Close the modal
      } else {
        setError(result.message || 'An error occurred.');
      }
    } catch (err) {
      console.error('Error submitting staff form:', err);
      setError('A network error occurred. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isOpen) {
    return null;
  }

  // Use class names similar to the original modal
  return (
    <div id="add-staff-modal" className="modal-overlay simple-modal" style={{ display: 'flex' }}>
      <div className="modal-content auth-modal-content" style={{ maxWidth: '500px' }}>
        <button
          id="close-add-staff-modal"
          className="modal-close"
          aria-label="Close form"
          onClick={onClose}
          disabled={isSubmitting}
        >
          &times;
        </button>
        <h2 className="auth-title">Add New Staff Member</h2>

        {error && (
          <div id="add-staff-error-message" className="flash error" style={{ marginTop: 0 }}>
            {error}
          </div>
        )}

        <form id="add-staff-form" className="auth-form-modal active" style={{ paddingTop: '15px' }} onSubmit={handleSubmit}>

          <InputField
            label="Full Name"
            id="add-staff-full_name"
            name="full_name"
            value={formData.full_name}
            onChange={handleChange}
            required
          />
          <InputField
            label="Email"
            id="add-staff-email"
            name="email"
            type="email"
            value={formData.email}
            onChange={handleChange}
            required
          />
          <InputField
            label="Phone Number"
            id="add-staff-phone_number"
            name="phone_number"
            type="tel"
            value={formData.phone_number}
            onChange={handleChange}
          />
          <TextAreaField
            label="Address"
            id="add-staff-address"
            name="address"
            value={formData.address}
            onChange={handleChange}
            rows={3}
          />
          <InputField
            label="South African ID Number"
            id="add-staff-id_number"
            name="id_number"
            value={formData.id_number}
            onChange={handleChange}
            maxLength={13} // HTML5 validation
            // Add pattern="\d{13}" for stricter validation if desired
          />

          {/* Send Activation Email Checkbox - matches style/structure from Flask template */}
          <div className="form-group" style={{ flexDirection: 'row', alignItems: 'center', gap: '10px', backgroundColor: '#f4f7fa', padding: '10px', borderRadius: '8px' }}>
            <input
                type="checkbox"
                id="send_activation_email"
                name="send_activation_email"
                checked={formData.send_activation_email}
                onChange={handleChange}
                style={{ width: '20px', height: '20px' }}
            />
            <label htmlFor="send_activation_email" style={{ fontWeight: 'bold', marginBottom: 0 }}>
                Send activation email to staff member
            </label>
          </div>

          <button type="submit" className="cta" disabled={isSubmitting}>
            {isSubmitting ? 'Saving...' : 'Save Staff Member'}
          </button>
        </form>
      </div>
    </div>
  );
}

export default AddStaffModal;