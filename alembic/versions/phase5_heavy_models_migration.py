"""Add Phase 5 heavy models support

Revision ID: phase5_heavy_models
Revises: 540a7d1cc9fe
Create Date: 2025-07-02 14:30:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "phase5_heavy_models"
down_revision: Union[str, Sequence[str], None] = "540a7d1cc9fe"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add new columns to text_analysis table
    op.add_column(
        "text_analysis", sa.Column("entity_sentiment", sa.JSON(), nullable=True)
    )
    op.add_column(
        "text_analysis", sa.Column("argument_structure", sa.JSON(), nullable=True)
    )
    op.add_column(
        "text_analysis", sa.Column("emotion_intensity", sa.JSON(), nullable=True)
    )
    op.add_column(
        "text_analysis", sa.Column("stance_results", sa.JSON(), nullable=True)
    )

    # Create advanced_topics table
    op.create_table(
        "advanced_topics",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("topic_id", sa.Integer(), nullable=False),
        sa.Column("topic_label", sa.String(length=255), nullable=True),
        sa.Column("subreddit_name", sa.String(length=255), nullable=True),
        sa.Column("model_type", sa.String(length=50), nullable=False),
        sa.Column("model_version", sa.String(length=50), nullable=True),
        sa.Column("top_words", sa.JSON(), nullable=False),
        sa.Column("representative_docs", sa.JSON(), nullable=True),
        sa.Column("embedding", sa.JSON(), nullable=True),
        sa.Column("document_count", sa.Integer(), nullable=False),
        sa.Column("coherence_score", sa.Float(), nullable=True),
        sa.Column("diversity_score", sa.Float(), nullable=True),
        sa.Column("parent_topic_id", sa.Integer(), nullable=True),
        sa.Column("hierarchy_level", sa.Integer(), nullable=True),
        sa.Column("time_period_start", sa.DateTime(), nullable=True),
        sa.Column("time_period_end", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["subreddit_name"],
            ["subreddits.name"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_advanced_topics_topic_id"),
        "advanced_topics",
        ["topic_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_advanced_topics_subreddit_name"),
        "advanced_topics",
        ["subreddit_name"],
        unique=False,
    )

    # Create topic_evolution table
    op.create_table(
        "topic_evolution",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("topic_id", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("time_bin", sa.Integer(), nullable=False),
        sa.Column("document_count", sa.Integer(), nullable=False),
        sa.Column("relative_frequency", sa.Float(), nullable=False),
        sa.Column("word_changes", sa.JSON(), nullable=True),
        sa.Column("sentiment_shift", sa.Float(), nullable=True),
        sa.Column("merged_with", sa.JSON(), nullable=True),
        sa.Column("split_into", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["topic_id"],
            ["advanced_topics.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_topic_evolution_timestamp"),
        "topic_evolution",
        ["timestamp"],
        unique=False,
    )

    # Create argument_structures table
    op.create_table(
        "argument_structures",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("post_id", sa.String(length=255), nullable=True),
        sa.Column("comment_id", sa.String(length=255), nullable=True),
        sa.Column("components", sa.JSON(), nullable=False),
        sa.Column("relationships", sa.JSON(), nullable=True),
        sa.Column("overall_quality", sa.Float(), nullable=True),
        sa.Column("logical_flow_score", sa.Float(), nullable=True),
        sa.Column("evidence_support_score", sa.Float(), nullable=True),
        sa.Column("balance_score", sa.Float(), nullable=True),
        sa.Column("clarity_score", sa.Float(), nullable=True),
        sa.Column("main_claims", sa.JSON(), nullable=True),
        sa.Column("conclusions", sa.JSON(), nullable=True),
        sa.Column("fallacies_detected", sa.JSON(), nullable=True),
        sa.Column("processed_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["post_id"],
            ["posts.id"],
        ),
        sa.ForeignKeyConstraint(
            ["comment_id"],
            ["comments.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_argument_structures_post_id"),
        "argument_structures",
        ["post_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_argument_structures_comment_id"),
        "argument_structures",
        ["comment_id"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop new tables
    op.drop_index(
        op.f("ix_argument_structures_comment_id"), table_name="argument_structures"
    )
    op.drop_index(
        op.f("ix_argument_structures_post_id"), table_name="argument_structures"
    )
    op.drop_table("argument_structures")

    op.drop_index(op.f("ix_topic_evolution_timestamp"), table_name="topic_evolution")
    op.drop_table("topic_evolution")

    op.drop_index(
        op.f("ix_advanced_topics_subreddit_name"), table_name="advanced_topics"
    )
    op.drop_index(op.f("ix_advanced_topics_topic_id"), table_name="advanced_topics")
    op.drop_table("advanced_topics")

    # Remove columns from text_analysis
    op.drop_column("text_analysis", "stance_results")
    op.drop_column("text_analysis", "emotion_intensity")
    op.drop_column("text_analysis", "argument_structure")
    op.drop_column("text_analysis", "entity_sentiment")
