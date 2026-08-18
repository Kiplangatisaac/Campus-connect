import React, { useState, useEffect } from 'react';
import BulletinPost from '../components/BulletinPost';
import api from '../services/api';
import { toast } from 'react-toastify';

export default function BulletinPage() {
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [activeCategory, setActiveCategory] = useState('all');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newPost, setNewPost] = useState({
    title: '',
    content: '',
    category: 'general'
  });

  useEffect(() => {
    fetchPosts();
  }, []);

  const fetchPosts = async () => {
    setLoading(true);
    try {
      const { data } = await api.get('/bulletin');
      setPosts(data.posts || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreatePost = async (e) => {
    e.preventDefault();
    if (!newPost.title.trim() || !newPost.content.trim()) {
      toast.error('Title and content are required');
      return;
    }
    try {
      const { data } = await api.post('/bulletin', newPost);
      setPosts([data.post, ...posts]);
      setShowCreateModal(false);
      setNewPost({ title: '', content: '', category: 'general' });
      toast.success('Post created!');
    } catch (err) {
      toast.error('Failed to create post');
    }
  };

  const filteredPosts = activeCategory === 'all'
    ? posts
    : posts.filter(p => p.category === activeCategory);

  const categories = [
    { key: 'all', label: 'All', icon: '📋' },
    { key: 'academic', label: 'Academic', icon: '📚' },
    { key: 'events', label: 'Events', icon: '🎉' },
    { key: 'jobs', label: 'Jobs', icon: '💼' },
    { key: 'housing', label: 'Housing', icon: '🏠' },
    { key: 'general', label: 'General', icon: '💬' },
    { key: 'urgent', label: 'Urgent', icon: '🔴' },
  ];

  return (
    <div className="bulletin-page">
      <div className="page-header">
        <h1>Bulletin Board</h1>
        <button className="create-btn" onClick={() => setShowCreateModal(true)}>
          + New Post
        </button>
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
      ) : (
        <div className="bulletin-posts">
          {filteredPosts.map(post => (
            <BulletinPost key={post._id} post={post} onRefresh={fetchPosts} />
          ))}
          {filteredPosts.length === 0 && (
            <div className="empty-state">
              <p>No posts in this category</p>
            </div>
          )}
        </div>
      )}

      {showCreateModal && (
        <div className="modal-overlay" onClick={() => setShowCreateModal(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <h3>Create Bulletin Post</h3>
            <form onSubmit={handleCreatePost}>
              <div className="form-group">
                <label>Title</label>
                <input
                  type="text"
                  value={newPost.title}
                  onChange={(e) => setNewPost({ ...newPost, title: e.target.value })}
                  placeholder="Post title"
                  required
                />
              </div>
              <div className="form-group">
                <label>Category</label>
                <select
                  value={newPost.category}
                  onChange={(e) => setNewPost({ ...newPost, category: e.target.value })}
                >
                  {categories.filter(c => c.key !== 'all').map(cat => (
                    <option key={cat.key} value={cat.key}>{cat.label}</option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label>Content</label>
                <textarea
                  value={newPost.content}
                  onChange={(e) => setNewPost({ ...newPost, content: e.target.value })}
                  placeholder="Write your post..."
                  rows={6}
                  required
                />
              </div>
              <div className="modal-actions">
                <button type="button" className="btn-cancel" onClick={() => setShowCreateModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn-primary">Publish</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
