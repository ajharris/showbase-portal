import React, { useState } from 'react';

const HelpBoard = () => {
  const [subject, setSubject] = useState('');
  const [markdown, setMarkdown] = useState('');
  const [loading, setLoading] = useState(false); // Track loading state
  const [error, setError] = useState(''); // Track errors

  const handleSubjectChange = (event) => {
    setSubject(event.target.value);
  };

  const handleMarkdownChange = (event) => {
    setMarkdown(event.target.value);
  };

  const handleSubmit = async () => {
    if (!subject || !markdown) {
      alert('Please provide both a subject and content.');
      return;
    }

    setLoading(true); // Start loading
    setError(''); // Clear previous error

    try {
      const response = await fetch('/help/submit-ticket', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': window.csrf_token, // Ensure CSRF token is included
        },
        body: JSON.stringify({ subject, markdown }),
      });

      const data = await response.json();

      if (response.ok) {
        alert(data.status || 'Help ticket submitted successfully!');
        setSubject('');
        setMarkdown('');
      } else {
        throw new Error(data.error || 'Failed to submit the help ticket.');
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false); // Stop loading
    }
  };

  return (
    <div>
      <h2>Help Bulletin Board</h2>

      <input
        type="text"
        className="input"
        value={subject}
        onChange={handleSubjectChange}
        placeholder="Enter the subject of your ticket"
        style={{ width: '50%', marginBottom: '10px' }}
      />

      <textarea
        className="textarea"
        rows="10"
        cols="50"
        value={markdown}
        onChange={handleMarkdownChange}
        placeholder="Enter your question/problem here (Markdown compatible)"
      />

      <div>
        <button
          className="button"
          onClick={handleSubmit}
          disabled={loading} // Disable button while loading
        >
          {loading ? 'Submitting...' : 'Submit Help Ticket'}
        </button>
      </div>

      {error && <p style={{ color: 'red' }}>{error}</p>} {/* Display error message */}
    </div>
  );
};

export default HelpBoard;
