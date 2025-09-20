"""
Response Validation System for Pydantic Models - Phase 2
This module provides validation and formatting utilities for structured responses.
"""

import re
import json
from typing import Union, Dict, Any, Optional
from pydantic import ValidationError

from structured_responses import (
    AgentResponse, 
    ResponseStatus, 
    ResponseType,
    SimpleResponse,
    ErrorResponse,
    ActionResponse,
    DataResponse,
    GmailResponse,
    CalendarResponse,
    DocsResponse,
    NotionResponse,
    GitHubResponse,
    get_response_model_for_app,
    create_simple_response,
    create_error_response,
    create_action_response
)


class ResponseValidator:
    """Validates and structures agent responses using Pydantic models."""
    
    def __init__(self):
        self.integration_keywords = {
            'gmail': ['email', 'gmail', 'inbox', 'message', 'sent', 'unread'],
            'google_calendar': ['calendar', 'meeting', 'event', 'schedule',
                               'appointment'],
            'google_docs': ['document', 'docs', 'google docs', 'file'],
            'notion': ['notion', 'page', 'workspace', 'database'],
            'github': ['github', 'repository', 'repo', 'issue', 'commit']
        }
    
    def detect_response_type(self, message: str, app_type: str = None) -> str:
        """Detect the appropriate response type based on content."""
        message_lower = message.lower()
        
        # Error detection
        error_indicators = [
            'error', 'failed', 'not connected', 'unauthorized', 
            'invalid', 'denied', 'expired'
        ]
        if any(indicator in message_lower for indicator in error_indicators):
            if 'not connected' in message_lower:
                return ResponseType.ACTION
            else:
                return ResponseType.SIMPLE
        
        # Action detection
        action_indicators = [
            'please connect', 'settings > integrations', 'need to',
            'must', 'should', 'try:'
        ]
        if any(indicator in message_lower for indicator in action_indicators):
            return ResponseType.ACTION
        
        # Data detection - look for numbers, counts, lists
        data_indicators = [
            r'\d+\s+(email|meeting|document|page|repo)', 
            r'found \d+', 
            r'\d+\s+unread',
            r'you have \d+'
        ]
        if any(re.search(pattern, message_lower) for pattern in data_indicators):
            return ResponseType.DATA
        
        return ResponseType.SIMPLE
    
    def detect_app_type(self, message: str) -> Optional[str]:
        """Detect integration type from message content."""
        message_lower = message.lower()
        
        for app_type, keywords in self.integration_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                return app_type
        
        return None
    
    def extract_structured_data(self, message: str, app_type: str) -> Dict[str, Any]:
        """Extract structured data from message based on app type."""
        data = {}
        message_lower = message.lower()
        
        # Extract numbers for counts
        numbers = re.findall(r'\d+', message)
        
        if app_type == 'gmail':
            # Look for email counts
            email_match = re.search(r'(\d+)\s+email', message_lower)
            if email_match:
                data['email_count'] = int(email_match.group(1))
            
            unread_match = re.search(r'(\d+)\s+unread', message_lower)
            if unread_match:
                data['unread_count'] = int(unread_match.group(1))
        
        elif app_type == 'google_calendar':
            # Look for event counts
            event_match = re.search(r'(\d+)\s+(meeting|event)', message_lower)
            if event_match:
                data['event_count'] = int(event_match.group(1))
            
            # Look for next event info
            next_match = re.search(r'next:?\s*(.+?)(?:\.|$)', message_lower)
            if next_match:
                data['next_event'] = next_match.group(1).strip()
        
        elif app_type == 'google_docs':
            # Look for document counts
            doc_match = re.search(r'(\d+)\s+document', message_lower)
            if doc_match:
                data['document_count'] = int(doc_match.group(1))
        
        elif app_type == 'notion':
            # Look for page counts
            page_match = re.search(r'(\d+)\s+page', message_lower)
            if page_match:
                data['page_count'] = int(page_match.group(1))
        
        elif app_type == 'github':
            # Look for repo/issue counts
            repo_match = re.search(r'(\d+)\s+(repo|repositor)', message_lower)
            if repo_match:
                data['repo_count'] = int(repo_match.group(1))
            
            issue_match = re.search(r'(\d+)\s+issue', message_lower)
            if issue_match:
                data['issue_count'] = int(issue_match.group(1))
            
            # Extract repo name
            repo_name_match = re.search(r'in\s+(\w+)\s+repo', message_lower)
            if repo_name_match:
                data['repo_name'] = repo_name_match.group(1)
        
        return data
    
    def create_structured_response(
        self, 
        message: str, 
        app_type: str = None,
        force_simple: bool = False
    ) -> AgentResponse:
        """Create a structured response from a message."""
        
        # Auto-detect app type if not provided
        if not app_type:
            app_type = self.detect_app_type(message) or 'general'
        
        # Force simple response if requested
        if force_simple:
            return create_simple_response(message, app_type=app_type)
        
        # Detect response type
        response_type = self.detect_response_type(message, app_type)
        
        # Determine status
        status = ResponseStatus.SUCCESS
        if 'error' in message.lower() or 'failed' in message.lower():
            status = ResponseStatus.ERROR
        elif 'not connected' in message.lower() or 'please connect' in message.lower():
            status = ResponseStatus.WARNING
        
        try:
            # Create appropriate response based on type
            if response_type == ResponseType.ACTION:
                action_required = self._extract_action_required(message)
                return create_action_response(
                    message=message,
                    action_required=action_required,
                    app_type=app_type
                )
            
            elif response_type == ResponseType.SIMPLE:
                return create_error_response(
                    message=message,
                    app_type=app_type,
                    error_code="AGENT_ERROR"
                )
            
            elif response_type == ResponseType.DATA:
                # Use integration-specific models for data responses
                return self._create_integration_response(message, app_type, status)
            
            else:
                # Simple response
                return create_simple_response(
                    message=message,
                    status=status,
                    app_type=app_type
                )
        
        except ValidationError as e:
            # Fallback to simple response if validation fails
            return create_simple_response(
                message=message,
                status=status,
                app_type=app_type
            )
    
    def _extract_action_required(self, message: str) -> str:
        """Extract action from message."""
        if 'not connected' in message.lower():
            return "Connect integration in Settings > Integrations"
        elif 'need more details' in message.lower():
            return "Provide more specific information"
        else:
            return "See message for required action"
    
    def _create_integration_response(
        self, 
        message: str, 
        app_type: str, 
        status: ResponseStatus
    ) -> AgentResponse:
        """Create integration-specific response with extracted data."""
        
        data = self.extract_structured_data(message, app_type)
        
        # Create app-specific response
        if app_type == 'gmail':
            return GmailResponse(
                status=status,
                message=message,
                app_type=app_type,
                email_count=data.get('email_count'),
                unread_count=data.get('unread_count')
            )
        
        elif app_type == 'google_calendar':
            return CalendarResponse(
                status=status,
                message=message,
                app_type=app_type,
                event_count=data.get('event_count'),
                next_event=data.get('next_event')
            )
        
        elif app_type == 'google_docs':
            return DocsResponse(
                status=status,
                message=message,
                app_type=app_type,
                document_count=data.get('document_count'),
                document_id=data.get('document_id')
            )
        
        elif app_type == 'notion':
            return NotionResponse(
                status=status,
                message=message,
                app_type=app_type,
                page_count=data.get('page_count'),
                page_id=data.get('page_id')
            )
        
        elif app_type == 'github':
            return GitHubResponse(
                status=status,
                message=message,
                app_type=app_type,
                repo_count=data.get('repo_count'),
                issue_count=data.get('issue_count'),
                repo_name=data.get('repo_name')
            )
        
        else:
            # Fallback to simple response
            return create_simple_response(
                message=message,
                status=status,
                app_type=app_type
            )
    
    def validate_response(self, response: AgentResponse) -> bool:
        """Validate a structured response."""
        try:
            # Check message length (Phase 1 requirement)
            words = len(response.message.split())
            if words > 50:
                return False
            
            # Validate the response structure
            response.dict()  # This will raise ValidationError if invalid
            return True
        
        except (ValidationError, AttributeError):
            return False
    
    def to_json(self, response: AgentResponse) -> str:
        """Convert response to JSON string."""
        return response.model_dump_json(indent=2)
    
    def to_dict(self, response: AgentResponse) -> Dict[str, Any]:
        """Convert response to dictionary."""
        return response.model_dump()


# Global validator instance
validator = ResponseValidator()


def create_structured_response(
    message: str, 
    app_type: str = None,
    force_simple: bool = False
) -> AgentResponse:
    """Convenience function to create structured responses."""
    return validator.create_structured_response(message, app_type, force_simple)


def validate_response(response: AgentResponse) -> bool:
    """Convenience function to validate responses."""
    return validator.validate_response(response)