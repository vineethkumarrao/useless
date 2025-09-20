# Useless Chatbot AI

A full-stack AI-powered chatbot application built with Next.js frontend and FastAPI backend, featuring advanced AI agents powered by CrewAI and Google's Gemini AI for intelligent research, analysis, and writing tasks.

## 🚀 Features

### Frontend (Next.js)
- **Modern UI/UX**: Built with React 19, Next.js 15, and Tailwind CSS
- **Authentication**: Secure user authentication with Supabase and NextAuth
- **Responsive Design**: Mobile-first design with beautiful components
- **Real-time Chat**: Interactive chat interface with AI agents
- **Dashboard**: User dashboard for managing conversations and settings
- **Component Library**: Radix UI components with custom styling

### Backend (FastAPI)
- **AI-Powered Agents**: CrewAI agents specialized in:
  - Research and web searching (Tavily API integration)
  - Content analysis and writing
  - Data processing and insights
- **Multiple LLM Support**: 
  - Google Gemini 2.5 Flash (primary)
  - OpenRouter integration for various models
- **Authentication Service**: JWT-based auth with OTP verification
- **RESTful API**: Clean API endpoints for chat and user management
- **Real-time Processing**: Async processing for AI agent tasks

### AI Capabilities
- **Web Search Integration**: Real-time web search using Tavily API
- **Multi-Agent System**: Specialized agents for different types of tasks
- **LangChain Tools**: Extended functionality with LangChain integrations
- **Smart Routing**: Intelligent query routing to appropriate agents

### 🚀 **NEW: Enhanced Productivity Tools (20 Tools Across 5 Platforms)**
Our latest major update introduces **20 sophisticated enhanced tools** with intelligent routing for maximum productivity:

#### **📧 Gmail Enhanced Tools (4 Tools)**
- **GmailEnhancedReadTool**: Advanced email reading with smart filtering by sender, subject, date ranges, labels, and more
- **GmailBulkOperationTool**: Batch email operations including bulk labeling, archiving, deleting, and organization
- **GmailLabelManagementTool**: Intelligent label creation, management, and automated categorization
- **GmailSmartFeaturesTool**: Advanced analytics, email insights, and smart automation features

#### **📅 Calendar Enhanced Tools (4 Tools)**
- **CalendarAvailabilityFinderTool**: Smart availability detection across multiple calendars with conflict resolution
- **CalendarSmartSchedulerTool**: AI-powered optimal meeting scheduling with preference learning
- **CalendarRecurringEventTool**: Advanced recurring event management with complex patterns
- **CalendarAnalyticsTool**: Meeting analytics, productivity insights, and time management optimization

#### **📄 Google Docs Enhanced Tools (4 Tools)**
- **DocumentReaderTool**: Advanced document analysis with content extraction and summarization
- **DocumentEditorTool**: Intelligent document editing with AI-assisted writing and formatting
- **DocumentCollaboratorTool**: Enhanced collaboration features with permission management and sharing
- **DocumentAnalyzerTool**: Deep content analysis, readability scoring, and document insights

#### **📝 Notion Enhanced Tools (4 Tools)**
- **DatabaseManagerTool**: Advanced database operations with intelligent querying and data analysis
- **PageManagerTool**: Smart page creation, editing, and organization with template management
- **ContentAnalyzerTool**: Content analysis across pages with insights and knowledge extraction
- **WorkspaceIntelligenceTool**: Workspace-wide analytics and intelligent organization recommendations

#### **📂 GitHub Enhanced Tools (4 Tools)**  
- **RepositoryManagerTool**: Advanced repo analysis with code statistics and health metrics
- **IssueManagerTool**: Intelligent issue management with automated labeling and priority scoring
- **CodeAnalyzerTool**: Deep code analysis with quality metrics and improvement suggestions
- **WorkflowManagerTool**: CI/CD workflow optimization with performance analytics and recommendations

#### **🧠 Intelligent Tool Routing**
The system automatically selects between basic tools (quick operations) and enhanced tools (complex analysis) based on:
- **Query Complexity**: Keywords like "analyze", "optimize", "batch", "insights" trigger enhanced tools
- **Context Richness**: Rich user context automatically upgrades to enhanced capabilities
- **Task Requirements**: Multi-step operations and advanced features route to enhanced tools
- **Graceful Fallback**: Seamless fallback to basic tools when enhanced tools are unavailable

#### **✨ Enhanced Tool Benefits**
- **10x More Capable**: Each enhanced tool provides 10+ advanced features vs basic equivalents
- **AI-Powered Insights**: Built-in analytics and intelligence for every platform
- **Batch Operations**: Process multiple items simultaneously for maximum efficiency
- **Smart Automation**: Learn user patterns and provide intelligent recommendations
- **Phase 2 Compatible**: Full structured JSON responses for future integrations

## 🛠️ Tech Stack

### Frontend
- **Framework**: Next.js 15.5.3 with Turbopack
- **Runtime**: React 19.1.0
- **Styling**: Tailwind CSS 4
- **UI Components**: Radix UI primitives
- **Icons**: Lucide React, Remix Icons
- **Authentication**: NextAuth.js with Supabase adapter
- **Forms**: React Hook Form with Zod validation
- **HTTP Client**: Axios

### Backend
- **Framework**: FastAPI 0.104.1
- **Server**: Uvicorn with async support
- **AI Framework**: CrewAI 0.186.1
- **LLM Integration**: LangChain with Google Gemini
- **Web Search**: Tavily API
- **Environment**: Python-dotenv for configuration
- **HTTP Client**: httpx for async requests

### Database & Services
- **Database**: Supabase (PostgreSQL)
- **Authentication**: Supabase Auth
- **Web Search**: Tavily API
- **AI Models**: Google Gemini, OpenRouter models

## 📋 Prerequisites

Before running this project, make sure you have:

- **Node.js** (v18.0.0 or higher)
- **Python** (v3.9 or higher)
- **pnpm** (recommended) or npm
- **Git**

## 🔑 Environment Variables

You'll need to set up the following environment variables:

### Frontend (.env.local)
```env
# Supabase Configuration
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key

# NextAuth Configuration
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=your_nextauth_secret

# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Backend (python-backend/.env)
```env
# Google AI Configuration
GOOGLE_API_KEY=your_google_gemini_api_key

# Tavily Search API
TAVILY_API_KEY=your_tavily_api_key

# OpenRouter (Optional)
OPENROUTER_API_KEY=your_openrouter_api_key

# Database Configuration
DATABASE_URL=your_database_url

# JWT Configuration
JWT_SECRET_KEY=your_jwt_secret_key
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Email Configuration (for OTP)
SMTP_SERVER=your_smtp_server
SMTP_PORT=587
SMTP_USERNAME=your_smtp_username
SMTP_PASSWORD=your_smtp_password
FROM_EMAIL=your_from_email

# CORS Configuration
ALLOWED_ORIGINS=http://localhost:3000,https://yourdomain.com
```

## 🚀 Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/vineethkumarrao/useless.git
cd useless
```

### 2. Frontend Setup
```bash
# Install dependencies
pnpm install

# Create environment file
cp .env.example .env.local
# Edit .env.local with your configuration

# Run development server
pnpm dev
```

The frontend will be available at `http://localhost:3000`

### 3. Backend Setup
```bash
# Navigate to backend directory
cd python-backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
.\venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env
# Edit .env with your configuration

# Setup database (if needed)
python setup_database.py

# Run the server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The backend API will be available at `http://localhost:8000`

## 🎯 Usage

### Running the Full Application

1. **Start the Backend Server**:
   ```bash
   cd python-backend
   .\venv\Scripts\activate  # Windows
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

2. **Start the Frontend Development Server**:
   ```bash
   pnpm dev
   ```

3. **Access the Application**:
   - Frontend: `http://localhost:3000`
   - Backend API: `http://localhost:8000`
   - API Documentation: `http://localhost:8000/docs`

### Using VS Code Tasks

This project includes VS Code tasks for easy development:

1. **Start Frontend**: Run "dev" task
2. **Start Backend**: Run "Start Python FastAPI Backend" task
3. **Build Project**: Run "build" task

### 💡 Enhanced Tools Usage Examples

#### **Simple Queries (Basic Tools)**
```
"Show my recent emails"                    → Gmail basic read tool
"List my repositories"                     → GitHub basic list tool  
"What's on my calendar today?"             → Calendar basic events tool
```

#### **Complex Queries (Enhanced Tools)**
```
"Analyze my email patterns and give insights"        → Gmail Analytics Tool
"Optimize my calendar schedule for next week"        → Calendar Smart Scheduler
"Batch organize all project-related emails"          → Gmail Bulk Operations
"Analyze code quality across my repositories"        → GitHub Code Analyzer
"Give me workspace intelligence about my Notion"     → Notion Workspace Intelligence
```

#### **Advanced Examples**
```
# Gmail Enhanced Features
"Filter emails from last month by project labels and analyze trends"
"Bulk archive all newsletters and create smart filters for future"
"Generate email analytics report showing productivity patterns"

# Calendar Enhanced Features  
"Find optimal meeting times avoiding conflicts across 3 calendars"
"Analyze my meeting patterns and suggest productivity improvements"
"Create recurring project review meetings with intelligent scheduling"

# GitHub Enhanced Features
"Analyze repository health and code quality metrics"
"Manage issues with automated labeling and priority scoring" 
"Optimize CI/CD workflows based on performance analytics"

# Multi-Platform Intelligence
"Analyze productivity across Gmail, Calendar, and GitHub"
"Coordinate project tracking between Notion and GitHub issues"
"Optimize document workflow between Google Docs and Notion"
```

## 📚 API Documentation

### Authentication Endpoints
- `POST /signup` - User registration
- `POST /verify-otp` - OTP verification
- `POST /login` - User login
- `POST /logout` - User logout

### Chat Endpoints
- `POST /chat` - Send message to AI agents
- `GET /chat/history` - Get chat history
- `DELETE /chat/clear` - Clear chat history

### User Endpoints
- `GET /user/profile` - Get user profile
- `PUT /user/profile` - Update user profile

### Health Check
- `GET /health` - API health status

## 🤖 AI Agents

The application features specialized AI agents:

### Research Agent
- Performs web searches using Tavily API
- Gathers information from reliable sources
- Provides source URLs and verification

### Analysis Agent
- Analyzes data and content
- Provides insights and summaries
- Processes complex information

### Writing Agent
- Creates well-structured content
- Formats responses appropriately
- Maintains consistent tone and style

## 🔧 Configuration

### Frontend Configuration
- **Next.js Config**: `next.config.ts`
- **Tailwind Config**: `postcss.config.mjs`
- **TypeScript Config**: `tsconfig.json`
- **ESLint Config**: `eslint.config.mjs`

### Backend Configuration
- **Requirements**: `python-backend/requirements.txt`
- **Environment**: `python-backend/.env`
- **Database Schema**: `database-schema.sql`

## 📱 Development

### Frontend Development
```bash
# Start development server with turbopack
pnpm dev

# Build for production
pnpm build

# Start production server
pnpm start

# Lint code
pnpm lint
```

### Backend Development
```bash
# Run with auto-reload
uvicorn main:app --reload

# Run tests (if available)
python -m pytest

# Check code formatting
black .

# Type checking
mypy .
```

## 🚀 Deployment

### Frontend Deployment (Vercel)
1. Connect your GitHub repository to Vercel
2. Set environment variables in Vercel dashboard
3. Deploy automatically on push to main branch

### Backend Deployment
1. **Railway/Render**: Use the provided `requirements.txt`
2. **Docker**: Create Dockerfile for containerized deployment
3. **VPS**: Use systemd service or PM2 for process management

### Environment Variables for Production
Ensure all environment variables are properly set in your production environment.

## 🧪 Testing

### Testing API Endpoints
Use the provided test files:
- `python-backend/test_gemini_key.py` - Test Gemini API integration
- `python-backend/test_openrouter.py` - Test OpenRouter integration
- `python-backend/test_crew_gemini.py` - Test CrewAI agents

### Frontend Testing
```bash
# Run component tests (if configured)
pnpm test

# Run E2E tests (if configured)
pnpm test:e2e
```

## 🛠️ Troubleshooting

### Common Issues

1. **API Key Errors**: Ensure all API keys are correctly set in environment files
2. **CORS Issues**: Check `ALLOWED_ORIGINS` in backend environment
3. **Database Connection**: Verify Supabase URL and keys
4. **Python Environment**: Make sure virtual environment is activated
5. **Port Conflicts**: Check if ports 3000 and 8000 are available

### Debugging
- Check browser console for frontend errors
- Check FastAPI logs for backend errors
- Use `/docs` endpoint to test API directly
- Verify environment variables are loaded correctly

## 📖 Additional Resources

### Documentation
- [Next.js Documentation](https://nextjs.org/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [CrewAI Documentation](https://docs.crewai.com/)
- [Supabase Documentation](https://supabase.com/docs)

### APIs Used
- [Google Gemini AI](https://ai.google.dev/)
- [Tavily Search API](https://tavily.com/)
- [OpenRouter](https://openrouter.ai/)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Authors

- **Vineeth Kumar Rao** - Initial work - [vineethkumarrao](https://github.com/vineethkumarrao)

## 🙏 Acknowledgments

- Google for Gemini AI API
- CrewAI team for the amazing framework
- Vercel for hosting platform
- Supabase for backend services
- The open-source community for amazing tools and libraries

---

**Note**: This project is for educational and demonstration purposes. Make sure to follow the terms of service for all APIs used.
