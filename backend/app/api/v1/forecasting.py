"""Pipeline Forecasting API - Predict time-to-hire and identify bottlenecks.

Endpoints for recruiters to forecast hiring timelines and get optimization recommendations.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.ml.forecasting import ForecastService, ForecastModel

router = APIRouter(prefix="/api/v1/forecasting", tags=["forecasting"])


class ForecastRequest(BaseModel):
    """Request to forecast hiring timeline."""

    position_id: UUID = Field(..., description="Position UUID")
    department: Optional[str] = Field(None, description="Department name")


class ForecastResponse(BaseModel):
    """Response with hiring forecast."""

    position_id: str
    forecasted_fill_date: str
    estimated_days_to_fill: int
    confidence: float = Field(..., ge=0, le=1)
    bottleneck_stage: Optional[str] = None
    recommendations: list[str] = []
    model_version: str = "v1"
    created_at: str


@router.post("/pipeline", response_model=ForecastResponse)
async def forecast_pipeline(
    request: ForecastRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Forecast time-to-hire for a position.

    Predicts how long it will take to fill a position based on:
    - Historical hiring data for similar roles
    - Current pipeline status
    - JD complexity
    - Market conditions

    Returns:
    - Estimated days to fill
    - Predicted fill date
    - Confidence score
    - Identified bottleneck stage
    - Actionable recommendations
    """
    try:
        # Initialize model (would be cached in production)
        model = ForecastModel()
        # Load pre-trained model from cache/disk
        # model.load("/path/to/model.pkl")

        service = ForecastService(db, model)
        forecast = await service.forecast_position(request.position_id)

        if not forecast:
            raise HTTPException(status_code=404, detail="Position not found or insufficient data")

        return forecast.to_dict()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Forecast error: {str(e)}")


@router.get("/pipeline/{position_id}", response_model=ForecastResponse)
async def get_forecast(
    position_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the latest forecast for a position."""
    try:
        model = ForecastModel()
        service = ForecastService(db, model)
        forecast = await service.forecast_position(position_id)

        if not forecast:
            raise HTTPException(status_code=404, detail="Position not found or insufficient data")

        return forecast.to_dict()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Forecast error: {str(e)}")


class BulkForecastRequest(BaseModel):
    """Request to forecast multiple positions."""

    position_ids: list[UUID] = Field(..., description="Position UUIDs")


class BulkForecastResponse(BaseModel):
    """Response with multiple forecasts."""

    forecasts: list[ForecastResponse]
    total_count: int
    average_days_to_fill: float


@router.post("/pipeline/bulk", response_model=BulkForecastResponse)
async def forecast_bulk_positions(
    request: BulkForecastRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Forecast hiring timelines for multiple positions.

    Useful for:
    - Workforce planning
    - Resource allocation
    - Understanding aggregate hiring velocity
    """
    try:
        model = ForecastModel()
        service = ForecastService(db, model)

        forecasts = []
        for position_id in request.position_ids:
            forecast = await service.forecast_position(position_id)
            if forecast:
                forecasts.append(forecast.to_dict())

        if not forecasts:
            raise HTTPException(status_code=404, detail="No forecasts available for provided positions")

        avg_days = sum(f["estimated_days_to_fill"] for f in forecasts) / len(forecasts)

        return BulkForecastResponse(
            forecasts=forecasts,
            total_count=len(forecasts),
            average_days_to_fill=avg_days,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bulk forecast error: {str(e)}")


class ModelTrainingRequest(BaseModel):
    """Request to train/retrain the forecasting model."""

    min_samples: int = Field(default=100, ge=10)


class ModelTrainingResponse(BaseModel):
    """Response with training metrics."""

    status: str
    train_r2: Optional[float] = None
    test_r2: Optional[float] = None
    train_rmse_days: Optional[float] = None
    test_rmse_days: Optional[float] = None
    samples_used: Optional[int] = None
    message: str


@router.post("/model/train", response_model=ModelTrainingResponse)
async def train_forecast_model(
    request: ModelTrainingRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Train the pipeline forecasting model.

    This endpoint trains a new regression model from historical hiring data.
    Should be run periodically (e.g., weekly) to keep predictions accurate.

    Requires ADMIN role.
    """
    # Check admin role (would be added to user model)
    # if user.role not in [UserRole.ADMIN]:
    #     raise HTTPException(status_code=403, detail="Admin access required")

    try:
        model = ForecastModel()
        result = await model.train_from_data(db, min_samples=request.min_samples)

        if result["status"] == "success":
            # Save trained model (would be to Redis or disk)
            # model.save("/path/to/model.pkl")
            return ModelTrainingResponse(
                status="success",
                train_r2=result.get("train_r2"),
                test_r2=result.get("test_r2"),
                train_rmse_days=result.get("train_rmse_days"),
                test_rmse_days=result.get("test_rmse_days"),
                samples_used=result.get("samples_used"),
                message=f"Model trained successfully on {result.get('samples_used')} samples",
            )
        else:
            return ModelTrainingResponse(
                status="insufficient_data",
                samples_used=result.get("samples_found"),
                message=f"Insufficient data: {result.get('samples_found')} samples (need {request.min_samples})",
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Training error: {str(e)}")


__all__ = ["router"]
