import React, { useState, useEffect, useRef } from 'react';
import { Message, Tenant, OrderSummary, User } from '../types';
import { api, ApiError } from '../api';

interface ChatInterfaceProps {
  tenant: Tenant;
  user?: User | null;
  onBack: () => void;
  onViewDashboard?: () => void;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({ tenant, user, onBack, onViewDashboard }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [conversationId, setConversationId] = useState<string | undefined>(undefined);
  const [orderSummary, setOrderSummary] = useState<OrderSummary | null>(null);
  const [requiresConfirmation, setRequiresConfirmation] = useState(false);
  const [inputError, setInputError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const validateInput = (text: string): boolean => {
    setInputError(null);

    if (!text.trim()) {
      setInputError('Message cannot be empty');
      return false;
    }

    if (text.length > 5000) {
      setInputError('Message is too long (maximum 5000 characters)');
      return false;
    }

    return true;
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setInputMessage(value);
    
    // Clear input error when user starts typing
    if (inputError) {
      setInputError(null);
    }
  };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (loading) {
      return;
    }

    if (!validateInput(inputMessage)) {
      return;
    }

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      sender: 'user',
      text: inputMessage,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    const messageToSend = inputMessage;
    setInputMessage('');
    setLoading(true);
    setError(null);
    setInputError(null);

    try {
      const response = await api.sendMessage(
        tenant.id,
        messageToSend,
        conversationId,
        user?.id
      );

      // Update conversation ID if this is the first message
      if (!conversationId) {
        setConversationId(response.conversation_id);
      }

      const agentMessage: Message = {
        id: `agent-${Date.now()}`,
        sender: 'agent',
        text: response.response,
        timestamp: new Date(),
        intent: response.intent,
      };

      setMessages((prev) => [...prev, agentMessage]);

      // Handle order confirmation flow
      if (response.requires_confirmation && response.order_summary) {
        setRequiresConfirmation(true);
        setOrderSummary(response.order_summary);
      } else {
        setRequiresConfirmation(false);
        setOrderSummary(null);
      }
    } catch (err) {
      // Use user-friendly error message from ApiError
      const errorMsg = err instanceof ApiError && err.userMessage 
        ? err.userMessage 
        : err instanceof Error 
        ? err.message 
        : 'Failed to send message';
      
      setError(errorMsg);
      
      // Add error message to chat
      const errorMessage: Message = {
        id: `error-${Date.now()}`,
        sender: 'agent',
        text: `Sorry, I encountered an error: ${errorMsg}`,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const formatTimestamp = (timestamp: Date) => {
    return new Date(timestamp).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
    });
  };

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

  return (
    <div className="flex flex-col h-screen bg-gray-100">
      {/* Header */}
      <div className="bg-white shadow-md px-6 py-4 flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <button
            onClick={onBack}
            className="text-gray-600 hover:text-gray-900 transition-colors"
            aria-label="Back to tenant selection"
          >
            <svg
              className="w-6 h-6"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M15 19l-7-7 7-7"
              />
            </svg>
          </button>
          <div className="flex items-center space-x-3">
            <span className="text-3xl">{getTenantIcon(tenant.type)}</span>
            <div>
              <h1 className="text-xl font-semibold text-gray-900">
                {tenant.name}
              </h1>
              <p className="text-sm text-gray-500 capitalize">{tenant.type}</p>
            </div>
          </div>
        </div>
        <div className="flex items-center space-x-4">
          {user && (
            <div className="flex items-center space-x-2 px-3 py-1 bg-indigo-100 rounded-full">
              <div className="w-6 h-6 bg-indigo-500 rounded-full flex items-center justify-center text-white text-xs font-bold">
                {user.name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)}
              </div>
              <span className="text-sm text-indigo-700">{user.name.split(' ')[0]}</span>
            </div>
          )}
          {onViewDashboard && (
            <button
              onClick={onViewDashboard}
              className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              aria-label="View dashboard"
            >
              <svg
                className="w-5 h-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                />
              </svg>
              <span>Dashboard</span>
            </button>
          )}
        </div>
      </div>

      {/* Messages Container */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center py-12">
            <div className="text-6xl mb-4">{getTenantIcon(tenant.type)}</div>
            <h2 className="text-2xl font-semibold text-gray-900 mb-2">
              {user ? `¡Hola ${user.name.split(' ')[0]}!` : `¡Bienvenido a ${tenant.name}!`}
            </h2>
            <p className="text-gray-600">
              {user 
                ? `Estás chateando con ${tenant.name}. Pregúntame sobre el menú, horarios, ubicación o haz un pedido.`
                : 'Pregúntame sobre el menú, horarios, ubicación o haz un pedido.'}
            </p>
          </div>
        )}

        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${
              message.sender === 'user' ? 'justify-end' : 'justify-start'
            }`}
          >
            <div
              className={`max-w-xs md:max-w-md lg:max-w-lg xl:max-w-xl rounded-lg px-4 py-3 ${
                message.sender === 'user'
                  ? 'bg-blue-600 text-white'
                  : 'bg-white text-gray-900 shadow-md'
              }`}
            >
              <p className="text-sm whitespace-pre-wrap break-words">
                {message.text}
              </p>
              <div
                className={`text-xs mt-1 ${
                  message.sender === 'user'
                    ? 'text-blue-100'
                    : 'text-gray-500'
                }`}
              >
                {formatTimestamp(message.timestamp)}
                {message.intent && message.sender === 'agent' && (
                  <span className="ml-2 italic">({message.intent})</span>
                )}
              </div>
            </div>
          </div>
        ))}

        {/* Order Summary Display */}
        {requiresConfirmation && orderSummary && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <h3 className="font-semibold text-yellow-900 mb-2">
              Order Summary
            </h3>
            <div className="space-y-2">
              {orderSummary.products.map((product, index) => (
                <div
                  key={index}
                  className="flex justify-between text-sm text-yellow-900"
                >
                  <span>
                    {product.name} x {product.quantity}
                  </span>
                  <span>
                    ${(product.unit_price || product.price || 0).toFixed(2)}
                  </span>
                </div>
              ))}
              <div className="border-t border-yellow-300 pt-2 flex justify-between font-semibold text-yellow-900">
                <span>Total</span>
                <span>${orderSummary.total.toFixed(2)}</span>
              </div>
            </div>
            <p className="text-sm text-yellow-800 mt-2">
              Please confirm your order by typing "yes" or "confirm"
            </p>
          </div>
        )}

        {/* Loading Indicator */}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-white rounded-lg px-4 py-3 shadow-md">
              <div className="flex space-x-2">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                <div
                  className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                  style={{ animationDelay: '0.1s' }}
                ></div>
                <div
                  className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                  style={{ animationDelay: '0.2s' }}
                ></div>
              </div>
            </div>
          </div>
        )}

        {/* Error Display */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-red-800 text-sm">{error}</p>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Form */}
      <div className="bg-white border-t border-gray-200 px-6 py-4">
        <form onSubmit={handleSendMessage} className="space-y-2">
          <div className="flex space-x-4">
            <input
              type="text"
              value={inputMessage}
              onChange={handleInputChange}
              placeholder="Type your message..."
              disabled={loading}
              maxLength={5000}
              className={`flex-1 px-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed ${
                inputError
                  ? 'border-red-300 focus:ring-red-500'
                  : 'border-gray-300 focus:ring-blue-500'
              }`}
              aria-label="Message input"
              aria-invalid={!!inputError}
              aria-describedby={inputError ? 'input-error' : undefined}
            />
            <button
              type="submit"
              disabled={loading || !inputMessage.trim()}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:bg-gray-300 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
              aria-label="Send message"
            >
              {loading ? (
                <svg
                  className="animate-spin h-5 w-5"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  ></circle>
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  ></path>
                </svg>
              ) : (
                <svg
                  className="w-5 h-5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
                  />
                </svg>
              )}
            </button>
          </div>
          {inputError && (
            <p id="input-error" className="text-sm text-red-600 px-1">
              {inputError}
            </p>
          )}
          {inputMessage.length > 4500 && (
            <p className="text-xs text-gray-500 px-1">
              {inputMessage.length} / 5000 characters
            </p>
          )}
        </form>
      </div>
    </div>
  );
};

export default ChatInterface;
