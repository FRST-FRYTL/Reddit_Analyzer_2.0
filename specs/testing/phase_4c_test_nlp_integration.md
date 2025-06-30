# Phase 4C NLP Integration Test Specification

## Overview
This document provides comprehensive test specifications for the NLP (Natural Language Processing) integration in the Reddit Analyzer CLI application. Tests cover sentiment analysis, topic modeling, keyword extraction, and emotion detection functionality.

## Test Environment Setup

### Prerequisites
- [ ] All Phase 4B prerequisites completed
- [ ] NLP models downloaded (VADER, TextBlob, Transformers)
- [ ] Sufficient disk space for model storage (~2GB)
- [ ] Test database with sample Reddit data
- [ ] Python packages: `transformers`, `textblob`, `vaderSentiment`

### NLP Model Initialization
```bash
# Download required models
python -c "import nltk; nltk.download('vader_lexicon')"
python -c "from textblob import TextBlob; TextBlob('test').sentiment"
python -c "from transformers import pipeline; pipeline('sentiment-analysis')"
```

### Test Data Preparation
```bash
# Collect sample data for testing
uv run reddit-analyzer auth login --username admin_test --password admin123
uv run reddit-analyzer data collect --subreddit python --limit 50
uv run reddit-analyzer data collect --subreddit javascript --limit 50
uv run reddit-analyzer data collect --subreddit datascience --limit 50
```

## NLP Service Layer Tests

### 1. NLP Service Initialization

#### 1.1 Service Creation
```python
from reddit_analyzer.services.nlp_service import NLPService

# Test initialization
nlp_service = NLPService()
assert nlp_service is not None
assert nlp_service.sentiment_analyzer is not None
assert nlp_service.topic_modeler is not None
assert nlp_service.feature_extractor is not None
```

#### 1.2 Model Caching
```python
# First initialization should load models
nlp_service1 = NLPService()
load_time1 = nlp_service1.initialization_time

# Second initialization should use cached models
nlp_service2 = NLPService()
load_time2 = nlp_service2.initialization_time

assert load_time2 < load_time1 * 0.1  # Should be much faster
```

### 2. Text Analysis Processing

#### 2.1 Single Post Analysis
```python
# Test analyzing a single post
post_text = "Python is amazing! I love using it for data science."
result = nlp_service.analyze_text(post_text)

assert 'sentiment' in result
assert 'topics' in result
assert 'keywords' in result
assert 'emotions' in result
assert result['sentiment']['compound'] > 0.5  # Positive sentiment
```

#### 2.2 Batch Processing
```python
# Test batch analysis
posts = [
    "Python is great for machine learning",
    "JavaScript frameworks are getting complex",
    "Data visualization is important"
]
results = nlp_service.analyze_batch(posts)

assert len(results) == 3
assert all('sentiment' in r for r in results)
```

## CLI Command Tests

### 3. Enhanced Data Collection with NLP

#### 3.1 Collection with NLP (Default)
```bash
uv run reddit-analyzer data collect --subreddit python --limit 10
```
**Expected Output**:
- Progress bar for data collection
- "Processing NLP analysis..." message
- Progress bar for NLP processing
- "Collected 10 posts with NLP analysis"
- Exit code: 0

**Database Verification**:
```sql
-- Verify TextAnalysis records created
SELECT COUNT(*) FROM posts p
JOIN text_analyses ta ON p.id = ta.post_id
WHERE p.created_at > NOW() - INTERVAL '5 minutes';
-- Should return 10
```

#### 3.2 Collection without NLP
```bash
uv run reddit-analyzer data collect --subreddit python --limit 10 --skip-nlp
```
**Expected Output**:
- Progress bar for data collection
- "Collected 10 posts (NLP skipped)"
- No NLP processing messages
- Exit code: 0

### 4. New NLP Command Group

#### 4.1 NLP Analyze Command
```bash
# Analyze posts without existing NLP data
uv run reddit-analyzer nlp analyze --subreddit python --limit 20
```
**Expected Output**:
- "Found X posts without NLP analysis"
- Progress bar showing analysis
- "Successfully analyzed X posts"
- Exit code: 0

**With Reanalyze Flag**:
```bash
uv run reddit-analyzer nlp analyze --subreddit python --reanalyze --limit 10
```
**Expected Output**:
- "Re-analyzing 10 posts"
- Progress updates
- "Successfully re-analyzed 10 posts"

#### 4.2 NLP Topics Command
```bash
uv run reddit-analyzer nlp topics --subreddit python --num-topics 5
```
**Expected Output**:
```
Topic Analysis for r/python
═══════════════════════════

Topic 1: Machine Learning
- Keywords: learning, model, data, neural, tensorflow
- Post count: 15
- Sample posts: [list of titles]

Topic 2: Web Development
- Keywords: django, flask, api, web, server
- Post count: 12
- Sample posts: [list of titles]

[... more topics ...]
```
Exit code: 0

#### 4.3 NLP Keywords Command
```bash
uv run reddit-analyzer nlp keywords --subreddit python --top-n 20
```
**Expected Output**:
```
Top Keywords in r/python
═══════════════════════

1. python      (450 occurrences)
2. code        (320 occurrences)
3. learning    (285 occurrences)
4. data        (270 occurrences)
5. function    (245 occurrences)
[... more keywords ...]
```
Exit code: 0

#### 4.4 NLP Emotions Command
```bash
# For specific post
uv run reddit-analyzer nlp emotions --post-id abc123
```
**Expected Output**:
```
Emotion Analysis
════════════════

Post: "I finally understood decorators!"

Emotions:
- Joy:       85%
- Surprise:  45%
- Sadness:   5%
- Anger:     2%
- Fear:      3%

Dominant emotion: Joy
```

```bash
# For subreddit summary
uv run reddit-analyzer nlp emotions --subreddit python
```
**Expected Output**:
```
Emotion Summary for r/python
═══════════════════════════

Overall Emotion Distribution:
- Joy:       42%
- Surprise:  18%
- Sadness:   15%
- Anger:     12%
- Fear:      13%

Most joyful posts: [list]
Most surprising posts: [list]
```

#### 4.5 NLP Export Command
```bash
# CSV Export
uv run reddit-analyzer nlp export --subreddit python --format csv --output nlp_analysis.csv
```
**Expected Output**:
- "Exporting NLP data for r/python"
- Progress bar
- "Exported X records to nlp_analysis.csv"
- Exit code: 0

**CSV File Structure**:
```csv
post_id,title,sentiment_compound,sentiment_label,dominant_topic,keywords,emotions
abc123,"Python tips",0.8,positive,tutorials,"python,tips,learning","joy:0.7,surprise:0.3"
```

```bash
# JSON Export
uv run reddit-analyzer nlp export --subreddit python --format json --output nlp_analysis.json
```
**Expected Output**:
- Valid JSON file with nested structure
- Includes all NLP analysis fields

### 5. Enhanced Visualization Commands

#### 5.1 Real Sentiment Visualization
```bash
uv run reddit-analyzer viz sentiment python
```
**Expected Output**:
```
Sentiment Analysis for r/python
══════════════════════════════

Sentiment Distribution:

Positive  ████████████████████ 65%
Neutral   ████████ 25%
Negative  ███ 10%

Average Sentiment Score: 0.42 (Positive)

Most Positive Posts:
1. "Python changed my life!" (0.95)
2. "Amazing community support" (0.92)

Most Negative Posts:
1. "Frustrated with dependencies" (-0.78)
2. "Why is packaging so hard?" (-0.65)

Confidence Scores:
- High confidence: 78%
- Medium confidence: 18%
- Low confidence: 4%
```
Exit code: 0

#### 5.2 Sentiment Trends Over Time
```bash
uv run reddit-analyzer viz sentiment python --trend --days 7
```
**Expected Output**:
- ASCII line chart showing sentiment over 7 days
- Daily average sentiment scores
- Trend direction indicator

### 6. Performance Tests

#### 6.1 NLP Processing Speed
```bash
# Time NLP analysis for different batch sizes
time uv run reddit-analyzer nlp analyze --subreddit python --limit 10
time uv run reddit-analyzer nlp analyze --subreddit python --limit 100
time uv run reddit-analyzer nlp analyze --subreddit python --limit 1000
```
**Expected Performance**:
- 10 posts: < 15 seconds
- 100 posts: < 2 minutes
- 1000 posts: < 15 minutes
- Linear or better scaling

#### 6.2 Memory Usage
```python
# Monitor memory during batch processing
import psutil
import os

process = psutil.Process(os.getpid())
initial_memory = process.memory_info().rss / 1024 / 1024  # MB

# Process large batch
nlp_service.analyze_batch(posts * 100)

peak_memory = process.memory_info().rss / 1024 / 1024  # MB
memory_increase = peak_memory - initial_memory

assert memory_increase < 1000  # Should not exceed 1GB increase
```

### 7. Error Handling Tests

#### 7.1 Empty Text Handling
```bash
# Post with empty text
uv run reddit-analyzer nlp analyze --post-id empty_post_id
```
**Expected Output**:
- "Skipping post with empty text"
- Continues processing other posts
- Exit code: 0

#### 7.2 Model Loading Failures
```bash
# Simulate missing model files
rm -rf ~/.cache/huggingface/hub/*
uv run reddit-analyzer nlp analyze --subreddit python --limit 1
```
**Expected Output**:
- "Downloading required models..."
- Progress bar for download
- Successful completion after download

#### 7.3 API Rate Limits
```bash
# Process large batch that might hit transformer API limits
uv run reddit-analyzer nlp analyze --subreddit all --limit 10000
```
**Expected Output**:
- Handles rate limiting gracefully
- Implements backoff/retry logic
- Shows progress with estimated time

### 8. Integration Tests

#### 8.1 End-to-End Workflow
```bash
# Complete workflow from collection to visualization
uv run reddit-analyzer data collect --subreddit MachineLearning --limit 50
uv run reddit-analyzer nlp analyze --subreddit MachineLearning
uv run reddit-analyzer nlp topics --subreddit MachineLearning --num-topics 3
uv run reddit-analyzer viz sentiment MachineLearning
uv run reddit-analyzer report daily --subreddit MachineLearning
```
**Expected**:
- All commands complete successfully
- Data flows through entire pipeline
- Reports include NLP insights

#### 8.2 Multi-Model Consistency
```python
# Verify different models give consistent results
post_text = "This is an amazing Python library!"

vader_result = nlp_service.sentiment_analyzer.analyze_vader(post_text)
textblob_result = nlp_service.sentiment_analyzer.analyze_textblob(post_text)
transformer_result = nlp_service.sentiment_analyzer.analyze_transformer(post_text)

# All should be positive
assert all(r['label'] == 'positive' for r in [vader_result, textblob_result, transformer_result])
```

### 9. Database Integration Tests

#### 9.1 TextAnalysis Table
```sql
-- Verify schema
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'text_analyses';

-- Should include:
-- sentiment_score, sentiment_label, confidence_score
-- topics, keywords, emotions (JSON fields)
-- processing_time, model_versions
```

#### 9.2 Relationship Integrity
```sql
-- Verify all analyses have valid post references
SELECT COUNT(*)
FROM text_analyses ta
LEFT JOIN posts p ON ta.post_id = p.id
WHERE p.id IS NULL;
-- Should return 0
```

### 10. Configuration Tests

#### 10.1 NLP Settings
```bash
# Test with custom config
export NLP_ENABLE_TRANSFORMERS=false
uv run reddit-analyzer nlp analyze --subreddit python --limit 5
```
**Expected**:
- Uses only VADER and TextBlob
- Completes successfully
- Notes in output that transformers are disabled

#### 10.2 Model Selection
```bash
# Use specific transformer model
uv run reddit-analyzer nlp analyze --model distilbert-base-uncased --limit 5
```
**Expected**:
- Uses specified model
- Shows model name in output

## Test Execution Plan

### Phase 1: Unit Tests (1 hour)
1. Test NLP service initialization
2. Test individual analyzers
3. Test model caching
4. Test error handling

### Phase 2: CLI Integration (2 hours)
1. Test enhanced data collection
2. Test new NLP commands
3. Test visualization updates
4. Test export functionality

### Phase 3: Performance Testing (1 hour)
1. Benchmark processing speeds
2. Test memory usage
3. Test batch size limits
4. Test concurrent processing

### Phase 4: End-to-End Testing (1 hour)
1. Complete workflow tests
2. Multi-subreddit analysis
3. Report generation with NLP
4. Export and verification

## Success Criteria

- [ ] All NLP models load successfully
- [ ] Sentiment analysis accuracy > 80% on test set
- [ ] Topic modeling produces coherent topics
- [ ] Processing speed < 1 second per post
- [ ] Memory usage stays within limits
- [ ] All CLI commands execute without errors
- [ ] Export files contain valid NLP data
- [ ] Visualizations show real sentiment data
- [ ] Error handling prevents crashes
- [ ] Database integrity maintained

## Test Data Verification Script

```python
#!/usr/bin/env python3
"""Verify NLP integration is working correctly"""

from reddit_analyzer.models import Post, TextAnalysis
from reddit_analyzer.database import SessionLocal

def verify_nlp_integration():
    """Check that NLP data is properly stored"""
    db = SessionLocal()

    # Count posts with NLP analysis
    total_posts = db.query(Post).count()
    analyzed_posts = db.query(Post).join(TextAnalysis).count()

    print(f"Total posts: {total_posts}")
    print(f"Analyzed posts: {analyzed_posts}")
    print(f"Coverage: {analyzed_posts/total_posts*100:.1f}%")

    # Sample analysis quality
    sample = db.query(TextAnalysis).limit(5).all()
    for analysis in sample:
        print(f"\nPost: {analysis.post.title[:50]}...")
        print(f"Sentiment: {analysis.sentiment_label} ({analysis.sentiment_score:.2f})")
        print(f"Keywords: {', '.join(analysis.keywords[:5])}")
        print(f"Processing time: {analysis.processing_time:.2f}s")

    db.close()

if __name__ == "__main__":
    verify_nlp_integration()
```

## Troubleshooting Guide

### Common Issues

1. **Model Download Failures**
   - Check internet connection
   - Verify disk space (need ~2GB)
   - Try manual model download
   - Check Hugging Face availability

2. **Slow Processing**
   - Ensure models are cached
   - Check CPU/GPU availability
   - Reduce batch size
   - Disable transformer models for speed

3. **Memory Errors**
   - Reduce batch size
   - Process in smaller chunks
   - Increase system RAM
   - Use lighter models

4. **Inconsistent Results**
   - Verify text preprocessing
   - Check model versions
   - Ensure consistent tokenization
   - Review confidence thresholds

## Performance Benchmarks

### Expected Processing Times
- VADER: ~0.01s per post
- TextBlob: ~0.05s per post
- Transformers: ~0.5s per post (CPU), ~0.1s (GPU)
- Topic Modeling: ~5s per 100 posts
- Keyword Extraction: ~0.1s per post

### Resource Usage
- Memory: 500MB-2GB depending on models
- CPU: 1-4 cores utilized
- Disk: 2GB for model storage
- Network: Initial model download only
