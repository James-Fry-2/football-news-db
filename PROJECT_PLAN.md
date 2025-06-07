# FOOTBALL NEWS LLM PROJECT - COMPLETE CONTEXT PLAN

## PROJECT OVERVIEW
**Goal**: Transform existing football news database into AI-powered analytics platform  
**Timeline**: 8 weeks (solo development with Cursor)  
**Current Status**: Foundation complete, adding LLM capabilities  
**Budget**: £100-200/month operating costs  

---

## CURRENT CODEBASE STATUS ✅

### Already Built:
- **Database**: PostgreSQL with Articles, Players, Teams, relationships
- **Crawlers**: BBC Sport + Fantasy Football Scout working
- **API**: FastAPI with CRUD endpoints for articles/players
- **Infrastructure**: Docker setup, CI/CD, basic deployment
- **ETL Pipeline**: Article processing with entity extraction

### Architecture:
```
src/
├── api/routes/          # FastAPI endpoints
├── crawlers/           # BBC, FFS news crawlers  
├── db/models/          # SQLAlchemy models
├── db/services/        # Database services
├── config.py           # Configuration
└── main.py            # FastAPI app
```

---

## IMPLEMENTATION PHASES

### 🎯 PHASE 1: Vector Database Integration (Week 1)
**Goal**: Add semantic search to existing articles

#### Week 1 Tasks:
- **Day 1**: Database schema enhancement + migration
- **Day 2**: Pinecone setup + VectorService creation  
- **Day 3**: Article embedding pipeline
- **Day 4**: Semantic search API endpoints
- **Day 5**: Background embedding tasks

**Deliverables**:
- [ ] Vector fields added to Article model
- [ ] Pinecone index with article embeddings  
- [ ] `/semantic-search` API endpoint working
- [ ] Background embedding via Celery

**Dependencies**: OpenAI API key, Pinecone account

---

### 🤖 PHASE 2: LLM Chat System (Week 2)
**Goal**: Build conversational AI for football analysis

#### Week 2 Tasks:
- **Day 1**: LangChain + OpenAI integration
- **Day 2**: Custom football analysis tools
- **Day 3**: WebSocket chat endpoints
- **Day 4**: Conversation management (Redis)
- **Day 5**: Streaming responses + context

**Deliverables**:
- [ ] LLMService with football tools
- [ ] Real-time WebSocket chat
- [ ] Conversation persistence
- [ ] Context-aware responses

**Key Files to Create**:
- `src/services/llm_service.py`
- `src/api/routes/chat.py` 
- `src/llm/tools/football_tools.py`

---

### 🎨 PHASE 3: Frontend Chat Interface (Week 3)
**Goal**: User-friendly chat interface

#### Week 3 Tasks:
- **Day 1-2**: React chat component with WebSockets
- **Day 3**: Chart generation for LLM responses
- **Day 4**: User authentication + sessions
- **Day 5**: Mobile responsive design

**Deliverables**:
- [ ] React chat interface
- [ ] Real-time message streaming
- [ ] Dynamic chart generation
- [ ] User management system

---

### 🚀 PHASE 4: Advanced Features (Week 4)
**Goal**: Production-ready with advanced analytics

#### Week 4 Tasks:
- **Day 1**: External API integration (live data)
- **Day 2**: Advanced correlation analysis
- **Day 3**: FPL integration + recommendations
- **Day 4**: Performance optimization
- **Day 5**: Testing + deployment

**Deliverables**:
- [ ] Live player statistics
- [ ] News-performance correlation
- [ ] FPL strategy recommendations
- [ ] Production deployment

---

## TECHNOLOGY STACK

### Current Stack:
- **Backend**: FastAPI + PostgreSQL + Redis
- **Crawlers**: BeautifulSoup + Selenium  
- **Infrastructure**: Docker + GitHub Actions
- **Database**: SQLAlchemy + Alembic migrations

### Adding:
- **LLM**: OpenAI GPT-4 + LangChain
- **Vector DB**: Pinecone (cloud) or Weaviate (self-hosted)
- **Frontend**: React + TypeScript + Tailwind CSS
- **Real-time**: WebSockets + Redis pub/sub
- **Charts**: Chart.js or Recharts

---

## CURSOR WORKFLOW STRATEGY

### Daily Development Pattern:
1. **Morning Planning** (15 mins): Review progress, plan today's tasks
2. **Development Sessions** (2-3 hours): Use specific Cursor prompts
3. **Testing & Iteration** (30 mins): Test features, fix issues
4. **End-of-day Review** (15 mins): Document progress, plan tomorrow

### Key Cursor Commands:
- **`Ctrl+K`**: Generate specific components/functions
- **`Ctrl+L`**: Debug and explain issues
- **`@filename`**: Reference specific files in prompts
- **Chat**: Architecture planning and explanations

---

## PHASE-SPECIFIC CURSOR PROMPTS

### Phase 1: Vector Database
```bash
# Database Enhancement
@src/db/models/article.py "Add vector fields: embedding_status, search_vector_id, sentiment_score, content_hash"

# Service Creation  
"Create VectorService class with Pinecone integration, OpenAI embeddings, and batch processing"

# API Enhancement
@src/api/routes/articles.py "Add semantic search endpoints that use VectorService"
```

### Phase 2: LLM Integration
```bash
# LLM Service
"Create LLMService with LangChain, custom football tools, and conversation management"

# Chat Endpoints
@src/api/routes/ "Add WebSocket chat endpoints with real-time streaming"

# Custom Tools
"Create LangChain tools: PlayerStatsTool, NewsSearchTool, FPLCalculatorTool"
```

### Phase 3: Frontend
```bash
# React Components
"Create React chat interface with WebSocket integration and message streaming"

# Chart Generation
"Build chart components that render player performance data from LLM responses"

# User Interface
"Create responsive chat UI with message history and typing indicators"
```

### Phase 4: Advanced Features
```bash
# External APIs
@src/services/ "Create external API service for live player statistics"

# Analytics
"Build correlation analysis between news sentiment and player performance"

# FPL Integration
"Create FPL recommendation engine using player stats and fixtures"
```

---

## BUDGET & COST TRACKING

### Monthly Operating Costs:
- **OpenAI API**: $100-200 (main cost)
- **Pinecone**: $70 (vector database)
- **Hosting**: $50-100 (additional services)
- **External APIs**: $50-100 (football data)
- **Total**: $270-470/month

### Cost Optimization:
- Aggressive LLM response caching (70% cost reduction)
- Smart rate limiting (50 queries/day free tier)
- Efficient prompt engineering
- Background processing to avoid timeouts

---

## RISK MANAGEMENT

### High-Risk Items:
1. **LLM API Costs** → Implement caching + rate limiting
2. **External API Changes** → Build adapter pattern + fallbacks  
3. **Performance Issues** → Load testing + optimization
4. **Scope Creep** → Stick to MVP, iterate later

### Mitigation Strategies:
- Daily cost monitoring dashboard
- Multiple API provider fallbacks
- Progressive feature rollout
- Regular performance benchmarking

---

## SUCCESS METRICS

### Phase 1 Success:
- [ ] 1000+ articles embedded in Pinecone
- [ ] Semantic search returns relevant results
- [ ] API response time <500ms

### Phase 2 Success:
- [ ] Basic chat working with football analysis
- [ ] 3+ custom analysis tools functional
- [ ] WebSocket connections stable

### Phase 3 Success:
- [ ] Chat interface works on mobile + desktop
- [ ] Real-time message streaming
- [ ] User authentication working

### Phase 4 Success:
- [ ] Live data integration working
- [ ] FPL recommendations accurate
- [ ] Production deployment stable

### Launch Success (Week 8):
- [ ] 100+ beta users signed up
- [ ] 5+ conversations per user average
- [ ] Sub-2 second response times
- [ ] 95%+ uptime
- [ ] Positive user feedback

---

## CURRENT PRIORITIES (UPDATE DAILY)

### This Week Focus: Vector Database Integration

#### Today's Status: [UPDATE DAILY]
**Date**: 2025-06-04
**Current Task**: Modify article models to use vectors

**Completed Today**:
- [ x ] Add vector storage
- [ x ] Split docker containers into 3 separate containers, to separate app llm and web crawlers 
- [ x ] Create vector service to add vectors to the scraped articles

**Date**: 2025-06-05
**Current Task**: Test uploading articles through pipeline

**Completed Today**:
- [ x ] Added team names + players to database using script scraping from 
- [ ] Test Crawler pipeline
- [ ] 

**Date**: 2025-06-06
**Current Task**: Test uploading articles through pipeline

**Completed Today**:
- [ ] Test Crawler pipeline
- [ ] Complete setup of Pinecone

**Blockers**:
- 

**Tomorrow's Priority**:
- Complete setup of Pinecone
- Complete setup of Open API 
- Test Crawler pipeline at larger scale - 1000 articles + 5 crawlers 


#### This Week's Progress:
- [ ] **Day 1**: Database schema + migration
- [ ] **Day 2**: Pinecone setup + VectorService  
- [ ] **Day 3**: Article embedding pipeline
- [ ] **Day 4**: Semantic search endpoints
- [ ] **Day 5**: Background tasks + testing

---

## QUICK REFERENCE

### Essential Commands:
```bash
# Development
docker-compose up -d          # Start local environment
alembic upgrade head          # Run migrations
pytest tests/                # Run tests

# Vector Database
python scripts/setup-pinecone.py    # Initialize Pinecone
python scripts/batch-embed.py       # Embed existing articles

# Deployment
docker build -t football-llm .      # Build image
git push origin main                # Trigger CI/CD
```

### Key Files:
- **Config**: `src/config.py`
- **Main App**: `src/main.py`
- **Database**: `src/db/models/article.py`
- **API**: `src/api/routes/articles.py`
- **Docker**: `docker-compose.yml`

### Environment Variables Needed:
```bash
OPENAI_API_KEY=sk-...
PINECONE_API_KEY=...
PINECONE_ENV=us-east1-gcp
DATABASE_URL=postgresql://...
REDIS_URL=redis://localhost:6379
```

---

## DAILY STANDUP TEMPLATE

**Yesterday**: What did I complete?
**Today**: What will I work on?  
**Blockers**: What's preventing progress?
**Focus**: What's the most important task?

---

## NEXT ACTIONS

When you ask "What should I do today?", reference:
1. **Current Phase** (Week X focus)
2. **Today's Specific Tasks** from current week
3. **Yesterday's Progress** and any blockers
4. **Cursor Prompts** ready to use
5. **Success Criteria** for today's work

Update the "Current Priorities" section daily to track progress and maintain momentum.