import React, { useState, useEffect } from 'react';
import { BarLoader } from 'react-spinners';

// Reusable InputField component (borrowed from AddClientModal.jsx for consistency)
const InputField = ({ label, id, name, type = 'text', value, onChange, required = false, ...props }) => (
    <div className="form-group">
      <label htmlFor={id} className="form-label">{label}</label>
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

// Reusable SelectField component (based on InputField for consistency)
const SelectField = ({ label, id, name, value, onChange, required = false, children, ...props }) => (
    <div className="form-group">
        <label htmlFor={id} className="form-label">{label}</label>
        <select
            id={id}
            name={name}
            value={value}
            onChange={onChange}
            className="form-control"
            required={required}
            {...props}
        >
            {children}
        </select>
    </div>
);


function ScheduleBookingModal({ isOpen, onClose, booking, onScheduled }) {
  const [staffList, setStaffList] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);
  
  // Form state
  const [selectedStaff, setSelectedStaff] = useState('');
  const [scheduledDate, setScheduledDate] = useState('');
  const [scheduledTime, setScheduledTime] = useState('09:00'); // Default to 9 AM

  // Fetch available staff when the modal opens (and booking is present)
  useEffect(() => {
    if (isOpen && booking) {
      // Reset form on open
      setError(null);
      setSelectedStaff('');
      setScheduledDate('');
      setScheduledTime('09:00');
      setIsLoading(true);

      const fetchStaff = async () => {
        try {
          // Use the existing API endpoint for staff
          const response = await fetch('/api/admin/staff/all'); 
          if (!response.ok) throw new Error('Failed to fetch staff list');
          const data = await response.json();
          setStaffList(data);
        } catch (err) {
          setError(err.message);
        } finally {
          setIsLoading(false);
        }
      };
      fetchStaff();
    }
  }, [isOpen, booking]); // Re-run if the modal is opened or the booking changes

  //if (!isOpen) {
    //return null; // Don't render anything if not open
  //}

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      // Call the API endpoint we created in routes/api.py
      const response = await fetch('/api/admin/jobs/schedule', { 
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          // --- THIS IS THE FIX ---
          // The API route expects 'quote_request_id', not 'booking_id'
          quote_request_id: booking.id, 
          // -----------------------
          staff_id: selectedStaff,
          scheduled_date: scheduledDate,
          scheduled_time: scheduledTime,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.message || 'Failed to schedule job.');
      }

      // Success! Call the onScheduled prop from Bookings.jsx
      onScheduled(data.message); 
      onClose(); // Close the modal

    } catch (err) {
      setError(err.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Render modal content using the same structure as AddClientModal.jsx
  return (
    <div className={`react-modal-overlay simple-modal ${isOpen ? 'modal-open' : ''}`}>
      <div className="modal-content auth-modal-content" style={{ maxWidth: '600px' }}>
        <button
            type="button"
            className="modal-close"
            aria-label="Close form"
            onClick={onClose}
            disabled={isSubmitting}
        >
          &times;
        </button>
        <h2 className="auth-title">Schedule Job for Booking #{booking?.id}</h2>
        
        {isLoading ? (
          <div className="flex justify-center items-center h-48">
            <BarLoader color="#4A90E2" width="50%" />
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="auth-form-modal active" style={{ paddingTop: '15px' }}>
            
            {error && (
                <div className="flash error" style={{ marginTop: 0, marginBottom: '15px' }}>
                    {error}
                </div>
            )}

            {/* Booking Details (Read-only) */}
            <div className="mb-4 p-3 bg-gray-50 rounded border">
              <p><strong>Client:</strong> {booking?.client_name}</p>
              <p><strong>Service:</strong> {booking?.service_name}</p>
              <p><strong>Requested:</strong> {booking?.requested_date}</p>
              <p><strong>Notes/Address:</strong> {booking?.notes}</p>
            </div>

            {/* Scheduling Form */}
            <SelectField
              label="Assign Staff"
              id="staff_select"
              name="staff_select"
              value={selectedStaff}
              onChange={(e) => setSelectedStaff(e.target.value)}
              required
            >
              <option value="" disabled>Select a staff member...</option>
              {staffList.map(staff => (
                <option key={staff.id} value={staff.id}>
                  {staff.full_name} ({staff.email})
                </option>
              ))}
            </SelectField>

            <div className="flex gap-4">
              <div className="form-group flex-1">
                <label htmlFor="scheduled_date" className="form-label">Date</label>
                <input
                  type="date"
                  id="scheduled_date"
                  name="scheduled_date"
                  className="form-control"
                  value={scheduledDate}
                  onChange={(e) => setScheduledDate(e.target.value)}
                  required
                />
              </div>
              <div className="form-group flex-1">
                <label htmlFor="scheduled_time" className="form-label">Time</label>
                <input
                  type="time"
                  id="scheduled_time"
                  name="scheduled_time"
                  className="form-control"
                  value={scheduledTime}
                  onChange={(e) => setScheduledTime(e.target.value)}
                  required
                />
              </div>
            </div>

            {/* Footer buttons to match AddClientModal style */}
            <div className="modal-footer-custom" style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px', paddingTop: '20px' }}>
              <button 
                type="button" 
                className="btn btn-secondary" // Using a common secondary button style
                onClick={onClose} 
                disabled={isSubmitting}
              >
                Cancel
              </button>
              <button 
                type="submit" 
                className="cta" // Using the primary 'cta' class
                disabled={isSubmitting}
              >
                {isSubmitting ? 'Scheduling...' : 'Schedule Job'}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}

export default ScheduleBookingModal;