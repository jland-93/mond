"""
🌙 Mond Tag Management API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.core.database import get_db
from app.services.tag_service import TagService
from app.schemas.tag_schemas import (
    TagRecommendationResponse,
    TagPolicyCreate,
    TagPolicyResponse,
    ResourceTagResponse
)

router = APIRouter()


@router.get("/recommendations", response_model=List[TagRecommendationResponse])
async def get_tag_recommendations(
    resource_arn: str = Query(..., description="AWS Resource ARN"),
    resource_type: str = Query(..., description="AWS Resource Type"),
    limit: int = Query(5, ge=1, le=20, description="Number of recommendations"),
    db: AsyncSession = Depends(get_db)
):
    """
    🤖 Get AI-powered tag recommendations for a resource
    
    This endpoint uses machine learning to suggest relevant tags based on:
    - Resource type and configuration
    - Existing tag patterns in the organization
    - Compliance requirements
    - Historical tagging data
    """
    tag_service = TagService(db)
    
    try:
        recommendations = await tag_service.get_recommendations(
            resource_arn=resource_arn,
            resource_type=resource_type,
            limit=limit
        )
        return recommendations
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get recommendations: {str(e)}")


@router.post("/recommendations/{recommendation_id}/feedback")
async def submit_recommendation_feedback(
    recommendation_id: int,
    feedback: str = Query(..., regex="^(helpful|not_helpful|incorrect)$"),
    notes: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    📝 Submit feedback on tag recommendations to improve ML model
    """
    tag_service = TagService(db)
    
    try:
        await tag_service.submit_feedback(
            recommendation_id=recommendation_id,
            feedback=feedback,
            notes=notes
        )
        return {"message": "Feedback submitted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit feedback: {str(e)}")


@router.get("/policies", response_model=List[TagPolicyResponse])
async def get_tag_policies(
    mandatory_only: bool = Query(False, description="Filter mandatory policies only"),
    db: AsyncSession = Depends(get_db)
):
    """
    📋 Get tag policies and governance rules
    """
    tag_service = TagService(db)
    
    try:
        policies = await tag_service.get_policies(mandatory_only=mandatory_only)
        return policies
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get policies: {str(e)}")


@router.post("/policies", response_model=TagPolicyResponse)
async def create_tag_policy(
    policy: TagPolicyCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    ➕ Create a new tag policy
    """
    tag_service = TagService(db)
    
    try:
        new_policy = await tag_service.create_policy(policy)
        return new_policy
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create policy: {str(e)}")


@router.get("/compliance")
async def get_tag_compliance(
    aws_account_id: Optional[str] = Query(None, description="Filter by AWS Account ID"),
    region: Optional[str] = Query(None, description="Filter by AWS Region"),
    db: AsyncSession = Depends(get_db)
):
    """
    📊 Get tag compliance overview and metrics
    """
    tag_service = TagService(db)
    
    try:
        compliance_data = await tag_service.get_compliance_overview(
            aws_account_id=aws_account_id,
            region=region
        )
        return compliance_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get compliance data: {str(e)}")


@router.get("/resources", response_model=List[ResourceTagResponse])
async def get_resource_tags(
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    tag_key: Optional[str] = Query(None, description="Filter by tag key"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """
    🏷️ Get resource tagging information
    """
    tag_service = TagService(db)
    
    try:
        resources = await tag_service.get_resource_tags(
            resource_type=resource_type,
            tag_key=tag_key,
            limit=limit,
            offset=offset
        )
        return resources
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get resource tags: {str(e)}")


@router.post("/sync")
async def sync_aws_tags(
    aws_account_id: str = Query(..., description="AWS Account ID to sync"),
    region: Optional[str] = Query(None, description="AWS Region (all regions if not specified)"),
    db: AsyncSession = Depends(get_db)
):
    """
    🔄 Sync tags from AWS resources
    
    This endpoint triggers a background job to sync tag information
    from AWS services into Mond's database for analysis and recommendations.
    """
    tag_service = TagService(db)
    
    try:
        job_id = await tag_service.sync_aws_tags(
            aws_account_id=aws_account_id,
            region=region
        )
        return {
            "message": "Tag sync initiated",
            "job_id": job_id,
            "status": "running"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initiate sync: {str(e)}")
