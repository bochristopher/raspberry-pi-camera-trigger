import React, { useState, useEffect } from 'react'
import { Camera, Shield, Download, Eye, Clock, Hash } from 'lucide-react'
import { useWebSocket } from '../hooks/useWebSocket'

const CaptureModal = ({ capture, onClose }) => {
  if (!capture) return null

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleString()
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3 className="modal-title">Capture Details</h3>
          <button className="close-btn" onClick={onClose}>
            ×
          </button>
        </div>

        <div style={{ marginBottom: '20px' }}>
          <img
            src={capture.photo_url}
            alt={`Capture ${capture.id}`}
            style={{
              width: '100%',
              maxHeight: '300px',
              objectFit: 'contain',
              borderRadius: '6px',
              backgroundColor: '#f8fafc'
            }}
          />
        </div>

        <div style={{ display: 'grid', gap: '16px' }}>
          <div>
            <strong>Timestamp:</strong>
            <div style={{ color: '#64748b', fontSize: '14px' }}>
              {formatTimestamp(capture.timestamp)}
            </div>
          </div>

          <div>
            <strong>Signature Status:</strong>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '4px' }}>
              {capture.signature_valid ? (
                <>
                  <Shield size={16} style={{ color: '#059669' }} />
                  <span style={{ color: '#059669' }}>Verified</span>
                </>
              ) : (
                <>
                  <Shield size={16} style={{ color: '#dc2626' }} />
                  <span style={{ color: '#dc2626' }}>Unverified</span>
                </>
              )}
            </div>
          </div>

          <div>
            <strong>Accelerometer Data:</strong>
            <div style={{
              backgroundColor: '#f8fafc',
              padding: '12px',
              borderRadius: '6px',
              marginTop: '4px',
              fontSize: '14px',
              fontFamily: 'monospace'
            }}>
              X: {capture.accelerometer_data.acceleration_x?.toFixed(3)} m/s²<br />
              Y: {capture.accelerometer_data.acceleration_y?.toFixed(3)} m/s²<br />
              Z: {capture.accelerometer_data.acceleration_z?.toFixed(3)} m/s²
            </div>
          </div>

          <div>
            <strong>Signature:</strong>
            <div style={{
              backgroundColor: '#f8fafc',
              padding: '12px',
              borderRadius: '6px',
              marginTop: '4px',
              fontSize: '12px',
              fontFamily: 'monospace',
              wordBreak: 'break-all',
              color: '#64748b'
            }}>
              {capture.signature}
            </div>
          </div>

          <div>
            <strong>File Size:</strong>
            <div style={{ color: '#64748b', fontSize: '14px' }}>
              {(capture.size_bytes / 1024).toFixed(1)} KB
            </div>
          </div>
        </div>

        <div style={{ marginTop: '24px', display: 'flex', gap: '12px' }}>
          <a
            href={capture.photo_url}
            download={`capture_${capture.id}.jpg`}
            className="btn btn-primary"
          >
            <Download size={16} />
            Download Photo
          </a>
          <button className="btn btn-secondary" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  )
}

const Gallery = () => {
  const [captures, setCaptures] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [selectedCapture, setSelectedCapture] = useState(null)
  const { lastMessage } = useWebSocket()

  const fetchCaptures = async () => {
    try {
      const response = await fetch('/api/captures?limit=100')
      if (!response.ok) throw new Error('Failed to fetch captures')
      const data = await response.json()
      setCaptures(data)
      setLoading(false)
    } catch (err) {
      setError('Failed to load captures')
      setLoading(false)
      console.error(err)
    }
  }

  // Handle WebSocket messages for new captures
  useEffect(() => {
    if (lastMessage && lastMessage.type === 'new_capture') {
      fetchCaptures()
    }
  }, [lastMessage])

  useEffect(() => {
    fetchCaptures()
  }, [])

  const handleCaptureClick = async (capture) => {
    try {
      // Fetch full capture details
      const response = await fetch(`/api/capture/${capture.id}`)
      if (!response.ok) throw new Error('Failed to fetch capture details')
      const fullCapture = await response.json()
      setSelectedCapture(fullCapture)
    } catch (err) {
      setError('Failed to load capture details')
      console.error(err)
    }
  }

  if (loading) {
    return (
      <div className="container">
        <div className="loading">
          <div>Loading gallery...</div>
        </div>
      </div>
    )
  }

  return (
    <div className="container">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <h1 style={{ color: '#1e293b', margin: 0 }}>
          Photo Gallery
        </h1>
        <div style={{ color: '#64748b', fontSize: '14px' }}>
          {captures.length} total captures
        </div>
      </div>

      {error && (
        <div className="error">
          {error}
        </div>
      )}

      {captures.length === 0 ? (
        <div className="card">
          <div style={{
            textAlign: 'center',
            padding: '60px 20px',
            color: '#64748b'
          }}>
            <Camera size={64} style={{ margin: '0 auto 24px', opacity: 0.3 }} />
            <h3 style={{ marginBottom: '8px', color: '#374151' }}>No captures yet</h3>
            <p style={{ marginBottom: '24px' }}>Start capturing by tapping the sensor or using manual capture</p>
            <a href="/" className="btn btn-primary">
              Go to Dashboard
            </a>
          </div>
        </div>
      ) : (
        <div className="capture-grid">
          {captures.map((capture) => (
            <div
              key={capture.id}
              className="capture-card"
              onClick={() => handleCaptureClick(capture)}
              style={{ cursor: 'pointer' }}
            >
              <div style={{ position: 'relative' }}>
                <img
                  src={capture.photo_url}
                  alt={`Capture ${capture.id}`}
                  className="capture-image"
                  onError={(e) => {
                    e.target.style.backgroundColor = '#f1f5f9'
                    e.target.style.display = 'flex'
                    e.target.style.alignItems = 'center'
                    e.target.style.justifyContent = 'center'
                    e.target.innerHTML = 'Photo'
                  }}
                />
                <div style={{
                  position: 'absolute',
                  top: '8px',
                  right: '8px',
                  background: 'rgba(0, 0, 0, 0.7)',
                  color: 'white',
                  padding: '4px 8px',
                  borderRadius: '4px',
                  fontSize: '12px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px'
                }}>
                  <Eye size={12} />
                  View
                </div>
              </div>

              <div className="capture-info">
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                  <Clock size={14} style={{ color: '#64748b' }} />
                  <span className="capture-timestamp">
                    {new Date(capture.timestamp).toLocaleString()}
                  </span>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
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

                  <div style={{
                    fontSize: '12px',
                    color: '#9ca3af',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px'
                  }}>
                    <Hash size={12} />
                    #{capture.id}
                  </div>
                </div>

                <div style={{
                  marginTop: '8px',
                  fontSize: '12px',
                  color: '#64748b',
                  backgroundColor: '#f8fafc',
                  padding: '6px',
                  borderRadius: '4px'
                }}>
                  Motion: {Math.sqrt(
                    Math.pow(capture.accelerometer_data.acceleration_x || 0, 2) +
                    Math.pow(capture.accelerometer_data.acceleration_y || 0, 2) +
                    Math.pow(capture.accelerometer_data.acceleration_z || 0, 2)
                  ).toFixed(2)} m/s²
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {selectedCapture && (
        <CaptureModal
          capture={selectedCapture}
          onClose={() => setSelectedCapture(null)}
        />
      )}
    </div>
  )
}

export default Gallery