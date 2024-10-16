import React, { useState } from 'react';

const HelpBoard = () => {
  const [subject, setSubject] = useState('');
  const [markdown, setMarkdown] = useState('');

  const handleSubjectChange = (event) => {
    setSubject(event.target.value);
  };

  const handleMarkdownChange = (event) => {
    setMarkdown(event.target.value);
  };

  const handleSubmit = async () => {
    const response = await fetch('/help/submit-ticket', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': window.csrf_token,
      },
      body: JSON.stringify({ subject, markdown }),
    });

    if (response.ok) {
      alert('Help ticket submitted successfully!');
      setSubject(''); // Clear the subject field
      setMarkdown(''); // Clear the markdown field
    } else {
      alert('Failed to submit the help ticket.');
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
        <button className="button" onClick={handleSubmit}>
          Submit Help Ticket
        </button>
      </div>
    </div>
  );
};

export default HelpBoard;
