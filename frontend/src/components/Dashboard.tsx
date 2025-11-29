import React, { useState, useEffect } from 'react';
import { api, ApiError } from '../api';
import { TenantStats, NetworkInsightsResponse, Tenant } from '../types';

interface DashboardProps {
  tenant: Tenant;
  onBack: () => void;
}

const Dashboard: React.FC<DashboardProps> = ({ tenant, onBack }) => {
  const [stats, setStats] = useState<TenantStats | null>(null);
  const [networkInsights, setNetworkInsights] = useState<NetworkInsightsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showNetworkInsights, setShowNetworkInsights] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        
        // Fetch tenant stats
        const statsData = await api.getStats(tenant.id);
        setStats(statsData);
        
        // Optionally fetch network insights
        if (showNetworkInsights) {
          try {
            const insightsData = await api.getNetworkInsights();
            setNetworkInsights(insightsData);
          } catch (err) {
            console.error('Failed to fetch network insights:', err);
            // Don't fail the whole dashboard if network insights fail
          }
        }
      } catch (err) {
        const errorMsg = err instanceof ApiError && err.userMessage 
          ? err.userMessage 
          : err instanceof Error 
          ? err.message 
          : 'Failed to load dashboard data';
        setError(errorMsg);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [tenant.id, showNetworkInsights]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  const handleRetry = () => {
    setError(null);
    setLoading(true);
    // Trigger re-fetch by updating a dependency
    window.location.reload();
  };

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <div className="bg-white p-8 rounded-lg shadow-lg max-w-md w-full">
          <div className="flex items-center justify-center w-16 h-16 bg-red-100 rounded-full mx-auto mb-4">
            <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h2 className="text-xl font-semibold text-gray-900 text-center mb-2">
            Unable to Load Dashboard
          </h2>
          <p className="text-gray-600 text-center mb-6">{error}</p>
          <div className="flex flex-col gap-3">
            <button
              onClick={handleRetry}
              className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg hover:bg-blue-700 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
            >
              Try Again
            </button>
            <button
              onClick={onBack}
              className="w-full bg-gray-200 text-gray-800 py-3 px-4 rounded-lg hover:bg-gray-300 transition-colors focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2"
            >
              Back to Chat
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (!stats) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="flex items-center space-x-4 mb-2">
                <button
                  onClick={onBack}
                  className="text-blue-600 hover:text-blue-700 flex items-center"
                  aria-label="Cambiar negocio"
                >
                  <svg className="w-5 h-5 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                  </svg>
                  Cambiar Negocio
                </button>
              </div>
              <h1 className="text-2xl font-bold text-gray-900">{tenant.name} Dashboard</h1>
              <p className="text-sm text-gray-500 capitalize">{tenant.type}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          
          {/* Peak Hours Section */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold text-gray-800 mb-4 flex items-center">
              <svg className="w-6 h-6 mr-2 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Peak Hours
            </h2>
            {stats.peak_hours && stats.peak_hours.length > 0 ? (
              <div className="space-y-2">
                {stats.peak_hours.map((hourStat, index) => (
                  <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center">
                      <span className="text-2xl font-bold text-blue-600 w-16">
                        {hourStat.hour.toString().padStart(2, '0')}:00
                      </span>
                      <div className="ml-4">
                        <div className="text-sm text-gray-600">Interactions</div>
                        <div className="text-lg font-semibold text-gray-800">{hourStat.count}</div>
                      </div>
                    </div>
                    <div className="w-32 bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-blue-600 h-2 rounded-full"
                        style={{
                          width: `${Math.min(100, (hourStat.count / Math.max(...stats.peak_hours.map(h => h.count))) * 100)}%`
                        }}
                      ></div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 text-center py-8">No peak hours data available yet</p>
            )}
          </div>

          {/* Top Products Section */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold text-gray-800 mb-4 flex items-center">
              <svg className="w-6 h-6 mr-2 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
              </svg>
              Top Products
            </h2>
            {stats.top_products && stats.top_products.length > 0 ? (
              <div className="space-y-2">
                {stats.top_products.map((product, index) => (
                  <div key={product.product_id || index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center flex-1">
                      <span className="text-lg font-bold text-green-600 w-8">
                        #{index + 1}
                      </span>
                      <span className="ml-3 text-gray-800 font-medium truncate">{product.name}</span>
                    </div>
                    <div className="ml-4 flex items-center">
                      <span className="text-sm text-gray-600 mr-2">Mentions:</span>
                      <span className="bg-green-100 text-green-800 px-3 py-1 rounded-full font-semibold">
                        {product.mentions}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 text-center py-8">No product data available yet</p>
            )}
          </div>

          {/* Common Questions Section */}
          <div className="bg-white rounded-lg shadow-md p-6 lg:col-span-2">
            <h2 className="text-xl font-semibold text-gray-800 mb-4 flex items-center">
              <svg className="w-6 h-6 mr-2 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Common Questions
            </h2>
            {stats.common_questions && stats.common_questions.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {stats.common_questions.map((question, index) => (
                  <div key={index} className="p-4 bg-gray-50 rounded-lg border border-gray-200">
                    <div className="flex items-start justify-between">
                      <p className="text-gray-800 flex-1">{question.question}</p>
                      <span className="ml-3 bg-purple-100 text-purple-800 px-2 py-1 rounded text-sm font-semibold whitespace-nowrap">
                        {question.frequency}x
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 text-center py-8">No common questions data available yet</p>
            )}
          </div>

          {/* Network Insights Section (Optional) */}
          <div className="bg-white rounded-lg shadow-md p-6 lg:col-span-2">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-gray-800 flex items-center">
                <svg className="w-6 h-6 mr-2 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
                </svg>
                Network Insights
              </h2>
              <button
                onClick={() => setShowNetworkInsights(!showNetworkInsights)}
                className="text-sm bg-orange-100 text-orange-700 px-4 py-2 rounded-lg hover:bg-orange-200 transition-colors"
              >
                {showNetworkInsights ? 'Hide' : 'Show'} Global Patterns
              </button>
            </div>
            
            {showNetworkInsights && networkInsights ? (
              <div className="space-y-3">
                {networkInsights.patterns && networkInsights.patterns.length > 0 ? (
                  <>
                    {networkInsights.patterns.map((pattern, index) => (
                      <div key={index} className="p-4 bg-gradient-to-r from-orange-50 to-yellow-50 rounded-lg border border-orange-200">
                        <div className="flex items-start justify-between">
                          <p className="text-gray-800 flex-1">{pattern.pattern}</p>
                          <div className="ml-3 flex flex-col items-end">
                            <span className="bg-orange-100 text-orange-800 px-2 py-1 rounded text-xs font-semibold">
                              {Math.round(pattern.confidence * 100)}% confidence
                            </span>
                            {pattern.business_types && pattern.business_types.length > 0 && (
                              <span className="mt-1 text-xs text-gray-600">
                                {pattern.business_types.join(', ')}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                    <p className="text-xs text-gray-500 mt-2">
                      Generated at: {new Date(networkInsights.generated_at).toLocaleString()}
                    </p>
                  </>
                ) : (
                  <p className="text-gray-500 text-center py-8">No network insights available yet</p>
                )}
              </div>
            ) : showNetworkInsights && !networkInsights ? (
              <div className="text-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-orange-600 mx-auto"></div>
                <p className="mt-2 text-gray-600">Loading network insights...</p>
              </div>
            ) : (
              <p className="text-gray-500 text-center py-8">
                Click "Show Global Patterns" to view insights across all businesses
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
