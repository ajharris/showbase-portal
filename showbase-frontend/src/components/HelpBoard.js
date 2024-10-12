// showbase-frontend/src/components/HelpBoard.js
import React, { useEffect, useState } from 'react';
import ReactMarkdown from 'react-markdown';

const HelpBoard = () => {
    const [helpContent, setHelpContent] = useState('');
    const [posts, setPosts] = useState([]);

    useEffect(() => {
        // Fetch existing help posts from the server
        fetch('/api/posts')
            .then(response => response.json())
            .then(data => setPosts(data));
    }, []);

    const handlePost = () => {
        if (helpContent.trim()) {
            fetch('/api/posts', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ content: helpContent })
            })
            .then(response => response.json())
            .then(newPost => {
                setPosts([...posts, { id: newPost.id, content: helpContent }]);
                setHelpContent('');
            });
        }
    };

    return (
        <div>
            <h2>Help Bulletin Board</h2>
            <textarea
                rows="5"
                cols="50"
                value={helpContent}
                onChange={(e) => setHelpContent(e.target.value)}
                placeholder="Write your question or answer here..."
            />
            <button onClick={handlePost}>Post</button>
            <div>
                {posts.map((post) => (
                    <div key={post.id} className="post">
                        <ReactMarkdown>{post.content}</ReactMarkdown>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default HelpBoard;
