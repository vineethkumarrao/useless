#!/usr/bin/env python3
"""
Test Phase 1 CrewAI Optimization Implementation
This script demonstrates the response template system and optimized formatting.
"""

from crewai_agents import format_agent_response

def test_phase1_optimization():
    """Test the Phase 1 optimization features."""
    print("🚀 Testing Phase 1 CrewAI Optimization")
    print("=" * 50)
    
    # Test Gmail Response Formatting
    print("\n📧 Gmail Response Tests:")
    test_cases = [
        ("Found 12 emails in your inbox. Here are the recent ones from today...", "gmail"),
        ("Gmail not connected to your account", "gmail"),
        ("Email sent successfully to john@example.com", "gmail"),
        ("Deleted 3 emails from spam folder", "gmail"),
    ]
    
    for original, app_type in test_cases:
        formatted = format_agent_response(original, app_type)
        print(f"  Original: {original[:50]}...")
        print(f"  Optimized: {formatted}")
        print()
    
    # Test Calendar Response Formatting
    print("📅 Calendar Response Tests:")
    calendar_tests = [
        ("Created a meeting for next Monday at 2pm with the team", "google_calendar"),
        ("Google Calendar not connected to your account", "google_calendar"),
        ("Found 7 events scheduled for this week", "google_calendar"),
        ("Updated the meeting time from 2pm to 3pm", "google_calendar"),
    ]
    
    for original, app_type in calendar_tests:
        formatted = format_agent_response(original, app_type)
        print(f"  Original: {original}")
        print(f"  Optimized: {formatted}")
        print()
    
    # Test Other Apps
    print("📝 Multi-App Response Tests:")
    multi_tests = [
        ("Created a new document titled 'Project Plan' with 500 words", "google_docs"),
        ("Found 15 pages in your Notion workspace related to projects", "notion"),
        ("Listed 8 repositories in your GitHub account", "github"),
        ("This is a general response that should be kept concise and helpful", "general"),
    ]
    
    for original, app_type in multi_tests:
        formatted = format_agent_response(original, app_type)
        print(f"  {app_type.title()}: {formatted}")
    
    print("\n✅ Phase 1 Optimization Test Complete!")
    print("🎯 Key Improvements Demonstrated:")
    print("  • Response templates for consistent formatting")
    print("  • Automatic brevity (50-100 word limit)")
    print("  • App-specific response patterns")
    print("  • Error message standardization")
    print("  • Fallback handling for edge cases")

if __name__ == "__main__":
    test_phase1_optimization()