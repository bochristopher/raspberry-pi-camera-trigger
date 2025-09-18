import React from 'react'
import { Link, useLocation } from 'react-router-dom'
import { Camera, BarChart3, Shield } from 'lucide-react'

const Navigation = () => {
  const location = useLocation()

  const navItems = [
    { path: '/', label: 'Dashboard', icon: BarChart3 },
    { path: '/gallery', label: 'Gallery', icon: Camera },
    { path: '/verify', label: 'Verify', icon: Shield }
  ]

  return (
    <nav className="navigation">
      <div className="nav-container">
        <Link to="/" className="nav-brand">
          ProvenSense MVP
        </Link>

        <ul className="nav-links">
          {navItems.map(({ path, label, icon: Icon }) => (
            <li key={path}>
              <Link
                to={path}
                className={`nav-link ${location.pathname === path ? 'active' : ''}`}
              >
                <Icon size={16} />
                {label}
              </Link>
            </li>
          ))}
        </ul>
      </div>
    </nav>
  )
}

export default Navigation