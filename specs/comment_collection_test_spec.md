# Comment Collection Feature Test Specification

**Date**: 2025-07-02
**Version**: v1
**Feature**: Data Collection with Comments Support

## Overview

This test specification outlines the comprehensive testing strategy for the new comment collection feature added to the `reddit-analyzer data collect` command. The tests ensure correct functionality, error handling, and performance of comment collection across various scenarios.

## Test Categories

### 1. Unit Tests - RedditClient Service

#### Test File: `test_reddit_client_comments.py`

##### 1.1 Basic Comment Collection
```python
def test_get_post_comments_basic():
    """Test basic comment fetching for a post."""
    # Mock PRAW submission with comments
    # Verify correct comment data extraction
    # Check depth limiting works

def test_get_post_comments_with_filters():
    """Test comment fetching with min_score filter."""
    # Mock comments with various scores
    # Apply min_score filter
    # Verify only high-score comments returned

def test_get_post_comments_nested():
    """Test nested comment tree handling."""
    # Create mock comment tree (3 levels deep)
    # Verify depth parameter respected
    # Check parent-child relationships preserved
```

##### 1.2 Edge Cases
```python
def test_get_post_comments_deleted():
    """Test handling of deleted comments."""
    # Mock deleted comments ([deleted] author/body)
    # Verify proper handling

def test_get_post_comments_no_replies():
    """Test posts with no comments."""
    # Mock post with empty comments
    # Verify returns empty list

def test_get_post_comments_max_depth_exceeded():
    """Test very deep comment threads."""
    # Create 10-level deep comment tree
    # Set depth=3
    # Verify only 3 levels returned
```

##### 1.3 Direct Comment Stream
```python
def test_get_all_comments():
    """Test direct subreddit comment fetching."""
    # Mock subreddit.comments() stream
    # Verify comment data extraction
    # Check limit parameter works

def test_get_all_comments_error_handling():
    """Test error handling in comment stream."""
    # Mock API errors
    # Verify graceful error handling
```

### 2. Integration Tests - CLI Commands

#### Test File: `test_phase4e_cli_comments.py`

##### 2.1 Basic CLI Command Tests
```python
def test_collect_with_comments():
    """Test data collect with --with-comments flag."""
    # Run: reddit-analyzer data collect python --limit 5 --with-comments
    # Verify posts collected
    # Verify comments collected for each post
    # Check database contains comments

def test_collect_comments_only():
    """Test --comments-only mode."""
    # First collect some posts
    # Run: reddit-analyzer data collect python --comments-only
    # Verify no new posts collected
    # Verify comments added to existing posts

def test_comment_limit_option():
    """Test --comment-limit parameter."""
    # Run with --comment-limit 10
    # Verify max 10 comments per post

def test_comment_depth_option():
    """Test --comment-depth parameter."""
    # Run with --comment-depth 2
    # Verify no comments deeper than level 2
```

##### 2.2 Filter Tests
```python
def test_min_comment_score_filter():
    """Test --min-comment-score filter."""
    # Run with --min-comment-score 5
    # Verify only comments with score >= 5 collected

def test_multiple_options_combined():
    """Test combining multiple comment options."""
    # Run with all options:
    # --with-comments --comment-limit 20 --comment-depth 2 --min-comment-score 3
    # Verify all constraints respected
```

##### 2.3 Error Handling
```python
def test_conflicting_options():
    """Test --with-comments and --comments-only together."""
    # Run with both flags
    # Verify error message
    # Verify exit code 1

def test_comments_only_no_posts():
    """Test --comments-only when no posts exist."""
    # Run on empty subreddit
    # Verify appropriate message
    # Verify no errors
```

### 3. Database Tests

#### Test File: `test_comment_persistence.py`

##### 3.1 Comment Storage
```python
def test_comment_model_creation():
    """Test Comment model creation and relationships."""
    # Create post
    # Create comments with parent-child relationships
    # Verify foreign keys work
    # Test cascade deletion

def test_comment_user_association():
    """Test comment author relationships."""
    # Create users
    # Create comments by users
    # Verify user-comment relationships
```

##### 3.2 NLP Integration
```python
def test_comment_nlp_analysis():
    """Test NLP analysis on comments."""
    # Collect comments
    # Verify TextAnalysis created for comments
    # Check sentiment scores stored
    # Verify comment_id foreign key

def test_skip_nlp_for_comments():
    """Test --skip-nlp works with comments."""
    # Collect with --skip-nlp
    # Verify no TextAnalysis for comments
```

### 4. Performance Tests

#### Test File: `test_comment_collection_performance.py`

##### 4.1 Batch Processing
```python
def test_large_comment_collection():
    """Test collecting many comments efficiently."""
    # Mock 100 posts with 50 comments each
    # Measure collection time
    # Verify < 5s per post target

def test_memory_usage():
    """Test memory usage with deep comment trees."""
    # Create very deep nested comments
    # Monitor memory usage
    # Verify no memory leaks
```

##### 4.2 Rate Limiting
```python
def test_rate_limit_handling():
    """Test Reddit API rate limit handling."""
    # Mock rate limit response
    # Verify exponential backoff
    # Check collection resumes after wait
```

### 5. Real Data Tests

#### Test File: `test_phase4e_real_data_comments.py`

##### 5.1 Live Reddit Tests (if credentials available)
```python
@pytest.mark.skipif(not has_reddit_creds(), reason="No Reddit credentials")
def test_real_comment_collection():
    """Test with real Reddit data."""
    # Collect from small subreddit
    # Verify actual comments retrieved
    # Check data integrity

def test_real_nested_comments():
    """Test real nested comment threads."""
    # Find post with deep discussions
    # Collect with various depth limits
    # Verify tree structure preserved
```

## Test Data Requirements

### Mock Data Structure
```python
# Mock post with comments
mock_post = {
    "id": "test123",
    "title": "Test Post",
    "num_comments": 25,
    "comments": [
        {
            "id": "c1",
            "body": "Top level comment",
            "score": 10,
            "replies": [
                {
                    "id": "c2",
                    "body": "Reply to c1",
                    "score": 5,
                    "replies": [...]
                }
            ]
        }
    ]
}
```

### Database Fixtures
```python
@pytest.fixture
def post_with_comments(db_session):
    """Create post with comment tree."""
    post = Post(id="p1", title="Test Post")
    c1 = Comment(id="c1", post_id="p1", body="Comment 1")
    c2 = Comment(id="c2", post_id="p1", parent_id="c1", body="Reply")
    db_session.add_all([post, c1, c2])
    db_session.commit()
    return post
```

## Expected Outputs

### CLI Output Examples

#### Successful Collection
```
🚀 Starting data collection from r/python (posts with comments)
[####################################]  100%  Collecting from r/python...
✅ Collected 10 new posts from r/python

💬 Collecting comments...
[####################################]  100%  Collecting comments...
✅ Collected 234 new comments

🧠 Processing NLP analysis for 234 comments...
[####################################]  100%  Analyzing comment sentiment...
✅ Completed NLP analysis for 230 comments
```

#### Comments Only Mode
```
🚀 Starting data collection from r/python (comments only)
💬 Collecting comments...
[####################################]  100%  Collecting comments...
✅ Collected 567 new comments
```

## Error Scenarios

### 1. API Errors
- Rate limiting (429 status)
- Authentication failures
- Network timeouts
- Suspended/private subreddits

### 2. Data Errors
- Malformed comment data
- Missing parent comments
- Circular references
- Unicode/encoding issues

### 3. Database Errors
- Foreign key violations
- Duplicate key errors
- Transaction failures
- Connection pool exhaustion

## Performance Targets

1. **Collection Speed**: < 5 seconds per post with 50 comments
2. **Memory Usage**: < 500MB for 1000 comments
3. **Database Writes**: Batch inserts for efficiency
4. **API Calls**: Respect Reddit's 60 req/min limit

## Test Execution Plan

### Phase 1: Unit Tests
1. Run RedditClient tests in isolation
2. Mock all external dependencies
3. Verify 100% code coverage for new methods

### Phase 2: Integration Tests
1. Use test database
2. Mock Reddit API responses
3. Test all CLI option combinations

### Phase 3: Performance Tests
1. Use larger datasets
2. Profile memory and CPU usage
3. Identify bottlenecks

### Phase 4: Real Data Tests (Optional)
1. Use test Reddit account
2. Small-scale live testing
3. Verify against actual Reddit data

## Success Criteria

1. **Functionality**: All test cases pass
2. **Coverage**: > 90% code coverage for new code
3. **Performance**: Meets all performance targets
4. **Reliability**: No flaky tests
5. **Documentation**: All tests well-documented

## Test Report Format

```markdown
# Comment Collection Test Report

**Date**: YYYY-MM-DD
**Version**: vX
**Test Suite**: Phase 4E - Comment Collection

## Summary
- Total Tests: XX
- Passed: XX
- Failed: XX
- Skipped: XX
- Coverage: XX%

## Test Results
[Detailed results by category]

## Performance Metrics
[Collection times, memory usage]

## Issues Found
[List any bugs discovered]

## Recommendations
[Next steps and improvements]
```
