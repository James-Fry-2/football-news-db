import React, { useState } from 'react';
import { useLocation } from 'react-router-dom';
import { Header, UserProfile } from './Header';

interface LayoutProps {
  children: React.ReactNode;
}

export const Layout: React.FC<LayoutProps> = ({ children }) => {
  const location = useLocation();
  
  // Pages that need full height without padding
  const fullHeightPages = ['/chat'];
  const isFullHeightPage = fullHeightPages.includes(location.pathname);

  // Placeholder user state - replace with your actual auth logic
  const [user, setUser] = useState<UserProfile | undefined>(
    // Uncomment this line to test with a logged-in user
    // {
    //   name: 'John Doe',
    //   email: 'john.doe@example.com',
    //   role: 'admin'
    // }
    undefined
  );

  const handleLogin = () => {
    // Placeholder login logic - replace with your actual auth implementation
    console.log('Login clicked');
    // For demo purposes, let's simulate a login
    setUser({
      name: 'John Doe',
      email: 'john.doe@example.com',
      role: 'admin'
    });
  };

  const handleLogout = () => {
    // Placeholder logout logic - replace with your actual auth implementation
    console.log('Logout clicked');
    setUser(undefined);
  };

  return (
    <div className="min-h-screen bg-background">
      <Header
        user={user}
        onLogin={handleLogin}
        onLogout={handleLogout}
      />
      <main className={isFullHeightPage ? "" : "container mx-auto px-4 py-8"}>
        {children}
      </main>
    </div>
  );
}; 