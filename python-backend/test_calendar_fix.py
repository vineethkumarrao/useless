#!/usr/bin/env python3
"""
Quick Calendar Fix Test
Test the calendar timezone fix
"""

import sys
import os
from datetime import datetime, timedelta

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from langchain_tools import GoogleCalendarCreateTool

USER_ID = "7015e198-46ea-4090-a67f-da24718634c6"

def test_calendar_fix():
    """Test the calendar timezone fix"""
    print("🔧 Testing Calendar Timezone Fix")
    print(f"👤 User ID: {USER_ID}")
    
    try:
        # Create tomorrow 6 AM meeting with simpler datetime format
        tomorrow = datetime.now() + timedelta(days=1)
        start_dt = tomorrow.replace(hour=6, minute=0, second=0, microsecond=0)
        end_dt = tomorrow.replace(hour=7, minute=0, second=0, microsecond=0)
        
        # Use simple ISO format (the tool will fix timezone)
        start_time = start_dt.isoformat()
        end_time = end_dt.isoformat()
        
        print(f"📅 Creating event from {start_time} to {end_time}")
        
        calendar_tool = GoogleCalendarCreateTool()
        result = calendar_tool._run(
            USER_ID,
            "Daily Standup - Timezone Fixed",
            start_time,
            end_time,
            "Testing timezone fix for calendar events",
            "America/New_York",  # Proper timezone
            "primary"
        )
        
        print(f"📝 Result: {result}")
        
        if "Successfully created" in result:
            print("✅ Calendar timezone fix working!")
            return True
        else:
            print("❌ Calendar timezone fix failed")
            return False
            
    except Exception as e:
        print(f"💥 Error: {e}")
        return False

if __name__ == "__main__":
    test_calendar_fix()