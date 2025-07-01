# ChatContainer Component

A flexible, responsive chat layout component for React applications with TypeScript support.

## Features

- **Flexible Grid Layout**: Uses CSS Grid for responsive layout management
- **Message Area**: Scrollable message display with auto-scroll functionality
- **Input Area**: Auto-resizing textarea with keyboard shortcuts
- **Responsive Sidebar Integration**: Works seamlessly with sidebar components
- **Proper Overflow Handling**: Smooth scrolling and overflow management
- **Expandable View**: Full-screen mode for focused conversations
- **Message Types**: Support for user, assistant, system, and error messages
- **Loading States**: Built-in loading indicators and disabled states
- **Accessibility**: Screen reader friendly with proper ARIA labels

## Components

### ChatContainer

The main chat interface component.

```tsx
interface ChatContainerProps {
  messages?: Message[];
  onSendMessage: (message: string) => Promise<void>;
  isLoading?: boolean;
  placeholder?: string;
  className?: string;
  sidebarOpen?: boolean;
  onToggleSidebar?: () => void;
  showHeader?: boolean;
  headerContent?: React.ReactNode;
  disabled?: boolean;
  maxHeight?: string;
  enableAutoScroll?: boolean;
}
```

### ChatGrid

A responsive grid layout wrapper for chat interfaces.

```tsx
interface ChatGridProps {
  sidebar?: React.ReactNode;
  sidebarOpen?: boolean;
  children: React.ReactNode;
  className?: string;
}
```

### Message

Message data structure.

```tsx
interface Message {
  id: string;
  content: string;
  timestamp: Date;
  sender: 'user' | 'assistant';
  type?: 'text' | 'system' | 'error';
}
```

## Usage Examples

### Basic Usage

```tsx
import { ChatContainer, Message } from '@/components/ChatContainer';

const [messages, setMessages] = useState<Message[]>([]);
const [isLoading, setIsLoading] = useState(false);

const handleSendMessage = async (content: string) => {
  // Your message handling logic
  console.log('Sending:', content);
};

return (
  <ChatContainer
    messages={messages}
    onSendMessage={handleSendMessage}
    isLoading={isLoading}
    placeholder="Type your message..."
  />
);
```

### With Sidebar Integration

```tsx
import { ChatContainer, ChatGrid } from '@/components/ChatContainer';
import { Sidebar } from '@/components/Sidebar';

const [sidebarOpen, setSidebarOpen] = useState(true);

return (
  <ChatGrid
    sidebar={
      <Sidebar
        isOpen={sidebarOpen}
        onToggle={() => setSidebarOpen(!sidebarOpen)}
        // ... other sidebar props
      />
    }
    sidebarOpen={sidebarOpen}
  >
    <ChatContainer
      messages={messages}
      onSendMessage={handleSendMessage}
      sidebarOpen={sidebarOpen}
      onToggleSidebar={() => setSidebarOpen(!sidebarOpen)}
    />
  </ChatGrid>
);
```

### Custom Header

```tsx
<ChatContainer
  messages={messages}
  onSendMessage={handleSendMessage}
  headerContent={
    <div>
      <h3 className="text-sm font-medium">Custom Chat Title</h3>
      <p className="text-xs text-muted-foreground">
        Custom description
      </p>
    </div>
  }
/>
```

### Full-height Layout

```tsx
<div className="h-screen bg-background">
  <ChatContainer
    messages={messages}
    onSendMessage={handleSendMessage}
    maxHeight="100vh"
  />
</div>
```

## Keyboard Shortcuts

- **Enter**: Send message
- **Shift + Enter**: New line in input
- **Ctrl/Cmd + /**: Focus input (if implemented in parent)

## Responsive Behavior

- **Mobile (< 768px)**: 
  - Single column layout
  - Sidebar hidden by default
  - Mobile-optimized touch targets
  
- **Tablet (768px - 1024px)**:
  - Sidebar toggleable
  - Optimized message bubbles
  
- **Desktop (> 1024px)**:
  - Full sidebar visible
  - Enhanced keyboard navigation
  - Larger chat area

## Styling

The component uses Tailwind CSS classes and CSS custom properties for theming:

- `--background`: Background color
- `--foreground`: Text color
- `--border`: Border color
- `--muted`: Muted text color
- `--primary`: Primary accent color

## Accessibility

- Screen reader support with proper ARIA labels
- Keyboard navigation support
- Focus management
- High contrast mode support
- Motion reduction respect

## Dependencies

- React 18+
- TypeScript 4.5+
- Tailwind CSS 3.0+
- Lucide React (for icons)
- Custom Button and utility components 