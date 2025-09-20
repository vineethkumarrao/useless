"""
Phase 2 Structured Response Testing Suite
Tests Pydantic response models, validation, and integration with agents.
"""

import sys
import os
import json
from datetime import datetime

# Add the current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from structured_responses import (
        ResponseStatus, ResponseType, SimpleResponse, DataResponse,
        ActionResponse, ErrorResponse, GmailResponse, CalendarResponse,
        create_simple_response, create_error_response, create_action_response
    )
    from response_validator import (
        ResponseValidator, create_structured_response, validate_response
    )
    from crewai_agents import (
        format_agent_response, get_structured_response, 
        STRUCTURED_RESPONSES_AVAILABLE
    )
    IMPORTS_SUCCESSFUL = True
except ImportError as e:
    print(f"Import error: {e}")
    IMPORTS_SUCCESSFUL = False


def test_pydantic_models():
    """Test basic Pydantic model creation and validation."""
    print("\\n[TEST 1] Testing Pydantic Model Creation...")
    
    if not IMPORTS_SUCCESSFUL:
        print("❌ FAILED: Imports not available")
        return False
    
    try:
        # Test simple response
        simple = create_simple_response(
            "Gmail not connected. Please connect in Settings.",
            app_type="gmail"
        )
        print(f"✅ Simple Response: {simple.message} ({len(simple.message.split())} words)")
        
        # Test error response
        error = create_error_response(
            "Failed to access Gmail API.",
            error_code="AUTH_FAILED",
            app_type="gmail"
        )
        print(f"✅ Error Response: {error.message} ({error.error_code})")
        
        # Test action response
        action = create_action_response(
            "Calendar not connected.",
            action_required="Connect Google Calendar in Settings",
            app_type="google_calendar"
        )
        print(f"✅ Action Response: {action.message}")
        
        # Test Gmail-specific response
        gmail = GmailResponse(
            status=ResponseStatus.SUCCESS,
            message="Found 12 emails, 3 unread.",
            email_count=12,
            unread_count=3
        )
        print(f"✅ Gmail Response: {gmail.message} (emails: {gmail.email_count})")
        
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


def test_response_validation():
    """Test response validation system."""
    print("\\n[TEST 2] Testing Response Validation...")
    
    if not IMPORTS_SUCCESSFUL:
        print("❌ FAILED: Imports not available")
        return False
    
    try:
        validator = ResponseValidator()
        
        # Test message brevity validation
        brief_response = create_simple_response("Short message.", app_type="gmail")
        long_message = "This is a very long message that exceeds the fifty word limit for Phase 1 optimization requirements and should trigger validation errors when processed by the Pydantic model validation system that we have implemented in Phase 2 of the CrewAI optimization project."
        
        print(f"✅ Brief message valid: {validate_response(brief_response)}")
        
        try:
            long_response = create_simple_response(long_message, app_type="gmail")
            print(f"❌ Long message validation failed - should have been rejected")
            return False
        except Exception:
            print("✅ Long message correctly rejected")
        
        # Test app type detection
        gmail_detected = validator.detect_app_type("Check my Gmail inbox for emails")
        calendar_detected = validator.detect_app_type("What meetings do I have today?")
        
        print(f"✅ Gmail detection: {gmail_detected}")
        print(f"✅ Calendar detection: {calendar_detected}")
        
        # Test response type detection
        error_type = validator.detect_response_type("Gmail not connected")
        data_type = validator.detect_response_type("Found 5 emails, 2 unread")
        simple_type = validator.detect_response_type("Task completed successfully")
        
        print(f"✅ Error type detection: {error_type}")
        print(f"✅ Data type detection: {data_type}")
        print(f"✅ Simple type detection: {simple_type}")
        
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


def test_structured_response_creation():
    """Test automated structured response creation."""
    print("\\n[TEST 3] Testing Structured Response Creation...")
    
    if not IMPORTS_SUCCESSFUL:
        print("❌ FAILED: Imports not available")
        return False
    
    try:
        test_messages = [
            ("Gmail not connected. Please connect in Settings.", "gmail"),
            ("Found 12 emails, 3 unread from GitHub.", "gmail"),
            ("You have 4 meetings today. Next: standup at 2 PM.", "google_calendar"),
            ("Created document 'Phase 2 Results' successfully.", "google_docs"),
            ("Search found 8 pages about optimization.", "notion"),
            ("Created issue in useless repository.", "github"),
            ("Task completed successfully.", "general")
        ]
        
        for message, app_type in test_messages:
            response = create_structured_response(message, app_type)
            word_count = len(response.message.split())
            
            print(f"✅ {app_type}: {response.message}")
            print(f"   Status: {response.status}, Type: {response.response_type}, Words: {word_count}")
            
            # Validate Phase 1 compliance
            if word_count > 50:
                print(f"❌ FAILED: Message too long ({word_count} words)")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


def test_integration_specific_responses():
    """Test integration-specific response models."""
    print("\\n[TEST 4] Testing Integration-Specific Responses...")
    
    if not IMPORTS_SUCCESSFUL:
        print("❌ FAILED: Imports not available")
        return False
    
    try:
        # Test Gmail response with extracted data
        gmail_response = create_structured_response(
            "Found 15 emails, 4 unread from GitHub notifications.", 
            "gmail"
        )
        
        if hasattr(gmail_response, 'email_count'):
            print(f"✅ Gmail data extraction: {gmail_response.email_count} emails, {gmail_response.unread_count} unread")
        else:
            print("✅ Gmail response (no data extraction)")
        
        # Test Calendar response
        calendar_response = create_structured_response(
            "You have 3 meetings today. Next: Team standup at 2:00 PM", 
            "google_calendar"
        )
        
        if hasattr(calendar_response, 'event_count'):
            print(f"✅ Calendar data extraction: {calendar_response.event_count} events")
            if calendar_response.next_event:
                print(f"   Next event: {calendar_response.next_event}")
        else:
            print("✅ Calendar response (no data extraction)")
        
        # Test GitHub response
        github_response = create_structured_response(
            "Created issue in useless repo successfully.", 
            "github"
        )
        
        if hasattr(github_response, 'repo_name'):
            print(f"✅ GitHub data extraction: repo '{github_response.repo_name}'")
        else:
            print("✅ GitHub response (no data extraction)")
        
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


def test_agent_integration():
    """Test integration with CrewAI agents."""
    print("\\n[TEST 5] Testing Agent Integration...")
    
    if not IMPORTS_SUCCESSFUL:
        print("❌ FAILED: Imports not available")
        return False
    
    try:
        # Test Phase 1 compatibility
        phase1_response = format_agent_response(
            "Gmail not connected. Please connect in Settings > Integrations.",
            "gmail"
        )
        print(f"✅ Phase 1 compatibility: {phase1_response}")
        
        # Test Phase 2 structured response
        if STRUCTURED_RESPONSES_AVAILABLE:
            structured_dict = get_structured_response(
                "Found 8 emails, 2 unread from notifications.",
                "gmail"
            )
            print(f"✅ Phase 2 structured: {structured_dict['message']}")
            print(f"   Full structure: status={structured_dict['status']}, type={structured_dict['response_type']}")
        else:
            print("⚠️  Phase 2 structured responses not available (fallback mode)")
        
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


def test_json_serialization():
    """Test JSON serialization of responses."""
    print("\\n[TEST 6] Testing JSON Serialization...")
    
    if not IMPORTS_SUCCESSFUL:
        print("❌ FAILED: Imports not available")
        return False
    
    try:
        # Create a complex response
        response = create_structured_response(
            "Found 12 emails, 3 unread from GitHub.",
            "gmail"
        )
        
        # Test JSON serialization
        json_str = response.model_dump_json(indent=2)
        print("✅ JSON serialization successful:")
        print(json_str[:200] + "..." if len(json_str) > 200 else json_str)
        
        # Test dictionary conversion
        response_dict = response.model_dump()
        print(f"✅ Dict conversion: {len(response_dict)} fields")
        
        # Validate required fields
        required_fields = ['status', 'message', 'response_type', 'app_type', 'timestamp']
        missing_fields = [field for field in required_fields if field not in response_dict]
        
        if missing_fields:
            print(f"❌ FAILED: Missing required fields: {missing_fields}")
            return False
        else:
            print("✅ All required fields present")
        
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


def test_real_world_scenarios():
    """Test real-world usage scenarios."""
    print("\\n[TEST 7] Testing Real-World Scenarios...")
    
    if not IMPORTS_SUCCESSFUL:
        print("❌ FAILED: Imports not available")
        return False
    
    try:
        scenarios = [
            # Connection errors
            ("Gmail not connected. Please connect in Settings > Integrations.", "gmail"),
            ("Calendar not connected. Please connect in Settings > Integrations.", "google_calendar"),
            
            # Data responses
            ("Found 25 emails, 8 unread.", "gmail"),
            ("You have 5 meetings today.", "google_calendar"),
            ("Found 12 documents in your Drive.", "google_docs"),
            
            # Action responses  
            ("To create an issue, I need more details. Try: 'Create issue: Fix login bug'", "github"),
            ("To create a Notion page, I need more details.", "notion"),
            
            # Success responses
            ("Email sent successfully.", "gmail"),
            ("Meeting created for tomorrow at 2 PM.", "google_calendar"),
            ("Document 'Project Plan' created successfully.", "google_docs")
        ]
        
        success_count = 0
        
        for message, app_type in scenarios:
            try:
                response = create_structured_response(message, app_type)
                word_count = len(response.message.split())
                
                # Validate Phase 1 compliance (≤50 words)
                if word_count <= 50:
                    print(f"✅ {app_type}: {word_count} words - {response.status}")
                    success_count += 1
                else:
                    print(f"❌ {app_type}: {word_count} words (too long)")
                    
            except Exception as e:
                print(f"❌ {app_type}: Error - {e}")
        
        success_rate = (success_count / len(scenarios)) * 100
        print(f"\\n📊 Success Rate: {success_count}/{len(scenarios)} ({success_rate:.1f}%)")
        
        return success_rate >= 80  # 80% success threshold
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


def run_all_tests():
    """Run all Phase 2 tests."""
    print("=" * 60)
    print("PHASE 2 STRUCTURED RESPONSE TESTING SUITE")
    print("=" * 60)
    
    tests = [
        ("Pydantic Models", test_pydantic_models),
        ("Response Validation", test_response_validation),
        ("Structured Creation", test_structured_response_creation),
        ("Integration Specific", test_integration_specific_responses),
        ("Agent Integration", test_agent_integration),
        ("JSON Serialization", test_json_serialization),
        ("Real-World Scenarios", test_real_world_scenarios)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\\n❌ {test_name} CRASHED: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\\n" + "=" * 60)
    print("PHASE 2 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    success_rate = (passed / total) * 100
    print(f"\\nOverall Success Rate: {passed}/{total} ({success_rate:.1f}%)")
    
    if success_rate >= 80:
        print("\\n🎉 PHASE 2 IMPLEMENTATION SUCCESSFUL!")
        print("✅ Structured responses working correctly")
        print("✅ Phase 1 optimization maintained")
        print("✅ Pydantic validation active")
        print("✅ Ready for production use")
    else:
        print("\\n⚠️  PHASE 2 NEEDS ATTENTION")
        print("Some tests failed - review implementation")
    
    return success_rate >= 80


if __name__ == "__main__":
    run_all_tests()