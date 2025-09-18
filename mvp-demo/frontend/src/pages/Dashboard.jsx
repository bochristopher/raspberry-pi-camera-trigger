import React, { useState, useEffect } from 'react'
import { Camera, Cpu, Shield, Zap, TrendingUp } from 'lucide-react'
import { useWebSocket } from '../hooks/useWebSocket'

const Dashboard = () => {
  const [status, setStatus] = useState(null)
  const [recentCaptures, setRecentCaptures] = useState([])
  const [loading, setLoading] = useState(true)
  const [capturing, setCapturing] = useState(false)
  const [error, setError] = useState(null)
  const { lastMessage, isConnected } = useWebSocket()

  // Fetch system status
  const fetchStatus = async () => {
    try {
      const response = await fetch('/api/status')
      if (!response.ok) throw new Error('Failed to fetch status')
      const data = await response.json()
      setStatus(data)
    } catch (err) {
      setError('Failed to load system status')
      console.error(err)
    }
  }

  // Fetch recent captures
  const fetchRecentCaptures = async () => {
    try {
      const response = await fetch('/api/captures?limit=5')
      if (!response.ok) throw new Error('Failed to fetch captures')
      const data = await response.json()
      setRecentCaptures(data)
      setLoading(false)
    } catch (err) {
      setError('Failed to load recent captures')
      setLoading(false)
      console.error(err)
    }
  }

  // Manual capture
  const handleManualCapture = async () => {
    setCapturing(true)
    setError(null)

    try {
      const response = await fetch('/api/capture/manual', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          duration: 2.0,
          description: 'Manual capture from dashboard'
        })
      })

      if (!response.ok) throw new Error('Failed to capture photo')

      const result = await response.json()
      console.log('Capture successful:', result)

      // Refresh captures and status
      await Promise.all([fetchRecentCaptures(), fetchStatus()])

    } catch (err) {
      setError('Failed to capture photo: ' + err.message)
      console.error(err)
    } finally {
      setCapturing(false)
    }
  }

  // Handle WebSocket messages
  useEffect(() => {
    if (lastMessage) {
      console.log('Received WebSocket message:', lastMessage)

      if (lastMessage.type === 'new_capture') {
        // Refresh captures when new capture is received
        fetchRecentCaptures()
        fetchStatus()
      } else if (lastMessage.type === 'status_update') {
        // Update status from WebSocket
        setStatus(prev => ({ ...prev, ...lastMessage.data }))
      }
    }
  }, [lastMessage])

  // Initial data fetch
  useEffect(() => {
    Promise.all([fetchStatus(), fetchRecentCaptures()])
  }, [])

  if (loading) {
    return (
      <div className="container">
        <div className="loading">
          <div>Loading dashboard...</div>
        </div>
      </div>
    )
  }

  return (
    <div className="container">
      <h1 style={{ marginBottom: '24px', color: '#1e293b' }}>
        ProvenSense Dashboard
      </h1>

      {error && (
        <div className="error">
          {error}
        </div>
      )}

      {/* System Status */}
      <div className="card">
        <h2 style={{ marginBottom: '16px', color: '#374151' }}>System Status</h2>

        <div className="grid grid-3">
          <div className="stat-card">
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '8px' }}>
              <Cpu size={24} color={status?.online ? '#059669' : '#dc2626'} />
            </div>
            <span className="stat-value" style={{ color: status?.online ? '#059669' : '#dc2626' }}>
              {status?.online ? 'Online' : 'Offline'}
            </span>
            <div className="stat-label">System</div>
          </div>

          <div className="stat-card">
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '8px' }}>
              <Camera size={24} color={status?.camera_ready ? '#059669' : '#dc2626'} />
            </div>
            <span className="stat-value" style={{ color: status?.camera_ready ? '#059669' : '#dc2626' }}>
              {status?.camera_ready ? 'Ready' : 'Not Ready'}
            </span>
            <div className="stat-label">Camera</div>
          </div>

          <div className="stat-card">
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '8px' }}>
              <Zap size={24} color={status?.accelerometer_ready ? '#059669' : '#dc2626'} />
            </div>
            <span className="stat-value" style={{ color: status?.accelerometer_ready ? '#059669' : '#dc2626' }}>
              {status?.accelerometer_ready ? 'Ready' : 'Not Ready'}
            </span>
            <div className="stat-label">Accelerometer</div>
          </div>

          <div className="stat-card">
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '8px' }}>
              <Shield size={24} color={status?.secure_element_ready ? '#059669' : '#dc2626'} />
            </div>
            <span className="stat-value" style={{ color: status?.secure_element_ready ? '#059669' : '#dc2626' }}>
              {status?.secure_element_ready ? 'Ready' : 'Not Ready'}
            </span>
            <div className="stat-label">Secure Element</div>
          </div>

          <div className="stat-card">
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '8px' }}>
              <TrendingUp size={24} color="#2563eb" />
            </div>
            <span className="stat-value">{status?.total_captures || 0}</span>
            <div className="stat-label">Total Captures</div>
          </div>

          <div className="stat-card">
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '8px' }}>
              <div style={{
                width: '12px',
                height: '12px',
                borderRadius: '50%',
                backgroundColor: isConnected ? '#059669' : '#dc2626'
              }} />
            </div>
            <span className="stat-value" style={{ color: isConnected ? '#059669' : '#dc2626' }}>
              {isConnected ? 'Connected' : 'Disconnected'}
            </span>
            <div className="stat-label">WebSocket</div>
          </div>
        </div>

        <div style={{ marginTop: '20px', display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
          <button
            className="btn btn-primary"
            onClick={handleManualCapture}
            disabled={capturing || !status?.camera_ready}
          >
            <Camera size={16} />
            {capturing ? 'Capturing...' : 'Manual Capture'}
          </button>

          {status?.last_capture && (
            <div style={{
              padding: '8px 16px',
              backgroundColor: '#f1f5f9',
              borderRadius: '6px',
              fontSize: '14px',
              color: '#475569',
              display: 'flex',
              alignItems: 'center'
            }}>
              Last capture: {new Date(status.last_capture).toLocaleTimeString()}
            </div>
          )}
        </div>
      </div>

      {/* Recent Captures */}
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <h2 style={{ color: '#374151', margin: 0 }}>Recent Captures</h2>
          <a href="/gallery" className="btn btn-secondary">
            View All
          </a>
        </div>

        {recentCaptures.length === 0 ? (
          <div style={{
            textAlign: 'center',
            padding: '40px',
            color: '#64748b',
            backgroundColor: '#f8fafc',
            borderRadius: '6px'
          }}>
            <Camera size={48} style={{ margin: '0 auto 16px', opacity: 0.5 }} />
            <p>No captures yet</p>
            <p style={{ fontSize: '14px' }}>Tap the sensor or use manual capture to get started</p>
          </div>
        ) : (
          <div className="capture-grid">
            {recentCaptures.map((capture) => (
              <div key={capture.id} className="capture-card">
                <img
                  src={capture.photo_url}
                  alt={`Capture ${capture.id}`}
                  className="capture-image"
                  onError={(e) => {
                    e.target.style.display = 'none'
                  }}
                />
                <div className="capture-info">
                  <div className="capture-timestamp">
                    {new Date(capture.timestamp).toLocaleString()}
                  </div>
                  <div className="capture-status">
                    {capture.signature_valid ? (
                      <>
                        <Shield size={16} className="status-verified" />
                        <span className="status-verified">Verified</span>
                      </>
                    ) : (
                      <>
                        <Shield size={16} className="status-unverified" />
                        <span className="status-unverified">Unverified</span>
                      </>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Instructions */}
      <div className="card">
        <h2 style={{ marginBottom: '16px', color: '#374151' }}>How to Use</h2>
        <div style={{ color: '#64748b', lineHeight: '1.6' }}>
          <ol style={{ paddingLeft: '20px' }}>
            <li><strong>Tap the sensor</strong> - Gently tap or move the accelerometer to trigger automatic capture</li>
            <li><strong>Manual capture</strong> - Click the "Manual Capture" button above</li>
            <li><strong>View photos</strong> - Check recent captures here or visit the Gallery page</li>
            <li><strong>Verify signatures</strong> - Use the Verify page to check cryptographic integrity</li>
          </ol>
          <p style={{ marginTop: '16px', fontSize: '14px', color: '#9ca3af' }}>
            All captures are automatically signed with cryptographic signatures for tamper-evident provenance.
          </p>
        </div>
      </div>
    </div>
  )
}

export default Dashboard