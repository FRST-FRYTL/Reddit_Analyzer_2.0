"""
Machine learning predictions database model.

This module defines the database model for storing ML model predictions
including popularity predictions, content classification, and user categorization.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, JSON
from datetime import datetime

from app.database import Base


class MLPrediction(Base):
    """
    Model for storing machine learning model predictions.

    Stores predictions from various ML models including popularity predictors,
    content classifiers, and user behavior models with confidence scores.
    """

    __tablename__ = "ml_predictions"

    id = Column(Integer, primary_key=True, index=True)

    # Model information
    model_name = Column(String(100), nullable=False, index=True)  # Model identifier
    model_version = Column(String(50), nullable=True)  # Model version
    model_type = Column(
        String(50), nullable=False
    )  # classification, regression, clustering

    # Input data reference
    input_data_id = Column(String(255), nullable=False, index=True)  # ID of input data
    input_type = Column(String(50), nullable=False)  # post, comment, user

    # Prediction results
    prediction = Column(JSON, nullable=False)  # Main prediction result
    confidence_score = Column(Float, nullable=True)  # Prediction confidence
    probability_distribution = Column(JSON, nullable=True)  # Class probabilities

    # Feature importance (for explainable AI)
    feature_importance = Column(
        JSON, nullable=True
    )  # Important features for prediction

    # Performance metrics (if ground truth available)
    actual_value = Column(JSON, nullable=True)  # Actual outcome
    prediction_error = Column(Float, nullable=True)  # Error measure

    # Processing metadata
    predicted_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    processing_time_ms = Column(
        Integer, nullable=True
    )  # Processing time in milliseconds

    def __repr__(self):
        return f"<MLPrediction(model={self.model_name}, input={self.input_data_id}, confidence={self.confidence_score})>"
