"""
🌙 Mond Dashboard API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime, timedelta
from app.core.database import get_db
from app.services.dashboard_service import DashboardService

router = APIRouter()


@router.get("/overview")
async def get_dashboard_overview(
    aws_account_id: Optional[str] = Query(None, description="Filter by AWS Account ID"),
    time_range: str = Query("7d", regex="^(1d|7d|30d|90d)$", description="Time range for metrics"),
    db: AsyncSession = Depends(get_db)
):
    """
    🌙 Get main dashboard overview with key metrics
    
    Returns:
    - Security score and trends
    - Tag compliance overview
    - Recent security findings
    - System health status
    """
    dashboard_service = DashboardService(db)
    
    try:
        overview_data = await dashboard_service.get_overview(
            aws_account_id=aws_account_id,
            time_range=time_range
        )
        return overview_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get overview: {str(e)}")


@router.get("/security-score")
async def get_security_score(
    aws_account_id: Optional[str] = Query(None),
    include_trend: bool = Query(True, description="Include historical trend data"),
    db: AsyncSession = Depends(get_db)
):
    """
    🛡️ Get security score and breakdown
    
    Security score is calculated based on:
    - Security Hub findings severity
    - Compliance rule violations
    - Tag governance adherence
    - Best practice implementation
    """
    dashboard_service = DashboardService(db)
    
    try:
        security_data = await dashboard_service.get_security_score(
            aws_account_id=aws_account_id,
            include_trend=include_trend
        )
        return security_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get security score: {str(e)}")


@router.get("/tag-health")
async def get_tag_health(
    aws_account_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """
    🏷️ Get tag health metrics and compliance status
    
    Returns:
    - Tag coverage percentage
    - Policy compliance rate
    - Most/least tagged resource types
    - Tag consistency score
    """
    dashboard_service = DashboardService(db)
    
    try:
        tag_health = await dashboard_service.get_tag_health(
            aws_account_id=aws_account_id
        )
        return tag_health
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get tag health: {str(e)}")


@router.get("/recent-findings")
async def get_recent_findings(
    limit: int = Query(10, ge=1, le=50),
    severity: Optional[str] = Query(None, regex="^(CRITICAL|HIGH|MEDIUM|LOW)$"),
    aws_account_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """
    🚨 Get recent security findings
    """
    dashboard_service = DashboardService(db)
    
    try:
        findings = await dashboard_service.get_recent_findings(
            limit=limit,
            severity=severity,
            aws_account_id=aws_account_id
        )
        return findings
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get findings: {str(e)}")


@router.get("/metrics/time-series")
async def get_time_series_metrics(
    metric_name: str = Query(..., description="Metric name to retrieve"),
    start_time: datetime = Query(..., description="Start time for metrics"),
    end_time: datetime = Query(..., description="End time for metrics"),
    granularity: str = Query("1h", regex="^(5m|15m|1h|6h|1d)$", description="Data granularity"),
    aws_account_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """
    📈 Get time series metrics data for charts
    
    Available metrics:
    - security_score
    - tag_compliance_rate
    - findings_count
    - resource_count
    """
    dashboard_service = DashboardService(db)
    
    try:
        metrics = await dashboard_service.get_time_series_metrics(
            metric_name=metric_name,
            start_time=start_time,
            end_time=end_time,
            granularity=granularity,
            aws_account_id=aws_account_id
        )
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")


@router.get("/cost-allocation")
async def get_cost_allocation(
    time_range: str = Query("30d", regex="^(7d|30d|90d)$"),
    group_by: str = Query("tag", regex="^(tag|service|region|account)$"),
    aws_account_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """
    💰 Get cost allocation data based on tags
    
    Shows how costs are distributed across:
    - Tag values (Project, Environment, etc.)
    - AWS services
    - Regions
    - Accounts
    """
    dashboard_service = DashboardService(db)
    
    try:
        cost_data = await dashboard_service.get_cost_allocation(
            time_range=time_range,
            group_by=group_by,
            aws_account_id=aws_account_id
        )
        return cost_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get cost data: {str(e)}")


@router.get("/recommendations/summary")
async def get_recommendations_summary(
    aws_account_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """
    💡 Get summary of active recommendations
    
    Returns:
    - Tag recommendations count
    - Security recommendations
    - Cost optimization opportunities
    - Compliance improvements
    """
    dashboard_service = DashboardService(db)
    
    try:
        recommendations = await dashboard_service.get_recommendations_summary(
            aws_account_id=aws_account_id
        )
        return recommendations
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get recommendations: {str(e)}")
