// frontend/src/App.js

import React, { useState } from 'react';
import axios from 'axios';
import './App.css';

function App() {
  const [question, setQuestion] = useState('');
  const [posts, setPosts] = useState([]);
  const [filters, setFilters] = useState({
    minUpvotes: '',
    minComments: '',
    maxPostAge: '' // in days
  });
  const [message, setMessage] = useState('');
  const [selectedSubreddits, setSelectedSubreddits] = useState([]);
  const [availableSubreddits, setAvailableSubreddits] = useState([]);
  const [comments, setComments] = useState([]);
  const [view, setView] = useState('posts'); // 'posts' or 'comments'

  const handleSearch = async () => {
    if (!question.trim()) {
      setMessage('Please enter a question.');
      return;
    }

    setMessage('Searching...');
    try {
      const response = await axios.post('http://localhost:5000/api/search', { question });
      setPosts(response.data.posts);
      setAvailableSubreddits(response.data.subreddits);
      setSelectedSubreddits([]); // Reset any previous subreddit selections
      setMessage('');
      setView('posts'); // Ensure we're viewing posts after search
      setComments([]); // Reset comments
    } catch (error) {
      console.error(error);
      setMessage('Error fetching posts.');
    }
  };

  const handleSave = async (post) => {
    try {
      const response = await axios.post('http://localhost:5000/api/save', post);
      setMessage(response.data.message || 'Post saved successfully.');
    } catch (error) {
      console.error(error);
      setMessage('Error saving post.');
    }
  };

  const handleFilterChange = (e) => {
    setFilters({
      ...filters,
      [e.target.name]: e.target.value
    });
  };

  const applyFilters = (post) => {
    const { minUpvotes, minComments, maxPostAge } = filters;
    const postAgeDays = (Date.now() / 1000 - post.created_utc) / 86400;

    if (minUpvotes && post.score < parseInt(minUpvotes)) return false;
    if (minComments && post.num_comments < parseInt(minComments)) return false;
    if (maxPostAge && postAgeDays > parseInt(maxPostAge)) return false;
    if (selectedSubreddits.length > 0 && !selectedSubreddits.includes(post.subreddit)) return false;

    return true;
  };

  const fetchComments = async (permalink) => {
    setMessage('Fetching comments...');
    try {
      const response = await axios.post('http://localhost:5000/api/comments', { permalink });
      setComments(response.data.comments);
      setView('comments');
      setMessage('');
    } catch (error) {
      console.error(error);
      setMessage('Error fetching comments.');
    }
  };

  return (
    <div className="App">
      <h1>Reddit Content Browser</h1>
      <div className="search-container">
        <input
          type="text"
          placeholder="Ask a question..."
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
        />
        <button onClick={handleSearch}>Search</button>
      </div>

      <div className="filters-container">
        <h3>Filters</h3>
        <div className="filters">
          <div>
            <label>Minimum Upvotes:</label>
            <input
              type="number"
              name="minUpvotes"
              value={filters.minUpvotes}
              onChange={handleFilterChange}
              placeholder="e.g., 100"
            />
          </div>
          <div>
            <label>Minimum Comments:</label>
            <input
              type="number"
              name="minComments"
              value={filters.minComments}
              onChange={handleFilterChange}
              placeholder="e.g., 50"
            />
          </div>
          <div>
            <label>Maximum Post Age (days):</label>
            <input
              type="number"
              name="maxPostAge"
              value={filters.maxPostAge}
              onChange={handleFilterChange}
              placeholder="e.g., 7"
            />
          </div>
        </div>
      </div>

      <div className="subreddits-container">
        <h3>Select Subreddits:</h3>
        <select
          multiple
          value={selectedSubreddits}
          onChange={(e) => {
            const options = e.target.options;
            const selected = [];
            for (let i = 0; i < options.length; i++) {
              if (options[i].selected) {
                selected.push(options[i].value);
              }
            }
            setSelectedSubreddits(selected);
          }}
        >
          {availableSubreddits.map((subreddit) => (
            <option key={subreddit} value={subreddit}>
              {subreddit}
            </option>
          ))}
        </select>
        <button onClick={() => setSelectedSubreddits([])}>Reset Subreddit Filters</button>
      </div>

      <div className="view-toggle">
        <button onClick={() => setView('posts')} disabled={view === 'posts'}>
          View Posts
        </button>
        <button onClick={() => setView('comments')} disabled={view === 'comments'}>
          View Comments
        </button>
      </div>

      {message && <p className="message">{message}</p>}

      <div className="content-container">
        {view === 'posts' && (
          <div className="posts-container">
            {posts.filter(applyFilters).map((post) => (
              <div key={post.id} className="post">
                <h3>
                  <a href={`https://reddit.com${post.permalink}`} target="_blank" rel="noopener noreferrer">
                    {post.title}
                  </a>
                </h3>
                <p><strong>Subreddit:</strong> {post.subreddit}</p>
                <p><strong>Upvotes:</strong> {post.score} | <strong>Comments:</strong> {post.num_comments}</p>
                <button onClick={() => fetchComments(post.permalink)}>View Comments</button>
                <button onClick={() => handleSave(post)}>Save Post</button>
              </div>
            ))}
          </div>
        )}

        {view === 'comments' && (
          <div className="comments-container">
            <button onClick={() => setView('posts')}>Back to Posts</button>
            <h3>Comments</h3>
            {comments.length === 0 ? (
              <p>No comments available.</p>
            ) : (
              comments.map((comment) => (
                <div key={comment.id} className="comment">
                  <p><strong>{comment.author}</strong> ({comment.score} points)</p>
                  <p>{comment.body}</p>
                </div>
              ))
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
