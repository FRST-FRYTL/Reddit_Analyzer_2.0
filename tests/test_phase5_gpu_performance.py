"""Tests for GPU performance in Phase 5 heavy models."""

import pytest
import time
from unittest.mock import Mock, patch

from reddit_analyzer.processing.sentiment_analyzer import SentimentAnalyzer
from reddit_analyzer.processing.emotion_analyzer import EmotionAnalyzer


class TestGPUDetection:
    """Test GPU detection and initialization."""

    @patch("torch.cuda.is_available")
    def test_cuda_available(self, mock_cuda):
        """Test detection when CUDA is available."""
        mock_cuda.return_value = True

        analyzer = SentimentAnalyzer()
        assert analyzer.device.type == "cuda"

    @patch("torch.cuda.is_available")
    def test_cuda_not_available(self, mock_cuda):
        """Test fallback when CUDA is not available."""
        mock_cuda.return_value = False

        analyzer = SentimentAnalyzer()
        assert analyzer.device.type == "cpu"

    @patch("torch.cuda.is_available")
    @patch("torch.cuda.get_device_properties")
    def test_gpu_memory_info(self, mock_props, mock_cuda):
        """Test GPU memory information retrieval."""
        mock_cuda.return_value = True

        mock_device = Mock()
        mock_device.total_memory = 8 * 1024**3  # 8GB
        mock_props.return_value = mock_device

        analyzer = SentimentAnalyzer()
        # Should initialize without errors
        assert analyzer.device.type == "cuda"


class TestGPUPerformance:
    """Test GPU acceleration performance."""

    def create_test_texts(self, count=100):
        """Create test texts for benchmarking."""
        texts = [
            "This is a positive sentiment text about great policies.",
            "This is a negative sentiment text about bad decisions.",
            "This is a neutral statement about current events.",
        ]
        return texts * (count // 3)

    @pytest.mark.skipif(
        not pytest.importorskip("torch").cuda.is_available(), reason="GPU not available"
    )
    def test_gpu_vs_cpu_sentiment(self):
        """Compare GPU vs CPU performance for sentiment analysis."""
        texts = self.create_test_texts(300)

        # Test CPU performance
        with patch("torch.cuda.is_available", return_value=False):
            cpu_analyzer = SentimentAnalyzer()

            cpu_start = time.time()
            cpu_results = []
            for text in texts:
                result = cpu_analyzer.analyze_sentiment(text)
                cpu_results.append(result)
            cpu_time = time.time() - cpu_start

        # Test GPU performance
        gpu_analyzer = SentimentAnalyzer()

        gpu_start = time.time()
        gpu_results = []
        for text in texts:
            result = gpu_analyzer.analyze_sentiment(text)
            gpu_results.append(result)
        gpu_time = time.time() - gpu_start

        # GPU should be faster for batch processing
        print(f"CPU time: {cpu_time:.2f}s, GPU time: {gpu_time:.2f}s")
        # Note: In mock testing, times might be similar

    @patch("reddit_analyzer.processing.emotion_analyzer.pipeline")
    def test_batch_processing_optimization(self, mock_pipeline):
        """Test batch processing optimization."""
        # Mock the pipeline
        mock_model = Mock()
        mock_model.return_value = [
            {"label": "joy", "score": 0.8},
            {"label": "anger", "score": 0.2},
        ]
        mock_pipeline.return_value = mock_model

        analyzer = EmotionAnalyzer()
        texts = self.create_test_texts(32)  # One batch

        # Process as batch
        batch_start = time.time()
        results = analyzer.analyze_batch(texts)
        _ = time.time() - batch_start  # Track time but not used in assertion

        assert len(results) == 32
        assert all("emotions" in r for r in results)

    def test_memory_efficient_processing(self):
        """Test memory-efficient processing of large batches."""
        analyzer = EmotionAnalyzer()

        # Create large batch
        large_texts = self.create_test_texts(1000)

        # Process in chunks to avoid memory issues
        chunk_size = 32
        results = []

        for i in range(0, len(large_texts), chunk_size):
            chunk = large_texts[i : i + chunk_size]
            chunk_results = analyzer.analyze_batch(chunk)
            results.extend(chunk_results)

        assert len(results) == len(large_texts)


class TestGPUFallback:
    """Test GPU fallback mechanisms."""

    @patch("torch.cuda.is_available")
    def test_cuda_out_of_memory_fallback(self, mock_cuda):
        """Test fallback when GPU runs out of memory."""
        mock_cuda.return_value = True

        analyzer = SentimentAnalyzer()

        # Simulate OOM error
        with patch.object(analyzer, "transformer_pipeline") as mock_pipeline:
            mock_pipeline.side_effect = RuntimeError("CUDA out of memory")

            # Should fall back gracefully
            result = analyzer.analyze_sentiment("Test text")
            assert result is not None
            assert "error" not in result

    def test_model_loading_fallback(self):
        """Test fallback when model fails to load on GPU."""
        with patch(
            "reddit_analyzer.processing.emotion_analyzer.pipeline"
        ) as mock_pipeline:
            mock_pipeline.side_effect = Exception("Failed to load model")

            analyzer = EmotionAnalyzer()
            assert analyzer.model is None
            assert analyzer.available is False

    @patch("torch.cuda.is_available")
    def test_dynamic_batch_size_adjustment(self, mock_cuda):
        """Test dynamic batch size adjustment for GPU memory."""
        mock_cuda.return_value = True

        analyzer = EmotionAnalyzer()

        # Test different batch sizes
        for batch_size in [8, 16, 32, 64]:
            texts = self.create_test_texts(batch_size)
            results = analyzer.analyze_batch(texts)
            assert len(results) == batch_size


@pytest.mark.benchmark
class TestGPUBenchmarks:
    """Benchmarks for GPU acceleration."""

    def test_sentiment_throughput(self, benchmark):
        """Benchmark sentiment analysis throughput."""
        analyzer = SentimentAnalyzer()
        texts = ["This is a test sentence for sentiment analysis."] * 10

        def process_texts():
            results = []
            for text in texts:
                result = analyzer.analyze_sentiment(text)
                results.append(result)
            return results

        results = benchmark(process_texts)
        assert len(results) == 10

    def test_emotion_throughput(self, benchmark):
        """Benchmark emotion detection throughput."""
        analyzer = EmotionAnalyzer()
        text = "I am very happy about this amazing development!"

        result = benchmark(analyzer.analyze_emotions, text)
        assert isinstance(result, dict)

    def test_mixed_precision_performance(self):
        """Test mixed precision inference performance."""
        # This would test FP16 vs FP32 performance
        # Requires actual GPU and torch.cuda.amp
        pass


class TestGPUMonitoring:
    """Test GPU monitoring and metrics."""

    @patch("torch.cuda.is_available")
    @patch("torch.cuda.memory_allocated")
    @patch("torch.cuda.get_device_properties")
    def test_gpu_memory_monitoring(self, mock_props, mock_memory, mock_cuda):
        """Test GPU memory usage monitoring."""
        mock_cuda.return_value = True
        mock_memory.return_value = 2 * 1024**3  # 2GB used

        mock_device = Mock()
        mock_device.total_memory = 8 * 1024**3  # 8GB total
        mock_props.return_value = mock_device

        from reddit_analyzer.utils.gpu_monitor import log_gpu_metrics

        # Should log without errors
        log_gpu_metrics()

    def test_performance_metrics_collection(self):
        """Test collection of performance metrics."""
        from reddit_analyzer.utils.metrics import ProcessingMetrics

        metrics = ProcessingMetrics(
            texts_per_second=100.5,
            gpu_utilization=0.85,
            memory_usage=0.45,
            model_load_time=2.3,
            batch_processing_time=0.05,
        )

        assert metrics.texts_per_second == 100.5
        assert metrics.gpu_utilization == 0.85
