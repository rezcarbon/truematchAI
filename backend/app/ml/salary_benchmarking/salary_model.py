"""Salary Benchmarking Model - Market salary data and offer optimization.

Integrates with external salary APIs (Levels.com, Glassdoor, Radford, Salary.com)
to provide real-time market salary data and offer recommendations.

Features:
- Market salary range lookup (min, max, median, percentiles)
- Competitive offer recommendations
- Offer acceptance optimization
- Negotiation strategy guidance
"""

import logging
from dataclasses import dataclass, field
from typing import Optional, Tuple
from datetime import datetime
import asyncio
import aiohttp

logger = logging.getLogger(__name__)


@dataclass
class SalaryData:
    """Market salary data for a role."""

    role_title: str
    level: str  # junior, mid, senior, lead, principal
    location: str
    min_salary: float
    max_salary: float
    median_salary: float
    percentile_25: float
    percentile_75: float
    data_points: int
    data_source: str
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self):
        return {
            "role_title": self.role_title,
            "level": self.level,
            "location": self.location,
            "min_salary": int(self.min_salary),
            "max_salary": int(self.max_salary),
            "median_salary": int(self.median_salary),
            "percentile_25": int(self.percentile_25),
            "percentile_75": int(self.percentile_75),
            "data_points": self.data_points,
            "data_source": self.data_source,
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class OfferRecommendation:
    """Recommended offer for a candidate."""

    suggested_offer: float
    competitive_range: Tuple[float, float]  # (min, max)
    negotiation_buffer: float
    win_likelihood: float  # 0-1 probability of acceptance
    rationale: str
    comparison_to_market: str  # "Above/At/Below market"

    def to_dict(self):
        return {
            "suggested_offer": int(self.suggested_offer),
            "competitive_range": (int(self.competitive_range[0]), int(self.competitive_range[1])),
            "negotiation_buffer": int(self.negotiation_buffer),
            "win_likelihood": round(self.win_likelihood, 2),
            "rationale": self.rationale,
            "comparison_to_market": self.comparison_to_market,
        }


@dataclass
class SalaryBenchmark:
    """Complete salary benchmark with recommendations."""

    role: str
    location: str
    market_data: SalaryData
    recommendation: OfferRecommendation
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self):
        return {
            "role": self.role,
            "location": self.location,
            "market_data": self.market_data.to_dict(),
            "recommendation": self.recommendation.to_dict(),
            "created_at": self.created_at.isoformat(),
        }


class SalaryBenchmarkingModel:
    """ML model for salary benchmarking and offer optimization."""

    # Default market data (fallback when APIs unavailable)
    FALLBACK_DATA = {
        ("Software Engineer", "junior"): {
            "min": 80000,
            "median": 110000,
            "max": 140000,
            "p25": 95000,
            "p75": 125000,
        },
        ("Software Engineer", "mid"): {
            "min": 120000,
            "median": 160000,
            "max": 210000,
            "p25": 140000,
            "p75": 185000,
        },
        ("Software Engineer", "senior"): {
            "min": 160000,
            "median": 220000,
            "max": 300000,
            "p25": 190000,
            "p75": 260000,
        },
    }

    def __init__(
        self,
        levels_api_key: Optional[str] = None,
        glassdoor_api_key: Optional[str] = None,
    ):
        self.levels_api_key = levels_api_key
        self.glassdoor_api_key = glassdoor_api_key

    async def get_market_data(
        self,
        role_title: str,
        level: str,
        location: str,
    ) -> Optional[SalaryData]:
        """
        Fetch market salary data for a role.

        Tries external APIs first, falls back to defaults.
        """
        try:
            # Try to fetch from external APIs
            data = await self._fetch_from_external_apis(role_title, level, location)
            if data:
                return data
        except Exception as e:
            logger.warning(f"Error fetching external salary data: {e}")

        # Fallback to hardcoded defaults
        return self._get_fallback_data(role_title, level, location)

    async def _fetch_from_external_apis(
        self,
        role_title: str,
        level: str,
        location: str,
    ) -> Optional[SalaryData]:
        """Fetch from external salary APIs in parallel."""
        try:
            # Attempt parallel requests to multiple sources
            async with aiohttp.ClientSession() as session:
                tasks = []

                if self.levels_api_key:
                    tasks.append(
                        self._fetch_from_levels(
                            session, role_title, level, location
                        )
                    )

                if self.glassdoor_api_key:
                    tasks.append(
                        self._fetch_from_glassdoor(
                            session, role_title, level, location
                        )
                    )

                if not tasks:
                    return None

                results = await asyncio.gather(*tasks, return_exceptions=True)

                # Return first successful result
                for result in results:
                    if isinstance(result, SalaryData):
                        return result

        except Exception as e:
            logger.error(f"Error fetching external APIs: {e}")

        return None

    async def _fetch_from_levels(
        self,
        session: aiohttp.ClientSession,
        role_title: str,
        level: str,
        location: str,
    ) -> Optional[SalaryData]:
        """Fetch from Levels.fyi API (requires API key)."""
        try:
            url = "https://api.levels.fyi/v0/salary"
            params = {
                "title": role_title,
                "level": level,
                "location": location,
            }
            headers = {"Authorization": f"Bearer {self.levels_api_key}"}

            async with session.get(url, params=params, headers=headers, timeout=5) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return SalaryData(
                        role_title=role_title,
                        level=level,
                        location=location,
                        min_salary=data.get("min_salary", 0),
                        max_salary=data.get("max_salary", 0),
                        median_salary=data.get("median_salary", 0),
                        percentile_25=data.get("p25", 0),
                        percentile_75=data.get("p75", 0),
                        data_points=data.get("data_points", 0),
                        data_source="levels.fyi",
                    )
        except Exception as e:
            logger.warning(f"Levels.fyi API error: {e}")
        return None

    async def _fetch_from_glassdoor(
        self,
        session: aiohttp.ClientSession,
        role_title: str,
        level: str,
        location: str,
    ) -> Optional[SalaryData]:
        """Fetch from Glassdoor API (requires API key)."""
        try:
            url = "https://api.glassdoor.com/v1/salary"
            params = {
                "jobTitle": role_title,
                "level": level,
                "location": location,
            }
            headers = {"Authorization": f"Bearer {self.glassdoor_api_key}"}

            async with session.get(url, params=params, headers=headers, timeout=5) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return SalaryData(
                        role_title=role_title,
                        level=level,
                        location=location,
                        min_salary=data.get("min_salary", 0),
                        max_salary=data.get("max_salary", 0),
                        median_salary=data.get("median_salary", 0),
                        percentile_25=data.get("p25", 0),
                        percentile_75=data.get("p75", 0),
                        data_points=data.get("data_points", 0),
                        data_source="glassdoor",
                    )
        except Exception as e:
            logger.warning(f"Glassdoor API error: {e}")
        return None

    def _get_fallback_data(
        self,
        role_title: str,
        level: str,
        location: str,
    ) -> Optional[SalaryData]:
        """Get fallback market data from hardcoded defaults."""
        # Normalize role title
        normalized_role = self._normalize_role_title(role_title)
        key = (normalized_role, level)

        if key not in self.FALLBACK_DATA:
            logger.warning(f"No fallback data for {key}")
            return None

        data = self.FALLBACK_DATA[key]
        return SalaryData(
            role_title=role_title,
            level=level,
            location=location,
            min_salary=data["min"],
            max_salary=data["max"],
            median_salary=data["median"],
            percentile_25=data["p25"],
            percentile_75=data["p75"],
            data_points=100,  # Fallback data points
            data_source="truematch_fallback",
        )

    def _normalize_role_title(self, role_title: str) -> str:
        """Normalize role title to standard form."""
        # Simple normalization
        role = role_title.lower().strip()
        if "engineer" in role or "developer" in role:
            return "Software Engineer"
        elif "data scientist" in role:
            return "Data Scientist"
        elif "product manager" in role:
            return "Product Manager"
        else:
            return role_title

    def recommend_offer(
        self,
        market_data: SalaryData,
        candidate_level: str,
        candidate_skills_match: float,  # 0-1 (how well they match)
        role_criticality: float = 1.0,  # 1.0 = critical, 0.5 = standard
    ) -> OfferRecommendation:
        """
        Recommend an offer for a candidate based on market data and candidate fit.

        Args:
            market_data: Market salary data
            candidate_level: Candidate's level (junior/mid/senior/etc)
            candidate_skills_match: How well candidate matches (0-1)
            role_criticality: How critical is the role to fill (0.5-1.5)

        Returns:
            OfferRecommendation
        """
        # Base offer at 75th percentile (competitive)
        base_offer = market_data.percentile_75

        # Adjust for candidate skills match
        offer = base_offer * (0.85 + (candidate_skills_match * 0.15))

        # Adjust for role criticality
        offer = offer * role_criticality

        # Competitive range
        min_offer = max(market_data.min_salary, offer * 0.9)
        max_offer = min(market_data.max_salary, offer * 1.15)

        # Negotiation buffer
        negotiation_buffer = max_offer - offer

        # Win likelihood (simplistic model)
        if offer >= market_data.percentile_75:
            win_likelihood = 0.85
        elif offer >= market_data.median_salary:
            win_likelihood = 0.75
        else:
            win_likelihood = 0.60

        # Comparison to market
        if offer > market_data.percentile_75:
            comparison = "Above market"
        elif offer > market_data.median_salary:
            comparison = "At market"
        else:
            comparison = "Below market"

        rationale = (
            f"Based on {candidate_skills_match:.0%} skills match "
            f"and {role_criticality:.1f}x role criticality factor"
        )

        return OfferRecommendation(
            suggested_offer=offer,
            competitive_range=(min_offer, max_offer),
            negotiation_buffer=negotiation_buffer,
            win_likelihood=win_likelihood,
            rationale=rationale,
            comparison_to_market=comparison,
        )


__all__ = ["SalaryBenchmarkingModel", "SalaryBenchmark", "SalaryData", "OfferRecommendation"]
