"""
Pydantic Response Models for CrewAI Agent Optimization - Phase 2
This module defines structured response models for consistent agent outputs.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, Union, Literal
from enum import Enum
from datetime import datetime


class ResponseStatus(str, Enum):
    """Standardized response status values."""
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    PARTIAL = "partial"


class ResponseType(str, Enum):
    """Type of response content."""
    SIMPLE = "simple"           # Basic text response
    DATA = "data"              # Response with structured data
    ACTION = "action"          # Response requiring user action
    NOTIFICATION = "notification"  # Status/notification message


class BaseAgentResponse(BaseModel):
    """Base response model for all agent outputs."""
    status: ResponseStatus = Field(..., description="Response status")
    message: str = Field(
        ..., max_length=200, description="Main response message"
    )
    response_type: ResponseType = Field(
        default=ResponseType.SIMPLE, description="Type of response"
    )
    app_type: Optional[str] = Field(
        None, description="Integration type (gmail, calendar, etc.)"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now, description="Response timestamp"
    )
    
    @validator('message')
    def validate_message_brevity(cls, v):
        """Ensure message maintains Phase 1 brevity standards."""
        words = len(v.split())
        if words > 50:
            raise ValueError(f"Message too long: {words} words (max 50)")
        return v


class SimpleResponse(BaseAgentResponse):
    """Simple text-only response."""
    response_type: ResponseType = Field(default=ResponseType.SIMPLE)


class DataResponse(BaseAgentResponse):
    """Response containing structured data."""
    data: Dict[str, Any] = Field(..., description="Structured response data")
    data_summary: str = Field(
        ..., max_length=100, description="Brief summary of data"
    )
    response_type: ResponseType = Field(default=ResponseType.DATA)


class ActionResponse(BaseAgentResponse):
    """Response requiring user action."""
    action_required: str = Field(..., description="Action user needs to take")
    action_details: Optional[Dict[str, Any]] = Field(
        None, description="Additional action details"
    )
    response_type: ResponseType = Field(default=ResponseType.ACTION)


class ErrorResponse(BaseAgentResponse):
    """Error response with details."""
    error_code: Optional[str] = Field(
        None, description="Error code for debugging"
    )
    error_details: Optional[Dict[str, Any]] = Field(
        None, description="Detailed error information"
    )
    status: ResponseStatus = Field(default=ResponseStatus.ERROR)


class NotificationResponse(BaseAgentResponse):
    """Notification/status message."""
    priority: str = Field(
        default="normal", description="Notification priority"
    )
    expires_at: Optional[datetime] = Field(
        None, description="When notification expires"
    )
    response_type: ResponseType = Field(default=ResponseType.NOTIFICATION)


# Integration-specific response models
class GmailResponse(BaseAgentResponse):
    """Gmail-specific response model."""
    app_type: str = Field(default="gmail")
    email_count: Optional[int] = Field(
        None, description="Number of emails"
    )
    unread_count: Optional[int] = Field(
        None, description="Number of unread emails"
    )


class CalendarResponse(BaseAgentResponse):
    """Calendar-specific response model."""
    app_type: str = Field(default="google_calendar")
    event_count: Optional[int] = Field(
        None, description="Number of events"
    )
    next_event: Optional[str] = Field(
        None, description="Next upcoming event"
    )


class DocsResponse(BaseAgentResponse):
    """Google Docs-specific response model."""
    app_type: str = Field(default="google_docs")
    document_count: Optional[int] = Field(
        None, description="Number of documents"
    )
    document_id: Optional[str] = Field(
        None, description="Document ID for operations"
    )


class NotionResponse(BaseAgentResponse):
    """Notion-specific response model."""
    app_type: str = Field(default="notion")
    page_count: Optional[int] = Field(
        None, description="Number of pages"
    )
    page_id: Optional[str] = Field(
        None, description="Page ID for operations"
    )


class GitHubResponse(BaseAgentResponse):
    """GitHub-specific response model."""
    app_type: str = Field(default="github")
    repo_count: Optional[int] = Field(
        None, description="Number of repositories"
    )
    issue_count: Optional[int] = Field(
        None, description="Number of issues"
    )
    repo_name: Optional[str] = Field(
        None, description="Repository name"
    )


# Union type for all possible responses
AgentResponse = Union[
    SimpleResponse,
    DataResponse, 
    ActionResponse,
    ErrorResponse,
    NotificationResponse,
    GmailResponse,
    CalendarResponse,
    DocsResponse,
    NotionResponse,
    GitHubResponse
]


def get_response_model_for_app(app_type: str) -> type:
    """Get the appropriate response model for a given app type."""
    model_mapping = {
        'gmail': GmailResponse,
        'google_calendar': CalendarResponse,
        'google_docs': DocsResponse,
        'notion': NotionResponse,
        'github': GitHubResponse,
        'general': SimpleResponse
    }
    return model_mapping.get(app_type, SimpleResponse)


def create_simple_response(
    message: str, 
    status: ResponseStatus = ResponseStatus.SUCCESS, 
    app_type: str = None
) -> SimpleResponse:
    """Helper function to create simple responses."""
    return SimpleResponse(
        status=status,
        message=message,
        app_type=app_type
    )


def create_error_response(
    message: str, 
    error_code: str = None, 
    app_type: str = None, 
    error_details: Dict = None
) -> ErrorResponse:
    """Helper function to create error responses."""
    return ErrorResponse(
        status=ResponseStatus.ERROR,
        message=message,
        error_code=error_code,
        error_details=error_details,
        app_type=app_type
    )


def create_action_response(
    message: str, 
    action_required: str, 
    app_type: str = None, 
    action_details: Dict = None
) -> ActionResponse:
    """Helper function to create action responses."""
    return ActionResponse(
        status=ResponseStatus.WARNING,
        message=message,
        action_required=action_required,
        action_details=action_details,
        app_type=app_type
    )