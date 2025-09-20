# Calendar Test Results
**Generated:** 2025-09-20T09:23:51.190833
**Test User:** 7015e198-46ea-4090-a67f-da24718634c6
**Total Tests:** 15

## Summary

- ✅ Successful Tests: 15/15
- ❌ Failed Tests: 0/15
- 📊 Average Quality Score: 7.0/10
- 📅 Tests with Real Data: 15/15
- ⏱️ Average Response Time: 5.93s

## Test Categories Performance
- **View**: 4 tests, avg 10.0/10, 4 with real data
- **Create**: 2 tests, avg 8.5/10, 2 with real data
- **Modify**: 1 tests, avg 8.0/10, 1 with real data
- **Availability**: 3 tests, avg 9.3/10, 3 with real data
- **Analytics**: 2 tests, avg 1.0/10, 2 with real data
- **Optimization**: 1 tests, avg 0.0/10, 1 with real data
- **Reminders**: 1 tests, avg 0.0/10, 1 with real data
- **Summary**: 1 tests, avg 10.0/10, 1 with real data

## Detailed Results

### Test 1: View Today's Events

**Category:** view
**Message:** What's on my calendar today?
**Duration:** 16.05s
**Response Length:** 100 characters

**Status:** ✅ SUCCESS
**Quality Score:** 10/10
**Has Real Data:** ✅
**Has Errors:** ✅
**Issues:** None

**Response:**
```
📅 Today's schedule:
Upcoming Calendar Events (next 1 days):

1. Daily Standup - Timezone Fixed
  ...
```

### Test 2: View This Week Events

**Category:** view
**Message:** Show me my calendar for this week
**Duration:** 4.66s
**Response Length:** 99 characters

**Status:** ✅ SUCCESS
**Quality Score:** 10/10
**Has Real Data:** ✅
**Has Errors:** ✅
**Issues:** None

**Response:**
```
📅 Upcoming events:
Upcoming Calendar Events (next 7 days):

1. Daily Standup - Timezone Fixed
  ...
```

### Test 3: View Next Week Schedule

**Category:** view
**Message:** What do I have scheduled for next week?
**Duration:** 5.04s
**Response Length:** 99 characters

**Status:** ✅ SUCCESS
**Quality Score:** 10/10
**Has Real Data:** ✅
**Has Errors:** ✅
**Issues:** None

**Response:**
```
📅 Upcoming events:
Upcoming Calendar Events (next 7 days):

1. Daily Standup - Timezone Fixed
  ...
```

### Test 4: View Upcoming Events

**Category:** view
**Message:** Show me my upcoming events
**Duration:** 5.06s
**Response Length:** 99 characters

**Status:** ✅ SUCCESS
**Quality Score:** 10/10
**Has Real Data:** ✅
**Has Errors:** ✅
**Issues:** None

**Response:**
```
📅 Upcoming events:
Upcoming Calendar Events (next 7 days):

1. Daily Standup - Timezone Fixed
  ...
```

### Test 5: Create Meeting

**Category:** create
**Message:** Schedule a meeting with team tomorrow at 2 PM
**Duration:** 4.81s
**Response Length:** 99 characters

**Status:** ✅ SUCCESS
**Quality Score:** 8/10
**Has Real Data:** ✅
**Has Errors:** ✅
**Issues:** Create operation should confirm event creation

**Response:**
```
📅 Upcoming events:
Upcoming Calendar Events (next 7 days):

1. Daily Standup - Timezone Fixed
  ...
```

### Test 6: Create Personal Event

**Category:** create
**Message:** Add a personal appointment for doctor visit next Friday at 10 AM
**Duration:** 8.47s
**Response Length:** 167 characters

**Status:** ✅ SUCCESS
**Quality Score:** 9/10
**Has Real Data:** ✅
**Has Errors:** ✅
**Issues:** Poor formatting - no line breaks in long response

**Response:**
```
Okay, I've added your personal appointment for a doctor visit next Friday at 10 AM. If you're interested, there are also telehealth options available for virtual care.
```

### Test 7: Update Meeting Time

**Category:** modify
**Message:** Move my next meeting to 3 PM instead
**Duration:** 5.08s
**Response Length:** 99 characters

**Status:** ✅ SUCCESS
**Quality Score:** 8/10
**Has Real Data:** ✅
**Has Errors:** ✅
**Issues:** Modify operation should confirm changes

**Response:**
```
📅 Upcoming events:
Upcoming Calendar Events (next 7 days):

1. Daily Standup - Timezone Fixed
  ...
```

### Test 8: Check Availability

**Category:** availability
**Message:** When am I free tomorrow afternoon?
**Duration:** 7.86s
**Response Length:** 61 characters

**Status:** ✅ SUCCESS
**Quality Score:** 10/10
**Has Real Data:** ✅
**Has Errors:** ✅
**Issues:** None

**Response:**
```
You're free tomorrow afternoon! You have no scheduled events.
```

### Test 9: Find Meeting Slot

**Category:** availability
**Message:** When can I schedule a 1-hour meeting this week?
**Duration:** 5.26s
**Response Length:** 99 characters

**Status:** ✅ SUCCESS
**Quality Score:** 10/10
**Has Real Data:** ✅
**Has Errors:** ✅
**Issues:** None

**Response:**
```
📅 Upcoming events:
Upcoming Calendar Events (next 7 days):

1. Daily Standup - Timezone Fixed
  ...
```

### Test 10: Check Conflicts

**Category:** availability
**Message:** Do I have any scheduling conflicts this week?
**Duration:** 9.75s
**Response Length:** 91 characters

**Status:** ✅ SUCCESS
**Quality Score:** 8/10
**Has Real Data:** ✅
**Has Errors:** ✅
**Issues:** Availability operation should mention free/busy times

**Response:**
```
You have no scheduling conflicts this week! Your calendar is clear for the next seven days.
```

### Test 11: Meeting Analytics

**Category:** analytics
**Message:** Analyze my meeting patterns and give insights
**Duration:** 2.87s
**Response Length:** 90 characters

**Status:** ✅ SUCCESS
**Quality Score:** 1/10
**Has Real Data:** ✅
**Has Errors:** ❌
**Issues:** Contains error pattern: Calendar error:, Contains error pattern: ❌ Calendar error:, Contains error pattern: Error:

**Response:**
```
❌ Calendar error: CalendarAnalyticsTool._arun() got an unexpected keyword argument 'query'
```

### Test 12: Time Usage Analysis

**Category:** analytics
**Message:** How much time do I spend in meetings?
**Duration:** 2.80s
**Response Length:** 90 characters

**Status:** ✅ SUCCESS
**Quality Score:** 1/10
**Has Real Data:** ✅
**Has Errors:** ❌
**Issues:** Contains error pattern: Calendar error:, Contains error pattern: ❌ Calendar error:, Contains error pattern: Error:

**Response:**
```
❌ Calendar error: CalendarAnalyticsTool._arun() got an unexpected keyword argument 'query'
```

### Test 13: Calendar Optimization

**Category:** optimization
**Message:** Help me optimize my calendar and reduce meeting overload
**Duration:** 3.08s
**Response Length:** 90 characters

**Status:** ✅ SUCCESS
**Quality Score:** 0/10
**Has Real Data:** ✅
**Has Errors:** ❌
**Issues:** Contains error pattern: Calendar error:, Contains error pattern: ❌ Calendar error:, Contains error pattern: Error:, Optimization operation should provide suggestions

**Response:**
```
❌ Calendar error: CalendarAnalyticsTool._arun() got an unexpected keyword argument 'query'
```

### Test 14: Event Reminders

**Category:** reminders
**Message:** Set up reminders for my important meetings
**Duration:** 3.13s
**Response Length:** 90 characters

**Status:** ✅ SUCCESS
**Quality Score:** 0/10
**Has Real Data:** ✅
**Has Errors:** ❌
**Issues:** Contains error pattern: Calendar error:, Contains error pattern: ❌ Calendar error:, Contains error pattern: Error:, Reminder operation should mention notifications

**Response:**
```
❌ Calendar error: CalendarAnalyticsTool._arun() got an unexpected keyword argument 'query'
```

### Test 15: Calendar Summary

**Category:** summary
**Message:** Give me a summary of my calendar for tomorrow
**Duration:** 4.98s
**Response Length:** 99 characters

**Status:** ✅ SUCCESS
**Quality Score:** 10/10
**Has Real Data:** ✅
**Has Errors:** ✅
**Issues:** None

**Response:**
```
📅 Upcoming events:
Upcoming Calendar Events (next 7 days):

1. Daily Standup - Timezone Fixed
  ...
```

