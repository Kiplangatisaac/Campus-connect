import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import { format } from 'date-fns';
import { FiCalendar, FiLink, FiRefreshCw, FiCheck, FiX, FiClock } from 'react-icons/fi';
import { toast } from 'react-toastify';
import './CalendarPage.css';

const PROVIDERS = [
  { id: 'google_calendar', name: 'Google Calendar', icon: '📅', color: '#4285f4', description: 'Sync with Google Calendar events', query: 'google_calendar' },
  { id: 'outlook', name: 'Microsoft Outlook', icon: '📧', color: '#0078d4', description: 'Sync with Outlook & Office 365', query: 'outlook' },
  { id: 'calendly', name: 'Calendly', icon: '🕐', color: '#006bff', description: 'Import scheduling links & events', query: 'calendly' },
  { id: 'slack', name: 'Slack', icon: '💬', color: '#4a154b', description: 'Sync Slack calendar & reminders', query: 'slack' },
];

export default function CalendarPage() {
  const { user: _user } = useAuth();
  const [connections, setConnections] = useState([]);
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [selectedDate, setSelectedDate] = useState(new Date());

  useEffect(() => {
    loadCalendarData();
  }, []);

  const loadCalendarData = async () => {
    setLoading(true);
    try {
      const [connRes, eventsRes] = await Promise.all([
        api.get('/calendar/status').catch(() => ({ data: { connections: [] } })),
        api.get('/calendar/events', { params: { limit: 100 } }).catch(() => ({ data: { events: [] } }))
      ]);
      setConnections(connRes.data.connections || []);
      const evts = eventsRes.data.events || [];
      setEvents(evts);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleConnect = async (provider) => {
    try {
      const { data } = await api.post(`/calendar/connect`, null, { params: { provider: provider.id } });
      if (data.auth_url) {
        window.open(data.auth_url, '_blank', 'width=600,height=700');
        toast.info(`Connect your ${provider.name} in the popup window`);
      } else {
        toast.success(`${provider.name} connected successfully`);
      }
      loadCalendarData();
    } catch (err) {
      const msg = err.response?.data?.detail || 'Connection failed. Configure calendar API keys in backend .env';
      toast.error(msg);
    }
  };

  const handleDisconnect = async (providerId) => {
    try {
      const conn = connections.find(c => c.provider === providerId);
      if (!conn) return;
      const { data } = await api.delete(`/calendar/status/${conn.id}`);
      toast.success(data.message || 'Disconnected successfully');
      loadCalendarData();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to disconnect');
    }
  };

  const handleSyncAll = async () => {
    setSyncing(true);
    let total = 0;
    try {
      for (const conn of connections) {
        if (!conn.is_active) continue;
        try {
          const { data } = await api.post('/calendar/sync', null, { params: { connection_id: conn.id } });
          total += data.events_synced || 0;
        } catch (e) {
          console.warn(`Sync failed for ${conn.provider}:`, e);
        }
      }
      toast.success(`Synced ${total} events`);
      loadCalendarData();
    } catch (err) {
      toast.error('Sync failed');
    } finally {
      setSyncing(false);
    }
  };

  const handleImportEvent = async (event) => {
    try {
      const { data } = await api.post('/calendar/import', null, { params: { event_ids: [event.id] } });
      toast.success(`Imported "${data.imported?.[0]?.title || 'event'}" to campus`);
      loadCalendarData();
    } catch (err) {
      toast.error('Import failed');
    }
  };

  const getDaysInMonth = (date) => {
    const year = date.getFullYear();
    const month = date.getMonth();
    const firstDay = new Date(year, month, 1).getDay();
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    const days = [];
    for (let i = 0; i < firstDay; i++) days.push(null);
    for (let i = 1; i <= daysInMonth; i++) days.push(i);
    return days;
  };

  const getEventsForDay = (day) => {
    if (!day) return [];
    const y = selectedDate.getFullYear();
    const m = String(selectedDate.getMonth() + 1).padStart(2, '0');
    const d = String(day).padStart(2, '0');
    const dateStr = `${y}-${m}-${d}`;
    return events.filter(e => e.start_time?.startsWith(dateStr) || e.start_time?.startsWith(dateStr + 'T'));
  };

  const isConnected = (providerId) => connections.some(c => c.provider === providerId && c.is_active);

  const days = getDaysInMonth(selectedDate);
  const monthName = format(selectedDate, 'MMMM yyyy');

  return (
    <div className="calendar-page">
      <div className="calendar-header">
        <div className="calendar-title">
          <FiCalendar className="cal-icon" />
          <h2>Calendar Integration</h2>
        </div>
        <button className="sync-btn" onClick={handleSyncAll} disabled={syncing || connections.filter(c => c.is_active).length === 0}>
          <FiRefreshCw className={syncing ? 'spinning' : ''} />
          {syncing ? 'Syncing...' : 'Sync All'}
        </button>
      </div>

      <div className="calendar-layout">
        <div className="calendar-sidebar-section">
          <h3>Connect Your Calendar</h3>
          <p className="section-desc">Link your apps to sync events automatically. <strong>Note:</strong> Configuring OAuth client IDs in backend .env enables live connections.</p>

          <div className="provider-list">
            {PROVIDERS.map(provider => {
              const connected = isConnected(provider.id);
              return (
                <div key={provider.id} className={`provider-card ${connected ? 'connected' : ''}`}>
                  <div className="provider-icon" style={{ background: provider.color }}>
                    {provider.icon}
                  </div>
                  <div className="provider-info">
                    <h4>{provider.name}</h4>
                    <p>{provider.description}</p>
                    {connected && <span className="connected-badge"><FiCheck /> Connected</span>}
                  </div>
                  <div className="provider-actions">
                    {connected ? (
                      <button className="disconnect-btn" onClick={() => handleDisconnect(provider.id)} title="Disconnect">
                        <FiX />
                      </button>
                    ) : (
                      <button className="connect-btn" onClick={() => handleConnect(provider)}>
                        <FiLink /> Connect
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>

          {connections.filter(c => c.is_active).length > 0 && (
            <div className="sync-status">
              <h4>Sync Status</h4>
              {connections.filter(c => c.is_active).map(conn => (
                <div key={conn.id} className="sync-item">
                  <span>{PROVIDERS.find(p => p.id === conn.provider)?.name || conn.provider}</span>
                  <span className="sync-time">
                    <FiClock />
                    {conn.last_synced ? format(new Date(conn.last_synced), 'MMM d, HH:mm') : 'Never'}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="calendar-main">
          <div className="calendar-nav">
            <button onClick={() => setSelectedDate(new Date(selectedDate.getFullYear(), selectedDate.getMonth() - 1))}>&larr;</button>
            <h3>{monthName}</h3>
            <button onClick={() => setSelectedDate(new Date(selectedDate.getFullYear(), selectedDate.getMonth() + 1))}>&rarr;</button>
          </div>

          <div className="calendar-grid">
            <div className="calendar-weekdays">
              {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(d => (
                <div key={d} className="weekday">{d}</div>
              ))}
            </div>
            <div className="calendar-days">
              {days.map((day, i) => {
                const dayEvents = getEventsForDay(day);
                const today = new Date();
                const isToday = day === today.getDate() &&
                  selectedDate.getMonth() === today.getMonth() &&
                  selectedDate.getFullYear() === today.getFullYear();
                return (
                  <div
                    key={i}
                    className={`calendar-day ${day ? '' : 'empty'} ${isToday ? 'today' : ''} ${dayEvents.length > 0 ? 'has-events' : ''}`}
                    onClick={() => day && setSelectedDate(new Date(selectedDate.getFullYear(), selectedDate.getMonth(), day))}
                  >
                    {day && <span className="day-number">{day}</span>}
                    {dayEvents.slice(0, 2).map((ev, j) => (
                      <div key={j} className="day-event" title={ev.title}>{ev.title?.substring(0, 8)}</div>
                    ))}
                    {dayEvents.length > 2 && <div className="day-more">+{dayEvents.length - 2}</div>}
                  </div>
                );
              })}
            </div>
          </div>

          {events.length > 0 && (
            <div className="upcoming-events-section">
              <h3>Upcoming Events</h3>
              <div className="events-timeline">
                {events.slice(0, 10).map((event, i) => {
                  const start = event.start_time ? format(new Date(event.start_time), 'MMM d, HH:mm') : 'TBD';
                  return (
                    <div key={event.id || i} className="timeline-event">
                      <div className="timeline-dot"></div>
                      <div className="timeline-content">
                        <h4>{event.title}</h4>
                        <p>{start}</p>
                        {event.synced === 0 && (
                          <button className="import-btn" onClick={() => handleImportEvent(event)}>Import to Campus</button>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {events.length === 0 && !loading && (
            <div className="empty-calendar">
              <FiCalendar size={64} />
              <h3>No Events Yet</h3>
              <p>Connect a calendar above to sync your events, or check the Events page for campus events.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
