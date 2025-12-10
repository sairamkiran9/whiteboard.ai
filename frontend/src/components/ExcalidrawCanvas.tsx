'use client';

import { useState, useRef, useCallback, useEffect } from 'react';
import { Excalidraw } from '@excalidraw/excalidraw';
import type { ExcalidrawImperativeAPI } from '@excalidraw/excalidraw/types/types';
import type { ExcalidrawElement } from '@excalidraw/excalidraw/types/element/types';
import AIDesignAPI from '@/lib/api';
import type { SuggestionResponse, APIError } from '@/types/api';

interface ExcalidrawCanvasProps {
  sessionId?: string | null;
  onSuggestionReceived?: (suggestion: SuggestionResponse) => void;
  onError?: (error: APIError) => void;
  className?: string;
}

export default function ExcalidrawCanvas({ 
  sessionId,
  onSuggestionReceived, 
  onError, 
  className = "" 
}: ExcalidrawCanvasProps) {
  const [excalidrawAPI, setExcalidrawAPI] = useState<ExcalidrawImperativeAPI | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [lastElements, setLastElements] = useState<readonly ExcalidrawElement[]>([]);
  const [suggestions, setSuggestions] = useState<SuggestionResponse | null>(null);
  
  // Ref to prevent too frequent API calls
  const debounceTimerRef = useRef<NodeJS.Timeout | null>(null);
  const lastRequestTimeRef = useRef<number>(0);

  const handleCanvasChange = useCallback(async (elements: readonly ExcalidrawElement[]) => {
    // Debounce API calls to avoid flooding
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }

    debounceTimerRef.current = setTimeout(async () => {
      try {
        // Skip if no significant changes detected
        const hasChanges = AIDesignAPI.hasSignificantChanges([...lastElements], [...elements]);
        if (!hasChanges) {
          console.log('No significant changes detected, skipping API call');
          return;
        }

        // Rate limiting - don't call API more than once every 10 seconds for significant changes
        const now = Date.now();
        const timeSinceLastRequest = now - lastRequestTimeRef.current;
        if (timeSinceLastRequest < 10000) {
          console.log(`Rate limited: ${(10000 - timeSinceLastRequest) / 1000}s remaining`);
          return;
        }

        setIsLoading(true);
        lastRequestTimeRef.current = Date.now();

        // Format elements for API
        const formattedElements = AIDesignAPI.formatCanvasElements([...elements]);
        const recentChanges = AIDesignAPI.detectChanges([...lastElements], [...elements]);

        console.log(`Calling API with ${formattedElements.length} elements and ${recentChanges.length} changes`);

        // Prepare API request
        const request = {
          session_id: sessionId || undefined,
          canvas_elements: formattedElements,
          recent_changes: recentChanges,
          context: {
            user_id: 'demo-user',
            timestamp: new Date().toISOString(),
            has_memory: !!sessionId
          }
        };

        // Get AI suggestion
        const suggestion = await AIDesignAPI.getSuggestion(request);
        
        setSuggestions(suggestion);
        setLastElements(elements);
        
        // Notify parent component
        if (onSuggestionReceived) {
          onSuggestionReceived(suggestion);
        }

        console.log('AI Suggestion received:', suggestion);

      } catch (error) {
        console.error('Error getting AI suggestion:', error);
        if (onError) {
          onError(error as APIError);
        }
      } finally {
        setIsLoading(false);
      }
    }, 5000); // 5 second debounce to reduce API calls

  }, [lastElements, onSuggestionReceived, onError]);

  // Health check disabled to reduce network calls
  // Health checks are now handled by the main app component
  useEffect(() => {
    console.log('ExcalidrawCanvas initialized - health checks disabled for reduced network traffic');
  }, []);

  return (
    <div className={`relative w-full h-full ${className}`}>
      {/* Loading indicator */}
      {isLoading && (
        <div className="absolute top-4 right-4 z-50 bg-blue-500 text-white px-3 py-1 rounded-lg text-sm flex items-center gap-2">
          <div className="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full"></div>
          Getting AI suggestion...
        </div>
      )}

      {/* Suggestion display */}
      {suggestions && suggestions.suggestion && (
        <div className="absolute top-4 left-4 z-40 bg-white border border-gray-200 rounded-lg shadow-lg p-4 max-w-sm">
          <div className="text-sm font-semibold text-gray-700 mb-2">💡 AI Suggestion</div>
          <div className="text-xs text-gray-600 mb-2">{suggestions.reasoning}</div>
          
          {suggestions.suggestion.nodes.length > 0 && (
            <div className="mb-2">
              <div className="text-xs font-medium text-gray-500">Suggested components:</div>
              {suggestions.suggestion.nodes.map((node, idx) => (
                <div key={idx} className="text-xs text-blue-600">
                  • {node.label} ({node.type})
                </div>
              ))}
            </div>
          )}
          
          {suggestions.reference && (
            <a 
              href={suggestions.reference} 
              target="_blank" 
              rel="noopener noreferrer"
              className="text-xs text-blue-500 hover:underline"
            >
              📚 Learn more
            </a>
          )}
        </div>
      )}

      {/* Excalidraw Canvas */}
      <div className="w-full h-full">
        <Excalidraw
          excalidrawAPI={(api: ExcalidrawImperativeAPI) => setExcalidrawAPI(api)}
          onChange={handleCanvasChange}
          initialData={{
            appState: {
              theme: 'light',
              viewBackgroundColor: '#fafafb',
              gridSize: null,
            },
            scrollToContent: true,
          }}
        />
      </div>
    </div>
  );
}