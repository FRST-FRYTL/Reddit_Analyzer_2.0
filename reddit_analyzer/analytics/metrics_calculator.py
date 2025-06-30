"""
Metrics calculation module for Reddit data analysis.

This module provides comprehensive metrics calculation for posts, comments,
users, and subreddits including engagement, influence, quality, and activity metrics.
"""

import logging
from typing import Dict, List, Optional, Any
import numpy as np
from datetime import datetime, timedelta
import math

logger = logging.getLogger(__name__)


class MetricsCalculator:
    """
    Comprehensive metrics calculation system for Reddit data.

    Calculates engagement metrics, influence scores, content quality metrics,
    user activity scores, and subreddit health indicators.
    """

    def __init__(self):
        """Initialize the metrics calculator."""
        # Weighting factors for different metrics
        self.engagement_weights = {
            "score": 0.4,
            "comments": 0.3,
            "upvote_ratio": 0.2,
            "awards": 0.1,
        }

        self.quality_weights = {
            "engagement": 0.3,
            "content_length": 0.2,
            "readability": 0.2,
            "sentiment": 0.15,
            "originality": 0.15,
        }

        logger.info("Metrics calculator initialized")

    def calculate_post_metrics(
        self, posts: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Calculate comprehensive metrics for Reddit posts.

        Args:
            posts: List of post dictionaries

        Returns:
            List of posts with calculated metrics
        """
        if not posts:
            return []

        enhanced_posts = []

        for post in posts:
            metrics = {
                "post_id": post.get("id"),
                "engagement_score": self._calculate_engagement_score(post),
                "virality_score": self._calculate_virality_score(post),
                "quality_score": self._calculate_content_quality_score(post),
                "controversy_score": self._calculate_controversy_score(post),
                "reach_potential": self._calculate_reach_potential(post),
                "interaction_rate": self._calculate_interaction_rate(post),
                "content_metrics": self._calculate_content_metrics(post),
                "temporal_metrics": self._calculate_temporal_metrics(post),
            }

            # Combine original post data with metrics
            enhanced_post = {**post, "calculated_metrics": metrics}
            enhanced_posts.append(enhanced_post)

        return enhanced_posts

    def calculate_user_metrics(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate comprehensive metrics for a Reddit user.

        Args:
            user_data: Dictionary containing user data including posts and comments

        Returns:
            Dictionary with calculated user metrics
        """
        posts = user_data.get("posts", [])
        comments = user_data.get("comments", [])
        user_info = user_data.get("user_info", {})

        metrics = {
            "user_id": user_info.get("id"),
            "activity_score": self._calculate_user_activity_score(
                posts, comments, user_info
            ),
            "influence_score": self._calculate_user_influence_score(
                posts, comments, user_info
            ),
            "engagement_metrics": self._calculate_user_engagement_metrics(
                posts, comments
            ),
            "content_quality_metrics": self._calculate_user_content_quality(
                posts, comments
            ),
            "behavioral_metrics": self._calculate_user_behavioral_metrics(
                posts, comments, user_info
            ),
            "reputation_score": self._calculate_user_reputation_score(
                user_info, posts, comments
            ),
            "consistency_metrics": self._calculate_user_consistency_metrics(
                posts, comments
            ),
            "community_metrics": self._calculate_user_community_metrics(
                posts, comments
            ),
        }

        return metrics

    def calculate_subreddit_metrics(
        self, subreddit_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive metrics for a subreddit.

        Args:
            subreddit_data: Dictionary containing subreddit data

        Returns:
            Dictionary with calculated subreddit metrics
        """
        posts = subreddit_data.get("posts", [])
        comments = subreddit_data.get("comments", [])
        subreddit_info = subreddit_data.get("subreddit_info", {})

        metrics = {
            "subreddit_name": subreddit_info.get("display_name"),
            "health_score": self._calculate_subreddit_health_score(
                posts, comments, subreddit_info
            ),
            "activity_metrics": self._calculate_subreddit_activity_metrics(
                posts, comments
            ),
            "engagement_metrics": self._calculate_subreddit_engagement_metrics(
                posts, comments
            ),
            "growth_metrics": self._calculate_subreddit_growth_metrics(
                posts, comments, subreddit_info
            ),
            "content_diversity": self._calculate_content_diversity_metrics(posts),
            "moderation_metrics": self._calculate_moderation_metrics(posts, comments),
            "community_sentiment": self._calculate_community_sentiment_metrics(
                posts, comments
            ),
            "influence_distribution": self._calculate_influence_distribution(
                posts, comments
            ),
        }

        return metrics

    def _calculate_engagement_score(self, post: Dict[str, Any]) -> float:
        """Calculate engagement score for a post."""
        score = post.get("score", 0)
        num_comments = post.get("num_comments", 0)
        upvote_ratio = post.get("upvote_ratio", 0.5)
        awards = post.get("total_awards_received", 0)

        # Normalize metrics
        normalized_score = math.log1p(max(0, score)) / 10
        normalized_comments = math.log1p(num_comments) / 5
        normalized_ratio = upvote_ratio
        normalized_awards = math.log1p(awards) / 3

        # Calculate weighted engagement score
        engagement_score = (
            self.engagement_weights["score"] * normalized_score
            + self.engagement_weights["comments"] * normalized_comments
            + self.engagement_weights["upvote_ratio"] * normalized_ratio
            + self.engagement_weights["awards"] * normalized_awards
        )

        return min(1.0, engagement_score)

    def _calculate_virality_score(self, post: Dict[str, Any]) -> float:
        """Calculate virality score based on rapid engagement growth."""
        score = post.get("score", 0)
        num_comments = post.get("num_comments", 0)
        created_utc = post.get("created_utc")

        if not created_utc:
            return 0.0

        # Calculate time since posting (in hours)
        if isinstance(created_utc, (int, float)):
            post_time = datetime.fromtimestamp(created_utc)
        else:
            post_time = created_utc

        hours_since_post = (datetime.now() - post_time).total_seconds() / 3600

        if hours_since_post <= 0:
            return 0.0

        # Calculate engagement rate per hour
        engagement_per_hour = (score + num_comments * 2) / max(hours_since_post, 0.1)

        # Apply logarithmic scaling
        virality_score = math.log1p(engagement_per_hour) / 10

        return min(1.0, virality_score)

    def _calculate_content_quality_score(self, post: Dict[str, Any]) -> float:
        """Calculate content quality score."""
        # Get text analysis results if available
        text_analysis = post.get("text_analysis", {})
        sentiment = post.get("sentiment", {})

        # Content length factor
        title_length = len(post.get("title", ""))
        content_length = len(post.get("selftext", "") or "")

        length_score = min(1.0, (title_length + content_length) / 1000)

        # Readability score
        readability = text_analysis.get("readability", {})
        readability_score = 1.0 - min(1.0, readability.get("readability_score", 0.5))

        # Sentiment quality (prefer neutral to positive content)
        sentiment_score = 0.5  # Default neutral
        if sentiment:
            compound = sentiment.get("compound_score", 0)
            sentiment_score = 0.7 if compound > 0 else 0.3 if compound < -0.5 else 0.5

        # Engagement quality
        engagement_score = self._calculate_engagement_score(post)

        # Originality (inverse of common patterns)
        originality_score = 0.5  # Default, would need more sophisticated analysis

        # Calculate weighted quality score
        quality_score = (
            self.quality_weights["engagement"] * engagement_score
            + self.quality_weights["content_length"] * length_score
            + self.quality_weights["readability"] * readability_score
            + self.quality_weights["sentiment"] * sentiment_score
            + self.quality_weights["originality"] * originality_score
        )

        return quality_score

    def _calculate_controversy_score(self, post: Dict[str, Any]) -> float:
        """Calculate controversy score based on voting patterns."""
        upvote_ratio = post.get("upvote_ratio", 0.5)
        score = post.get("score", 0)
        num_comments = post.get("num_comments", 0)

        # Controversy is high when upvote ratio is close to 0.5 and there's high engagement
        ratio_controversy = 1.0 - abs(upvote_ratio - 0.5) * 2
        engagement_factor = min(1.0, (score + num_comments) / 100)

        controversy_score = ratio_controversy * engagement_factor

        return controversy_score

    def _calculate_reach_potential(self, post: Dict[str, Any]) -> float:
        """Calculate potential reach based on subreddit and engagement."""
        # This would need subreddit subscriber data for accurate calculation
        subreddit = post.get("subreddit", {})
        subscribers = (
            subreddit.get("subscribers", 100000)
            if isinstance(subreddit, dict)
            else 100000
        )

        engagement_score = self._calculate_engagement_score(post)

        # Estimate reach as percentage of subreddit subscribers
        base_reach = min(
            0.1, subscribers / 1000000
        )  # Larger subs have lower reach per post
        reach_potential = base_reach * (
            1 + engagement_score * 4
        )  # High engagement increases reach

        return min(1.0, reach_potential)

    def _calculate_interaction_rate(self, post: Dict[str, Any]) -> float:
        """Calculate interaction rate (comments per score)."""
        score = max(1, post.get("score", 1))
        num_comments = post.get("num_comments", 0)

        interaction_rate = num_comments / score

        # Normalize to 0-1 scale (high interaction rate is ~0.1)
        normalized_rate = min(1.0, interaction_rate * 10)

        return normalized_rate

    def _calculate_content_metrics(self, post: Dict[str, Any]) -> Dict[str, float]:
        """Calculate detailed content metrics."""
        title = post.get("title", "")
        content = post.get("selftext", "") or ""

        return {
            "title_length": len(title),
            "content_length": len(content),
            "title_word_count": len(title.split()),
            "content_word_count": len(content.split()),
            "has_media": 1.0 if post.get("url", "").startswith("http") else 0.0,
            "is_self_post": 1.0 if post.get("is_self", True) else 0.0,
            "has_flair": 1.0 if post.get("link_flair_text") else 0.0,
        }

    def _calculate_temporal_metrics(self, post: Dict[str, Any]) -> Dict[str, float]:
        """Calculate time-based metrics."""
        created_utc = post.get("created_utc")

        if not created_utc:
            return {}

        if isinstance(created_utc, (int, float)):
            post_time = datetime.fromtimestamp(created_utc)
        else:
            post_time = created_utc

        now = datetime.now()
        age_hours = (now - post_time).total_seconds() / 3600

        return {
            "age_hours": age_hours,
            "age_days": age_hours / 24,
            "hour_of_day": post_time.hour,
            "day_of_week": post_time.weekday(),
            "is_weekend": 1.0 if post_time.weekday() >= 5 else 0.0,
            "is_business_hours": 1.0 if 9 <= post_time.hour <= 17 else 0.0,
        }

    def _calculate_user_activity_score(
        self, posts: List[Dict], comments: List[Dict], user_info: Dict[str, Any]
    ) -> float:
        """Calculate user activity score."""
        total_posts = len(posts)
        total_comments = len(comments)

        # Account age
        created_utc = user_info.get("created_utc")
        if created_utc:
            if isinstance(created_utc, (int, float)):
                account_age_days = (
                    datetime.now() - datetime.fromtimestamp(created_utc)
                ).days
            else:
                account_age_days = (datetime.now() - created_utc).days
        else:
            account_age_days = 365  # Default to 1 year

        account_age_days = max(1, account_age_days)

        # Activity per day
        posts_per_day = total_posts / account_age_days
        comments_per_day = total_comments / account_age_days

        # Recent activity (last 30 days)
        recent_cutoff = datetime.now() - timedelta(days=30)
        recent_posts = sum(
            1
            for p in posts
            if self._parse_timestamp(p.get("created_utc")) > recent_cutoff
        )
        recent_comments = sum(
            1
            for c in comments
            if self._parse_timestamp(c.get("created_utc")) > recent_cutoff
        )

        # Calculate activity score
        base_activity = math.log1p(posts_per_day + comments_per_day) / 5
        recent_activity = math.log1p(recent_posts + recent_comments) / 20

        activity_score = min(1.0, base_activity * 0.7 + recent_activity * 0.3)

        return activity_score

    def _calculate_user_influence_score(
        self, posts: List[Dict], comments: List[Dict], user_info: Dict[str, Any]
    ) -> float:
        """Calculate user influence score."""
        # Karma metrics
        comment_karma = user_info.get("comment_karma", 0)
        link_karma = user_info.get("link_karma", 0)
        total_karma = comment_karma + link_karma

        # Average scores
        post_scores = [p.get("score", 0) for p in posts]
        comment_scores = [c.get("score", 0) for c in comments]

        avg_post_score = np.mean(post_scores) if post_scores else 0
        avg_comment_score = np.mean(comment_scores) if comment_scores else 0

        # Awards received
        total_awards = sum(p.get("total_awards_received", 0) for p in posts)

        # Calculate influence components
        karma_influence = math.log1p(total_karma) / 15
        score_influence = math.log1p(avg_post_score + avg_comment_score) / 10
        award_influence = math.log1p(total_awards) / 5

        influence_score = min(
            1.0, karma_influence * 0.5 + score_influence * 0.3 + award_influence * 0.2
        )

        return influence_score

    def _calculate_user_engagement_metrics(
        self, posts: List[Dict], comments: List[Dict]
    ) -> Dict[str, float]:
        """Calculate user engagement metrics."""
        # Comments per post ratio
        comment_post_ratio = len(comments) / max(len(posts), 1)

        # Average engagement received
        avg_post_comments = (
            np.mean([p.get("num_comments", 0) for p in posts]) if posts else 0
        )
        avg_post_score = np.mean([p.get("score", 0) for p in posts]) if posts else 0
        avg_comment_score = (
            np.mean([c.get("score", 0) for c in comments]) if comments else 0
        )

        # Response generation (posts that get comments)
        posts_with_responses = sum(1 for p in posts if p.get("num_comments", 0) > 0)
        response_rate = posts_with_responses / max(len(posts), 1)

        return {
            "comment_post_ratio": comment_post_ratio,
            "avg_post_comments": avg_post_comments,
            "avg_post_score": avg_post_score,
            "avg_comment_score": avg_comment_score,
            "response_rate": response_rate,
            "total_interactions": len(posts) + len(comments),
        }

    def _calculate_user_content_quality(
        self, posts: List[Dict], comments: List[Dict]
    ) -> Dict[str, float]:
        """Calculate user content quality metrics."""
        # High-scoring content
        high_score_posts = sum(1 for p in posts if p.get("score", 0) > 100)
        high_score_comments = sum(1 for c in comments if c.get("score", 0) > 10)

        # Quality ratio
        quality_post_ratio = high_score_posts / max(len(posts), 1)
        quality_comment_ratio = high_score_comments / max(len(comments), 1)

        # Content length diversity
        post_lengths = [len(p.get("selftext", "") or "") for p in posts]
        avg_post_length = np.mean(post_lengths) if post_lengths else 0

        comment_lengths = [len(c.get("body", "") or "") for c in comments]
        avg_comment_length = np.mean(comment_lengths) if comment_lengths else 0

        return {
            "quality_post_ratio": quality_post_ratio,
            "quality_comment_ratio": quality_comment_ratio,
            "avg_post_length": avg_post_length,
            "avg_comment_length": avg_comment_length,
            "content_diversity_score": min(
                1.0, (avg_post_length + avg_comment_length) / 1000
            ),
        }

    def _calculate_user_behavioral_metrics(
        self, posts: List[Dict], comments: List[Dict], user_info: Dict[str, Any]
    ) -> Dict[str, float]:
        """Calculate user behavioral pattern metrics."""
        # Posting frequency patterns
        all_timestamps = []
        for post in posts:
            ts = self._parse_timestamp(post.get("created_utc"))
            if ts:
                all_timestamps.append(ts)
        for comment in comments:
            ts = self._parse_timestamp(comment.get("created_utc"))
            if ts:
                all_timestamps.append(ts)

        # Activity time patterns
        hours = [ts.hour for ts in all_timestamps]
        weekdays = [ts.weekday() for ts in all_timestamps]

        # Calculate consistency (lower std = more consistent)
        hour_consistency = 1.0 - (np.std(hours) / 12) if hours else 0.5

        # Peak activity time
        peak_hour = max(set(hours), key=hours.count) if hours else 12

        # Weekend vs weekday activity
        weekend_activity = sum(1 for wd in weekdays if wd >= 5)
        weekend_ratio = weekend_activity / max(len(weekdays), 1)

        return {
            "hour_consistency": hour_consistency,
            "peak_activity_hour": peak_hour,
            "weekend_activity_ratio": weekend_ratio,
            "activity_spread": len(set(hours)) / 24 if hours else 0,
            "posting_regularity": self._calculate_posting_regularity(all_timestamps),
        }

    def _calculate_user_reputation_score(
        self, user_info: Dict[str, Any], posts: List[Dict], comments: List[Dict]
    ) -> float:
        """Calculate user reputation score."""
        # Account age factor
        created_utc = user_info.get("created_utc")
        if created_utc:
            account_age_days = (
                datetime.now() - self._parse_timestamp(created_utc)
            ).days
        else:
            account_age_days = 365

        age_factor = min(1.0, account_age_days / 365)  # Max factor at 1 year

        # Karma per day
        total_karma = user_info.get("comment_karma", 0) + user_info.get("link_karma", 0)
        karma_per_day = total_karma / max(account_age_days, 1)
        karma_factor = min(1.0, karma_per_day / 10)  # Max factor at 10 karma/day

        # Verification and premium status
        verification_factor = 0.1 if user_info.get("has_verified_email", False) else 0
        premium_factor = 0.1 if user_info.get("is_gold", False) else 0

        # Content quality
        avg_post_score = np.mean([p.get("score", 0) for p in posts]) if posts else 0
        quality_factor = min(0.3, avg_post_score / 100)

        reputation_score = (
            age_factor * 0.3
            + karma_factor * 0.4
            + quality_factor
            + verification_factor
            + premium_factor
        )

        return min(1.0, reputation_score)

    def _calculate_user_consistency_metrics(
        self, posts: List[Dict], comments: List[Dict]
    ) -> Dict[str, float]:
        """Calculate user consistency metrics."""
        all_timestamps = []
        for post in posts:
            ts = self._parse_timestamp(post.get("created_utc"))
            if ts:
                all_timestamps.append(ts)
        for comment in comments:
            ts = self._parse_timestamp(comment.get("created_utc"))
            if ts:
                all_timestamps.append(ts)

        if len(all_timestamps) < 2:
            return {"posting_regularity": 0.0, "activity_consistency": 0.0}

        all_timestamps.sort()

        # Calculate intervals between posts/comments
        intervals = [
            (all_timestamps[i] - all_timestamps[i - 1]).total_seconds() / 3600
            for i in range(1, len(all_timestamps))
        ]

        # Consistency is inverse of coefficient of variation
        mean_interval = np.mean(intervals)
        std_interval = np.std(intervals)

        if mean_interval > 0:
            cv = std_interval / mean_interval
            consistency = 1.0 / (1.0 + cv)
        else:
            consistency = 0.0

        return {
            "posting_regularity": min(1.0, consistency),
            "activity_consistency": consistency,
            "avg_interval_hours": mean_interval,
        }

    def _calculate_user_community_metrics(
        self, posts: List[Dict], comments: List[Dict]
    ) -> Dict[str, float]:
        """Calculate user community engagement metrics."""
        # Subreddit diversity
        post_subreddits = set(
            p.get("subreddit", "") for p in posts if p.get("subreddit")
        )
        comment_subreddits = set(
            c.get("subreddit", "") for c in comments if c.get("subreddit")
        )
        all_subreddits = post_subreddits.union(comment_subreddits)

        # Community focus vs diversity
        diversity_score = min(1.0, len(all_subreddits) / 20)  # Max at 20 subreddits

        # Cross-posting behavior
        crosspost_count = sum(
            1 for p in posts if "crosspost" in p.get("title", "").lower()
        )
        crosspost_ratio = crosspost_count / max(len(posts), 1)

        return {
            "subreddit_diversity": diversity_score,
            "unique_communities": len(all_subreddits),
            "crosspost_ratio": crosspost_ratio,
            "community_focus": 1.0 - diversity_score,  # Inverse of diversity
        }

    def _calculate_subreddit_health_score(
        self, posts: List[Dict], comments: List[Dict], subreddit_info: Dict[str, Any]
    ) -> float:
        """Calculate overall subreddit health score."""
        # Activity level
        recent_cutoff = datetime.now() - timedelta(days=7)
        recent_posts = sum(
            1
            for p in posts
            if self._parse_timestamp(p.get("created_utc")) > recent_cutoff
        )
        recent_comments = sum(
            1
            for c in comments
            if self._parse_timestamp(c.get("created_utc")) > recent_cutoff
        )

        activity_score = min(1.0, (recent_posts + recent_comments / 10) / 100)

        # Engagement quality
        avg_engagement = (
            np.mean([self._calculate_engagement_score(p) for p in posts])
            if posts
            else 0
        )

        # Content diversity
        diversity_score = self._calculate_content_diversity_score(posts)

        # Moderation quality (low removal rate is good)
        removed_posts = sum(1 for p in posts if p.get("removed_by_category"))
        moderation_score = 1.0 - min(1.0, removed_posts / max(len(posts), 1))

        health_score = (
            activity_score * 0.3
            + avg_engagement * 0.3
            + diversity_score * 0.2
            + moderation_score * 0.2
        )

        return health_score

    def _calculate_subreddit_activity_metrics(
        self, posts: List[Dict], comments: List[Dict]
    ) -> Dict[str, float]:
        """Calculate subreddit activity metrics."""
        # Time-based activity
        daily_posts = {}
        daily_comments = {}

        for post in posts:
            date = self._parse_timestamp(post.get("created_utc"))
            if date:
                day = date.date()
                daily_posts[day] = daily_posts.get(day, 0) + 1

        for comment in comments:
            date = self._parse_timestamp(comment.get("created_utc"))
            if date:
                day = date.date()
                daily_comments[day] = daily_comments.get(day, 0) + 1

        # Calculate averages
        days_with_activity = len(
            set(daily_posts.keys()).union(set(daily_comments.keys()))
        )
        avg_daily_posts = sum(daily_posts.values()) / max(days_with_activity, 1)
        avg_daily_comments = sum(daily_comments.values()) / max(days_with_activity, 1)

        return {
            "avg_daily_posts": avg_daily_posts,
            "avg_daily_comments": avg_daily_comments,
            "total_posts": len(posts),
            "total_comments": len(comments),
            "comments_per_post": len(comments) / max(len(posts), 1),
            "active_days": days_with_activity,
        }

    def _calculate_subreddit_engagement_metrics(
        self, posts: List[Dict], comments: List[Dict]
    ) -> Dict[str, float]:
        """Calculate subreddit engagement metrics."""
        if not posts:
            return {}

        # Average engagement scores
        engagement_scores = [self._calculate_engagement_score(p) for p in posts]
        avg_engagement = np.mean(engagement_scores)

        # Score statistics
        scores = [p.get("score", 0) for p in posts]
        avg_score = np.mean(scores)
        median_score = np.median(scores)

        # Comment statistics
        comment_counts = [p.get("num_comments", 0) for p in posts]
        avg_comments = np.mean(comment_counts)

        # Upvote ratio statistics
        upvote_ratios = [p.get("upvote_ratio", 0.5) for p in posts]
        avg_upvote_ratio = np.mean(upvote_ratios)

        return {
            "avg_engagement_score": avg_engagement,
            "avg_post_score": avg_score,
            "median_post_score": median_score,
            "avg_comments_per_post": avg_comments,
            "avg_upvote_ratio": avg_upvote_ratio,
            "engagement_consistency": 1.0
            - np.std(engagement_scores) / max(avg_engagement, 0.1),
        }

    def _calculate_subreddit_growth_metrics(
        self, posts: List[Dict], comments: List[Dict], subreddit_info: Dict[str, Any]
    ) -> Dict[str, float]:
        """Calculate subreddit growth metrics."""
        # Subscriber growth (would need historical data for accurate calculation)
        current_subscribers = subreddit_info.get("subscribers", 0)

        # Activity growth over time periods
        now = datetime.now()
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)

        recent_posts = sum(
            1 for p in posts if self._parse_timestamp(p.get("created_utc")) > week_ago
        )
        monthly_posts = sum(
            1 for p in posts if self._parse_timestamp(p.get("created_utc")) > month_ago
        )

        recent_comments = sum(
            1
            for c in comments
            if self._parse_timestamp(c.get("created_utc")) > week_ago
        )
        monthly_comments = sum(
            1
            for c in comments
            if self._parse_timestamp(c.get("created_utc")) > month_ago
        )

        # Calculate growth rates (simplified)
        weekly_activity = recent_posts + recent_comments
        monthly_activity = monthly_posts + monthly_comments

        return {
            "current_subscribers": current_subscribers,
            "weekly_posts": recent_posts,
            "weekly_comments": recent_comments,
            "monthly_posts": monthly_posts,
            "monthly_comments": monthly_comments,
            "activity_growth_rate": (weekly_activity * 4) / max(monthly_activity, 1)
            - 1,  # Approximate weekly to monthly
        }

    def _calculate_content_diversity_metrics(
        self, posts: List[Dict]
    ) -> Dict[str, float]:
        """Calculate content diversity metrics."""
        diversity_score = self._calculate_content_diversity_score(posts)

        # Content type distribution
        text_posts = sum(1 for p in posts if p.get("is_self", True))
        link_posts = len(posts) - text_posts

        # Flair diversity
        flairs = [
            p.get("link_flair_text", "") for p in posts if p.get("link_flair_text")
        ]
        unique_flairs = len(set(flairs))

        return {
            "diversity_score": diversity_score,
            "text_post_ratio": text_posts / max(len(posts), 1),
            "link_post_ratio": link_posts / max(len(posts), 1),
            "unique_flairs": unique_flairs,
            "flair_usage_rate": len(flairs) / max(len(posts), 1),
        }

    def _calculate_content_diversity_score(self, posts: List[Dict]) -> float:
        """Calculate content diversity score using entropy."""
        if not posts:
            return 0.0

        # Categories for diversity calculation
        categories = {
            "text": sum(1 for p in posts if p.get("is_self", True)),
            "link": sum(1 for p in posts if not p.get("is_self", True)),
            "image": sum(
                1
                for p in posts
                if any(
                    domain in (p.get("url", "") or "")
                    for domain in ["imgur", "i.redd.it", "reddit.com/gallery"]
                )
            ),
            "video": sum(
                1
                for p in posts
                if any(
                    domain in (p.get("url", "") or "")
                    for domain in ["youtube", "streamable", "v.redd.it"]
                )
            ),
        }

        total = sum(categories.values())
        if total == 0:
            return 0.0

        # Calculate Shannon entropy
        entropy = 0
        for count in categories.values():
            if count > 0:
                p = count / total
                entropy -= p * math.log2(p)

        # Normalize entropy (max entropy for 4 categories is log2(4) = 2)
        normalized_entropy = entropy / 2

        return normalized_entropy

    def _calculate_moderation_metrics(
        self, posts: List[Dict], comments: List[Dict]
    ) -> Dict[str, float]:
        """Calculate moderation activity metrics."""
        # Removed/deleted content
        removed_posts = sum(1 for p in posts if p.get("removed_by_category"))
        deleted_posts = sum(1 for p in posts if p.get("selftext") == "[deleted]")

        # Locked/stickied posts
        locked_posts = sum(1 for p in posts if p.get("locked", False))
        stickied_posts = sum(1 for p in posts if p.get("stickied", False))

        total_posts = max(len(posts), 1)

        return {
            "removal_rate": removed_posts / total_posts,
            "deletion_rate": deleted_posts / total_posts,
            "lock_rate": locked_posts / total_posts,
            "sticky_rate": stickied_posts / total_posts,
            "moderation_activity": (removed_posts + locked_posts + stickied_posts)
            / total_posts,
        }

    def _calculate_community_sentiment_metrics(
        self, posts: List[Dict], comments: List[Dict]
    ) -> Dict[str, float]:
        """Calculate community sentiment metrics."""
        # Aggregate sentiment from posts and comments
        all_sentiment_scores = []

        for post in posts:
            sentiment = post.get("sentiment", {})
            if sentiment:
                all_sentiment_scores.append(sentiment.get("compound_score", 0))

        for comment in comments:
            sentiment = comment.get("sentiment", {})
            if sentiment:
                all_sentiment_scores.append(sentiment.get("compound_score", 0))

        if not all_sentiment_scores:
            return {"avg_sentiment": 0.0, "sentiment_consistency": 0.0}

        avg_sentiment = np.mean(all_sentiment_scores)
        sentiment_std = np.std(all_sentiment_scores)
        sentiment_consistency = 1.0 - min(
            1.0, sentiment_std / 2
        )  # Normalize by max std of 2

        # Sentiment distribution
        positive_ratio = sum(1 for s in all_sentiment_scores if s > 0.1) / len(
            all_sentiment_scores
        )
        negative_ratio = sum(1 for s in all_sentiment_scores if s < -0.1) / len(
            all_sentiment_scores
        )
        neutral_ratio = 1.0 - positive_ratio - negative_ratio

        return {
            "avg_sentiment": avg_sentiment,
            "sentiment_consistency": sentiment_consistency,
            "positive_ratio": positive_ratio,
            "negative_ratio": negative_ratio,
            "neutral_ratio": neutral_ratio,
        }

    def _calculate_influence_distribution(
        self, posts: List[Dict], comments: List[Dict]
    ) -> Dict[str, float]:
        """Calculate influence distribution metrics."""
        # Author contribution distribution
        post_authors = [p.get("author", "") for p in posts if p.get("author")]
        comment_authors = [c.get("author", "") for c in comments if c.get("author")]

        all_authors = post_authors + comment_authors
        author_counts = {}
        for author in all_authors:
            author_counts[author] = author_counts.get(author, 0) + 1

        if not author_counts:
            return {"gini_coefficient": 0.0, "top_contributor_ratio": 0.0}

        # Calculate Gini coefficient for contribution inequality
        counts = sorted(author_counts.values())
        n = len(counts)
        gini = (
            n + 1 - 2 * sum((n + 1 - i) * count for i, count in enumerate(counts))
        ) / (n * sum(counts))

        # Top contributor concentration
        total_contributions = sum(author_counts.values())
        top_10_percent = max(1, len(author_counts) // 10)
        top_contributors = sorted(author_counts.values(), reverse=True)[:top_10_percent]
        top_contributor_ratio = sum(top_contributors) / total_contributions

        return {
            "gini_coefficient": gini,
            "top_contributor_ratio": top_contributor_ratio,
            "unique_contributors": len(author_counts),
            "avg_contributions_per_user": total_contributions / len(author_counts),
        }

    def _parse_timestamp(self, timestamp: Any) -> Optional[datetime]:
        """Parse timestamp from various formats."""
        if isinstance(timestamp, datetime):
            return timestamp
        elif isinstance(timestamp, (int, float)):
            return datetime.fromtimestamp(timestamp)
        else:
            return None

    def _calculate_posting_regularity(self, timestamps: List[datetime]) -> float:
        """Calculate posting regularity score."""
        if len(timestamps) < 2:
            return 0.0

        timestamps.sort()
        intervals = [
            (timestamps[i] - timestamps[i - 1]).total_seconds() / 3600
            for i in range(1, len(timestamps))
        ]

        # Regularity is inverse of coefficient of variation
        mean_interval = np.mean(intervals)
        std_interval = np.std(intervals)

        if mean_interval > 0:
            cv = std_interval / mean_interval
            regularity = 1.0 / (1.0 + cv)
        else:
            regularity = 0.0

        return min(1.0, regularity)
