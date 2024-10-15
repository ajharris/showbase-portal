import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';

const MarkdownBoard = () => {
  const [markdown, setMarkdown] = useState('');

  const handleInputChange = (event) => {
    setMarkdown(event.target.value);
  };

  return (
    <div>
      <h2>Markdown Board</h2>
      <textarea
        rows="10"
        cols="50"
        value={markdown}
        onChange={handleInputChange}
        placeholder="Enter Markdown here"
      />
      <div>
        <h3>Rendered Markdown:</h3>
        <ReactMarkdown>{markdown}</ReactMarkdown>
      </div>
    </div>
  );
};

export default MarkdownBoard;
