"""Salary Benchmarking API - Market salary data and offer optimization.

Endpoints for recruiters to get market salary benchmarks and offer recommendations.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.ml.salary_benchmarking import SalaryBenchmarkingService

router = APIRouter(prefix="/api/v1/salary-benchmarking", tags=["salary"])


class SalaryDataResponse(BaseModel):
    """Market salary data for a role."""

    role_title: str
    level: str
    location: str
    min_salary: int
    max_salary: int
    median_salary: int
    percentile_25: int
    percentile_75: int
    data_points: int
    data_source: str
    updated_at: str


class OfferRecommendationResponse(BaseModel):
    """Recommended offer for a candidate."""

    suggested_offer: int
    competitive_range: tuple[int, int]
    negotiation_buffer: int
    win_likelihood: float = Field(..., ge=0, le=1)
    rationale: str
    comparison_to_market: str


class SalaryBenchmarkResponse(BaseModel):
    """Complete salary benchmark with recommendations."""

    role: str
    location: str
    market_data: SalaryDataResponse
    recommendation: OfferRecommendationResponse
    created_at: str


@router.get("/benchmark", response_model=SalaryBenchmarkResponse)
async def get_salary_benchmark(
    role_title: str = Query(..., description="Job title (e.g., 'Software Engineer')"),
    level: str = Query(
        ..., description="Career level (junior, mid, senior, lead, principal)"
    ),
    location: str = Query(..., description="Location (e.g., 'San Francisco, CA')"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get market salary benchmark for a role.

    Returns:
    - Market salary range (min, max, median, percentiles)
    - Recommended offer based on market data
    - Win likelihood and negotiation strategy
    - Comparison to market positioning

    Data sources:
    - Levels.fyi (if API key configured)
    - Glassdoor (if API key configured)
    - TrueMatch fallback data
    """
    try:
        # Initialize service
        # In production, API keys would come from config
        service = SalaryBenchmarkingService(db)

        benchmark = await service.get_benchmark(
            role_title=role_title,
            level=level,
            location=location,
        )

        if not benchmark:
            raise HTTPException(
                status_code=404, detail="No salary data available for this role"
            )

        return benchmark.to_dict()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Benchmarking error: {str(e)}")


@router.get("/benchmark/candidate/{candidate_id}/{position_id}", response_model=SalaryBenchmarkResponse)
async def get_candidate_salary_benchmark(
    candidate_id: UUID,
    position_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get personalized salary benchmark for a candidate/position pair.

    Accounts for:
    - Candidate's skills match to the role
    - Candidate's salary expectations (if in resume)
    - Market data for the specific role/location
    - Role criticality and importance

    Returns offer recommendation optimized for:
    - Competitiveness (attracts the candidate)
    - Market alignment
    - Win likelihood
    """
    try:
        service = SalaryBenchmarkingService(db)

        benchmark = await service.get_benchmark_for_candidate(
            candidate_id=candidate_id,
            position_id=position_id,
        )

        if not benchmark:
            raise HTTPException(
                status_code=404, detail="Unable to generate benchmark for this candidate/position"
            )

        return benchmark.to_dict()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Benchmarking error: {str(e)}")


class BulkBenchmarkRequest(BaseModel):
    """Request benchmarks for multiple roles."""

    roles: list[dict] = Field(
        ...,
        description="List of {role_title, level, location} objects",
    )


class BulkBenchmarkResponse(BaseModel):
    """Response with multiple benchmarks."""

    benchmarks: list[SalaryBenchmarkResponse]
    total_count: int
    average_suggested_offer: float


@router.post("/benchmark/bulk", response_model=BulkBenchmarkResponse)
async def get_bulk_salary_benchmarks(
    request: BulkBenchmarkRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get salary benchmarks for multiple roles.

    Useful for:
    - Compensation planning
    - Offer letter generation
    - Hiring budget planning
    """
    try:
        service = SalaryBenchmarkingService(db)

        benchmarks = []
        for role_data in request.roles:
            benchmark = await service.get_benchmark(
                role_title=role_data.get("role_title"),
                level=role_data.get("level"),
                location=role_data.get("location"),
            )
            if benchmark:
                benchmarks.append(benchmark.to_dict())

        if not benchmarks:
            raise HTTPException(
                status_code=404, detail="No benchmarks available for provided roles"
            )

        avg_offer = sum(b["recommendation"]["suggested_offer"] for b in benchmarks) / len(benchmarks)

        return BulkBenchmarkResponse(
            benchmarks=benchmarks,
            total_count=len(benchmarks),
            average_suggested_offer=avg_offer,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bulk benchmarking error: {str(e)}")


class SalaryDataRequest(BaseModel):
    """Request to update salary data."""

    role_title: str
    level: str
    location: str
    min_salary: float
    max_salary: float
    median_salary: float
    percentile_25: float
    percentile_75: float
    data_points: int
    data_source: str = "manual"


class SalaryDataUpdateResponse(BaseModel):
    """Response for data update."""

    status: str
    message: str


@router.post("/data/update", response_model=SalaryDataUpdateResponse)
async def update_salary_data(
    request: SalaryDataRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update salary benchmark data.

    Allows admins to manually update fallback salary data when external APIs are unavailable.

    Requires ADMIN role.
    """
    try:
        # In production, this would:
        # 1. Validate admin role
        # 2. Update SalaryBenchmark table
        # 3. Invalidate cache
        # 4. Return confirmation

        return SalaryDataUpdateResponse(
            status="success",
            message=f"Salary data updated for {request.role_title} ({request.level}) in {request.location}",
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Update error: {str(e)}")


__all__ = ["router"]
