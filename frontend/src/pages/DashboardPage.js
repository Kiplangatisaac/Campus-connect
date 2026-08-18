import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useChat } from '../context/ChatContext';
import UrgentAnnouncements from '../components/UrgentAnnouncements';
import api from '../services/api';
import { format } from 'date-fns';
import '../styles/dashboard.css';

export default function DashboardPage() {
  const { user } = useAuth();
  const { totalUnread } = useChat();
  const [stats, setStats] = useState({});
  const [recentActivity, setRecentActivity] = useState([]);
  const [upcomingEvents, setUpcomingEvents] = useState([]);
  const [announcements, setAnnouncements] = useState([]);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const [statsRes, activityRes, eventsRes, announcementsRes] = await Promise.all([
        api.get('/dashboard/stats').catch(() => ({ data: {} })),
        api.get('/dashboard/activity').catch(() => ({ data: { activities: [] } })),
        api.get('/events?upcoming=true&limit=3').catch(() => ({ data: { events: [] } })),
        api.get('/bulletin?urgent=true&limit=5').catch(() => ({ data: { posts: [] } }))
      ]);
      setStats(statsRes.data);
      setRecentActivity(activityRes.data.activities || []);
      setUpcomingEvents(eventsRes.data.events || []);
      setAnnouncements(announcementsRes.data.posts || []);
    } catch (err) {
      console.error(err);
    }
  };

  const quickActions = [
    { icon: '💬', label: 'Messages', path: '/chat', color: '#2196f3' },
    { icon: '👥', label: 'Groups', path: '/groups', color: '#4caf50' },
    { icon: '🌟', label: 'Moments', path: '/moments', color: '#ff5722' },
    { icon: '📋', label: 'Bulletin', path: '/bulletin', color: '#ff9800' },
    { icon: '📅', label: 'Events', path: '/events', color: '#9c27b0' },
    { icon: '📆', label: 'Calendar', path: '/calendar', color: '#00bcd4' },
  ];

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <div className="welcome-section">
          <h1>Welcome back, {user?.name?.split(' ')[0]}!</h1>
          <p className="welcome-date">{format(new Date(), 'EEEE, MMMM d, yyyy')}</p>
        </div>
      </div>

      <UrgentAnnouncements announcements={announcements} />

      <div className="kyu-stats-bar">
        <div className="kyu-stat-item">
          <span className="kyu-stat-number">13000+</span>
          <span className="kyu-stat-label">Students</span>
        </div>
        <div className="kyu-stat-divider"></div>
        <div className="kyu-stat-item">
          <span className="kyu-stat-number">300+</span>
          <span className="kyu-stat-label">Staff</span>
        </div>
        <div className="kyu-stat-divider"></div>
        <div className="kyu-stat-item">
          <span className="kyu-stat-number">100+</span>
          <span className="kyu-stat-label">Programmes</span>
        </div>
        <div className="kyu-stat-divider"></div>
        <div className="kyu-stat-item">
          <span className="kyu-stat-number">4</span>
          <span className="kyu-stat-label">Schools</span>
        </div>
      </div>

      <div className="stats-grid">
        <div className="stat-card messages">
          <div className="stat-icon">💬</div>
          <div className="stat-info">
            <span className="stat-value">{stats.messages || 0}</span>
            <span className="stat-label">Messages</span>
          </div>
          {totalUnread > 0 && <span className="stat-badge">{totalUnread} new</span>}
        </div>
        <div className="stat-card groups">
          <div className="stat-icon">👥</div>
          <div className="stat-info">
            <span className="stat-value">{stats.groups || 0}</span>
            <span className="stat-label">Groups</span>
          </div>
        </div>
        <div className="stat-card posts">
          <div className="stat-icon">📋</div>
          <div className="stat-info">
            <span className="stat-value">{stats.posts || 0}</span>
            <span className="stat-label">Posts</span>
          </div>
        </div>
        <div className="stat-card events">
          <div className="stat-icon">📅</div>
          <div className="stat-info">
            <span className="stat-value">{stats.events || 0}</span>
            <span className="stat-label">Events</span>
          </div>
        </div>
      </div>

      <div className="kyu-schools-section">
        <h3>Our Schools</h3>
        <div className="kyu-schools-grid">
          <div className="kyu-school-card">
            <div className="school-icon">🏥</div>
            <h4>School of Health Sciences</h4>
            <p>Clinical care, research and academia</p>
            <span className="school-programs">Bachelors, Masters, PhD</span>
          </div>
          <div className="kyu-school-card">
            <div className="school-icon">📊</div>
            <h4>School of Business & Education</h4>
            <p>Career guidance and mentorship</p>
            <span className="school-programs">Bachelors, Masters, PhD</span>
          </div>
          <div className="kyu-school-card">
            <div className="school-icon">🔬</div>
            <h4>School of Pure & Applied Sciences</h4>
            <p>Science, Technology and Mathematics</p>
            <span className="school-programs">Bachelors, Masters, PhD</span>
          </div>
          <div className="kyu-school-card">
            <div className="school-icon">⚙️</div>
            <h4>School of Engineering & Technology</h4>
            <p>Practical-based teaching and industrial attachments</p>
            <span className="school-programs">Bachelors, Masters, PhD</span>
          </div>
        </div>
      </div>

      <div className="quick-actions">
        <h3>Quick Actions</h3>
        <div className="quick-actions-grid">
          {quickActions.map(action => (
            <Link key={action.path} to={action.path} className="quick-action-card" style={{ '--action-color': action.color }}>
              <span className="quick-action-icon">{action.icon}</span>
              <span className="quick-action-label">{action.label}</span>
            </Link>
          ))}
        </div>
      </div>

      <div className="dashboard-grid">
        <div className="dashboard-section recent-activity">
          <div className="section-header">
            <h3>Recent Activity</h3>
            <Link to="/bulletin" className="see-all">See all</Link>
          </div>
          <div className="activity-list">
            {recentActivity.length > 0 ? recentActivity.map((activity, i) => (
              <div key={activity._id || i} className="activity-item">
                <div className="activity-avatar">
                  <img
                    src={activity.user?.avatar || `https://ui-avatars.com/api/?name=${activity.user?.name}`}
                    alt=""
                  />
                </div>
                <div className="activity-content">
                  <p><strong>{activity.user?.name}</strong> {activity.action}</p>
                  <span className="activity-time">{format(new Date(activity.createdAt), 'HH:mm')}</span>
                </div>
              </div>
            )) : (
              <div className="empty-state">No recent activity</div>
            )}
          </div>
        </div>

        <div className="dashboard-section upcoming-events">
          <div className="section-header">
            <h3>Upcoming Events</h3>
            <Link to="/events" className="see-all">See all</Link>
          </div>
          <div className="events-list">
            {upcomingEvents.length > 0 ? upcomingEvents.map(event => (
              <div key={event._id} className="event-list-item">
                <div className="event-list-date">
                  <span className="event-month">{format(new Date(event.date), 'MMM')}</span>
                  <span className="event-day">{format(new Date(event.date), 'd')}</span>
                </div>
                <div className="event-list-info">
                  <span className="event-list-title">{event.title}</span>
                  <span className="event-list-time">{format(new Date(event.date), 'HH:mm')}</span>
                </div>
              </div>
            )) : (
              <div className="empty-state">No upcoming events</div>
            )}
          </div>
        </div>
      </div>

      <div className="kyu-footer-info">
        <div className="kyu-footer-contact">
          <p>P.O.Box 143-10300 Kerugoya, Kenya</p>
          <p>+254 709 742000 | info@kyu.ac.ke</p>
        </div>
        <div className="kyu-footer-iso">
          <img src="/images/iso-badge.png" alt="ISO 9001:2015" className="iso-badge" onError={(e) => { e.target.style.display = 'none'; }} />
          <span>KyU is ISO 9001:2015 Certified</span>
        </div>
      </div>
    </div>
  );
}
