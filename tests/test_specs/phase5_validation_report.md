# Phase 5 Heavy Models Validation Report

**Generated**: 2025-07-02T17:07:46.442469

## Environment

- **Python**: 3.12.3
- **CUDA Available**: True
- **GPU**: NVIDIA GeForce RTX 3070

### Installed Packages
- ✓ **spacy**: 3.8.7
- ✓ **transformers**: 4.53.0
- ✓ **torch**: 2.7.1+cu126
- ✗ **bertopic**: Not installed

### SpaCy Models

## Test Results

### Basic Functionality (Required)
- ❌ Sentiment Analysis
- ❌ Topic Modeling
- ❌ Keyword Extraction

### Heavy Models (Optional)
- **Entity Extraction**: Available ❌, Functional ❌
- **Emotion Detection**: Available ❌, Functional ❌
- **Stance Detection**: Available ❌, Functional ❌
- **Argument Mining**: Available ❌, Functional ❌
- **Advanced Topics**: Available ❌, Functional ❌

### GPU Acceleration
- GPU Detected: ✅
- GPU Functional: ❌

### Fallback Mechanisms
- All Fallbacks Work: ✅
- Clear Messages: ✅
- No Crashes: ❌

### CLI Commands
- Commands Available: 5
- Commands Functional: 0

## Summary

- **Basic Functionality**: False
- **Heavy Models Available**: 0/5
- **Heavy Models Functional**: 0/5
- **Gpu Acceleration**: False
- **Fallbacks Working**: True
- **Cli Commands**: 0/5

## Recommendations

- Install missing packages for full functionality: bertopic
- Install spaCy language models: `python -m spacy download en_core_web_lg`
