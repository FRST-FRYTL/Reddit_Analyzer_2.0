"""Test data fixtures for Phase 4D tests."""

import pytest
from datetime import datetime, timedelta
from reddit_analyzer.models import (
    Subreddit,
    Post,
    Comment,
    User,
    UserRole,
    TextAnalysis,
)
from reddit_analyzer.database import get_session
import random


@pytest.fixture
def authenticated_cli():
    """Fixture that ensures real authentication before tests."""
    from reddit_analyzer.cli.utils.auth_manager import cli_auth

    # Login with test credentials
    cli_auth.login("user_test", "user123")
    yield
    # Optionally logout after tests
    cli_auth.logout()


@pytest.fixture
def political_test_data():
    """Create comprehensive political test data."""
    return {
        "subreddits": [
            {
                "name": "test_politics",
                "display_name": "Test Politics",
                "description": "Test political subreddit for analysis",
                "subscribers": 50000,
                "posts": 50,
                "topics": [
                    "healthcare",
                    "economy",
                    "climate",
                    "immigration",
                    "education",
                ],
                "sentiment_distribution": {
                    "positive": 0.3,
                    "negative": 0.4,
                    "neutral": 0.3,
                },
            },
            {
                "name": "test_conservative",
                "display_name": "Test Conservative",
                "description": "Conservative political discussion",
                "subscribers": 30000,
                "posts": 30,
                "topics": ["taxes", "gun_rights", "border_security", "free_market"],
                "sentiment_distribution": {
                    "positive": 0.4,
                    "negative": 0.3,
                    "neutral": 0.3,
                },
            },
            {
                "name": "test_progressive",
                "display_name": "Test Progressive",
                "description": "Progressive political discussion",
                "subscribers": 25000,
                "posts": 25,
                "topics": ["universal_healthcare", "climate_action", "social_justice"],
                "sentiment_distribution": {
                    "positive": 0.35,
                    "negative": 0.35,
                    "neutral": 0.3,
                },
            },
        ]
    }


def generate_political_content(topic):
    """Generate realistic political content for NLP analysis."""
    templates = {
        "healthcare": "The healthcare system needs comprehensive reform. We should consider universal coverage to ensure all citizens have access to medical care. Current costs are unsustainable and bankrupting families.",
        "economy": "Economic policies must balance growth with sustainability. Tax reform is needed to ensure fair contribution from all income levels. Job creation and wage growth are critical priorities.",
        "climate": "Climate change requires immediate action through policy changes. We need investment in renewable energy and reduction of carbon emissions. The science is clear and action is urgent.",
        "immigration": "Immigration reform should address both security and humanitarian concerns. We need a path to citizenship for law-abiding residents and better border management systems.",
        "education": "Education funding needs to be increased to ensure quality schools for all children. Teacher salaries must be competitive and resources adequate.",
        "taxes": "Tax rates should encourage business growth while ensuring adequate government revenue. We need to simplify the tax code and close loopholes.",
        "gun_rights": "The Second Amendment protects individual rights while allowing for reasonable regulations. We need to balance safety with constitutional freedoms.",
        "border_security": "Border security is essential for national sovereignty. We need effective enforcement combined with humane treatment of asylum seekers.",
        "free_market": "Free market principles drive innovation and prosperity. Government regulation should be minimal and focused on preventing abuse.",
        "universal_healthcare": "Healthcare is a human right that should be guaranteed to all citizens. A single-payer system would reduce costs and improve outcomes.",
        "climate_action": "We need a Green New Deal to transform our economy and save the planet. Fossil fuel companies must be held accountable for environmental damage.",
        "social_justice": "Systemic inequalities require comprehensive reform. We must address racial, economic, and social disparities through policy action.",
    }
    return templates.get(
        topic,
        f"This is a detailed political discussion about {topic} and its implications for society.",
    )


@pytest.fixture
def test_database_with_data(authenticated_cli, political_test_data):
    """Fixture that creates test data in database."""
    with get_session() as session:
        # Create test users
        users = []
        for i in range(10):
            user = User(
                username=f"test_user_{i}",
                created_utc=datetime.utcnow() - timedelta(days=30),
                role=UserRole.USER,
            )
            users.append(user)
            session.add(user)

        session.flush()

        # Create subreddits and posts
        for sub_data in political_test_data["subreddits"]:
            # Create subreddit
            subreddit = Subreddit(
                name=sub_data["name"],
                display_name=sub_data["display_name"],
                description=sub_data["description"],
                subscribers=sub_data["subscribers"],
                created_utc=datetime.utcnow() - timedelta(days=365),
            )
            session.add(subreddit)
            session.flush()

            # Create posts for this subreddit
            for i in range(sub_data["posts"]):
                topic = sub_data["topics"][i % len(sub_data["topics"])]

                # Determine sentiment based on distribution
                rand = random.random()
                if rand < sub_data["sentiment_distribution"]["positive"]:
                    sentiment_score = random.uniform(0.1, 0.5)
                elif rand < (
                    sub_data["sentiment_distribution"]["positive"]
                    + sub_data["sentiment_distribution"]["negative"]
                ):
                    sentiment_score = random.uniform(-0.5, -0.1)
                else:
                    sentiment_score = random.uniform(-0.1, 0.1)

                post = Post(
                    id=f"{sub_data['name']}_post_{i}",
                    title=f"Discussion about {topic} - Post {i}",
                    selftext=generate_political_content(topic),
                    author_id=users[i % len(users)].id,
                    subreddit_id=subreddit.id,
                    score=100 + (i * 10),
                    num_comments=5 + i,
                    created_utc=datetime.utcnow() - timedelta(days=i % 30),
                    upvote_ratio=0.5 + (sentiment_score * 0.3),
                )
                session.add(post)
                session.flush()

                # Create text analysis for the post
                analysis = TextAnalysis(
                    post_id=post.id,
                    sentiment_score=sentiment_score,
                    sentiment_label=(
                        "positive"
                        if sentiment_score > 0.1
                        else ("negative" if sentiment_score < -0.1 else "neutral")
                    ),
                    keywords=[topic, "politics", "policy", "discussion"],
                    topics=[{"topic": topic, "score": 0.8}],
                    entities=[
                        {"text": topic.replace("_", " ").title(), "type": "TOPIC"}
                    ],
                    processed_at=datetime.utcnow(),
                )
                session.add(analysis)

                # Create comments for posts
                for j in range(min(5, i + 1)):
                    comment = Comment(
                        id=f"{post.id}_comment_{j}",
                        body=f"I agree with the points about {topic}. Here's my perspective...",
                        author_id=users[(i + j) % len(users)].id,
                        post_id=post.id,
                        score=10 + j,
                        created_utc=post.created_utc + timedelta(hours=j + 1),
                    )
                    session.add(comment)

        session.commit()

    yield

    # Cleanup
    with get_session() as session:
        # Delete in reverse order of dependencies
        session.query(TextAnalysis).filter(
            (TextAnalysis.post_id.like("%test_%"))
            | (TextAnalysis.comment_id.like("%test_%"))
        ).delete(synchronize_session=False)
        session.query(Comment).filter(Comment.id.like("%test_%")).delete(
            synchronize_session=False
        )
        session.query(Post).filter(Post.id.like("%test_%")).delete(
            synchronize_session=False
        )
        session.query(Subreddit).filter(Subreddit.name.like("test_%")).delete(
            synchronize_session=False
        )
        session.query(User).filter(User.username.like("test_user_%")).delete(
            synchronize_session=False
        )
        session.commit()


def create_political_test_posts(count=10):
    """Helper to create test posts with known political content."""
    posts = []
    topics = ["healthcare", "taxes", "immigration", "climate", "education"]

    for i in range(count):
        topic = topics[i % len(topics)]
        posts.append(
            {
                "id": f"test_post_{i}",
                "title": f"Discussion about {topic}",
                "selftext": generate_political_content(topic),
                "score": 100 + (i * 10),
                "num_comments": 5 + i,
                "created_utc": datetime.utcnow() - timedelta(days=i),
            }
        )

    return posts
