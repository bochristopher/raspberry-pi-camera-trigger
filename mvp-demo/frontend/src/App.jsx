import React from 'react'
import { Routes, Route } from 'react-router-dom'
import Navigation from './components/Navigation'
import Dashboard from './pages/Dashboard'
import Gallery from './pages/Gallery'
import Verify from './pages/Verify'
import { WebSocketProvider } from './hooks/useWebSocket'

function App() {
  return (
    <WebSocketProvider>
      <div className="min-h-screen bg-gray-50">
        <Navigation />
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/gallery" element={<Gallery />} />
          <Route path="/verify" element={<Verify />} />
        </Routes>
      </div>
    </WebSocketProvider>
  )
}

export default App