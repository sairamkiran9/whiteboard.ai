'use client';

import { useState, useEffect } from 'react';
import AIDesignAPI from '@/lib/api';
import type { ProvidersResponse, APIError } from '@/types/api';

interface ProviderSelectorProps {
  onError?: (error: APIError) => void;
  className?: string;
}

export default function ProviderSelector({ onError, className = "" }: ProviderSelectorProps) {
  const [providers, setProviders] = useState<ProvidersResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const [isSwitching, setIsSwitching] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Initialize with default Groq provider (no API calls on mount)
  useEffect(() => {
    // Set default provider data without making API calls
    const defaultProviders: ProvidersResponse = {
      available_providers: ["groq", "openai", "anthropic"],
      current_provider: "groq",
      provider_status: {
        "groq": true,
        "openai": false,
        "anthropic": false
      }
    };
    
    setProviders(defaultProviders);
    setIsLoading(false);
    console.log('Using default Groq provider (no API call)');
  }, []);

  // Manual refresh providers (only when user requests it)
  const refreshProviders = async () => {
    try {
      setIsRefreshing(true);
      const providerData = await AIDesignAPI.getProviders();
      setProviders(providerData);
      console.log('Refreshed providers from API:', providerData);
    } catch (error) {
      console.error('Failed to refresh providers:', error);
      if (onError) {
        onError(error as APIError);
      }
    } finally {
      setIsRefreshing(false);
    }
  };

  // Handle provider switching
  const handleProviderSwitch = async (provider: string) => {
    try {
      setIsSwitching(true);
      console.log(`Switching to provider: ${provider}`);
      
      // For now, just update local state (offline mode)
      // Real API switching can be enabled by uncommenting the API calls below
      
      if (providers) {
        const updatedProviders = {
          ...providers,
          current_provider: provider
        };
        setProviders(updatedProviders);
        console.log(`Switched to ${provider} (offline mode)`);
        setIsExpanded(false);
        return;
      }
      
      // Uncomment below for real API switching:
      /*
      const result = await AIDesignAPI.switchProvider(provider);
      
      if (result.success) {
        // Reload providers to get updated current provider
        const updatedProviders = await AIDesignAPI.getProviders();
        setProviders(updatedProviders);
        console.log(`Successfully switched to ${provider}`);
        setIsExpanded(false); // Close dropdown
      } else {
        console.error('Provider switch failed:', result.error);
        if (onError) {
          onError({
            error: 'Provider Switch Failed',
            details: result.error
          });
        }
      }
      */
    } catch (error) {
      console.error('Error switching provider:', error);
      if (onError) {
        onError(error as APIError);
      }
    } finally {
      setIsSwitching(false);
    }
  };

  const getProviderIcon = (provider: string) => {
    switch (provider) {
      case 'openai':
        return '🤖';
      case 'anthropic':
        return '🔷';
      case 'groq':
        return '⚡';
      default:
        return '🤖';
    }
  };

  const getProviderName = (provider: string) => {
    switch (provider) {
      case 'openai':
        return 'OpenAI';
      case 'anthropic':
        return 'Anthropic';
      case 'groq':
        return 'Groq';
      default:
        return provider;
    }
  };

  if (isLoading) {
    return (
      <div className={`flex items-center gap-2 ${className}`}>
        <div className="animate-spin w-4 h-4 border-2 border-gray-300 border-t-blue-500 rounded-full"></div>
        <span className="text-sm text-gray-500">Loading providers...</span>
      </div>
    );
  }

  if (!providers) {
    return (
      <div className={`text-sm text-red-500 ${className}`}>
        ⚠️ Failed to load providers
      </div>
    );
  }

  return (
    <div className={`relative ${className}`}>
      {/* Current Provider Button */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-center gap-2 px-3 py-2 bg-white border border-gray-200 rounded-lg shadow-sm hover:bg-gray-50 transition-colors"
      >
        <span className="text-lg">
          {providers.current_provider ? 
            getProviderIcon(providers.current_provider) : 
            '🤖'
          }
        </span>
        <div className="flex flex-col items-start">
          <span className="text-sm font-medium text-gray-700">
            {providers.current_provider ? 
              getProviderName(providers.current_provider) : 
              'No Provider'
            }
          </span>
          <span className="text-xs text-gray-500">AI Provider</span>
        </div>
        <svg 
          className={`w-4 h-4 text-gray-400 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
          fill="none" 
          stroke="currentColor" 
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {/* Dropdown Menu */}
      {isExpanded && (
        <div className="absolute top-full left-0 mt-1 w-full bg-white border border-gray-200 rounded-lg shadow-lg z-50 min-w-48">
          <div className="py-1">
            {/* Header */}
            <div className="px-3 py-2 border-b border-gray-100">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-semibold text-gray-700">Available Providers</h3>
                  <p className="text-xs text-gray-500">
                    {providers.available_providers.length} providers configured (offline mode)
                  </p>
                </div>
                <button
                  onClick={refreshProviders}
                  disabled={isRefreshing}
                  className="text-xs bg-gray-100 hover:bg-gray-200 px-2 py-1 rounded flex items-center gap-1 disabled:opacity-50"
                  title="Refresh from backend"
                >
                  {isRefreshing ? '⏳' : '🔄'} Sync
                </button>
              </div>
            </div>

            {/* Provider List */}
            {Object.entries(providers.provider_status).map(([provider, isConfigured]) => (
              <button 
                key={provider}
                onClick={() => handleProviderSwitch(provider)}
                disabled={!isConfigured || provider === providers.current_provider || isSwitching}
                className={`w-full flex items-center justify-between px-3 py-2 transition-colors ${
                  provider === providers.current_provider 
                    ? 'bg-blue-50 cursor-default' 
                    : isConfigured && !isSwitching
                      ? 'hover:bg-gray-50 cursor-pointer' 
                      : 'opacity-50 cursor-not-allowed'
                }`}
              >
                <div className="flex items-center gap-2">
                  <span className="text-lg">{getProviderIcon(provider)}</span>
                  <div className="flex flex-col text-left">
                    <span className="text-sm font-medium text-gray-700">
                      {getProviderName(provider)}
                    </span>
                    <span className="text-xs text-gray-500">
                      {isConfigured ? 'Configured' : 'Not configured'}
                    </span>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {/* Status Indicator */}
                  <div className={`w-2 h-2 rounded-full ${
                    isConfigured ? 'bg-green-400' : 'bg-red-400'
                  }`} />
                  
                  {/* Current Provider Indicator */}
                  {provider === providers.current_provider && (
                    <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded">
                      Active
                    </span>
                  )}
                  
                  {/* Switching Indicator */}
                  {isSwitching && (
                    <div className="animate-spin w-3 h-3 border border-gray-300 border-t-blue-500 rounded-full"></div>
                  )}
                </div>
              </button>
            ))}

            {/* Footer */}
            <div className="px-3 py-2 border-t border-gray-100 bg-gray-50">
              <p className="text-xs text-gray-500">
                💡 Configure providers in your .env file to enable switching
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Click outside to close */}
      {isExpanded && (
        <div 
          className="fixed inset-0 z-40" 
          onClick={() => setIsExpanded(false)}
        />
      )}
    </div>
  );
}