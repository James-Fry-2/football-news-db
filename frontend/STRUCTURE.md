# Frontend Directory Structure

This document provides a complete overview of the React TypeScript frontend structure for the Football News Database.

## 📁 Complete Directory Structure

```
frontend/
├── public/                          # Static assets
│   ├── football.svg                 # App icon
│   └── vite.svg                     # Vite logo
├── src/
│   ├── components/                  # React components
│   │   ├── ui/                      # Base UI components
│   │   │   ├── Button.tsx           # Reusable button component
│   │   │   ├── Input.tsx            # Form input component
│   │   │   ├── Card.tsx             # Card container component
│   │   │   ├── Badge.tsx            # Status badges
│   │   │   ├── Avatar.tsx           # User avatar
│   │   │   ├── Skeleton.tsx         # Loading placeholders
│   │   │   ├── Dialog.tsx           # Modal dialogs
│   │   │   ├── Dropdown.tsx         # Dropdown menus
│   │   │   ├── Tabs.tsx             # Tab navigation
│   │   │   ├── Progress.tsx         # Progress bars
│   │   │   └── index.ts             # Export all UI components
│   │   ├── features/                # Feature-specific components
│   │   │   ├── articles/            # Article-related components
│   │   │   │   ├── ArticleCard.tsx
│   │   │   │   ├── ArticleList.tsx
│   │   │   │   ├── ArticleForm.tsx
│   │   │   │   └── ArticleFilters.tsx
│   │   │   ├── search/              # Search components
│   │   │   │   ├── SearchForm.tsx
│   │   │   │   ├── SearchResults.tsx
│   │   │   │   ├── SearchFilters.tsx
│   │   │   │   └── SearchSuggestions.tsx
│   │   │   ├── chat/                # Chat components
│   │   │   │   ├── ChatMessage.tsx
│   │   │   │   ├── ChatInput.tsx
│   │   │   │   ├── ChatHistory.tsx
│   │   │   │   ├── ConversationList.tsx
│   │   │   │   └── MessageFeedback.tsx
│   │   │   ├── analytics/           # Analytics components
│   │   │   │   ├── StatsCards.tsx
│   │   │   │   ├── ChartsGrid.tsx
│   │   │   │   ├── SourceChart.tsx
│   │   │   │   └── TrendChart.tsx
│   │   │   ├── players/             # Player components
│   │   │   │   ├── PlayerCard.tsx
│   │   │   │   ├── PlayerList.tsx
│   │   │   │   └── PlayerForm.tsx
│   │   │   └── admin/               # Admin components
│   │   │       ├── RateLimitStats.tsx
│   │   │       ├── UserTierForm.tsx
│   │   │       └── AdminDashboard.tsx
│   │   ├── layout/                  # Layout components
│   │   │   ├── Header.tsx           # Main header with navigation
│   │   │   ├── Sidebar.tsx          # Navigation sidebar
│   │   │   ├── Footer.tsx           # Footer component
│   │   │   ├── Navigation.tsx       # Navigation component
│   │   │   └── MobileMenu.tsx       # Mobile navigation
│   │   └── Layout.tsx               # Main layout wrapper
│   ├── pages/                       # Page components
│   │   ├── HomePage.tsx             # Landing page
│   │   ├── ArticlesPage.tsx         # Articles listing page
│   │   ├── ArticlePage.tsx          # Individual article page
│   │   ├── SearchPage.tsx           # Search interface page
│   │   ├── ChatPage.tsx             # Chat interface page
│   │   ├── AnalyticsPage.tsx        # Analytics dashboard
│   │   ├── AdminPage.tsx            # Admin panel
│   │   ├── PlayersPage.tsx          # Players management
│   │   ├── NotFoundPage.tsx         # 404 error page
│   │   └── ErrorPage.tsx            # General error page
│   ├── hooks/                       # Custom React hooks
│   │   ├── api/                     # API-related hooks
│   │   │   ├── useArticles.ts       # Articles API hooks
│   │   │   ├── useSearch.ts         # Search API hooks
│   │   │   ├── useChat.ts           # Chat API hooks
│   │   │   ├── usePlayers.ts        # Players API hooks
│   │   │   ├── useAnalytics.ts      # Analytics API hooks
│   │   │   └── useAdmin.ts          # Admin API hooks
│   │   ├── ui/                      # UI-related hooks
│   │   │   ├── useDebounce.ts       # Debouncing hook
│   │   │   ├── useLocalStorage.ts   # Local storage hook
│   │   │   ├── useMediaQuery.ts     # Media query hook
│   │   │   ├── useIntersection.ts   # Intersection observer
│   │   │   └── useWebSocket.ts      # WebSocket management
│   │   ├── forms/                   # Form-related hooks
│   │   │   ├── useSearchForm.ts     # Search form logic
│   │   │   ├── useArticleForm.ts    # Article form logic
│   │   │   └── useChatForm.ts       # Chat form logic
│   │   └── index.ts                 # Export all hooks
│   ├── services/                    # API service layer
│   │   ├── api.ts                   # Axios configuration
│   │   ├── articlesService.ts       # Articles API service
│   │   ├── searchService.ts         # Search API service
│   │   ├── chatService.ts           # Chat API service + WebSocket
│   │   ├── playersService.ts        # Players API service
│   │   ├── analysisService.ts       # Analytics API service
│   │   ├── adminService.ts          # Admin API service
│   │   └── index.ts                 # Export all services
│   ├── types/                       # TypeScript definitions
│   │   ├── api.ts                   # API response/request types
│   │   ├── ui.ts                    # UI component types
│   │   ├── forms.ts                 # Form validation types
│   │   ├── env.d.ts                 # Environment variables
│   │   └── global.d.ts              # Global type declarations
│   ├── utils/                       # Utility functions
│   │   ├── cn.ts                    # Class name utility (clsx + tailwind-merge)
│   │   ├── date.ts                  # Date formatting utilities
│   │   ├── string.ts                # String manipulation utilities
│   │   ├── validation.ts            # Form validation schemas (Zod)
│   │   ├── api.ts                   # API utilities
│   │   ├── storage.ts               # Local/session storage utilities
│   │   ├── constants.ts             # App constants
│   │   └── index.ts                 # Export all utilities
│   ├── stores/                      # Global state management
│   │   ├── authStore.ts             # Authentication state
│   │   ├── themeStore.ts            # Theme/dark mode state
│   │   ├── searchStore.ts           # Search state persistence
│   │   └── index.ts                 # Export all stores
│   ├── config/                      # Configuration files
│   │   ├── api.ts                   # API configuration
│   │   ├── routes.ts                # Route definitions
│   │   ├── constants.ts             # Application constants
│   │   └── queryClient.ts           # React Query configuration
│   ├── assets/                      # Static assets
│   │   ├── images/                  # Image files
│   │   ├── icons/                   # Icon files
│   │   └── fonts/                   # Custom fonts
│   ├── styles/                      # Additional styles
│   │   ├── globals.css              # Global CSS overrides
│   │   ├── components.css           # Component-specific styles
│   │   └── utilities.css            # Utility classes
│   ├── App.tsx                      # Main App component
│   ├── main.tsx                     # Application entry point
│   └── index.css                    # Global styles with Tailwind
├── tests/                           # Test files
│   ├── __mocks__/                   # Test mocks
│   ├── components/                  # Component tests
│   ├── hooks/                       # Hook tests
│   ├── services/                    # Service tests
│   ├── utils/                       # Utility tests
│   ├── setup.ts                     # Test setup
│   └── helpers.ts                   # Test helpers
├── docs/                            # Documentation
│   ├── COMPONENTS.md                # Component documentation
│   ├── API.md                       # API integration guide
│   └── DEPLOYMENT.md                # Deployment guide
├── .env.example                     # Environment variables template
├── .eslintrc.cjs                    # ESLint configuration
├── .gitignore                       # Git ignore rules
├── .prettierrc                      # Prettier configuration
├── index.html                       # HTML template
├── package.json                     # Dependencies and scripts
├── postcss.config.js                # PostCSS configuration
├── tailwind.config.js               # Tailwind CSS configuration
├── tsconfig.json                    # TypeScript configuration
├── tsconfig.node.json               # Node TypeScript configuration
├── vite.config.ts                   # Vite configuration
└── README.md                        # Project documentation
```

## 🔧 Key Features by Directory

### `/src/components/`
- **UI Components**: Reusable, styled components following design system
- **Feature Components**: Specific functionality components
- **Layout Components**: Navigation, header, footer, sidebar

### `/src/hooks/`
- **API Hooks**: React Query hooks for each API endpoint
- **UI Hooks**: Common UI functionality (debounce, media queries, etc.)
- **Form Hooks**: Form state management and validation

### `/src/services/`
- **API Services**: Axios-based service layer for each API group
- **WebSocket Service**: Real-time chat functionality
- **Error Handling**: Centralized error handling and notifications

### `/src/types/`
- **API Types**: Complete TypeScript definitions for API responses
- **UI Types**: Component and form prop types
- **Global Types**: Application-wide type definitions

### `/src/utils/`
- **Utilities**: Helper functions for common operations
- **Validation**: Zod schemas for form validation
- **Constants**: Application constants and configuration

### `/src/pages/`
- **Route Components**: Top-level page components
- **SEO-Ready**: Proper metadata and structure
- **Error Boundaries**: Graceful error handling

## 🚀 Integration with Backend

### API Endpoints Covered
- **Articles**: `/api/v1/articles/*`
- **Search**: `/api/v1/search/*` and `/api/v1/vector/*`
- **Chat**: `/api/v1/chat/*` with WebSocket support
- **Players**: `/api/v1/players/*`
- **Analytics**: `/api/v1/analysis/*`
- **Admin**: `/api/v1/admin/*`

### WebSocket Integration
- Real-time chat with streaming responses
- Automatic reconnection handling
- Message type routing and handling

### Rate Limiting
- Client-side rate limit awareness
- User tier management
- Proper error handling for rate limits

## 🎨 Design System

### Tailwind Configuration
- Custom color palette with CSS variables
- Dark mode support
- Consistent spacing and typography
- Component variants and utilities

### Component Standards
- TypeScript interfaces for all props
- Forward refs for form components
- Consistent naming conventions
- Error and loading states

## 📱 Responsive Design
- Mobile-first approach
- Breakpoint-specific layouts
- Touch-friendly interactions
- Progressive enhancement

## 🔒 Security & Performance
- Type-safe API calls
- Input validation with Zod
- XSS protection
- Code splitting and lazy loading
- Optimistic updates with React Query

## 🧪 Testing Strategy
- Unit tests for utilities and hooks
- Component testing with React Testing Library
- Integration tests for API services
- E2E tests for critical user flows

This structure provides a comprehensive, scalable frontend that integrates seamlessly with your FastAPI backend while maintaining modern React development best practices. 