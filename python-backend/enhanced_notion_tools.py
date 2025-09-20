"""
Enhanced Notion Tools for CrewAI Integration

This module provides advanced Notion tools that build upon the basic functionality
to provide enhanced features for database management, page operations, content analysis,
and workspace intelligence.

Enhanced tools follow CrewAI Phase 2 structured response patterns and provide
comprehensive Notion workspace management capabilities for professional workflows.
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from langchain.tools import BaseTool
import httpx
import json
from datetime import datetime, timezone, timedelta
import re
from dataclasses import dataclass

# Import existing OAuth functionality
from langchain_tools import get_notion_access_token, run_async_in_thread


# =============================================================================
# ENHANCED NOTION TOOLS - DATA MODELS
# =============================================================================


@dataclass
class PageInfo:
    """Notion page information structure"""
    id: str
    title: str
    url: str
    created_time: str
    last_edited_time: str
    created_by: str
    parent_type: str
    parent_id: str
    archived: bool
    properties: Dict


@dataclass
class DatabaseInfo:
    """Notion database information structure"""
    id: str
    title: str
    url: str
    created_time: str
    last_edited_time: str
    properties: Dict
    parent_type: str
    parent_id: str
    archived: bool


@dataclass
class WorkspaceMetrics:
    """Notion workspace analytics metrics"""
    total_pages: int
    total_databases: int
    pages_created_this_week: int
    pages_edited_this_week: int
    most_active_database: str
    content_types: Dict[str, int]
    collaboration_score: float
    organization_score: float


class NotionFilters(BaseModel):
    """Advanced Notion filtering options"""
    object_type: Optional[str] = Field(None, description="Filter by type: 'page', 'database', or 'both'")
    title_contains: Optional[str] = Field(None, description="Filter by title containing text")
    created_after: Optional[str] = Field(None, description="Filter by creation date (YYYY-MM-DD or relative like '7d')")
    edited_after: Optional[str] = Field(None, description="Filter by last edit date (YYYY-MM-DD or relative like '7d')")
    parent_type: Optional[str] = Field(None, description="Filter by parent type: 'page', 'database', 'workspace'")
    archived: Optional[bool] = Field(None, description="Filter by archived status")
    has_properties: Optional[List[str]] = Field(None, description="Filter by presence of specific properties")
    max_results: int = Field(50, description="Maximum results to return")


class DatabaseQuery(BaseModel):
    """Database query configuration"""
    database_id: str = Field(description="Database ID to query")
    filter_conditions: Optional[Dict] = Field(None, description="Notion filter conditions")
    sort_conditions: Optional[List[Dict]] = Field(None, description="Notion sort conditions")
    page_size: int = Field(100, description="Number of results per page")
    include_properties: Optional[List[str]] = Field(None, description="Specific properties to include")


class PageTemplate(BaseModel):
    """Page template configuration"""
    template_type: str = Field(description="Template type: 'project', 'meeting', 'task', 'note', 'custom'")
    title: str = Field(description="Page title")
    properties: Optional[Dict] = Field(None, description="Page properties to set")
    content_blocks: Optional[List[Dict]] = Field(None, description="Initial content blocks")
    database_id: Optional[str] = Field(None, description="Parent database ID")


# =============================================================================
# ENHANCED NOTION TOOL INPUTS
# =============================================================================

class DatabaseManagerInput(BaseModel):
    """Input for enhanced database manager tool"""
    user_id: str = Field(description="User ID for authentication")
    action: str = Field(description="Action: 'query', 'create_entry', 'update_entry', 'analyze_database', 'get_schema'")
    database_query: Optional[DatabaseQuery] = Field(None, description="Database query configuration")
    entry_data: Optional[Dict] = Field(None, description="Entry data for create/update operations")
    entry_id: Optional[str] = Field(None, description="Entry ID for update operations")
    analysis_type: Optional[str] = Field("basic", description="Analysis type: 'basic', 'comprehensive'")


class PageManagerInput(BaseModel):
    """Input for enhanced page manager tool"""
    user_id: str = Field(description="User ID for authentication")
    action: str = Field(description="Action: 'search', 'read', 'create', 'update', 'archive', 'move'")
    page_id: Optional[str] = Field(None, description="Page ID for read/update/archive/move operations")
    filters: Optional[NotionFilters] = Field(None, description="Filters for search action")
    page_template: Optional[PageTemplate] = Field(None, description="Template for create action")
    content_blocks: Optional[List[Dict]] = Field(None, description="Content blocks for update action")
    new_parent_id: Optional[str] = Field(None, description="New parent ID for move action")


class ContentAnalyzerInput(BaseModel):
    """Input for enhanced content analyzer tool"""
    user_id: str = Field(description="User ID for authentication")
    action: str = Field(description="Action: 'analyze_page', 'analyze_database', 'extract_insights', 'content_audit'")
    target_id: str = Field(description="Page or database ID to analyze")
    analysis_scope: Optional[str] = Field("comprehensive", description="Analysis scope: 'basic', 'comprehensive', 'deep'")
    include_suggestions: bool = Field(True, description="Include improvement suggestions")


class WorkspaceIntelligenceInput(BaseModel):
    """Input for enhanced workspace intelligence tool"""
    user_id: str = Field(description="User ID for authentication")
    action: str = Field(description="Action: 'workspace_overview', 'activity_analysis', 'optimization_suggestions', 'content_mapping'")
    timeframe: Optional[str] = Field("week", description="Timeframe: 'day', 'week', 'month', 'quarter'")
    include_metrics: bool = Field(True, description="Include detailed metrics")
    focus_area: Optional[str] = Field(None, description="Focus area: 'productivity', 'collaboration', 'organization'")


# =============================================================================
# ENHANCED NOTION DATABASE MANAGER TOOL
# =============================================================================

class DatabaseManagerTool(BaseTool):
    """Enhanced Notion database manager tool with advanced querying and analytics"""
    
    name: str = "enhanced_notion_database_manager"
    description: str = """
    Advanced Notion database manager with enhanced querying, entry management, and database analytics.
    
    Actions:
    - 'query': Advanced database querying with filters and sorting
    - 'create_entry': Create new database entries with rich properties
    - 'update_entry': Update existing database entries
    - 'analyze_database': Analyze database structure and content patterns
    - 'get_schema': Get detailed database schema and property information
    
    Provides comprehensive database management and intelligence capabilities.
    """
    args_schema: type = DatabaseManagerInput
    
    async def _arun(self, **kwargs) -> str:
        """Async implementation"""
        return await self._execute_database_action(**kwargs)
    
    def _run(self, **kwargs) -> str:
        """Sync implementation"""
        return run_async_in_thread(self._execute_database_action(**kwargs))
    
    async def _execute_database_action(
        self,
        user_id: str,
        action: str,
        database_query: Optional[DatabaseQuery] = None,
        entry_data: Optional[Dict] = None,
        entry_id: Optional[str] = None,
        analysis_type: str = "basic"
    ) -> str:
        """Execute the database action"""
        access_token = await get_notion_access_token(user_id)
        if not access_token:
            return json.dumps({
                "status": "error",
                "message": "No valid Notion access token found. Please connect Notion.",
                "error_code": "AUTH_REQUIRED"
            })
        
        try:
            if action == "query":
                if not database_query:
                    return json.dumps({
                        "status": "error",
                        "message": "database_query required for query action",
                        "error_code": "MISSING_QUERY"
                    })
                return await self._query_database(access_token, database_query)
            elif action == "create_entry":
                if not database_query or not entry_data:
                    return json.dumps({
                        "status": "error",
                        "message": "database_query and entry_data required for create_entry action",
                        "error_code": "MISSING_DATA"
                    })
                return await self._create_database_entry(access_token, database_query.database_id, entry_data)
            elif action == "update_entry":
                if not entry_id or not entry_data:
                    return json.dumps({
                        "status": "error",
                        "message": "entry_id and entry_data required for update_entry action",
                        "error_code": "MISSING_DATA"
                    })
                return await self._update_database_entry(access_token, entry_id, entry_data)
            elif action == "analyze_database":
                if not database_query:
                    return json.dumps({
                        "status": "error",
                        "message": "database_query required for analyze_database action",
                        "error_code": "MISSING_QUERY"
                    })
                return await self._analyze_database(access_token, database_query.database_id, analysis_type)
            elif action == "get_schema":
                if not database_query:
                    return json.dumps({
                        "status": "error",
                        "message": "database_query required for get_schema action",
                        "error_code": "MISSING_QUERY"
                    })
                return await self._get_database_schema(access_token, database_query.database_id)
            else:
                return json.dumps({
                    "status": "error",
                    "message": f"Unknown action: {action}. Available actions: query, create_entry, update_entry, analyze_database, get_schema",
                    "error_code": "INVALID_ACTION"
                })
        
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Error executing database action: {str(e)}",
                "error_code": "EXECUTION_ERROR"
            })
    
    async def _query_database(self, access_token: str, query: DatabaseQuery) -> str:
        """Query database with advanced filtering and sorting"""
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
        
        query_data = {
            "page_size": min(query.page_size, 100)
        }
        
        if query.filter_conditions:
            query_data["filter"] = query.filter_conditions
        
        if query.sort_conditions:
            query_data["sorts"] = query.sort_conditions
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"https://api.notion.com/v1/databases/{query.database_id}/query",
                    headers=headers,
                    json=query_data
                )
                
                if response.status_code != 200:
                    return json.dumps({
                        "status": "error",
                        "message": f"Database query failed with status {response.status_code}",
                        "error_code": "QUERY_ERROR"
                    })
                
                data = response.json()
                results = data.get('results', [])
                
                # Process results
                entries = []
                for result in results:
                    entry = {
                        "id": result.get('id', ''),
                        "url": result.get('url', ''),
                        "created_time": result.get('created_time', ''),
                        "last_edited_time": result.get('last_edited_time', ''),
                        "properties": self._extract_properties(result.get('properties', {})),
                        "archived": result.get('archived', False)
                    }
                    entries.append(entry)
                
                return json.dumps({
                    "status": "success",
                    "message": f"Found {len(entries)} database entries",
                    "database_id": query.database_id,
                    "entries": entries,
                    "total_results": len(entries),
                    "has_more": data.get('has_more', False),
                    "query_executed": datetime.now(timezone.utc).isoformat()
                })
        
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Database query error: {str(e)}",
                "error_code": "QUERY_EXCEPTION"
            })
    
    async def _create_database_entry(self, access_token: str, database_id: str, entry_data: Dict) -> str:
        """Create new database entry"""
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
        
        page_data = {
            "parent": {"database_id": database_id},
            "properties": entry_data.get("properties", {}),
            "children": entry_data.get("content_blocks", [])
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.notion.com/v1/pages",
                    headers=headers,
                    json=page_data
                )
                
                if response.status_code != 200:
                    return json.dumps({
                        "status": "error",
                        "message": f"Entry creation failed with status {response.status_code}",
                        "error_code": "CREATE_ERROR"
                    })
                
                new_entry = response.json()
                
                return json.dumps({
                    "status": "success",
                    "message": "Database entry created successfully",
                    "entry": {
                        "id": new_entry.get('id', ''),
                        "url": new_entry.get('url', ''),
                        "created_time": new_entry.get('created_time', ''),
                        "properties": self._extract_properties(new_entry.get('properties', {}))
                    },
                    "database_id": database_id,
                    "created_at": datetime.now(timezone.utc).isoformat()
                })
        
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Entry creation error: {str(e)}",
                "error_code": "CREATE_EXCEPTION"
            })
    
    async def _update_database_entry(self, access_token: str, entry_id: str, entry_data: Dict) -> str:
        """Update existing database entry"""
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
        
        update_data = {}
        if "properties" in entry_data:
            update_data["properties"] = entry_data["properties"]
        if "archived" in entry_data:
            update_data["archived"] = entry_data["archived"]
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.patch(
                    f"https://api.notion.com/v1/pages/{entry_id}",
                    headers=headers,
                    json=update_data
                )
                
                if response.status_code != 200:
                    return json.dumps({
                        "status": "error",
                        "message": f"Entry update failed with status {response.status_code}",
                        "error_code": "UPDATE_ERROR"
                    })
                
                updated_entry = response.json()
                
                return json.dumps({
                    "status": "success",
                    "message": "Database entry updated successfully",
                    "entry": {
                        "id": updated_entry.get('id', ''),
                        "last_edited_time": updated_entry.get('last_edited_time', ''),
                        "properties": self._extract_properties(updated_entry.get('properties', {}))
                    },
                    "updated_at": datetime.now(timezone.utc).isoformat()
                })
        
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Entry update error: {str(e)}",
                "error_code": "UPDATE_EXCEPTION"
            })
    
    async def _analyze_database(self, access_token: str, database_id: str, analysis_type: str) -> str:
        """Analyze database structure and content patterns"""
        # First get database schema
        schema_result = await self._get_database_schema(access_token, database_id)
        schema_data = json.loads(schema_result)
        
        if schema_data.get("status") != "success":
            return schema_result
        
        # Get database entries for analysis
        query = DatabaseQuery(database_id=database_id, page_size=100)
        entries_result = await self._query_database(access_token, query)
        entries_data = json.loads(entries_result)
        
        if entries_data.get("status") != "success":
            return entries_result
        
        entries = entries_data.get("entries", [])
        database_info = schema_data.get("database", {})
        
        # Perform analysis
        analysis = {
            "database_info": {
                "id": database_id,
                "title": database_info.get("title", ""),
                "total_entries": len(entries),
                "properties_count": len(database_info.get("properties", {})),
                "created_time": database_info.get("created_time", "")
            },
            "content_analysis": self._analyze_database_content(entries, database_info),
            "usage_patterns": self._analyze_usage_patterns(entries),
            "data_quality": self._analyze_data_quality(entries, database_info)
        }
        
        if analysis_type == "comprehensive":
            analysis["insights"] = self._generate_database_insights(entries, database_info)
            analysis["optimization_suggestions"] = self._generate_optimization_suggestions(entries, database_info)
        
        return json.dumps({
            "status": "success",
            "message": f"Database analysis completed for {len(entries)} entries",
            "database_id": database_id,
            "analysis_type": analysis_type,
            "analysis": analysis,
            "analyzed_at": datetime.now(timezone.utc).isoformat()
        })
    
    async def _get_database_schema(self, access_token: str, database_id: str) -> str:
        """Get detailed database schema"""
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Notion-Version": "2022-06-28"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://api.notion.com/v1/databases/{database_id}",
                    headers=headers
                )
                
                if response.status_code != 200:
                    return json.dumps({
                        "status": "error",
                        "message": f"Failed to get database schema. Status: {response.status_code}",
                        "error_code": "SCHEMA_ERROR"
                    })
                
                database_data = response.json()
                
                # Extract schema information
                schema = {
                    "id": database_data.get('id', ''),
                    "title": self._extract_database_title(database_data),
                    "description": self._extract_database_description(database_data),
                    "url": database_data.get('url', ''),
                    "created_time": database_data.get('created_time', ''),
                    "last_edited_time": database_data.get('last_edited_time', ''),
                    "properties": self._extract_database_properties_schema(database_data.get('properties', {})),
                    "archived": database_data.get('archived', False),
                    "is_inline": database_data.get('is_inline', False)
                }
                
                return json.dumps({
                    "status": "success",
                    "message": f"Database schema retrieved for '{schema['title']}'",
                    "database": schema,
                    "properties_count": len(schema["properties"]),
                    "retrieved_at": datetime.now(timezone.utc).isoformat()
                })
        
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Schema retrieval error: {str(e)}",
                "error_code": "SCHEMA_EXCEPTION"
            })
    
    def _extract_properties(self, properties: Dict) -> Dict:
        """Extract and format Notion properties"""
        formatted_properties = {}
        
        for prop_name, prop_data in properties.items():
            prop_type = prop_data.get('type', 'unknown')
            
            if prop_type == 'title':
                title_array = prop_data.get('title', [])
                formatted_properties[prop_name] = title_array[0].get('plain_text', '') if title_array else ''
            elif prop_type == 'rich_text':
                text_array = prop_data.get('rich_text', [])
                formatted_properties[prop_name] = ' '.join([t.get('plain_text', '') for t in text_array])
            elif prop_type == 'number':
                formatted_properties[prop_name] = prop_data.get('number')
            elif prop_type == 'select':
                select_data = prop_data.get('select')
                formatted_properties[prop_name] = select_data.get('name', '') if select_data else ''
            elif prop_type == 'multi_select':
                multi_select = prop_data.get('multi_select', [])
                formatted_properties[prop_name] = [item.get('name', '') for item in multi_select]
            elif prop_type == 'date':
                date_data = prop_data.get('date')
                if date_data:
                    formatted_properties[prop_name] = {
                        'start': date_data.get('start', ''),
                        'end': date_data.get('end', '')
                    }
                else:
                    formatted_properties[prop_name] = None
            elif prop_type == 'checkbox':
                formatted_properties[prop_name] = prop_data.get('checkbox', False)
            elif prop_type == 'url':
                formatted_properties[prop_name] = prop_data.get('url', '')
            elif prop_type == 'email':
                formatted_properties[prop_name] = prop_data.get('email', '')
            elif prop_type == 'phone_number':
                formatted_properties[prop_name] = prop_data.get('phone_number', '')
            else:
                # For other types, store the raw data
                formatted_properties[prop_name] = prop_data
        
        return formatted_properties
    
    def _extract_database_title(self, database_data: Dict) -> str:
        """Extract database title"""
        title_array = database_data.get('title', [])
        return title_array[0].get('plain_text', 'Untitled Database') if title_array else 'Untitled Database'
    
    def _extract_database_description(self, database_data: Dict) -> str:
        """Extract database description"""
        description_array = database_data.get('description', [])
        return ' '.join([d.get('plain_text', '') for d in description_array])
    
    def _extract_database_properties_schema(self, properties: Dict) -> Dict:
        """Extract database properties schema"""
        schema = {}
        
        for prop_name, prop_data in properties.items():
            prop_type = prop_data.get('type', 'unknown')
            schema[prop_name] = {
                'type': prop_type,
                'id': prop_data.get('id', ''),
                'name': prop_name
            }
            
            # Add type-specific configuration
            if prop_type == 'select':
                options = prop_data.get('select', {}).get('options', [])
                schema[prop_name]['options'] = [opt.get('name', '') for opt in options]
            elif prop_type == 'multi_select':
                options = prop_data.get('multi_select', {}).get('options', [])
                schema[prop_name]['options'] = [opt.get('name', '') for opt in options]
            elif prop_type == 'number':
                number_config = prop_data.get('number', {})
                schema[prop_name]['format'] = number_config.get('format', 'number')
            elif prop_type == 'formula':
                formula_config = prop_data.get('formula', {})
                schema[prop_name]['expression'] = formula_config.get('expression', '')
        
        return schema
    
    def _analyze_database_content(self, entries: List[Dict], database_info: Dict) -> Dict:
        """Analyze database content patterns"""
        if not entries:
            return {"message": "No entries to analyze"}
        
        analysis = {
            "entry_count": len(entries),
            "property_usage": {},
            "content_types": {},
            "completion_rate": {}
        }
        
        properties_schema = database_info.get("properties", {})
        
        for prop_name, prop_schema in properties_schema.items():
            prop_type = prop_schema.get('type', 'unknown')
            filled_count = 0
            
            for entry in entries:
                prop_value = entry.get('properties', {}).get(prop_name)
                if prop_value is not None and prop_value != '' and prop_value != []:
                    filled_count += 1
            
            analysis["property_usage"][prop_name] = {
                "type": prop_type,
                "filled_entries": filled_count,
                "completion_rate": filled_count / len(entries) if entries else 0
            }
        
        return analysis
    
    def _analyze_usage_patterns(self, entries: List[Dict]) -> Dict:
        """Analyze usage patterns from entries"""
        if not entries:
            return {"message": "No entries to analyze"}
        
        # Analyze creation and edit patterns
        creation_dates = []
        edit_dates = []
        
        for entry in entries:
            created = entry.get('created_time', '')
            edited = entry.get('last_edited_time', '')
            
            if created:
                creation_dates.append(created)
            if edited:
                edit_dates.append(edited)
        
        patterns = {
            "total_entries": len(entries),
            "creation_pattern": self._analyze_temporal_pattern(creation_dates),
            "edit_pattern": self._analyze_temporal_pattern(edit_dates),
            "activity_level": "high" if len(entries) > 50 else "medium" if len(entries) > 10 else "low"
        }
        
        return patterns
    
    def _analyze_temporal_pattern(self, dates: List[str]) -> Dict:
        """Analyze temporal patterns in dates"""
        if not dates:
            return {"message": "No dates to analyze"}
        
        # Convert dates and analyze patterns
        try:
            date_objects = [datetime.fromisoformat(d.replace('Z', '+00:00')) for d in dates if d]
            
            if not date_objects:
                return {"message": "No valid dates found"}
            
            # Recent activity (last 7 days)
            now = datetime.now(timezone.utc)
            week_ago = now - timedelta(days=7)
            recent_count = len([d for d in date_objects if d > week_ago])
            
            return {
                "total_items": len(date_objects),
                "recent_activity": recent_count,
                "oldest_date": min(date_objects).isoformat(),
                "newest_date": max(date_objects).isoformat(),
                "activity_trend": "increasing" if recent_count > len(date_objects) * 0.3 else "stable"
            }
        except Exception as e:
            return {"error": f"Date analysis error: {str(e)}"}
    
    def _analyze_data_quality(self, entries: List[Dict], database_info: Dict) -> Dict:
        """Analyze data quality metrics"""
        if not entries:
            return {"message": "No entries to analyze"}
        
        quality_metrics = {
            "completeness_score": 0.0,
            "consistency_issues": [],
            "missing_data_patterns": {},
            "recommendations": []
        }
        
        properties_schema = database_info.get("properties", {})
        total_properties = len(properties_schema)
        
        if total_properties == 0:
            return quality_metrics
        
        # Calculate completeness
        total_filled = 0
        total_possible = len(entries) * total_properties
        
        for entry in entries:
            properties = entry.get('properties', {})
            for prop_name in properties_schema.keys():
                prop_value = properties.get(prop_name)
                if prop_value is not None and prop_value != '' and prop_value != []:
                    total_filled += 1
        
        quality_metrics["completeness_score"] = total_filled / total_possible if total_possible > 0 else 0
        
        # Generate recommendations
        if quality_metrics["completeness_score"] < 0.7:
            quality_metrics["recommendations"].append("Consider improving data completeness - many properties are unfilled")
        if len(entries) < 5:
            quality_metrics["recommendations"].append("Database has few entries - consider adding more data for better insights")
        
        return quality_metrics
    
    def _generate_database_insights(self, entries: List[Dict], database_info: Dict) -> List[str]:
        """Generate insights about database usage"""
        insights = []
        
        if len(entries) == 0:
            insights.append("Database is empty - consider adding initial entries")
            return insights
        
        # Activity insights
        if len(entries) > 100:
            insights.append("High-activity database with extensive content")
        elif len(entries) > 20:
            insights.append("Moderately active database with good content volume")
        else:
            insights.append("Growing database - consider strategies to increase content")
        
        # Property insights
        properties_count = len(database_info.get("properties", {}))
        if properties_count > 15:
            insights.append("Complex database structure - consider organizing properties into sections")
        elif properties_count < 3:
            insights.append("Simple database structure - consider adding more properties for richer data")
        
        return insights
    
    def _generate_optimization_suggestions(self, entries: List[Dict], database_info: Dict) -> List[str]:
        """Generate optimization suggestions"""
        suggestions = []
        
        # Performance suggestions
        if len(entries) > 1000:
            suggestions.append("Large database - consider archiving old entries or using filtered views")
        
        # Structure suggestions
        properties_count = len(database_info.get("properties", {}))
        if properties_count > 20:
            suggestions.append("Many properties detected - consider using templates to improve data entry efficiency")
        
        # Usage suggestions
        if len(entries) < 10:
            suggestions.append("Few entries present - consider batch importing data or creating entry templates")
        
        return suggestions


# =============================================================================
# ENHANCED NOTION PAGE MANAGER TOOL
# =============================================================================

class PageManagerTool(BaseTool):
    """Enhanced Notion page manager tool with advanced page operations and templates"""
    
    name: str = "enhanced_notion_page_manager"
    description: str = """
    Advanced Notion page manager with enhanced search, creation, updating, and organization capabilities.
    
    Actions:
    - 'search': Advanced page search with comprehensive filtering
    - 'read': Read page content with structure extraction
    - 'create': Create pages with professional templates
    - 'update': Update page content and properties
    - 'archive': Archive or restore pages
    - 'move': Move pages to different locations
    
    Supports templates, bulk operations, and intelligent page organization.
    """
    args_schema: type = PageManagerInput
    
    async def _arun(self, **kwargs) -> str:
        """Async implementation"""
        return await self._execute_page_action(**kwargs)
    
    def _run(self, **kwargs) -> str:
        """Sync implementation"""
        return run_async_in_thread(self._execute_page_action(**kwargs))
    
    async def _execute_page_action(
        self,
        user_id: str,
        action: str,
        page_id: Optional[str] = None,
        filters: Optional[NotionFilters] = None,
        page_template: Optional[PageTemplate] = None,
        content_blocks: Optional[List[Dict]] = None,
        new_parent_id: Optional[str] = None
    ) -> str:
        """Execute the page action"""
        access_token = await get_notion_access_token(user_id)
        if not access_token:
            return json.dumps({
                "status": "error",
                "message": "No valid Notion access token found. Please connect Notion.",
                "error_code": "AUTH_REQUIRED"
            })
        
        try:
            if action == "search":
                return await self._search_pages(access_token, filters or NotionFilters())
            elif action == "read":
                if not page_id:
                    return json.dumps({
                        "status": "error",
                        "message": "page_id required for read action",
                        "error_code": "MISSING_PAGE_ID"
                    })
                return await self._read_page(access_token, page_id)
            elif action == "create":
                if not page_template:
                    return json.dumps({
                        "status": "error",
                        "message": "page_template required for create action",
                        "error_code": "MISSING_TEMPLATE"
                    })
                return await self._create_page(access_token, page_template)
            elif action == "update":
                if not page_id:
                    return json.dumps({
                        "status": "error",
                        "message": "page_id required for update action",
                        "error_code": "MISSING_PAGE_ID"
                    })
                return await self._update_page(access_token, page_id, content_blocks)
            elif action == "archive":
                if not page_id:
                    return json.dumps({
                        "status": "error",
                        "message": "page_id required for archive action",
                        "error_code": "MISSING_PAGE_ID"
                    })
                return await self._archive_page(access_token, page_id)
            elif action == "move":
                if not page_id or not new_parent_id:
                    return json.dumps({
                        "status": "error",
                        "message": "page_id and new_parent_id required for move action",
                        "error_code": "MISSING_DATA"
                    })
                return await self._move_page(access_token, page_id, new_parent_id)
            else:
                return json.dumps({
                    "status": "error",
                    "message": f"Unknown action: {action}. Available actions: search, read, create, update, archive, move",
                    "error_code": "INVALID_ACTION"
                })
        
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Error executing page action: {str(e)}",
                "error_code": "EXECUTION_ERROR"
            })
    
    async def _search_pages(self, access_token: str, filters: NotionFilters) -> str:
        """Search pages with advanced filtering"""
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
        
        search_data = {
            "page_size": min(filters.max_results, 100)
        }
        
        # Add search query if title filter is provided
        if filters.title_contains:
            search_data["query"] = filters.title_contains
        
        # Add object type filter
        if filters.object_type and filters.object_type != "both":
            search_data["filter"] = {"property": "object", "value": filters.object_type}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.notion.com/v1/search",
                    headers=headers,
                    json=search_data
                )
                
                if response.status_code != 200:
                    return json.dumps({
                        "status": "error",
                        "message": f"Search failed with status {response.status_code}",
                        "error_code": "SEARCH_ERROR"
                    })
                
                data = response.json()
                results = data.get('results', [])
                
                # Filter results based on additional criteria
                filtered_results = self._apply_additional_filters(results, filters)
                
                pages = []
                for result in filtered_results:
                    if result.get('object') == 'page':
                        page_info = {
                            "id": result.get('id', ''),
                            "title": self._extract_page_title(result),
                            "url": result.get('url', ''),
                            "created_time": result.get('created_time', ''),
                            "last_edited_time": result.get('last_edited_time', ''),
                            "archived": result.get('archived', False),
                            "parent_type": self._get_parent_type(result.get('parent', {})),
                            "parent_id": self._get_parent_id(result.get('parent', {}))
                        }
                        pages.append(page_info)
                
                return json.dumps({
                    "status": "success",
                    "message": f"Found {len(pages)} pages matching criteria",
                    "pages": pages,
                    "total_found": len(pages),
                    "filters_applied": filters.dict(exclude_none=True),
                    "searched_at": datetime.now(timezone.utc).isoformat()
                })
        
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Search error: {str(e)}",
                "error_code": "SEARCH_EXCEPTION"
            })
    
    async def _read_page(self, access_token: str, page_id: str) -> str:
        """Read page with comprehensive content extraction"""
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Notion-Version": "2022-06-28"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                # Get page properties
                page_response = await client.get(
                    f"https://api.notion.com/v1/pages/{page_id}",
                    headers=headers
                )
                
                if page_response.status_code != 200:
                    return json.dumps({
                        "status": "error",
                        "message": f"Failed to read page. Status: {page_response.status_code}",
                        "error_code": "READ_ERROR"
                    })
                
                page_data = page_response.json()
                
                # Get page content blocks
                blocks_response = await client.get(
                    f"https://api.notion.com/v1/blocks/{page_id}/children",
                    headers=headers,
                    params={"page_size": 100}
                )
                
                blocks_data = {}
                if blocks_response.status_code == 200:
                    blocks_data = blocks_response.json()
                
                # Extract content
                content_analysis = self._analyze_page_content(blocks_data.get('results', []))
                
                page_info = {
                    "id": page_data.get('id', ''),
                    "title": self._extract_page_title(page_data),
                    "url": page_data.get('url', ''),
                    "created_time": page_data.get('created_time', ''),
                    "last_edited_time": page_data.get('last_edited_time', ''),
                    "archived": page_data.get('archived', False),
                    "properties": self._extract_properties(page_data.get('properties', {})),
                    "parent_info": {
                        "type": self._get_parent_type(page_data.get('parent', {})),
                        "id": self._get_parent_id(page_data.get('parent', {}))
                    },
                    "content_analysis": content_analysis
                }
                
                return json.dumps({
                    "status": "success",
                    "message": f"Successfully read page '{page_info['title']}'",
                    "page": page_info,
                    "content_blocks": len(blocks_data.get('results', [])),
                    "read_at": datetime.now(timezone.utc).isoformat()
                })
        
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Page read error: {str(e)}",
                "error_code": "READ_EXCEPTION"
            })
    
    async def _create_page(self, access_token: str, template: PageTemplate) -> str:
        """Create page with template"""
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
        
        # Build page data
        page_data = {
            "properties": {
                "title": {
                    "title": [{"text": {"content": template.title}}]
                }
            }
        }
        
        # Add additional properties if provided
        if template.properties:
            page_data["properties"].update(template.properties)
        
        # Set parent
        if template.database_id:
            page_data["parent"] = {"database_id": template.database_id}
        else:
            # Default to workspace
            page_data["parent"] = {"type": "workspace", "workspace": True}
        
        # Add template content
        if template.template_type != "custom":
            template_blocks = self._get_template_blocks(template.template_type, template.title)
            page_data["children"] = template_blocks
        elif template.content_blocks:
            page_data["children"] = template.content_blocks
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.notion.com/v1/pages",
                    headers=headers,
                    json=page_data
                )
                
                if response.status_code != 200:
                    return json.dumps({
                        "status": "error",
                        "message": f"Page creation failed with status {response.status_code}",
                        "error_code": "CREATE_ERROR"
                    })
                
                new_page = response.json()
                
                return json.dumps({
                    "status": "success",
                    "message": f"Successfully created page '{template.title}'",
                    "page": {
                        "id": new_page.get('id', ''),
                        "title": template.title,
                        "url": new_page.get('url', ''),
                        "created_time": new_page.get('created_time', ''),
                        "template_applied": template.template_type
                    },
                    "created_at": datetime.now(timezone.utc).isoformat()
                })
        
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Page creation error: {str(e)}",
                "error_code": "CREATE_EXCEPTION"
            })
    
    def _apply_additional_filters(self, results: List[Dict], filters: NotionFilters) -> List[Dict]:
        """Apply additional client-side filters"""
        filtered = results
        
        # Filter by creation date
        if filters.created_after:
            cutoff_date = self._parse_date_filter(filters.created_after)
            if cutoff_date:
                filtered = [r for r in filtered 
                           if self._is_after_date(r.get('created_time', ''), cutoff_date)]
        
        # Filter by edit date
        if filters.edited_after:
            cutoff_date = self._parse_date_filter(filters.edited_after)
            if cutoff_date:
                filtered = [r for r in filtered 
                           if self._is_after_date(r.get('last_edited_time', ''), cutoff_date)]
        
        # Filter by archived status
        if filters.archived is not None:
            filtered = [r for r in filtered if r.get('archived', False) == filters.archived]
        
        return filtered
    
    def _parse_date_filter(self, date_str: str) -> Optional[datetime]:
        """Parse date filter (supports relative dates like '7d')"""
        try:
            if date_str.endswith('d'):
                days = int(date_str[:-1])
                return datetime.now(timezone.utc) - timedelta(days=days)
            else:
                return datetime.fromisoformat(date_str).replace(tzinfo=timezone.utc)
        except:
            return None
    
    def _is_after_date(self, date_str: str, cutoff_date: datetime) -> bool:
        """Check if date is after cutoff"""
        try:
            date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return date_obj > cutoff_date
        except:
            return False
    
    def _extract_page_title(self, page_data: Dict) -> str:
        """Extract page title from page data"""
        properties = page_data.get('properties', {})
        for prop_name, prop_data in properties.items():
            if prop_data.get('type') == 'title':
                title_array = prop_data.get('title', [])
                return title_array[0].get('plain_text', 'Untitled') if title_array else 'Untitled'
        return 'Untitled Page'
    
    def _get_parent_type(self, parent: Dict) -> str:
        """Get parent type from parent object"""
        return parent.get('type', 'unknown')
    
    def _get_parent_id(self, parent: Dict) -> str:
        """Get parent ID from parent object"""
        parent_type = parent.get('type', '')
        if parent_type == 'database_id':
            return parent.get('database_id', '')
        elif parent_type == 'page_id':
            return parent.get('page_id', '')
        elif parent_type == 'workspace':
            return 'workspace'
        return ''
    
    def _analyze_page_content(self, blocks: List[Dict]) -> Dict:
        """Analyze page content structure"""
        analysis = {
            "block_count": len(blocks),
            "block_types": {},
            "text_content": "",
            "has_media": False,
            "has_databases": False,
            "word_count": 0
        }
        
        for block in blocks:
            block_type = block.get('type', 'unknown')
            analysis["block_types"][block_type] = analysis["block_types"].get(block_type, 0) + 1
            
            # Extract text content
            text = self._extract_block_text(block)
            if text:
                analysis["text_content"] += text + " "
            
            # Check for media
            if block_type in ['image', 'video', 'file', 'pdf']:
                analysis["has_media"] = True
            
            # Check for databases
            if block_type in ['child_database', 'database']:
                analysis["has_databases"] = True
        
        analysis["word_count"] = len(analysis["text_content"].split())
        analysis["text_content"] = analysis["text_content"].strip()[:500]  # Limit for response size
        
        return analysis
    
    def _extract_block_text(self, block: Dict) -> str:
        """Extract text from a Notion block"""
        block_type = block.get('type', '')
        block_data = block.get(block_type, {})
        
        text_content = ""
        
        # Handle different block types
        if block_type in ['paragraph', 'heading_1', 'heading_2', 'heading_3', 'bulleted_list_item', 'numbered_list_item']:
            rich_text = block_data.get('rich_text', [])
            text_content = ' '.join([t.get('plain_text', '') for t in rich_text])
        elif block_type == 'quote':
            rich_text = block_data.get('rich_text', [])
            text_content = ' '.join([t.get('plain_text', '') for t in rich_text])
        elif block_type == 'code':
            rich_text = block_data.get('rich_text', [])
            text_content = ' '.join([t.get('plain_text', '') for t in rich_text])
        
        return text_content
    
    def _get_template_blocks(self, template_type: str, title: str) -> List[Dict]:
        """Get template blocks for different page types"""
        
        templates = {
            "project": [
                {
                    "object": "block",
                    "type": "heading_1",
                    "heading_1": {
                        "rich_text": [{"type": "text", "text": {"content": "Project Overview"}}]
                    }
                },
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": "Project description and objectives..."}}]
                    }
                },
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"type": "text", "text": {"content": "Goals"}}]
                    }
                },
                {
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [{"type": "text", "text": {"content": "Goal 1"}}]
                    }
                },
                {
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [{"type": "text", "text": {"content": "Goal 2"}}]
                    }
                },
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"type": "text", "text": {"content": "Timeline"}}]
                    }
                },
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": "Project timeline and milestones..."}}]
                    }
                }
            ],
            
            "meeting": [
                {
                    "object": "block",
                    "type": "heading_1",
                    "heading_1": {
                        "rich_text": [{"type": "text", "text": {"content": f"Meeting Notes - {datetime.now().strftime('%Y-%m-%d')}"}}]
                    }
                },
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {"type": "text", "text": {"content": "Date: "}},
                            {"type": "text", "text": {"content": datetime.now().strftime('%B %d, %Y')}}
                        ]
                    }
                },
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"type": "text", "text": {"content": "Attendees"}}]
                    }
                },
                {
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [{"type": "text", "text": {"content": "Attendee 1"}}]
                    }
                },
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"type": "text", "text": {"content": "Agenda"}}]
                    }
                },
                {
                    "object": "block",
                    "type": "numbered_list_item",
                    "numbered_list_item": {
                        "rich_text": [{"type": "text", "text": {"content": "Topic 1"}}]
                    }
                },
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"type": "text", "text": {"content": "Action Items"}}]
                    }
                },
                {
                    "object": "block",
                    "type": "to_do",
                    "to_do": {
                        "rich_text": [{"type": "text", "text": {"content": "Action item 1"}}],
                        "checked": False
                    }
                }
            ],
            
            "task": [
                {
                    "object": "block",
                    "type": "heading_1",
                    "heading_1": {
                        "rich_text": [{"type": "text", "text": {"content": "Task Details"}}]
                    }
                },
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": "Task description and requirements..."}}]
                    }
                },
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"type": "text", "text": {"content": "Checklist"}}]
                    }
                },
                {
                    "object": "block",
                    "type": "to_do",
                    "to_do": {
                        "rich_text": [{"type": "text", "text": {"content": "Subtask 1"}}],
                        "checked": False
                    }
                },
                {
                    "object": "block",
                    "type": "to_do",
                    "to_do": {
                        "rich_text": [{"type": "text", "text": {"content": "Subtask 2"}}],
                        "checked": False
                    }
                }
            ],
            
            "note": [
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": "Note content goes here..."}}]
                    }
                },
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"type": "text", "text": {"content": "Key Points"}}]
                    }
                },
                {
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [{"type": "text", "text": {"content": "Key point 1"}}]
                    }
                },
                {
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [{"type": "text", "text": {"content": "Key point 2"}}]
                    }
                }
            ]
        }
        
        return templates.get(template_type, [])

    def _extract_properties(self, properties: Dict) -> Dict:
        """Extract and format page properties"""
        extracted = {}
        
        for prop_name, prop_data in properties.items():
            prop_type = prop_data.get("type", "unknown")
            
            if prop_type == "title":
                title_array = prop_data.get("title", [])
                extracted[prop_name] = "".join([t.get("plain_text", "") for t in title_array])
            elif prop_type == "rich_text":
                text_array = prop_data.get("rich_text", [])
                extracted[prop_name] = "".join([t.get("plain_text", "") for t in text_array])
            elif prop_type == "select":
                select_data = prop_data.get("select")
                extracted[prop_name] = select_data.get("name") if select_data else None
            elif prop_type == "multi_select":
                multi_select = prop_data.get("multi_select", [])
                extracted[prop_name] = [item.get("name") for item in multi_select]
            elif prop_type == "date":
                date_data = prop_data.get("date")
                if date_data:
                    extracted[prop_name] = {
                        "start": date_data.get("start"),
                        "end": date_data.get("end")
                    }
            elif prop_type == "checkbox":
                extracted[prop_name] = prop_data.get("checkbox", False)
            elif prop_type == "number":
                extracted[prop_name] = prop_data.get("number")
            elif prop_type == "url":
                extracted[prop_name] = prop_data.get("url")
            elif prop_type == "email":
                extracted[prop_name] = prop_data.get("email")
            elif prop_type == "phone_number":
                extracted[prop_name] = prop_data.get("phone_number")
            else:
                extracted[prop_name] = str(prop_data)
                
        return extracted


# =============================================================================
# ENHANCED NOTION CONTENT ANALYZER TOOL
# =============================================================================

class ContentAnalyzerTool(BaseTool):
    """Enhanced Notion content analyzer tool for comprehensive workspace analysis"""
    
    name: str = "enhanced_notion_content_analyzer"
    description: str = """
    Advanced Notion content analyzer for comprehensive page and database analysis.
    
    Actions:
    - 'analyze_page': Detailed page content and structure analysis
    - 'analyze_database': Database schema and content pattern analysis  
    - 'extract_insights': Extract key insights from content
    - 'content_audit': Comprehensive content quality audit
    
    Provides detailed analytics and actionable insights for content optimization.
    """
    args_schema: type = ContentAnalyzerInput
    
    async def _arun(self, **kwargs) -> str:
        """Async implementation"""
        return await self._execute_analyzer_action(**kwargs)
    
    def _run(self, **kwargs) -> str:
        """Sync implementation"""
        return run_async_in_thread(self._execute_analyzer_action(**kwargs))
    
    async def _execute_analyzer_action(
        self,
        user_id: str,
        action: str,
        target_id: str,
        analysis_scope: str = "comprehensive",
        include_suggestions: bool = True
    ) -> str:
        """Execute the analyzer action"""
        access_token = await get_notion_access_token(user_id)
        if not access_token:
            return json.dumps({
                "status": "error",
                "message": "No valid Notion access token found. Please connect Notion.",
                "error_code": "AUTH_REQUIRED"
            })
        
        try:
            if action == "analyze_page":
                return await self._analyze_page_comprehensive(access_token, target_id, analysis_scope, include_suggestions)
            elif action == "analyze_database":
                return await self._analyze_database_comprehensive(access_token, target_id, analysis_scope, include_suggestions)
            elif action == "extract_insights":
                return await self._extract_content_insights(access_token, target_id)
            elif action == "content_audit":
                return await self._content_quality_audit(access_token, target_id)
            else:
                return json.dumps({
                    "status": "error",
                    "message": f"Unknown action: {action}. Available actions: analyze_page, analyze_database, extract_insights, content_audit",
                    "error_code": "INVALID_ACTION"
                })
        
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Error executing analyzer action: {str(e)}",
                "error_code": "EXECUTION_ERROR"
            })
    
    async def _analyze_page_comprehensive(self, access_token: str, page_id: str, scope: str, include_suggestions: bool) -> str:
        """Comprehensive page analysis"""
        # Use page manager to read page
        page_manager = PageManagerTool()
        page_result = await page_manager._read_page(access_token, page_id)
        page_data = json.loads(page_result)
        
        if page_data.get("status") != "success":
            return page_result
        
        page = page_data.get("page", {})
        content_analysis = page.get("content_analysis", {})
        
        # Enhanced analysis
        analysis = {
            "page_info": {
                "id": page.get("id", ""),
                "title": page.get("title", ""),
                "created": page.get("created_time", ""),
                "last_edited": page.get("last_edited_time", ""),
                "archived": page.get("archived", False)
            },
            "content_metrics": {
                "word_count": content_analysis.get("word_count", 0),
                "block_count": content_analysis.get("block_count", 0),
                "block_types": content_analysis.get("block_types", {}),
                "has_media": content_analysis.get("has_media", False),
                "has_databases": content_analysis.get("has_databases", False)
            },
            "structure_analysis": self._analyze_page_structure(content_analysis),
            "readability_metrics": self._calculate_readability_metrics(content_analysis.get("text_content", ""))
        }
        
        if include_suggestions:
            analysis["suggestions"] = self._generate_page_suggestions(analysis)
        
        if scope == "deep":
            analysis["detailed_insights"] = self._generate_detailed_page_insights(analysis)
        
        return json.dumps({
            "status": "success",
            "message": f"Page analysis completed for '{page.get('title', 'Unknown')}'",
            "target_id": page_id,
            "analysis_scope": scope,
            "analysis": analysis,
            "analyzed_at": datetime.now(timezone.utc).isoformat()
        })
    
    def _analyze_page_structure(self, content_analysis: Dict) -> Dict:
        """Analyze page structure quality"""
        block_types = content_analysis.get("block_types", {})
        total_blocks = sum(block_types.values())
        
        structure_score = 0.0
        structure_issues = []
        
        # Check for headings
        heading_count = block_types.get("heading_1", 0) + block_types.get("heading_2", 0) + block_types.get("heading_3", 0)
        if heading_count > 0:
            structure_score += 30
        else:
            structure_issues.append("No headings found - consider adding section headers")
        
        # Check for lists
        list_count = block_types.get("bulleted_list_item", 0) + block_types.get("numbered_list_item", 0)
        if list_count > 0:
            structure_score += 20
        
        # Check for variety in content types
        unique_types = len(block_types)
        if unique_types > 3:
            structure_score += 25
        elif unique_types == 1:
            structure_issues.append("Content uses only one block type - consider adding variety")
        
        # Check for appropriate length
        if total_blocks > 5:
            structure_score += 25
        elif total_blocks < 3:
            structure_issues.append("Page is quite short - consider adding more content")
        
        return {
            "structure_score": min(structure_score, 100),
            "total_blocks": total_blocks,
            "unique_block_types": unique_types,
            "has_headings": heading_count > 0,
            "has_lists": list_count > 0,
            "structure_issues": structure_issues
        }
    
    def _calculate_readability_metrics(self, text_content: str) -> Dict:
        """Calculate readability metrics for text content"""
        if not text_content:
            return {"message": "No text content to analyze"}
        
        words = text_content.split()
        sentences = [s.strip() for s in re.split(r'[.!?]+', text_content) if s.strip()]
        
        if not words or not sentences:
            return {"message": "Insufficient text for analysis"}
        
        metrics = {
            "word_count": len(words),
            "sentence_count": len(sentences),
            "average_words_per_sentence": len(words) / len(sentences),
            "longest_sentence": max([len(s.split()) for s in sentences]),
            "shortest_sentence": min([len(s.split()) for s in sentences]),
            "readability_notes": []
        }
        
        # Add readability insights
        if metrics["average_words_per_sentence"] > 20:
            metrics["readability_notes"].append("Sentences are quite long - consider breaking them down")
        elif metrics["average_words_per_sentence"] < 8:
            metrics["readability_notes"].append("Sentences are very short - consider combining some for better flow")
        
        return metrics
    
    def _generate_page_suggestions(self, analysis: Dict) -> List[str]:
        """Generate suggestions for page improvement"""
        suggestions = []
        
        content_metrics = analysis.get("content_metrics", {})
        structure_analysis = analysis.get("structure_analysis", {})
        
        # Word count suggestions
        word_count = content_metrics.get("word_count", 0)
        if word_count < 50:
            suggestions.append("Page is quite brief - consider adding more detailed content")
        elif word_count > 2000:
            suggestions.append("Page is very long - consider breaking it into multiple pages")
        
        # Structure suggestions
        if not structure_analysis.get("has_headings", False):
            suggestions.append("Add headings to improve page organization and readability")
        
        if not structure_analysis.get("has_lists", False) and word_count > 200:
            suggestions.append("Consider using bullet points or numbered lists to organize information")
        
        # Media suggestions
        if not content_metrics.get("has_media", False) and word_count > 500:
            suggestions.append("Consider adding images or other media to make the page more engaging")
        
        return suggestions
    
    def _generate_detailed_page_insights(self, analysis: Dict) -> List[str]:
        """Generate detailed insights for deep analysis"""
        insights = []
        
        content_metrics = analysis.get("content_metrics", {})
        structure_analysis = analysis.get("structure_analysis", {})
        
        # Content insights
        block_count = content_metrics.get("block_count", 0)
        if block_count > 50:
            insights.append("High content density - this page serves as a comprehensive resource")
        elif block_count < 5:
            insights.append("Minimal content - this appears to be a brief note or placeholder")
        
        # Structure insights
        structure_score = structure_analysis.get("structure_score", 0)
        if structure_score > 80:
            insights.append("Excellent page structure with good organization and variety")
        elif structure_score < 40:
            insights.append("Page structure could be improved for better readability")
        
        return insights


# =============================================================================
# ENHANCED NOTION WORKSPACE INTELLIGENCE TOOL
# =============================================================================

class WorkspaceIntelligenceTool(BaseTool):
    """Enhanced Notion workspace intelligence tool for comprehensive workspace analysis"""
    
    name: str = "enhanced_notion_workspace_intelligence"
    description: str = """
    Advanced Notion workspace intelligence for comprehensive workspace analysis and optimization.
    
    Actions:
    - 'workspace_overview': Complete workspace analysis with metrics
    - 'activity_analysis': Analyze workspace activity patterns
    - 'optimization_suggestions': Generate workspace optimization recommendations
    - 'content_mapping': Map and analyze workspace content organization
    
    Provides strategic insights for workspace productivity and organization.
    """
    args_schema: type = WorkspaceIntelligenceInput
    
    async def _arun(self, **kwargs) -> str:
        """Async implementation"""
        return await self._execute_intelligence_action(**kwargs)
    
    def _run(self, **kwargs) -> str:
        """Sync implementation"""
        return run_async_in_thread(self._execute_intelligence_action(**kwargs))
    
    async def _execute_intelligence_action(
        self,
        user_id: str,
        action: str,
        timeframe: str = "week",
        include_metrics: bool = True,
        focus_area: Optional[str] = None
    ) -> str:
        """Execute the intelligence action"""
        access_token = await get_notion_access_token(user_id)
        if not access_token:
            return json.dumps({
                "status": "error",
                "message": "No valid Notion access token found. Please connect Notion.",
                "error_code": "AUTH_REQUIRED"
            })
        
        try:
            if action == "workspace_overview":
                return await self._workspace_overview(access_token, timeframe, include_metrics)
            elif action == "activity_analysis":
                return await self._activity_analysis(access_token, timeframe)
            elif action == "optimization_suggestions":
                return await self._optimization_suggestions(access_token, focus_area)
            elif action == "content_mapping":
                return await self._content_mapping(access_token)
            else:
                return json.dumps({
                    "status": "error",
                    "message": f"Unknown action: {action}. Available actions: workspace_overview, activity_analysis, optimization_suggestions, content_mapping",
                    "error_code": "INVALID_ACTION"
                })
        
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Error executing intelligence action: {str(e)}",
                "error_code": "EXECUTION_ERROR"
            })
    
    async def _workspace_overview(self, access_token: str, timeframe: str, include_metrics: bool) -> str:
        """Generate comprehensive workspace overview"""
        # Get all workspace content
        search_result = await self._search_all_content(access_token)
        
        if not search_result:
            return json.dumps({
                "status": "error",
                "message": "Failed to retrieve workspace content",
                "error_code": "SEARCH_ERROR"
            })
        
        pages = [item for item in search_result if item.get('object') == 'page']
        databases = [item for item in search_result if item.get('object') == 'database']
        
        # Calculate timeframe cutoff
        cutoff_date = self._calculate_timeframe_cutoff(timeframe)
        
        # Analyze content
        overview = {
            "workspace_summary": {
                "total_pages": len(pages),
                "total_databases": len(databases),
                "total_items": len(search_result)
            },
            "content_analysis": self._analyze_workspace_content(pages, databases, cutoff_date),
            "organization_analysis": self._analyze_workspace_organization(pages, databases)
        }
        
        if include_metrics:
            overview["detailed_metrics"] = self._calculate_workspace_metrics(pages, databases, cutoff_date)
        
        return json.dumps({
            "status": "success",
            "message": f"Workspace overview completed for {timeframe} timeframe",
            "timeframe": timeframe,
            "overview": overview,
            "analyzed_at": datetime.now(timezone.utc).isoformat()
        })
    
    async def _search_all_content(self, access_token: str) -> List[Dict]:
        """Search all workspace content"""
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
        
        all_results = []
        
        try:
            async with httpx.AsyncClient() as client:
                # Search with empty query to get all content
                response = await client.post(
                    "https://api.notion.com/v1/search",
                    headers=headers,
                    json={"page_size": 100}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    all_results.extend(data.get('results', []))
                    
                    # Handle pagination if needed
                    while data.get('has_more', False) and len(all_results) < 500:  # Limit to prevent excessive calls
                        response = await client.post(
                            "https://api.notion.com/v1/search",
                            headers=headers,
                            json={
                                "page_size": 100,
                                "start_cursor": data.get('next_cursor')
                            }
                        )
                        
                        if response.status_code == 200:
                            data = response.json()
                            all_results.extend(data.get('results', []))
                        else:
                            break
            
            return all_results
            
        except Exception as e:
            print(f"Error searching workspace: {e}")
            return []
    
    def _calculate_timeframe_cutoff(self, timeframe: str) -> datetime:
        """Calculate cutoff date for timeframe"""
        now = datetime.now(timezone.utc)
        
        if timeframe == "day":
            return now - timedelta(days=1)
        elif timeframe == "week":
            return now - timedelta(days=7)
        elif timeframe == "month":
            return now - timedelta(days=30)
        elif timeframe == "quarter":
            return now - timedelta(days=90)
        else:
            return now - timedelta(days=7)  # Default to week
    
    def _analyze_workspace_content(self, pages: List[Dict], databases: List[Dict], cutoff_date: datetime) -> Dict:
        """Analyze workspace content patterns"""
        analysis = {
            "content_distribution": {
                "pages": len(pages),
                "databases": len(databases),
                "ratio": len(pages) / max(len(databases), 1)
            },
            "recent_activity": {
                "pages_created": 0,
                "pages_edited": 0,
                "databases_created": 0,
                "databases_edited": 0
            },
            "content_types": {},
            "parent_distribution": {}
        }
        
        # Analyze recent activity
        for page in pages:
            created_date = self._parse_notion_date(page.get('created_time', ''))
            edited_date = self._parse_notion_date(page.get('last_edited_time', ''))
            
            if created_date and created_date > cutoff_date:
                analysis["recent_activity"]["pages_created"] += 1
            if edited_date and edited_date > cutoff_date:
                analysis["recent_activity"]["pages_edited"] += 1
            
            # Analyze parent distribution
            parent = page.get('parent', {})
            parent_type = parent.get('type', 'unknown')
            analysis["parent_distribution"][parent_type] = analysis["parent_distribution"].get(parent_type, 0) + 1
        
        for database in databases:
            created_date = self._parse_notion_date(database.get('created_time', ''))
            edited_date = self._parse_notion_date(database.get('last_edited_time', ''))
            
            if created_date and created_date > cutoff_date:
                analysis["recent_activity"]["databases_created"] += 1
            if edited_date and edited_date > cutoff_date:
                analysis["recent_activity"]["databases_edited"] += 1
        
        return analysis
    
    def _analyze_workspace_organization(self, pages: List[Dict], databases: List[Dict]) -> Dict:
        """Analyze workspace organization quality"""
        organization = {
            "organization_score": 0.0,
            "structure_insights": [],
            "hierarchy_depth": 0,
            "orphaned_pages": 0
        }
        
        # Calculate organization metrics
        total_items = len(pages) + len(databases)
        
        if total_items == 0:
            return organization
        
        # Check for proper hierarchy
        workspace_items = 0
        database_items = 0
        page_items = 0
        
        for item in pages + databases:
            parent = item.get('parent', {})
            parent_type = parent.get('type', '')
            
            if parent_type == 'workspace':
                workspace_items += 1
            elif parent_type == 'database_id':
                database_items += 1
            elif parent_type == 'page_id':
                page_items += 1
        
        # Score based on organization patterns
        if database_items > workspace_items * 0.5:
            organization["organization_score"] += 40
            organization["structure_insights"].append("Good use of databases for structured content")
        
        if workspace_items < total_items * 0.8:
            organization["organization_score"] += 30
            organization["structure_insights"].append("Well-organized hierarchy with proper nesting")
        else:
            organization["structure_insights"].append("Many items at workspace level - consider organizing into databases or parent pages")
        
        organization["orphaned_pages"] = workspace_items
        
        return organization
    
    def _calculate_workspace_metrics(self, pages: List[Dict], databases: List[Dict], cutoff_date: datetime) -> Dict:
        """Calculate detailed workspace metrics"""
        metrics = {
            "productivity_metrics": {
                "creation_rate": 0.0,
                "edit_rate": 0.0,
                "activity_level": "low"
            },
            "content_health": {
                "active_content_ratio": 0.0,
                "stale_content_count": 0,
                "content_freshness_score": 0.0
            },
            "collaboration_indicators": {
                "shared_content_ratio": 0.0,
                "public_content_count": 0
            }
        }
        
        total_items = len(pages) + len(databases)
        if total_items == 0:
            return metrics
        
        # Calculate activity metrics
        recent_creates = 0
        recent_edits = 0
        stale_items = 0
        
        for item in pages + databases:
            created_date = self._parse_notion_date(item.get('created_time', ''))
            edited_date = self._parse_notion_date(item.get('last_edited_time', ''))
            
            if created_date and created_date > cutoff_date:
                recent_creates += 1
            if edited_date and edited_date > cutoff_date:
                recent_edits += 1
                
            # Check for stale content (not edited in 30 days)
            thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
            if edited_date and edited_date < thirty_days_ago:
                stale_items += 1
        
        metrics["productivity_metrics"]["creation_rate"] = recent_creates / 7  # Per day average
        metrics["productivity_metrics"]["edit_rate"] = recent_edits / 7  # Per day average
        
        if recent_creates + recent_edits > total_items * 0.2:
            metrics["productivity_metrics"]["activity_level"] = "high"
        elif recent_creates + recent_edits > total_items * 0.1:
            metrics["productivity_metrics"]["activity_level"] = "medium"
        
        # Content health metrics
        metrics["content_health"]["stale_content_count"] = stale_items
        metrics["content_health"]["active_content_ratio"] = (total_items - stale_items) / total_items
        metrics["content_health"]["content_freshness_score"] = min(100, (recent_edits / max(total_items, 1)) * 100)
        
        return metrics
    
    def _parse_notion_date(self, date_str: str) -> Optional[datetime]:
        """Parse Notion date string"""
        try:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except:
            return None


# =============================================================================
# ENHANCED NOTION TOOL INSTANCES
# =============================================================================

# Create tool instances
enhanced_notion_database_manager = DatabaseManagerTool()
enhanced_notion_page_manager = PageManagerTool()
enhanced_notion_content_analyzer = ContentAnalyzerTool()
enhanced_notion_workspace_intelligence = WorkspaceIntelligenceTool()

# Export all enhanced tools
__all__ = [
    'DatabaseManagerTool',
    'PageManagerTool',
    'ContentAnalyzerTool', 
    'WorkspaceIntelligenceTool',
    'enhanced_notion_database_manager',
    'enhanced_notion_page_manager',
    'enhanced_notion_content_analyzer',
    'enhanced_notion_workspace_intelligence'
]