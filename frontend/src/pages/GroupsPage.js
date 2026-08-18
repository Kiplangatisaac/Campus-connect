import React, { useState, useEffect } from 'react';
import GroupCard from '../components/GroupCard';
import api from '../services/api';
import { toast } from 'react-toastify';

export default function GroupsPage() {
  const [groups, setGroups] = useState([]);
  const [filteredGroups, setFilteredGroups] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [activeFilter, setActiveFilter] = useState('all');
  const [loading, setLoading] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newGroup, setNewGroup] = useState({
    name: '',
    description: '',
    type: 'study',
    department: ''
  });

  useEffect(() => {
    fetchGroups();
  }, []);

  useEffect(() => {
    let filtered = groups;
    if (searchQuery) {
      filtered = filtered.filter(g =>
        g.name.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }
    if (activeFilter !== 'all') {
      filtered = filtered.filter(g => g.type === activeFilter);
    }
    setFilteredGroups(filtered);
  }, [groups, searchQuery, activeFilter]);

  const fetchGroups = async () => {
    setLoading(true);
    try {
      const { data } = await api.get('/groups');
      setGroups(data.groups || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateGroup = async (e) => {
    e.preventDefault();
    try {
      const { data } = await api.post('/groups', newGroup);
      setGroups([data.group, ...groups]);
      setShowCreateModal(false);
      setNewGroup({ name: '', description: '', type: 'study', department: '' });
      toast.success('Group created!');
    } catch (err) {
      toast.error('Failed to create group');
    }
  };

  const handleJoinGroup = async (groupId) => {
    try {
      await api.post(`/groups/${groupId}/join`);
      fetchGroups();
      toast.success('Joined group!');
    } catch (err) {
      toast.error('Failed to join group');
    }
  };

  const handleLeaveGroup = async (groupId) => {
    try {
      await api.post(`/groups/${groupId}/leave`);
      fetchGroups();
      toast.success('Left group');
    } catch (err) {
      toast.error('Failed to leave group');
    }
  };

  const filters = [
    { key: 'all', label: 'All Groups' },
    { key: 'faculty', label: 'Faculty' },
    { key: 'study', label: 'Study Groups' },
    { key: 'club', label: 'Clubs' }
  ];

  return (
    <div className="groups-page">
      <div className="page-header">
        <h1>Groups</h1>
        <button className="create-btn" onClick={() => setShowCreateModal(true)}>
          + Create Group
        </button>
      </div>

      <div className="groups-toolbar">
        <input
          type="text"
          placeholder="Search groups..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="search-input"
        />
        <div className="filter-tabs">
          {filters.map(f => (
            <button
              key={f.key}
              className={`filter-tab ${activeFilter === f.key ? 'active' : ''}`}
              onClick={() => setActiveFilter(f.key)}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="loading"><div className="spinner"></div></div>
      ) : (
        <div className="groups-grid">
          {filteredGroups.map(group => (
            <GroupCard
              key={group._id}
              group={group}
              onJoin={handleJoinGroup}
              onLeave={handleLeaveGroup}
            />
          ))}
          {filteredGroups.length === 0 && (
            <div className="empty-state">
              <p>No groups found</p>
            </div>
          )}
        </div>
      )}

      {showCreateModal && (
        <div className="modal-overlay" onClick={() => setShowCreateModal(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <h3>Create Group</h3>
            <form onSubmit={handleCreateGroup}>
              <div className="form-group">
                <label>Group Name</label>
                <input
                  type="text"
                  value={newGroup.name}
                  onChange={(e) => setNewGroup({ ...newGroup, name: e.target.value })}
                  placeholder="Enter group name"
                  required
                />
              </div>
              <div className="form-group">
                <label>Description</label>
                <textarea
                  value={newGroup.description}
                  onChange={(e) => setNewGroup({ ...newGroup, description: e.target.value })}
                  placeholder="What is this group about?"
                  rows={3}
                />
              </div>
              <div className="form-group">
                <label>Type</label>
                <select
                  value={newGroup.type}
                  onChange={(e) => setNewGroup({ ...newGroup, type: e.target.value })}
                >
                  <option value="study">Study Group</option>
                  <option value="faculty">Faculty</option>
                  <option value="club">Club</option>
                </select>
              </div>
              <div className="form-group">
                <label>Department</label>
                <input
                  type="text"
                  value={newGroup.department}
                  onChange={(e) => setNewGroup({ ...newGroup, department: e.target.value })}
                  placeholder="Department (optional)"
                />
              </div>
              <div className="modal-actions">
                <button type="button" className="btn-cancel" onClick={() => setShowCreateModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn-primary">Create</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
