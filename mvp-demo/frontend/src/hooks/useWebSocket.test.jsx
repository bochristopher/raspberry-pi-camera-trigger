import React from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { WebSocketProvider, useWebSocket } from './useWebSocket'

// Mock WebSocket
global.WebSocket = vi.fn(() => ({
  close: vi.fn(),
  send: vi.fn(),
  readyState: 1
}))

// Test component that uses the hook
const TestComponent = () => {
  const { connectionStatus, isConnected, lastMessage } = useWebSocket()

  return (
    <div>
      <div data-testid="status">{connectionStatus}</div>
      <div data-testid="connected">{isConnected ? 'true' : 'false'}</div>
      <div data-testid="message">{lastMessage ? JSON.stringify(lastMessage) : 'none'}</div>
    </div>
  )
}

describe('useWebSocket', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('provides initial state', () => {
    render(
      <WebSocketProvider>
        <TestComponent />
      </WebSocketProvider>
    )

    expect(screen.getByTestId('status')).toHaveTextContent('Connecting')
    expect(screen.getByTestId('connected')).toHaveTextContent('false')
    expect(screen.getByTestId('message')).toHaveTextContent('none')
  })

  it('throws error when used outside provider', () => {
    // Suppress console.error for this test
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

    expect(() => {
      render(<TestComponent />)
    }).toThrow('useWebSocket must be used within a WebSocketProvider')

    consoleSpy.mockRestore()
  })

  it('connects to WebSocket on mount', async () => {
    const mockWebSocket = {
      close: vi.fn(),
      send: vi.fn(),
      readyState: 1,
      onopen: null,
      onmessage: null,
      onclose: null,
      onerror: null
    }

    global.WebSocket = vi.fn(() => mockWebSocket)

    render(
      <WebSocketProvider>
        <TestComponent />
      </WebSocketProvider>
    )

    expect(global.WebSocket).toHaveBeenCalledWith('ws://localhost:3000/ws')
  })

  it('handles connection state changes', async () => {
    const mockWebSocket = {
      close: vi.fn(),
      send: vi.fn(),
      readyState: 1,
      onopen: null,
      onmessage: null,
      onclose: null,
      onerror: null
    }

    global.WebSocket = vi.fn(() => mockWebSocket)

    render(
      <WebSocketProvider>
        <TestComponent />
      </WebSocketProvider>
    )

    // Simulate connection opened
    mockWebSocket.onopen()

    await waitFor(() => {
      expect(screen.getByTestId('status')).toHaveTextContent('Connected')
      expect(screen.getByTestId('connected')).toHaveTextContent('true')
    })
  })

  it('handles incoming messages', async () => {
    const mockWebSocket = {
      close: vi.fn(),
      send: vi.fn(),
      readyState: 1,
      onopen: null,
      onmessage: null,
      onclose: null,
      onerror: null
    }

    global.WebSocket = vi.fn(() => mockWebSocket)

    render(
      <WebSocketProvider>
        <TestComponent />
      </WebSocketProvider>
    )

    // Simulate connection opened
    mockWebSocket.onopen()

    // Simulate message received
    const testMessage = { type: 'test', data: 'hello' }
    mockWebSocket.onmessage({ data: JSON.stringify(testMessage) })

    await waitFor(() => {
      expect(screen.getByTestId('message')).toHaveTextContent(JSON.stringify(testMessage))
    })
  })

  it('handles connection errors', async () => {
    const mockWebSocket = {
      close: vi.fn(),
      send: vi.fn(),
      readyState: 1,
      onopen: null,
      onmessage: null,
      onclose: null,
      onerror: null
    }

    global.WebSocket = vi.fn(() => mockWebSocket)

    render(
      <WebSocketProvider>
        <TestComponent />
      </WebSocketProvider>
    )

    // Simulate connection error
    mockWebSocket.onerror(new Error('Connection failed'))

    await waitFor(() => {
      expect(screen.getByTestId('status')).toHaveTextContent('Error')
    })
  })
})