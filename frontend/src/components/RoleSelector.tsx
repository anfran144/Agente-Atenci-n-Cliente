import React from 'react';

type UserRole = 'customer' | 'business';

interface RoleSelectorProps {
  onRoleSelect: (role: UserRole) => void;
}

const RoleSelector: React.FC<RoleSelectorProps> = ({ onRoleSelect }) => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center py-12 px-4">
      <div className="max-w-2xl w-full">
        <div className="text-center mb-12">
          <div className="text-6xl mb-4">🤖</div>
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Agente de Atención al Cliente
          </h1>
          <p className="text-lg text-gray-600">
            ¿Cómo deseas ingresar?
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Cliente */}
          <button
            onClick={() => onRoleSelect('customer')}
            className="bg-white rounded-2xl shadow-lg hover:shadow-xl transition-all duration-300 p-8 text-center transform hover:-translate-y-2 focus:outline-none focus:ring-4 focus:ring-blue-300 border-2 border-transparent hover:border-blue-400"
          >
            <div className="text-6xl mb-4">👤</div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
              Soy Cliente
            </h2>
            <p className="text-gray-600">
              Quiero consultar información, hacer pedidos o dejar una reseña
            </p>
            <div className="mt-6 flex flex-wrap justify-center gap-2">
              <span className="px-3 py-1 bg-blue-100 text-blue-700 text-sm rounded-full">
                Consultas
              </span>
              <span className="px-3 py-1 bg-green-100 text-green-700 text-sm rounded-full">
                Pedidos
              </span>
              <span className="px-3 py-1 bg-purple-100 text-purple-700 text-sm rounded-full">
                Reseñas
              </span>
            </div>
          </button>

          {/* Empresa */}
          <button
            onClick={() => onRoleSelect('business')}
            className="bg-white rounded-2xl shadow-lg hover:shadow-xl transition-all duration-300 p-8 text-center transform hover:-translate-y-2 focus:outline-none focus:ring-4 focus:ring-indigo-300 border-2 border-transparent hover:border-indigo-400"
          >
            <div className="text-6xl mb-4">🏢</div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
              Soy Empresa
            </h2>
            <p className="text-gray-600">
              Quiero ver el dashboard y estadísticas de mi negocio
            </p>
            <div className="mt-6 flex flex-wrap justify-center gap-2">
              <span className="px-3 py-1 bg-orange-100 text-orange-700 text-sm rounded-full">
                Dashboard
              </span>
              <span className="px-3 py-1 bg-pink-100 text-pink-700 text-sm rounded-full">
                Estadísticas
              </span>
              <span className="px-3 py-1 bg-cyan-100 text-cyan-700 text-sm rounded-full">
                Insights
              </span>
            </div>
          </button>
        </div>

        <p className="text-center text-gray-500 mt-8 text-sm">
          Plataforma multi-negocio con efecto de red
        </p>
      </div>
    </div>
  );
};

export default RoleSelector;
