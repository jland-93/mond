"""
🌙 Mond Security API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.core.database import get_db
from app.services.security_service import SecurityService

router = APIRouter()


@router.get("/findings")
async def get_security_findings(
    severity: Optional[str] = Query(None, regex="^(CRITICAL|HIGH|MEDIUM|LOW)$"),
    status: Optional[str] = Query(None, regex="^(NEW|NOTIFIED|RESOLVED|SUPPRESSED)$"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """
    🚨 Get security findings from AWS Security Hub
    """
    security_service = SecurityService(db)
    
    try:
        findings = await security_service.get_findings(
            severity=severity,
            status=status,
            limit=limit,
            offset=offset
        )
        return findings
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get findings: {str(e)}")


@router.get("/compliance")
async def get_compliance_status(
    framework: Optional[str] = Query(None, description="Compliance framework (CIS, SOC2, etc.)"),
    aws_account_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """
    📋 Get compliance status and rules
    """
    security_service = SecurityService(db)
    
    try:
        compliance = await security_service.get_compliance_status(
            framework=framework,
            aws_account_id=aws_account_id
        )
        return compliance
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get compliance: {str(e)}")


@router.post("/sync")
async def sync_security_data(
    aws_account_id: str = Query(..., description="AWS Account ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    🔄 Sync security data from AWS services
    """
    security_service = SecurityService(db)
    
    try:
        job_id = await security_service.sync_security_data(aws_account_id)
        return {"message": "Security sync initiated", "job_id": job_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to sync: {str(e)}")
