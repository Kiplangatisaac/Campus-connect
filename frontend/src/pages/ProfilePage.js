import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import { toast } from 'react-toastify';

export default function ProfilePage() {
  const { userId } = useParams();
  const { user: currentUser, updateUser } = useAuth();
  const [profileUser, setProfileUser] = useState(null);
  const [isOwnProfile, setIsOwnProfile] = useState(false);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);
  const [editData, setEditData] = useState({});
  const [stats, setStats] = useState({});

  useEffect(() => {
    fetchProfile();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userId]);

  const fetchProfile = async () => {
    setLoading(true);
    try {
      if (!userId || userId === currentUser?._id) {
        setProfileUser(currentUser);
        setIsOwnProfile(true);
        setEditData({
          name: currentUser?.name || '',
          bio: currentUser?.bio || '',
          department: currentUser?.department || '',
          course: currentUser?.course || ''
        });
      } else {
        const { data } = await api.get(`/users/${userId}`);
        setProfileUser(data.user);
        setIsOwnProfile(false);
      }
      const { data: statsData } = await api.get(`/users/${userId || currentUser?._id}/stats`).catch(() => ({ data: {} }));
      setStats(statsData);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveProfile = async () => {
    try {
      const { data } = await api.put('/users/profile', editData);
      updateUser(data.user);
      setProfileUser(data.user);
      setEditing(false);
      toast.success('Profile updated!');
    } catch (err) {
      toast.error('Failed to update profile');
    }
  };

  const handleAvatarUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const formData = new FormData();
    formData.append('avatar', file);
    try {
      const { data } = await api.post('/users/avatar', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      updateUser({ avatar: data.avatar });
      setProfileUser(prev => ({ ...prev, avatar: data.avatar }));
      toast.success('Avatar updated!');
    } catch (err) {
      toast.error('Failed to upload avatar');
    }
  };

  const roleColors = {
    student: '#2196f3',
    moderator: '#4caf50',
    admin: '#f44336'
  };

  const badges = [
    { icon: '🎓', label: 'Student', condition: true },
    { icon: '💬', label: 'Chatterbox', condition: stats.messagesSent > 100 },
    { icon: '🌟', label: 'Active', condition: stats.daysActive > 30 },
    { icon: '👥', label: 'Social', condition: stats.groupsJoined > 5 },
    { icon: '📋', label: 'Reporter', condition: stats.postsCreated > 10 },
    { icon: '🎯', label: 'Organizer', condition: stats.eventsCreated > 5 },
  ];

  if (loading) {
    return (
      <div className="loading"><div className="spinner"></div></div>
    );
  }

  return (
    <div className="profile-page">
      <div className="profile-header-section">
        <div className="profile-cover"></div>
        <div className="profile-avatar-section">
          <div className="profile-avatar-wrapper">
            <img
              src={profileUser?.avatar || `https://ui-avatars.com/api/?name=${profileUser?.name}&background=1a237e&color=fff&size=120`}
              alt=""
              className="profile-avatar-large"
            />
            {isOwnProfile && (
              <label className="avatar-upload-btn">
                📷
                <input type="file" accept="image/*" onChange={handleAvatarUpload} style={{ display: 'none' }} />
              </label>
            )}
          </div>
          <div className="profile-main-info">
            <h1>{profileUser?.name}</h1>
            <span
              className="profile-role-badge"
              style={{ background: roleColors[profileUser?.role] }}
            >
              {profileUser?.role?.charAt(0).toUpperCase() + profileUser?.role?.slice(1)}
            </span>
            {profileUser?.department && (
              <p className="profile-department">📚 {profileUser.department}</p>
            )}
            {profileUser?.course && (
              <p className="profile-course">🎓 {profileUser.course}</p>
            )}
          </div>
          {isOwnProfile && !editing && (
            <button className="edit-profile-btn" onClick={() => setEditing(true)}>
              ✏️ Edit Profile
            </button>
          )}
        </div>
      </div>

      <div className="profile-content">
        <div className="profile-sidebar">
          <div className="profile-stats-card">
            <h3>Stats</h3>
            <div className="profile-stats-grid">
              <div className="profile-stat">
                <span className="stat-number">{stats.messagesSent || 0}</span>
                <span className="stat-name">Messages</span>
              </div>
              <div className="profile-stat">
                <span className="stat-number">{stats.groupsJoined || 0}</span>
                <span className="stat-name">Groups</span>
              </div>
              <div className="profile-stat">
                <span className="stat-number">{stats.postsCreated || 0}</span>
                <span className="stat-name">Posts</span>
              </div>
              <div className="profile-stat">
                <span className="stat-number">{stats.eventsAttended || 0}</span>
                <span className="stat-name">Events</span>
              </div>
            </div>
          </div>

          <div className="profile-badges-card">
            <h3>Badges</h3>
            <div className="badges-grid">
              {badges.map((badge, i) => (
                <div
                  key={i}
                  className={`badge-item ${badge.condition ? 'earned' : 'locked'}`}
                  title={badge.label}
                >
                  <span className="badge-icon">{badge.icon}</span>
                  <span className="badge-label">{badge.label}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="profile-main">
          {editing ? (
            <div className="profile-edit-form">
              <h3>Edit Profile</h3>
              <div className="form-group">
                <label>Name</label>
                <input
                  type="text"
                  value={editData.name}
                  onChange={(e) => setEditData({ ...editData, name: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label>Bio</label>
                <textarea
                  value={editData.bio}
                  onChange={(e) => setEditData({ ...editData, bio: e.target.value })}
                  rows={4}
                  placeholder="Tell us about yourself..."
                />
              </div>
              <div className="form-group">
                <label>Department</label>
                <input
                  type="text"
                  value={editData.department}
                  onChange={(e) => setEditData({ ...editData, department: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label>Course</label>
                <input
                  type="text"
                  value={editData.course}
                  onChange={(e) => setEditData({ ...editData, course: e.target.value })}
                />
              </div>
              <div className="form-actions">
                <button className="btn-cancel" onClick={() => setEditing(false)}>Cancel</button>
                <button className="btn-primary" onClick={handleSaveProfile}>Save Changes</button>
              </div>
            </div>
          ) : (
            <div className="profile-info-card">
              <h3>About</h3>
              <p className="profile-bio">{profileUser?.bio || 'No bio yet'}</p>
              <div className="profile-details">
                <div className="detail-item">
                  <span className="detail-label">Email</span>
                  <span className="detail-value">{profileUser?.email}</span>
                </div>
                {profileUser?.regNumber && (
                  <div className="detail-item">
                    <span className="detail-label">Reg Number</span>
                    <span className="detail-value">{profileUser.regNumber}</span>
                  </div>
                )}
                {profileUser?.yearOfStudy && (
                  <div className="detail-item">
                    <span className="detail-label">Year</span>
                    <span className="detail-value">Year {profileUser.yearOfStudy}</span>
                  </div>
                )}
                <div className="detail-item">
                  <span className="detail-label">Joined</span>
                  <span className="detail-value">
                    {new Date(profileUser?.createdAt).toLocaleDateString()}
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
