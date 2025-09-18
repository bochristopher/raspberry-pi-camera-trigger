import React, { createContext, useContext, useEffect, useState } from 'react'

const WebSocketContext = createContext()

export const useWebSocket = () => {
  const context = useContext(WebSocketContext)
  if (!context) {
    throw new Error('useWebSocket must be used within a WebSocketProvider')
  }
  return context
}

export const WebSocketProvider = ({ children }) => {
  const [socket, setSocket] = useState(null)
  const [connectionStatus, setConnectionStatus] = useState('Connecting')
  const [lastMessage, setLastMessage] = useState(null)

  useEffect(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${window.location.host}/ws`

    const connectWebSocket = () => {
      try {
        const ws = new WebSocket(wsUrl)

        ws.onopen = () => {
          console.log('WebSocket connected')
          setConnectionStatus('Connected')
          setSocket(ws)
        }

        ws.onmessage = (event) => {
          try {
            const message = JSON.parse(event.data)
            setLastMessage(message)
          } catch (error) {
            console.error('Error parsing WebSocket message:', error)
          }
        }

        ws.onclose = () => {
          console.log('WebSocket disconnected')
          setConnectionStatus('Disconnected')
          setSocket(null)

          // Attempt to reconnect after 3 seconds
          setTimeout(connectWebSocket, 3000)
        }

        ws.onerror = (error) => {
          console.error('WebSocket error:', error)
          setConnectionStatus('Error')
        }

        return ws
      } catch (error) {
        console.error('Failed to create WebSocket:', error)
        setConnectionStatus('Error')
        setTimeout(connectWebSocket, 3000)
      }
    }

    const ws = connectWebSocket()

    return () => {
      if (ws) {
        ws.close()
      }
    }
  }, [])

  const value = {
    socket,
    connectionStatus,
    lastMessage,
    isConnected: connectionStatus === 'Connected'
  }

  return (
    <WebSocketContext.Provider value={value}>
      {children}
    </WebSocketContext.Provider>
  )
}