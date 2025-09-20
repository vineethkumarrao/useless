"""
Enhanced Google Docs Tools for CrewAI Integration

This module provides advanced Google Docs tools that build upon the basic functionality
to provide enhanced features for document management, collaborative editing, 
formatting, and intelligent document operations.

Enhanced tools follow CrewAI Phase 2 structured response patterns and provide
comprehensive document manipulation capabilities for professional workflows.
"""

from typing import Dict, List, Optional, Union, Any
from pydantic import BaseModel, Field
from langchain.tools import BaseTool
import httpx
import json
from datetime import datetime, timezone, timedelta
import re
from dataclasses import dataclass

# Import existing OAuth functionality
from langchain_tools import get_google_docs_access_token, run_async_in_thread


# =============================================================================
# ENHANCED GOOGLE DOCS TOOLS - DATA MODELS
# =============================================================================

@dataclass
class DocumentInfo:
    """Document information structure"""
    id: str
    title: str
    created_time: str
    modified_time: str
    owner: str
    shared: bool
    permissions: str
    word_count: int
    web_view_link: str
    edit_link: str

@dataclass
class DocumentContent:
    """Document content structure"""
    title: str
    text_content: str
    formatted_content: dict
    headings: List[Dict]
    tables: List[Dict]
    images: List[Dict]
    links: List[Dict]
    comments: List[Dict]

@dataclass
class DocumentMetrics:
    """Document analysis metrics"""
    word_count: int
    character_count: int
    paragraph_count: int
    heading_count: int
    table_count: int
    image_count: int
    link_count: int
    comment_count: int
    reading_time_minutes: int
    complexity_score: float

class DocumentFilters(BaseModel):
    """Advanced document filtering options"""
    title_contains: Optional[str] = Field(None, description="Filter by title containing text")
    owner_email: Optional[str] = Field(None, description="Filter by document owner")
    shared_with_me: Optional[bool] = Field(None, description="Filter shared documents")
    modified_after: Optional[str] = Field(None, description="Filter by modification date (YYYY-MM-DD or relative like '7d')")
    content_contains: Optional[str] = Field(None, description="Filter by content containing text")
    file_type: Optional[str] = Field("document", description="Document type filter")
    max_results: int = Field(50, description="Maximum results to return")

class FormattingOptions(BaseModel):
    """Document formatting options"""
    font_family: Optional[str] = Field(None, description="Font family (Arial, Times New Roman, etc.)")
    font_size: Optional[int] = Field(None, description="Font size in points")
    bold: Optional[bool] = Field(None, description="Bold formatting")
    italic: Optional[bool] = Field(None, description="Italic formatting")
    underline: Optional[bool] = Field(None, description="Underline formatting")
    text_color: Optional[str] = Field(None, description="Text color (hex format)")
    background_color: Optional[str] = Field(None, description="Background color (hex format)")
    alignment: Optional[str] = Field(None, description="Text alignment (left, center, right, justify)")

class CollaborationSettings(BaseModel):
    """Document collaboration settings"""
    share_with_emails: List[str] = Field(default_factory=list, description="Email addresses to share with")
    permission_level: str = Field("reader", description="Permission level: reader, commenter, editor")
    notify_users: bool = Field(True, description="Send notification emails")
    message: Optional[str] = Field(None, description="Custom message to include")


# =============================================================================
# ENHANCED GOOGLE DOCS TOOL INPUTS
# =============================================================================

class DocumentReaderInput(BaseModel):
    """Input for enhanced document reader tool"""
    user_id: str = Field(description="User ID for authentication")
    action: str = Field(description="Action: 'search', 'read', 'analyze'")
    document_id: Optional[str] = Field(None, description="Document ID for read/analyze actions")
    filters: Optional[DocumentFilters] = Field(None, description="Filters for search action")
    include_formatting: bool = Field(False, description="Include formatting information")
    extract_structure: bool = Field(True, description="Extract document structure (headings, tables, etc.)")

class DocumentEditorInput(BaseModel):
    """Input for enhanced document editor tool"""
    user_id: str = Field(description="User ID for authentication")
    action: str = Field(description="Action: 'create', 'update', 'format', 'insert'")
    document_id: Optional[str] = Field(None, description="Document ID for update operations")
    title: Optional[str] = Field(None, description="Document title for create action")
    content: Optional[str] = Field(None, description="Content to add or replace")
    position: Optional[str] = Field("end", description="Position for insert: 'start', 'end', or index number")
    formatting: Optional[FormattingOptions] = Field(None, description="Formatting options")
    template: Optional[str] = Field(None, description="Template type: 'report', 'meeting_notes', 'proposal', etc.")

class DocumentCollaboratorInput(BaseModel):
    """Input for enhanced document collaborator tool"""
    user_id: str = Field(description="User ID for authentication")
    action: str = Field(description="Action: 'share', 'manage_permissions', 'get_activity', 'add_comment'")
    document_id: str = Field(description="Document ID")
    collaboration_settings: Optional[CollaborationSettings] = Field(None, description="Collaboration settings for share action")
    comment_text: Optional[str] = Field(None, description="Comment text for add_comment action")
    comment_position: Optional[int] = Field(None, description="Position in document for comment")

class DocumentAnalyzerInput(BaseModel):
    """Input for enhanced document analyzer tool"""
    user_id: str = Field(description="User ID for authentication")
    action: str = Field(description="Action: 'analyze_content', 'extract_insights', 'generate_summary', 'check_readability'")
    document_id: str = Field(description="Document ID to analyze")
    analysis_type: Optional[str] = Field("comprehensive", description="Analysis type: 'basic', 'comprehensive', 'content_only'")
    include_suggestions: bool = Field(True, description="Include improvement suggestions")


# =============================================================================
# ENHANCED GOOGLE DOCS READER TOOL
# =============================================================================

class DocumentReaderTool(BaseTool):
    """Enhanced Google Docs reader tool with advanced search and analysis capabilities"""
    
    name: str = "enhanced_docs_reader"
    description: str = """
    Advanced Google Docs reader tool with enhanced search, content extraction, and document analysis.
    
    Actions:
    - 'search': Find documents with advanced filtering options
    - 'read': Read document content with structure extraction
    - 'analyze': Analyze document metrics and readability
    
    Returns comprehensive document information with structured data.
    """
    args_schema: type = DocumentReaderInput
    
    async def _arun(self, **kwargs) -> str:
        """Async implementation"""
        return await self._execute_reader_action(**kwargs)
    
    def _run(self, **kwargs) -> str:
        """Sync implementation"""
        return run_async_in_thread(self._execute_reader_action(**kwargs))
    
    async def _execute_reader_action(
        self,
        user_id: str,
        action: str,
        document_id: Optional[str] = None,
        filters: Optional[DocumentFilters] = None,
        include_formatting: bool = False,
        extract_structure: bool = True
    ) -> str:
        """Execute the reader action"""
        access_token = await get_google_docs_access_token(user_id)
        if not access_token:
            return json.dumps({
                "status": "error",
                "message": "No valid Google Docs access token found. Please connect Google Docs.",
                "error_code": "AUTH_REQUIRED"
            })
        
        try:
            if action == "search":
                return await self._search_documents(access_token, filters or DocumentFilters())
            elif action == "read":
                if not document_id:
                    return json.dumps({
                        "status": "error", 
                        "message": "document_id required for read action",
                        "error_code": "MISSING_DOCUMENT_ID"
                    })
                return await self._read_document(access_token, document_id, include_formatting, extract_structure)
            elif action == "analyze":
                if not document_id:
                    return json.dumps({
                        "status": "error",
                        "message": "document_id required for analyze action", 
                        "error_code": "MISSING_DOCUMENT_ID"
                    })
                return await self._analyze_document(access_token, document_id)
            else:
                return json.dumps({
                    "status": "error",
                    "message": f"Unknown action: {action}. Available actions: search, read, analyze",
                    "error_code": "INVALID_ACTION"
                })
        
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Error executing reader action: {str(e)}",
                "error_code": "EXECUTION_ERROR"
            })
    
    async def _search_documents(self, access_token: str, filters: DocumentFilters) -> str:
        """Search for documents with advanced filtering"""
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # Build search query
        query_parts = ["mimeType='application/vnd.google-apps.document'"]
        
        if filters.title_contains:
            query_parts.append(f"name contains '{filters.title_contains}'")
        
        if filters.owner_email:
            query_parts.append(f"'{filters.owner_email}' in owners")
        
        if filters.shared_with_me is not None:
            if filters.shared_with_me:
                query_parts.append("sharedWithMe=true")
            else:
                query_parts.append("sharedWithMe=false")
        
        if filters.modified_after:
            # Parse relative dates like "7d" or absolute dates
            if filters.modified_after.endswith('d'):
                days = int(filters.modified_after[:-1])
                date_str = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
            else:
                # Try to parse as YYYY-MM-DD
                try:
                    parsed_date = datetime.fromisoformat(filters.modified_after).replace(tzinfo=timezone.utc)
                    date_str = parsed_date.isoformat()
                except:
                    date_str = filters.modified_after
            
            query_parts.append(f"modifiedTime > '{date_str}'")
        
        query = " and ".join(query_parts)
        
        params = {
            "q": query,
            "pageSize": min(filters.max_results, 100),
            "fields": "files(id,name,createdTime,modifiedTime,owners,shared,permissions,webViewLink,size)"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://www.googleapis.com/drive/v3/files",
                    headers=headers,
                    params=params
                )
                
                if response.status_code != 200:
                    return json.dumps({
                        "status": "error",
                        "message": f"Search failed with status {response.status_code}",
                        "error_code": "API_ERROR"
                    })
                
                data = response.json()
                files = data.get('files', [])
                
                # Filter by content if requested (requires additional API calls)
                if filters.content_contains:
                    files = await self._filter_by_content(access_token, files, filters.content_contains)
                
                documents = []
                for file in files:
                    doc_info = {
                        "id": file.get('id', ''),
                        "title": file.get('name', 'Untitled'),
                        "created_time": file.get('createdTime', ''),
                        "modified_time": file.get('modifiedTime', ''),
                        "owner": file.get('owners', [{}])[0].get('displayName', 'Unknown') if file.get('owners') else 'Unknown',
                        "shared": file.get('shared', False),
                        "web_view_link": file.get('webViewLink', ''),
                        "size_bytes": file.get('size', 0)
                    }
                    documents.append(doc_info)
                
                return json.dumps({
                    "status": "success",
                    "message": f"Found {len(documents)} documents matching criteria",
                    "documents": documents,
                    "total_found": len(documents),
                    "query_used": query,
                    "filters_applied": filters.dict(exclude_none=True)
                })
        
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Search error: {str(e)}",
                "error_code": "SEARCH_ERROR"
            })
    
    async def _filter_by_content(self, access_token: str, files: List[Dict], content_filter: str) -> List[Dict]:
        """Filter documents by content (expensive operation - limits to first 10 files)"""
        if not content_filter:
            return files
        
        filtered_files = []
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # Limit content search to prevent rate limiting
        for file in files[:10]:  
            try:
                doc_id = file.get('id')
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"https://docs.googleapis.com/v1/documents/{doc_id}",
                        headers=headers
                    )
                    
                    if response.status_code == 200:
                        doc_data = response.json()
                        content = self._extract_text_content(doc_data.get('body', {}).get('content', []))
                        if content_filter.lower() in content.lower():
                            filtered_files.append(file)
            except:
                continue  # Skip files that can't be read
        
        return filtered_files
    
    async def _read_document(self, access_token: str, document_id: str, include_formatting: bool, extract_structure: bool) -> str:
        """Read document with comprehensive content extraction"""
        headers = {"Authorization": f"Bearer {access_token}"}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://docs.googleapis.com/v1/documents/{document_id}",
                    headers=headers
                )
                
                if response.status_code != 200:
                    return json.dumps({
                        "status": "error",
                        "message": f"Failed to read document. Status: {response.status_code}",
                        "error_code": "READ_ERROR"
                    })
                
                doc_data = response.json()
                title = doc_data.get('title', 'Untitled Document')
                body = doc_data.get('body', {})
                content_elements = body.get('content', [])
                
                # Extract text content
                text_content = self._extract_text_content(content_elements)
                
                result = {
                    "status": "success",
                    "message": f"Successfully read document '{title}'",
                    "document": {
                        "id": document_id,
                        "title": title,
                        "text_content": text_content,
                        "word_count": len(text_content.split()),
                        "character_count": len(text_content)
                    }
                }
                
                if extract_structure:
                    structure = self._extract_document_structure(content_elements)
                    result["document"]["structure"] = structure
                
                if include_formatting:
                    formatting_info = self._extract_formatting_info(content_elements)
                    result["document"]["formatting"] = formatting_info
                
                return json.dumps(result)
        
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Error reading document: {str(e)}",
                "error_code": "READ_EXCEPTION"
            })
    
    async def _analyze_document(self, access_token: str, document_id: str) -> str:
        """Analyze document metrics and readability"""
        # First read the document
        doc_result = await self._read_document(access_token, document_id, True, True)
        doc_data = json.loads(doc_result)
        
        if doc_data["status"] != "success":
            return doc_result
        
        document = doc_data["document"]
        text_content = document["text_content"]
        structure = document.get("structure", {})
        
        # Calculate metrics
        words = text_content.split()
        sentences = re.split(r'[.!?]+', text_content)
        paragraphs = text_content.split('\n\n')
        
        metrics = {
            "word_count": len(words),
            "character_count": len(text_content),
            "sentence_count": len([s for s in sentences if s.strip()]),
            "paragraph_count": len([p for p in paragraphs if p.strip()]),
            "average_words_per_sentence": len(words) / max(len(sentences), 1),
            "average_sentences_per_paragraph": len(sentences) / max(len(paragraphs), 1),
            "reading_time_minutes": max(1, len(words) // 200),  # Assume 200 WPM reading speed
            "headings": structure.get("headings", []),
            "tables": structure.get("tables", []),
            "links": structure.get("links", [])
        }
        
        # Calculate readability score (simplified Flesch Reading Ease)
        if metrics["sentence_count"] > 0 and metrics["word_count"] > 0:
            avg_sentence_length = metrics["word_count"] / metrics["sentence_count"]
            # Simplified calculation without syllable count
            readability_score = max(0, min(100, 206.835 - (1.015 * avg_sentence_length)))
        else:
            readability_score = 0
        
        # Generate insights
        insights = []
        if metrics["average_words_per_sentence"] > 20:
            insights.append("Consider shortening sentences for better readability")
        if len(structure.get("headings", [])) == 0 and metrics["word_count"] > 500:
            insights.append("Document would benefit from headings to improve structure")
        if readability_score < 30:
            insights.append("Document is quite complex - consider simplifying language")
        elif readability_score > 90:
            insights.append("Document is very easy to read")
        
        return json.dumps({
            "status": "success",
            "message": f"Document analysis completed for '{document['title']}'",
            "document_id": document_id,
            "metrics": metrics,
            "readability_score": round(readability_score, 1),
            "insights": insights,
            "analysis_timestamp": datetime.now(timezone.utc).isoformat()
        })
    
    def _extract_text_content(self, content_elements: List[Dict]) -> str:
        """Extract plain text from Google Docs content structure"""
        text = ""
        for element in content_elements:
            if 'paragraph' in element:
                paragraph = element['paragraph']
                for text_run in paragraph.get('elements', []):
                    if 'textRun' in text_run:
                        text += text_run['textRun'].get('content', '')
            elif 'table' in element:
                table = element['table']
                for row in table.get('tableRows', []):
                    for cell in row.get('tableCells', []):
                        cell_content = self._extract_text_content(cell.get('content', []))
                        text += cell_content + "\t"
                    text += "\n"
        return text
    
    def _extract_document_structure(self, content_elements: List[Dict]) -> Dict:
        """Extract document structure (headings, tables, lists, etc.)"""
        structure = {
            "headings": [],
            "tables": [],
            "lists": [],
            "links": [],
            "images": []
        }
        
        for element in content_elements:
            if 'paragraph' in element:
                paragraph = element['paragraph']
                style = paragraph.get('paragraphStyle', {})
                heading_id = style.get('headingId')
                
                if heading_id:
                    text = ""
                    for text_run in paragraph.get('elements', []):
                        if 'textRun' in text_run:
                            text += text_run['textRun'].get('content', '')
                    
                    structure["headings"].append({
                        "level": self._get_heading_level(style),
                        "text": text.strip(),
                        "id": heading_id
                    })
                
                # Extract links
                for text_run in paragraph.get('elements', []):
                    if 'textRun' in text_run:
                        text_style = text_run['textRun'].get('textStyle', {})
                        link = text_style.get('link', {})
                        if link:
                            structure["links"].append({
                                "text": text_run['textRun'].get('content', '').strip(),
                                "url": link.get('url', '')
                            })
            
            elif 'table' in element:
                table = element['table']
                rows = len(table.get('tableRows', []))
                cols = len(table.get('tableRows', [{}])[0].get('tableCells', [])) if rows > 0 else 0
                structure["tables"].append({
                    "rows": rows,
                    "columns": cols,
                    "has_header": rows > 0  # Simplified assumption
                })
        
        return structure
    
    def _get_heading_level(self, style: Dict) -> int:
        """Determine heading level from style"""
        named_style = style.get('namedStyleType', '')
        if 'HEADING_1' in named_style:
            return 1
        elif 'HEADING_2' in named_style:
            return 2
        elif 'HEADING_3' in named_style:
            return 3
        elif 'HEADING_4' in named_style:
            return 4
        elif 'HEADING_5' in named_style:
            return 5
        elif 'HEADING_6' in named_style:
            return 6
        return 0
    
    def _extract_formatting_info(self, content_elements: List[Dict]) -> Dict:
        """Extract formatting information from document"""
        formatting = {
            "fonts_used": set(),
            "text_styles": {
                "bold": False,
                "italic": False,
                "underline": False
            },
            "colors_used": set(),
            "alignments_used": set()
        }
        
        for element in content_elements:
            if 'paragraph' in element:
                paragraph = element['paragraph']
                # Check paragraph alignment
                alignment = paragraph.get('paragraphStyle', {}).get('alignment', 'START')
                formatting["alignments_used"].add(alignment)
                
                for text_run in paragraph.get('elements', []):
                    if 'textRun' in text_run:
                        text_style = text_run['textRun'].get('textStyle', {})
                        
                        # Font information
                        if 'weightedFontFamily' in text_style:
                            font = text_style['weightedFontFamily'].get('fontFamily', '')
                            if font:
                                formatting["fonts_used"].add(font)
                        
                        # Text styling
                        if text_style.get('bold'):
                            formatting["text_styles"]["bold"] = True
                        if text_style.get('italic'):
                            formatting["text_styles"]["italic"] = True
                        if text_style.get('underline'):
                            formatting["text_styles"]["underline"] = True
                        
                        # Colors
                        fg_color = text_style.get('foregroundColor', {})
                        if fg_color:
                            color = fg_color.get('color', {}).get('rgbColor', {})
                            if color:
                                color_hex = self._rgb_to_hex(color)
                                formatting["colors_used"].add(color_hex)
        
        # Convert sets to lists for JSON serialization
        formatting["fonts_used"] = list(formatting["fonts_used"])
        formatting["colors_used"] = list(formatting["colors_used"]) 
        formatting["alignments_used"] = list(formatting["alignments_used"])
        
        return formatting
    
    def _rgb_to_hex(self, rgb_color: Dict) -> str:
        """Convert RGB color to hex format"""
        r = int(rgb_color.get('red', 0) * 255)
        g = int(rgb_color.get('green', 0) * 255)
        b = int(rgb_color.get('blue', 0) * 255)
        return f"#{r:02x}{g:02x}{b:02x}"


# =============================================================================
# ENHANCED GOOGLE DOCS EDITOR TOOL
# =============================================================================

class DocumentEditorTool(BaseTool):
    """Enhanced Google Docs editor tool with advanced editing and formatting"""
    
    name: str = "enhanced_docs_editor"
    description: str = """
    Advanced Google Docs editor tool with enhanced editing, formatting, and template capabilities.
    
    Actions:
    - 'create': Create new documents with templates
    - 'update': Update existing document content
    - 'format': Apply advanced formatting to document sections
    - 'insert': Insert content at specific positions
    
    Supports templates, advanced formatting, and intelligent content insertion.
    """
    args_schema: type = DocumentEditorInput
    
    async def _arun(self, **kwargs) -> str:
        """Async implementation"""
        return await self._execute_editor_action(**kwargs)
    
    def _run(self, **kwargs) -> str:
        """Sync implementation"""  
        return run_async_in_thread(self._execute_editor_action(**kwargs))
    
    async def _execute_editor_action(
        self,
        user_id: str,
        action: str,
        document_id: Optional[str] = None,
        title: Optional[str] = None,
        content: Optional[str] = None,
        position: str = "end",
        formatting: Optional[FormattingOptions] = None,
        template: Optional[str] = None
    ) -> str:
        """Execute the editor action"""
        access_token = await get_google_docs_access_token(user_id)
        if not access_token:
            return json.dumps({
                "status": "error",
                "message": "No valid Google Docs access token found. Please connect Google Docs.",
                "error_code": "AUTH_REQUIRED"
            })
        
        try:
            if action == "create":
                return await self._create_document(access_token, title, content, template)
            elif action == "update":
                if not document_id:
                    return json.dumps({
                        "status": "error",
                        "message": "document_id required for update action",
                        "error_code": "MISSING_DOCUMENT_ID"
                    })
                return await self._update_document(access_token, document_id, content, position)
            elif action == "format":
                if not document_id:
                    return json.dumps({
                        "status": "error",
                        "message": "document_id required for format action",
                        "error_code": "MISSING_DOCUMENT_ID"
                    })
                return await self._format_document(access_token, document_id, formatting)
            elif action == "insert":
                if not document_id:
                    return json.dumps({
                        "status": "error",
                        "message": "document_id required for insert action",
                        "error_code": "MISSING_DOCUMENT_ID"
                    })
                return await self._insert_content(access_token, document_id, content, position)
            else:
                return json.dumps({
                    "status": "error",
                    "message": f"Unknown action: {action}. Available actions: create, update, format, insert",
                    "error_code": "INVALID_ACTION"
                })
        
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Error executing editor action: {str(e)}",
                "error_code": "EXECUTION_ERROR"
            })
    
    async def _create_document(self, access_token: str, title: Optional[str], content: Optional[str], template: Optional[str]) -> str:
        """Create a new document with optional template"""
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        doc_title = title or f"New Document - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        # Apply template if specified
        if template:
            template_content = self._get_template_content(template, title or "Document")
            if template_content:
                content = template_content if not content else f"{template_content}\n\n{content}"
        
        try:
            async with httpx.AsyncClient() as client:
                # Create document
                response = await client.post(
                    "https://docs.googleapis.com/v1/documents",
                    headers=headers,
                    json={"title": doc_title}
                )
                
                if response.status_code != 200:
                    return json.dumps({
                        "status": "error",
                        "message": f"Failed to create document. Status: {response.status_code}",
                        "error_code": "CREATE_ERROR"
                    })
                
                doc = response.json()
                document_id = doc.get('documentId')
                
                # Add content if provided
                if content:
                    await self._insert_content_at_position(access_token, document_id, content, 1)
                
                # Get web view link
                drive_response = await client.get(
                    f"https://www.googleapis.com/drive/v3/files/{document_id}",
                    headers=headers,
                    params={"fields": "webViewLink,webContentLink"}
                )
                
                web_links = {}
                if drive_response.status_code == 200:
                    drive_data = drive_response.json()
                    web_links = {
                        "view_link": drive_data.get('webViewLink', ''),
                        "edit_link": drive_data.get('webContentLink', '')
                    }
                
                return json.dumps({
                    "status": "success",
                    "message": f"Successfully created document '{doc_title}'",
                    "document": {
                        "id": document_id,
                        "title": doc_title,
                        "created": datetime.now(timezone.utc).isoformat(),
                        **web_links
                    },
                    "template_applied": template if template else None
                })
        
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Error creating document: {str(e)}",
                "error_code": "CREATE_EXCEPTION"
            })
    
    async def _update_document(self, access_token: str, document_id: str, content: Optional[str], position: str) -> str:
        """Update existing document content"""
        if not content:
            return json.dumps({
                "status": "error",
                "message": "Content required for update action",
                "error_code": "MISSING_CONTENT"
            })
        
        try:
            # Get current document info
            headers = {"Authorization": f"Bearer {access_token}"}
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://docs.googleapis.com/v1/documents/{document_id}",
                    headers=headers
                )
                
                if response.status_code != 200:
                    return json.dumps({
                        "status": "error",
                        "message": f"Failed to access document. Status: {response.status_code}",
                        "error_code": "ACCESS_ERROR"
                    })
                
                doc_data = response.json()
                doc_title = doc_data.get('title', 'Unknown Document')
                
                # Calculate insertion position
                if position == "start":
                    insert_index = 1
                elif position == "end":
                    # Find the end of document
                    body = doc_data.get('body', {})
                    content_elements = body.get('content', [])
                    end_index = 1
                    for element in content_elements:
                        if 'endIndex' in element:
                            end_index = max(end_index, element['endIndex'])
                    insert_index = max(1, end_index - 1)
                else:
                    try:
                        insert_index = int(position)
                    except ValueError:
                        insert_index = 1
                
                # Insert content
                await self._insert_content_at_position(access_token, document_id, content, insert_index)
                
                return json.dumps({
                    "status": "success",
                    "message": f"Successfully updated document '{doc_title}'",
                    "document_id": document_id,
                    "content_added": len(content.split()),
                    "insertion_position": position,
                    "updated": datetime.now(timezone.utc).isoformat()
                })
        
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Error updating document: {str(e)}",
                "error_code": "UPDATE_EXCEPTION"
            })
    
    async def _insert_content_at_position(self, access_token: str, document_id: str, content: str, index: int):
        """Insert content at specific index"""
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        requests = [{
            "insertText": {
                "location": {"index": index},
                "text": content + "\n"
            }
        }]
        
        async with httpx.AsyncClient() as client:
            await client.post(
                f"https://docs.googleapis.com/v1/documents/{document_id}:batchUpdate",
                headers=headers,
                json={"requests": requests}
            )
    
    def _get_template_content(self, template: str, doc_title: str) -> str:
        """Get template content based on template type"""
        templates = {
            "report": f"""# {doc_title}

## Executive Summary
[Brief overview of the main findings and recommendations]

## Introduction
[Background information and purpose of the report]

## Methodology
[Explanation of methods used]

## Findings
[Detailed findings and analysis]

## Recommendations
[Actionable recommendations based on findings]

## Conclusion
[Summary and final thoughts]

---
*Report generated on {datetime.now().strftime('%B %d, %Y')}*
""",
            
            "meeting_notes": f"""# {doc_title}
**Date:** {datetime.now().strftime('%B %d, %Y')}
**Time:** [Meeting time]
**Attendees:** [List of attendees]

## Agenda
- [Agenda item 1]
- [Agenda item 2]
- [Agenda item 3]

## Discussion Points
### Topic 1
[Discussion notes]

### Topic 2
[Discussion notes]

## Action Items
- [ ] [Action item 1] - [Assigned to] - [Due date]
- [ ] [Action item 2] - [Assigned to] - [Due date]

## Next Steps
[Next meeting date and follow-up items]
""",
            
            "proposal": f"""# {doc_title}

## Overview
[Brief description of the proposal]

## Problem Statement
[Description of the problem being addressed]

## Proposed Solution
[Detailed description of the proposed solution]

## Benefits
- [Benefit 1]
- [Benefit 2]
- [Benefit 3]

## Implementation Plan
### Phase 1
[Phase 1 details]

### Phase 2
[Phase 2 details]

## Timeline
[Project timeline with milestones]

## Budget
[Cost breakdown and budget considerations]

## Conclusion
[Summary and call to action]

---
*Prepared by: [Your name]*
*Date: {datetime.now().strftime('%B %d, %Y')}*
""",
            
            "project_plan": f"""# {doc_title}

## Project Overview
**Project Name:** {doc_title}
**Start Date:** {datetime.now().strftime('%B %d, %Y')}
**End Date:** [Project end date]
**Project Manager:** [Name]

## Objectives
- [Objective 1]
- [Objective 2]
- [Objective 3]

## Scope
### In Scope
- [In scope item 1]
- [In scope item 2]

### Out of Scope
- [Out of scope item 1]
- [Out of scope item 2]

## Deliverables
1. [Deliverable 1]
2. [Deliverable 2]
3. [Deliverable 3]

## Timeline & Milestones
| Milestone | Due Date | Status |
|-----------|----------|---------|
| [Milestone 1] | [Date] | Pending |
| [Milestone 2] | [Date] | Pending |

## Resources
- **Team Members:** [List team members]
- **Budget:** [Budget amount]
- **Tools/Software:** [Required tools]

## Risk Management
| Risk | Impact | Likelihood | Mitigation Strategy |
|------|--------|------------|-------------------|
| [Risk 1] | [High/Medium/Low] | [High/Medium/Low] | [Strategy] |

## Success Metrics
- [Metric 1]
- [Metric 2]
- [Metric 3]
"""
        }
        
        return templates.get(template, "")


# =============================================================================
# ENHANCED GOOGLE DOCS COLLABORATOR TOOL
# =============================================================================

class DocumentCollaboratorTool(BaseTool):
    """Enhanced Google Docs collaboration tool for sharing and teamwork features"""
    
    name: str = "enhanced_docs_collaborator"
    description: str = """
    Advanced Google Docs collaboration tool for managing document sharing, permissions, and teamwork.
    
    Actions:
    - 'share': Share documents with specific users and permissions
    - 'manage_permissions': Update sharing permissions for users
    - 'get_activity': Get document activity and revision history
    - 'add_comment': Add comments to specific document locations
    
    Enables comprehensive document collaboration workflows.
    """
    args_schema: type = DocumentCollaboratorInput
    
    async def _arun(self, **kwargs) -> str:
        """Async implementation"""
        return await self._execute_collaborator_action(**kwargs)
    
    def _run(self, **kwargs) -> str:
        """Sync implementation"""
        return run_async_in_thread(self._execute_collaborator_action(**kwargs))
    
    async def _execute_collaborator_action(
        self,
        user_id: str,
        action: str,
        document_id: str,
        collaboration_settings: Optional[CollaborationSettings] = None,
        comment_text: Optional[str] = None,
        comment_position: Optional[int] = None
    ) -> str:
        """Execute collaboration action"""
        access_token = await get_google_docs_access_token(user_id)
        if not access_token:
            return json.dumps({
                "status": "error",
                "message": "No valid Google Docs access token found. Please connect Google Docs.",
                "error_code": "AUTH_REQUIRED"
            })
        
        try:
            if action == "share":
                if not collaboration_settings:
                    return json.dumps({
                        "status": "error",
                        "message": "collaboration_settings required for share action",
                        "error_code": "MISSING_SETTINGS"
                    })
                return await self._share_document(access_token, document_id, collaboration_settings)
            elif action == "manage_permissions":
                return await self._manage_permissions(access_token, document_id)
            elif action == "get_activity":
                return await self._get_document_activity(access_token, document_id)
            elif action == "add_comment":
                if not comment_text:
                    return json.dumps({
                        "status": "error",
                        "message": "comment_text required for add_comment action",
                        "error_code": "MISSING_COMMENT"
                    })
                return await self._add_comment(access_token, document_id, comment_text, comment_position or 1)
            else:
                return json.dumps({
                    "status": "error",
                    "message": f"Unknown action: {action}. Available actions: share, manage_permissions, get_activity, add_comment",
                    "error_code": "INVALID_ACTION"
                })
        
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Error executing collaborator action: {str(e)}",
                "error_code": "EXECUTION_ERROR"
            })
    
    async def _share_document(self, access_token: str, document_id: str, settings: CollaborationSettings) -> str:
        """Share document with specified users"""
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        results = []
        
        try:
            async with httpx.AsyncClient() as client:
                for email in settings.share_with_emails:
                    permission_data = {
                        "role": settings.permission_level,
                        "type": "user",
                        "emailAddress": email
                    }
                    
                    params = {}
                    if settings.notify_users:
                        params["sendNotificationEmail"] = "true"
                        if settings.message:
                            params["emailMessage"] = settings.message
                    
                    response = await client.post(
                        f"https://www.googleapis.com/drive/v3/files/{document_id}/permissions",
                        headers=headers,
                        json=permission_data,
                        params=params
                    )
                    
                    if response.status_code in [200, 201]:
                        results.append({
                            "email": email,
                            "status": "success",
                            "permission_level": settings.permission_level
                        })
                    else:
                        results.append({
                            "email": email,
                            "status": "error",
                            "error": f"HTTP {response.status_code}"
                        })
                
                successful = len([r for r in results if r["status"] == "success"])
                failed = len(results) - successful
                
                return json.dumps({
                    "status": "success",
                    "message": f"Document shared with {successful} users ({failed} failed)",
                    "document_id": document_id,
                    "sharing_results": results,
                    "successful_shares": successful,
                    "failed_shares": failed,
                    "permission_level": settings.permission_level,
                    "notifications_sent": settings.notify_users
                })
        
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Error sharing document: {str(e)}",
                "error_code": "SHARE_EXCEPTION"
            })
    
    async def _get_document_activity(self, access_token: str, document_id: str) -> str:
        """Get document activity and revision history"""
        headers = {"Authorization": f"Bearer {access_token}"}
        
        try:
            async with httpx.AsyncClient() as client:
                # Get document revisions
                response = await client.get(
                    f"https://www.googleapis.com/drive/v3/files/{document_id}/revisions",
                    headers=headers,
                    params={"fields": "revisions(id,modifiedTime,lastModifyingUser,size)"}
                )
                
                if response.status_code != 200:
                    return json.dumps({
                        "status": "error",
                        "message": f"Failed to get document activity. Status: {response.status_code}",
                        "error_code": "ACTIVITY_ERROR"
                    })
                
                revisions_data = response.json()
                revisions = revisions_data.get('revisions', [])
                
                # Get current permissions
                permissions_response = await client.get(
                    f"https://www.googleapis.com/drive/v3/files/{document_id}/permissions",
                    headers=headers,
                    params={"fields": "permissions(id,role,type,emailAddress,displayName)"}
                )
                
                permissions = []
                if permissions_response.status_code == 200:
                    permissions_data = permissions_response.json()
                    permissions = permissions_data.get('permissions', [])
                
                # Process revision history
                activity = []
                for revision in revisions[-10:]:  # Last 10 revisions
                    user = revision.get('lastModifyingUser', {})
                    activity.append({
                        "revision_id": revision.get('id', ''),
                        "modified_time": revision.get('modifiedTime', ''),
                        "user_name": user.get('displayName', 'Unknown'),
                        "user_email": user.get('emailAddress', ''),
                        "file_size": revision.get('size', 0)
                    })
                
                return json.dumps({
                    "status": "success",
                    "message": f"Retrieved activity for document",
                    "document_id": document_id,
                    "recent_activity": activity,
                    "total_revisions": len(revisions),
                    "current_permissions": [
                        {
                            "email": p.get('emailAddress', ''),
                            "name": p.get('displayName', ''),
                            "role": p.get('role', ''),
                            "type": p.get('type', '')
                        }
                        for p in permissions
                    ],
                    "activity_retrieved": datetime.now(timezone.utc).isoformat()
                })
        
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Error getting document activity: {str(e)}",
                "error_code": "ACTIVITY_EXCEPTION"
            })


# =============================================================================
# ENHANCED GOOGLE DOCS ANALYZER TOOL
# =============================================================================

class DocumentAnalyzerTool(BaseTool):
    """Enhanced Google Docs analyzer tool for comprehensive document analysis"""
    
    name: str = "enhanced_docs_analyzer"  
    description: str = """
    Advanced Google Docs analyzer tool for comprehensive document analysis and insights.
    
    Actions:
    - 'analyze_content': Comprehensive content analysis with metrics
    - 'extract_insights': Extract key insights and patterns from documents
    - 'generate_summary': Generate intelligent document summaries
    - 'check_readability': Analyze document readability and complexity
    
    Provides detailed analytics and actionable insights for document optimization.
    """
    args_schema: type = DocumentAnalyzerInput
    
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
        document_id: str,
        analysis_type: str = "comprehensive",
        include_suggestions: bool = True
    ) -> str:
        """Execute analyzer action"""
        access_token = await get_google_docs_access_token(user_id)
        if not access_token:
            return json.dumps({
                "status": "error",
                "message": "No valid Google Docs access token found. Please connect Google Docs.",
                "error_code": "AUTH_REQUIRED"
            })
        
        try:
            if action == "analyze_content":
                return await self._analyze_content(access_token, document_id, analysis_type, include_suggestions)
            elif action == "extract_insights":
                return await self._extract_insights(access_token, document_id)
            elif action == "generate_summary":
                return await self._generate_summary(access_token, document_id)
            elif action == "check_readability":
                return await self._check_readability(access_token, document_id)
            else:
                return json.dumps({
                    "status": "error",
                    "message": f"Unknown action: {action}. Available actions: analyze_content, extract_insights, generate_summary, check_readability",
                    "error_code": "INVALID_ACTION"
                })
        
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Error executing analyzer action: {str(e)}",
                "error_code": "EXECUTION_ERROR"
            })
    
    async def _analyze_content(self, access_token: str, document_id: str, analysis_type: str, include_suggestions: bool) -> str:
        """Perform comprehensive content analysis"""
        # Read document first
        reader_tool = DocumentReaderTool()
        doc_result = await reader_tool._read_document(access_token, document_id, True, True)
        doc_data = json.loads(doc_result)
        
        if doc_data["status"] != "success":
            return doc_result
        
        document = doc_data["document"]
        text_content = document["text_content"]
        structure = document.get("structure", {})
        
        # Enhanced analysis metrics
        metrics = self._calculate_enhanced_metrics(text_content, structure)
        
        # Content analysis
        content_analysis = self._analyze_content_patterns(text_content)
        
        # Generate suggestions if requested
        suggestions = []
        if include_suggestions:
            suggestions = self._generate_improvement_suggestions(metrics, content_analysis, structure)
        
        return json.dumps({
            "status": "success",
            "message": f"Content analysis completed for '{document['title']}'",
            "document_id": document_id,
            "analysis_type": analysis_type,
            "metrics": metrics,
            "content_analysis": content_analysis,
            "structure_analysis": {
                "headings": len(structure.get("headings", [])),
                "tables": len(structure.get("tables", [])),
                "links": len(structure.get("links", [])),
                "has_clear_structure": len(structure.get("headings", [])) > 0
            },
            "suggestions": suggestions if include_suggestions else [],
            "analyzed_at": datetime.now(timezone.utc).isoformat()
        })
    
    def _calculate_enhanced_metrics(self, text_content: str, structure: Dict) -> Dict:
        """Calculate enhanced document metrics"""
        words = text_content.split()
        sentences = [s.strip() for s in re.split(r'[.!?]+', text_content) if s.strip()]
        paragraphs = [p.strip() for p in text_content.split('\n\n') if p.strip()]
        
        # Basic metrics
        metrics = {
            "word_count": len(words),
            "character_count": len(text_content),
            "character_count_no_spaces": len(text_content.replace(' ', '')),
            "sentence_count": len(sentences),
            "paragraph_count": len(paragraphs),
            "average_words_per_sentence": len(words) / max(len(sentences), 1),
            "average_sentences_per_paragraph": len(sentences) / max(len(paragraphs), 1),
            "reading_time_minutes": max(1, len(words) // 200),
            "speaking_time_minutes": max(1, len(words) // 130)
        }
        
        # Advanced metrics
        unique_words = set(word.lower().strip('.,!?";:()[]{}') for word in words)
        metrics["unique_words"] = len(unique_words)
        metrics["lexical_diversity"] = len(unique_words) / max(len(words), 1)
        
        # Sentence length analysis
        sentence_lengths = [len(s.split()) for s in sentences]
        if sentence_lengths:
            metrics["shortest_sentence"] = min(sentence_lengths)
            metrics["longest_sentence"] = max(sentence_lengths)
            metrics["median_sentence_length"] = sorted(sentence_lengths)[len(sentence_lengths)//2]
        
        return metrics
    
    def _analyze_content_patterns(self, text_content: str) -> Dict:
        """Analyze content patterns and characteristics"""
        analysis = {
            "tone_indicators": {
                "formal_words": 0,
                "informal_words": 0,
                "technical_terms": 0,
                "action_words": 0
            },
            "structural_elements": {
                "questions": len(re.findall(r'\?', text_content)),
                "exclamations": len(re.findall(r'!', text_content)),
                "bullet_points": len(re.findall(r'[•\-\*]\s', text_content)),
                "numbered_lists": len(re.findall(r'\d+\.\s', text_content))
            },
            "complexity_indicators": {
                "long_sentences": 0,
                "complex_words": 0,
                "passive_voice_indicators": 0
            }
        }
        
        words = text_content.lower().split()
        sentences = [s.strip() for s in re.split(r'[.!?]+', text_content) if s.strip()]
        
        # Tone analysis
        formal_words = ['therefore', 'furthermore', 'consequently', 'nevertheless', 'moreover']
        informal_words = ['ok', 'yeah', 'gonna', 'wanna', 'kinda']
        technical_terms = ['algorithm', 'implementation', 'methodology', 'analysis', 'framework']
        action_words = ['create', 'develop', 'implement', 'execute', 'establish', 'build']
        
        for word in words:
            if word in formal_words:
                analysis["tone_indicators"]["formal_words"] += 1
            elif word in informal_words:
                analysis["tone_indicators"]["informal_words"] += 1
            elif word in technical_terms:
                analysis["tone_indicators"]["technical_terms"] += 1
            elif word in action_words:
                analysis["tone_indicators"]["action_words"] += 1
        
        # Complexity analysis
        for sentence in sentences:
            word_count = len(sentence.split())
            if word_count > 25:
                analysis["complexity_indicators"]["long_sentences"] += 1
        
        # Complex words (simplified - words longer than 6 characters)
        analysis["complexity_indicators"]["complex_words"] = len([w for w in words if len(w) > 6])
        
        # Passive voice indicators (simplified)
        passive_indicators = ['was', 'were', 'been', 'being']
        analysis["complexity_indicators"]["passive_voice_indicators"] = sum(words.count(indicator) for indicator in passive_indicators)
        
        return analysis
    
    def _generate_improvement_suggestions(self, metrics: Dict, content_analysis: Dict, structure: Dict) -> List[str]:
        """Generate improvement suggestions based on analysis"""
        suggestions = []
        
        # Readability suggestions
        if metrics["average_words_per_sentence"] > 20:
            suggestions.append("Consider breaking down long sentences (avg: {:.1f} words) for better readability".format(metrics["average_words_per_sentence"]))
        
        # Structure suggestions
        if len(structure.get("headings", [])) == 0 and metrics["word_count"] > 500:
            suggestions.append("Add headings to improve document structure and navigation")
        
        if metrics["paragraph_count"] < 3 and metrics["word_count"] > 300:
            suggestions.append("Break content into more paragraphs for better readability")
        
        # Content suggestions
        if content_analysis["complexity_indicators"]["long_sentences"] > metrics["sentence_count"] * 0.3:
            suggestions.append("High number of long sentences detected - consider shorter, clearer sentences")
        
        if content_analysis["structural_elements"]["questions"] == 0 and metrics["word_count"] > 200:
            suggestions.append("Consider adding questions to engage readers and break up content")
        
        # Engagement suggestions
        if metrics["lexical_diversity"] < 0.4:
            suggestions.append("Consider using more varied vocabulary to improve engagement")
        
        if content_analysis["tone_indicators"]["action_words"] == 0:
            suggestions.append("Add more action-oriented language to make content more engaging")
        
        return suggestions


# =============================================================================
# ENHANCED GOOGLE DOCS TOOL INSTANCES
# =============================================================================

# Create tool instances
enhanced_docs_reader = DocumentReaderTool()
enhanced_docs_editor = DocumentEditorTool()  
enhanced_docs_collaborator = DocumentCollaboratorTool()
enhanced_docs_analyzer = DocumentAnalyzerTool()

# Export all enhanced tools
__all__ = [
    'DocumentReaderTool',
    'DocumentEditorTool', 
    'DocumentCollaboratorTool',
    'DocumentAnalyzerTool',
    'enhanced_docs_reader',
    'enhanced_docs_editor',
    'enhanced_docs_collaborator', 
    'enhanced_docs_analyzer'
]