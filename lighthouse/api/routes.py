"""API routes for Lighthouse.ai"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any

router = APIRouter()

@router.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Lighthouse.ai API", "status": "running"}

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
