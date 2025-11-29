import React, { useEffect, useState } from 'react';
import { Tenant, User } from '../types';
import { api, ApiError } from '../api';

type UserRole = 'customer' | 'business' | null;

interface TenantSelectorProps {
  onTenantSelect: (tenant: Tenant) => void;
  selectedUser?: User | null;
  userRole?: UserRole;
  onChangeUser?: () => void;
  onBack?: () => void;
}

const TenantSelector: React.FC<TenantSelectorProps> = ({ onTenantSelect, selectedUser, userRole, onChangeUser, onBack }) => {
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchTenants = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await api.getTenants();
        setTenants(data);
      } catch (err) {
        const errorMsg = err instanceof ApiError && err.userMessage 
          ? err.userMessage 
          : err instanceof Error 
          ? err.message 
          : 'Failed to load tenants';
        setError(errorMsg);
      } finally {
        setLoading(false);
      }
    };

    fetchTenants();
  }, []);

  const getTenantIcon = (type: string) => {
    switch (type.toLowerCase()) {
      case 'restaurant':
        return '🍽️';
      case 'bakery':
        return '🥖';
      case 'minimarket':
        return '🏪';
      default:
        return '🏢';
    }
  };

  const getTenantTypeLabel = (type: string) => {
    return type.charAt(0).toUpperCase() + type.slice(1);
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading tenants...</p>
        </div>
      </div>
    );
  }

  const handleRetry = () => {
    window.location.reload();
  };

  if (error) {
    return (
      <div className="flex justify-center items-center min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
        <div className="bg-white rounded-lg shadow-lg p-8 max-w-md w-full">
          <div className="flex items-center justify-center w-16 h-16 bg-red-100 rounded-full mx-auto mb-4">
            <svg
              className="w-8 h-8 text-red-600"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          </div>
          <h2 className="text-xl font-semibold text-gray-900 text-center mb-2">
            Unable to Load Tenants
          </h2>
          <p className="text-gray-600 text-center mb-6">{error}</p>
          <button
            onClick={handleRetry}
            className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg hover:bg-blue-700 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 py-12 px-4">
      <div className="max-w-4xl mx-auto">
        {/* User info banner */}
        {selectedUser && (
          <div className="bg-white rounded-lg shadow-md p-4 mb-8 flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-indigo-500 rounded-full flex items-center justify-center text-white font-bold">
                {selectedUser.name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)}
              </div>
              <div>
                <p className="font-medium text-gray-900">Hola, {selectedUser.name.split(' ')[0]}!</p>
                <p className="text-sm text-gray-500">{selectedUser.email}</p>
              </div>
            </div>
            {onChangeUser && (
              <button
                onClick={onChangeUser}
                className="text-indigo-600 hover:text-indigo-800 text-sm font-medium"
              >
                Cambiar usuario
              </button>
            )}
          </div>
        )}

        {/* Back button */}
        {onBack && (
          <button
            onClick={onBack}
            className="mb-6 flex items-center text-gray-600 hover:text-gray-900 transition-colors"
          >
            <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Volver
          </button>
        )}

        <div className="text-center mb-12">
          <div className="text-5xl mb-4">{userRole === 'business' ? '🏢' : '🛒'}</div>
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            {userRole === 'business' ? 'Selecciona tu Negocio' : 'Selecciona un Negocio'}
          </h1>
          <p className="text-lg text-gray-600">
            {userRole === 'business' 
              ? 'Elige el negocio para ver su dashboard y estadísticas'
              : 'Elige el negocio con el que quieres chatear'}
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {tenants.map((tenant) => (
            <button
              key={tenant.id}
              onClick={() => onTenantSelect(tenant)}
              className="bg-white rounded-xl shadow-md hover:shadow-xl transition-all duration-300 p-6 text-left transform hover:-translate-y-1 focus:outline-none focus:ring-4 focus:ring-blue-300"
            >
              <div className="flex items-start space-x-4">
                <div className="text-4xl">{getTenantIcon(tenant.type)}</div>
                <div className="flex-1">
                  <h3 className="text-xl font-semibold text-gray-900 mb-2">
                    {tenant.name}
                  </h3>
                  <span className="inline-block px-3 py-1 bg-blue-100 text-blue-800 text-sm font-medium rounded-full">
                    {getTenantTypeLabel(tenant.type)}
                  </span>
                </div>
              </div>
            </button>
          ))}
        </div>

        {tenants.length === 0 && (
          <div className="text-center py-12">
            <p className="text-gray-500 text-lg">No active tenants available</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default TenantSelector;
