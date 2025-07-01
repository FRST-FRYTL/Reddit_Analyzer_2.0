"""Add political topic analysis fields

Revision ID: 5453df6b0a6c
Revises: cbe264f3a8c4
Create Date: 2025-07-01 14:24:14.551683

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "5453df6b0a6c"
down_revision: Union[str, Sequence[str], None] = "cbe264f3a8c4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add political topic analysis fields to text_analysis table
    op.add_column(
        "text_analysis", sa.Column("political_topics", sa.JSON(), nullable=True)
    )
    op.add_column(
        "text_analysis", sa.Column("topic_sentiments", sa.JSON(), nullable=True)
    )
    op.add_column(
        "text_analysis",
        sa.Column("discussion_quality_score", sa.Float(), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Remove political topic analysis fields
    op.drop_column("text_analysis", "discussion_quality_score")
    op.drop_column("text_analysis", "topic_sentiments")
    op.drop_column("text_analysis", "political_topics")
