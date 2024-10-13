// src/components/Post.js
import React from 'react';

function Post({ content }) {
  return (
    <div className="post">
      <h3>{content.title}</h3>
      <p>{content.body}</p>
      {/* Add buttons for comments and reactions */}
    </div>
  );
}

export default Post;
