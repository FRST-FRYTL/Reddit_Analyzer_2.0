#!/usr/bin/env python3
"""Test script to verify Reddit API connection."""

import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), "../backend"))

from app.utils.logging import setup_logging
from app.services.reddit_client import RedditClient


def main():
    """Test Reddit API connection."""
    # Setup logging
    setup_logging()

    try:
        print("Testing Reddit API connection...")

        # Initialize Reddit client
        client = RedditClient()

        # Test connection
        if client.test_connection():
            print("✅ Reddit API connection successful!")

            # Try to fetch a single post from a popular subreddit
            print("\nTesting data fetching...")
            posts = client.get_subreddit_posts("announcements", limit=1)

            if posts:
                post = posts[0]
                print(f"✅ Successfully fetched post: '{post['title'][:50]}...'")
                print(f"   - Author: {post['author']}")
                print(f"   - Score: {post['score']}")
                print(f"   - Comments: {post['num_comments']}")
            else:
                print("❌ No posts fetched")
                return False

        else:
            print("❌ Reddit API connection failed!")
            return False

    except Exception as e:
        print(f"❌ Error during testing: {e}")
        return False

    print("\n🎉 All tests passed!")
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
