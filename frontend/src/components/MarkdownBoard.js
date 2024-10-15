import React, { useState } from 'react';

const MarkdownBoard = () => {
  const [markdown, setMarkdown] = useState('');

  const handleInputChange = (event) => {
    setMarkdown(event.target.value);
  };

  const handleSubmit = async () => {
    const response = await fetch('/help/submit-ticket', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': window.csrf_token,
      },
      body: JSON.stringify({ markdown }),
    });

    if (response.ok) {
      alert('Help ticket submitted successfully!');
      setMarkdown(''); // Clear the textarea after submission
    } else {
      alert('Failed to submit the help ticket.');
    }
  };

  return (
    <div>
      <h2>Help Bulletin Board</h2>
      <textarea
        className='textarea'
        rows="10"
        cols="50"
        value={markdown}
        onChange={handleInputChange}
        placeholder="Enter your question/problem here (Markdown compatible)"
      />
      <div>
        <button className='button' onClick={handleSubmit}>Submit Help Ticket</button>
      </div>
    </div>
  );
};

export default MarkdownBoard;
