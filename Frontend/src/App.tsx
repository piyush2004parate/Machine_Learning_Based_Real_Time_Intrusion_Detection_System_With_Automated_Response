import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ToastProvider } from './hooks/useToast';
import { Sidebar } from './components/Layout/Sidebar';
import { Header } from './components/Layout/Header';
import { Dashboard } from './pages/Dashboard';
import { LiveTraffic } from './pages/LiveTraffic';
import { Incidents } from './pages/Incidents';
import { AutomatedResponse } from './pages/AutomatedResponse';
import { Logs } from './pages/Logs';
import { Settings } from './pages/Settings';

function App() {
  const [darkMode, setDarkMode] = useState(true);

  const toggleDarkMode = () => {
    setDarkMode(!darkMode);
  };

  return (
    <ToastProvider>
      <Router>
        <div className={`${darkMode ? 'dark' : ''} min-h-screen bg-gray-950`}>
          <div className="flex">
            <Sidebar />
            <div className="flex-1">
              <Header darkMode={darkMode} toggleDarkMode={toggleDarkMode} />
              <main className="p-6 bg-gray-900 min-h-screen">
                <Routes>
                  <Route path="/" element={<Dashboard />} />
                  <Route path="/traffic" element={<LiveTraffic />} />
                  <Route path="/incidents" element={<Incidents />} />
                  <Route path="/response" element={<AutomatedResponse />} />
                  <Route path="/logs" element={<Logs />} />
                  <Route path="/settings" element={<Settings />} />
                </Routes>
              </main>
            </div>
          </div>
        </div>
      </Router>
    </ToastProvider>
  );
}

export default App;