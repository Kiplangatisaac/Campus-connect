import React, { useState, useEffect } from 'react';
import EventCard from '../components/EventCard';
import api from '../services/api';
import { format, startOfMonth, endOfMonth, eachDayOfInterval } from 'date-fns';
import { toast } from 'react-toastify';

export default function EventsPage() {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(false);
  const [viewMode, setViewMode] = useState('list');
  const [activeCategory, setActiveCategory] = useState('all');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [currentMonth, setCurrentMonth] = useState(new Date());
  const [newEvent, setNewEvent] = useState({
    title: '',
    description: '',
    date: '',
    time: '',
    location: '',
    category: 'academic'
  });

  useEffect(() => {
    fetchEvents();
  }, []);

  const fetchEvents = async () => {
    setLoading(true);
    try {
      const { data } = await api.get('/events');
      setEvents(data.events || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateEvent = async (e) => {
    e.preventDefault();
    try {
      const eventDate = new Date(`${newEvent.date}T${newEvent.time || '09:00'}`);
      const { data } = await api.post('/events', {
        ...newEvent,
        date: eventDate
      });
      setEvents([data.event, ...events]);
      setShowCreateModal(false);
      setNewEvent({ title: '', description: '', date: '', time: '', location: '', category: 'academic' });
      toast.success('Event created!');
    } catch (err) {
      toast.error('Failed to create event');
    }
  };

  const filteredEvents = activeCategory === 'all'
    ? events
    : events.filter(e => e.category === activeCategory);

  const categories = [
    { key: 'all', label: 'All', icon: '📅' },
    { key: 'academic', label: 'Academic', icon: '📚' },
    { key: 'social', label: 'Social', icon: '🎉' },
    { key: 'sports', label: 'Sports', icon: '⚽' },
    { key: 'cultural', label: 'Cultural', icon: '🎭' },
    { key: 'workshop', label: 'Workshop', icon: '🔧' },
  ];

  const getDaysInMonth = () => {
    const start = startOfMonth(currentMonth);
    const end = endOfMonth(currentMonth);
    return eachDayOfInterval({ start, end });
  };

  const getEventsForDay = (day) => {
    return events.filter(e => {
      const eventDate = new Date(e.date);
      return eventDate.toDateString() === day.toDateString();
    });
  };

  return (
    <div className="events-page">
      <div className="page-header">
        <h1>Events</h1>
        <div className="header-actions">
          <div className="view-toggle">
            <button className={viewMode === 'list' ? 'active' : ''} onClick={() => setViewMode('list')}>📋 List</button>
            <button className={viewMode === 'calendar' ? 'active' : ''} onClick={() => setViewMode('calendar')}>📅 Calendar</button>
          </div>
          <button className="create-btn" onClick={() => setShowCreateModal(true)}>
            + Create Event
          </button>
        </div>
      </div>

      <div className="category-tabs">
        {categories.map(cat => (
          <button
            key={cat.key}
            className={`category-tab ${activeCategory === cat.key ? 'active' : ''}`}
            onClick={() => setActiveCategory(cat.key)}
          >
            <span>{cat.icon}</span>
            {cat.label}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="loading"><div className="spinner"></div></div>
      ) : viewMode === 'list' ? (
        <div className="events-list-view">
          {filteredEvents.map(event => (
            <EventCard key={event._id} event={event} />
          ))}
          {filteredEvents.length === 0 && (
            <div className="empty-state"><p>No events found</p></div>
          )}
        </div>
      ) : (
        <div className="calendar-view">
          <div className="calendar-header">
            <button onClick={() => setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() - 1))}>
              ◀
            </button>
            <h3>{format(currentMonth, 'MMMM yyyy')}</h3>
            <button onClick={() => setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1))}>
              ▶
            </button>
          </div>
          <div className="calendar-grid">
            {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(d => (
              <div key={d} className="calendar-day-header">{d}</div>
            ))}
            {getDaysInMonth().map(day => (
              <div key={day.toISOString()} className="calendar-day">
                <span className="day-number">{format(day, 'd')}</span>
                {getEventsForDay(day).length > 0 && (
                  <div className="day-events">
                    {getEventsForDay(day).slice(0, 2).map(e => (
                      <div key={e._id} className="day-event-dot" title={e.title}></div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {showCreateModal && (
        <div className="modal-overlay" onClick={() => setShowCreateModal(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <h3>Create Event</h3>
            <form onSubmit={handleCreateEvent}>
              <div className="form-group">
                <label>Title</label>
                <input
                  type="text"
                  value={newEvent.title}
                  onChange={(e) => setNewEvent({ ...newEvent, title: e.target.value })}
                  placeholder="Event title"
                  required
                />
              </div>
              <div className="form-group">
                <label>Category</label>
                <select
                  value={newEvent.category}
                  onChange={(e) => setNewEvent({ ...newEvent, category: e.target.value })}
                >
                  {categories.filter(c => c.key !== 'all').map(cat => (
                    <option key={cat.key} value={cat.key}>{cat.label}</option>
                  ))}
                </select>
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>Date</label>
                  <input
                    type="date"
                    value={newEvent.date}
                    onChange={(e) => setNewEvent({ ...newEvent, date: e.target.value })}
                    required
                  />
                </div>
                <div className="form-group">
                  <label>Time</label>
                  <input
                    type="time"
                    value={newEvent.time}
                    onChange={(e) => setNewEvent({ ...newEvent, time: e.target.value })}
                  />
                </div>
              </div>
              <div className="form-group">
                <label>Location</label>
                <input
                  type="text"
                  value={newEvent.location}
                  onChange={(e) => setNewEvent({ ...newEvent, location: e.target.value })}
                  placeholder="Event location"
                />
              </div>
              <div className="form-group">
                <label>Description</label>
                <textarea
                  value={newEvent.description}
                  onChange={(e) => setNewEvent({ ...newEvent, description: e.target.value })}
                  placeholder="Event description"
                  rows={4}
                />
              </div>
              <div className="modal-actions">
                <button type="button" className="btn-cancel" onClick={() => setShowCreateModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn-primary">Create Event</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
