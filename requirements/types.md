# TypeScript Type Definitions

This document outlines the shared TypeScript types used across the frontend and backend of the AYA Vision Detection Demo application.

## Core Types

### Analysis Settings
```typescript
interface AnalysisSettings {
  subject: string;
  initialPrompt: string;
  enhancedPrompt: string;
  maxFileSize: number;
  allowedFileTypes: string[];
}
```

### Image Analysis
```typescript
interface AnalysisResult {
  imageId: string;
  fileName: string;
  imageBase64: string;
  detected: boolean;
  confidence: number;
  processingTime: number;
  timestamp: string;
}

interface EnhancedAnalysisResult extends AnalysisResult {
  enhancedAnalysis: string;
  enhancedPrompt: string;
  enhancedProcessingTime: number;
}
```

### Progress Tracking
```typescript
type ProcessingStatus = 'pending' | 'processing' | 'completed' | 'error';

interface ProgressInfo {
  progressId: string;
  totalImages: number;
  processedImages: number;
  currentImage: string;
  status: ProcessingStatus;
  error: string | null;
  startTime: string;
  estimatedCompletionTime: string;
}

interface AnalysisProgress extends ProgressInfo {
  results: AnalysisResult[];
}

interface EnhancedAnalysisProgress extends ProgressInfo {
  results: EnhancedAnalysisResult[];
}
```

## UI State Types

### Filtering
```typescript
type FilterOption = 'all' | 'detected' | 'notDetected' | 'unknown';

interface FilterState {
  currentFilter: FilterOption;
  searchTerm: string;
  dateRange: {
    start: string | null;
    end: string | null;
  };
  confidenceThreshold: number;
}
```

### Sorting
```typescript
type SortField = 'fileName' | 'detectionStatus' | 'processingTime' | 'timestamp';
type SortOrder = 'asc' | 'desc';

interface SortState {
  field: SortField;
  order: SortOrder;
}
```

### Pagination
```typescript
interface PaginationState {
  currentPage: number;
  itemsPerPage: number;
  totalItems: number;
  totalPages: number;
}
```

## Debug Types

### Debug Log
```typescript
interface DebugLog {
  timestamp: string;
  level: 'info' | 'warn' | 'error' | 'debug';
  message: string;
  context: Record<string, any>;
  stackTrace?: string;
}
```

### Debug State
```typescript
interface DebugState {
  isEnabled: boolean;
  currentSettings: AnalysisSettings;
  activeFilters: FilterState;
  sortState: SortState;
  sessionStorage: Record<string, any>;
  logs: DebugLog[];
  performanceMetrics: {
    apiLatency: number[];
    imageProcessingTime: number[];
    memoryUsage: number[];
  };
}
```

## API Types

### Request Types
```typescript
interface AnalyzeImagesRequest {
  images: File[];
  settings?: Partial<AnalysisSettings>;
}

interface EnhancedAnalysisRequest {
  imageIds: string[];
  prompt: string;
}

interface UpdateSettingsRequest {
  subject: string;
  initialPrompt: string;
  enhancedPrompt: string;
}
```

### Response Types
```typescript
interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: {
    code: string;
    message: string;
    details?: Record<string, any>;
  };
}

interface PaginatedResponse<T> extends ApiResponse<T> {
  pagination: PaginationState;
}
```

## WebSocket Types

### WebSocket Events
```typescript
type WebSocketEventType = 
  | 'analysis_progress'
  | 'enhanced_analysis_progress'
  | 'error'
  | 'connection_status';

interface WebSocketEvent<T = any> {
  type: WebSocketEventType;
  data: T;
}

interface WebSocketConnectionState {
  isConnected: boolean;
  lastPing: string;
  reconnectAttempts: number;
  connectionId: string;
}
```

## Error Types

### Application Errors
```typescript
class ApplicationError extends Error {
  constructor(
    public code: string,
    message: string,
    public details?: Record<string, any>
  ) {
    super(message);
    this.name = 'ApplicationError';
  }
}

class ValidationError extends ApplicationError {
  constructor(message: string, details?: Record<string, any>) {
    super('VALIDATION_ERROR', message, details);
  }
}

class ApiError extends ApplicationError {
  constructor(
    message: string,
    public statusCode: number,
    details?: Record<string, any>
  ) {
    super('API_ERROR', message, details);
  }
}
```

## Utility Types

### File Types
```typescript
interface FileMetadata {
  name: string;
  size: number;
  type: string;
  lastModified: number;
  dimensions?: {
    width: number;
    height: number;
  };
}

interface ProcessedFile extends FileMetadata {
  id: string;
  url: string;
  thumbnailUrl: string;
  processingStatus: ProcessingStatus;
}
```

### Date Types
```typescript
interface DateRange {
  start: string;
  end: string;
}

interface TimeRange {
  start: number;
  end: number;
}
```

## Type Guards

```typescript
function isAnalysisResult(value: any): value is AnalysisResult {
  return (
    typeof value === 'object' &&
    'imageId' in value &&
    'fileName' in value &&
    'detected' in value
  );
}

function isEnhancedAnalysisResult(value: any): value is EnhancedAnalysisResult {
  return (
    isAnalysisResult(value) &&
    'enhancedAnalysis' in value &&
    'enhancedPrompt' in value
  );
}

function isWebSocketEvent(value: any): value is WebSocketEvent {
  return (
    typeof value === 'object' &&
    'type' in value &&
    'data' in value
  );
}
```

## Type Constants

```typescript
const PROCESSING_STATUS = {
  PENDING: 'pending',
  PROCESSING: 'processing',
  COMPLETED: 'completed',
  ERROR: 'error',
} as const;

const FILTER_OPTIONS = {
  ALL: 'all',
  DETECTED: 'detected',
  NOT_DETECTED: 'notDetected',
  UNKNOWN: 'unknown',
} as const;

const SORT_FIELDS = {
  FILE_NAME: 'fileName',
  DETECTION_STATUS: 'detectionStatus',
  PROCESSING_TIME: 'processingTime',
  TIMESTAMP: 'timestamp',
} as const;

const SORT_ORDERS = {
  ASC: 'asc',
  DESC: 'desc',
} as const;
``` 