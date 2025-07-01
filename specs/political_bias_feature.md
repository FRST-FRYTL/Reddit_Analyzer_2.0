# Political Bias Analysis Feature Specification

## Overview

This specification outlines the implementation of political bias analysis capabilities for the Reddit Analyzer. The feature focuses on subreddit-level analysis of political discourse patterns, user activity distributions, and community dynamics. This is designed as an analytical/research tool rather than an individual user profiling system.

## Objectives

1. **Analyze Political Bias at Subreddit Level**: Provide aggregate metrics on the political leanings of entire subreddit communities
2. **Track Activity Patterns**: Understand how users with different political viewpoints engage within and across subreddits
3. **Identify Echo Chambers**: Detect communities with low political diversity
4. **Monitor Temporal Changes**: Track how political bias shifts over time and in response to events
5. **Research Tool**: Provide data for academic and journalistic research on political discourse

## Architecture Integration

### Compatibility Requirements

- **Non-Breaking**: All changes must be additive and not affect existing functionality
- **Modular Design**: Political bias analysis should be an optional module
- **Reuse Existing Components**: Leverage current NLP service, database models, and CLI structure
- **Performance Conscious**: Should not significantly impact regular data collection

### Component Integration

```
Existing System                    New Components
┌─────────────────┐               ┌──────────────────────┐
│   NLP Service   │──extends───►  │ PoliticalBiasAnalyzer│
└─────────────────┘               └──────────────────────┘
        │                                    │
        ▼                                    ▼
┌─────────────────┐               ┌──────────────────────┐
│  TextAnalysis   │──enhanced──►  │ + political_score    │
│     Model       │               │ + political_label    │
└─────────────────┘               └──────────────────────┘
        │                                    │
        ▼                                    ▼
┌─────────────────┐               ┌──────────────────────┐
│   CLI Commands  │──new group─►  │  politics commands   │
└─────────────────┘               └──────────────────────┘
```

## Feature Components

### 1. Political Bias Analyzer Service

```python
# reddit_analyzer/services/political_bias_analyzer.py

class PoliticalBiasAnalyzer:
    """
    Service for analyzing political bias in Reddit content.
    Extends NLP Service capabilities for political classification.
    """

    def __init__(self):
        self.nlp_service = get_nlp_service()
        self.political_classifier = None  # Lazy loaded
        self.zero_shot_classifier = None  # For flexibility

    def analyze_political_bias(self, text: str) -> Dict[str, Any]:
        """
        Analyze political bias of a single text.
        Returns score from -1.0 (far left) to 1.0 (far right).
        """

    def analyze_subreddit(self, subreddit_name: str,
                         time_period_days: int = 30) -> SubredditPoliticalProfile:
        """
        Comprehensive political analysis of a subreddit.
        """

    def compare_subreddits(self, subreddit_names: List[str]) -> Dict[str, Any]:
        """
        Comparative political analysis across multiple subreddits.
        """
```

### 2. Database Schema Extensions

#### Enhanced TextAnalysis Model

```python
# Add to existing TextAnalysis model (non-breaking)

# Political analysis fields (all nullable for backwards compatibility)
political_score = Column(Float, nullable=True)  # -1.0 to 1.0
political_label = Column(String(20), nullable=True)  # FAR_LEFT, LEFT, CENTER, RIGHT, FAR_RIGHT
political_confidence = Column(Float, nullable=True)  # 0.0 to 1.0
political_topics = Column(JSON, nullable=True)  # {"healthcare": 0.8, "economy": 0.6}
```

#### New Models

```python
# reddit_analyzer/models/political_analysis.py

class SubredditPoliticalProfile(Base):
    """Aggregate political analysis for a subreddit."""
    __tablename__ = "subreddit_political_profiles"

    id = Column(Integer, primary_key=True)
    subreddit_id = Column(Integer, ForeignKey("subreddits.id"))

    # Time period
    analysis_start_date = Column(DateTime, nullable=False)
    analysis_end_date = Column(DateTime, nullable=False)

    # Aggregate metrics
    mean_political_score = Column(Float)
    median_political_score = Column(Float)
    std_deviation = Column(Float)
    political_diversity_index = Column(Float)  # 0.0 to 1.0

    # Distribution
    far_left_percentage = Column(Float)
    left_percentage = Column(Float)
    center_percentage = Column(Float)
    right_percentage = Column(Float)
    far_right_percentage = Column(Float)

    # Activity metrics
    total_posts_analyzed = Column(Integer)
    total_comments_analyzed = Column(Integer)
    unique_users_analyzed = Column(Integer)

    # Metadata
    dominant_topics = Column(JSON)
    common_sources = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

class UserActivityPattern(Base):
    """Aggregate patterns of user political activity."""
    __tablename__ = "user_activity_patterns"

    id = Column(Integer, primary_key=True)
    subreddit_id = Column(Integer, ForeignKey("subreddits.id"))
    analysis_date = Column(DateTime)

    # Activity distribution
    posting_bias_distribution = Column(JSON)  # Distribution of post biases
    commenting_bias_distribution = Column(JSON)  # Distribution of comment biases

    # Cross-political engagement
    echo_chamber_score = Column(Float)  # 0.0 (diverse) to 1.0 (echo chamber)
    cross_political_users = Column(Integer)  # Users active in multiple political subs
    bridge_user_percentage = Column(Float)  # Users engaging across political divides
```

### 3. CLI Commands

```bash
# New command group: politics
reddit-analyzer politics analyze-subreddit SUBREDDIT [OPTIONS]
reddit-analyzer politics compare SUBREDDIT1 SUBREDDIT2 [SUBREDDIT3...] [OPTIONS]
reddit-analyzer politics trends SUBREDDIT --days DAYS [OPTIONS]
reddit-analyzer politics report SUBREDDIT --output FILE [OPTIONS]
reddit-analyzer politics echo-chamber SUBREDDIT [OPTIONS]
```

#### Command Examples

```bash
# Analyze a subreddit's political bias
uv run reddit-analyzer politics analyze-subreddit politics --days 30

# Compare political bias across subreddits
uv run reddit-analyzer politics compare politics conservative liberal --output comparison.json

# Track political trends over time
uv run reddit-analyzer politics trends news --days 90 --interval weekly

# Generate comprehensive report
uv run reddit-analyzer politics report worldnews --format pdf --output worldnews_political_analysis.pdf

# Analyze echo chamber characteristics
uv run reddit-analyzer politics echo-chamber politicalhumor
```

### 4. Analysis Algorithms

#### Political Score Calculation

```python
def calculate_political_score(text: str) -> Tuple[float, float]:
    """
    Calculate political bias score using ensemble method.

    Returns:
        (score, confidence) where score is -1.0 to 1.0
    """
    # 1. Zero-shot classification
    zero_shot_result = classify_political_lean_zero_shot(text)

    # 2. Keyword-based scoring
    keyword_score = score_political_keywords(text)

    # 3. Pre-trained model (if available)
    if self.political_classifier:
        model_score = self.political_classifier.predict(text)

    # 4. Ensemble scoring with confidence weighting
    final_score = weighted_average([zero_shot_result, keyword_score, model_score])
    confidence = calculate_confidence(results)

    return final_score, confidence
```

#### Echo Chamber Detection

```python
def calculate_echo_chamber_score(subreddit_users: List[User]) -> float:
    """
    Calculate how insular a community is politically.

    Returns:
        Score from 0.0 (diverse) to 1.0 (echo chamber)
    """
    # 1. Political homogeneity of posts
    political_variance = calculate_political_variance(posts)

    # 2. User overlap with other political subreddits
    cross_political_activity = analyze_user_cross_posting(users)

    # 3. Engagement with dissenting views
    dissent_engagement = measure_dissent_interaction(comments)

    # 4. Moderation patterns
    removed_content_bias = analyze_removed_content(moderation_log)

    return calculate_echo_score(political_variance, cross_political_activity,
                               dissent_engagement, removed_content_bias)
```

### 5. Visualization Components

#### ASCII Charts for CLI

```python
# Political distribution chart
def render_political_distribution(profile: SubredditPoliticalProfile):
    """
    Render ASCII chart of political distribution.

    Political Distribution for r/example
    ====================================
    Far Left  : ████ (12%)
    Left      : ████████████ (35%)
    Center    : ██████ (18%)
    Right     : ██████████ (28%)
    Far Right : ██ (7%)

    Diversity Index: 0.76 (High)
    Mean Bias: -0.08 (Slight Left)
    """
```

#### Export Formats

- **JSON**: Raw data for further analysis
- **CSV**: Tabular data for spreadsheet analysis
- **Markdown**: Formatted reports with charts
- **HTML**: Interactive visualizations (future)

### 6. Configuration

```python
# reddit_analyzer/config.py additions

class PoliticalAnalysisConfig:
    # Model settings
    POLITICAL_MODEL_NAME = "cardiffnlp/twitter-roberta-base-political-bias"
    USE_ZERO_SHOT = True
    ZERO_SHOT_MODEL = "facebook/bart-large-mnli"

    # Analysis settings
    MIN_USERS_FOR_ANALYSIS = 10  # Privacy threshold
    DEFAULT_TIME_PERIOD_DAYS = 30
    POLITICAL_KEYWORDS_PATH = "data/political_keywords.json"

    # Score thresholds
    FAR_LEFT_THRESHOLD = -0.6
    LEFT_THRESHOLD = -0.2
    CENTER_THRESHOLD = 0.2
    RIGHT_THRESHOLD = 0.6

    # Performance
    BATCH_SIZE = 100
    CACHE_TTL_HOURS = 24
```

### 7. Data Privacy and Ethics

#### Privacy Measures

1. **No Individual Scores Stored**: Political scores only stored in aggregate
2. **Minimum Threshold**: Require minimum 10 users for any analysis
3. **Anonymization**: No usernames in reports, only aggregate patterns
4. **Opt-out Mechanism**: Subreddits can request exclusion

#### Ethical Guidelines

```python
# reddit_analyzer/services/political_bias_analyzer.py

class PoliticalBiasAnalyzer:

    def _check_ethical_constraints(self, subreddit: str) -> bool:
        """Ensure analysis meets ethical guidelines."""
        # Check if subreddit opted out
        if subreddit in OPTED_OUT_SUBREDDITS:
            return False

        # Check minimum user threshold
        if unique_users < MIN_USERS_FOR_ANALYSIS:
            return False

        # Check if subreddit is private
        if is_private_subreddit(subreddit):
            return False

        return True
```

### 8. Performance Optimization

#### Caching Strategy

```python
# Use Redis for caching analysis results
CACHE_KEY_FORMAT = "political_analysis:{subreddit}:{start_date}:{end_date}"
CACHE_TTL = 24 * 60 * 60  # 24 hours

def get_cached_analysis(subreddit: str, start_date: date, end_date: date):
    cache_key = CACHE_KEY_FORMAT.format(
        subreddit=subreddit,
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat()
    )
    return redis_client.get(cache_key)
```

#### Batch Processing

```python
# Process posts in batches to avoid memory issues
def analyze_posts_batch(posts: List[Post], batch_size: int = 100):
    for i in range(0, len(posts), batch_size):
        batch = posts[i:i + batch_size]
        yield process_batch(batch)
```

### 9. Testing Strategy

#### Unit Tests

```python
# tests/test_political_bias_analyzer.py

def test_political_score_calculation():
    """Test political score calculation accuracy."""

def test_echo_chamber_detection():
    """Test echo chamber scoring algorithm."""

def test_privacy_thresholds():
    """Ensure privacy measures are enforced."""
```

#### Integration Tests

```python
# tests/test_political_bias_integration.py

def test_full_subreddit_analysis():
    """Test complete subreddit analysis workflow."""

def test_cli_commands():
    """Test all political analysis CLI commands."""
```

### 10. Migration Plan

#### Phase 1: Core Implementation (Week 1-2)
- Implement PoliticalBiasAnalyzer service
- Add database migrations for new fields
- Basic political scoring algorithm

#### Phase 2: CLI Integration (Week 3)
- Add politics command group
- Implement basic analysis commands
- ASCII visualization

#### Phase 3: Advanced Features (Week 4-5)
- Echo chamber detection
- Temporal analysis
- Comparative reports

#### Phase 4: Optimization (Week 6)
- Caching implementation
- Performance tuning
- Comprehensive testing

## Dependencies

### Required New Packages

```toml
# Add to pyproject.toml
transformers = "^4.36.0"  # For political classification models
torch = "^2.1.0"  # For transformer models
scipy = "^1.11.0"  # For statistical analysis
```

### Optional Packages

```toml
# For enhanced visualizations
plotly = "^5.18.0"
wordcloud = "^1.9.0"
```

## Success Metrics

1. **Performance**: Analysis completes within 5 minutes for 10,000 posts
2. **Accuracy**: 80%+ agreement with manual political bias labels
3. **Coverage**: Can analyze 95% of public subreddits
4. **Privacy**: Zero individual political scores exposed
5. **Usability**: Clear, actionable insights from reports

## Future Enhancements

1. **Real-time Monitoring**: Live political bias tracking
2. **Event Detection**: Automatic detection of political shifts
3. **Network Analysis**: Map political communities and their connections
4. **Sentiment Evolution**: Track how political sentiment evolves
5. **Misinformation Detection**: Identify potential misinformation patterns

## Conclusion

This political bias analysis feature provides powerful research capabilities while maintaining user privacy and system integrity. By focusing on aggregate analysis and research applications, it adds significant value without compromising the existing system or user trust.
