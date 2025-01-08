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
    maxPostAge: ''
  });
  const [message, setMessage] = useState('');

  const handleSearch = async () => {
    if (!question.trim()) {
      setMessage('Please enter a question.');
      return;
    }

    setMessage('Searching...');
    try {
      const response = await axios.post('http://localhost:5000/api/search', { question });
      setPosts(response.data.posts);
      setMessage('');
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

    return true;
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

      {message && <p className="message">{message}</p>}

      <div className="posts-container">
        {posts.filter(applyFilters).map((post) => (
          <div key={post.id} className="post">
            <h3><a href={`https://reddit.com${post.permalink}`} target="_blank" rel="noopener noreferrer">{post.title}</a></h3>
            <p><strong>Subreddit:</strong> {post.subreddit}</p>
            <p><strong>Upvotes:</strong> {post.score} | <strong>Comments:</strong> {post.num_comments}</p>
            <button onClick={() => handleSave(post)}>Save Post</button>
          </div>
        ))}
      </div>
    </div>
  );
}

export default App;
