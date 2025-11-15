import React, { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom'; // Keep Link if used elsewhere, otherwise remove
import FullCalendar from '@fullcalendar/react';
import dayGridPlugin from '@fullcalendar/daygrid';
import timeGridPlugin from '@fullcalendar/timegrid';
import interactionPlugin from '@fullcalendar/interaction';
import { BarLoader } from 'react-spinners';

import ScheduleBookingModal from '../components/ScheduleBookingModal';
import AddManualBookingModal from '../components/AddManualBookingModal';
import DayBookingsModal from '../components/DayBookingsModal';
// --- 1. IMPORT THE EDIT MODAL ---
import EditBookingModal from '../components/EditBookingModal';


// Helper function to format dates (Keep if needed elsewhere)
const formatDate = (isoString) => {
  if (!isoString) return 'N/A';
  try {
    // Simplified format example
    return new Date(isoString).toLocaleDateString('en-ZA', {
      day: '2-digit', month: 'short', year: 'numeric',
    });
  } catch (error) {
    return isoString;
  }
};

function Bookings() {
  // Existing state for data
  const [newBookings, setNewBookings] = useState([]);
  const [currentJobs, setCurrentJobs] = useState([]);
  const [calendarEvents, setCalendarEvents] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [flashMessage, setFlashMessage] = useState(null);

  // Existing state for Schedule Modal
  const [isScheduleModalOpen, setIsScheduleModalOpen] = useState(false);
  const [selectedBooking, setSelectedBooking] = useState(null);

  // Existing state for Add Manual Modal
  const [isManualModalOpen, setIsManualModalOpen] = useState(false);
  const [selectedDateForManual, setSelectedDateForManual] = useState(null); // Separate state

  // State for Day Bookings Modal
  const [isDayModalOpen, setIsDayModalOpen] = useState(false);
  const [selectedDateForDayView, setSelectedDateForDayView] = useState(null);

  // State for Edit Modal
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [selectedJobIdForEdit, setSelectedJobIdForEdit] = useState(null);

  // Fetch bookings and jobs
  const fetchBookings = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [newBookingsResponse, scheduledJobsResponse] = await Promise.all([
        fetch('/api/admin/bookings/new'),
        fetch('/api/admin/jobs/current') // Fetches 'Scheduled' and 'In-Progress' jobs
      ]);

      if (!newBookingsResponse.ok) {
        throw new Error(`Failed fetch new bookings (${newBookingsResponse.status})`);
      }
      const newBookingsData = await newBookingsResponse.json();
      // Map data for the "New Booking Requests" table
      setNewBookings(newBookingsData.map(req => ({
        id: req.id,
        client_name: req.client_name,
        service_name: req.service, // Field name from API response
        requested_date: req.request_date,
        notes: req.address,
        user_id: req.user_id,
        total_price: req.total_price
      })));

      if (!scheduledJobsResponse.ok) {
        throw new Error(`Failed fetch scheduled jobs (${scheduledJobsResponse.status})`);
      }
      const scheduledJobsData = await scheduledJobsResponse.json();
      // Set data for the "Current Scheduled Jobs" table
      setCurrentJobs(scheduledJobsData);

      // Format data for FullCalendar events
      const events = scheduledJobsData.map(job => ({
        id: String(job.id), // Ensure ID is a string
        title: `${job.client_name} - ${job.service || 'Job'}`, // Use service name from job data
        start: `${job.scheduled_date_iso}T${job.start_time || '09:00:00'}`, // API must provide scheduled_date_iso
        borderColor: job.status === 'Completed' ? '#28a745' : '#007bff', // Adjust colors as needed
        backgroundColor: job.status === 'Completed' ? '#28a745' : '#007bff',
      }));
      setCalendarEvents(events);

    } catch (err) {
      console.error("Error fetching bookings:", err);
      setError(err.message);
      setNewBookings([]);
      setCurrentJobs([]);
      setCalendarEvents([]);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchBookings();
  }, [fetchBookings]);

  // --- Modal Handlers ---

  // Schedule Modal
  const handleOpenScheduleModal = (booking) => { setSelectedBooking(booking); setIsScheduleModalOpen(true); };
  const handleCloseScheduleModal = () => { setIsScheduleModalOpen(false); setSelectedBooking(null); };
  const handleJobScheduled = (message) => {
    setFlashMessage({ type: 'success', text: message });
    fetchBookings(); // Refresh all data
    handleCloseScheduleModal(); // Close the modal
    setTimeout(() => setFlashMessage(null), 4000);
  };

  // Add Manual Modal
  const handleOpenManualModal = () => { setSelectedDateForManual(null); setIsManualModalOpen(true); };
  const handleCloseManualModal = () => { setIsManualModalOpen(false); setSelectedDateForManual(null); };
  const handleJobCreated = (message) => { // Called by AddManualBookingModal's onBooked prop
    setFlashMessage({ type: 'success', text: message });
    fetchBookings(); // Refresh all data
    handleCloseManualModal(); // Close the modal
    setTimeout(() => setFlashMessage(null), 4000);
  };

  // Calendar date click
  const handleDateClick = (arg) => {
    // Open the Day View modal
    console.log("Calendar date clicked:", arg.dateStr);
    setSelectedDateForDayView(arg.dateStr); // Use YYYY-MM-DD format
    setIsDayModalOpen(true);
  };

  // Calendar event click
  const handleEventClick = (arg) => {
    const jobId = arg.event.id;
    console.log('Calendar event clicked:', jobId);
    // Directly open Edit Modal
    handleOpenEditModal(jobId);
  };

  // Day Modal handlers
  const handleCloseDayModal = () => {
    setIsDayModalOpen(false);
    setSelectedDateForDayView(null);
  };

  // Called by DayBookingsModal's onBookingDeleted prop
  const handleBookingDeleted = (deletedJobId, date) => {
    console.log(`Booking ${deletedJobId} deleted from Bookings.jsx`);
    setFlashMessage({ type: 'success', text: `Booking #${deletedJobId} deleted.` });
    fetchBookings(); // Refresh calendar and tables
    // Keep Day modal open (as per report note)
  };

  // Edit Modal handlers
  // Called by DayBookingsModal's onEditBooking prop OR handleEventClick
  const handleOpenEditModal = (jobId) => {
    console.log("Opening Edit Modal for Job ID:", jobId);
    if (!jobId) return; // Basic check
    setSelectedJobIdForEdit(String(jobId)); // Ensure it's a string if needed
    
    // Close Day modal if it happens to be open
    if (isDayModalOpen) {
        setIsDayModalOpen(false);
        setSelectedDateForDayView(null);
    }
    setIsEditModalOpen(true); // Open the Edit Modal
  };

  const handleCloseEditModal = () => {
    setIsEditModalOpen(false);
    setSelectedJobIdForEdit(null);
  };

  // Called by the EditBookingModal's onJobUpdated prop
  const handleJobUpdated = (message) => {
    setFlashMessage({ type: 'success', text: message });
    fetchBookings(); // Refresh data
    handleCloseEditModal(); // Close edit modal after update
    setTimeout(() => setFlashMessage(null), 4000);
  };

  // --- 2. ADD HANDLER FOR QUICK STATUS CHANGE ---
  const handleStatusChange = async (jobId, newStatus) => {
    console.log(`Updating Job #${jobId} to status: ${newStatus}`);
    
    try {
      const response = await fetch(`/api/admin/jobs/update_status/${jobId}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ status: newStatus })
      });

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.message || `Failed to update status (Status: ${response.status})`);
      }
      
      const result = await response.json();
      setFlashMessage({ type: 'success', text: result.message });
      // Refresh all data to ensure calendar and tables are in sync
      fetchBookings(); 
      
    } catch (err) {
      console.error("Error updating status:", err);
      setFlashMessage({ type: 'error', text: `Error: ${err.message}` });
      // Re-fetch to revert optimistic UI change (if we were doing one)
      fetchBookings(); 
    } finally {
      setTimeout(() => setFlashMessage(null), 4000);
    }
  };


  // --- Render Functions ---
  const renderLoading = () => (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '20rem' }}>
      <BarLoader color="#4A90E2" width="50%" />
    </div>
  );
  const renderError = () => (
    <div className="flash danger mb-4">Error loading booking data: {error}</div>
  );

  return (
    <div className="container mx-auto p-4 md:p-6">
      {/* Header */}
      <div className="admin-header">
        <h1>Job Bookings & Scheduling</h1>
        <button type="button" className="cta" onClick={handleOpenManualModal}>
          Add Manual Booking
        </button>
      </div>

      {/* Flash Messages */}
      {flashMessage && (
        <div className={`flash ${flashMessage.type} mb-4`}>
          {flashMessage.text}
        </div>
      )}

      {/* Loading/Error State */}
      {error && renderError()}
      {isLoading && renderLoading()}

      {/* Main Content */}
      {!isLoading && !error && (
        <>
          {/* Calendar */}
          <div className="bg-white p-4 shadow rounded-lg mb-6">
            <FullCalendar
              plugins={[dayGridPlugin, timeGridPlugin, interactionPlugin]}
              initialView="dayGridMonth"
              headerToolbar={{
                left: 'prev,next today',
                center: 'title',
                right: 'dayGridMonth,timeGridWeek,timeGridDay'
              }}
              events={calendarEvents}
              dateClick={handleDateClick}    // Opens DayBookingsModal
              eventClick={handleEventClick}   // Opens EditBookingModal
              editable={true}
              droppable={true}
            />
          </div>

          {/* Tables */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* New Booking Requests Table */}
            <div className="bg-white p-4 shadow rounded-lg">
              <h2 className="text-xl font-semibold mb-4">New Booking Requests</h2>
              <div className="overflow-x-auto">
                <table className="data-table min-w-full">
                  <thead><tr><th>Client</th><th>Service</th><th>Requested</th><th>Actions</th></tr></thead>
                  <tbody>
                    {newBookings.length > 0 ? (
                      newBookings.map(booking => (
                        <tr key={booking.id}>
                          <td data-label="Client">{booking.client_name}</td>
                          <td data-label="Service">{booking.service_name}</td>
                          <td data-label="Requested">{booking.requested_date}</td>
                          <td data-label="Actions">
                            <button type="button" className="cta-outline-small" onClick={() => handleOpenScheduleModal(booking)}>
                              View & Schedule
                            </button>
                          </td>
                        </tr>
                      ))
                    ) : (
                      <tr><td colSpan="4" className="text-center py-4 text-gray-500">No new booking requests.</td></tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Current Scheduled Jobs Table */}
            <div className="bg-white p-4 shadow rounded-lg">
              <h2 className="text-xl font-semibold mb-4">Current Scheduled Jobs</h2>
              <div className="overflow-x-auto">
                <table className="data-table min-w-full">
                  <thead><tr><th>Client</th><th>Service</th><th>Scheduled</th><th>Staff</th><th>Status</th><th>Actions</th></tr></thead>
                  <tbody>
                    {currentJobs.length > 0 ? (
                      currentJobs.map(job => (
                        <tr key={job.id}>
                          <td data-label="Client">{job.client_name}</td>
                          <td data-label="Service">{job.service}</td>
                          <td data-label="Scheduled">{job.scheduled_date} {job.start_time}</td>
                          <td data-label="Staff">{job.assigned_staff || 'N/A'}</td>
                          <td data-label="Status">
                            {/* --- 3. CONNECT ONCHANGE HANDLER --- */}
                            <select 
                              className="form-control-small" 
                              value={job.status} // Use value for controlled component
                              onChange={(e) => handleStatusChange(job.id, e.target.value)}
                            >
                              <option value="Scheduled">Scheduled</option>
                              <option value="In Progress">In Progress</option>
                              <option value="Completed">Completed</option>
                              <option value="Cancelled">Cancelled</option>
                            </select>
                          </td>
                          <td data-label="Actions">
                            {/* --- 4. ADD EDIT BUTTON --- */}
                            <button 
                              type="button" 
                              className="cta-outline-small"
                              onClick={() => handleOpenEditModal(job.id)}
                            >
                              Edit
                            </button>
                          </td>
                        </tr>
                      ))
                    ) : (
                      <tr><td colSpan="6" className="text-center py-4 text-gray-500">No jobs scheduled.</td></tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </>
      )}

      {/* --- RENDER ALL MODALS --- */}
      <ScheduleBookingModal
        isOpen={isScheduleModalOpen}
        onClose={handleCloseScheduleModal}
        booking={selectedBooking}
        onScheduled={handleJobScheduled}
      />

      <AddManualBookingModal
        isOpen={isManualModalOpen}
        onClose={handleCloseManualModal}
        onBooked={handleJobCreated}
        preselectedDate={selectedDateForManual}
      />

      <DayBookingsModal
        isOpen={isDayModalOpen}
        onClose={handleCloseDayModal}
        selectedDate={selectedDateForDayView}
        onBookingDeleted={handleBookingDeleted}
        onEditBooking={handleOpenEditModal}
      />

      {/* --- 5. RENDER THE EDIT MODAL --- */}
      <EditBookingModal 
        isOpen={isEditModalOpen}
        onClose={handleCloseEditModal}
        jobId={selectedJobIdForEdit}
        onJobUpdated={handleJobUpdated} 
      /> 
      
    </div>
  );
}

export default Bookings;