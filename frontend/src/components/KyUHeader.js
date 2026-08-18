import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import './KyUHeader.css';

export default function KyUHeader() {
  const { user } = useAuth();
  const navigate = useNavigate();

  return (
    <header className="kyu-top-header">
      <div className="kyu-header-left">
        <Link to="/dashboard" className="kyu-header-logo">
          <img src="/images/kyu-logo.png" alt="KyU" className="kyu-header-logo-img" onError={(e) => { e.target.style.display = 'none'; }} />
          <div className="kyu-header-logo-text">
            <span className="kyu-header-university">Kirinyaga University</span>
            <span className="kyu-header-motto">Innovative Technology for a Dynamic World</span>
          </div>
        </Link>
      </div>
      <div className="kyu-header-center">
        <nav className="kyu-header-nav">
          <Link to="/dashboard" className="kyu-header-link">Home</Link>
          <Link to="/events" className="kyu-header-link">Events</Link>
          <Link to="/bulletin" className="kyu-header-link">News</Link>
          <Link to="/groups" className="kyu-header-link">Academics</Link>
          <a href="https://library.kyu.ac.ke" target="_blank" rel="noopener noreferrer" className="kyu-header-link">Library</a>
          <a href="https://students.kyu.ac.ke" target="_blank" rel="noopener noreferrer" className="kyu-header-link">Students</a>
        </nav>
      </div>
      <div className="kyu-header-right">
        <div className="kyu-header-contact">
          <span className="kyu-header-phone">+254 709 742000</span>
          <span className="kyu-header-email">info@kyu.ac.ke</span>
        </div>
        <div className="kyu-header-social">
          <a href="https://www.facebook.com/kirinyagauniversity" target="_blank" rel="noopener noreferrer" title="Facebook">FB</a>
          <a href="https://x.com/KyUniversity" target="_blank" rel="noopener noreferrer" title="Twitter">X</a>
          <a href="https://www.youtube.com/channel/UCJOUsBeWOeD8DpYcwWyogxw" target="_blank" rel="noopener noreferrer" title="YouTube">YT</a>
          <a href="https://www.linkedin.com/school/kirinyaga-university/" target="_blank" rel="noopener noreferrer" title="LinkedIn">IN</a>
        </div>
        {user && (
          <div className="kyu-header-user" onClick={() => navigate('/profile')}>
            <img
              src={user?.avatar || `https://ui-avatars.com/api/?name=${user?.name}&background=1a6b3c&color=fff`}
              alt={user?.name}
              className="kyu-header-avatar"
            />
          </div>
        )}
      </div>
    </header>
  );
}
