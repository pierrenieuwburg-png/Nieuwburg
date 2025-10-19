import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom'; // Import BrowserRouter
import App from './App.jsx';
import './index.css'; // Keep default styling for now

// The root element ID must match the one in admin_base.html
const rootElement = document.getElementById('admin-app-root');

if (rootElement) {
  ReactDOM.createRoot(rootElement).render(
    <React.StrictMode>
      {/* Wrap the App component with BrowserRouter */}
      {/* Set the basename to '/admin' to match Flask's blueprint prefix */}
      <BrowserRouter basename="/admin">
        <App />
      </BrowserRouter>
    </React.StrictMode>,
  );
} else {
  console.error("Failed to find the root element '#admin-app-root'. Make sure it exists in your HTML.");
}