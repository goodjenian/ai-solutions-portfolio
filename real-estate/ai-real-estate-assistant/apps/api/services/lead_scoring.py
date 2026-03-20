"""
Service for scoring leads based on behavioral signals.

This service implements the lead scoring algorithm with:
- Search activity scoring
- Engagement scoring
- Intent scoring
- Composite scoring with explainability
"""

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Lead, LeadScore
from db.repositories import (
    AgentAssignmentRepository,
    LeadInteractionRepository,
    LeadRepository,
    LeadScoreRepository,
)

logger = logging.getLogger(__name__)


# Scoring weights (can be tuned based on historical conversion data)
SCORING_WEIGHTS = {
    "search_activity": 0.25,  # 25% weight
    "engagement": 0.35,  # 35% weight
    "intent": 0.40,  # 40% weight
}

# Model version for tracking scoring algorithm changes
CURRENT_MODEL_VERSION = "1.0.0"


@dataclass
class ScoringFactors:
    """Raw scoring factors collected from lead interactions."""

    # Search activity
    search_count: int = 0
    saved_search_count: int = 0
    advanced_filter_count: int = 0
    recent_search_count_7d: int = 0

    # Engagement
    property_views: int = 0
    favorites_count: int = 0
    total_time_spent_minutes: float = 0.0
    return_visits: int = 0
    unique_sessions: int = 0

    # Intent
    inquiries_submitted: int = 0
    contact_requests: int = 0
    viewings_scheduled: int = 0
    reports_downloaded: int = 0
    properties_shared: int = 0

    # Profile completeness
    has_email: bool = False
    has_phone: bool = False
    has_name: bool = False
    has_budget: bool = False

    # Recency
    days_since_last_activity: int = 999
    days_since_first_seen: int = 0


@dataclass
class ScoreBreakdown:
    """Breakdown of the calculated score."""

    total_score: int
    search_activity_score: int
    engagement_score: int
    intent_score: int
    factors: dict[str, Any]
    recommendations: list[str]


class LeadScoringEngine:
    """Engine for calculating lead scores based on behavioral signals."""

    def __init__(
        self,
        session: AsyncSession,
        lead_repo: Optional[LeadRepository] = None,
        interaction_repo: Optional[LeadInteractionRepository] = None,
        score_repo: Optional[LeadScoreRepository] = None,
    ):
        self.session = session
        self.lead_repo = lead_repo or LeadRepository(session)
        self.interaction_repo = interaction_repo or LeadInteractionRepository(session)
        self.score_repo = score_repo or LeadScoreRepository(session)

    async def calculate_score(self, lead: Lead) -> ScoreBreakdown:
        """Calculate comprehensive lead score with breakdown.

        Args:
            lead: The lead to score

        Returns:
            ScoreBreakdown with total score and component scores
        """
        # Collect interaction statistics
        stats = await self.interaction_repo.get_interaction_stats(lead.id)

        # Build scoring factors from stats
        factors = await self._collect_scoring_factors(lead, stats)

        # Calculate component scores (0-100 each)
        search_score = self._calculate_search_activity_score(factors)
        engagement_score = self._calculate_engagement_score(factors)
        intent_score = self._calculate_intent_score(factors)

        # Calculate weighted total score
        total_score = round(
            search_score * SCORING_WEIGHTS["search_activity"]
            + engagement_score * SCORING_WEIGHTS["engagement"]
            + intent_score * SCORING_WEIGHTS["intent"]
        )

        # Generate recommendations
        recommendations = self._generate_recommendations(factors, total_score)

        return ScoreBreakdown(
            total_score=min(100, max(0, total_score)),
            search_activity_score=search_score,
            engagement_score=engagement_score,
            intent_score=intent_score,
            factors=self._factors_to_dict(factors),
            recommendations=recommendations,
        )

    async def _collect_scoring_factors(self, lead: Lead, stats: dict[str, Any]) -> ScoringFactors:
        """Collect all scoring factors for a lead."""
        type_counts: dict[str, int] = stats.get("type_counts", {})

        # Calculate days since last activity
        last_activity = stats.get("last_activity_at") or lead.last_activity_at
        if last_activity:
            days_since_activity = (datetime.now(UTC) - last_activity).days
        else:
            days_since_activity = 999

        # Calculate days since first seen
        first_activity = stats.get("first_activity_at") or lead.first_seen_at
        if first_activity:
            days_since_first_seen = (datetime.now(UTC) - first_activity).days
        else:
            days_since_first_seen = 0

        return ScoringFactors(
            # Search activity
            search_count=type_counts.get("search", 0),
            saved_search_count=type_counts.get("save_search", 0),
            advanced_filter_count=0,  # Would need to parse metadata
            recent_search_count_7d=type_counts.get("search", 0),  # Simplified
            # Engagement
            property_views=type_counts.get("view", 0),
            favorites_count=type_counts.get("favorite", 0),
            total_time_spent_minutes=stats.get("total_time_spent_seconds", 0) / 60,
            return_visits=min(10, len(set([stats.get("session_id", "default")]))),
            unique_sessions=1,  # Simplified
            # Intent
            inquiries_submitted=type_counts.get("inquiry", 0),
            contact_requests=type_counts.get("contact", 0),
            viewings_scheduled=type_counts.get("schedule_viewing", 0),
            reports_downloaded=type_counts.get("download_report", 0),
            properties_shared=type_counts.get("share", 0),
            # Profile completeness
            has_email=lead.email is not None,
            has_phone=lead.phone is not None,
            has_name=lead.name is not None,
            has_budget=lead.budget_min is not None or lead.budget_max is not None,
            # Recency
            days_since_last_activity=days_since_activity,
            days_since_first_seen=days_since_first_seen,
        )

    def _calculate_search_activity_score(self, factors: ScoringFactors) -> int:
        """Calculate search activity component score (0-100)."""
        score = 0

        # Number of searches (max 25 points)
        # 1-5 searches = 10 points, 6-10 = 15, 11-20 = 20, 20+ = 25
        if factors.search_count >= 20:
            score += 25
        elif factors.search_count >= 11:
            score += 20
        elif factors.search_count >= 6:
            score += 15
        elif factors.search_count >= 1:
            score += 10

        # Saved searches (max 30 points)
        # Each saved search = 10 points, max 3
        score += min(30, factors.saved_search_count * 10)

        # Search recency (max 20 points)
        # Recent searches in last 7 days boost score
        if factors.recent_search_count_7d > 0:
            recency_bonus = min(20, factors.recent_search_count_7d * 5)
            score += recency_bonus

        # Advanced filter usage (max 25 points)
        score += min(25, factors.advanced_filter_count * 5)

        return min(100, score)

    def _calculate_engagement_score(self, factors: ScoringFactors) -> int:
        """Calculate engagement component score (0-100)."""
        score = 0

        # Property views (max 25 points)
        # 1-5 views = 5, 6-15 = 10, 16-30 = 15, 31-50 = 20, 50+ = 25
        if factors.property_views >= 50:
            score += 25
        elif factors.property_views >= 31:
            score += 20
        elif factors.property_views >= 16:
            score += 15
        elif factors.property_views >= 6:
            score += 10
        elif factors.property_views >= 1:
            score += 5

        # Favorites (max 30 points)
        # Each favorite = 6 points, max 5
        score += min(30, factors.favorites_count * 6)

        # Time on site (max 25 points)
        # <5 min = 5, 5-15 = 10, 15-30 = 15, 30-60 = 20, 60+ = 25
        if factors.total_time_spent_minutes >= 60:
            score += 25
        elif factors.total_time_spent_minutes >= 30:
            score += 20
        elif factors.total_time_spent_minutes >= 15:
            score += 15
        elif factors.total_time_spent_minutes >= 5:
            score += 10
        elif factors.total_time_spent_minutes > 0:
            score += 5

        # Return visits (max 20 points)
        # Each return visit = 4 points, max 5
        score += min(20, (factors.return_visits - 1) * 4 if factors.return_visits > 0 else 0)

        return min(100, score)

    def _calculate_intent_score(self, factors: ScoringFactors) -> int:
        """Calculate intent component score (0-100)."""
        score = 0

        # Inquiry submitted (40 points each, max 40)
        if factors.inquiries_submitted >= 1:
            score += 40

        # Contact request (30 points each, max 30)
        if factors.contact_requests >= 1:
            score += 30

        # Viewing scheduled (50 points, max 50 - overrides other intent)
        if factors.viewings_scheduled >= 1:
            score = max(score, 80)  # At least 80 if viewing scheduled

        # Reports downloaded (5 points each, max 15)
        score += min(15, factors.reports_downloaded * 5)

        # Properties shared (3 points each, max 9)
        score += min(9, factors.properties_shared * 3)

        # Profile completeness (max 10 points)
        completeness_score = 0
        if factors.has_email:
            completeness_score += 3
        if factors.has_phone:
            completeness_score += 3
        if factors.has_name:
            completeness_score += 2
        if factors.has_budget:
            completeness_score += 2
        score += completeness_score

        # Recency penalty (reduce score if inactive)
        if factors.days_since_last_activity > 30:
            score = int(score * 0.5)  # 50% penalty if inactive > 30 days
        elif factors.days_since_last_activity > 14:
            score = int(score * 0.75)  # 25% penalty if inactive > 14 days

        return min(100, score)

    def _generate_recommendations(self, factors: ScoringFactors, total_score: int) -> list[str]:
        """Generate actionable recommendations based on lead behavior."""
        recommendations = []

        # High-intent recommendations
        if factors.inquiries_submitted > 0:
            recommendations.append("Lead has submitted inquiry - prioritize follow-up")
        if factors.viewings_scheduled > 0:
            recommendations.append("Lead has scheduled viewing - ensure agent is prepared")
        if factors.contact_requests > 0:
            recommendations.append("Lead requested contact - respond within 24 hours")

        # Engagement recommendations
        if factors.favorites_count >= 3 and factors.inquiries_submitted == 0:
            recommendations.append(
                "Lead has multiple favorites but no inquiry - consider proactive outreach"
            )
        if factors.property_views >= 20 and factors.inquiries_submitted == 0:
            recommendations.append("High browsing activity without inquiry - may need assistance")

        # Profile recommendations
        if not factors.has_email and factors.property_views >= 5:
            recommendations.append(
                "Anonymous lead with high activity - consider capturing contact info"
            )
        if not factors.has_phone and factors.inquiries_submitted > 0:
            recommendations.append("Lead inquired without phone - request for faster response")

        # Search behavior recommendations
        if factors.saved_search_count > 0:
            recommendations.append(
                f"Lead has {factors.saved_search_count} saved search(es) - share new matching properties"
            )

        # Recency recommendations
        if factors.days_since_last_activity > 7 and total_score >= 50:
            recommendations.append("Previously active lead - consider re-engagement campaign")

        # Score-based recommendations
        if total_score >= 80:
            recommendations.append("High-value lead - assign to senior agent")
        elif total_score >= 60:
            recommendations.append("Warm lead - qualify budget and timeline")

        return recommendations[:5]  # Limit to top 5 recommendations

    def _factors_to_dict(self, factors: ScoringFactors) -> dict[str, Any]:
        """Convert scoring factors to dictionary for storage."""
        return {
            "search_count": factors.search_count,
            "saved_search_count": factors.saved_search_count,
            "property_views": factors.property_views,
            "favorites_count": factors.favorites_count,
            "total_time_minutes": round(factors.total_time_spent_minutes, 1),
            "return_visits": factors.return_visits,
            "inquiries": factors.inquiries_submitted,
            "contact_requests": factors.contact_requests,
            "viewings_scheduled": factors.viewings_scheduled,
            "has_email": factors.has_email,
            "has_phone": factors.has_phone,
            "has_name": factors.has_name,
            "days_since_activity": factors.days_since_last_activity,
        }


class LeadScoringService:
    """High-level service for lead scoring operations."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.lead_repo = LeadRepository(session)
        self.interaction_repo = LeadInteractionRepository(session)
        self.score_repo = LeadScoreRepository(session)
        self.assignment_repo = AgentAssignmentRepository(session)
        self.engine = LeadScoringEngine(
            session, self.lead_repo, self.interaction_repo, self.score_repo
        )

    async def score_lead(self, lead_id: str) -> Optional[LeadScore]:
        """Calculate and store score for a single lead.

        Args:
            lead_id: ID of the lead to score

        Returns:
            The created LeadScore record, or None if lead not found
        """
        lead = await self.lead_repo.get_by_id(lead_id)
        if not lead:
            logger.warning(f"Lead not found: {lead_id}")
            return None

        # Calculate score breakdown
        breakdown = await self.engine.calculate_score(lead)

        # Store score in database
        score_record = await self.score_repo.create(
            lead_id=lead.id,
            total_score=breakdown.total_score,
            search_activity_score=breakdown.search_activity_score,
            engagement_score=breakdown.engagement_score,
            intent_score=breakdown.intent_score,
            score_factors=breakdown.factors,
            recommendations=breakdown.recommendations,
            model_version=CURRENT_MODEL_VERSION,
        )

        # Update lead's denormalized current score
        await self.lead_repo.update_score(lead, breakdown.total_score)

        logger.info(
            f"Scored lead {lead_id}: {breakdown.total_score} "
            f"(search={breakdown.search_activity_score}, "
            f"engagement={breakdown.engagement_score}, "
            f"intent={breakdown.intent_score})"
        )

        return score_record

    async def recalculate_all_scores(
        self,
        lead_ids: Optional[list[str]] = None,
        max_age_hours: int = 24,
        force: bool = False,
    ) -> dict[str, Any]:
        """Recalculate scores for multiple leads.

        Args:
            lead_ids: Specific lead IDs to recalculate, or None for all needing update
            max_age_hours: Only recalculate if score is older than this (unless force)
            force: Force recalculation regardless of age

        Returns:
            Dict with recalculation results
        """
        results: dict[str, Any] = {
            "recalculated": 0,
            "failed": 0,
            "skipped": 0,
            "errors": [],
        }

        if lead_ids is None:
            # Get leads needing recalculation
            lead_ids = await self.score_repo.get_leads_needing_recalc(
                max_age_hours=max_age_hours if not force else 0,
                limit=1000,
            )

        for lead_id in lead_ids:
            try:
                score = await self.score_lead(lead_id)
                if score:
                    results["recalculated"] += 1
                else:
                    results["skipped"] += 1
            except Exception as e:
                logger.error(f"Failed to score lead {lead_id}: {e}")
                results["failed"] += 1
                results["errors"].append(f"{lead_id}: {str(e)}")

        return results

    async def get_lead_score_breakdown(self, lead_id: str) -> Optional[dict[str, Any]]:
        """Get detailed score breakdown for a lead.

        Args:
            lead_id: Lead ID

        Returns:
            Dict with score breakdown and history, or None if not found
        """
        lead = await self.lead_repo.get_by_id(lead_id)
        if not lead:
            return None

        # Get latest score
        latest_score = await self.score_repo.get_latest_for_lead(lead_id)

        # Get score history
        history = await self.score_repo.get_history_for_lead(lead_id, limit=30)

        # Get interaction stats
        stats = await self.interaction_repo.get_interaction_stats(lead_id)

        return {
            "lead_id": lead_id,
            "current_score": lead.current_score,
            "latest_score": {
                "total_score": latest_score.total_score,
                "search_activity_score": latest_score.search_activity_score,
                "engagement_score": latest_score.engagement_score,
                "intent_score": latest_score.intent_score,
                "score_factors": latest_score.score_factors,
                "recommendations": latest_score.recommendations,
                "calculated_at": latest_score.calculated_at.isoformat(),
                "model_version": latest_score.model_version,
            }
            if latest_score
            else None,
            "score_history": [
                {
                    "total_score": s.total_score,
                    "calculated_at": s.calculated_at.isoformat(),
                }
                for s in history
            ],
            "interaction_stats": stats,
        }

    async def get_high_value_leads(
        self,
        threshold: int = 70,
        limit: int = 100,
        assigned_to_agent: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """Get leads with scores above threshold.

        Args:
            threshold: Minimum score threshold
            limit: Maximum number of leads to return
            assigned_to_agent: Filter by assigned agent

        Returns:
            List of high-value leads with scores
        """
        leads = await self.lead_repo.get_list(
            agent_id=assigned_to_agent,
            score_min=threshold,
            limit=limit,
            sort_by="score",
            sort_order="desc",
        )

        result = []
        for lead in leads:
            latest_score = await self.score_repo.get_latest_for_lead(lead.id)
            result.append(
                {
                    "id": lead.id,
                    "email": lead.email,
                    "name": lead.name,
                    "current_score": lead.current_score,
                    "status": lead.status,
                    "last_activity_at": lead.last_activity_at.isoformat(),
                    "recommendations": latest_score.recommendations if latest_score else [],
                }
            )

        return result

    async def get_scoring_statistics(self) -> dict[str, Any]:
        """Get overall scoring statistics.

        Returns:
            Dict with scoring statistics
        """
        # Get total leads
        total_leads = await self.lead_repo.count()

        # Get leads by score ranges
        high_value = await self.lead_repo.count(score_min=80)
        medium_value = await self.lead_repo.count(score_min=50, score_max=79)
        low_value = await self.lead_repo.count(score_max=49)

        # Get scores calculated today
        scores_today = await self.score_repo.count_scores_today()

        return {
            "total_leads": total_leads,
            "score_distribution": {
                "high_80_100": high_value,
                "medium_50_79": medium_value,
                "low_0_49": low_value,
            },
            "scores_calculated_today": scores_today,
            "model_version": CURRENT_MODEL_VERSION,
            "weights": SCORING_WEIGHTS,
        }
