const API_BASE = '/client/api'; 

const getHeaders = () => ({
  'Content-Type': 'application/json',
  'Accept': 'application/json',
});

// 1. Dashboard Stats & Profile (Matches @bp.route('/api/dashboard'))
export const getClientDashboard = async () => {
  try {
    const response = await fetch(`${API_BASE}/dashboard`, {
      method: 'GET',
      headers: getHeaders(),
    });
    if (!response.ok) throw new Error('Failed to fetch dashboard data');
    return await response.json();
  } catch (error) {
    console.error("Client API Error:", error);
    throw error;
  }
};

// 2. My Quotes & Requests (Matches @bp.route('/api/my-quotes'))
export const getMyQuotes = async () => {
  try {
    const response = await fetch(`${API_BASE}/my-quotes`, {
      method: 'GET',
      headers: getHeaders(),
    });
    if (!response.ok) throw new Error('Failed to fetch quotes');
    return await response.json();
  } catch (error) {
    console.error("Client API Error:", error);
    return [];
  }
};

// 3. My Invoices (Matches @bp.route('/api/my-invoices'))
export const getMyInvoices = async () => {
  try {
    const response = await fetch(`${API_BASE}/my-invoices`, {
      method: 'GET',
      headers: getHeaders(),
    });
    if (!response.ok) throw new Error('Failed to fetch invoices');
    return await response.json();
  } catch (error) {
    console.error("Client API Error:", error);
    return [];
  }
};

// 4. My Bookings (Matches @bp.route('/api/my-bookings'))
export const getMyBookings = async () => {
  try {
    const response = await fetch(`${API_BASE}/my-bookings`, {
      method: 'GET',
      headers: getHeaders(),
    });
    if (!response.ok) throw new Error('Failed to fetch bookings');
    return await response.json();
  } catch (error) {
    console.error("Client API Error:", error);
    return [];
  }
};

// 5. Update Profile (Matches @bp.route('/api/profile'))
export const updateClientProfile = async (profileData) => {
  try {
    const response = await fetch(`${API_BASE}/profile`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify(profileData)
    });
    if (!response.ok) throw new Error('Failed to update profile');
    return await response.json();
  } catch (error) {
    console.error("Client API Error:", error);
    throw error;
  }
};