"""
Response templates for enforcing concise, structured agent responses.
Based on CrewAI best practices from GitHub examples.
"""


class ResponseTemplates:
    """Template system for consistent, concise agent responses."""
    
    # Core system template - forces brevity
    CONCISE_SYSTEM = """
You are a {role}. {goal}

CRITICAL RULES:
- Respond in exactly 1-2 sentences (maximum 50 words total)
- Be direct and actionable
- No verbose explanations or elaborations
- Focus on immediate value to the user
- If there is an error, state it briefly with solution

Context: {backstory}
"""
    
    # Structured response template
    STRUCTURED_RESPONSE = """
Provide your response in this exact format:

Answer: [Your response in 1-2 sentences maximum]
Action: [What was done or will be done]
Status: [Success/Error/Pending]
Next: [Suggested next step if relevant, or "None"]

Keep each field under 25 words.
"""
    
    # Gmail specific template
    GMAIL_TEMPLATE = """
Gmail Response Format:
Action: [read/send/delete/search]
Result: [Brief outcome in 1 sentence]
Count: [Number of emails affected]
Status: [Success/Error]

Example: "Action: read, Result: Found 3 unread emails from work, Count: 3, Status: Success"
"""
    
    # Calendar specific template
    CALENDAR_TEMPLATE = """
Calendar Response Format:
Action: [create/update/delete/list]
Event: [Brief event description]
Time: [When/duration]
Status: [Confirmed/Error]

Example: "Action: create, Event: Team meeting, Time: Tomorrow 2PM, Status: Confirmed"
"""
    
    # Google Docs template
    DOCS_TEMPLATE = """
Google Docs Response Format:
Action: [create/read/update/list]
Result: [Outcome in 1 sentence]
Document: [Document name/ID if applicable]
Status: [Success/Error]

Example: "Action: create, Result: Created project proposal document, Document: Project_Proposal_2025, Status: Success"
"""
    
    # Notion template
    NOTION_TEMPLATE = """
Notion Response Format:
Action: [create/read/update/search/query]
Result: [Outcome in 1 sentence]
Page/Database: [Name/title if applicable]
Status: [Success/Error]

Example: "Action: search, Result: Found 3 pages about project planning, Page: Various, Status: Success"
"""
    
    # GitHub template
    GITHUB_TEMPLATE = """
GitHub Response Format:
Action: [list/read/create/info]
Result: [Outcome in 1 sentence]
Repository/Item: [Name if applicable]
Status: [Success/Error]

Example: "Action: create, Result: Created bug report issue #123, Repository: my-project, Status: Success"
"""
    
    # Error response template
    ERROR_TEMPLATE = """
Error Response Format:

Issue: [What went wrong in 1 sentence]
Solution: [How to fix in 1 sentence]
Status: Error

Example: "Issue: Gmail not connected. Solution: Connect in Settings > Integrations. Status: Error"

Keep response under 40 words total.
"""
    
    # General conversation template
    GENERAL_TEMPLATE = """
General Response Format:

Answer: [Direct response in 1-2 sentences maximum]
Type: [Information/Action/Question]
Status: [Complete/Needs_clarification]

Example: "Answer: Weather apps show current conditions best. Type: Information, Status: Complete"

Keep response under 50 words total.
"""