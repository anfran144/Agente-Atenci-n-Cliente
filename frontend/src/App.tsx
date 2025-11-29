import { useState } from 'react';
import RoleSelector from './components/RoleSelector';
import UserSelector from './components/UserSelector';
import TenantSelector from './components/TenantSelector';
import ChatInterface from './components/ChatInterface';
import Dashboard from './components/Dashboard';
import ErrorBoundary from './components/ErrorBoundary';
import { Tenant, User } from './types';

type UserRole = 'customer' | 'business' | null;
type View = 'role-selector' | 'user-selector' | 'tenant-selector' | 'chat' | 'dashboard';

function App() {
  const [userRole, setUserRole] = useState<UserRole>(null);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [selectedTenant, setSelectedTenant] = useState<Tenant | null>(null);
  const [currentView, setCurrentView] = useState<View>('role-selector');

  // Role selection handlers
  const handleRoleSelect = (role: 'customer' | 'business') => {
    setUserRole(role);
    if (role === 'customer') {
      setCurrentView('user-selector');
    } else {
      // Business goes directly to tenant selection for dashboard
      setCurrentView('tenant-selector');
    }
  };

  const handleBackToRoleSelector = () => {
    setUserRole(null);
    setSelectedUser(null);
    setSelectedTenant(null);
    setCurrentView('role-selector');
  };

  // Customer flow handlers
  const handleUserSelect = (user: User) => {
    setSelectedUser(user);
    setCurrentView('tenant-selector');
  };

  const handleSkipUser = () => {
    setSelectedUser(null);
    setCurrentView('tenant-selector');
  };

  const handleTenantSelect = (tenant: Tenant) => {
    setSelectedTenant(tenant);
    if (userRole === 'business') {
      setCurrentView('dashboard');
    } else {
      setCurrentView('chat');
    }
  };

  const handleBackToTenants = () => {
    setSelectedTenant(null);
    setCurrentView('tenant-selector');
  };

  const handleBackToUsers = () => {
    setSelectedUser(null);
    setSelectedTenant(null);
    setCurrentView('user-selector');
  };

  // Render role selector first
  if (currentView === 'role-selector') {
    return (
      <ErrorBoundary>
        <div className="min-h-screen">
          <RoleSelector onRoleSelect={handleRoleSelect} />
        </div>
      </ErrorBoundary>
    );
  }

  // Render user selector (only for customers)
  if (currentView === 'user-selector') {
    return (
      <ErrorBoundary>
        <div className="min-h-screen">
          <UserSelector 
            onUserSelect={handleUserSelect} 
            onSkip={handleSkipUser}
            onBack={handleBackToRoleSelector}
          />
        </div>
      </ErrorBoundary>
    );
  }

  // Render tenant selector
  if (currentView === 'tenant-selector' || !selectedTenant) {
    return (
      <ErrorBoundary>
        <div className="min-h-screen">
          <TenantSelector 
            onTenantSelect={handleTenantSelect} 
            selectedUser={selectedUser}
            userRole={userRole}
            onChangeUser={userRole === 'customer' ? handleBackToUsers : undefined}
            onBack={handleBackToRoleSelector}
          />
        </div>
      </ErrorBoundary>
    );
  }

  // Render dashboard view (for business)
  if (currentView === 'dashboard') {
    return (
      <ErrorBoundary>
        <div className="min-h-screen">
          <Dashboard 
            tenant={selectedTenant} 
            onBack={handleBackToTenants}
          />
        </div>
      </ErrorBoundary>
    );
  }

  // Render chat interface (for customers)
  return (
    <ErrorBoundary>
      <div className="min-h-screen">
        <ChatInterface 
          tenant={selectedTenant}
          user={selectedUser}
          onBack={handleBackToTenants}
        />
      </div>
    </ErrorBoundary>
  );
}

export default App;
