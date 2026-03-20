import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AMIReports } from './pages/AMIReports';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/ami-reports" element={<AMIReports />} />
        <Route path="*" element={
          <div className="flex items-center justify-center min-h-screen bg-gray-100">
            <div className="text-center">
              <h1 className="text-2xl font-bold text-gray-700 mb-4">OMEGA AMI Dashboard</h1>
              <a href="/ami-reports" className="px-6 py-3 bg-blue-600 text-white rounded hover:bg-blue-700">
                → Abrir AMI Reports
              </a>
            </div>
          </div>
        } />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
