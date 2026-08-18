import React, { useState, useEffect } from 'react';
import { format, differenceInDays, differenceInHours, differenceInMinutes } from 'date-fns';
import api from '../services/api';
import { toast } from 'react-toastify';

export default function EventCard({ event, onRSVP }) {
  const [rsvpStatus, setRsvpStatus] = useState(event.rsvpStatus || null);
  const [attendeeCount, setAttendeeCount] = useState(event.attendees?.length || 0);
  const [countdown, setCountdown] = useState('');

  useEffect(() => {
    const updateCountdown = () => {
      const now = new Date();
      const eventDate = new Date(event.date);
      const diff = eventDate - now;

      if (diff <= 0) {
        setCountdown('Happening now');
        return;
      }

      const days = differenceInDays(eventDate, now);
      const hours = differenceInHours(eventDate, now) % 24;
      const mins = differenceInMinutes(eventDate, now) % 60;

      if (days > 0) setCountdown(`${days}d ${hours}h`);
      else if (hours > 0) setCountdown(`${hours}h ${mins}m`);
      else setCountdown(`${mins}m`);
    };

    updateCountdown();
    const interval = setInterval(updateCountdown, 60000);
    return () => clearInterval(interval);
  }, [event.date]);

  const handleRSVP = async (status) => {
    try {
      const { data } = await api.post(`/events/${event._id}/rsvp`, { status });
      setRsvpStatus(status);
      setAttendeeCount(data.attendeeCount || attendeeCount);
      toast.success(`RSVP: ${status}`);
      onRSVP?.(event._id, status);
    } catch (err) {
      toast.error('Failed to RSVP');
    }
  };

  const isPast = new Date(event.date) < new Date();

  const categoryIcons = {
    academic: '📚',
    social: '🎉',
    sports: '⚽',
    cultural: '🎭',
    workshop: '🔧',
    other: '📌'
  };

  return (
    <div className={`event-card ${isPast ? 'past' : ''}`}>
      <div className="event-card-date">
        <span className="event-date-month">{format(new Date(event.date), 'MMM')}</span>
        <span className="event-date-day">{format(new Date(event.date), 'd')}</span>
      </div>
      <div className="event-card-body">
        <div className="event-card-header">
          <span className="event-category-icon">{categoryIcons[event.category] || '📌'}</span>
          <span className="event-category">{event.category}</span>
          <span className="event-countdown">{countdown}</span>
        </div>
        <h3 className="event-title">{event.title}</h3>
        <p className="event-description">{event.description}</p>
        <div className="event-meta">
          <span className="event-meta-item">📍 {event.location || 'TBA'}</span>
          <span className="event-meta-item">🕐 {format(new Date(event.date), 'HH:mm')}</span>
          <span className="event-meta-item">👥 {attendeeCount} attending</span>
        </div>
        {event.organizer && (
          <div className="event-organizer">
            <img
              src={event.organizer.avatar || `https://ui-avatars.com/api/?name=${event.organizer.name}&background=1a237e&color=fff`}
              alt=""
            />
            <span>Organized by {event.organizer.name}</span>
          </div>
        )}
      </div>
      <div className="event-card-footer">
        {!isPast ? (
          <>
            <button
              className={`event-rsvp-btn going ${rsvpStatus === 'going' ? 'active' : ''}`}
              onClick={() => handleRSVP('going')}
            >
              ✓ Going
            </button>
            <button
              className={`event-rsvp-btn maybe ${rsvpStatus === 'maybe' ? 'active' : ''}`}
              onClick={() => handleRSVP('maybe')}
            >
              ? Maybe
            </button>
            <button
              className={`event-rsvp-btn not-going ${rsvpStatus === 'not_going' ? 'active' : ''}`}
              onClick={() => handleRSVP('not_going')}
            >
              ✕ Not Going
            </button>
          </>
        ) : (
          <span className="event-past-label">Past Event</span>
        )}
      </div>
    </div>
  );
}
