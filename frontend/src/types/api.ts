/**
 * TypeScript types for AI Design Copilot API
 * Following backend Pydantic models
 */

export type NodeType = 
  | "client" 
  | "webserver" 
  | "api-gateway" 
  | "cache" 
  | "database" 
  | "worker" 
  | "queue" 
  | "storage";

export type EdgeType = 
  | "requests" 
  | "reads-from" 
  | "writes-to" 
  | "sends-message" 
  | "connects-to" 
  | "depends-on";

export interface Node {
  type: NodeType;
  label: string;
  id?: string;
}

export interface Edge {
  from: string;
  to: string;
  type: EdgeType;
  label?: string;
}

export interface Suggestion {
  nodes: Node[];
  edges: Edge[];
}

export interface SuggestionResponse {
  suggestion: Suggestion | null;
  reasoning: string;
  reference: string | null;
}

export interface CanvasRequest {
  canvas_elements: ExcalidrawElement[];
  recent_changes?: any[];
  context?: Record<string, any>;
}

export interface ExcalidrawElement {
  id: string;
  type: string;
  x: number;
  y: number;
  width: number;
  height: number;
  text?: string;
  [key: string]: any;
}

export interface APIError {
  error: string;
  details?: string;
  request_id?: string;
}

export interface HealthResponse {
  status: string;
  service?: string;
  patterns_loaded?: number;
}