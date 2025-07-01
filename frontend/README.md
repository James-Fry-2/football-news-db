# Football News DB - Frontend

A modern React TypeScript frontend for the Football News Database, featuring semantic search, real-time chat, and comprehensive analytics.

## 🚀 Tech Stack

- **React 18** with TypeScript
- **Vite** for fast development and building
- **TailwindCSS** for styling with custom design system
- **React Query** for server state management and caching
- **React Router** for client-side routing
- **React Hook Form** with Zod validation
- **Lucide React** for icons
- **Framer Motion** for animations
- **Recharts** for data visualization

## 📁 Project Structure

```
frontend/
├── public/                 # Static assets
├── src/
│   ├── components/         # Reusable UI components
│   │   ├── ui/            # Base UI components (Button, Input, etc.)
│   │   ├── features/      # Feature-specific components
│   │   └── Layout.tsx     # Main layout component
│   ├── pages/             # Page components
│   │   ├── HomePage.tsx
│   │   ├── ArticlesPage.tsx
│   │   ├── SearchPage.tsx
│   │   ├── ChatPage.tsx
│   │   ├── AnalyticsPage.tsx
│   │   └── AdminPage.tsx
│   ├── hooks/             # Custom React hooks
│   │   ├── useArticles.ts
│   │   ├── useSearch.ts
│   │   ├── useChat.ts
│   │   └── useWebSocket.ts
│   ├── services/          # API service layer
│   │   ├── api.ts         # Axios configuration
│   │   ├── articlesService.ts
│   │   ├── searchService.ts
│   │   ├── chatService.ts
│   │   ├── playersService.ts
│   │   ├── analysisService.ts
│   │   ├── adminService.ts
│   │   └── index.ts
│   ├── types/             # TypeScript type definitions
│   │   ├── api.ts         # API response types
│   │   └── env.d.ts       # Environment variables
│   ├── utils/             # Utility functions
│   │   ├── cn.ts          # Class name utility
│   │   ├── date.ts        # Date formatting
│   │   └── validation.ts  # Form validation schemas
│   ├── stores/            # Global state management
│   │   └── authStore.ts   # Authentication state
│   ├── config/            # Configuration files
│   │   └── constants.ts   # App constants
│   ├── App.tsx            # Main App component
│   ├── main.tsx           # Entry point
│   └── index.css          # Global styles
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.js
└── README.md
```

## 🎯 Features

### Core Features
- **Article Management**: Browse, search, and manage football articles
- **Semantic Search**: Advanced search with multiple ranking strategies
- **Real-time Chat**: LLM-powered chat with WebSocket support
- **Analytics Dashboard**: Statistics and insights visualization
- **Admin Panel**: User management and rate limiting controls

### API Integration
- **RESTful APIs**: Full integration with FastAPI backend
- **WebSocket Support**: Real-time chat functionality
- **Error Handling**: Comprehensive error handling with toast notifications
- **Rate Limiting**: User-aware rate limiting with proper feedback
- **Caching**: Intelligent caching with React Query

### UI/UX Features
- **Responsive Design**: Mobile-first responsive layout
- **Dark Mode**: Full dark mode support
- **Loading States**: Proper loading and skeleton states
- **Infinite Scroll**: Efficient data loading for large lists
- **Search Suggestions**: Real-time search suggestions with debouncing
- **Toast Notifications**: User-friendly error and success messages

## 🔧 Component Architecture

### UI Components (`src/components/ui/`)
Base reusable components following a design system:
- `Button.tsx` - Versatile button component with variants
- `Input.tsx` - Form input with validation support
- `Card.tsx` - Container component for content
- `Badge.tsx` - Status and category badges
- `Avatar.tsx` - User avatar component
- `Skeleton.tsx` - Loading placeholder component
- `Dialog.tsx` - Modal dialog component
- `Dropdown.tsx` - Dropdown menu component

### Feature Components (`src/components/features/`)
Feature-specific components:
- `ArticleCard.tsx` - Article display component
- `SearchForm.tsx` - Advanced search form
- `ChatMessage.tsx` - Chat message component
- `ChatInput.tsx` - Chat input with WebSocket integration
- `AnalyticsChart.tsx` - Chart components for analytics
- `PlayerCard.tsx` - Player information display
- `SearchResults.tsx` - Search results with filtering
- `ConversationList.tsx` - Chat conversation sidebar

### Layout Components
- `Layout.tsx` - Main application layout
- `Header.tsx` - Navigation header
- `Sidebar.tsx` - Navigation sidebar
- `Footer.tsx` - Application footer

## 🔗 API Integration

### Services Layer
Each service corresponds to a backend API route group:

```typescript
// Articles API
articlesService.getArticles(filters?)
articlesService.getArticle(url)
articlesService.createArticle(data)
articlesService.updateArticle(url, data)
articlesService.deleteArticle(url)

// Search API
searchService.semanticSearch(request)
searchService.enhancedSearch(request)
searchService.getSearchSuggestions(query)
searchService.getProcessingStats()

// Chat API
chatService.sendMessage(message)
chatService.getConversation(id)
chatService.listConversations()
// WebSocket for real-time chat
```

### React Query Integration
- **Caching**: Automatic caching with proper invalidation
- **Background Updates**: Automatic refetching when data becomes stale
- **Optimistic Updates**: Immediate UI updates for better UX
- **Error Handling**: Centralized error handling with retry logic

### TypeScript Types
All API responses and requests are fully typed:
- `Article`, `ArticleCreate`, `ArticleUpdate`
- `SearchResult`, `SearchResponse`, `SearchRequest`
- `ChatMessage`, `ChatResponse`, `ConversationSummary`
- `Player`, `Team`, `AnalysisResponse`

## 🔄 State Management

### React Query for Server State
- **Articles**: Cached article data with filters
- **Search**: Search results with query-based caching
- **Chat**: Conversation history and messages
- **Analytics**: Dashboard statistics

### Local State Management
- **Form State**: React Hook Form for complex forms
- **UI State**: Local component state for UI interactions
- **Auth State**: Simple context/store for authentication

## 🎨 Styling System

### TailwindCSS Configuration
- **Custom Colors**: CSS variables for theming
- **Dark Mode**: Automatic dark mode support
- **Design Tokens**: Consistent spacing, typography, and colors
- **Component Variants**: Systematic component styling

### CSS Variables
```css
:root {
  --background: 0 0% 100%;
  --foreground: 222.2 84% 4.9%;
  --primary: 221.2 83.2% 53.3%;
  --secondary: 210 40% 96%;
  /* ... more variables */
}
```

## 🚦 Getting Started

### Prerequisites
- Node.js 18+ 
- npm or yarn
- Running FastAPI backend

### Installation

1. **Install dependencies**:
```bash
cd frontend
npm install
```

2. **Environment setup**:
```bash
cp .env.example .env.local
# Edit .env.local with your API URLs
```

3. **Start development server**:
```bash
npm run dev
```

4. **Build for production**:
```bash
npm run build
```

### Environment Variables
```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

## 📝 Development Scripts

```bash
# Development
npm run dev          # Start dev server
npm run build        # Build for production
npm run preview      # Preview production build

# Code Quality
npm run lint         # Run ESLint
npm run lint:fix     # Fix ESLint errors
npm run type-check   # TypeScript type checking
npm run format       # Format with Prettier

# Testing
npm run test         # Run tests
npm run test:ui      # Run tests with UI
```

## 🔌 WebSocket Integration

Real-time chat functionality with automatic reconnection:
```typescript
const chatWS = new ChatWebSocketService(connectionId);
await chatWS.connect();

chatWS.onMessage('chunk', (message) => {
  // Handle streaming chat responses
});

chatWS.sendMessage('Hello!', conversationId);
```

## 📊 Performance Optimizations

- **Code Splitting**: Route-based code splitting
- **Lazy Loading**: Lazy load non-critical components
- **Image Optimization**: Proper image loading and optimization
- **Bundle Analysis**: Webpack bundle analyzer integration
- **Caching**: Aggressive caching strategies with React Query

## 🔒 Security Features

- **XSS Protection**: Proper output encoding
- **CSRF Protection**: Token-based CSRF protection
- **Rate Limiting**: Client-side rate limiting awareness
- **Input Validation**: Comprehensive form validation
- **Error Boundaries**: Graceful error handling

## 🚀 Deployment

The frontend is configured for deployment to:
- **Vercel** (recommended)
- **Netlify**
- **Static hosting** (GitHub Pages, etc.)

### Build Configuration
```bash
npm run build
# Output in dist/ directory
```

## 🧪 Testing Strategy

- **Unit Tests**: Component and utility testing with Vitest
- **Integration Tests**: API integration testing
- **E2E Tests**: Critical user flows testing
- **Visual Testing**: Component visual regression testing

## 📚 Additional Resources

- **Storybook**: Component development and documentation
- **TypeScript**: Full type safety throughout the application
- **ESLint + Prettier**: Code quality and formatting
- **Husky**: Git hooks for code quality

## 🤝 Contributing

1. Follow the established patterns and conventions
2. Add proper TypeScript types for new features
3. Include error handling and loading states
4. Write tests for new components and utilities
5. Update documentation for significant changes

## 📄 License

This project is part of the Football News DB system and follows the same licensing terms as the backend. 