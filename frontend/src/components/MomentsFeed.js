import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { FiHeart, FiMessageCircle, FiShare2, FiCamera, FiMoreHorizontal } from 'react-icons/fi';
import { format } from 'date-fns';
import api from '../services/api';
import './MomentsFeed.css';

const MomentsFeed = () => {
  const [moments, setMoments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [newPost, setNewPost] = useState('');
  const [posting, setPosting] = useState(false);

  useEffect(() => {
    loadMoments();
  }, []);

  const loadMoments = async () => {
    try {
      const { data } = await api.get('/moments/');
      setMoments(data);
    } catch (err) {
      console.error('Failed to load moments');
    } finally {
      setLoading(false);
    }
  };

  const handlePost = async () => {
    if (!newPost.trim()) return;
    setPosting(true);
    try {
      const { data } = await api.post('/moments/', { content: newPost });
      setMoments(prev => [data, ...prev]);
      setNewPost('');
    } catch (err) {
      console.error('Failed to post');
    } finally {
      setPosting(false);
    }
  };

  const handleLike = async (momentId) => {
    try {
      const { data } = await api.post(`/moments/${momentId}/like`);
      setMoments(prev => prev.map(m => {
        if (m.id === momentId) {
          return {
            ...m,
            is_liked: data.liked,
            likes_count: data.liked ? m.likes_count + 1 : m.likes_count - 1
          };
        }
        return m;
      }));
    } catch (err) {
      console.error('Failed to like');
    }
  };

  if (loading) {
    return <div className="moments-loading"><div className="spinner"></div></div>;
  }

  return (
    <div className="moments-feed">
      <div className="moments-header">
        <h2>Moments</h2>
      </div>

      <div className="moments-compose">
        <div className="compose-input">
          <textarea
            value={newPost}
            onChange={(e) => setNewPost(e.target.value)}
            placeholder="What's happening on campus?"
            rows={3}
          />
        </div>
        <div className="compose-actions">
          <button className="compose-camera"><FiCamera /> Photo</button>
          <button
            className="compose-submit"
            onClick={handlePost}
            disabled={!newPost.trim() || posting}
          >
            {posting ? 'Posting...' : 'Post'}
          </button>
        </div>
      </div>

      <div className="moments-list">
        {moments.map((moment, index) => (
          <motion.div
            key={moment.id}
            className="moment-card"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
          >
            <div className="moment-header">
              <div className="moment-user">
                <div className="moment-avatar">
                  {moment.user_avatar ? (
                    <img src={moment.user_avatar} alt="" />
                  ) : (
                    <span>{moment.user_name?.charAt(0)}</span>
                  )}
                </div>
                <div className="moment-user-info">
                  <h4>{moment.user_name}</h4>
                  <span>{format(new Date(moment.created_at), 'MMM d, h:mm a')}</span>
                </div>
              </div>
              <button className="moment-more"><FiMoreHorizontal /></button>
            </div>

            <div className="moment-content">
              <p>{moment.content}</p>
              {moment.image_url && (
                <img src={moment.image_url} alt="" className="moment-image" />
              )}
            </div>

            <div className="moment-actions">
              <button
                className={`moment-action ${moment.is_liked ? 'liked' : ''}`}
                onClick={() => handleLike(moment.id)}
              >
                <FiHeart /> {moment.likes_count || ''}
              </button>
              <button className="moment-action">
                <FiMessageCircle /> {moment.comments_count || ''}
              </button>
              <button className="moment-action">
                <FiShare2 />
              </button>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
};

export default MomentsFeed;
