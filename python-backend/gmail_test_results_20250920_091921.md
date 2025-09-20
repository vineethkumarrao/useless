# Gmail Test Results
**Generated:** 2025-09-20T09:19:21.756364
**Test User:** 7015e198-46ea-4090-a67f-da24718634c6
**Total Tests:** 15

## Summary

- ✅ Successful Tests: 15/15
- ❌ Failed Tests: 0/15
- 📊 Average Quality Score: 9.2/10
- 📧 Tests with Real Data: 14/15
- ⏱️ Average Response Time: 8.15s

## Test Categories Performance
- **Read**: 4 tests, avg 10.0/10, 4 with real data
- **Search**: 3 tests, avg 9.3/10, 3 with real data
- **Analytics**: 3 tests, avg 8.0/10, 3 with real data
- **Organize**: 2 tests, avg 9.0/10, 2 with real data
- **Batch**: 2 tests, avg 9.0/10, 1 with real data
- **Advanced**: 1 tests, avg 10.0/10, 1 with real data

## Detailed Results

### Test 1: Read Recent Emails

**Category:** read
**Message:** Show me my recent emails
**Duration:** 17.87s
**Response Length:** 99 characters

**Status:** ✅ SUCCESS
**Quality Score:** 10/10
**Has Real Data:** ✅
**Has Errors:** ✅
**Issues:** None

**Response:**
```
� Recent emails:
Found 5 emails:

Email 1:
Subject: Delivery Status Notification (Failure)
From:...
```

### Test 2: Read Latest 10 Emails

**Category:** read
**Message:** Show me my latest 10 emails
**Duration:** 6.82s
**Response Length:** 98 characters

**Status:** ✅ SUCCESS
**Quality Score:** 10/10
**Has Real Data:** ✅
**Has Errors:** ✅
**Issues:** None

**Response:**
```
Context: Recent conversation: Show me my recent emails; � Recent emails:
Found 5 emails:

Email...
```

### Test 3: Check Unread Emails

**Category:** read
**Message:** How many unread emails do I have?
**Duration:** 8.05s
**Response Length:** 102 characters

**Status:** ✅ SUCCESS
**Quality Score:** 10/10
**Has Real Data:** ✅
**Has Errors:** ✅
**Issues:** None

**Response:**
```
Context: Recent conversation: Show me my latest 10 emails; Context: Recent conversation: Show me my...
```

### Test 4: Show Today's Emails

**Category:** read
**Message:** Show me emails from today
**Duration:** 7.78s
**Response Length:** 96 characters

**Status:** ✅ SUCCESS
**Quality Score:** 10/10
**Has Real Data:** ✅
**Has Errors:** ✅
**Issues:** None

**Response:**
```
Context: Recent conversation: Show me my recent emails; Show me my latest 10 emails; Context:...
```

### Test 5: Search Emails by Sender

**Category:** search
**Message:** Find emails from gmail team
**Duration:** 6.69s
**Response Length:** 102 characters

**Status:** ✅ SUCCESS
**Quality Score:** 8/10
**Has Real Data:** ✅
**Has Errors:** ✅
**Issues:** Search operation should mention search results

**Response:**
```
Context: Recent conversation: Show me my recent emails; Show me my latest 10 emails; Show me emails...
```

### Test 6: Search Project Emails

**Category:** search
**Message:** Search for emails about 'project'
**Duration:** 7.85s
**Response Length:** 102 characters

**Status:** ✅ SUCCESS
**Quality Score:** 10/10
**Has Real Data:** ✅
**Has Errors:** ✅
**Issues:** None

**Response:**
```
Context: Recent conversation: Show me emails from today; Show me my recent emails; Find emails from...
```

### Test 7: Search Important Emails

**Category:** search
**Message:** Find important emails
**Duration:** 7.74s
**Response Length:** 102 characters

**Status:** ✅ SUCCESS
**Quality Score:** 10/10
**Has Real Data:** ✅
**Has Errors:** ✅
**Issues:** None

**Response:**
```
Context: Recent conversation: Show me emails from today; Show me my recent emails; Find emails from...
```

### Test 8: Email Analytics

**Category:** analytics
**Message:** Analyze my email patterns and give me insights
**Duration:** 8.45s
**Response Length:** 102 characters

**Status:** ✅ SUCCESS
**Quality Score:** 8/10
**Has Real Data:** ✅
**Has Errors:** ✅
**Issues:** Analytics operation should provide insights

**Response:**
```
Context: Recent conversation: Show me my recent emails; Find important emails; Show me my latest 10...
```

### Test 9: Email Volume Analysis

**Category:** analytics
**Message:** How many emails do I receive per day on average?
**Duration:** 7.30s
**Response Length:** 101 characters

**Status:** ✅ SUCCESS
**Quality Score:** 8/10
**Has Real Data:** ✅
**Has Errors:** ✅
**Issues:** Analytics operation should provide insights

**Response:**
```
Context: Recent conversation: How many unread emails do I have?; Show me my latest 10 emails; Show...
```

### Test 10: Top Senders Analysis

**Category:** analytics
**Message:** Who are my top email senders?
**Duration:** 7.13s
**Response Length:** 102 characters

**Status:** ✅ SUCCESS
**Quality Score:** 8/10
**Has Real Data:** ✅
**Has Errors:** ✅
**Issues:** Analytics operation should provide insights

**Response:**
```
Context: Recent conversation: Show me my latest 10 emails; Find important emails; Show me my recent...
```

### Test 11: Filter Management

**Category:** organize
**Message:** Help me organize and filter my inbox
**Duration:** 7.72s
**Response Length:** 96 characters

**Status:** ✅ SUCCESS
**Quality Score:** 8/10
**Has Real Data:** ✅
**Has Errors:** ✅
**Issues:** Organization operation should mention organizing

**Response:**
```
Context: Recent conversation: Show me my latest 10 emails; Show me my recent emails; How many...
```

### Test 12: Label Management

**Category:** organize
**Message:** Show me my email labels and organize them
**Duration:** 7.29s
**Response Length:** 101 characters

**Status:** ✅ SUCCESS
**Quality Score:** 10/10
**Has Real Data:** ✅
**Has Errors:** ✅
**Issues:** None

**Response:**
```
Context: Recent conversation: Help me organize and filter my inbox; Show me my recent emails; Show...
```

### Test 13: Batch Operations

**Category:** batch
**Message:** Perform batch operations on old emails
**Duration:** 7.25s
**Response Length:** 96 characters

**Status:** ✅ SUCCESS
**Quality Score:** 8/10
**Has Real Data:** ❌
**Has Errors:** ✅
**Issues:** Batch operation should mention bulk actions

**Response:**
```
Context: Recent conversation: Show me my email labels and organize them; Show me my latest 10...
```

### Test 14: Archive Old Emails

**Category:** batch
**Message:** Archive emails older than 30 days
**Duration:** 7.06s
**Response Length:** 101 characters

**Status:** ✅ SUCCESS
**Quality Score:** 10/10
**Has Real Data:** ✅
**Has Errors:** ✅
**Issues:** None

**Response:**
```
Context: Recent conversation: Perform batch operations on old emails; Show me my latest 10 emails;...
```

### Test 15: Email Summaries

**Category:** advanced
**Message:** Summarize my recent important emails
**Duration:** 7.20s
**Response Length:** 101 characters

**Status:** ✅ SUCCESS
**Quality Score:** 10/10
**Has Real Data:** ✅
**Has Errors:** ✅
**Issues:** None

**Response:**
```
Context: Recent conversation: Show me my recent emails; Find important emails; Show me emails from...
```

