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
  const [showToast, setShowToast] = useState(false);
  const [ghostElementIds, setGhostElementIds] = useState<string[]>([]);

  // Ref to prevent too frequent API calls
  const debounceTimerRef = useRef<NodeJS.Timeout | null>(null);
  const lastRequestTimeRef = useRef<number>(0);
  const toastTimerRef = useRef<NodeJS.Timeout | null>(null);

  const handleCanvasChange = useCallback(async (
    elements: readonly ExcalidrawElement[],
    appState: any,
    files: any
  ) => {
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

        // Prepare API request (removed session_id - backend doesn't support it)
        const request = {
          canvas_elements: formattedElements,
          recent_changes: recentChanges,
          context: {
            design_type: 'distributed-system',
            timestamp: new Date().toISOString()
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

        // Show toast notification if there's a suggestion
        if (suggestion.suggestion || suggestion.reasoning) {
          setShowToast(true);

          // Auto-dismiss toast after 5 seconds
          if (toastTimerRef.current) {
            clearTimeout(toastTimerRef.current);
          }
          toastTimerRef.current = setTimeout(() => {
            setShowToast(false);
          }, 5000);
        }

        // If we have Excalidraw elements in the response, add them as ghost elements
        if (suggestion.excalidraw_elements && suggestion.excalidraw_elements.length > 0 && excalidrawAPI) {
          console.log('Adding ghost elements to canvas:', suggestion.excalidraw_elements);

          // Track ghost element IDs
          const ghostIds = suggestion.excalidraw_elements
            .filter(el => el.type === 'rectangle' && el.id.startsWith('ghost-'))
            .map(el => el.id);
          setGhostElementIds(ghostIds);

          // Add ghost elements to the canvas
          const currentElements = excalidrawAPI.getSceneElements();
          excalidrawAPI.updateScene({
            elements: [...currentElements, ...suggestion.excalidraw_elements]
          });
        }

      } catch (error) {
        console.error('Error getting AI suggestion:', error);
        if (onError) {
          onError(error as APIError);
        }
      } finally {
        setIsLoading(false);
      }
    }, 5000); // 5 second debounce to reduce API calls

  }, [lastElements, onSuggestionReceived, onError, excalidrawAPI]);

  // Convert ghost element to real element (on Tab press)
  const acceptGhostSuggestion = useCallback(() => {
    if (!excalidrawAPI || ghostElementIds.length === 0) {
      return;
    }

    console.log('Accepting ghost suggestion:', ghostElementIds);

    const currentElements = excalidrawAPI.getSceneElements();
    const updatedElements = currentElements.map((el: any) => {
      // Check if this is a ghost element or its text
      const isGhostRect = ghostElementIds.includes(el.id);
      const isGhostText = el.containerId && ghostElementIds.includes(el.containerId);

      if (isGhostRect || isGhostText) {
        // Convert ghost to real element
        const updates: any = {
          ...el,
          strokeStyle: 'solid',  // Remove dashed stroke
          opacity: 100,  // Full opacity
          groupIds: el.groupIds?.filter((id: string) => id !== 'ai-suggestion') || [],  // Remove AI suggestion group
          customData: undefined,  // Remove ghost metadata
        };

        // Remove question mark from text (handle both text and originalText fields)
        if (el.text && el.text.endsWith('?')) {
          updates.text = el.text.slice(0, -1);
        }
        if (el.originalText && el.originalText.endsWith('?')) {
          updates.originalText = el.originalText.slice(0, -1);
        }

        return updates;
      }
      return el;
    });

    excalidrawAPI.updateScene({
      elements: updatedElements
    });

    // Clear ghost tracking
    setGhostElementIds([]);
    setShowToast(false);  // Dismiss toast
    console.log('Ghost suggestion accepted and converted to real element');
  }, [excalidrawAPI, ghostElementIds]);

  // Remove ghost element (on Esc press)
  const rejectGhostSuggestion = useCallback(() => {
    if (!excalidrawAPI || ghostElementIds.length === 0) {
      return;
    }

    console.log('Rejecting ghost suggestion:', ghostElementIds);

    const currentElements = excalidrawAPI.getSceneElements();
    const filteredElements = currentElements.filter((el: any) => {
      // Remove ghost rectangles
      if (ghostElementIds.includes(el.id)) {
        return false;
      }
      // Remove ghost text labels
      if (el.containerId && ghostElementIds.includes(el.containerId)) {
        return false;
      }
      return true;
    });

    excalidrawAPI.updateScene({
      elements: filteredElements
    });

    // Clear ghost tracking
    setGhostElementIds([]);
    setShowToast(false);  // Dismiss toast
    console.log('Ghost suggestion rejected and removed');
  }, [excalidrawAPI, ghostElementIds]);

  // Keyboard event handler for Tab (accept) and Esc (reject)
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Only handle if there are ghost elements
      if (ghostElementIds.length === 0) {
        return;
      }

      if (event.key === 'Tab') {
        event.preventDefault();  // Prevent default Tab behavior
        acceptGhostSuggestion();
      } else if (event.key === 'Escape') {
        event.preventDefault();
        rejectGhostSuggestion();
      }
    };

    window.addEventListener('keydown', handleKeyDown);

    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [ghostElementIds, acceptGhostSuggestion, rejectGhostSuggestion]);

  // Health check disabled to reduce network calls
  // Health checks are now handled by the main app component
  useEffect(() => {
    console.log('ExcalidrawCanvas initialized - Tab to accept, Esc to reject suggestions');
  }, []);

  return (
    <div className={`relative w-full h-full ${className}`}>
      {/* Loading indicator */}
      {isLoading && (
        <div className="absolute top-4 right-4 z-50 bg-blue-500 text-white px-3 py-1 rounded-lg text-sm flex items-center gap-2 shadow-lg">
          <div className="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full"></div>
          Getting AI suggestion...
        </div>
      )}

      {/* Toast notification for suggestions */}
      {showToast && suggestions && (
        <div className="absolute top-4 left-1/2 transform -translate-x-1/2 z-50 bg-white border border-blue-200 rounded-lg shadow-xl p-4 max-w-md animate-slideDown">
          <div className="flex items-start gap-3">
            {/* Icon */}
            <div className="flex-shrink-0 w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
              <span className="text-lg">💡</span>
            </div>

            {/* Content */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between mb-1">
                <h4 className="text-sm font-semibold text-gray-800">
                  AI Suggestion
                  {suggestions.metadata?.confidence && (
                    <span className="ml-2 text-xs font-normal text-gray-500">
                      ({Math.round(suggestions.metadata.confidence * 100)}% confident)
                    </span>
                  )}
                </h4>
                <button
                  onClick={() => setShowToast(false)}
                  className="text-gray-400 hover:text-gray-600 transition-colors"
                  aria-label="Dismiss"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              <p className="text-xs text-gray-600 mb-2 leading-relaxed">
                {suggestions.reasoning}
              </p>

              {suggestions.suggestion?.nodes && suggestions.suggestion.nodes.length > 0 && (
                <>
                  <div className="flex flex-wrap gap-1 mb-2">
                    {suggestions.suggestion.nodes.map((node, idx) => (
                      <span
                        key={idx}
                        className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-50 text-blue-700 border border-blue-200"
                      >
                        {node.label}
                      </span>
                    ))}
                  </div>

                  {/* Keyboard hints */}
                  {ghostElementIds.length > 0 && (
                    <div className="flex items-center gap-3 text-xs text-gray-500 pt-2 border-t border-gray-100">
                      <kbd className="px-1.5 py-0.5 bg-gray-100 border border-gray-300 rounded text-gray-700 font-mono">Tab</kbd>
                      <span>to accept</span>
                      <span className="text-gray-300">|</span>
                      <kbd className="px-1.5 py-0.5 bg-gray-100 border border-gray-300 rounded text-gray-700 font-mono">Esc</kbd>
                      <span>to reject</span>
                    </div>
                  )}
                </>
              )}
            </div>
          </div>

          {/* Progress bar for auto-dismiss */}
          <div className="absolute bottom-0 left-0 right-0 h-1 bg-gray-100 rounded-b-lg overflow-hidden">
            <div className="h-full bg-blue-500 animate-shrink" style={{ animationDuration: '5s' }}></div>
          </div>
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