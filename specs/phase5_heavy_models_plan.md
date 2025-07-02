# Phase 5: Heavy NLP Models Integration Plan

**Status**: Planning (Not Executed)
**Prerequisites**: User has installed spaCy large model and PyTorch CUDA support

## Overview

Phase 5 focuses on leveraging the heavy NLP models that the user has already installed to provide enhanced analysis capabilities. This plan outlines how to integrate and utilize:

1. spaCy large model (en_core_web_lg)
2. PyTorch with CUDA support
3. Transformer-based models for advanced sentiment and emotion analysis

## Current Model Utilization

### Models Currently Used
- **VADER**: Rule-based sentiment (lightweight)
- **TextBlob**: Basic sentiment polarity
- **Transformers**: cardiffnlp/twitter-roberta-base-sentiment-latest (CPU mode)
- **scikit-learn**: LDA topic modeling

### Underutilized Resources
- **spaCy large model**: Installed but not leveraged for entity recognition, dependency parsing
- **CUDA GPU**: Available but transformers running on CPU
- **Advanced features**: Not using emotion detection, stance detection, argument mining

## Implementation Plan

### 1. GPU Acceleration for Transformers
```python
# Update sentiment_analyzer.py
class SentimentAnalyzer:
    def __init__(self):
        # Detect and use CUDA if available
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # Load models to GPU
        self.transformer_model = pipeline(
            "sentiment-analysis",
            model="cardiffnlp/twitter-roberta-base-sentiment-latest",
            device=0 if torch.cuda.is_available() else -1
        )
```

### 2. Enhanced Entity Recognition
```python
# New file: entity_analyzer.py
class EntityAnalyzer:
    def __init__(self):
        # Use the large spaCy model
        self.nlp = spacy.load("en_core_web_lg")

    def extract_political_entities(self, text):
        """Extract politicians, organizations, policies."""
        doc = self.nlp(text)

        entities = {
            "politicians": [],
            "organizations": [],
            "locations": [],
            "policies": [],
            "events": []
        }

        # Use spaCy's named entity recognition
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                # Check if politician using knowledge base
                if self._is_politician(ent.text):
                    entities["politicians"].append({
                        "name": ent.text,
                        "context": ent.sent.text,
                        "sentiment": self._get_entity_sentiment(doc, ent)
                    })
```

### 3. Advanced Emotion Detection
```python
# emotion_analyzer.py
class EmotionAnalyzer:
    def __init__(self):
        # Use j-hartmann/emotion-english-distilroberta-base
        self.emotion_model = pipeline(
            "text-classification",
            model="j-hartmann/emotion-english-distilroberta-base",
            device=0 if torch.cuda.is_available() else -1
        )

    def analyze_emotional_tone(self, text):
        """Detect emotions: anger, fear, joy, sadness, surprise, disgust."""
        results = self.emotion_model(text)

        # Map to political discourse patterns
        political_emotions = {
            "outrage": results.get("anger", 0) + results.get("disgust", 0),
            "fear": results.get("fear", 0),
            "hope": results.get("joy", 0),
            "disappointment": results.get("sadness", 0)
        }
```

### 4. Stance Detection
```python
# stance_detector.py
class StanceDetector:
    def __init__(self):
        # Use stance detection model
        self.stance_model = pipeline(
            "zero-shot-classification",
            model="facebook/bart-large-mnli",
            device=0 if torch.cuda.is_available() else -1
        )

    def detect_stance(self, text, topic):
        """Detect if text supports, opposes, or is neutral on topic."""
        candidate_labels = [
            f"supports {topic}",
            f"opposes {topic}",
            f"neutral about {topic}"
        ]

        result = self.stance_model(text, candidate_labels)
        return self._parse_stance(result)
```

### 5. Argument Mining
```python
# argument_miner.py
class ArgumentMiner:
    def __init__(self):
        self.nlp = spacy.load("en_core_web_lg")

    def extract_arguments(self, text):
        """Extract claims, evidence, and reasoning."""
        doc = self.nlp(text)

        arguments = []
        for sent in doc.sents:
            # Identify argumentative sentences
            if self._is_claim(sent):
                argument = {
                    "claim": sent.text,
                    "evidence": self._find_evidence(doc, sent),
                    "reasoning": self._extract_reasoning(sent),
                    "strength": self._evaluate_argument_strength(sent)
                }
                arguments.append(argument)
```

### 6. Enhanced Topic Modeling
```python
# advanced_topic_modeler.py
class AdvancedTopicModeler:
    def __init__(self):
        # Use BERTopic for transformer-based topic modeling
        from bertopic import BERTopic

        # Configure for GPU usage
        self.model = BERTopic(
            embedding_model="all-mpnet-base-v2",
            calculate_probabilities=True,
            device="cuda"
        )
```

## New CLI Commands

### 1. Entity Analysis
```bash
reddit-analyzer analyze entities [subreddit] --entity-type politicians
reddit-analyzer analyze entity-sentiment "Joe Biden" --subreddit politics
```

### 2. Emotion Analysis
```bash
reddit-analyzer analyze emotions [subreddit] --breakdown
reddit-analyzer analyze emotional-trends [subreddit] --days 30
```

### 3. Stance Detection
```bash
reddit-analyzer analyze stance [subreddit] --topic "climate change"
reddit-analyzer analyze stance-distribution [subreddit] --issues
```

### 4. Argument Analysis
```bash
reddit-analyzer analyze arguments [subreddit] --quality-threshold high
reddit-analyzer analyze debate-quality [subreddit] --thread [url]
```

## Performance Optimizations

### 1. Batch Processing
```python
def process_batch_gpu(texts, batch_size=32):
    """Process texts in batches for GPU efficiency."""
    results = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        batch_results = self.model(batch)
        results.extend(batch_results)
    return results
```

### 2. Model Caching
```python
@lru_cache(maxsize=10000)
def cached_sentiment(text_hash):
    """Cache sentiment results for repeated texts."""
    return self.sentiment_model(text)
```

### 3. Async Processing
```python
async def analyze_posts_async(posts):
    """Process posts concurrently."""
    tasks = []
    for post in posts:
        task = asyncio.create_task(analyze_post(post))
        tasks.append(task)

    results = await asyncio.gather(*tasks)
    return results
```

## Testing Strategy

### 1. GPU Performance Tests
```python
def test_gpu_acceleration():
    """Verify GPU is being used and measure speedup."""
    texts = ["sample text"] * 1000

    # CPU timing
    cpu_time = time_cpu_processing(texts)

    # GPU timing
    gpu_time = time_gpu_processing(texts)

    assert gpu_time < cpu_time * 0.5  # Expect at least 2x speedup
```

### 2. Quality Validation
```python
def test_entity_extraction_quality():
    """Validate entity extraction against golden dataset."""
    test_cases = load_golden_entity_dataset()

    for case in test_cases:
        extracted = entity_analyzer.extract_entities(case["text"])
        assert_entities_match(extracted, case["expected"])
```

## Database Schema Updates

### 1. Entity Storage
```sql
CREATE TABLE political_entities (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    type VARCHAR(50),  -- politician, organization, policy
    subreddit_id INTEGER,
    first_seen TIMESTAMP,
    mention_count INTEGER,
    average_sentiment FLOAT
);

CREATE TABLE entity_mentions (
    id SERIAL PRIMARY KEY,
    entity_id INTEGER REFERENCES political_entities(id),
    post_id VARCHAR(255) REFERENCES posts(id),
    context TEXT,
    sentiment FLOAT,
    emotion_scores JSONB
);
```

### 2. Enhanced Analysis Results
```sql
ALTER TABLE text_analysis ADD COLUMN emotion_scores JSONB;
ALTER TABLE text_analysis ADD COLUMN stance_positions JSONB;
ALTER TABLE text_analysis ADD COLUMN argument_quality FLOAT;
ALTER TABLE text_analysis ADD COLUMN processing_model VARCHAR(100);
```

## Configuration Updates

### 1. Model Settings
```python
# config.py additions
class Config:
    # GPU settings
    USE_GPU = os.getenv("USE_GPU", "true").lower() == "true"
    GPU_BATCH_SIZE = int(os.getenv("GPU_BATCH_SIZE", "32"))

    # Model selection
    SPACY_MODEL = os.getenv("SPACY_MODEL", "en_core_web_lg")
    EMOTION_MODEL = os.getenv("EMOTION_MODEL", "j-hartmann/emotion-english-distilroberta-base")
    STANCE_MODEL = os.getenv("STANCE_MODEL", "facebook/bart-large-mnli")

    # Processing thresholds
    MIN_ARGUMENT_LENGTH = int(os.getenv("MIN_ARGUMENT_LENGTH", "50"))
    ENTITY_CONFIDENCE_THRESHOLD = float(os.getenv("ENTITY_CONFIDENCE_THRESHOLD", "0.8"))
```

## Memory Management

### 1. Model Loading Strategy
```python
class ModelManager:
    """Lazy load models to manage memory."""

    def __init__(self):
        self._models = {}

    def get_model(self, model_name):
        if model_name not in self._models:
            self._models[model_name] = self._load_model(model_name)
        return self._models[model_name]

    def unload_model(self, model_name):
        if model_name in self._models:
            del self._models[model_name]
            torch.cuda.empty_cache()
```

## Monitoring and Metrics

### 1. GPU Utilization
```python
def log_gpu_metrics():
    """Log GPU memory and utilization."""
    if torch.cuda.is_available():
        memory_used = torch.cuda.memory_allocated() / 1024**3  # GB
        memory_total = torch.cuda.get_device_properties(0).total_memory / 1024**3

        logger.info(f"GPU Memory: {memory_used:.2f}/{memory_total:.2f} GB")
```

### 2. Processing Speed Metrics
```python
@dataclass
class ProcessingMetrics:
    texts_per_second: float
    gpu_utilization: float
    memory_usage: float
    model_load_time: float
    batch_processing_time: float
```

## Rollout Plan

### Phase 5A: GPU Acceleration (Week 1)
1. Update transformers to use CUDA
2. Implement batch processing
3. Add GPU monitoring
4. Benchmark performance improvements

### Phase 5B: Entity Analysis (Week 2)
1. Implement entity extraction with spaCy large
2. Create political entity database
3. Add entity-based CLI commands
4. Test entity recognition accuracy

### Phase 5C: Emotion & Stance (Week 3)
1. Integrate emotion detection model
2. Implement stance detection
3. Update database schema
4. Create emotion trend analysis

### Phase 5D: Argument Mining (Week 4)
1. Implement argument extraction
2. Add argument quality scoring
3. Create debate analysis features
4. Validate against human annotations

## Success Metrics

1. **Performance**: 3-5x speedup for batch processing
2. **Accuracy**: 90%+ entity recognition precision
3. **Coverage**: Analyze 10x more posts per minute
4. **Quality**: Detect nuanced emotions and stances
5. **Usability**: New insights not possible with light models

## Risk Mitigation

1. **Memory Issues**: Implement model unloading and batch size limits
2. **GPU Availability**: Graceful fallback to CPU mode
3. **Processing Time**: Add progress bars and time estimates
4. **Model Errors**: Comprehensive error handling and retries

## Conclusion

Phase 5 will transform the Reddit Analyzer into a state-of-the-art political discourse analysis tool by leveraging heavy NLP models. The GPU acceleration and advanced models will enable:

- Real-time analysis of large-scale discussions
- Nuanced understanding of political arguments
- Tracking of political entities and their perception
- Emotional tone analysis of political discourse
- Stance detection on controversial issues

This positions the tool for professional political analysis and research applications.
