# API Endpoints Specification

This document outlines the API contract between the frontend and backend components of the AYA Vision Detection Demo application.

## Base URL

```
/api/v1
```

## Authentication

All endpoints require a valid JWT token in the Authorization header:
```
Authorization: Bearer <jwt_token>
```

## Endpoints

### 1. Image Analysis

#### Upload and Analyze Images
```http
POST /analyze
Content-Type: multipart/form-data

Request:
- images: File[] (multiple image files)
- settings: AnalysisSettings (optional)

Response:
{
  "progressId": string,
  "totalImages": number,
  "status": "processing"
}
```

#### Get Analysis Progress
```http
GET /analyze/progress/{progressId}

Response:
{
  "progressId": string,
  "totalImages": number,
  "processedImages": number,
  "currentImage": string,
  "status": "processing" | "completed" | "error",
  "results": AnalysisResult[],
  "error": string | null
}
```

### 2. Enhanced Analysis

#### Trigger Enhanced Analysis
```http
POST /enhanced-analysis
Content-Type: application/json

Request:
{
  "imageIds": string[],
  "prompt": string
}

Response:
{
  "analysisId": string,
  "totalImages": number,
  "status": "processing"
}
```

#### Get Enhanced Analysis Progress
```http
GET /enhanced-analysis/progress/{analysisId}

Response:
{
  "analysisId": string,
  "totalImages": number,
  "processedImages": number,
  "currentImage": string,
  "status": "processing" | "completed" | "error",
  "results": EnhancedAnalysisResult[],
  "error": string | null
}
```

### 3. Image Management

#### Delete Image
```http
DELETE /images/{imageId}

Response:
{
  "success": boolean,
  "message": string
}
```

#### Get Image Details
```http
GET /images/{imageId}

Response:
{
  "imageId": string,
  "fileName": string,
  "uploadDate": string,
  "analysisStatus": "pending" | "completed" | "error",
  "detectionResult": boolean | null,
  "enhancedAnalysis": string | null
}
```

### 4. Settings Management

#### Get Settings
```http
GET /settings

Response:
{
  "subject": string,
  "initialPrompt": string,
  "enhancedPrompt": string,
  "maxFileSize": number,
  "allowedFileTypes": string[]
}
```

#### Update Settings
```http
PUT /settings
Content-Type: application/json

Request:
{
  "subject": string,
  "initialPrompt": string,
  "enhancedPrompt": string
}

Response:
{
  "success": boolean,
  "message": string,
  "settings": Settings
}
```

### 5. Debug Information

#### Get Debug Information
```http
GET /debug/info

Response:
{
  "currentSettings": Settings,
  "activeFilters": FilterState,
  "sortState": SortState,
  "sessionStorage": Record<string, any>,
  "logs": DebugLog[]
}
```

#### Clear Debug Data
```http
POST /debug/clear

Response:
{
  "success": boolean,
  "message": string
}
```

## Error Responses

All endpoints may return the following error responses:

```http
// 400 Bad Request
{
  "error": "Bad Request",
  "message": string,
  "details": object
}

// 401 Unauthorized
{
  "error": "Unauthorized",
  "message": "Invalid or missing authentication token"
}

// 403 Forbidden
{
  "error": "Forbidden",
  "message": "Insufficient permissions"
}

// 404 Not Found
{
  "error": "Not Found",
  "message": "Resource not found"
}

// 413 Payload Too Large
{
  "error": "Payload Too Large",
  "message": "File size exceeds maximum allowed"
}

// 415 Unsupported Media Type
{
  "error": "Unsupported Media Type",
  "message": "File type not supported"
}

// 429 Too Many Requests
{
  "error": "Too Many Requests",
  "message": "Rate limit exceeded",
  "retryAfter": number
}

// 500 Internal Server Error
{
  "error": "Internal Server Error",
  "message": "An unexpected error occurred"
}
```

## Rate Limiting

- All endpoints are rate limited to 100 requests per minute per IP address
- Rate limit headers are included in all responses:
  ```
  X-RateLimit-Limit: 100
  X-RateLimit-Remaining: 99
  X-RateLimit-Reset: 1623456789
  ```

## WebSocket Events

For real-time progress updates, the application uses WebSocket connections:

```typescript
// Connection URL
ws://api.example.com/ws

// Events
{
  "type": "analysis_progress",
  "data": {
    "progressId": string,
    "processedImages": number,
    "totalImages": number,
    "currentImage": string,
    "status": string
  }
}

{
  "type": "enhanced_analysis_progress",
  "data": {
    "analysisId": string,
    "processedImages": number,
    "totalImages": number,
    "currentImage": string,
    "status": string
  }
}
```

## Versioning

The API is versioned through the URL path:
- Current version: v1
- Future versions will be released as v2, v3, etc.
- Each version will maintain backward compatibility for at least 12 months after the release of a new version. 