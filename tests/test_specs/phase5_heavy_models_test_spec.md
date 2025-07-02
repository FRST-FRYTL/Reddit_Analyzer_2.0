# Phase 5 Heavy Models Test Specification

**Version**: 1.0
**Date**: 2025-07-02
**Author**: Test Engineering Team
**Status**: Ready for Implementation

## 1. Executive Summary

This document specifies the comprehensive testing strategy for Phase 5 heavy models implementation in the Reddit Analyzer. The test suite validates GPU acceleration, advanced NLP features, fallback mechanisms, and performance requirements while ensuring backward compatibility.

## 2. Test Objectives

### Primary Objectives
1. Validate GPU acceleration provides expected performance improvements
2. Ensure all heavy models function correctly when available
3. Verify graceful degradation when models/GPU are unavailable
4. Confirm backward compatibility with existing features
5. Validate new CLI commands and their outputs
6. Ensure database schema updates work correctly

### Quality Metrics
- **Feature Coverage**: 100% of new analyzers tested
- **Performance**: GPU provides ≥2x speedup for batch processing
- **Reliability**: Zero crashes from missing dependencies
- **Accuracy**: Heavy models improve analysis accuracy by ≥20%

## 3. Test Categories

### 3.1 Unit Tests

#### 3.1.1 Entity Analyzer Tests
```python
# tests/test_entity_analyzer.py

class TestEntityAnalyzer:
    """Test entity extraction and analysis."""

    def test_entity_extraction_without_model(self):
        """Test graceful handling when spaCy model unavailable."""
        # Should return empty results with warning

    def test_entity_extraction_with_small_model(self):
        """Test basic entity extraction with small model."""
        # Should extract basic entities

    def test_entity_extraction_with_large_model(self):
        """Test advanced entity extraction with large model."""
        # Should extract entities with higher accuracy

    def test_political_entity_classification(self):
        """Test classification of political entities."""
        # Should identify politicians, organizations, policies

    def test_entity_sentiment_analysis(self):
        """Test sentiment analysis for specific entities."""
        # Should return entity-specific sentiment scores

    def test_entity_relationship_extraction(self):
        """Test extraction of relationships between entities."""
        # Should identify entity relationships
```

#### 3.1.2 Emotion Analyzer Tests
```python
# tests/test_emotion_analyzer.py

class TestEmotionAnalyzer:
    """Test emotion detection capabilities."""

    def test_emotion_detection_fallback(self):
        """Test fallback when transformer model unavailable."""
        # Should use VADER for basic emotion approximation

    def test_emotion_detection_cpu(self):
        """Test emotion detection on CPU."""
        # Should work but slower

    def test_emotion_detection_gpu(self):
        """Test emotion detection with GPU acceleration."""
        # Should be faster than CPU

    def test_political_emotion_mapping(self):
        """Test mapping to political emotions."""
        # Should map to outrage, fear, hope, disappointment

    def test_batch_emotion_processing(self):
        """Test batch processing efficiency."""
        # Should process multiple texts efficiently
```

#### 3.1.3 Stance Detector Tests
```python
# tests/test_stance_detector.py

class TestStanceDetector:
    """Test stance detection functionality."""

    def test_stance_detection_unavailable(self):
        """Test when stance model unavailable."""
        # Should return None with appropriate message

    def test_basic_stance_detection(self):
        """Test stance towards specific topics."""
        # Should detect support/oppose/neutral

    def test_political_position_detection(self):
        """Test political position identification."""
        # Should identify left/center/right positions

    def test_multi_issue_stance(self):
        """Test stance on multiple issues."""
        # Should handle multiple topics

    def test_confidence_scoring(self):
        """Test confidence scores for stance detection."""
        # Should provide calibrated confidence scores
```

#### 3.1.4 Argument Miner Tests
```python
# tests/test_argument_miner.py

class TestArgumentMiner:
    """Test argument structure extraction."""

    def test_claim_identification(self):
        """Test identification of claims."""
        # Should identify argumentative claims

    def test_evidence_extraction(self):
        """Test extraction of supporting evidence."""
        # Should link evidence to claims

    def test_argument_quality_scoring(self):
        """Test argument quality evaluation."""
        # Should score based on evidence strength

    def test_fallacy_detection(self):
        """Test detection of logical fallacies."""
        # Should identify common fallacies

    def test_debate_structure_analysis(self):
        """Test analysis of debate threads."""
        # Should map argument relationships
```

### 3.2 Integration Tests

#### 3.2.1 NLP Service Integration
```python
# tests/test_nlp_service_heavy_models.py

class TestNLPServiceHeavyModels:
    """Test NLP service with heavy models."""

    def test_service_initialization_without_models(self):
        """Test service starts without heavy models."""
        # Should initialize with basic models only

    def test_service_initialization_with_models(self):
        """Test service with all models available."""
        # Should load all analyzers

    def test_analyzer_lazy_loading(self):
        """Test lazy loading of heavy analyzers."""
        # Should load only when requested

    def test_memory_management(self):
        """Test memory usage with multiple models."""
        # Should manage memory efficiently

    def test_concurrent_analysis(self):
        """Test concurrent requests to different analyzers."""
        # Should handle parallel processing
```

#### 3.2.2 CLI Integration Tests
```python
# tests/test_cli_heavy_models.py

class TestCLIHeavyModels:
    """Test CLI commands with heavy models."""

    def test_analyze_emotions_command(self):
        """Test emotion analysis CLI command."""
        # Should display emotion breakdown

    def test_analyze_stance_command(self):
        """Test stance detection CLI command."""
        # Should show stance analysis

    def test_analyze_entities_command(self):
        """Test entity extraction CLI command."""
        # Should display entity analysis

    def test_analyze_arguments_command(self):
        """Test argument analysis CLI command."""
        # Should show argument structure

    def test_advanced_topics_command(self):
        """Test advanced topic modeling CLI command."""
        # Should display hierarchical topics

    def test_batch_analysis_command(self):
        """Test batch processing with GPU."""
        # Should process efficiently
```

### 3.3 Performance Tests

#### 3.3.1 GPU Acceleration Tests
```python
# tests/test_gpu_performance.py

class TestGPUPerformance:
    """Test GPU acceleration performance."""

    def test_gpu_detection(self):
        """Test CUDA availability detection."""
        # Should correctly detect GPU

    def test_cpu_vs_gpu_sentiment(self):
        """Compare CPU vs GPU for sentiment analysis."""
        # GPU should be ≥2x faster

    def test_cpu_vs_gpu_emotions(self):
        """Compare CPU vs GPU for emotion detection."""
        # GPU should show speedup

    def test_batch_size_optimization(self):
        """Test optimal batch sizes for GPU."""
        # Should find optimal batch size

    def test_memory_usage_gpu(self):
        """Test GPU memory management."""
        # Should not exceed memory limits

    def test_mixed_precision_inference(self):
        """Test mixed precision for speed."""
        # Should improve performance
```

#### 3.3.2 Scalability Tests
```python
# tests/test_scalability_heavy_models.py

class TestScalabilityHeavyModels:
    """Test scalability with heavy models."""

    def test_concurrent_users(self):
        """Test with multiple concurrent users."""
        # Should handle 10+ concurrent requests

    def test_large_document_processing(self):
        """Test processing of large documents."""
        # Should handle documents >10k words

    def test_streaming_analysis(self):
        """Test streaming data analysis."""
        # Should process in real-time

    def test_model_switching_overhead(self):
        """Test overhead of switching models."""
        # Should minimize switching time
```

### 3.4 Accuracy Tests

#### 3.4.1 Model Quality Tests
```python
# tests/test_model_accuracy.py

class TestModelAccuracy:
    """Test accuracy of heavy models."""

    def test_entity_recognition_accuracy(self):
        """Test entity recognition F1 score."""
        # Should achieve >0.85 F1 on test set

    def test_emotion_detection_accuracy(self):
        """Test emotion classification accuracy."""
        # Should achieve >0.80 accuracy

    def test_stance_detection_accuracy(self):
        """Test stance classification accuracy."""
        # Should achieve >0.75 accuracy

    def test_topic_coherence(self):
        """Test topic model coherence."""
        # Should have high coherence scores
```

### 3.5 Fallback and Error Handling Tests

#### 3.5.1 Graceful Degradation Tests
```python
# tests/test_graceful_degradation.py

class TestGracefulDegradation:
    """Test system behavior without heavy models."""

    def test_missing_spacy_model(self):
        """Test when spaCy large model missing."""
        # Should fall back to small model

    def test_missing_transformers(self):
        """Test when transformers not installed."""
        # Should use traditional methods

    def test_cuda_unavailable(self):
        """Test when CUDA not available."""
        # Should fall back to CPU

    def test_model_loading_failure(self):
        """Test when model fails to load."""
        # Should handle gracefully

    def test_out_of_memory_gpu(self):
        """Test GPU OOM handling."""
        # Should fall back to CPU
```

### 3.6 Database Tests

#### 3.6.1 Schema Migration Tests
```python
# tests/test_phase5_migrations.py

class TestPhase5Migrations:
    """Test database schema updates."""

    def test_migration_up(self):
        """Test applying Phase 5 migration."""
        # Should add new fields/tables

    def test_migration_down(self):
        """Test rolling back Phase 5 migration."""
        # Should remove new fields/tables

    def test_data_preservation(self):
        """Test existing data preserved."""
        # Should not lose any data

    def test_new_fields_storage(self):
        """Test storing heavy model results."""
        # Should store all new data types
```

## 4. Test Data Requirements

### 4.1 Test Datasets
```yaml
test_datasets:
  entity_recognition:
    - political_entities_golden.json  # 1000 annotated entities
    - entity_relationships.json       # 500 relationship pairs

  emotion_detection:
    - emotion_labeled_posts.json      # 2000 labeled posts
    - political_emotions.json         # 1000 political texts

  stance_detection:
    - stance_annotated_debates.json   # 1500 stance examples
    - multi_issue_stances.json        # 500 multi-issue texts

  argument_mining:
    - argument_structures.json        # 800 annotated arguments
    - debate_threads.json            # 200 full debates

  performance:
    - large_corpus.json              # 10k posts for benchmarking
    - streaming_data.json            # Simulated real-time data
```

### 4.2 Golden Outputs
```yaml
golden_outputs:
  cli_commands:
    - analyze_emotions_gpu_output.txt
    - analyze_emotions_cpu_output.txt
    - analyze_stance_output.txt
    - analyze_entities_output.txt
    - analyze_arguments_output.txt
    - advanced_topics_output.txt

  api_responses:
    - emotion_analysis_response.json
    - entity_extraction_response.json
    - stance_detection_response.json
    - argument_structure_response.json
```

## 5. Test Environment Setup

### 5.1 GPU Test Environment
```bash
# GPU test environment setup
export CUDA_VISIBLE_DEVICES=0
export USE_GPU=true
export GPU_BATCH_SIZE=32

# Install heavy models
uv sync --extra nlp-enhanced
python -m spacy download en_core_web_lg

# Pre-download transformer models
python scripts/download_heavy_models.py
```

### 5.2 CPU-Only Test Environment
```bash
# CPU-only environment
export CUDA_VISIBLE_DEVICES=""
export USE_GPU=false

# Install without GPU support
uv sync --extra nlp-enhanced-cpu
```

### 5.3 Minimal Test Environment
```bash
# Minimal environment (no heavy models)
export SKIP_HEAVY_MODELS=true
uv sync --extra dev
```

## 6. Test Execution Plan

### 6.1 Test Phases

#### Phase A: Unit Testing (Week 1)
1. Test individual analyzers in isolation
2. Verify fallback mechanisms
3. Validate error handling
4. Check memory management

#### Phase B: Integration Testing (Week 2)
1. Test analyzer integration with NLP service
2. Validate CLI commands
3. Test database storage
4. Verify API endpoints

#### Phase C: Performance Testing (Week 3)
1. Benchmark GPU vs CPU performance
2. Test scalability limits
3. Measure memory usage
4. Optimize batch sizes

#### Phase D: Accuracy Validation (Week 4)
1. Validate model accuracy against golden datasets
2. Compare heavy vs light model results
3. Test edge cases
4. Validate political analysis quality

### 6.2 Test Automation
```yaml
# .github/workflows/test-heavy-models.yml
name: Heavy Models Tests

on: [push, pull_request]

jobs:
  test-minimal:
    runs-on: ubuntu-latest
    steps:
      - name: Test without heavy models
        run: |
          export SKIP_HEAVY_MODELS=true
          uv run pytest tests/test_graceful_degradation.py

  test-cpu:
    runs-on: ubuntu-latest
    steps:
      - name: Test with CPU models
        run: |
          uv sync --extra nlp-enhanced-cpu
          uv run pytest tests/test_*_heavy_models.py -m "not gpu"

  test-gpu:
    runs-on: [self-hosted, gpu]
    steps:
      - name: Test with GPU acceleration
        run: |
          uv sync --extra nlp-enhanced
          uv run pytest tests/test_*_heavy_models.py
```

## 7. Success Criteria

### 7.1 Functional Requirements
- [ ] All heavy model analyzers function correctly when available
- [ ] Graceful fallback when models unavailable
- [ ] CLI commands display proper output
- [ ] Database stores all new analysis results
- [ ] No crashes from missing dependencies

### 7.2 Performance Requirements
- [ ] GPU provides ≥2x speedup for batch processing
- [ ] Single document analysis <1s on GPU
- [ ] Batch processing >100 docs/minute on GPU
- [ ] Memory usage <4GB for all models loaded
- [ ] Model switching overhead <0.5s

### 7.3 Accuracy Requirements
- [ ] Entity recognition F1 >0.85
- [ ] Emotion detection accuracy >0.80
- [ ] Stance detection accuracy >0.75
- [ ] Topic coherence score >0.45
- [ ] Argument quality correlation >0.70 with human ratings

### 7.4 Reliability Requirements
- [ ] 99.9% uptime with heavy models
- [ ] Zero data loss during analysis
- [ ] Graceful handling of all error conditions
- [ ] Successful rollback capability
- [ ] No memory leaks after 24h operation

## 8. Risk Mitigation

### 8.1 Technical Risks
1. **GPU Memory Overflow**
   - Mitigation: Dynamic batch size adjustment
   - Fallback: Automatic CPU processing

2. **Model Download Failures**
   - Mitigation: Retry logic with exponential backoff
   - Fallback: Use cached models

3. **Incompatible Dependencies**
   - Mitigation: Strict version pinning
   - Fallback: Isolated environments

### 8.2 Performance Risks
1. **Slow Model Loading**
   - Mitigation: Lazy loading and caching
   - Optimization: Model quantization

2. **High Memory Usage**
   - Mitigation: Model unloading strategy
   - Optimization: Mixed precision inference

## 9. Test Reporting

### 9.1 Test Metrics Dashboard
```yaml
metrics:
  coverage:
    - Line coverage >90%
    - Branch coverage >85%
    - Feature coverage 100%

  performance:
    - GPU speedup ratio
    - Memory usage trends
    - Response time percentiles

  accuracy:
    - Model accuracy scores
    - Fallback usage rate
    - Error rates by type
```

### 9.2 Test Report Template
```markdown
# Phase 5 Heavy Models Test Report

## Executive Summary
- Test execution period: [dates]
- Overall pass rate: X%
- Critical issues: [count]
- Performance improvement: X%

## Detailed Results
[Section for each test category]

## Recommendations
[Action items for improvements]
```

## 10. Acceptance Criteria

The Phase 5 implementation will be considered complete when:

1. All test categories achieve >95% pass rate
2. GPU acceleration provides documented performance improvements
3. Fallback mechanisms work reliably
4. Documentation is complete and accurate
5. No critical or high-severity bugs remain
6. Performance benchmarks meet requirements
7. Accuracy metrics meet thresholds

## Appendix A: Test Commands

```bash
# Run all Phase 5 tests
uv run pytest tests/test_*heavy_models*.py -v

# Run performance benchmarks
uv run python tests/benchmarks/heavy_models_benchmark.py

# Run accuracy validation
uv run python tests/validation/model_accuracy_test.py

# Run integration tests
uv run pytest tests/test_cli_heavy_models.py -v --tb=short

# Generate test report
uv run python scripts/generate_phase5_test_report.py
```

## Appendix B: Troubleshooting Guide

### Common Issues

1. **CUDA out of memory**
   ```bash
   export GPU_BATCH_SIZE=16  # Reduce batch size
   ```

2. **Model download timeout**
   ```bash
   export HF_TIMEOUT=600  # Increase timeout
   ```

3. **Import errors**
   ```bash
   uv sync --extra nlp-enhanced --force
   ```

4. **Slow CPU performance**
   ```bash
   export OMP_NUM_THREADS=8  # Increase CPU threads
   ```
