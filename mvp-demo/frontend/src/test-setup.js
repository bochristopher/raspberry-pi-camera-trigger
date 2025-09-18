import '@testing-library/jest-dom'
import { vi } from 'vitest'

// Mock WebSocket globally
global.WebSocket = vi.fn(() => ({
  close: vi.fn(),
  send: vi.fn(),
  readyState: 1,
  onopen: null,
  onmessage: null,
  onclose: null,
  onerror: null
}))

// Mock fetch globally
global.fetch = vi.fn()

// Mock window.location
Object.defineProperty(window, 'location', {
  value: {
    host: 'localhost:3000',
    protocol: 'http:'
  },
  writable: true
})