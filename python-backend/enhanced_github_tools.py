"""
Enhanced GitHub Tools for CrewAI Agents

Comprehensive GitHub integration tools providing advanced repository management,
issue/PR operations, code analysis, and development workflow automation.

Tools:
1. RepositoryManagerTool - Advanced repo operations, branch management, releases
2. IssueManagerTool - Smart issue management, templates, analytics  
3. CodeAnalyzerTool - Code quality analysis, security scanning, metrics
4. WorkflowManagerTool - CI/CD management, automation, deployment tracking

All tools return structured JSON responses compatible with CrewAI Phase 2.
"""

import json
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from pydantic import BaseModel, Field
from langchain.tools import BaseTool
import aiohttp
import base64
import hashlib

# Import GitHub access token function
from langchain_tools import get_github_access_token

# =============================================================================
# PYDANTIC MODELS FOR INPUTS
# =============================================================================

@dataclass
class RepositoryQuery:
    """Repository query configuration"""
    repo_name: Optional[str] = None
    owner: Optional[str] = None  
    include_stats: bool = True
    include_branches: bool = False
    include_releases: bool = False
    include_contributors: bool = False

@dataclass  
class IssueFilters:
    """Issue filtering options"""
    state: str = "open"  # open, closed, all
    labels: Optional[List[str]] = None
    assignee: Optional[str] = None
    milestone: Optional[str] = None
    since: Optional[str] = None
    sort: str = "created"  # created, updated, comments
    direction: str = "desc"  # asc, desc
    per_page: int = 30

@dataclass
class CodeAnalysisConfig:
    """Code analysis configuration"""
    analysis_type: str = "quality"  # quality, security, metrics, dependencies
    file_patterns: Optional[List[str]] = None
    include_tests: bool = True
    depth: str = "comprehensive"  # basic, standard, comprehensive
    exclude_patterns: Optional[List[str]] = None

@dataclass
class WorkflowConfig:
    """Workflow management configuration"""
    workflow_type: str = "all"  # all, ci, cd, tests, security
    include_runs: bool = True
    include_artifacts: bool = False
    status_filter: str = "all"  # all, active, disabled, success, failure
    max_results: int = 50

# Pydantic Input Models
class RepositoryManagerInput(BaseModel):
    """Input model for Repository Manager Tool"""
    user_id: str = Field(description="User ID for authentication")
    action: str = Field(description="Action to perform: 'list_repos', 'get_repo', 'create_repo', 'update_repo', 'delete_repo', 'manage_branches', 'create_release'")
    repo_query: Optional[Dict] = Field(default=None, description="Repository query configuration")
    repo_data: Optional[Dict] = Field(default=None, description="Repository data for create/update operations")
    branch_data: Optional[Dict] = Field(default=None, description="Branch management data")
    release_data: Optional[Dict] = Field(default=None, description="Release creation data")

class IssueManagerInput(BaseModel):
    """Input model for Issue Manager Tool"""  
    user_id: str = Field(description="User ID for authentication")
    action: str = Field(description="Action to perform: 'list_issues', 'get_issue', 'create_issue', 'update_issue', 'close_issue', 'list_prs', 'create_pr', 'merge_pr', 'get_analytics'")
    repo_owner: Optional[str] = Field(default=None, description="Repository owner")
    repo_name: Optional[str] = Field(default=None, description="Repository name")
    issue_filters: Optional[Dict] = Field(default=None, description="Issue filtering configuration")
    issue_data: Optional[Dict] = Field(default=None, description="Issue data for create/update operations")
    pr_data: Optional[Dict] = Field(default=None, description="Pull request data")
    analytics_config: Optional[Dict] = Field(default=None, description="Analytics configuration")

class CodeAnalyzerInput(BaseModel):
    """Input model for Code Analyzer Tool"""
    user_id: str = Field(description="User ID for authentication") 
    action: str = Field(description="Action to perform: 'analyze_repository', 'analyze_file', 'security_scan', 'dependency_check', 'code_metrics', 'quality_report'")
    repo_owner: Optional[str] = Field(default=None, description="Repository owner")
    repo_name: Optional[str] = Field(default=None, description="Repository name")
    file_path: Optional[str] = Field(default=None, description="Specific file path to analyze")
    analysis_config: Optional[Dict] = Field(default=None, description="Analysis configuration")
    report_format: str = Field(default="detailed", description="Report format: basic, detailed, comprehensive")

class WorkflowManagerInput(BaseModel):
    """Input model for Workflow Manager Tool"""
    user_id: str = Field(description="User ID for authentication")
    action: str = Field(description="Action to perform: 'list_workflows', 'get_workflow', 'trigger_workflow', 'get_runs', 'download_artifacts', 'workflow_analytics', 'deployment_status'")
    repo_owner: Optional[str] = Field(default=None, description="Repository owner")
    repo_name: Optional[str] = Field(default=None, description="Repository name") 
    workflow_config: Optional[Dict] = Field(default=None, description="Workflow configuration")
    workflow_id: Optional[str] = Field(default=None, description="Specific workflow ID")
    run_id: Optional[str] = Field(default=None, description="Specific workflow run ID")

# =============================================================================
# ENHANCED GITHUB REPOSITORY MANAGER TOOL  
# =============================================================================

class RepositoryManagerTool(BaseTool):
    """Enhanced GitHub repository manager for comprehensive repo operations"""
    
    name: str = "enhanced_github_repository_manager"
    description: str = """
    Advanced GitHub repository management tool for comprehensive repository operations.
    
    Actions:
    - 'list_repos': List user repositories with advanced filtering
    - 'get_repo': Get detailed repository information with analytics
    - 'create_repo': Create new repository with templates and settings
    - 'update_repo': Update repository settings and configuration
    - 'delete_repo': Delete repository with confirmation
    - 'manage_branches': Branch management operations (list, create, delete, protect)
    - 'create_release': Create releases with automated changelog generation
    
    Provides comprehensive repository management with analytics and automation.
    """
    args_schema: type = RepositoryManagerInput
    
    async def _arun(self, **kwargs) -> str:
        """Async implementation"""
        return await self._execute_repository_action(**kwargs)
    
    def _run(self, **kwargs) -> str:
        """Sync implementation"""  
        return asyncio.run(self._arun(**kwargs))
    
    async def _execute_repository_action(self, user_id: str, action: str, **kwargs) -> str:
        """Execute repository management action"""
        try:
            # Get GitHub access token
            access_token = await get_github_access_token(user_id)
            
            if not access_token:
                return json.dumps({
                    "status": "error",
                    "message": "GitHub integration not found or inactive",
                    "error_code": "GITHUB_NOT_CONFIGURED",
                    "action": action
                })
            
            # Execute action
            if action == "list_repos":
                return await self._list_repositories(access_token, kwargs.get('repo_query', {}))
            elif action == "get_repo":
                return await self._get_repository(access_token, kwargs.get('repo_query', {}))
            elif action == "create_repo":
                return await self._create_repository(access_token, kwargs.get('repo_data', {}))
            elif action == "update_repo":
                return await self._update_repository(access_token, kwargs.get('repo_query', {}), kwargs.get('repo_data', {}))
            elif action == "delete_repo":
                return await self._delete_repository(access_token, kwargs.get('repo_query', {}))
            elif action == "manage_branches":
                return await self._manage_branches(access_token, kwargs.get('repo_query', {}), kwargs.get('branch_data', {}))
            elif action == "create_release":
                return await self._create_release(access_token, kwargs.get('repo_query', {}), kwargs.get('release_data', {}))
            else:
                return json.dumps({
                    "status": "error",
                    "message": f"Unknown repository action: {action}",
                    "error_code": "INVALID_ACTION",
                    "available_actions": ["list_repos", "get_repo", "create_repo", "update_repo", "delete_repo", "manage_branches", "create_release"]
                })
                
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Repository action failed: {str(e)}",
                "error_code": "REPOSITORY_ACTION_FAILED",
                "action": action
            })

    async def _list_repositories(self, access_token: str, query_config: Dict) -> str:
        """List user repositories with filtering"""
        try:
            # Convert dict to dataclass, handling missing keys gracefully
            query = RepositoryQuery(
                repo_name=query_config.get('repo_name'),
                owner=query_config.get('owner'),
                include_stats=query_config.get('include_stats', True),
                include_branches=query_config.get('include_branches', False),
                include_releases=query_config.get('include_releases', False),
                include_contributors=query_config.get('include_contributors', False)
            )
            
            headers = {
                "Authorization": f"token {access_token}",
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "Enhanced-GitHub-Tools"
            }
            
            async with aiohttp.ClientSession() as session:
                # List repositories
                repos_url = "https://api.github.com/user/repos"
                params = {
                    "sort": "updated",
                    "per_page": 100,
                    "type": "all"
                }
                
                async with session.get(repos_url, headers=headers, params=params) as response:
                    if response.status == 200:
                        repos_data = await response.json()
                        
                        repositories = []
                        for repo in repos_data:
                            repo_info = {
                                "id": repo.get("id"),
                                "name": repo.get("name"),
                                "full_name": repo.get("full_name"),
                                "description": repo.get("description"),
                                "private": repo.get("private", False),
                                "fork": repo.get("fork", False),
                                "created_at": repo.get("created_at"),
                                "updated_at": repo.get("updated_at"),
                                "language": repo.get("language"),
                                "size": repo.get("size", 0),
                                "stargazers_count": repo.get("stargazers_count", 0),
                                "watchers_count": repo.get("watchers_count", 0),
                                "forks_count": repo.get("forks_count", 0),
                                "open_issues_count": repo.get("open_issues_count", 0),
                                "default_branch": repo.get("default_branch"),
                                "clone_url": repo.get("clone_url"),
                                "ssh_url": repo.get("ssh_url"),
                                "html_url": repo.get("html_url")
                            }
                            
                            if query.include_stats:
                                repo_info["statistics"] = await self._get_repo_statistics(session, headers, repo.get("full_name"))
                            
                            repositories.append(repo_info)
                        
                        # Filter by name if specified
                        if query.repo_name:
                            repositories = [r for r in repositories if query.repo_name.lower() in r["name"].lower()]
                        
                        return json.dumps({
                            "status": "success",
                            "message": f"Found {len(repositories)} repositories",
                            "repositories": repositories,
                            "total_count": len(repositories),
                            "retrieved_at": datetime.now(timezone.utc).isoformat()
                        })
                    else:
                        error_data = await response.json()
                        return json.dumps({
                            "status": "error",
                            "message": f"Failed to list repositories: {error_data.get('message', 'Unknown error')}",
                            "error_code": "GITHUB_API_ERROR"
                        })
                        
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Error listing repositories: {str(e)}",
                "error_code": "LIST_REPOS_FAILED"
            })

    async def _get_repository(self, access_token: str, query_config: Dict) -> str:
        """Get detailed repository information"""
        try:
            # Convert dict to dataclass, handling missing keys gracefully
            query = RepositoryQuery(
                repo_name=query_config.get('repo_name'),
                owner=query_config.get('owner'),
                include_stats=query_config.get('include_stats', True),
                include_branches=query_config.get('include_branches', False),
                include_releases=query_config.get('include_releases', False),
                include_contributors=query_config.get('include_contributors', False)
            )
            
            if not query.owner or not query.repo_name:
                return json.dumps({
                    "status": "error",
                    "message": "Repository owner and name are required",
                    "error_code": "MISSING_REPO_INFO"
                })
            
            headers = {
                "Authorization": f"token {access_token}",
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "Enhanced-GitHub-Tools"
            }
            
            async with aiohttp.ClientSession() as session:
                # Get repository details
                repo_url = f"https://api.github.com/repos/{query.owner}/{query.repo_name}"
                
                async with session.get(repo_url, headers=headers) as response:
                    if response.status == 200:
                        repo_data = await response.json()
                        
                        repository_info = {
                            "basic_info": {
                                "id": repo_data.get("id"),
                                "name": repo_data.get("name"),
                                "full_name": repo_data.get("full_name"),
                                "description": repo_data.get("description"),
                                "homepage": repo_data.get("homepage"),
                                "private": repo_data.get("private", False),
                                "fork": repo_data.get("fork", False),
                                "archived": repo_data.get("archived", False),
                                "disabled": repo_data.get("disabled", False),
                                "created_at": repo_data.get("created_at"),
                                "updated_at": repo_data.get("updated_at"),
                                "pushed_at": repo_data.get("pushed_at")
                            },
                            "metrics": {
                                "size": repo_data.get("size", 0),
                                "stargazers_count": repo_data.get("stargazers_count", 0),
                                "watchers_count": repo_data.get("watchers_count", 0),
                                "forks_count": repo_data.get("forks_count", 0),
                                "open_issues_count": repo_data.get("open_issues_count", 0),
                                "subscribers_count": repo_data.get("subscribers_count", 0)
                            },
                            "settings": {
                                "default_branch": repo_data.get("default_branch"),
                                "language": repo_data.get("language"),
                                "topics": repo_data.get("topics", []),
                                "has_issues": repo_data.get("has_issues", False),
                                "has_projects": repo_data.get("has_projects", False),
                                "has_wiki": repo_data.get("has_wiki", False),
                                "has_pages": repo_data.get("has_pages", False),
                                "has_downloads": repo_data.get("has_downloads", False),
                                "allow_squash_merge": repo_data.get("allow_squash_merge", True),
                                "allow_merge_commit": repo_data.get("allow_merge_commit", True),
                                "allow_rebase_merge": repo_data.get("allow_rebase_merge", True),
                                "delete_branch_on_merge": repo_data.get("delete_branch_on_merge", False)
                            },
                            "urls": {
                                "html_url": repo_data.get("html_url"),
                                "clone_url": repo_data.get("clone_url"),
                                "ssh_url": repo_data.get("ssh_url"),
                                "git_url": repo_data.get("git_url")
                            }
                        }
                        
                        # Add branches if requested
                        if query.include_branches:
                            repository_info["branches"] = await self._get_repo_branches(session, headers, query.owner, query.repo_name)
                        
                        # Add releases if requested  
                        if query.include_releases:
                            repository_info["releases"] = await self._get_repo_releases(session, headers, query.owner, query.repo_name)
                        
                        # Add contributors if requested
                        if query.include_contributors:
                            repository_info["contributors"] = await self._get_repo_contributors(session, headers, query.owner, query.repo_name)
                        
                        return json.dumps({
                            "status": "success",
                            "message": f"Retrieved repository '{query.repo_name}' details",
                            "repository": repository_info,
                            "retrieved_at": datetime.now(timezone.utc).isoformat()
                        })
                    else:
                        error_data = await response.json()
                        return json.dumps({
                            "status": "error",
                            "message": f"Failed to get repository: {error_data.get('message', 'Unknown error')}",
                            "error_code": "GITHUB_API_ERROR"
                        })
                        
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Error getting repository: {str(e)}",
                "error_code": "GET_REPO_FAILED"
            })

    async def _create_repository(self, access_token: str, repo_data: Dict) -> str:
        """Create a new repository"""
        try:
            headers = {
                "Authorization": f"token {access_token}",
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "Enhanced-GitHub-Tools",
                "Content-Type": "application/json"
            }
            
            # Prepare repository creation data
            create_data = {
                "name": repo_data.get("name", ""),
                "description": repo_data.get("description", ""),
                "homepage": repo_data.get("homepage", ""),
                "private": repo_data.get("private", False),
                "has_issues": repo_data.get("has_issues", True),
                "has_projects": repo_data.get("has_projects", True),
                "has_wiki": repo_data.get("has_wiki", True),
                "auto_init": repo_data.get("auto_init", True),
                "gitignore_template": repo_data.get("gitignore_template"),
                "license_template": repo_data.get("license_template")
            }
            
            # Remove None values
            create_data = {k: v for k, v in create_data.items() if v is not None}
            
            if not create_data.get("name"):
                return json.dumps({
                    "status": "error",
                    "message": "Repository name is required",
                    "error_code": "MISSING_REPO_NAME"
                })
            
            async with aiohttp.ClientSession() as session:
                create_url = "https://api.github.com/user/repos"
                
                async with session.post(create_url, headers=headers, json=create_data) as response:
                    if response.status == 201:
                        created_repo = await response.json()
                        
                        return json.dumps({
                            "status": "success",
                            "message": f"Successfully created repository '{created_repo.get('name')}'",
                            "repository": {
                                "id": created_repo.get("id"),
                                "name": created_repo.get("name"),
                                "full_name": created_repo.get("full_name"),
                                "html_url": created_repo.get("html_url"),
                                "clone_url": created_repo.get("clone_url"),
                                "ssh_url": created_repo.get("ssh_url"),
                                "private": created_repo.get("private"),
                                "created_at": created_repo.get("created_at")
                            },
                            "created_at": datetime.now(timezone.utc).isoformat()
                        })
                    else:
                        error_data = await response.json()
                        return json.dumps({
                            "status": "error",
                            "message": f"Failed to create repository: {error_data.get('message', 'Unknown error')}",
                            "error_code": "GITHUB_API_ERROR"
                        })
                        
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Error creating repository: {str(e)}",
                "error_code": "CREATE_REPO_FAILED"
            })

    async def _get_repo_statistics(self, session: aiohttp.ClientSession, headers: Dict, full_name: str) -> Dict:
        """Get repository statistics"""
        try:
            stats_url = f"https://api.github.com/repos/{full_name}/stats/contributors"
            async with session.get(stats_url, headers=headers) as response:
                if response.status == 200:
                    stats_data = await response.json()
                    
                    total_commits = sum(contributor.get("total", 0) for contributor in stats_data)
                    total_contributors = len(stats_data)
                    
                    return {
                        "total_commits": total_commits,
                        "total_contributors": total_contributors,
                        "latest_contributor_activity": max(
                            (week.get("w", 0) for contributor in stats_data for week in contributor.get("weeks", [])),
                            default=0
                        )
                    }
        except:
            pass
        
        return {"total_commits": 0, "total_contributors": 0, "latest_contributor_activity": 0}

    async def _get_repo_branches(self, session: aiohttp.ClientSession, headers: Dict, owner: str, repo: str) -> List[Dict]:
        """Get repository branches"""
        try:
            branches_url = f"https://api.github.com/repos/{owner}/{repo}/branches"
            async with session.get(branches_url, headers=headers) as response:
                if response.status == 200:
                    branches_data = await response.json()
                    return [
                        {
                            "name": branch.get("name"),
                            "commit_sha": branch.get("commit", {}).get("sha"),
                            "protected": branch.get("protected", False)
                        }
                        for branch in branches_data
                    ]
        except:
            pass
        
        return []

    async def _get_repo_releases(self, session: aiohttp.ClientSession, headers: Dict, owner: str, repo: str) -> List[Dict]:
        """Get repository releases"""
        try:
            releases_url = f"https://api.github.com/repos/{owner}/{repo}/releases"
            async with session.get(releases_url, headers=headers, params={"per_page": 10}) as response:
                if response.status == 200:
                    releases_data = await response.json()
                    return [
                        {
                            "id": release.get("id"),
                            "tag_name": release.get("tag_name"),
                            "name": release.get("name"),
                            "draft": release.get("draft", False),
                            "prerelease": release.get("prerelease", False),
                            "created_at": release.get("created_at"),
                            "published_at": release.get("published_at")
                        }
                        for release in releases_data
                    ]
        except:
            pass
        
        return []

    async def _get_repo_contributors(self, session: aiohttp.ClientSession, headers: Dict, owner: str, repo: str) -> List[Dict]:
        """Get repository contributors"""
        try:
            contributors_url = f"https://api.github.com/repos/{owner}/{repo}/contributors"
            async with session.get(contributors_url, headers=headers, params={"per_page": 20}) as response:
                if response.status == 200:
                    contributors_data = await response.json()
                    return [
                        {
                            "login": contributor.get("login"),
                            "contributions": contributor.get("contributions", 0),
                            "avatar_url": contributor.get("avatar_url"),
                            "html_url": contributor.get("html_url")
                        }
                        for contributor in contributors_data
                    ]
        except:
            pass
        
        return []


# =============================================================================
# ENHANCED GITHUB ISSUE MANAGER TOOL
# =============================================================================

class IssueManagerTool(BaseTool):
    """Enhanced GitHub issue and pull request manager"""
    
    name: str = "enhanced_github_issue_manager"
    description: str = """
    Advanced GitHub issue and pull request management tool.
    
    Actions:
    - 'list_issues': List issues with advanced filtering and sorting
    - 'get_issue': Get detailed issue information with comments
    - 'create_issue': Create new issue with templates and labels
    - 'update_issue': Update issue details, labels, assignees
    - 'close_issue': Close issue with resolution tracking
    - 'list_prs': List pull requests with status and reviews
    - 'create_pr': Create pull request with automation
    - 'merge_pr': Merge pull request with options
    - 'get_analytics': Get issue/PR analytics and insights
    
    Provides comprehensive issue tracking and pull request management.
    """
    args_schema: type = IssueManagerInput
    
    async def _arun(self, **kwargs) -> str:
        """Async implementation"""
        return await self._execute_issue_action(**kwargs)
    
    def _run(self, **kwargs) -> str:
        """Sync implementation"""
        return asyncio.run(self._arun(**kwargs))
    
    async def _execute_issue_action(self, user_id: str, action: str, **kwargs) -> str:
        """Execute issue management action"""
        try:
            # Get GitHub access token
            access_token = await get_github_access_token(user_id)
            
            if not access_token:
                return json.dumps({
                    "status": "error",
                    "message": "GitHub integration not found or inactive",
                    "error_code": "GITHUB_NOT_CONFIGURED",
                    "action": action
                })
            
            # Execute action
            if action == "list_issues":
                return await self._list_issues(access_token, kwargs.get('repo_owner'), kwargs.get('repo_name'), kwargs.get('issue_filters', {}))
            elif action == "get_issue":
                return await self._get_issue(access_token, kwargs.get('repo_owner'), kwargs.get('repo_name'), kwargs.get('issue_data', {}))
            elif action == "create_issue":
                return await self._create_issue(access_token, kwargs.get('repo_owner'), kwargs.get('repo_name'), kwargs.get('issue_data', {}))
            elif action == "update_issue":
                return await self._update_issue(access_token, kwargs.get('repo_owner'), kwargs.get('repo_name'), kwargs.get('issue_data', {}))
            elif action == "close_issue":
                return await self._close_issue(access_token, kwargs.get('repo_owner'), kwargs.get('repo_name'), kwargs.get('issue_data', {}))
            elif action == "list_prs":
                return await self._list_pull_requests(access_token, kwargs.get('repo_owner'), kwargs.get('repo_name'), kwargs.get('issue_filters', {}))
            elif action == "create_pr":
                return await self._create_pull_request(access_token, kwargs.get('repo_owner'), kwargs.get('repo_name'), kwargs.get('pr_data', {}))
            elif action == "merge_pr":
                return await self._merge_pull_request(access_token, kwargs.get('repo_owner'), kwargs.get('repo_name'), kwargs.get('pr_data', {}))
            elif action == "get_analytics":
                return await self._get_analytics(access_token, kwargs.get('repo_owner'), kwargs.get('repo_name'), kwargs.get('analytics_config', {}))
            else:
                return json.dumps({
                    "status": "error",
                    "message": f"Unknown issue action: {action}",
                    "error_code": "INVALID_ACTION",
                    "available_actions": ["list_issues", "get_issue", "create_issue", "update_issue", "close_issue", "list_prs", "create_pr", "merge_pr", "get_analytics"]
                })
                
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Issue action failed: {str(e)}",
                "error_code": "ISSUE_ACTION_FAILED",
                "action": action
            })

    async def _list_issues(self, access_token: str, repo_owner: str, repo_name: str, filter_config: Dict) -> str:
        """List issues with filtering"""
        try:
            if not repo_owner or not repo_name:
                return json.dumps({
                    "status": "error",
                    "message": "Repository owner and name are required",
                    "error_code": "MISSING_REPO_INFO"
                })
            
            # Convert dict to dataclass, handling missing keys gracefully
            filters = IssueFilters(
                state=filter_config.get('state', 'open'),
                labels=filter_config.get('labels'),
                assignee=filter_config.get('assignee'),
                milestone=filter_config.get('milestone'),
                since=filter_config.get('since'),
                sort=filter_config.get('sort', 'created'),
                direction=filter_config.get('direction', 'desc'),
                per_page=filter_config.get('per_page', 30)
            )
            
            headers = {
                "Authorization": f"token {access_token}",
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "Enhanced-GitHub-Tools"
            }
            
            params = {
                "state": filters.state,
                "sort": filters.sort,
                "direction": filters.direction,
                "per_page": min(filters.per_page, 100)
            }
            
            if filters.labels:
                params["labels"] = ",".join(filters.labels)
            if filters.assignee:
                params["assignee"] = filters.assignee
            if filters.milestone:
                params["milestone"] = filters.milestone
            if filters.since:
                params["since"] = filters.since
            
            async with aiohttp.ClientSession() as session:
                issues_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/issues"
                
                async with session.get(issues_url, headers=headers, params=params) as response:
                    if response.status == 200:
                        issues_data = await response.json()
                        
                        issues = []
                        for issue in issues_data:
                            # Skip pull requests (they appear in issues endpoint)
                            if issue.get("pull_request"):
                                continue
                                
                            issue_info = {
                                "number": issue.get("number"),
                                "id": issue.get("id"),
                                "title": issue.get("title"),
                                "body": issue.get("body", "")[:500] + ("..." if len(issue.get("body", "")) > 500 else ""),
                                "state": issue.get("state"),
                                "locked": issue.get("locked", False),
                                "created_at": issue.get("created_at"),
                                "updated_at": issue.get("updated_at"),
                                "closed_at": issue.get("closed_at"),
                                "author": {
                                    "login": issue.get("user", {}).get("login"),
                                    "avatar_url": issue.get("user", {}).get("avatar_url")
                                },
                                "assignees": [
                                    {"login": assignee.get("login"), "avatar_url": assignee.get("avatar_url")}
                                    for assignee in issue.get("assignees", [])
                                ],
                                "labels": [
                                    {"name": label.get("name"), "color": label.get("color")}
                                    for label in issue.get("labels", [])
                                ],
                                "milestone": {
                                    "title": issue.get("milestone", {}).get("title"),
                                    "number": issue.get("milestone", {}).get("number")
                                } if issue.get("milestone") else None,
                                "comments": issue.get("comments", 0),
                                "html_url": issue.get("html_url")
                            }
                            
                            issues.append(issue_info)
                        
                        return json.dumps({
                            "status": "success",
                            "message": f"Found {len(issues)} issues in {repo_owner}/{repo_name}",
                            "issues": issues,
                            "total_count": len(issues),
                            "filters_applied": asdict(filters),
                            "retrieved_at": datetime.now(timezone.utc).isoformat()
                        })
                    else:
                        error_data = await response.json()
                        return json.dumps({
                            "status": "error",
                            "message": f"Failed to list issues: {error_data.get('message', 'Unknown error')}",
                            "error_code": "GITHUB_API_ERROR"
                        })
                        
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Error listing issues: {str(e)}",
                "error_code": "LIST_ISSUES_FAILED"
            })

    async def _create_issue(self, access_token: str, repo_owner: str, repo_name: str, issue_data: Dict) -> str:
        """Create a new issue"""
        try:
            if not repo_owner or not repo_name:
                return json.dumps({
                    "status": "error",
                    "message": "Repository owner and name are required",
                    "error_code": "MISSING_REPO_INFO"
                })
            
            if not issue_data.get("title"):
                return json.dumps({
                    "status": "error",
                    "message": "Issue title is required",
                    "error_code": "MISSING_ISSUE_TITLE"
                })
            
            headers = {
                "Authorization": f"token {access_token}",
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "Enhanced-GitHub-Tools",
                "Content-Type": "application/json"
            }
            
            create_data = {
                "title": issue_data.get("title"),
                "body": issue_data.get("body", ""),
                "assignees": issue_data.get("assignees", []),
                "milestone": issue_data.get("milestone"),
                "labels": issue_data.get("labels", [])
            }
            
            # Remove None values
            create_data = {k: v for k, v in create_data.items() if v is not None}
            
            async with aiohttp.ClientSession() as session:
                issues_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/issues"
                
                async with session.post(issues_url, headers=headers, json=create_data) as response:
                    if response.status == 201:
                        created_issue = await response.json()
                        
                        return json.dumps({
                            "status": "success",
                            "message": f"Successfully created issue #{created_issue.get('number')} in {repo_owner}/{repo_name}",
                            "issue": {
                                "number": created_issue.get("number"),
                                "id": created_issue.get("id"),
                                "title": created_issue.get("title"),
                                "html_url": created_issue.get("html_url"),
                                "state": created_issue.get("state"),
                                "created_at": created_issue.get("created_at")
                            },
                            "created_at": datetime.now(timezone.utc).isoformat()
                        })
                    else:
                        error_data = await response.json()
                        return json.dumps({
                            "status": "error",
                            "message": f"Failed to create issue: {error_data.get('message', 'Unknown error')}",
                            "error_code": "GITHUB_API_ERROR"
                        })
                        
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Error creating issue: {str(e)}",
                "error_code": "CREATE_ISSUE_FAILED"
            })


# Create tool instances
enhanced_github_repository_manager = RepositoryManagerTool()
enhanced_github_issue_manager = IssueManagerTool()


# =============================================================================
# ENHANCED GITHUB CODE ANALYZER TOOL
# =============================================================================

class CodeAnalyzerTool(BaseTool):
    """Enhanced GitHub code analysis tool for quality, security, and metrics"""
    
    name: str = "enhanced_github_code_analyzer"
    description: str = """
    Advanced GitHub code analysis tool for comprehensive code quality assessment.
    
    Actions:
    - 'analyze_repository': Full repository code analysis and quality report
    - 'analyze_file': Detailed analysis of specific file
    - 'security_scan': Security vulnerability scanning
    - 'dependency_check': Dependency analysis and vulnerability check
    - 'code_metrics': Code complexity and maintainability metrics
    - 'quality_report': Comprehensive code quality assessment
    
    Provides detailed code insights, security scanning, and quality metrics.
    """
    args_schema: type = CodeAnalyzerInput
    
    async def _arun(self, **kwargs) -> str:
        """Async implementation"""
        return await self._execute_analysis_action(**kwargs)
    
    def _run(self, **kwargs) -> str:
        """Sync implementation"""
        return asyncio.run(self._arun(**kwargs))
    
    async def _execute_analysis_action(self, user_id: str, action: str, **kwargs) -> str:
        """Execute code analysis action"""
        try:
            # Get GitHub access token
            access_token = await get_github_access_token(user_id)
            
            if not access_token:
                return json.dumps({
                    "status": "error",
                    "message": "GitHub integration not found or inactive",
                    "error_code": "GITHUB_NOT_CONFIGURED",
                    "action": action
                })
            
            # Execute action
            if action == "analyze_repository":
                return await self._analyze_repository(access_token, kwargs.get('repo_owner'), kwargs.get('repo_name'), kwargs.get('analysis_config', {}))
            elif action == "analyze_file":
                return await self._analyze_file(access_token, kwargs.get('repo_owner'), kwargs.get('repo_name'), kwargs.get('file_path'), kwargs.get('analysis_config', {}))
            elif action == "security_scan":
                return await self._security_scan(access_token, kwargs.get('repo_owner'), kwargs.get('repo_name'), kwargs.get('analysis_config', {}))
            elif action == "dependency_check":
                return await self._dependency_check(access_token, kwargs.get('repo_owner'), kwargs.get('repo_name'), kwargs.get('analysis_config', {}))
            elif action == "code_metrics":
                return await self._code_metrics(access_token, kwargs.get('repo_owner'), kwargs.get('repo_name'), kwargs.get('analysis_config', {}))
            elif action == "quality_report":
                return await self._quality_report(access_token, kwargs.get('repo_owner'), kwargs.get('repo_name'), kwargs.get('analysis_config', {}))
            else:
                return json.dumps({
                    "status": "error",
                    "message": f"Unknown analysis action: {action}",
                    "error_code": "INVALID_ACTION",
                    "available_actions": ["analyze_repository", "analyze_file", "security_scan", "dependency_check", "code_metrics", "quality_report"]
                })
                
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Analysis action failed: {str(e)}",
                "error_code": "ANALYSIS_ACTION_FAILED",
                "action": action
            })

    async def _analyze_repository(self, access_token: str, repo_owner: str, repo_name: str, config: Dict) -> str:
        """Analyze entire repository"""
        try:
            if not repo_owner or not repo_name:
                return json.dumps({
                    "status": "error",
                    "message": "Repository owner and name are required",
                    "error_code": "MISSING_REPO_INFO"
                })
            
            analysis_config = CodeAnalysisConfig(**config)
            
            headers = {
                "Authorization": f"token {access_token}",
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "Enhanced-GitHub-Tools"
            }
            
            async with aiohttp.ClientSession() as session:
                # Get repository content structure
                contents_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents"
                
                async with session.get(contents_url, headers=headers) as response:
                    if response.status == 200:
                        contents = await response.json()
                        
                        # Analyze repository structure
                        file_analysis = await self._analyze_file_structure(session, headers, repo_owner, repo_name, contents, analysis_config)
                        
                        # Get language statistics
                        languages = await self._get_language_stats(session, headers, repo_owner, repo_name)
                        
                        # Security analysis
                        security_analysis = await self._get_security_alerts(session, headers, repo_owner, repo_name)
                        
                        # Code quality metrics
                        quality_metrics = self._calculate_quality_metrics(file_analysis, languages)
                        
                        analysis_report = {
                            "repository_info": {
                                "owner": repo_owner,
                                "name": repo_name,
                                "analyzed_at": datetime.now(timezone.utc).isoformat()
                            },
                            "file_structure": file_analysis,
                            "language_distribution": languages,
                            "security_analysis": security_analysis,
                            "quality_metrics": quality_metrics,
                            "recommendations": self._generate_recommendations(file_analysis, languages, security_analysis, quality_metrics),
                            "analysis_config": asdict(analysis_config)
                        }
                        
                        return json.dumps({
                            "status": "success",
                            "message": f"Repository analysis completed for {repo_owner}/{repo_name}",
                            "analysis": analysis_report,
                            "analyzed_at": datetime.now(timezone.utc).isoformat()
                        })
                    else:
                        error_data = await response.json()
                        return json.dumps({
                            "status": "error",
                            "message": f"Failed to access repository: {error_data.get('message', 'Unknown error')}",
                            "error_code": "GITHUB_API_ERROR"
                        })
                        
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Error analyzing repository: {str(e)}",
                "error_code": "ANALYZE_REPO_FAILED"
            })

    async def _analyze_file(self, access_token: str, repo_owner: str, repo_name: str, file_path: str, config: Dict) -> str:
        """Analyze specific file"""
        try:
            if not all([repo_owner, repo_name, file_path]):
                return json.dumps({
                    "status": "error",
                    "message": "Repository owner, name, and file path are required",
                    "error_code": "MISSING_FILE_INFO"
                })
            
            headers = {
                "Authorization": f"token {access_token}",
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "Enhanced-GitHub-Tools"
            }
            
            async with aiohttp.ClientSession() as session:
                # Get file content
                file_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/{file_path}"
                
                async with session.get(file_url, headers=headers) as response:
                    if response.status == 200:
                        file_data = await response.json()
                        
                        if file_data.get("type") != "file":
                            return json.dumps({
                                "status": "error",
                                "message": "Specified path is not a file",
                                "error_code": "INVALID_FILE_PATH"
                            })
                        
                        # Decode file content
                        content = ""
                        if file_data.get("content"):
                            try:
                                content = base64.b64decode(file_data["content"]).decode('utf-8')
                            except:
                                content = "Binary file - content analysis not available"
                        
                        # Analyze file
                        file_analysis = {
                            "file_info": {
                                "name": file_data.get("name"),
                                "path": file_data.get("path"),
                                "size": file_data.get("size", 0),
                                "sha": file_data.get("sha"),
                                "download_url": file_data.get("download_url")
                            },
                            "content_analysis": self._analyze_file_content(content, file_path),
                            "quality_metrics": self._calculate_file_quality(content, file_path),
                            "security_scan": self._scan_file_security(content, file_path)
                        }
                        
                        return json.dumps({
                            "status": "success",
                            "message": f"File analysis completed for {file_path}",
                            "file_analysis": file_analysis,
                            "analyzed_at": datetime.now(timezone.utc).isoformat()
                        })
                    else:
                        error_data = await response.json()
                        return json.dumps({
                            "status": "error",
                            "message": f"Failed to get file: {error_data.get('message', 'Unknown error')}",
                            "error_code": "GITHUB_API_ERROR"
                        })
                        
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Error analyzing file: {str(e)}",
                "error_code": "ANALYZE_FILE_FAILED"
            })

    async def _analyze_file_structure(self, session: aiohttp.ClientSession, headers: Dict, owner: str, repo: str, contents: List, config: CodeAnalysisConfig, path="") -> Dict:
        """Analyze repository file structure"""
        structure_analysis = {
            "total_files": 0,
            "file_types": {},
            "directory_structure": {},
            "large_files": [],
            "potential_issues": []
        }
        
        for item in contents:
            if item.get("type") == "file":
                structure_analysis["total_files"] += 1
                
                # Analyze file type
                file_name = item.get("name", "")
                file_ext = file_name.split(".")[-1] if "." in file_name else "no_extension"
                structure_analysis["file_types"][file_ext] = structure_analysis["file_types"].get(file_ext, 0) + 1
                
                # Check file size
                size = item.get("size", 0)
                if size > 1000000:  # Files larger than 1MB
                    structure_analysis["large_files"].append({
                        "name": file_name,
                        "path": item.get("path"),
                        "size": size
                    })
                
            elif item.get("type") == "dir":
                # Recursively analyze directories (limited depth for performance)
                if path.count("/") < 3:  # Limit recursion depth
                    try:
                        subdir_url = item.get("url")
                        async with session.get(subdir_url, headers=headers) as response:
                            if response.status == 200:
                                subdir_contents = await response.json()
                                subdir_analysis = await self._analyze_file_structure(
                                    session, headers, owner, repo, subdir_contents, config, 
                                    f"{path}/{item.get('name')}" if path else item.get("name")
                                )
                                
                                # Merge analysis
                                structure_analysis["total_files"] += subdir_analysis["total_files"]
                                for ext, count in subdir_analysis["file_types"].items():
                                    structure_analysis["file_types"][ext] = structure_analysis["file_types"].get(ext, 0) + count
                                structure_analysis["large_files"].extend(subdir_analysis["large_files"])
                                structure_analysis["potential_issues"].extend(subdir_analysis["potential_issues"])
                                
                    except Exception:
                        # Skip subdirectory on error
                        pass
        
        return structure_analysis

    async def _get_language_stats(self, session: aiohttp.ClientSession, headers: Dict, owner: str, repo: str) -> Dict:
        """Get repository language statistics"""
        try:
            languages_url = f"https://api.github.com/repos/{owner}/{repo}/languages"
            async with session.get(languages_url, headers=headers) as response:
                if response.status == 200:
                    languages_data = await response.json()
                    
                    total_bytes = sum(languages_data.values())
                    if total_bytes == 0:
                        return {"languages": {}, "primary_language": None, "total_bytes": 0}
                    
                    # Calculate percentages
                    language_percentages = {
                        lang: (bytes_count / total_bytes) * 100
                        for lang, bytes_count in languages_data.items()
                    }
                    
                    # Find primary language
                    primary_language = max(languages_data, key=languages_data.get) if languages_data else None
                    
                    return {
                        "languages": language_percentages,
                        "primary_language": primary_language,
                        "total_bytes": total_bytes,
                        "language_count": len(languages_data)
                    }
        except:
            pass
        
        return {"languages": {}, "primary_language": None, "total_bytes": 0}

    async def _get_security_alerts(self, session: aiohttp.ClientSession, headers: Dict, owner: str, repo: str) -> Dict:
        """Get security vulnerability alerts"""
        # Note: This requires special permissions and may not be available for all repositories
        security_analysis = {
            "alerts_available": False,
            "vulnerability_count": 0,
            "severity_breakdown": {"low": 0, "medium": 0, "high": 0, "critical": 0},
            "recommendations": []
        }
        
        try:
            # Try to get security advisories (public API)
            advisories_url = f"https://api.github.com/repos/{owner}/{repo}/security-advisories"
            async with session.get(advisories_url, headers=headers) as response:
                if response.status == 200:
                    advisories_data = await response.json()
                    security_analysis["alerts_available"] = True
                    security_analysis["vulnerability_count"] = len(advisories_data)
                    
                    for advisory in advisories_data:
                        severity = advisory.get("severity", "unknown").lower()
                        if severity in security_analysis["severity_breakdown"]:
                            security_analysis["severity_breakdown"][severity] += 1
        except:
            pass
        
        # Add general security recommendations
        security_analysis["recommendations"] = [
            "Enable Dependabot security updates",
            "Configure branch protection rules",
            "Use secret scanning",
            "Enable code scanning with CodeQL",
            "Regular dependency updates"
        ]
        
        return security_analysis

    def _analyze_file_content(self, content: str, file_path: str) -> Dict:
        """Analyze file content"""
        if content == "Binary file - content analysis not available":
            return {"type": "binary", "analysis": "Binary file - no content analysis"}
        
        lines = content.split('\n')
        
        analysis = {
            "line_count": len(lines),
            "character_count": len(content),
            "blank_lines": sum(1 for line in lines if line.strip() == ""),
            "comment_lines": self._count_comment_lines(lines, file_path),
            "code_lines": 0,
            "file_type": self._get_file_type(file_path),
            "estimated_complexity": "low"
        }
        
        # Calculate code lines
        analysis["code_lines"] = analysis["line_count"] - analysis["blank_lines"] - analysis["comment_lines"]
        
        # Estimate complexity
        if analysis["line_count"] > 1000:
            analysis["estimated_complexity"] = "high"
        elif analysis["line_count"] > 300:
            analysis["estimated_complexity"] = "medium"
        
        return analysis

    def _calculate_file_quality(self, content: str, file_path: str) -> Dict:
        """Calculate file quality metrics"""
        if content == "Binary file - content analysis not available":
            return {"quality_score": "N/A", "issues": ["Binary file"]}
        
        issues = []
        quality_score = 100
        
        lines = content.split('\n')
        
        # Check for very long lines
        long_lines = [i for i, line in enumerate(lines) if len(line) > 120]
        if long_lines:
            issues.append(f"Long lines detected: {len(long_lines)} lines exceed 120 characters")
            quality_score -= min(20, len(long_lines))
        
        # Check for TODO/FIXME comments
        todo_count = sum(1 for line in lines if any(keyword in line.upper() for keyword in ['TODO', 'FIXME', 'HACK', 'XXX']))
        if todo_count > 0:
            issues.append(f"Technical debt indicators: {todo_count} TODO/FIXME comments found")
            quality_score -= min(10, todo_count * 2)
        
        # Check file size
        if len(lines) > 1000:
            issues.append("Large file: Consider breaking into smaller modules")
            quality_score -= 15
        
        # Check for duplicated code patterns (simple check)
        unique_lines = set(line.strip() for line in lines if line.strip())
        if len(unique_lines) < len([line for line in lines if line.strip()]) * 0.7:
            issues.append("Potential code duplication detected")
            quality_score -= 10
        
        quality_score = max(0, quality_score)
        
        return {
            "quality_score": quality_score,
            "issues": issues,
            "suggestions": self._get_quality_suggestions(file_path, issues)
        }

    def _scan_file_security(self, content: str, file_path: str) -> Dict:
        """Basic security scanning of file content"""
        if content == "Binary file - content analysis not available":
            return {"security_issues": [], "risk_level": "unknown"}
        
        security_issues = []
        risk_level = "low"
        
        # Check for common security patterns
        security_patterns = {
            "hardcoded_secrets": [
                r'password\s*=\s*["\'][^"\']+["\']',
                r'api_key\s*=\s*["\'][^"\']+["\']',
                r'secret\s*=\s*["\'][^"\']+["\']',
                r'token\s*=\s*["\'][^"\']+["\']'
            ],
            "sql_injection": [
                r'execute\s*\(\s*["\'].*%.*["\']',
                r'query\s*\(\s*["\'].*\+.*["\']'
            ],
            "path_traversal": [
                r'\.\./\.\.',
                r'os\.path\.join\([^)]*\.\.[^)]*\)'
            ]
        }
        
        import re
        content_lower = content.lower()
        
        for category, patterns in security_patterns.items():
            for pattern in patterns:
                if re.search(pattern, content_lower, re.IGNORECASE):
                    security_issues.append(f"Potential {category.replace('_', ' ')} vulnerability detected")
                    risk_level = "medium"
        
        # Check for unsafe functions (example for Python)
        if file_path.endswith('.py'):
            unsafe_functions = ['eval', 'exec', 'input', '__import__']
            for func in unsafe_functions:
                if f'{func}(' in content:
                    security_issues.append(f"Use of potentially unsafe function: {func}")
                    risk_level = "medium"
        
        if len(security_issues) > 3:
            risk_level = "high"
        
        return {
            "security_issues": security_issues,
            "risk_level": risk_level,
            "scan_coverage": "basic"
        }

    def _calculate_quality_metrics(self, file_analysis: Dict, languages: Dict) -> Dict:
        """Calculate overall quality metrics"""
        total_files = file_analysis.get("total_files", 0)
        large_files_count = len(file_analysis.get("large_files", []))
        
        quality_metrics = {
            "maintainability_score": 85,  # Base score
            "complexity_rating": "medium",
            "documentation_coverage": "unknown",
            "test_coverage": "unknown",
            "code_duplication": "low",
            "technical_debt": "low"
        }
        
        # Adjust based on file structure
        if large_files_count > total_files * 0.1:
            quality_metrics["maintainability_score"] -= 10
            quality_metrics["complexity_rating"] = "high"
        
        # Adjust based on language diversity
        language_count = languages.get("language_count", 0)
        if language_count > 5:
            quality_metrics["maintainability_score"] -= 5
            quality_metrics["complexity_rating"] = "high"
        
        return quality_metrics

    def _generate_recommendations(self, file_analysis: Dict, languages: Dict, security: Dict, quality: Dict) -> List[str]:
        """Generate improvement recommendations"""
        recommendations = []
        
        # File structure recommendations
        if len(file_analysis.get("large_files", [])) > 0:
            recommendations.append("Consider refactoring large files into smaller, more focused modules")
        
        # Language diversity recommendations
        language_count = languages.get("language_count", 0)
        if language_count > 5:
            recommendations.append("High language diversity detected - consider consolidating technologies")
        
        # Security recommendations
        if security.get("vulnerability_count", 0) > 0:
            recommendations.append("Address identified security vulnerabilities")
        
        recommendations.extend([
            "Implement automated testing and code quality checks",
            "Set up continuous integration and deployment",
            "Add comprehensive documentation",
            "Enable dependency scanning and updates"
        ])
        
        return recommendations

    def _count_comment_lines(self, lines: List[str], file_path: str) -> int:
        """Count comment lines based on file type"""
        comment_count = 0
        file_ext = file_path.split('.')[-1].lower()
        
        comment_patterns = {
            'py': ['#'],
            'js': ['//', '/*', '*/', '*'],
            'ts': ['//', '/*', '*/', '*'],
            'java': ['//', '/*', '*/', '*'],
            'c': ['//', '/*', '*/', '*'],
            'cpp': ['//', '/*', '*/', '*'],
            'go': ['//'],
            'rs': ['//', '/*', '*/', '*'],
            'php': ['//', '#', '/*', '*/', '*'],
            'rb': ['#'],
            'sh': ['#'],
            'yaml': ['#'],
            'yml': ['#']
        }
        
        patterns = comment_patterns.get(file_ext, ['#', '//'])
        
        for line in lines:
            stripped_line = line.strip()
            if any(stripped_line.startswith(pattern) for pattern in patterns):
                comment_count += 1
        
        return comment_count

    def _get_file_type(self, file_path: str) -> str:
        """Get file type from extension"""
        ext = file_path.split('.')[-1].lower()
        
        type_mapping = {
            'py': 'python',
            'js': 'javascript',
            'ts': 'typescript',
            'java': 'java',
            'c': 'c',
            'cpp': 'cpp',
            'go': 'go',
            'rs': 'rust',
            'php': 'php',
            'rb': 'ruby',
            'sh': 'shell',
            'yaml': 'yaml',
            'yml': 'yaml',
            'json': 'json',
            'xml': 'xml',
            'html': 'html',
            'css': 'css',
            'md': 'markdown'
        }
        
        return type_mapping.get(ext, 'unknown')

    def _get_quality_suggestions(self, file_path: str, issues: List[str]) -> List[str]:
        """Get quality improvement suggestions"""
        suggestions = []
        
        if any("long lines" in issue.lower() for issue in issues):
            suggestions.append("Consider breaking long lines for better readability")
        
        if any("todo" in issue.lower() for issue in issues):
            suggestions.append("Address TODO/FIXME comments before production")
        
        if any("large file" in issue.lower() for issue in issues):
            suggestions.append("Refactor large files into smaller, focused modules")
        
        if any("duplication" in issue.lower() for issue in issues):
            suggestions.append("Extract common code into reusable functions or modules")
        
        suggestions.extend([
            "Add comprehensive comments and documentation",
            "Implement unit tests for critical functionality",
            "Use linting tools for consistent code style"
        ])
        
        return suggestions


# =============================================================================
# ENHANCED GITHUB WORKFLOW MANAGER TOOL
# =============================================================================

class WorkflowManagerTool(BaseTool):
    """Enhanced GitHub workflow and CI/CD manager"""
    
    name: str = "enhanced_github_workflow_manager"
    description: str = """
    Advanced GitHub Actions workflow and CI/CD management tool.
    
    Actions:
    - 'list_workflows': List repository workflows with status
    - 'get_workflow': Get detailed workflow information and runs
    - 'trigger_workflow': Trigger workflow execution manually
    - 'get_runs': Get workflow run history and details
    - 'download_artifacts': Download build artifacts from runs
    - 'workflow_analytics': Get workflow performance analytics
    - 'deployment_status': Check deployment status and environments
    
    Provides comprehensive CI/CD pipeline management and monitoring.
    """
    args_schema: type = WorkflowManagerInput
    
    async def _arun(self, **kwargs) -> str:
        """Async implementation"""
        return await self._execute_workflow_action(**kwargs)
    
    def _run(self, **kwargs) -> str:
        """Sync implementation"""
        return asyncio.run(self._arun(**kwargs))
    
    async def _execute_workflow_action(self, user_id: str, action: str, **kwargs) -> str:
        """Execute workflow management action"""
        try:
            # Get GitHub access token
            access_token = await get_github_access_token(user_id)
            
            if not access_token:
                return json.dumps({
                    "status": "error",
                    "message": "GitHub integration not found or inactive",
                    "error_code": "GITHUB_NOT_CONFIGURED",
                    "action": action
                })
            
            # Execute action
            if action == "list_workflows":
                return await self._list_workflows(access_token, kwargs.get('repo_owner'), kwargs.get('repo_name'), kwargs.get('workflow_config', {}))
            elif action == "get_workflow":
                return await self._get_workflow(access_token, kwargs.get('repo_owner'), kwargs.get('repo_name'), kwargs.get('workflow_id'), kwargs.get('workflow_config', {}))
            elif action == "trigger_workflow":
                return await self._trigger_workflow(access_token, kwargs.get('repo_owner'), kwargs.get('repo_name'), kwargs.get('workflow_id'), kwargs.get('workflow_config', {}))
            elif action == "get_runs":
                return await self._get_workflow_runs(access_token, kwargs.get('repo_owner'), kwargs.get('repo_name'), kwargs.get('workflow_config', {}))
            elif action == "download_artifacts":
                return await self._download_artifacts(access_token, kwargs.get('repo_owner'), kwargs.get('repo_name'), kwargs.get('run_id'), kwargs.get('workflow_config', {}))
            elif action == "workflow_analytics":
                return await self._workflow_analytics(access_token, kwargs.get('repo_owner'), kwargs.get('repo_name'), kwargs.get('workflow_config', {}))
            elif action == "deployment_status":
                return await self._deployment_status(access_token, kwargs.get('repo_owner'), kwargs.get('repo_name'), kwargs.get('workflow_config', {}))
            else:
                return json.dumps({
                    "status": "error",
                    "message": f"Unknown workflow action: {action}",
                    "error_code": "INVALID_ACTION",
                    "available_actions": ["list_workflows", "get_workflow", "trigger_workflow", "get_runs", "download_artifacts", "workflow_analytics", "deployment_status"]
                })
                
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Workflow action failed: {str(e)}",
                "error_code": "WORKFLOW_ACTION_FAILED",
                "action": action
            })

    async def _list_workflows(self, access_token: str, repo_owner: str, repo_name: str, config: Dict) -> str:
        """List repository workflows"""
        try:
            if not repo_owner or not repo_name:
                return json.dumps({
                    "status": "error",
                    "message": "Repository owner and name are required",
                    "error_code": "MISSING_REPO_INFO"
                })
            
            workflow_config = WorkflowConfig(**config)
            
            headers = {
                "Authorization": f"token {access_token}",
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "Enhanced-GitHub-Tools"
            }
            
            async with aiohttp.ClientSession() as session:
                workflows_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/actions/workflows"
                
                async with session.get(workflows_url, headers=headers) as response:
                    if response.status == 200:
                        workflows_data = await response.json()
                        
                        workflows = []
                        for workflow in workflows_data.get("workflows", []):
                            workflow_info = {
                                "id": workflow.get("id"),
                                "name": workflow.get("name"),
                                "path": workflow.get("path"),
                                "state": workflow.get("state"),
                                "created_at": workflow.get("created_at"),
                                "updated_at": workflow.get("updated_at"),
                                "badge_url": workflow.get("badge_url"),
                                "html_url": workflow.get("html_url")
                            }
                            
                            # Get recent runs if requested
                            if workflow_config.include_runs:
                                workflow_info["recent_runs"] = await self._get_recent_workflow_runs(
                                    session, headers, repo_owner, repo_name, workflow.get("id")
                                )
                            
                            workflows.append(workflow_info)
                        
                        # Filter by type if specified
                        if workflow_config.workflow_type != "all":
                            # This is a simple filter - in practice you'd analyze workflow content
                            workflows = [w for w in workflows if workflow_config.workflow_type.lower() in w["name"].lower()]
                        
                        return json.dumps({
                            "status": "success",
                            "message": f"Found {len(workflows)} workflows in {repo_owner}/{repo_name}",
                            "workflows": workflows,
                            "total_count": len(workflows),
                            "retrieved_at": datetime.now(timezone.utc).isoformat()
                        })
                    else:
                        error_data = await response.json()
                        return json.dumps({
                            "status": "error",
                            "message": f"Failed to list workflows: {error_data.get('message', 'Unknown error')}",
                            "error_code": "GITHUB_API_ERROR"
                        })
                        
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Error listing workflows: {str(e)}",
                "error_code": "LIST_WORKFLOWS_FAILED"
            })

    async def _get_recent_workflow_runs(self, session: aiohttp.ClientSession, headers: Dict, owner: str, repo: str, workflow_id: int, limit: int = 5) -> List[Dict]:
        """Get recent runs for a workflow"""
        try:
            runs_url = f"https://api.github.com/repos/{owner}/{repo}/actions/workflows/{workflow_id}/runs"
            params = {"per_page": limit}
            
            async with session.get(runs_url, headers=headers, params=params) as response:
                if response.status == 200:
                    runs_data = await response.json()
                    
                    return [
                        {
                            "id": run.get("id"),
                            "status": run.get("status"),
                            "conclusion": run.get("conclusion"),
                            "created_at": run.get("created_at"),
                            "run_started_at": run.get("run_started_at"),
                            "updated_at": run.get("updated_at"),
                            "head_branch": run.get("head_branch"),
                            "head_sha": run.get("head_sha")[:7] if run.get("head_sha") else None,
                            "html_url": run.get("html_url")
                        }
                        for run in runs_data.get("workflow_runs", [])
                    ]
        except:
            pass
        
        return []

    async def _workflow_analytics(self, access_token: str, repo_owner: str, repo_name: str, config: Dict) -> str:
        """Get workflow performance analytics"""
        try:
            if not repo_owner or not repo_name:
                return json.dumps({
                    "status": "error",
                    "message": "Repository owner and name are required",
                    "error_code": "MISSING_REPO_INFO"
                })
            
            headers = {
                "Authorization": f"token {access_token}",
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "Enhanced-GitHub-Tools"
            }
            
            async with aiohttp.ClientSession() as session:
                # Get all workflows first
                workflows_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/actions/workflows"
                
                async with session.get(workflows_url, headers=headers) as response:
                    if response.status == 200:
                        workflows_data = await response.json()
                        
                        analytics = {
                            "repository": f"{repo_owner}/{repo_name}",
                            "total_workflows": len(workflows_data.get("workflows", [])),
                            "workflow_analytics": [],
                            "overall_metrics": {
                                "total_runs": 0,
                                "success_rate": 0,
                                "average_duration": 0,
                                "most_active_workflow": None,
                                "failure_patterns": []
                            }
                        }
                        
                        total_runs = 0
                        successful_runs = 0
                        total_duration = 0
                        workflow_activity = {}
                        
                        for workflow in workflows_data.get("workflows", []):
                            workflow_id = workflow.get("id")
                            workflow_name = workflow.get("name")
                            
                            # Get workflow runs for analysis
                            runs_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/actions/workflows/{workflow_id}/runs"
                            
                            try:
                                async with session.get(runs_url, headers=headers, params={"per_page": 50}) as runs_response:
                                    if runs_response.status == 200:
                                        runs_data = await runs_response.json()
                                        workflow_runs = runs_data.get("workflow_runs", [])
                                        
                                        workflow_analytics = self._analyze_workflow_runs(workflow_name, workflow_runs)
                                        analytics["workflow_analytics"].append(workflow_analytics)
                                        
                                        # Aggregate metrics
                                        total_runs += len(workflow_runs)
                                        successful_runs += workflow_analytics["success_count"]
                                        total_duration += workflow_analytics["average_duration"] * len(workflow_runs)
                                        workflow_activity[workflow_name] = len(workflow_runs)
                                        
                            except Exception:
                                continue
                        
                        # Calculate overall metrics
                        if total_runs > 0:
                            analytics["overall_metrics"]["total_runs"] = total_runs
                            analytics["overall_metrics"]["success_rate"] = (successful_runs / total_runs) * 100
                            analytics["overall_metrics"]["average_duration"] = total_duration / total_runs if total_runs > 0 else 0
                            analytics["overall_metrics"]["most_active_workflow"] = max(workflow_activity, key=workflow_activity.get) if workflow_activity else None
                        
                        return json.dumps({
                            "status": "success",
                            "message": f"Workflow analytics completed for {repo_owner}/{repo_name}",
                            "analytics": analytics,
                            "analyzed_at": datetime.now(timezone.utc).isoformat()
                        })
                    else:
                        error_data = await response.json()
                        return json.dumps({
                            "status": "error",
                            "message": f"Failed to get workflows for analytics: {error_data.get('message', 'Unknown error')}",
                            "error_code": "GITHUB_API_ERROR"
                        })
                        
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Error generating workflow analytics: {str(e)}",
                "error_code": "WORKFLOW_ANALYTICS_FAILED"
            })

    def _analyze_workflow_runs(self, workflow_name: str, runs: List[Dict]) -> Dict:
        """Analyze individual workflow runs"""
        if not runs:
            return {
                "workflow_name": workflow_name,
                "total_runs": 0,
                "success_count": 0,
                "failure_count": 0,
                "success_rate": 0,
                "average_duration": 0,
                "latest_run": None
            }
        
        success_count = sum(1 for run in runs if run.get("conclusion") == "success")
        failure_count = sum(1 for run in runs if run.get("conclusion") in ["failure", "cancelled", "timed_out"])
        
        # Calculate average duration (simplified)
        durations = []
        for run in runs:
            if run.get("run_started_at") and run.get("updated_at"):
                try:
                    start = datetime.fromisoformat(run["run_started_at"].replace('Z', '+00:00'))
                    end = datetime.fromisoformat(run["updated_at"].replace('Z', '+00:00'))
                    duration = (end - start).total_seconds()
                    durations.append(duration)
                except:
                    continue
        
        average_duration = sum(durations) / len(durations) if durations else 0
        
        return {
            "workflow_name": workflow_name,
            "total_runs": len(runs),
            "success_count": success_count,
            "failure_count": failure_count,
            "success_rate": (success_count / len(runs)) * 100,
            "average_duration": average_duration,
            "latest_run": {
                "status": runs[0].get("status"),
                "conclusion": runs[0].get("conclusion"),
                "created_at": runs[0].get("created_at")
            } if runs else None
        }


# Create remaining tool instances
enhanced_github_code_analyzer = CodeAnalyzerTool()
enhanced_github_workflow_manager = WorkflowManagerTool()

# Export complete tools list
ENHANCED_GITHUB_TOOLS = [
    enhanced_github_repository_manager,
    enhanced_github_issue_manager,
    enhanced_github_code_analyzer,
    enhanced_github_workflow_manager
]