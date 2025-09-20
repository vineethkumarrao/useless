"""
Test Phase 1 optimization with real user who has all 5 apps connected.
User: test@example.com - Connected to Gmail, Calendar, Docs, Notion, GitHub
"""

import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from crewai_agents import process_user_query_async


async def test_real_user_with_all_apps():
    """Test optimized responses with real user who has all apps connected."""
    
    user_id = "test@example.com"
    conversation_id = "test_optimization_conv"
    
    print("=" * 80)
    print("PHASE 1 OPTIMIZATION TEST - Real User with All Apps Connected")
    print("User:", user_id)
    print("=" * 80)
    
    # Test cases for each app with realistic requests
    test_cases = [
        # Gmail tests
        {
            "app": "Gmail",
            "message": "Check my recent emails and tell me if there's anything important",
            "expected_brevity": True
        },
        {
            "app": "Gmail", 
            "message": "Send an email to vineethkumarrao@gmail.com saying 'Phase 1 optimization test successful'",
            "expected_brevity": True
        },
        {
            "app": "Gmail",
            "message": "Search for emails from github and show me the latest ones",
            "expected_brevity": True
        },
        
        # Calendar tests
        {
            "app": "Calendar",
            "message": "What's my schedule for today?",
            "expected_brevity": True
        },
        {
            "app": "Calendar",
            "message": "Create a meeting for tomorrow at 2PM called 'Phase 1 Review' for 1 hour",
            "expected_brevity": True
        },
        {
            "app": "Calendar",
            "message": "Do I have any conflicts this week?",
            "expected_brevity": True
        },
        
        # Google Docs tests
        {
            "app": "Docs",
            "message": "List my recent documents",
            "expected_brevity": True
        },
        {
            "app": "Docs",
            "message": "Create a new document called 'Phase 1 Test Results'",
            "expected_brevity": True
        },
        {
            "app": "Docs",
            "message": "Read the content of my latest document",
            "expected_brevity": True
        },
        
        # Notion tests
        {
            "app": "Notion",
            "message": "Search my Notion workspace for 'optimization' notes",
            "expected_brevity": True
        },
        {
            "app": "Notion",
            "message": "Create a new page about Phase 1 implementation results",
            "expected_brevity": True
        },
        {
            "app": "Notion",
            "message": "Show me my recent Notion pages",
            "expected_brevity": True
        },
        
        # GitHub tests
        {
            "app": "GitHub",
            "message": "List my repositories and their latest activity",
            "expected_brevity": True
        },
        {
            "app": "GitHub",
            "message": "Create an issue in my useless repo about Phase 1 completion",
            "expected_brevity": True
        },
        {
            "app": "GitHub",
            "message": "Show me open issues in my repositories",
            "expected_brevity": True
        },
        
        # General conversation tests
        {
            "app": "General",
            "message": "How can you help me be more productive?",
            "expected_brevity": True
        },
        {
            "app": "General",
            "message": "What integrations do I have connected?",
            "expected_brevity": True
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n[TEST {i}] {test_case['app']} - {test_case['message'][:50]}...")
        print("-" * 60)
        
        try:
            # Process the query
            response = await process_user_query_async(
                message=test_case['message'],
                user_id=user_id,
                agent_mode=True,
                conversation_id=conversation_id,
                conversation_history=[]
            )
            
            # Analyze response
            word_count = len(response.split())
            sentence_count = len([s for s in response.split('.') if s.strip()])
            
            # Check if optimization worked
            is_brief = word_count <= 50  # Target: under 50 words
            is_concise = sentence_count <= 3  # Target: 1-3 sentences
            
            # Display results
            print(f"RESPONSE: {response}")
            print(f"ANALYSIS:")
            print(f"  - Word count: {word_count} {'✅' if is_brief else '❌'} (target: ≤50)")
            print(f"  - Sentences: {sentence_count} {'✅' if is_concise else '❌'} (target: ≤3)")
            
            # Check for structured elements
            has_action = any(keyword in response.lower() for keyword in ['action:', 'status:', 'result:', 'created', 'found', 'sent'])
            print(f"  - Has action info: {'✅' if has_action else '❌'}")
            
            # Overall assessment
            optimization_success = is_brief and is_concise
            print(f"  - Optimization: {'✅ SUCCESS' if optimization_success else '❌ NEEDS WORK'}")
            
            results.append({
                'app': test_case['app'],
                'message': test_case['message'],
                'response': response,
                'word_count': word_count,
                'sentence_count': sentence_count,
                'optimization_success': optimization_success,
                'has_action_info': has_action
            })
            
        except Exception as e:
            print(f"ERROR: {e}")
            results.append({
                'app': test_case['app'],
                'message': test_case['message'],
                'response': f"ERROR: {e}",
                'word_count': 0,
                'sentence_count': 0,
                'optimization_success': False,
                'has_action_info': False
            })
    
    # Summary Report
    print("\n" + "=" * 80)
    print("PHASE 1 OPTIMIZATION SUMMARY REPORT")
    print("=" * 80)
    
    successful_optimizations = sum(1 for r in results if r['optimization_success'])
    total_tests = len(results)
    avg_word_count = sum(r['word_count'] for r in results if r['word_count'] > 0) / max(1, len([r for r in results if r['word_count'] > 0]))
    
    print(f"Overall Success Rate: {successful_optimizations}/{total_tests} ({successful_optimizations/total_tests*100:.1f}%)")
    print(f"Average Word Count: {avg_word_count:.1f} words (target: ≤50)")
    
    # App-specific results
    apps = ['Gmail', 'Calendar', 'Docs', 'Notion', 'GitHub', 'General']
    for app in apps:
        app_results = [r for r in results if r['app'] == app]
        if app_results:
            app_success = sum(1 for r in app_results if r['optimization_success'])
            app_total = len(app_results)
            avg_words = sum(r['word_count'] for r in app_results if r['word_count'] > 0) / max(1, len([r for r in app_results if r['word_count'] > 0]))
            print(f"{app}: {app_success}/{app_total} success, avg {avg_words:.1f} words")
    
    # Specific examples
    print(f"\nBEST EXAMPLES (shortest responses):")
    sorted_results = sorted([r for r in results if r['word_count'] > 0], key=lambda x: x['word_count'])
    for r in sorted_results[:3]:
        print(f"  - {r['app']}: {r['word_count']} words - '{r['response'][:100]}...'")
    
    print(f"\nNEEDS IMPROVEMENT (longest responses):")
    for r in sorted_results[-3:]:
        print(f"  - {r['app']}: {r['word_count']} words - '{r['response'][:100]}...'")
    
    print("\n" + "=" * 80)
    print("PHASE 1 TEST COMPLETE")
    print("=" * 80)
    
    return results

async def test_before_after_comparison():
    """Test to show before/after optimization comparison."""
    
    print("\n" + "=" * 80)
    print("BEFORE/AFTER OPTIMIZATION COMPARISON")
    print("=" * 80)
    
    user_id = "test@example.com"
    
    # Simulate typical verbose responses (what we had before)
    before_responses = {
        "gmail": "I have successfully accessed your Gmail account and retrieved your recent emails. After carefully reviewing your inbox, I found several important messages that require your attention. The most recent email is from your colleague regarding the project deadline, and there are also some promotional emails and newsletters. I recommend prioritizing the work-related emails first and then dealing with the promotional content. Would you like me to provide more detailed information about any specific email?",
        "calendar": "I have checked your Google Calendar and found your schedule for today. You have several appointments and meetings scheduled throughout the day. Your first meeting is at 9 AM with the development team, followed by a lunch meeting at 12 PM with the client. In the afternoon, you have a project review session at 3 PM and a team standup at 5 PM. Please make sure to prepare for these meetings and allocate appropriate time for travel between locations if needed.",
        "docs": "I have successfully accessed your Google Docs account and retrieved the list of your recent documents. You have several documents that have been recently modified, including project proposals, meeting notes, and draft reports. The most recently updated document appears to be your quarterly review document that was last modified yesterday. I can help you with reading, editing, or creating new documents as needed. Please let me know what specific document operations you would like me to perform."
    }
    
    # Test current optimized responses
    test_messages = {
        "gmail": "Check my recent emails",
        "calendar": "What's my schedule today?", 
        "docs": "List my recent documents"
    }
    
    print("COMPARISON RESULTS:")
    print("-" * 60)
    
    for app, message in test_messages.items():
        print(f"\n{app.upper()} TEST:")
        print(f"Message: '{message}'")
        
        # Show "before" (verbose)
        before = before_responses[app]
        print(f"\nBEFORE (verbose): {len(before.split())} words")
        print(f"'{before}'")
        
        # Show "after" (optimized)
        try:
            after = await process_user_query_async(
                message=message,
                user_id=user_id,
                agent_mode=True,
                conversation_id="comparison_test"
            )
            print(f"\nAFTER (optimized): {len(after.split())} words")
            print(f"'{after}'")
            
            # Calculate improvement
            word_reduction = len(before.split()) - len(after.split())
            reduction_percent = (word_reduction / len(before.split())) * 100
            print(f"\nIMPROVEMENT: -{word_reduction} words ({reduction_percent:.1f}% reduction)")
            
        except Exception as e:
            print(f"\nAFTER (error): {e}")
        
        print("-" * 60)

if __name__ == "__main__":
    print("Starting Phase 1 Optimization Test with Real User...")
    
    async def main():
        # Test optimized responses
        await test_real_user_with_all_apps()
        
        # Show before/after comparison
        await test_before_after_comparison()
        
        print("\n🎉 Phase 1 optimization testing complete!")
        print("Check the results above to see how response brevity has improved.")
    
    asyncio.run(main())