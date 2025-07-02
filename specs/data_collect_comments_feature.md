# Data Collection: Comments Feature Specification

**Date**: 2025-07-02
**Version**: v1
**Status**: Draft

## Overview

This specification outlines the expansion of the existing `reddit-analyzer data collect` command to support downloading comments in addition to posts. Currently, the system only collects post data from subreddits. This enhancement will allow users to collect comment data, providing deeper insights into community discussions.

## Current State

### Existing Command
```bash
uv run reddit-analyzer data collect <subreddit> [OPTIONS]
```

### Current Options
- `--limit`: Number of posts to collect (default: 100)
- `--sort`: Sort method (hot/new/top/rising)
- `--time-filter`: Time filter for top posts
- `--skip-nlp`: Skip NLP analysis
- `--force`: Force re-collection

### Current Behavior
- Collects only post data (title, content, score, created_utc, etc.)
- Stores posts in the `posts` table
- Optionally runs NLP analysis on post content
- Comments table exists but is not populated

## Proposed Enhancement

### New Options
```bash
uv run reddit-analyzer data collect <subreddit> [OPTIONS]
  --with-comments               # Include comments for each post
  --comment-limit INTEGER       # Max comments per post (default: 50)
  --comment-depth INTEGER       # Max comment tree depth (default: 3)
  --comments-only              # Collect only comments from existing posts
  --min-comment-score INTEGER  # Minimum comment score to include
```

### Usage Examples
```bash
# Collect posts with top 50 comments each
uv run reddit-analyzer data collect python --limit 100 --with-comments

# Collect posts with 100 comments each, max depth 5
uv run reddit-analyzer data collect javascript --with-comments --comment-limit 100 --comment-depth 5

# Collect only comments for existing posts
uv run reddit-analyzer data collect datascience --comments-only

# Collect posts with high-quality comments only
uv run reddit-analyzer data collect machinelearning --with-comments --min-comment-score 10
```

## Implementation Details

### 1. Database Schema (Existing)
The `comments` table already exists with proper structure:
```python
class Comment(Base):
    id: str (primary key)
    post_id: str (foreign key to posts)
    parent_id: str (self-referential for nested comments)
    author: str
    body: str
    score: int
    created_utc: datetime
    edited: bool
    depth: int
    sentiment_score: float (nullable)
    sentiment_label: str (nullable)
```

### 2. Reddit API Integration
Update `RedditClient` service to handle comment collection:
```python
class RedditClient:
    def get_post_comments(
        self,
        post_id: str,
        limit: int = 50,
        depth: int = 3,
        min_score: int = None
    ) -> List[Comment]:
        """Fetch comments for a specific post."""

    def get_all_comments(
        self,
        subreddit: str,
        limit: int = 1000,
        time_filter: str = 'all'
    ) -> List[Comment]:
        """Fetch comments directly from subreddit."""
```

### 3. Collection Strategies

#### Strategy A: With Posts (--with-comments)
1. Collect posts as normal
2. For each post, fetch its comments
3. Store comments with proper parent-child relationships
4. Maintain comment tree structure

#### Strategy B: Comments Only (--comments-only)
1. Query existing posts in database
2. Fetch comments for posts without comments
3. Skip posts that already have comments (unless --force)

#### Strategy C: Direct Comment Stream
1. Use Reddit's comment stream endpoint
2. Filter by subreddit and time range
3. Match comments to existing posts or create stub posts

### 4. Performance Considerations

#### Rate Limiting
- Reddit API: 60 requests per minute
- Implement exponential backoff
- Queue comment requests to avoid hitting limits

#### Batch Processing
```python
# Process comments in batches
COMMENT_BATCH_SIZE = 10  # posts to process at once
COMMENT_REQUEST_DELAY = 1.0  # seconds between batches
```

#### Progress Tracking
```python
# Show progress for comment collection
with Progress() as progress:
    task = progress.add_task("Collecting comments...", total=num_posts)
    for post in posts:
        comments = collect_comments(post)
        progress.update(task, advance=1)
```

### 5. NLP Analysis for Comments

#### Comment-Specific Analysis
- Sentiment analysis per comment
- Parent-child sentiment comparison
- Thread-level sentiment aggregation
- Emotion detection for discussions

#### Storage Optimization
- Run NLP in batches after collection
- Store only significant results (configurable threshold)
- Cache intermediate results

### 6. CLI Output Format

#### Collection Summary
```
Posts collected: 100
Comments collected: 4,532
Average comments per post: 45.3
Maximum comment depth reached: 5
Collection time: 4m 32s

Top commented posts:
1. "Python 3.12 Released!" - 234 comments
2. "Best practices for async/await" - 189 comments
3. "New to Python, where to start?" - 156 comments
```

#### Verbose Output (--verbose)
```
Collecting post: t3_abc123 "Python 3.12 Released!"
  ├─ Fetching 234 comments (depth: 0-3)
  ├─ Processing comment tree...
  ├─ Running NLP analysis...
  └─ Saved 198 comments (36 below threshold)
```

## Migration Path

### Phase 1: Basic Implementation
- Add comment collection to existing command
- Implement --with-comments flag
- Basic progress reporting

### Phase 2: Advanced Features
- Implement --comments-only mode
- Add filtering options (min_score, depth)
- Optimize batch processing

### Phase 3: Analysis Integration
- Enhanced NLP for comment threads
- Parent-child relationship analysis
- Thread summarization

## Testing Strategy

### Unit Tests
```python
def test_comment_collection():
    # Test basic comment fetching
    # Test depth limiting
    # Test score filtering

def test_comment_tree_building():
    # Test parent-child relationships
    # Test orphaned comments handling

def test_comment_nlp_processing():
    # Test sentiment analysis
    # Test batch processing
```

### Integration Tests
- Mock Reddit API responses
- Test rate limit handling
- Test database transactions
- Verify foreign key constraints

### Performance Tests
- Measure collection time for various limits
- Test memory usage with deep comment trees
- Verify batch processing efficiency

## Error Handling

### Expected Errors
1. **Deleted/Removed Comments**: Skip and log
2. **Rate Limit Exceeded**: Exponential backoff
3. **Network Timeouts**: Retry with backoff
4. **Missing Parent Comments**: Create placeholder

### Error Reporting
```
Warning: 23 comments skipped (deleted/removed)
Warning: 5 comments have missing parents
Error: Rate limit exceeded, waiting 60s...
```

## Success Metrics

1. **Collection Completeness**: >95% of available comments collected
2. **Performance**: <5s per post with 50 comments
3. **Accuracy**: Correct parent-child relationships
4. **Reliability**: <1% failure rate due to transient errors

## Future Enhancements

1. **Live Comment Streaming**: Real-time comment monitoring
2. **Comment Thread Analysis**: Identify controversial threads
3. **User Interaction Graphs**: Map user interactions
4. **Smart Sampling**: Intelligently sample comments for large threads
5. **Incremental Updates**: Update only new comments

## Configuration

### New Settings
```python
# config.py additions
COMMENT_COLLECTION_ENABLED = True
DEFAULT_COMMENT_LIMIT = 50
DEFAULT_COMMENT_DEPTH = 3
COMMENT_SCORE_THRESHOLD = -5
COMMENT_BATCH_SIZE = 10
COMMENT_NLP_ENABLED = True
```

### CLI Defaults
Users can set defaults in `~/.reddit-analyzer/config.json`:
```json
{
  "data_collect": {
    "with_comments": true,
    "comment_limit": 100,
    "comment_depth": 5
  }
}
```

## Backwards Compatibility

- Existing `data collect` behavior unchanged without new flags
- Comments table already exists, no migration needed
- Old posts can have comments added with --comments-only
- NLP analysis can be run separately on comments

## Documentation Updates

### CLI Help Text
Update help text for the data collect command to include new options and examples.

### User Guide
Add new section on comment collection:
- When to use --with-comments vs --comments-only
- Performance implications of deep comment trees
- Best practices for large-scale collection

### API Documentation
Document new RedditClient methods and their parameters.

## Implementation Timeline

- **Week 1**: Core comment collection functionality
- **Week 2**: CLI integration and progress reporting
- **Week 3**: NLP analysis and optimization
- **Week 4**: Testing and documentation

## Review Checklist

- [ ] Database schema supports requirements
- [ ] API rate limits properly handled
- [ ] Progress reporting is informative
- [ ] Error handling is comprehensive
- [ ] Performance targets are achievable
- [ ] Backwards compatibility maintained
- [ ] Documentation is complete
