import React, { useState, useEffect } from 'react'
import { Shield, CheckCircle, XCircle, AlertTriangle, RefreshCw, Hash, Clock, Download } from 'lucide-react'

const VerificationResult = ({ result, onClose }) => {
  if (!result) return null

  const isValid = result.overall_valid

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3 className="modal-title">Verification Result</h3>
          <button className="close-btn" onClick={onClose}>
            ×
          </button>
        </div>

        <div className={`verification-result ${isValid ? 'verification-valid' : 'verification-invalid'}`}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
            {isValid ? (
              <CheckCircle size={24} />
            ) : (
              <XCircle size={24} />
            )}
            <div>
              <strong>
                {isValid ? 'Verification Successful' : 'Verification Failed'}
              </strong>
              <div style={{ fontSize: '14px', opacity: 0.8 }}>
                Capture #{result.capture_id}
              </div>
            </div>
          </div>

          <div style={{ display: 'grid', gap: '12px', fontSize: '14px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span>Signature Valid:</span>
              <span>{result.signature_valid ? '✓' : '✗'}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span>Timestamp Valid:</span>
              <span>{result.timestamp_valid ? '✓' : '✗'}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span>Data Integrity:</span>
              <span>{result.data_integrity ? '✓' : '✗'}</span>
            </div>
          </div>
        </div>

        <div style={{ marginTop: '20px' }}>
          <h4 style={{ marginBottom: '12px', color: '#374151' }}>Technical Details</h4>

          <div style={{ display: 'grid', gap: '12px', fontSize: '14px', color: '#64748b' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <strong>Verification Time:</strong>
              <span>{new Date(result.verification_timestamp).toLocaleString()}</span>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <strong>File Status:</strong>
              <span style={{ color: result.details?.file_exists ? '#059669' : '#dc2626' }}>
                {result.details?.file_exists ? '✓ File exists' : '✗ File missing'}
              </span>
            </div>

            {result.details?.accelerometer_data && (
              <>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <strong>Sensor Source:</strong>
                  <span style={{
                    color: result.details.accelerometer_data.source === 'real_lis3dh' ? '#059669' : '#f59e0b',
                    fontWeight: '500'
                  }}>
                    {result.details.accelerometer_data.source === 'real_lis3dh' ?
                      '🔧 Real LIS3DH Hardware' : '🖥️ Simulated Sensor'}
                  </span>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <strong>Motion Analysis:</strong>
                  <span>
                    {(() => {
                      const accel = result.details.accelerometer_data
                      const magnitude = Math.sqrt(accel.acceleration_x**2 + accel.acceleration_y**2 + accel.acceleration_z**2)
                      if (magnitude > 12) return '🏃 High motion detected'
                      if (magnitude > 10.5) return '👋 Moderate tap motion'
                      if (magnitude > 9) return '📱 Gentle movement'
                      return '🧘 Stationary'
                    })()}
                  </span>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <strong>G-Force Reading:</strong>
                  <span style={{ fontFamily: 'monospace' }}>
                    {(() => {
                      const accel = result.details.accelerometer_data
                      const magnitude = Math.sqrt(accel.acceleration_x**2 + accel.acceleration_y**2 + accel.acceleration_z**2)
                      return `${magnitude.toFixed(2)}g`
                    })()}
                  </span>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <strong>Sensor Health:</strong>
                  <span style={{
                    color: (() => {
                      const accel = result.details.accelerometer_data
                      const z = Math.abs(accel.acceleration_z)
                      return (z > 8 && z < 12) ? '#059669' : '#f59e0b'
                    })()
                  }}>
                    {(() => {
                      const accel = result.details.accelerometer_data
                      const z = Math.abs(accel.acceleration_z)
                      return (z > 8 && z < 12) ? '✓ Normal gravity reading' : '⚠️ Unusual orientation'
                    })()}
                  </span>
                </div>
              </>
            )}

            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <strong>Capture Method:</strong>
              <span>
                {result.details?.signature?.includes('tap_signature') ? '👆 Tap-triggered' :
                 result.details?.signature?.includes('manual_signature') ? '📱 Manual capture' :
                 '🤖 System capture'}
              </span>
            </div>
          </div>

          <div style={{ fontSize: '14px', color: '#64748b', marginTop: '16px' }}>
            <strong>Signature Preview:</strong>
            <div style={{
              fontFamily: 'monospace',
              backgroundColor: '#f8fafc',
              padding: '8px',
              borderRadius: '4px',
              marginTop: '4px',
              wordBreak: 'break-all',
              fontSize: '12px'
            }}>
              {result.details?.signature}
            </div>
            <div style={{ fontSize: '12px', color: '#9ca3af', marginTop: '4px' }}>
              🔒 Cryptographic proof of authenticity (truncated for security)
            </div>
          </div>

          {result.details?.accelerometer_data && (
            <div style={{ fontSize: '14px', color: '#64748b', marginTop: '16px' }}>
              <strong>Sensor Readings:</strong>
              <div style={{
                backgroundColor: '#f8fafc',
                padding: '12px',
                borderRadius: '4px',
                marginTop: '4px',
                fontFamily: 'monospace',
                fontSize: '12px'
              }}>
                <div>📐 X-axis: {result.details.accelerometer_data.acceleration_x?.toFixed(3)}g</div>
                <div>📐 Y-axis: {result.details.accelerometer_data.acceleration_y?.toFixed(3)}g</div>
                <div>📐 Z-axis: {result.details.accelerometer_data.acceleration_z?.toFixed(3)}g</div>
                <div style={{ marginTop: '8px', color: '#64748b' }}>
                  ⏰ Captured: {new Date(result.details.accelerometer_data.timestamp * 1000).toLocaleString()}
                </div>
              </div>
            </div>
          )}

          <div style={{
            marginTop: '16px',
            padding: '12px',
            backgroundColor: result.overall_valid ? '#dcfce7' : '#fef2f2',
            borderRadius: '6px',
            border: `1px solid ${result.overall_valid ? '#bbf7d0' : '#fecaca'}`
          }}>
            <div style={{
              color: result.overall_valid ? '#166534' : '#dc2626',
              fontWeight: '500',
              marginBottom: '4px'
            }}>
              🛡️ Trust Level: {result.overall_valid ? 'High' : 'Low'}
            </div>
            <div style={{
              fontSize: '12px',
              color: result.overall_valid ? '#166534' : '#dc2626',
              opacity: 0.8
            }}>
              {result.overall_valid ?
                'All verification checks passed. This capture is cryptographically authentic.' :
                'One or more verification checks failed. Data integrity may be compromised.'}
            </div>
          </div>
        </div>

        <div style={{ marginTop: '24px', display: 'flex', gap: '12px' }}>
          <button className="btn btn-secondary" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  )
}

const Verify = () => {
  const [captures, setCaptures] = useState([])
  const [verificationResults, setVerificationResults] = useState({})
  const [loading, setLoading] = useState(true)
  const [verifying, setVerifying] = useState(false)
  const [error, setError] = useState(null)
  const [selectedResult, setSelectedResult] = useState(null)
  const [bulkResult, setBulkResult] = useState(null)

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

  const verifyCapture = async (captureId) => {
    try {
      setVerifying(true)
      const response = await fetch(`/api/verify/${captureId}`)
      if (!response.ok) throw new Error('Failed to verify capture')
      const result = await response.json()

      setVerificationResults(prev => ({
        ...prev,
        [captureId]: result
      }))

      return result
    } catch (err) {
      setError(`Failed to verify capture ${captureId}`)
      console.error(err)
      return null
    } finally {
      setVerifying(false)
    }
  }

  const verifyAllCaptures = async () => {
    try {
      setVerifying(true)
      const response = await fetch('/api/verify/all')
      if (!response.ok) throw new Error('Failed to verify all captures')
      const result = await response.json()
      setBulkResult(result)

      // Also update individual results
      const newResults = {}
      result.results.forEach(r => {
        newResults[r.id] = {
          capture_id: r.id,
          overall_valid: r.valid,
          signature_valid: r.valid,
          timestamp_valid: true,
          data_integrity: true
        }
      })
      setVerificationResults(newResults)

    } catch (err) {
      setError('Failed to verify all captures')
      console.error(err)
    } finally {
      setVerifying(false)
    }
  }

  const handleVerifyClick = async (captureId) => {
    const result = await verifyCapture(captureId)
    if (result) {
      setSelectedResult(result)
    }
  }

  useEffect(() => {
    fetchCaptures()
  }, [])

  if (loading) {
    return (
      <div className="container">
        <div className="loading">
          <div>Loading verification data...</div>
        </div>
      </div>
    )
  }

  return (
    <div className="container">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <h1 style={{ color: '#1e293b', margin: 0 }}>
          Signature Verification
        </h1>
        <div style={{ display: 'flex', gap: '12px' }}>
          <button
            className="btn btn-primary"
            onClick={verifyAllCaptures}
            disabled={verifying}
          >
            {verifying ? (
              <>
                <RefreshCw size={16} style={{ animation: 'spin 1s linear infinite' }} />
                Verifying...
              </>
            ) : (
              <>
                <Shield size={16} />
                Verify All
              </>
            )}
          </button>
        </div>
      </div>

      {error && (
        <div className="error">
          {error}
        </div>
      )}

      {/* Bulk Verification Results */}
      {bulkResult && (
        <div className="card">
          <h2 style={{ marginBottom: '16px', color: '#374151' }}>Verification Summary</h2>

          <div className="stats-grid">
            <div className="stat-card">
              <span className="stat-value">{bulkResult.total_captures}</span>
              <div className="stat-label">Total Captures</div>
            </div>

            <div className="stat-card">
              <span className="stat-value" style={{ color: '#059669' }}>
                {bulkResult.valid_captures}
              </span>
              <div className="stat-label">Valid</div>
            </div>

            <div className="stat-card">
              <span className="stat-value" style={{ color: '#dc2626' }}>
                {bulkResult.invalid_captures}
              </span>
              <div className="stat-label">Invalid</div>
            </div>

            <div className="stat-card">
              <span className="stat-value" style={{
                color: bulkResult.verification_rate === 100 ? '#059669' :
                       bulkResult.verification_rate > 80 ? '#f59e0b' : '#dc2626'
              }}>
                {bulkResult.verification_rate.toFixed(1)}%
              </span>
              <div className="stat-label">Success Rate</div>
            </div>
          </div>

          {bulkResult.verification_rate === 100 ? (
            <div style={{
              marginTop: '16px',
              padding: '16px',
              backgroundColor: '#dcfce7',
              color: '#166534',
              borderRadius: '6px',
              display: 'flex',
              alignItems: 'center',
              gap: '12px'
            }}>
              <CheckCircle size={20} />
              <div>
                <strong>All signatures verified successfully!</strong>
                <div style={{ fontSize: '14px', opacity: 0.8 }}>
                  Complete cryptographic integrity confirmed across all captures.
                </div>
              </div>
            </div>
          ) : (
            <div style={{
              marginTop: '16px',
              padding: '16px',
              backgroundColor: '#fef3c7',
              color: '#92400e',
              borderRadius: '6px',
              display: 'flex',
              alignItems: 'center',
              gap: '12px'
            }}>
              <AlertTriangle size={20} />
              <div>
                <strong>Some signatures failed verification</strong>
                <div style={{ fontSize: '14px', opacity: 0.8 }}>
                  Review individual captures below for details.
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Individual Captures */}
      <div className="card">
        <h2 style={{ marginBottom: '16px', color: '#374151' }}>Individual Verification</h2>

        {captures.length === 0 ? (
          <div style={{
            textAlign: 'center',
            padding: '40px',
            color: '#64748b',
            backgroundColor: '#f8fafc',
            borderRadius: '6px'
          }}>
            <Shield size={48} style={{ margin: '0 auto 16px', opacity: 0.5 }} />
            <p>No captures to verify</p>
            <p style={{ fontSize: '14px' }}>Create some captures first to test verification</p>
          </div>
        ) : (
          <div style={{ display: 'grid', gap: '12px' }}>
            {captures.map((capture) => {
              const result = verificationResults[capture.id]
              const isVerified = result?.overall_valid

              return (
                <div
                  key={capture.id}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '16px',
                    backgroundColor: '#f8fafc',
                    borderRadius: '6px',
                    border: result ? (isVerified ? '1px solid #bbf7d0' : '1px solid #fecaca') : '1px solid #e2e8f0'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <Hash size={16} style={{ color: '#64748b' }} />
                      <span style={{ fontWeight: '500' }}>#{capture.id}</span>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <Clock size={16} style={{ color: '#64748b' }} />
                      <span style={{ fontSize: '14px', color: '#64748b' }}>
                        {new Date(capture.timestamp).toLocaleString()}
                      </span>
                    </div>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    {result && (
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        {isVerified ? (
                          <>
                            <CheckCircle size={20} style={{ color: '#059669' }} />
                            <span style={{ color: '#059669', fontSize: '14px', fontWeight: '500' }}>
                              Verified
                            </span>
                          </>
                        ) : (
                          <>
                            <XCircle size={20} style={{ color: '#dc2626' }} />
                            <span style={{ color: '#dc2626', fontSize: '14px', fontWeight: '500' }}>
                              Failed
                            </span>
                          </>
                        )}
                      </div>
                    )}

                    <button
                      className="btn btn-secondary"
                      onClick={() => handleVerifyClick(capture.id)}
                      disabled={verifying}
                      style={{ fontSize: '14px', padding: '8px 16px' }}
                    >
                      <Shield size={14} />
                      {result ? 'View Details' : 'Verify'}
                    </button>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>

      {/* How It Works */}
      <div className="card">
        <h2 style={{ marginBottom: '16px', color: '#374151' }}>How Verification Works</h2>
        <div style={{ color: '#64748b', lineHeight: '1.6' }}>
          <ol style={{ paddingLeft: '20px' }}>
            <li><strong>Cryptographic Signatures</strong> - Each capture is signed with ECDSA using a secure element</li>
            <li><strong>Data Integrity</strong> - Verifies that photo files haven't been modified or corrupted</li>
            <li><strong>Timestamp Validation</strong> - Ensures timestamps are accurate and haven't been tampered with</li>
            <li><strong>Chain of Custody</strong> - Provides tamper-evident proof of data authenticity</li>
          </ol>
          <p style={{ marginTop: '16px', fontSize: '14px', color: '#9ca3af' }}>
            This cryptographic verification provides legal-grade evidence that your sensor data is authentic and unmodified.
          </p>
        </div>
      </div>

      {selectedResult && (
        <VerificationResult
          result={selectedResult}
          onClose={() => setSelectedResult(null)}
        />
      )}
    </div>
  )
}

export default Verify