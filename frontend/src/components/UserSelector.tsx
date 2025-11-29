import React, { useEffect, useState } from 'react';
import { User } from '../types';
import { api, ApiError } from '../api';

interface UserSelectorProps {
  onUserSelect: (user: User) => void;
  onSkip: () => void;
  onBack?: () => void;
}

const UserSelector: React.FC<UserSelectorProps> = ({ onUserSelect, onSkip, onBack }) => {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchUsers = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await api.getUsers();
        setUsers(data);
      } catch (err) {
        const errorMsg = err instanceof ApiError && err.userMessage 
          ? err.userMessage 
          : err instanceof Error 
          ? err.message 
          : 'Failed to load users';
        setError(errorMsg);
      } finally {
        setLoading(false);
      }
    };

    fetchUsers();
  }, []);

  const getUserAvatar = (name: string) => {
    return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
  };

  const getAvatarColor = (index: number) => {
    const colors = [
      'bg-blue-500',
      'bg-green-500',
      'bg-purple-500',
      'bg-orange-500',
      'bg-pink-500',
    ];
    return colors[index % colors.length];
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-screen bg-gradient-to-br from-indigo-50 to-purple-100">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Cargando usuarios...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex justify-center items-center min-h-screen bg-gradient-to-br from-indigo-50 to-purple-100 p-4">
        <div className="bg-white rounded-lg shadow-lg p-8 max-w-md w-full">
          <div className="flex items-center justify-center w-16 h-16 bg-red-100 rounded-full mx-auto mb-4">
            <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h2 className="text-xl font-semibold text-gray-900 text-center mb-2">Error</h2>
          <p className="text-gray-600 text-center mb-6">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="w-full bg-indigo-600 text-white py-3 px-4 rounded-lg hover:bg-indigo-700 transition-colors"
          >
            Reintentar
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 to-purple-100 py-12 px-4">
      <div className="max-w-2xl mx-auto">
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
          <div className="text-6xl mb-4">👤</div>
          <h1 className="text-3xl font-bold text-gray-900 mb-4">
            ¿Quién eres?
          </h1>
          <p className="text-lg text-gray-600">
            Selecciona tu perfil para personalizar tu experiencia
          </p>
        </div>

        <div className="space-y-4">
          {users.map((user, index) => (
            <button
              key={user.id}
              onClick={() => onUserSelect(user)}
              className="w-full bg-white rounded-xl shadow-md hover:shadow-xl transition-all duration-300 p-4 text-left transform hover:-translate-y-1 focus:outline-none focus:ring-4 focus:ring-indigo-300"
            >
              <div className="flex items-center space-x-4">
                <div className={`w-12 h-12 ${getAvatarColor(index)} rounded-full flex items-center justify-center text-white font-bold text-lg`}>
                  {getUserAvatar(user.name)}
                </div>
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-gray-900">
                    {user.name}
                  </h3>
                  <p className="text-sm text-gray-500">{user.email}</p>
                </div>
                <svg className="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </div>
            </button>
          ))}
        </div>

        <div className="mt-8 text-center">
          <button
            onClick={onSkip}
            className="text-gray-500 hover:text-gray-700 underline transition-colors"
          >
            Continuar como invitado
          </button>
        </div>

        {users.length === 0 && (
          <div className="text-center py-12">
            <p className="text-gray-500 text-lg">No hay usuarios disponibles</p>
            <button
              onClick={onSkip}
              className="mt-4 bg-indigo-600 text-white py-2 px-6 rounded-lg hover:bg-indigo-700 transition-colors"
            >
              Continuar como invitado
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default UserSelector;
