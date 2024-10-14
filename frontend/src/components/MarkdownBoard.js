import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown'; // You'll need this package to render markdown

const MarkdownBoard = () => {
  const [markdown, setMarkdown] = useState('');

  const handleInputChange = (event) => {
    setMarkdown(event.target.value);
  };

  return (
    <div>
      <h3>Markdown Editor</h3>
      <textarea
        rows="10"
        cols="50"
        value={markdown}
        onChange={handleInputChange}
        placeholder="Type your markdown here..."
      />
      <h3>Preview</h3>
      <div className="markdown-preview">
        <ReactMarkdown>{markdown}</ReactMarkdown>
      </div>
    </div>
  );
};

export default MarkdownBoard;
