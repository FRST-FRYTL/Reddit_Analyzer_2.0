# Political Analysis Feature Specification v2

## Overview

This specification outlines the implementation of political discourse analysis capabilities for the Reddit Analyzer. The feature focuses on objective, topic-based analysis of political discussions at the subreddit level, prioritizing transparency, accuracy, and ethical considerations. This is designed as a research tool for understanding political discourse patterns without making definitive bias classifications.

## Key Changes from v1

- **Topic-First Approach**: Focus on political topic detection and sentiment, not bias classification
- **Multi-Dimensional Analysis**: Avoid oversimplified left-right spectrum
- **Phased Implementation**: Start with objective metrics, defer classification
- **Reduced Dependencies**: No heavy ML frameworks initially required
- **Enhanced Transparency**: Clear limitations and confidence intervals
- **Ethical Safeguards**: Stronger privacy protections and opt-in mechanisms

## Objectives

1. **Analyze Political Topics**: Identify and track political topic prevalence in subreddits
2. **Measure Discussion Quality**: Assess civility, constructiveness, and engagement patterns
3. **Track Topic Sentiment**: Understand how communities discuss political topics
4. **Community Dynamics**: Analyze cross-community engagement and diversity
5. **Research Tool**: Provide objective data for academic and journalistic research

## Architecture Integration

### Compatibility Requirements

- **Non-Breaking**: All changes must be additive and not affect existing functionality
- **Lightweight**: Initial implementation uses existing NLP capabilities
- **Modular Design**: Political analysis as an optional, explicitly activated module
- **Performance Conscious**: Minimal impact on regular data collection

### Component Integration

```
Existing System                    New Components
┌─────────────────┐               ┌──────────────────────┐
│   NLP Service   │──extends───►  │ TopicAnalyzer        │
└─────────────────┘               └──────────────────────┘
        │                                    │
        ▼                                    ▼
┌─────────────────┐               ┌──────────────────────┐
│  TextAnalysis   │──enhanced──►  │ + political_topics   │
│     Model       │               │ + topic_sentiment    │
└─────────────────┘               │ + discussion_quality │
        │                         └──────────────────────┘
        ▼
┌─────────────────┐               ┌──────────────────────┐
│   CLI Commands  │──new group─►  │  analysis commands   │
└─────────────────┘               └──────────────────────┘
```

## Implementation Phases

### Phase 1: Topic Analysis Foundation (Weeks 1-2)

#### 1.1 Topic Detection Service

```python
# reddit_analyzer/services/topic_analyzer.py

class TopicAnalyzer:
    """
    Service for analyzing political topics in Reddit content.
    Uses existing NLP capabilities for topic detection.
    """

    def __init__(self):
        self.nlp_service = get_nlp_service()
        self.political_topics = self._load_topic_taxonomy()

    def detect_political_topics(self, text: str) -> Dict[str, float]:
        """
        Detect political topics in text with confidence scores.
        Returns: {"healthcare": 0.8, "economy": 0.6, "climate": 0.3}
        """

    def analyze_topic_sentiment(self, text: str, topic: str) -> Dict[str, Any]:
        """
        Analyze sentiment specifically around a political topic.
        Returns sentiment score, subjectivity, and confidence.
        """

    def calculate_discussion_quality(self, comments: List[str]) -> Dict[str, float]:
        """
        Assess quality metrics: civility, constructiveness, diversity.
        """
```

#### 1.2 Political Topic Taxonomy

```python
# reddit_analyzer/data/political_topics.py

POLITICAL_TOPIC_TAXONOMY = {
    "healthcare": {
        "keywords": ["healthcare", "insurance", "medicare", "medicaid", "ACA"],
        "subtopics": ["public_option", "single_payer", "prescription_drugs"]
    },
    "economy": {
        "keywords": ["economy", "jobs", "unemployment", "inflation", "wages"],
        "subtopics": ["taxation", "minimum_wage", "trade", "regulation"]
    },
    "climate": {
        "keywords": ["climate", "environment", "emissions", "renewable"],
        "subtopics": ["paris_agreement", "green_energy", "carbon_tax"]
    },
    "immigration": {
        "keywords": ["immigration", "border", "refugees", "visa"],
        "subtopics": ["border_security", "pathway_citizenship", "asylum"]
    },
    # ... more topics
}
```

#### 1.3 Database Schema Extensions

```python
# Add to existing TextAnalysis model (non-breaking)

# Topic analysis fields (all nullable for backwards compatibility)
political_topics = Column(JSON, nullable=True)  # {"healthcare": 0.8, "economy": 0.6}
topic_sentiments = Column(JSON, nullable=True)  # {"healthcare": {"sentiment": 0.3, "confidence": 0.8}}
discussion_quality_score = Column(Float, nullable=True)  # 0.0 to 1.0
```

### Phase 2: Enhanced Analytics (Weeks 3-4)

#### 2.1 New Models

```python
# reddit_analyzer/models/topic_analysis.py

class SubredditTopicProfile(Base):
    """Aggregate topic analysis for a subreddit."""
    __tablename__ = "subreddit_topic_profiles"

    id = Column(Integer, primary_key=True)
    subreddit_id = Column(Integer, ForeignKey("subreddits.id"))

    # Time period
    analysis_start_date = Column(DateTime, nullable=False)
    analysis_end_date = Column(DateTime, nullable=False)

    # Topic metrics
    dominant_topics = Column(JSON)  # Top 5 topics by prevalence
    topic_distribution = Column(JSON)  # All topics with percentages
    topic_sentiment_map = Column(JSON)  # Sentiment by topic

    # Discussion quality
    avg_discussion_quality = Column(Float)
    civility_score = Column(Float)
    constructiveness_score = Column(Float)
    viewpoint_diversity = Column(Float)

    # Activity metrics
    total_posts_analyzed = Column(Integer)
    total_comments_analyzed = Column(Integer)
    unique_users_analyzed = Column(Integer)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    confidence_level = Column(Float)  # Overall confidence in analysis

class CommunityOverlap(Base):
    """Track user overlap between communities."""
    __tablename__ = "community_overlaps"

    id = Column(Integer, primary_key=True)
    subreddit_a_id = Column(Integer, ForeignKey("subreddits.id"))
    subreddit_b_id = Column(Integer, ForeignKey("subreddits.id"))

    # Overlap metrics
    user_overlap_count = Column(Integer)
    user_overlap_percentage = Column(Float)
    shared_topics = Column(JSON)

    # Engagement patterns
    cross_posting_count = Column(Integer)
    sentiment_differential = Column(Float)  # How differently topics are discussed

    analysis_date = Column(DateTime)
```

#### 2.2 CLI Commands

```bash
# New command group: analyze
reddit-analyzer analyze topics SUBREDDIT [OPTIONS]
reddit-analyzer analyze sentiment SUBREDDIT --topic TOPIC [OPTIONS]
reddit-analyzer analyze quality SUBREDDIT [OPTIONS]
reddit-analyzer analyze overlap SUBREDDIT1 SUBREDDIT2 [OPTIONS]
reddit-analyzer analyze report SUBREDDIT --output FILE [OPTIONS]
```

#### Command Examples

```bash
# Analyze political topics in a subreddit
uv run reddit-analyzer analyze topics politics --days 30

# Analyze sentiment around specific topic
uv run reddit-analyzer analyze sentiment politics --topic healthcare

# Assess discussion quality
uv run reddit-analyzer analyze quality news --min-comments 50

# Compare community overlap
uv run reddit-analyzer analyze overlap politics conservative --include-topics

# Generate comprehensive report
uv run reddit-analyzer analyze report worldnews --format markdown --output analysis.md
```

### Phase 3: Advanced Metrics (Weeks 5-6)

#### 3.1 Discussion Quality Algorithms

```python
def calculate_discussion_quality(comments: List[Comment]) -> Dict[str, float]:
    """
    Calculate multi-dimensional discussion quality metrics.
    """
    # Civility score (based on toxic language detection)
    civility = 1.0 - detect_toxicity_rate(comments)

    # Constructiveness (length, references, questions)
    constructiveness = calculate_constructiveness(comments)

    # Viewpoint diversity (unique perspectives)
    diversity = calculate_viewpoint_diversity(comments)

    # Engagement quality (response rate, depth)
    engagement = calculate_engagement_quality(comments)

    return {
        "overall_quality": weighted_average([civility, constructiveness, diversity, engagement]),
        "civility_score": civility,
        "constructiveness_score": constructiveness,
        "viewpoint_diversity": diversity,
        "engagement_quality": engagement,
        "confidence": calculate_confidence(len(comments))
    }
```

#### 3.2 Community Dynamics Analysis

```python
def analyze_community_dynamics(subreddit_a: str, subreddit_b: str) -> Dict[str, Any]:
    """
    Analyze relationship between two communities.
    """
    # User overlap
    shared_users = find_shared_users(subreddit_a, subreddit_b)

    # Topic overlap
    topics_a = get_dominant_topics(subreddit_a)
    topics_b = get_dominant_topics(subreddit_b)
    shared_topics = set(topics_a) & set(topics_b)

    # Sentiment differential
    sentiment_diff = {}
    for topic in shared_topics:
        sentiment_a = get_topic_sentiment(subreddit_a, topic)
        sentiment_b = get_topic_sentiment(subreddit_b, topic)
        sentiment_diff[topic] = abs(sentiment_a - sentiment_b)

    return {
        "user_overlap_percentage": len(shared_users) / total_users,
        "shared_topics": list(shared_topics),
        "sentiment_differential": sentiment_diff,
        "engagement_patterns": analyze_cross_engagement(shared_users)
    }
```

### Phase 4: Multi-Dimensional Political Analysis (Weeks 7-8)

#### 4.1 Political Dimensions Model

Implement a nuanced political analysis system using multiple dimensions rather than a single left-right axis:

```python
# reddit_analyzer/services/political_dimensions_analyzer.py

class PoliticalDimensionsAnalyzer:
    """
    Multi-dimensional political analysis system.
    Avoids oversimplified left-right classification.
    """

    def __init__(self):
        self.topic_analyzer = TopicAnalyzer()
        self.dimensions = self._initialize_dimensions()

    def _initialize_dimensions(self):
        """Initialize the three-axis political model."""
        return {
            "economic": EconomicDimension(),  # Market <-> Planned
            "social": SocialDimension(),      # Liberty <-> Authority
            "governance": GovernanceDimension()  # Decentralized <-> Centralized
        }

    def analyze_political_dimensions(self, text: str) -> PoliticalAnalysisResult:
        """
        Analyze text across multiple political dimensions.
        Returns scores with confidence intervals.
        """
        # Extract political topics first
        topics = self.topic_analyzer.detect_political_topics(text)

        # Analyze each dimension based on topic content
        results = {}
        for dimension_name, dimension in self.dimensions.items():
            score, confidence, evidence = dimension.analyze(text, topics)
            results[dimension_name] = {
                "score": score,  # -1.0 to 1.0
                "confidence": confidence,  # 0.0 to 1.0
                "evidence": evidence,  # Key phrases/topics that influenced score
                "label": dimension.get_label(score)  # Human-readable position
            }

        return PoliticalAnalysisResult(
            dimensions=results,
            dominant_topics=topics,
            analysis_quality=self._calculate_quality_score(results)
        )

class EconomicDimension:
    """Economic axis: Market-oriented <-> Planned economy."""

    MARKET_INDICATORS = {
        "keywords": ["free market", "competition", "privatization", "deregulation"],
        "topics": ["entrepreneurship", "market_solutions", "economic_freedom"]
    }

    PLANNED_INDICATORS = {
        "keywords": ["regulation", "public ownership", "wealth redistribution"],
        "topics": ["market_regulation", "public_services", "economic_equality"]
    }

    def analyze(self, text: str, topics: Dict[str, float]) -> Tuple[float, float, List[str]]:
        """Analyze economic dimension with evidence tracking."""
        market_score = self._score_indicators(text, topics, self.MARKET_INDICATORS)
        planned_score = self._score_indicators(text, topics, self.PLANNED_INDICATORS)

        # Calculate position (-1 = planned, +1 = market)
        total = market_score + planned_score
        if total > 0:
            position = (market_score - planned_score) / total
            confidence = min(total / 10, 1.0)  # Confidence based on evidence strength
        else:
            position = 0.0
            confidence = 0.0

        evidence = self._extract_evidence(text, market_score, planned_score)
        return position, confidence, evidence

    def get_label(self, score: float) -> str:
        """Convert numeric score to human-readable label."""
        if score < -0.6:
            return "Strongly Planned Economy"
        elif score < -0.2:
            return "Moderately Planned Economy"
        elif score < 0.2:
            return "Mixed Economy"
        elif score < 0.6:
            return "Moderately Market Economy"
        else:
            return "Strongly Market Economy"

class SocialDimension:
    """Social axis: Individual liberty <-> Social authority."""

    LIBERTY_INDICATORS = {
        "keywords": ["individual freedom", "personal choice", "civil liberties"],
        "topics": ["personal_autonomy", "privacy_rights", "freedom_expression"]
    }

    AUTHORITY_INDICATORS = {
        "keywords": ["social order", "traditional values", "collective good"],
        "topics": ["social_cohesion", "moral_standards", "community_values"]
    }

    # Similar implementation pattern...

class GovernanceDimension:
    """Governance axis: Decentralized <-> Centralized power."""

    DECENTRALIZED_INDICATORS = {
        "keywords": ["local control", "states rights", "grassroots", "bottom-up"],
        "topics": ["federalism", "local_governance", "community_solutions"]
    }

    CENTRALIZED_INDICATORS = {
        "keywords": ["federal", "national policy", "central planning", "top-down"],
        "topics": ["national_programs", "federal_regulation", "unified_policy"]
    }

    # Similar implementation pattern...

#### 4.2 Enhanced Database Models for Political Dimensions

```python
# reddit_analyzer/models/political_analysis.py

class PoliticalDimensionsAnalysis(Base):
    """Store multi-dimensional political analysis results."""
    __tablename__ = "political_dimensions_analyses"

    id = Column(Integer, primary_key=True)
    text_analysis_id = Column(Integer, ForeignKey("text_analyses.id"))

    # Economic dimension
    economic_score = Column(Float)  # -1.0 (planned) to 1.0 (market)
    economic_confidence = Column(Float)  # 0.0 to 1.0
    economic_label = Column(String(50))
    economic_evidence = Column(JSON)  # Keywords/phrases that influenced score

    # Social dimension
    social_score = Column(Float)  # -1.0 (authority) to 1.0 (liberty)
    social_confidence = Column(Float)
    social_label = Column(String(50))
    social_evidence = Column(JSON)

    # Governance dimension
    governance_score = Column(Float)  # -1.0 (centralized) to 1.0 (decentralized)
    governance_confidence = Column(Float)
    governance_label = Column(String(50))
    governance_evidence = Column(JSON)

    # Overall metrics
    analysis_quality = Column(Float)  # Overall confidence in the analysis
    dominant_dimension = Column(String(20))  # Which dimension had strongest signal

    created_at = Column(DateTime, default=datetime.utcnow)

class SubredditPoliticalDimensions(Base):
    """Aggregate political dimensions for a subreddit."""
    __tablename__ = "subreddit_political_dimensions"

    id = Column(Integer, primary_key=True)
    subreddit_id = Column(Integer, ForeignKey("subreddits.id"))

    # Time period
    analysis_start_date = Column(DateTime, nullable=False)
    analysis_end_date = Column(DateTime, nullable=False)

    # Aggregate scores for each dimension
    avg_economic_score = Column(Float)
    economic_std_dev = Column(Float)
    economic_distribution = Column(JSON)  # Histogram data

    avg_social_score = Column(Float)
    social_std_dev = Column(Float)
    social_distribution = Column(JSON)

    avg_governance_score = Column(Float)
    governance_std_dev = Column(Float)
    governance_distribution = Column(JSON)

    # Political diversity metrics
    political_diversity_index = Column(Float)  # 0.0 to 1.0
    dimension_correlation = Column(JSON)  # Correlation between dimensions

    # Cluster analysis
    political_clusters = Column(JSON)  # Identified political groupings
    cluster_sizes = Column(JSON)  # Size of each cluster

    # Metadata
    total_posts_analyzed = Column(Integer)
    total_comments_analyzed = Column(Integer)
    avg_confidence_level = Column(Float)

    created_at = Column(DateTime, default=datetime.utcnow)
```

#### 4.3 CLI Commands for Political Dimensions

```bash
# Extended CLI commands for political dimensions
reddit-analyzer analyze dimensions SUBREDDIT [OPTIONS]
reddit-analyzer analyze political-compass SUBREDDIT [OPTIONS]
reddit-analyzer analyze dimension-trends SUBREDDIT --dimension DIMENSION [OPTIONS]
reddit-analyzer analyze political-diversity SUBREDDIT [OPTIONS]
reddit-analyzer analyze political-clusters SUBREDDIT [OPTIONS]
```

#### Command Examples

```bash
# Analyze political dimensions of a subreddit
uv run reddit-analyzer analyze dimensions politics --days 30

# Generate political compass visualization
uv run reddit-analyzer analyze political-compass news --output compass.png

# Track specific dimension over time
uv run reddit-analyzer analyze dimension-trends economics --dimension economic --interval daily

# Analyze political diversity
uv run reddit-analyzer analyze political-diversity politicaldiscussion

# Identify political clusters
uv run reddit-analyzer analyze political-clusters moderatepolitics --min-cluster-size 50
```

#### 4.4 Visualization for Multi-Dimensional Analysis

```python
def render_political_compass(profile: SubredditPoliticalDimensions):
    """
    Political Compass for r/example (2024-01-01 to 2024-01-31)
    =========================================================

                        Liberty (+1.0)
                             |
                             |
    Planned (-1.0) ----------+---------- Market (+1.0)
                             |
                             |
                        Authority (-1.0)

    Average Position:
    - Economic: +0.25 (Moderately Market Economy)
    - Social: +0.15 (Slightly Liberty-oriented)

    Governance: -0.10 (Slightly Centralized)

    Political Diversity: High (0.78/1.0)
    Confidence Level: 73%
    """

def render_dimension_distribution(dimension_name: str, distribution: Dict):
    """
    Economic Dimension Distribution
    ===============================

    Strongly Planned    : ██ (5%)
    Moderately Planned  : ████████ (20%)
    Mixed Economy       : ████████████████ (40%)
    Moderately Market   : ██████████ (25%)
    Strongly Market     : ████ (10%)

    Mean: +0.25 | Std Dev: 0.42 | Diversity: 0.73
    """

def generate_3d_visualization(profile: SubredditPoliticalDimensions):
    """
    Generate 3D scatter plot showing all three dimensions.
    Useful for identifying political clusters and outliers.
    """
```

#### 4.5 Algorithms for Political Dimension Analysis

```python
def calculate_political_diversity(analyses: List[PoliticalDimensionsAnalysis]) -> float:
    """
    Calculate political diversity using multi-dimensional dispersion.
    """
    if len(analyses) < 10:
        return 0.0

    # Extract all dimension scores
    points = np.array([
        [a.economic_score, a.social_score, a.governance_score]
        for a in analyses
    ])

    # Calculate dispersion metrics
    centroid = np.mean(points, axis=0)
    distances = np.linalg.norm(points - centroid, axis=1)

    # Normalize by theoretical maximum dispersion
    max_distance = np.sqrt(3)  # Maximum distance in 3D unit cube
    normalized_dispersion = np.mean(distances) / max_distance

    # Weight by confidence levels
    weights = [a.analysis_quality for a in analyses]
    weighted_diversity = np.average(normalized_dispersion, weights=weights)

    return min(weighted_diversity * 1.5, 1.0)  # Scale to 0-1 range

def identify_political_clusters(analyses: List[PoliticalDimensionsAnalysis]) -> Dict:
    """
    Identify distinct political groups within a subreddit.
    """
    # Use DBSCAN or K-means clustering on the 3D political space
    points = np.array([
        [a.economic_score, a.social_score, a.governance_score]
        for a in analyses
    ])

    # Determine optimal number of clusters
    optimal_k = find_optimal_clusters(points)

    # Perform clustering
    clusters = KMeans(n_clusters=optimal_k).fit_predict(points)

    # Characterize each cluster
    cluster_profiles = {}
    for cluster_id in range(optimal_k):
        cluster_points = points[clusters == cluster_id]
        cluster_profiles[f"cluster_{cluster_id}"] = {
            "size": len(cluster_points),
            "centroid": {
                "economic": float(np.mean(cluster_points[:, 0])),
                "social": float(np.mean(cluster_points[:, 1])),
                "governance": float(np.mean(cluster_points[:, 2]))
            },
            "label": generate_cluster_label(cluster_points)
        }

    return cluster_profiles
```

## Data Privacy and Ethics

### Enhanced Privacy Measures

1. **No Individual Analysis**: All analysis strictly at aggregate level
2. **Higher Thresholds**: Minimum 25 unique users for any analysis
3. **Time Aggregation**: Minimum 7-day windows to prevent tracking
4. **Data Retention**: Analysis results deleted after 90 days
5. **Opt-Out Registry**: Subreddits can request permanent exclusion

### Ethical Guidelines

```python
class EthicalConstraints:
    # Minimum thresholds
    MIN_USERS_FOR_ANALYSIS = 25
    MIN_TIME_WINDOW_DAYS = 7

    # Excluded categories
    EXCLUDED_SUBREDDIT_TYPES = ["support", "mental_health", "recovery"]

    # Transparency requirements
    REQUIRE_CONFIDENCE_INTERVALS = True
    REQUIRE_LIMITATION_DISCLOSURE = True

    def validate_analysis_request(self, subreddit: str, params: Dict) -> Tuple[bool, str]:
        """Validate that analysis request meets ethical guidelines."""
        # Check opt-out registry
        if is_opted_out(subreddit):
            return False, "Subreddit has opted out of analysis"

        # Check user threshold
        if get_unique_users(subreddit, params) < self.MIN_USERS_FOR_ANALYSIS:
            return False, "Insufficient users for ethical analysis"

        # Check subreddit type
        if get_subreddit_type(subreddit) in self.EXCLUDED_SUBREDDIT_TYPES:
            return False, "Subreddit type excluded from analysis"

        return True, "Analysis approved"
```

## Visualization and Reporting

### ASCII Visualizations

```python
def render_topic_distribution(profile: SubredditTopicProfile):
    """
    Topic Distribution for r/example (2024-01-01 to 2024-01-31)
    =========================================================

    Healthcare    : ████████████████ (32%) [+0.3 sentiment]
    Economy       : ██████████ (20%) [-0.1 sentiment]
    Climate       : ████████ (16%) [+0.5 sentiment]
    Immigration   : ██████ (12%) [-0.2 sentiment]
    Education     : █████ (10%) [+0.2 sentiment]
    Other         : █████ (10%)

    Discussion Quality: 0.72/1.0 (Good)
    - Civility: 0.85
    - Constructiveness: 0.68
    - Viewpoint Diversity: 0.63

    Confidence Level: 82% (1,234 posts, 5,678 comments analyzed)
    """
```

### Report Formats

1. **Markdown**: Human-readable reports with clear visualizations
2. **JSON**: Structured data with confidence intervals
3. **CSV**: Tabular exports for further analysis
4. **HTML**: Interactive dashboards (future enhancement)

## Configuration

```python
# reddit_analyzer/config.py additions

class TopicAnalysisConfig:
    # Analysis settings
    MIN_USERS_FOR_ANALYSIS = 25
    MIN_TIME_WINDOW_DAYS = 7
    DEFAULT_TIME_PERIOD_DAYS = 30

    # Topic detection
    TOPIC_CONFIDENCE_THRESHOLD = 0.5
    MAX_TOPICS_PER_POST = 5

    # Quality metrics
    TOXICITY_MODEL = "existing"  # Use existing NLP service
    MIN_COMMENT_LENGTH = 20  # For quality analysis

    # Performance
    BATCH_SIZE = 100
    CACHE_TTL_HOURS = 12  # Shorter for evolving discussions

    # Transparency
    ALWAYS_SHOW_CONFIDENCE = True
    ALWAYS_SHOW_LIMITATIONS = True
```

## Testing Strategy

### Unit Tests

```python
# tests/test_topic_analyzer.py

def test_topic_detection_accuracy():
    """Test topic detection with known examples."""

def test_sentiment_analysis_by_topic():
    """Test topic-specific sentiment analysis."""

def test_discussion_quality_metrics():
    """Test quality scoring algorithms."""

def test_privacy_thresholds():
    """Ensure all privacy measures enforced."""
```

### Integration Tests

```python
# tests/test_topic_analysis_integration.py

def test_full_subreddit_analysis_flow():
    """Test complete analysis workflow."""

def test_ethical_constraints_enforcement():
    """Verify ethical guidelines are followed."""
```

## Performance Considerations

### Optimization Strategies

1. **Incremental Analysis**: Process new content only
2. **Caching**: Cache topic detection results for common phrases
3. **Batch Processing**: Process posts in configurable batches
4. **Async Processing**: Non-blocking analysis for large subreddits

## Success Metrics

1. **Accuracy**: 85%+ agreement with manual topic labeling
2. **Performance**: Analysis completes within 2 minutes for 10,000 posts
3. **Coverage**: Can analyze 95% of public subreddits meeting thresholds
4. **Privacy**: Zero individual-level data exposed
5. **Transparency**: 100% of outputs include confidence levels and limitations

## Migration Plan

### Week 1-2: Topic Analysis Foundation
- Implement TopicAnalyzer service
- Add database migrations for topic analysis
- Basic topic detection CLI commands
- Unit tests for topic detection

### Week 3-4: Enhanced Analytics
- Discussion quality metrics implementation
- Community overlap analysis
- Enhanced reporting features
- Integration tests

### Week 5-6: Advanced Metrics
- Implement quality scoring algorithms
- Add community dynamics analysis
- Performance optimization
- Comprehensive testing

### Week 7-8: Multi-Dimensional Political Analysis
- Implement PoliticalDimensionsAnalyzer
- Add political dimensions database models
- CLI commands for political compass
- Clustering algorithms
- Visualization components
- Final integration testing

## Why Multi-Dimensional Political Analysis?

The multi-dimensional approach addresses key limitations of traditional left-right political classification:

1. **Nuanced Understanding**: Captures that someone can be economically conservative but socially liberal, or favor decentralized governance while supporting planned economy initiatives.

2. **Avoids False Dichotomies**: Recognizes that political positions exist in a multi-dimensional space, not on a single line.

3. **Evidence-Based**: Each dimension score includes the specific evidence (keywords, topics) that influenced it, providing transparency.

4. **Confidence Awareness**: Every score includes a confidence metric, acknowledging uncertainty in algorithmic classification.

5. **Clustering Insights**: Can identify distinct political communities that might be missed by single-axis analysis (e.g., libertarian socialists, authoritarian capitalists).

## Conclusion

This revised specification provides a sophisticated political analysis framework that:
- Starts with objective topic analysis before attempting any classification
- Uses a multi-dimensional model to avoid oversimplification
- Maintains strong privacy protections and ethical constraints
- Provides transparency through confidence scores and evidence tracking
- Allows for phased implementation with validation at each step

By combining topic-based analysis with optional multi-dimensional political classification, the feature provides valuable research insights while respecting the complexity of political discourse and user privacy.
