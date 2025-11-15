import React, { useState, useEffect } from 'react';
import { BarLoader } from 'react-spinners'; // Or any loader you prefer

function Services() {
  const [servicesData, setServicesData] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
  const fetchServices = async () => {
    setIsLoading(true);
    try {
      // Use fetch directly, just like in your other components
      const response = await fetch('/api/services'); // <-- This is the API endpoint

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setServicesData(data); // Set the data from the response
      setError(null);

    } catch (err) {
      console.error("Error fetching services:", err);
      setError(`Error loading services: ${err.message}`);
      setServicesData([]); // Clear data on error
    } finally {
      setIsLoading(false);
    }
  };

  fetchServices();
}, []); // Empty dependency array means this runs once on mount

  const renderContent = () => {
    if (isLoading) {
      return (
        <div className="flex justify-center items-center h-64">
          <BarLoader color="#4A90E2" />
        </div>
      );
    }

    if (error) {
      return (
        <div className="text-center text-red-500 p-4">
          {error}
        </div>
      );
    }

    if (servicesData.length === 0) {
      return (
        <div className="text-center text-gray-500 p-4">
          No services have been added yet.
        </div>
      );
    }

    // Render the list of service categories and their items
    return (
      <div className="space-y-6">
        {servicesData.map((category) => (
          <div key={category.id} className="bg-white p-4 shadow rounded-lg">
            <h3 className="text-xl font-semibold text-gray-800 mb-3 border-b pb-2">
              {category.name}
              {/* We can add Edit/Delete buttons for the category here later */}
            </h3>
            <ul className="divide-y divide-gray-200">
              {category.services && category.services.length > 0 ? (
                category.services.map((item) => (
                  <li key={item.id} className="py-3 flex justify-between items-center">
                    <div>
                      <p className="font-medium text-gray-700">{item.name}</p>
                      <p className="text-sm text-gray-500">{item.description}</p>
                    </div>
                    <div className="text-right">
                      <p className="font-semibold text-gray-900">R {parseFloat(item.price).toFixed(2)}</p>
                      {/* We can add Edit/Delete buttons for the item here later */}
                    </div>
                  </li>
                ))
              ) : (
                <li className="py-3 text-sm text-gray-400">No items in this category.</li>
              )}
            </ul>
            {/* We can add an "Add New Item" button here later */}
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className="container mx-auto p-4 md:p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Services Management</h1>
        {/* The "Add New Category" button will go here */}
        {/* <button className="btn btn-primary">Add New Category</button> */}
      </div>
      
      {renderContent()}
      
    </div>
  );
}

export default Services;