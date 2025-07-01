# Phase 4D: Political Analysis Testing Specification

## Overview

This specification outlines comprehensive testing requirements for the political analysis features implemented in Phase 4C. The testing strategy covers unit tests, integration tests, CLI command tests, and performance benchmarks for all political analysis components.

## Testing Objectives

1. **Validate Topic Detection Accuracy**: Ensure political topics are correctly identified with appropriate confidence scores
2. **Verify Multi-Dimensional Analysis**: Confirm political dimensions are analyzed accurately across all three axes
3. **Test Discussion Quality Metrics**: Validate civility, constructiveness, and diversity calculations
4. **Ensure Data Privacy**: Verify aggregate-only analysis and minimum threshold enforcement
5. **Validate CLI Commands**: Test all new CLI commands with various scenarios
6. **Performance Testing**: Ensure analysis completes within acceptable timeframes

## Test Categories

### 1. Unit Tests

#### 1.1 Topic Analyzer Tests (`tests/test_topic_analyzer.py`)

```python
class TestTopicAnalyzer:
    """Comprehensive tests for political topic analysis."""

    # Topic Detection Tests
    - test_detect_political_topics_healthcare
    - test_detect_political_topics_economy
    - test_detect_political_topics_climate
    - test_detect_political_topics_immigration
    - test_detect_political_topics_education
    - test_detect_political_topics_foreign_policy
    - test_detect_political_topics_social_issues
    - test_detect_political_topics_technology
    - test_detect_political_topics_democracy

    # Multi-Topic Detection
    - test_detect_multiple_topics
    - test_detect_overlapping_topics
    - test_topic_confidence_thresholds

    # Edge Cases
    - test_empty_text_returns_empty
    - test_short_text_handling
    - test_non_political_text
    - test_mixed_political_nonpolitical_text

    # Topic Sentiment Analysis
    - test_analyze_topic_sentiment_positive
    - test_analyze_topic_sentiment_negative
    - test_analyze_topic_sentiment_neutral
    - test_invalid_topic_sentiment
    - test_sentiment_with_no_topic_keywords

    # Discussion Quality
    - test_calculate_discussion_quality_high
    - test_calculate_discussion_quality_low
    - test_discussion_quality_with_toxic_comments
    - test_discussion_quality_empty_comments
    - test_discussion_quality_minimal_comments
```

#### 1.2 Political Dimensions Tests (`tests/test_political_dimensions_analyzer.py`)

```python
class TestPoliticalDimensionsAnalyzer:
    """Tests for multi-dimensional political analysis."""

    # Economic Dimension Tests
    - test_analyze_economic_dimension_market
    - test_analyze_economic_dimension_planned
    - test_analyze_economic_dimension_mixed
    - test_economic_confidence_scoring

    # Social Dimension Tests
    - test_analyze_social_dimension_liberty
    - test_analyze_social_dimension_authority
    - test_analyze_social_dimension_balanced
    - test_social_evidence_extraction

    # Governance Dimension Tests
    - test_analyze_governance_dimension_decentralized
    - test_analyze_governance_dimension_centralized
    - test_analyze_governance_dimension_mixed

    # Multi-Dimensional Analysis
    - test_analyze_all_dimensions_simultaneously
    - test_dimension_independence
    - test_mixed_political_positions

    # Edge Cases
    - test_empty_text_returns_empty_result
    - test_short_text_returns_empty_result
    - test_non_political_text_low_confidence

class TestPoliticalDiversityCalculation:
    """Tests for political diversity metrics."""

    - test_calculate_diversity_high
    - test_calculate_diversity_low
    - test_calculate_diversity_moderate
    - test_diversity_with_weighted_confidence
    - test_diversity_insufficient_data

class TestPoliticalClustering:
    """Tests for political group identification."""

    - test_identify_clusters_distinct_groups
    - test_identify_clusters_overlapping_groups
    - test_cluster_labeling_accuracy
    - test_cluster_size_thresholds
    - test_clustering_insufficient_data
```

### 2. Integration Tests

#### 2.1 Database Integration (`tests/integration/test_political_analysis_db.py`)

```python
class TestPoliticalAnalysisDatabase:
    """Test database operations for political analysis."""

    # Model Tests
    - test_create_subreddit_topic_profile
    - test_create_community_overlap
    - test_create_political_dimensions_analysis
    - test_create_subreddit_political_dimensions

    # Relationship Tests
    - test_subreddit_topic_profile_relationships
    - test_political_dimensions_relationships
    - test_cascade_delete_behavior

    # Query Tests
    - test_query_recent_analyses
    - test_query_by_date_range
    - test_aggregate_queries

    # Data Integrity
    - test_constraint_validation
    - test_json_field_storage
    - test_float_precision
```

#### 2.2 Service Integration (`tests/integration/test_political_services.py`)

```python
class TestPoliticalServicesIntegration:
    """Test integration between political analysis services."""

    - test_topic_analyzer_with_nlp_service
    - test_political_analyzer_with_topic_analyzer
    - test_end_to_end_analysis_pipeline
    - test_batch_analysis_performance
    - test_service_error_handling
```

### 3. CLI Command Tests

#### 3.1 Topic Analysis Commands (`tests/cli/test_analyze_commands.py`)

```python
class TestAnalyzeTopicsCommand:
    """Test 'analyze topics' CLI command."""

    - test_analyze_topics_basic
    - test_analyze_topics_with_days_option
    - test_analyze_topics_with_limit_option
    - test_analyze_topics_save_report
    - test_analyze_topics_invalid_subreddit
    - test_analyze_topics_no_data
    - test_analyze_topics_output_format

class TestAnalyzeSentimentCommand:
    """Test 'analyze sentiment' CLI command."""

    - test_analyze_sentiment_valid_topic
    - test_analyze_sentiment_invalid_topic
    - test_analyze_sentiment_with_days
    - test_analyze_sentiment_no_matches
    - test_analyze_sentiment_output_examples

class TestAnalyzeQualityCommand:
    """Test 'analyze quality' CLI command."""

    - test_analyze_quality_basic
    - test_analyze_quality_min_comments
    - test_analyze_quality_insufficient_data
    - test_analyze_quality_scoring_display

class TestAnalyzeOverlapCommand:
    """Test 'analyze overlap' CLI command."""

    - test_analyze_overlap_two_subreddits
    - test_analyze_overlap_same_subreddit_error
    - test_analyze_overlap_with_topics
    - test_analyze_overlap_no_shared_users
```

#### 3.2 Political Dimensions Commands (`tests/cli/test_political_commands.py`)

```python
class TestAnalyzeDimensionsCommand:
    """Test 'analyze dimensions' CLI command."""

    - test_analyze_dimensions_basic
    - test_analyze_dimensions_with_limit
    - test_analyze_dimensions_save_analysis
    - test_analyze_dimensions_display_format
    - test_analyze_dimensions_clustering

class TestPoliticalCompassCommand:
    """Test 'analyze political-compass' CLI command."""

    - test_political_compass_existing_analysis
    - test_political_compass_no_analysis
    - test_political_compass_visualization
    - test_political_compass_output_file

class TestPoliticalDiversityCommand:
    """Test 'analyze political-diversity' CLI command."""

    - test_political_diversity_high
    - test_political_diversity_low
    - test_political_diversity_visualization
    - test_political_diversity_clusters
```

### 4. Performance Tests

#### 4.1 Analysis Performance (`tests/performance/test_political_performance.py`)

```python
class TestPoliticalAnalysisPerformance:
    """Performance benchmarks for political analysis."""

    @pytest.mark.benchmark
    def test_topic_detection_performance:
        """Topic detection should complete within 100ms per post."""

    @pytest.mark.benchmark
    def test_dimension_analysis_performance:
        """Dimension analysis should complete within 200ms per post."""

    @pytest.mark.benchmark
    def test_batch_analysis_performance:
        """Batch of 1000 posts should complete within 30 seconds."""

    @pytest.mark.benchmark
    def test_diversity_calculation_performance:
        """Diversity calculation for 10,000 items within 5 seconds."""
```

### 5. Privacy and Ethics Tests

#### 5.1 Privacy Enforcement (`tests/test_privacy_enforcement.py`)

```python
class TestPrivacyEnforcement:
    """Test privacy and ethical constraints."""

    - test_minimum_user_threshold_enforced
    - test_no_individual_scores_stored
    - test_aggregate_only_analysis
    - test_time_window_enforcement
    - test_opted_out_subreddit_exclusion
    - test_private_subreddit_exclusion
    - test_sensitive_subreddit_types_excluded
```

### 6. End-to-End Tests

#### 6.1 Complete Workflow Tests (`tests/e2e/test_political_workflows.py`)

```python
class TestPoliticalAnalysisWorkflows:
    """End-to-end workflow tests."""

    def test_complete_subreddit_analysis_workflow:
        """Test complete analysis from data collection to reporting."""
        # 1. Collect subreddit data
        # 2. Run topic analysis
        # 3. Run political dimensions analysis
        # 4. Calculate diversity metrics
        # 5. Generate reports
        # 6. Verify all outputs

    def test_comparative_analysis_workflow:
        """Test comparing multiple subreddits."""
        # 1. Analyze multiple subreddits
        # 2. Compare political dimensions
        # 3. Analyze community overlap
        # 4. Generate comparative report

    def test_temporal_analysis_workflow:
        """Test analysis over time periods."""
        # 1. Analyze same subreddit over different periods
        # 2. Track political drift
        # 3. Identify trend changes
```

## Test Data Requirements

### 1. Fixtures

```python
# tests/fixtures/political_fixtures.py

@pytest.fixture
def sample_political_texts():
    """Sample texts with known political content."""
    return {
        "healthcare_positive": "Universal healthcare is essential...",
        "economy_market": "Free markets drive innovation...",
        "climate_urgent": "Climate change requires immediate action...",
        "mixed_topics": "Healthcare costs affect the economy...",
        "non_political": "I enjoyed the movie last night..."
    }

@pytest.fixture
def sample_subreddit_data():
    """Sample subreddit with posts and comments."""
    # Create test subreddit with variety of political content

@pytest.fixture
def mock_nlp_service():
    """Mocked NLP service for isolated testing."""
    # Mock sentiment analysis responses
```

### 2. Test Database

```python
# tests/conftest.py

@pytest.fixture
def test_db():
    """Create test database for each test."""
    # Setup test database
    # Run migrations
    # Yield session
    # Cleanup
```

## Test Execution Strategy

### 1. Test Organization

```
tests/
├── unit/
│   ├── test_topic_analyzer.py
│   ├── test_political_dimensions_analyzer.py
│   └── test_privacy_enforcement.py
├── integration/
│   ├── test_political_analysis_db.py
│   └── test_political_services.py
├── cli/
│   ├── test_analyze_commands.py
│   └── test_political_commands.py
├── performance/
│   └── test_political_performance.py
├── e2e/
│   └── test_political_workflows.py
└── fixtures/
    └── political_fixtures.py
```

### 2. Test Commands

```bash
# Run all political analysis tests
pytest tests/ -k "political or topic or dimension" -v

# Run unit tests only
pytest tests/unit/ -v

# Run integration tests
pytest tests/integration/ -v

# Run CLI tests
pytest tests/cli/ -v

# Run with coverage
pytest tests/ --cov=reddit_analyzer.services.topic_analyzer \
              --cov=reddit_analyzer.services.political_dimensions_analyzer \
              --cov=reddit_analyzer.cli.analyze \
              --cov-report=html

# Run performance tests
pytest tests/performance/ -v --benchmark-only

# Run specific test categories
pytest -m "topic_analysis" -v
pytest -m "political_dimensions" -v
pytest -m "privacy" -v
```

### 3. Continuous Integration

```yaml
# .github/workflows/political-analysis-tests.yml

name: Political Analysis Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          pip install uv
          uv sync --extra dev
      - name: Run political analysis tests
        run: |
          uv run pytest tests/ -k "political or topic" -v --cov
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## Test Metrics and Success Criteria

### 1. Coverage Requirements

- Topic Analyzer: Minimum 90% code coverage
- Political Dimensions Analyzer: Minimum 85% code coverage
- CLI Commands: Minimum 80% code coverage
- Integration Points: 100% coverage of critical paths

### 2. Performance Benchmarks

- Topic detection: < 100ms per post
- Dimension analysis: < 200ms per post
- Batch processing: > 50 posts/second
- Memory usage: < 500MB for 10,000 posts

### 3. Accuracy Metrics

- Topic detection accuracy: > 85% on test dataset
- Sentiment correlation: > 0.7 with human labels
- Dimension classification: > 80% agreement with manual review
- Clustering quality: Silhouette score > 0.5

## Test Reporting

### 1. Test Report Format

```
Phase 4D: Political Analysis Testing Results
==========================================

Test Summary:
- Total Tests: 145
- Passed: 142
- Failed: 2
- Skipped: 1
- Coverage: 88.5%

Category Breakdown:
┌─────────────────────┬────────┬────────┬────────┐
│ Category            │ Total  │ Passed │ Failed │
├─────────────────────┼────────┼────────┼────────┤
│ Unit Tests          │ 65     │ 64     │ 1      │
│ Integration Tests   │ 30     │ 29     │ 1      │
│ CLI Tests           │ 25     │ 25     │ 0      │
│ Performance Tests   │ 15     │ 15     │ 0      │
│ Privacy Tests       │ 10     │ 10     │ 0      │
└─────────────────────┴────────┴────────┴────────┘

Performance Results:
- Topic Detection: 78ms average (✓ within target)
- Dimension Analysis: 156ms average (✓ within target)
- Batch Processing: 68 posts/second (✓ exceeds target)

Failed Tests:
1. test_analyze_economic_dimension_edge_case
   - Issue: Confidence calculation overflow
   - Priority: Medium

2. test_political_compass_unicode_display
   - Issue: ASCII art rendering on Windows
   - Priority: Low
```

### 2. Coverage Report

```
Coverage Report: Political Analysis Components
============================================

File                                      Stmts   Miss  Cover
-----------------------------------------------------------
services/topic_analyzer.py                 162     16    90%
services/political_dimensions_analyzer.py  173     28    84%
cli/analyze.py                            497     89    82%
models/political_analysis.py               88      4    95%
data/political_topics.py                   17      2    88%
-----------------------------------------------------------
TOTAL                                     937    139    85%

Uncovered Lines:
- Error handling paths: 45%
- Edge cases: 30%
- Deprecated methods: 25%
```

## Risk Mitigation

### 1. Test Risks

- **Risk**: Political bias in test data
  - **Mitigation**: Use diverse, balanced test datasets
  - **Validation**: Regular review by multiple stakeholders

- **Risk**: Model dependency changes
  - **Mitigation**: Pin model versions, test with multiple versions
  - **Validation**: Automated compatibility testing

- **Risk**: Performance degradation
  - **Mitigation**: Continuous benchmarking, performance gates
  - **Validation**: Load testing with production-scale data

### 2. Data Privacy Risks

- **Risk**: Test data containing real user information
  - **Mitigation**: Use synthetic data, anonymize real data
  - **Validation**: Automated PII detection in test data

## Maintenance Plan

### 1. Test Maintenance

- Weekly: Run full test suite, update baselines
- Monthly: Review and update test data
- Quarterly: Performance benchmark review
- Annually: Complete test strategy review

### 2. Test Evolution

- Add tests for new political topics as they emerge
- Update dimension indicators based on linguistic evolution
- Enhance clustering algorithms based on research
- Expand language support with appropriate tests

## Conclusion

This comprehensive test specification ensures the political analysis features are thoroughly validated across all dimensions: functionality, performance, privacy, and user experience. The multi-layered testing approach provides confidence in the system's accuracy, reliability, and ethical compliance while maintaining the flexibility to evolve with changing political discourse patterns.
