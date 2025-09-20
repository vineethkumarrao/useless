# Normal Chat Test Results
**Generated:** 2025-09-20T09:13:11.003095
**Test User:** 7015e198-46ea-4090-a67f-da24718634c6
**Total Tests:** 12

## Summary

- ✅ Successful Tests: 12/12
- ❌ Failed Tests: 0/12
- 📊 Average Quality Score: 8.5/10
- ⏱️ Average Response Time: 10.24s

## Detailed Results

### Test 1: Agent OFF - General greeting

**Message:** Hello, how are you?
**Agent Mode:** OFF
**Duration:** 9.33s
**Response Length:** 101 characters

**Status:** ✅ SUCCESS
**Quality Score:** 9/10
**Issues:** Poor formatting - no line breaks in long response

**Response:**
```
Hello! I'm functioning perfectly and ready to help, thank you for asking. How can I assist you today?
```

### Test 2: Agent OFF - Simple question

**Message:** What's the weather like today?
**Agent Mode:** OFF
**Duration:** 15.05s
**Response Length:** 157 characters

**Status:** ✅ SUCCESS
**Quality Score:** 9/10
**Issues:** Poor formatting - no line breaks in long response

**Response:**
```
Today, it's overcast and 28°C in Harbour Island, Bahamas. Meanwhile, the United States is experiencing clear and cool weather, with temperatures around 16°C.
```

### Test 3: Agent OFF - Gmail request (should suggest agent mode)

**Message:** Show me my recent emails
**Agent Mode:** OFF
**Duration:** 15.67s
**Response Length:** 56 characters

**Status:** ✅ SUCCESS
**Quality Score:** 7/10
**Issues:** Should suggest switching to agent mode ON

**Response:**
```
Hi there! I'm here to help. What would you like to know?
```

### Test 4: Agent OFF - Calendar request (should suggest agent mode)

**Message:** What's on my calendar today?
**Agent Mode:** OFF
**Duration:** 13.06s
**Response Length:** 109 characters

**Status:** ✅ SUCCESS
**Quality Score:** 6/10
**Issues:** Should suggest switching to agent mode ON, Poor formatting - no line breaks in long response

**Response:**
```
It looks like you have no scheduled events today. You can check Google Calendar for more details if you like!
```

### Test 5: Agent OFF - GitHub request (should suggest agent mode)

**Message:** List my repositories
**Agent Mode:** OFF
**Duration:** 7.99s
**Response Length:** 56 characters

**Status:** ✅ SUCCESS
**Quality Score:** 10/10
**Issues:** None

**Response:**
```
Hi there! I'm here to help. What would you like to know?
```

### Test 6: Agent OFF - Notion request (should suggest agent mode)

**Message:** Search my Notion pages
**Agent Mode:** OFF
**Duration:** 9.29s
**Response Length:** 168 characters

**Status:** ✅ SUCCESS
**Quality Score:** 6/10
**Issues:** Should suggest switching to agent mode ON, Poor formatting - no line breaks in long response

**Response:**
```
I can't directly access your personal Notion pages to search them for you. To find what you're looking for, please use the search bar within your Notion app or browser.
```

### Test 7: Agent OFF - Google Docs request (should suggest agent mode)

**Message:** Show my recent documents
**Agent Mode:** OFF
**Duration:** 14.88s
**Response Length:** 56 characters

**Status:** ✅ SUCCESS
**Quality Score:** 7/10
**Issues:** Should suggest switching to agent mode ON

**Response:**
```
Hi there! I'm here to help. What would you like to know?
```

### Test 8: Agent ON - General question

**Message:** Tell me about artificial intelligence
**Agent Mode:** ON
**Duration:** 5.94s
**Response Length:** 56 characters

**Status:** ✅ SUCCESS
**Quality Score:** 10/10
**Issues:** None

**Response:**
```
Hi there! I'm here to help. What would you like to know?
```

### Test 9: Agent ON - Gmail basic request

**Message:** Show me my recent emails
**Agent Mode:** ON
**Duration:** 13.82s
**Response Length:** 95 characters

**Status:** ✅ SUCCESS
**Quality Score:** 10/10
**Issues:** None

**Response:**
```
Context: Recent conversation: Show me my recent emails; Show my recent documents... � Recent...
```

### Test 10: Agent ON - Calendar basic request

**Message:** What's on my calendar today?
**Agent Mode:** ON
**Duration:** 5.24s
**Response Length:** 99 characters

**Status:** ✅ SUCCESS
**Quality Score:** 10/10
**Issues:** None

**Response:**
```
📅 Upcoming events:
Upcoming Calendar Events (next 1 days):

1. Daily Standup - Timezone Fixed
  ...
```

### Test 11: Agent ON - Complex Gmail analysis

**Message:** Analyze my email patterns and give me insights
**Agent Mode:** ON
**Duration:** 2.37s
**Response Length:** 55 characters

**Status:** ✅ SUCCESS
**Quality Score:** 8/10
**Issues:** Contains error pattern: Error:

**Response:**
```
❌ Gmail error: name 'GmailAnalyticsTool' is not defined
```

### Test 12: Agent ON - Web search request

**Message:** What are the latest developments in AI?
**Agent Mode:** ON
**Duration:** 10.20s
**Response Length:** 72 characters

**Status:** ✅ SUCCESS
**Quality Score:** 10/10
**Issues:** None

**Response:**
```
I don't have real-time info, but I'm happy to help with other questions!
```

