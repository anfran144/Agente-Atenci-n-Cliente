from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

# User models
class UserResponse(BaseModel):
    """Response model for user information"""
    id: str = Field(..., description="User ID")
    name: str = Field(..., description="User name")
    email: str = Field(..., description="User email")
    phone: Optional[str] = Field(None, description="User phone")
    preferences: Dict[str, Any] = Field(default_factory=dict, description="User preferences")
    is_active: bool = Field(True, description="Whether the user is active")

class UserPreferenceResponse(BaseModel):
    """Response model for learned user preferences"""
    id: str = Field(..., description="Preference ID")
    user_id: str = Field(..., description="User ID")
    tenant_id: str = Field(..., description="Tenant ID")
    preference_type: str = Field(..., description="Type of preference")
    preference_value: str = Field(..., description="Preference value")
    confidence: float = Field(..., description="Confidence score")
    learned_from_count: int = Field(..., description="Times detected")

# Request/Response models for /chat endpoint
class ChatRequest(BaseModel):
    """Request model for chat endpoint"""
    tenant_id: str = Field(..., description="ID of the tenant (business)")
    conversation_id: Optional[str] = Field(None, description="Existing conversation ID, if continuing a conversation")
    message: str = Field(..., description="User message text")
    user_id: Optional[str] = Field(None, description="User ID for personalization")
    customer_id: Optional[str] = Field(None, description="Optional customer identifier (deprecated, use user_id)")

class OrderSummary(BaseModel):
    """Order summary for confirmation"""
    products: List[Dict[str, Any]] = Field(..., description="List of products with quantities and prices")
    total: float = Field(..., description="Total order amount")

class ChatResponse(BaseModel):
    """Response model for chat endpoint"""
    conversation_id: str = Field(..., description="Conversation ID")
    response: str = Field(..., description="Agent response text")
    intent: str = Field(..., description="Classified intent of the message")
    requires_confirmation: bool = Field(..., description="Whether the response requires user confirmation")
    order_summary: Optional[OrderSummary] = Field(None, description="Order summary if intent is order-related")

# Tenant models
class TenantResponse(BaseModel):
    """Response model for tenant information"""
    id: str = Field(..., description="Tenant ID")
    name: str = Field(..., description="Business name")
    type: str = Field(..., description="Business type (restaurant, bakery, minimarket)")
    is_active: bool = Field(..., description="Whether the tenant is active")

# Stats models
class HourStat(BaseModel):
    """Statistics for a specific hour"""
    hour: int = Field(..., ge=0, le=23, description="Hour of day (0-23)")
    count: int = Field(..., ge=0, description="Number of interactions")

class ProductStat(BaseModel):
    """Statistics for a product"""
    product_id: str = Field(..., description="Product ID")
    name: str = Field(..., description="Product name")
    mentions: int = Field(..., ge=0, description="Number of mentions")

class CommonQuestion(BaseModel):
    """Common question statistics"""
    question: str = Field(..., description="Question text or pattern")
    frequency: int = Field(..., ge=0, description="Number of times asked")

class StatsResponse(BaseModel):
    """Response model for tenant statistics"""
    tenant_id: str = Field(..., description="Tenant ID")
    peak_hours: List[HourStat] = Field(..., description="Peak hours by interaction count")
    top_products: List[ProductStat] = Field(..., description="Most mentioned products")
    common_questions: List[CommonQuestion] = Field(..., description="Most common questions")

# Network insights models
class GlobalPattern(BaseModel):
    """Global pattern across all tenants"""
    pattern: str = Field(..., description="Description of the pattern")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    business_types: Optional[List[str]] = Field(None, description="Relevant business types")

class NetworkInsightsResponse(BaseModel):
    """Response model for network insights"""
    patterns: List[GlobalPattern] = Field(..., description="Detected global patterns")
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="When insights were generated")
