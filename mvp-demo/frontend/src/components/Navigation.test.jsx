import React from 'react'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, it, expect } from 'vitest'
import Navigation from './Navigation'

// Helper to render component with router
const renderWithRouter = (component, { route = '/' } = {}) => {
  return render(
    <MemoryRouter initialEntries={[route]}>
      {component}
    </MemoryRouter>
  )
}

describe('Navigation', () => {
  it('renders the brand name', () => {
    renderWithRouter(<Navigation />)
    expect(screen.getByText('ProvenSense MVP')).toBeTruthy()
  })

  it('renders all navigation links', () => {
    renderWithRouter(<Navigation />)

    expect(screen.getByText('Dashboard')).toBeTruthy()
    expect(screen.getByText('Gallery')).toBeTruthy()
    expect(screen.getByText('Verify')).toBeTruthy()
  })

  it('highlights active link', () => {
    renderWithRouter(<Navigation />, { route: '/gallery' })

    const galleryLink = screen.getByText('Gallery').closest('a')
    expect(galleryLink).toHaveClass('active')
  })

  it('has correct link hrefs', () => {
    renderWithRouter(<Navigation />)

    const dashboardLink = screen.getByText('Dashboard').closest('a')
    const galleryLink = screen.getByText('Gallery').closest('a')
    const verifyLink = screen.getByText('Verify').closest('a')

    expect(dashboardLink).toHaveAttribute('href', '/')
    expect(galleryLink).toHaveAttribute('href', '/gallery')
    expect(verifyLink).toHaveAttribute('href', '/verify')
  })
})