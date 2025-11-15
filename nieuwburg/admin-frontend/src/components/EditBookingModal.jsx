import React, { useState, useEffect, useCallback } from 'react';
import { BarLoader } from 'react-spinners';

function EditBookingModal({ isOpen, onClose, jobId, onJobUpdated }) {
  const [formData, setFormData] = useState({
    scheduled_date: '',
    start_time: '',
    staff_id: '',
    status: '',
    notes: ''
  });
  const [allStaff, setAllStaff] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState(null);
  const [originalJob, setOriginalJob] = useState(null); // To compare changes

  // Fetch job details and staff list when modal opens
  const fetchModalData = useCallback(async () => {
    if (!isOpen || !jobId) return;

    setIsLoading(true);
    setError(null);
    try {
      const [jobResponse, staffResponse] = await Promise.all([
        fetch(`/api/admin/jobs/${jobId}`),
        fetch('/api/admin/staff/all')
      ]);

      if (!jobResponse.ok) {
        throw new Error(`Failed to fetch job details (${jobResponse.status})`);
      }
      const jobData = await jobResponse.json();
      
      if (!staffResponse.ok) {
        throw new Error(`Failed to fetch staff list (${staffResponse.status})`);
      }
      const staffData = await staffResponse.json();

      // Set form with fetched data
      setFormData({
        scheduled_date: jobData.scheduled_date || '',
        start_time: jobData.start_time || '',
        staff_id: jobData.assigned_staff_id || '', // API sends first staff ID
        status: jobData.status || 'Scheduled',
        notes: jobData.notes || ''
      });
      setOriginalJob(jobData); // Store original data
      setAllStaff(staffData);

    } catch (err) {
      console.error("Error fetching edit modal data:", err);
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  }, [isOpen, jobId]);

  useEffect(() => {
    fetchModalData();
  }, [fetchModalData]); // Runs when isOpen or jobId changes

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSaving(true);
    setError(null);

    try {
      const response = await fetch(`/api/admin/jobs/${jobId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.message || `Failed to update job (Status: ${response.status})`);
      }
      
      const result = await response.json();
      onJobUpdated(result.message); // Call parent handler to refresh and close

    } catch (err) {
      console.error("Error saving job:", err);
      setError(err.message);
    } finally {
      setIsSaving(false);
    }
  };

  const renderLoader = () => (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '15rem' }}>
      <BarLoader color="#4A90E2" width="50%" />
    </div>
  );

  return (
    <div 
      className={`react-modal-overlay simple-modal ${isOpen ? 'modal-open' : ''}`} 
      onClick={onClose}
    >
      <div className="modal-content auth-modal-content" style={{ maxWidth: '500px' }} onClick={e => e.stopPropagation()}>
        <button type="button" className="modal-close" aria-label="Close modal" onClick={onClose}>&times;</button>
        <h2 className="auth-title">Edit Booking #{jobId}</h2>
        
        {error && <div className="flash error mb-4">{error}</div>}

        {isLoading ? (
          renderLoader()
        ) : (
          <form onSubmit={handleSubmit} className="form-layout mt-4">
            {originalJob && (
                <div className="form-info-box mb-4">
                  <p><strong>Client:</strong> {originalJob.client_name}</p>
                  <p><strong>Service:</strong> {originalJob.service_name}</p>
                </div>
            )}
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="form-group">
                <label htmlFor="scheduled_date">Date</label>
                <input
                  type="date"
                  id="scheduled_date"
                  name="scheduled_date"
                  className="form-control"
                  value={formData.scheduled_date}
                  onChange={handleChange}
                  required
                />
              </div>
              <div className="form-group">
                <label htmlFor="start_time">Time</label>
                <input
                  type="time"
                  id="start_time"
                  name="start_time"
                  className="form-control"
                  value={formData.start_time}
                  onChange={handleChange}
                  required
                />
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="staff_id">Assign Staff</label>
              <select
                id="staff_id"
                name="staff_id"
                className="form-control"
                value={formData.staff_id}
                onChange={handleChange}
                required
              >
                <option value="">Select Staff...</option>
                {allStaff.map(staff => (
                  <option key={staff.id} value={staff.id}>{staff.full_name}</option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="status">Status</label>
              <select
                id="status"
                name="status"
                className="form-control"
                value={formData.status}
                onChange={handleChange}
                required
              >
                <option value="Scheduled">Scheduled</option>
                <option value="In Progress">In Progress</option>
                <option value="Completed">Completed</option>
                <option value="Cancelled">Cancelled</option>
              </select>
            </div>
            
            <div className="form-group">
                <label htmlFor="notes">Notes</label>
                <textarea
                    id="notes"
                    name="notes"
                    className="form-control"
                    rows="3"
                    value={formData.notes}
                    onChange={handleChange}
                    placeholder="Add internal notes..."
                ></textarea>
            </div>

            <div className="form-actions">
              <button
                type="button"
                className="cta-outline"
                onClick={onClose}
                disabled={isSaving}
              >
                Cancel
              </button>
              <button
                type="submit"
                className="cta"
                disabled={isLoading || isSaving}
              >
                {isSaving ? 'Saving...' : 'Save Changes'}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}

export default EditBookingModal;