import React, { useState } from 'react';
import { format } from 'date-fns';
import api from '../services/api';
import { toast } from 'react-toastify';

export default function BulletinPost({ post, onRefresh }) {
  const [showComments, setShowComments] = useState(false);
  const [commentText, setCommentText] = useState('');
  const [comments, setComments] = useState(post.comments || []);
  const [likes, setLikes] = useState(post.likes?.length || 0);
  const [isLiked, setIsLiked] = useState(post.likes?.includes(localStorage.getItem('userId')));

  const categoryColors = {
    academic: '#1a237e',
    events: '#ffd700',
    jobs: '#4caf50',
    housing: '#ff9800',
    general: '#9e9e9e',
    urgent: '#f44336'
  };

  const handleLike = async () => {
    try {
      const { data } = await api.post(`/bulletin/${post._id}/like`);
      setLikes(data.likes);
      setIsLiked(!isLiked);
    } catch (err) {
      toast.error('Failed to like post');
    }
  };

  const handleComment = async (e) => {
    e.preventDefault();
    if (!commentText.trim()) return;
    try {
      const { data } = await api.post(`/bulletin/${post._id}/comments`, {
        content: commentText
      });
      setComments([...comments, data.comment]);
      setCommentText('');
      toast.success('Comment added');
    } catch (err) {
      toast.error('Failed to add comment');
    }
  };

  const handleDelete = async () => {
    if (!window.confirm('Delete this post?')) return;
    try {
      await api.delete(`/bulletin/${post._id}`);
      toast.success('Post deleted');
      onRefresh?.();
    } catch (err) {
      toast.error('Failed to delete post');
    }
  };

  return (
    <div className="bulletin-post">
      <div className="bulletin-post-header">
        <img
          src={post.author?.avatar || `https://ui-avatars.com/api/?name=${post.author?.name}&background=1a237e&color=fff`}
          alt=""
          className="bulletin-avatar"
        />
        <div className="bulletin-author-info">
          <span className="bulletin-author-name">{post.author?.name}</span>
          <span className="bulletin-time">{format(new Date(post.createdAt), 'MMM d, HH:mm')}</span>
        </div>
        <span
          className="bulletin-category"
          style={{ background: categoryColors[post.category] || '#666' }}
        >
          {post.category}
        </span>
      </div>
      <div className="bulletin-post-body">
        <h3 className="bulletin-title">{post.title}</h3>
        <p className="bulletin-content">{post.content}</p>
        {post.attachments?.length > 0 && (
          <div className="bulletin-attachments">
            {post.attachments.map((att, i) => (
              <img key={i} src={att.url} alt="" className="bulletin-attachment-img" />
            ))}
          </div>
        )}
      </div>
      <div className="bulletin-post-footer">
        <button
          className={`bulletin-action ${isLiked ? 'liked' : ''}`}
          onClick={handleLike}
        >
          {isLiked ? '❤️' : '🤍'} {likes}
        </button>
        <button
          className="bulletin-action"
          onClick={() => setShowComments(!showComments)}
        >
          💬 {comments.length}
        </button>
        <button className="bulletin-action">↗️ Share</button>
        <button className="bulletin-action delete" onClick={handleDelete}>🗑️</button>
      </div>

      {showComments && (
        <div className="bulletin-comments">
          {comments.map((comment, i) => (
            <div key={comment._id || i} className="bulletin-comment">
              <img
                src={comment.author?.avatar || `https://ui-avatars.com/api/?name=${comment.author?.name}&background=666&color=fff`}
                alt=""
                className="comment-avatar"
              />
              <div className="comment-body">
                <span className="comment-author">{comment.author?.name}</span>
                <span className="comment-text">{comment.content}</span>
                <span className="comment-time">{format(new Date(comment.createdAt), 'HH:mm')}</span>
              </div>
            </div>
          ))}
          <form className="comment-form" onSubmit={handleComment}>
            <input
              type="text"
              placeholder="Write a comment..."
              value={commentText}
              onChange={(e) => setCommentText(e.target.value)}
            />
            <button type="submit">Send</button>
          </form>
        </div>
      )}
    </div>
  );
}
