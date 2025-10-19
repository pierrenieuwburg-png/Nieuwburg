import React, { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import FullCalendar from '@fullcalendar/react';
import dayGridPlugin from '@fullcalendar/daygrid';
import timeGridPlugin from '@fullcalendar/timegrid';
import listPlugin from '@fullcalendar/list';
import interactionPlugin from '@fullcalendar/interaction'; // For dateClick/eventClick

function Bookings() {
  const [currentJobs, setCurrentJobs] = useState([]);
  const [newBookings, setNewBookings] = useState([]);
  const [isLoadingJobs, setIsLoadingJobs] = useState(true);
  const [isLoadingBookings, setIsLoadingBookings] = useState(true);
  const [error, setError] = useState(null);
  const [calendarEvents, setCalendarEvents] = useState([]); // State for calendar events

  // Fetch Current Jobs (Scheduled/In-Progress)
  useEffect(() => {
    const fetchCurrentJobs = async () => {
      setIsLoadingJobs(true);
      setError(null); // Clear previous errors
      try {
        const response = await fetch('/api/admin/jobs/current');
        if (!response.ok) {
          if (response.status === 403) throw new Error('Permission denied fetching current jobs.');
          throw new Error(`HTTP error fetching jobs! status: ${response.status}`);
        }
        const data = await response.json();
        setCurrentJobs(data);

        // --- Transform job data for FullCalendar ---
        const events = data.map(job => ({
          id: job.id.toString(), // FullCalendar needs string IDs
          title: `${job.client_name} - ${job.service}`,
          start: `${job.scheduled_date_iso}T${job.start_time || '09:00:00'}`, // Combine date and time, default if no time
          // Optionally add end time if available and needed for timeGrid view
          // end: `${job.scheduled_date_iso}T${job.end_time || '17:00:00'}`,
          extendedProps: { // Store original job data if needed for clicks
            client_name: job.client_name,
            service: job.service,
            status: job.status,
            assigned_staff: job.assigned_staff,
          },
          // Add color based on status if desired (using colors from style.css)
           backgroundColor: getStatusColor(job.status),
           borderColor: getStatusColor(job.status),
        }));
        setCalendarEvents(events);
        // --- End Transformation ---

      } catch (err) {
        console.error('Error fetching current jobs:', err);
        setError(prev => prev ? `${prev}\n${err.message}` : err.message);
        setCalendarEvents([]); // Clear events on error
      } finally {
        setIsLoadingJobs(false);
      }
    };
    fetchCurrentJobs();
  }, []); // Run once on mount

  // Fetch New Confirmed Bookings (Quote Requests) - Keep as is
  useEffect(() => {
    const fetchNewBookings = async () => {
      setIsLoadingBookings(true);
      try {
        const response = await fetch('/api/admin/bookings/new');
        if (!response.ok) {
           if (response.status === 403) throw new Error('Permission denied fetching new bookings.');
           throw new Error(`HTTP error fetching new bookings! status: ${response.status}`);
        }
        const data = await response.json();
        setNewBookings(data);
      } catch (err) {
        console.error('Error fetching new bookings:', err);
        setError(prev => prev ? `${prev}\n${err.message}` : err.message);
      } finally {
        setIsLoadingBookings(false);
      }
    };
    fetchNewBookings();
  }, []); // Run once on mount

  // Helper function to get status colors (similar to admin_bookings.html logic)
  const getStatusColor = (status) => {
    switch (status?.toLowerCase()) {
      case 'scheduled': return '#007bff';
      case 'in-progress': return '#ffc107';
      case 'completed': return '#28a745';
      case 'cancelled': return '#6c757d';
      default: return '#6c757d'; // Default grey
    }
  };

  // Helper function to format price (keep as is)
  const formatPrice = (price) => {
      if (price === 'N/A' || price === null || price === undefined) return 'N/A';
      const num = parseFloat(price);
      return isNaN(num) ? 'N/A' : `R${num.toFixed(2)}`;
  };

  // --- Calendar Event Handlers (Placeholders) ---
  const handleDateClick = (arg) => {
    // Placeholder: Could open a modal to add a job for 'arg.dateStr'
    alert('Clicked on date: ' + arg.dateStr);
  };

  const handleEventClick = (arg) => {
    // Placeholder: Could open a modal showing job details using 'arg.event.id'
    // or navigate to the job edit page
    alert('Clicked on event: ' + arg.event.title + '\nJob ID: ' + arg.event.id);
    // Example navigation (if you set up the route):
    // navigate(`/job/edit/${arg.event.id}`);
  };
  // --- End Calendar Event Handlers ---

  return (
    <div>
      <div className="admin-header">
        <h1>Bookings & Scheduling</h1>
        <p>Manage incoming requests and schedule new jobs.</p>
      </div>

      {/* Display general error messages */}
      {error && (
        <div className="flash error" style={{ marginBottom: '20px' }}>
           {error.split('\n').map((line, i) => <p key={i} style={{margin:0}}>{line}</p>)}
        </div>
      )}

      {/* --- FullCalendar Implementation --- */}
      <div className="admin-section">
        <h2>Schedule Overview</h2>
        {isLoadingJobs ? (
            <p>Loading schedule...</p>
        ) : (
            <FullCalendar
                plugins={[dayGridPlugin, timeGridPlugin, listPlugin, interactionPlugin]}
                initialView="dayGridMonth"
                headerToolbar={{
                    left: 'prev,next today',
                    center: 'title',
                    right: 'dayGridMonth,timeGridWeek,listWeek'
                }}
                events={calendarEvents}
                height="auto" // Adjust height automatically
                dayMaxEvents={true} // Allow "more" link if too many events
                dateClick={handleDateClick} // Handle clicking on a date
                eventClick={handleEventClick} // Handle clicking on an event
            />
        )}
      </div>
      {/* --- End FullCalendar Implementation --- */}


      <div className="admin-section">
        <h2>Scheduled & In-Progress Jobs</h2>
        {/* Keep the table for now, maybe hide/remove later if calendar is sufficient */}
        <table className="data-table" id="jobs-table">
          {/* ... table structure remains the same ... */}
           <thead>
            <tr>
              <th>Date</th>
              <th>Client</th>
              <th>Service</th>
              <th>Status</th>
              <th>Assigned Staff</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {isLoadingJobs ? (
              <tr><td colSpan="6" style={{ textAlign: 'center', padding: '20px' }}>Loading current jobs...</td></tr>
            ) : currentJobs.length > 0 ? (
              currentJobs.map(job => (
                <tr key={job.id} id={`job-row-${job.id}`}>
                  <td>{job.scheduled_date} {job.start_time}</td>
                  <td>{job.client_name}</td>
                  <td>{job.service}</td>
                  <td>
                    <span id={`status-badge-${job.id}`} className={`booking-status status-${job.status.toLowerCase()}`}>
                      {job.status}
                    </span>
                  </td>
                  <td>{job.assigned_staff}</td>
                  <td className="action-buttons">
                    <Link to={`/job/edit/${job.id}`} className="cta-outline-small">Edit</Link>
                     <select className="status-update-dropdown" data-job-id={job.id} defaultValue={job.status}>
                        <option value="Scheduled">Scheduled</option>
                        <option value="In-Progress">In-Progress</option>
                        <option value="Completed">Completed</option>
                        <option value="Cancelled">Cancelled</option>
                    </select>
                  </td>
                </tr>
              ))
            ) : (
              <tr><td colSpan="6" style={{ textAlign: 'center', padding: '20px' }}>There are no currently scheduled jobs.</td></tr>
            )}
          </tbody>
        </table>
      </div>

      <div className="admin-section">
        <h2>New Confirmed Bookings</h2>
         {/* Keep the new bookings table as is */}
        <table className="data-table">
           {/* ... table structure remains the same ... */}
            <thead>
            <tr>
              <th>Confirmed On</th>
              <th>Client</th>
              <th>Service Details</th>
              <th>Address</th>
              <th>Final Price</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {isLoadingBookings ? (
              <tr><td colSpan="6" style={{ textAlign: 'center', padding: '20px' }}>Loading new bookings...</td></tr>
            ) : newBookings.length > 0 ? (
              newBookings.map(req => (
                <tr key={req.id}>
                  <td>{req.request_date}</td>
                  <td>
                    <strong>{req.client_name}</strong><br />
                    <small>{req.client_phone}</small>
                  </td>
                  <td>
                    <strong>{req.service}</strong> ({req.property_type})
                  </td>
                  <td>{req.address}</td>
                  <td><strong>{formatPrice(req.total_price)}</strong></td>
                  <td>
                    <Link to={`/schedule_job/${req.id}`} className="cta-outline-small">View & Schedule</Link>
                  </td>
                </tr>
              ))
            ) : (
              <tr><td colSpan="6" style={{ textAlign: 'center', padding: '20px' }}>There are no new confirmed bookings.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default Bookings;

export default Bookings;