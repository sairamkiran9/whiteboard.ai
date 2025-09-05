'use client';

import { useState, useEffect } from 'react';
import dynamic from 'next/dynamic';
import ErrorBoundary from '@/components/ErrorBoundary';
import NotificationSystem, { useNotifications } from '@/components/NotificationSystem';
import AIDesignAPI from '@/lib/api';
import type { SuggestionResponse, APIError, HealthResponse } from '@/types/api';

// Dynamically import Excalidraw to avoid SSR issues
const ExcalidrawCanvas = dynamic(
  () => import('@/components/ExcalidrawCanvas'),
  { 
    ssr: false,
    loading: () => (
      <div className="flex items-center justify-center h-screen bg-gray-50">
        <div className="text-center">
          <div className="animate-spin w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full mx-auto mb-4"></div>
          <p className="text-gray-600">Loading AI Design Copilot...</p>
        </div>
      </div>
    )
  }
);

function DesignCopilotApp() {
  const { showError, showSuccess, showNotification } = useNotifications();
  const [backendStatus, setBackendStatus] = useState<'checking' | 'connected' | 'error'>('checking');
  const [currentSuggestion, setCurrentSuggestion] = useState<SuggestionResponse | null>(null);

  useEffect(() => {
    // Check backend connectivity on app load
    const checkBackend = async () => {
      try {
        const health = await AIDesignAPI.checkHealth();
        const suggestHealth = await AIDesignAPI.checkSuggestionHealth();
        
        setBackendStatus('connected');
        showSuccess(`Connected to backend! ${suggestHealth.patterns_loaded} patterns loaded.`);
        
        console.log('Backend health:', health);
        console.log('Suggestion service:', suggestHealth);
      } catch (error) {
        console.error('Backend connection failed:', error);
        setBackendStatus('error');
        showError(error as APIError);
      }
    };

    checkBackend();
  }, [showError, showSuccess]);

  const handleSuggestionReceived = (suggestion: SuggestionResponse) => {
    setCurrentSuggestion(suggestion);
    
    if (suggestion.suggestion) {
      const nodeCount = suggestion.suggestion.nodes.length;
      const edgeCount = suggestion.suggestion.edges.length;
      
      if (nodeCount > 0 || edgeCount > 0) {
        showNotification({
          type: 'info',
          title: '💡 New AI Suggestion',
          message: `${nodeCount} new components, ${edgeCount} new connections`,
          duration: 4000,
        });
      }
    }
  };

  const handleError = (error: APIError) => {
    console.error('Canvas error:', error);
    showError(error);
  };

  return (
    <div className="relative w-screen h-screen overflow-hidden bg-gray-50">
      {/* Header */}
      <header className="absolute top-0 left-0 right-0 z-40 bg-white border-b border-gray-200 shadow-sm">
        <div className="flex items-center justify-between px-6 py-3">
          <div className="flex items-center space-x-3">
            <h1 className="text-xl font-bold text-gray-800">🎨 AI Design Copilot</h1>
            <span className="text-sm text-gray-500">GitHub Copilot for System Architecture</span>
          </div>
          
          {/* Status indicator */}
          <div className="flex items-center space-x-2">
            <div className={`w-2 h-2 rounded-full ${
              backendStatus === 'connected' ? 'bg-green-500' : 
              backendStatus === 'error' ? 'bg-red-500' : 
              'bg-yellow-500 animate-pulse'
            }`}></div>
            <span className="text-sm text-gray-600">
              {backendStatus === 'connected' ? 'Backend Connected' :
               backendStatus === 'error' ? 'Backend Error' :
               'Connecting...'}
            </span>
          </div>
        </div>
      </header>

      {/* Instructions panel */}
      <div className="absolute top-16 left-4 z-30 bg-white rounded-lg shadow-lg p-4 max-w-sm">
        <h2 className="font-semibold text-gray-800 mb-2">🚀 Getting Started</h2>
        <ul className="text-sm text-gray-600 space-y-1">
          <li>• Draw rectangles and label them (e.g., "client app", "database")</li>
          <li>• Connect components with arrows</li>
          <li>• Watch for AI suggestions in real-time</li>
          <li>• AI recognizes common patterns and suggests improvements</li>
        </ul>
        
        {backendStatus === 'error' && (
          <div className="mt-3 p-2 bg-red-50 border border-red-200 rounded text-red-700 text-xs">
            ⚠️ Backend not connected. Start the FastAPI server on port 8000.
          </div>
        )}
      </div>

      {/* Main Canvas */}
      <div className="absolute inset-0 pt-16">
        <ExcalidrawCanvas
          onSuggestionReceived={handleSuggestionReceived}
          onError={handleError}
          className="w-full h-full"
        />
      </div>

      {/* Current suggestion sidebar */}
      {currentSuggestion && (
        <div className="absolute top-16 right-4 z-30 bg-white rounded-lg shadow-lg p-4 max-w-xs suggestion-panel max-h-96 overflow-y-auto">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-semibold text-gray-800">Latest Suggestion</h3>
            <button 
              onClick={() => setCurrentSuggestion(null)}
              className="text-gray-400 hover:text-gray-600"
            >
              ×
            </button>
          </div>
          
          <div className="text-sm text-gray-600 mb-3">
            {currentSuggestion.reasoning}
          </div>
          
          {currentSuggestion.suggestion && (
            <>
              {currentSuggestion.suggestion.nodes.length > 0 && (
                <div className="mb-3">
                  <div className="text-xs font-medium text-gray-500 mb-1">Suggested Components:</div>
                  {currentSuggestion.suggestion.nodes.map((node, idx) => (
                    <div key={idx} className="text-xs bg-blue-50 text-blue-700 px-2 py-1 rounded mb-1">
                      <strong>{node.type}</strong>: {node.label}
                    </div>
                  ))}
                </div>
              )}
              
              {currentSuggestion.suggestion.edges.length > 0 && (
                <div className="mb-3">
                  <div className="text-xs font-medium text-gray-500 mb-1">Suggested Connections:</div>
                  {currentSuggestion.suggestion.edges.map((edge, idx) => (
                    <div key={idx} className="text-xs bg-green-50 text-green-700 px-2 py-1 rounded mb-1">
                      {edge.from} <strong>{edge.type}</strong> {edge.to}
                    </div>
                  ))}
                </div>
              )}
            </>
          )}
          
          {currentSuggestion.reference && (
            <a
              href={currentSuggestion.reference}
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs text-blue-500 hover:underline block mt-2"
            >
              📚 Learn more about this pattern
            </a>
          )}
        </div>
      )}
    </div>
  );
}

// Error fallback component for the main app
function AppErrorFallback({ error, retry }: { error?: Error; retry: () => void }) {
  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-50">
      <div className="text-center p-8 bg-white rounded-lg shadow-lg max-w-lg">
        <div className="text-red-500 text-4xl mb-4">🚨</div>
        <h2 className="text-xl font-semibold text-gray-800 mb-2">
          AI Design Copilot Failed to Load
        </h2>
        <p className="text-gray-600 mb-4">
          {error?.message || 'An unexpected error occurred while loading the application'}
        </p>
        <div className="space-x-4">
          <button
            onClick={retry}
            className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-md transition-colors"
          >
            Retry
          </button>
          <button
            onClick={() => window.location.reload()}
            className="bg-gray-500 hover:bg-gray-600 text-white px-4 py-2 rounded-md transition-colors"
          >
            Refresh Page
          </button>
        </div>
      </div>
    </div>
  );
}

export default function Home() {
  return (
    <ErrorBoundary fallback={AppErrorFallback}>
      <NotificationSystem>
        <DesignCopilotApp />
      </NotificationSystem>
    </ErrorBoundary>
  );
}