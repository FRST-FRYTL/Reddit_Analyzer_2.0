"""CLI-specific logging configuration."""

import logging
import os


def configure_cli_logging(verbose: bool = False, quiet: bool = False) -> None:
    """Configure logging for CLI commands.

    Args:
        verbose: Enable verbose output (DEBUG level)
        quiet: Suppress most output (ERROR level only)
    """
    # Determine log level
    if quiet:
        level = logging.ERROR
    elif verbose:
        level = logging.DEBUG
    else:
        level = logging.WARNING

    # Configure root logger
    logging.basicConfig(
        level=level,
        format=(
            "%(message)s"
            if not verbose
            else "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        ),
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Suppress noisy loggers
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine.Engine").setLevel(logging.WARNING)
    logging.getLogger("passlib").setLevel(logging.ERROR)
    logging.getLogger("praw").setLevel(logging.WARNING)
    logging.getLogger("prawcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("spacy").setLevel(logging.WARNING)
    logging.getLogger("nltk").setLevel(logging.WARNING)

    # Suppress transformer warnings unless explicitly requested
    if not verbose:
        # These warnings about missing transformers are expected when not installed
        import warnings

        warnings.filterwarnings("ignore", message=".*Transformers.*not available.*")
        warnings.filterwarnings("ignore", message=".*BERT.*not available.*")
        warnings.filterwarnings("ignore", message=".*UMAP.*not available.*")


def suppress_startup_warnings() -> None:
    """Suppress warnings that appear during module imports."""
    import warnings

    # Suppress the specific warnings we see at startup
    warnings.filterwarnings("ignore", category=UserWarning, module="passlib")
    warnings.filterwarnings("ignore", message=".*bcrypt.*version.*")

    # Set environment variable to reduce TensorFlow/PyTorch warnings if they're imported
    os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"
    os.environ["TRANSFORMERS_VERBOSITY"] = "error"
