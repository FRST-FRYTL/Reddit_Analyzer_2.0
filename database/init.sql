-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    created_utc TIMESTAMP,
    comment_karma INTEGER DEFAULT 0,
    link_karma INTEGER DEFAULT 0,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Subreddits table
CREATE TABLE subreddits (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    display_name VARCHAR(255),
    description TEXT,
    subscribers INTEGER DEFAULT 0,
    created_utc TIMESTAMP,
    is_nsfw BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Posts table
CREATE TABLE posts (
    id VARCHAR(255) PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    selftext TEXT,
    url VARCHAR(2000),
    author_id INTEGER REFERENCES users(id),
    subreddit_id INTEGER REFERENCES subreddits(id),
    score INTEGER DEFAULT 0,
    upvote_ratio FLOAT DEFAULT 0.5,
    num_comments INTEGER DEFAULT 0,
    created_utc TIMESTAMP NOT NULL,
    is_self BOOLEAN DEFAULT FALSE,
    is_nsfw BOOLEAN DEFAULT FALSE,
    is_locked BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Comments table (basic structure)
CREATE TABLE comments (
    id VARCHAR(255) PRIMARY KEY,
    post_id VARCHAR(255) REFERENCES posts(id),
    parent_id VARCHAR(255),
    author_id INTEGER REFERENCES users(id),
    body TEXT,
    score INTEGER DEFAULT 0,
    created_utc TIMESTAMP NOT NULL,
    is_deleted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add indexes for performance
CREATE INDEX idx_posts_created_utc ON posts(created_utc);
CREATE INDEX idx_posts_subreddit_id ON posts(subreddit_id);
CREATE INDEX idx_posts_author_id ON posts(author_id);
CREATE INDEX idx_comments_post_id ON comments(post_id);
CREATE INDEX idx_comments_author_id ON comments(author_id);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_subreddits_name ON subreddits(name);
