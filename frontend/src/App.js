// frontend/src/App.js

import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

function App() {
  // State variables
  const [question, setQuestion] = useState('');
  const [audiences, setAudiences] = useState([]);
  const [selectedAudience, setSelectedAudience] = useState('');
  const [posts, setPosts] = useState([]);
  const [topics, setTopics] = useState([]);
  const [selectedTopic, setSelectedTopic] = useState('');
  const [message, setMessage] = useState('');

  // New Audience states
  const [newAudienceName, setNewAudienceName] = useState('');
  const [newSubreddit, setNewSubreddit] = useState('');
  const [subreddits, setSubreddits] = useState([]);

  // Fetch existing audiences on component mount
  useEffect(() => {
    fetchAudiences();
  }, []);

  // Function to fetch audiences
  const fetchAudiences = async () => {
    try {
      const response = await axios.get('http://localhost:5000/api/audiences');
      setAudiences(response.data.audiences);
    } catch (error) {
      console.error(error);
      setMessage('Error fetching audiences.');
    }
  };

  // Function to add a subreddit to the subreddits list
  const addSubreddit = () => {
    const trimmedSub = newSubreddit.trim();
    if (trimmedSub && !subreddits.includes(trimmedSub)) {
      setSubreddits([...subreddits, trimmedSub]);
      setNewSubreddit('');
    }
  };

  // Function to remove a subreddit from the subreddits list
  const removeSubreddit = (sub) => {
    setSubreddits(subreddits.filter((s) => s !== sub));
  };

  // Function to create a new audience with subreddits
  const createAudience = async () => {
    if (!newAudienceName.trim()) {
      setMessage('Please enter a name for the audience.');
      return;
    }

    if (subreddits.length === 0) {
      setMessage('Please add at least one subreddit.');
      return;
    }

    try {
      const response = await axios.post('http://localhost:5000/api/audiences', {
        name: newAudienceName.trim(),
        subreddits: subreddits,
      });
      setMessage(response.data.message);
      setNewAudienceName('');
      setSubreddits([]);
      fetchAudiences();
    } catch (error) {
      console.error(error);
      setMessage(error.response?.data?.error || 'Error creating audience.');
    }
  };

  // Function to handle audience selection
  const handleAudienceSelect = (e) => {
    setSelectedAudience(e.target.value);
    setSelectedTopic('');
    setPosts([]);
    setTopics([]);
  };

  // Function to handle search
  const handleSearch = async () => {
    if (!question.trim() || !selectedAudience) {
      setMessage('Please enter a question and select an audience.');
      return;
    }

    setMessage('Searching...');
    try {
      const response = await axios.post('http://localhost:5000/api/search_audience', {
        question,
        audience: selectedAudience,
      });
      setPosts(response.data.posts);
      setTopics([]); // Clear previous topics
      setMessage('');
    } catch (error) {
      console.error(error);
      setMessage(error.response?.data?.error || 'Error fetching posts.');
    }
  };

  // Function to fetch topics
  const fetchTopics = async () => {
    if (!selectedAudience) {
      setMessage('Please select an audience first.');
      return;
    }

    setMessage('Fetching topics...');
    try {
      const response = await axios.post('http://localhost:5000/api/get_topics', {
        audience: selectedAudience,
      });
      setTopics(response.data.topics);
      setMessage('');
    } catch (error) {
      console.error(error);
      setMessage(error.response?.data?.error || 'Error fetching topics.');
    }
  };

  // Function to handle topic selection
  const handleTopicSelect = async (topic) => {
    setSelectedTopic(topic);
    setMessage('Filtering posts...');
    try {
      const response = await axios.post('http://localhost:5000/api/filter_posts', {
        topic,
        audience: selectedAudience,
      });
      setPosts(response.data.posts);
      setMessage('');
    } catch (error) {
      console.error(error);
      setMessage(error.response?.data?.error || 'Error filtering posts.');
    }
  };

  // Function to handle saving a post
  const handleSave = async (post) => {
    try {
      const response = await axios.post('http://localhost:5000/api/save', post);
      setMessage(response.data.message || 'Post saved successfully.');
    } catch (error) {
      console.error(error);
      setMessage(error.response?.data?.error || 'Error saving post.');
    }
  };

  return (
    <div className="App">
      <h1>Reddit Content Browser</h1>

      {/* Create Audience Section */}
      <div className="create-audience">
        <h2>Create Audience</h2>
        <input
          type="text"
          placeholder="Audience Name (e.g., Software Developers)"
          value={newAudienceName}
          onChange={(e) => setNewAudienceName(e.target.value)}
        />
        <div className="subreddit-input">
          <input
            type="text"
            placeholder="Subreddit Name (e.g., programming)"
            value={newSubreddit}
            onChange={(e) => setNewSubreddit(e.target.value)}
            onKeyPress={(e) => {
              if (e.key === 'Enter') addSubreddit();
            }}
          />
          <button onClick={addSubreddit}>Add Subreddit</button>
        </div>
        <div className="subreddit-list">
          {subreddits.map((sub) => (
            <span key={sub} className="subreddit-item">
              r/{sub}
              <button onClick={() => removeSubreddit(sub)}>×</button>
            </span>
          ))}
        </div>
        <button onClick={createAudience}>Create Audience</button>
      </div>

      {/* Select Audience Section */}
      <div className="select-audience">
        <h2>Select Audience</h2>
        <select value={selectedAudience} onChange={handleAudienceSelect}>
          <option value="">-- Select an Audience --</option>
          {audiences.map((audience) => (
            <option key={audience.name} value={audience.name}>
              {audience.name}
            </option>
          ))}
        </select>
      </div>

      {/* Fetch Topics Button */}
      {selectedAudience && (
        <div className="fetch-topics">
          <button onClick={fetchTopics}>Fetch Top Topics</button>
        </div>
      )}

      {/* Search Section */}
      <div className="search-container">
        <input
          type="text"
          placeholder="Search..."
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
        />
        <button onClick={handleSearch}>Search</button>
      </div>

      {/* Topics Section */}
      {topics.length > 0 && (
        <div className="topics-container">
          <h2>Top Topics</h2>
          <div className="topics-list">
            {topics.map((topic) => (
              <button key={topic} onClick={() => handleTopicSelect(topic)}>
                {topic}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Message Display */}
      {message && <p className="message">{message}</p>}

      {/* Posts Display */}
      <div className="posts-container">
        {posts.length === 0 ? (
          <p>No posts to display.</p>
        ) : (
          posts.map((post) => (
            <div key={post.id} className="post">
              <h3>
                <a href={`https://reddit.com${post.permalink}`} target="_blank" rel="noopener noreferrer">
                  {post.title}
                </a>
              </h3>
              <p><strong>Subreddit:</strong> r/{post.subreddit}</p>
              <p><strong>Upvotes:</strong> {post.score} | <strong>Comments:</strong> {post.num_comments}</p>
              <button onClick={() => handleSave(post)}>Save Post</button>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

export default App;
