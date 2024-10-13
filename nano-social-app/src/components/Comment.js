// src/components/Comment.js
import React from 'react';

function Comment({ comment }) {
  return (
    <div className="comment">
      <p>{comment.text}</p>
      {/* Add nested comments or reply functionality */}
    </div>
  );
}

export default Comment;
