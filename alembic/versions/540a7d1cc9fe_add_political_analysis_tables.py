"""Add political analysis tables

Revision ID: 540a7d1cc9fe
Revises: 5453df6b0a6c
Create Date: 2025-07-01 14:24:59.651651

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "540a7d1cc9fe"
down_revision: Union[str, Sequence[str], None] = "5453df6b0a6c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create subreddit_topic_profiles table
    op.create_table(
        "subreddit_topic_profiles",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column(
            "subreddit_id",
            sa.Integer(),
            sa.ForeignKey("subreddits.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("analysis_start_date", sa.DateTime(), nullable=False),
        sa.Column("analysis_end_date", sa.DateTime(), nullable=False),
        sa.Column("dominant_topics", sa.JSON(), nullable=True),
        sa.Column("topic_distribution", sa.JSON(), nullable=True),
        sa.Column("topic_sentiment_map", sa.JSON(), nullable=True),
        sa.Column("avg_discussion_quality", sa.Float(), nullable=True),
        sa.Column("civility_score", sa.Float(), nullable=True),
        sa.Column("constructiveness_score", sa.Float(), nullable=True),
        sa.Column("viewpoint_diversity", sa.Float(), nullable=True),
        sa.Column("total_posts_analyzed", sa.Integer(), default=0),
        sa.Column("total_comments_analyzed", sa.Integer(), default=0),
        sa.Column("unique_users_analyzed", sa.Integer(), default=0),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("confidence_level", sa.Float(), nullable=True),
    )

    # Create community_overlaps table
    op.create_table(
        "community_overlaps",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column(
            "subreddit_a_id",
            sa.Integer(),
            sa.ForeignKey("subreddits.id"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "subreddit_b_id",
            sa.Integer(),
            sa.ForeignKey("subreddits.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("user_overlap_count", sa.Integer(), default=0),
        sa.Column("user_overlap_percentage", sa.Float(), nullable=True),
        sa.Column("shared_topics", sa.JSON(), nullable=True),
        sa.Column("cross_posting_count", sa.Integer(), default=0),
        sa.Column("sentiment_differential", sa.Float(), nullable=True),
        sa.Column("analysis_date", sa.DateTime(), nullable=False),
    )

    # Create political_dimensions_analyses table
    op.create_table(
        "political_dimensions_analyses",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column(
            "text_analysis_id",
            sa.Integer(),
            sa.ForeignKey("text_analysis.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("economic_score", sa.Float(), nullable=True),
        sa.Column("economic_confidence", sa.Float(), nullable=True),
        sa.Column("economic_label", sa.String(50), nullable=True),
        sa.Column("economic_evidence", sa.JSON(), nullable=True),
        sa.Column("social_score", sa.Float(), nullable=True),
        sa.Column("social_confidence", sa.Float(), nullable=True),
        sa.Column("social_label", sa.String(50), nullable=True),
        sa.Column("social_evidence", sa.JSON(), nullable=True),
        sa.Column("governance_score", sa.Float(), nullable=True),
        sa.Column("governance_confidence", sa.Float(), nullable=True),
        sa.Column("governance_label", sa.String(50), nullable=True),
        sa.Column("governance_evidence", sa.JSON(), nullable=True),
        sa.Column("analysis_quality", sa.Float(), nullable=True),
        sa.Column("dominant_dimension", sa.String(20), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    # Create subreddit_political_dimensions table
    op.create_table(
        "subreddit_political_dimensions",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column(
            "subreddit_id",
            sa.Integer(),
            sa.ForeignKey("subreddits.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("analysis_start_date", sa.DateTime(), nullable=False),
        sa.Column("analysis_end_date", sa.DateTime(), nullable=False),
        sa.Column("avg_economic_score", sa.Float(), nullable=True),
        sa.Column("economic_std_dev", sa.Float(), nullable=True),
        sa.Column("economic_distribution", sa.JSON(), nullable=True),
        sa.Column("avg_social_score", sa.Float(), nullable=True),
        sa.Column("social_std_dev", sa.Float(), nullable=True),
        sa.Column("social_distribution", sa.JSON(), nullable=True),
        sa.Column("avg_governance_score", sa.Float(), nullable=True),
        sa.Column("governance_std_dev", sa.Float(), nullable=True),
        sa.Column("governance_distribution", sa.JSON(), nullable=True),
        sa.Column("political_diversity_index", sa.Float(), nullable=True),
        sa.Column("dimension_correlation", sa.JSON(), nullable=True),
        sa.Column("political_clusters", sa.JSON(), nullable=True),
        sa.Column("cluster_sizes", sa.JSON(), nullable=True),
        sa.Column("total_posts_analyzed", sa.Integer(), default=0),
        sa.Column("total_comments_analyzed", sa.Integer(), default=0),
        sa.Column("avg_confidence_level", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop tables in reverse order
    op.drop_table("subreddit_political_dimensions")
    op.drop_table("political_dimensions_analyses")
    op.drop_table("community_overlaps")
    op.drop_table("subreddit_topic_profiles")
