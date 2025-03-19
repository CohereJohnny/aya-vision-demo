Product Requirements Document (PRD) - AYA Vision Flare Detection Demo

1. Introduction/Overview

Product Name: AYA Vision Detection Demo
Purpose: This application demonstrates the capabilities of Cohere's c4ai-aya-vision-32b model for image analysis, specifically in the context of detecting objects in imagery. It serves as a proof-of-concept and demonstration tool for Cohere Solution Engineers and Architects to showcase the model's potential to prospective customers.
Target Users: Cohere Solution Engineers, Solution Architects, and (indirectly) prospective Cohere customers.

2. Goals

Demonstrate the accuracy and speed of the c4ai-aya-vision-32b model in a real-world, visually-driven scenario.
Provide a simple, user-friendly interface for uploading and processing images.
Clearly display the results of the model's analysis in an easily understandable format.
Enable quick iteration and potential future expansion of features.
Showcase the model's capabilities for both binary classification and detailed generative analysis.
Support flexible configuration of detection subjects to demonstrate versatility.

3. Features

3.1  Image Upload:

Users can upload a batch of images simultaneously (configurable minimum: 1 for development, 40-50 for production).
Supported file formats: JPG, PNG, and other common image formats.
Upload method: File selection dialog (using HTML <input type="file" multiple>) and drag-and-drop functionality.
Error handling:
- Handle cases where the user uploads files that are not images.
- Handle cases where the user uploads too few or too many images. Provide clear error messages.
- Handle cases where the file size is too large (set a reasonable maximum file size limit per image and for the total upload).
Progress Tracking:
Display a comprehensive progress tracking system that monitors both upload and analysis phases:
  - Upload Phase (0-50%): Shows real-time upload progress with percentage, upload speed, and estimated time remaining.
  - Analysis Phase (50-100%): Shows real-time analysis progress as each image is processed, with current image name and completion count.
  - Status messages update dynamically to inform users about the current stage of processing.
  - Progress bar advances incrementally as each image is analyzed, providing accurate visual feedback.
  - Backend tracking system stores progress information for each batch with a unique progress ID.
  - Frontend polls the server at regular intervals to retrieve the latest progress information.
  - Handles potential network delays or processing bottlenecks with graceful UI updates.
  - Provides clear indication when processing is complete before redirecting to results page.

3.2 Two-Stage Analysis Pipeline:

The application implements a two-stage analysis pipeline:
  - Stage 1: Initial Analysis - Binary classification of all uploaded images
  - Stage 2: Enhanced Analysis - Detailed generative analysis of images that were positively identified in Stage 1

3.2.1 Initial Analysis (Stage 1):
Convert each uploaded image to Base64 encoding (required for the Cohere API).
Send each encoded image to the Cohere c4ai-aya-vision-32b model.
Prompt: The prompt is configurable through the Settings page. A default prompt is provided: "Is a [subject] in this image? Answer with only 'true' or 'false'."
Handle API responses and errors:
- Gracefully handle potential API errors (e.g., network issues, rate limits, model errors). Display informative error messages to the user.
- Implement retry logic (with exponential backoff) for transient errors.
- Log all API interactions (requests and responses) for debugging and analysis.

3.2.2 Enhanced Analysis (Stage 2):
Triggered by the user from the Initial Analysis results page.
Only processes images that were positively identified (True) in the Initial Analysis stage.
Uses a user-defined prompt for detailed generative analysis.
Provides a text field for users to enter a custom prompt for enhanced analysis.
Default enhanced analysis prompt: "Describe in detail what you see in this image, focusing on [subject]. Provide information about its appearance, surroundings, and any notable characteristics."
Displays a progress indicator during the enhanced analysis process.
Stores enhanced analysis results separately from initial analysis results.

3.3 Initial Results Display:

Present the results in a clear, grid-based format with cards for each image.
Each card includes:
- Image Thumbnail (small preview of the uploaded image).
- File Name.
- Detection Result (True/False) - This is the direct output from the model.
- Actions - Including a delete button to remove individual images from the collection.
Provide clear visual cues (e.g., green checkmark for "True," red X for "False") to improve readability.
Include an "Enhanced Analysis" button that is enabled when at least one image has been positively identified.

3.4 Enhanced Results Display:

Present the enhanced analysis results in a dedicated page.
Display only the images that were positively identified in the initial analysis.
Each card includes:
- Image Thumbnail (larger than in the initial results view).
- File Name.
- Enhanced Analysis Result - The detailed text response from the model.
- Option to expand/collapse the full analysis text.
Provide a way to navigate back to the initial results page.
Include options to copy or download the enhanced analysis results.

3.5 Filtering and Sorting:
Users can filter images by detection status (All, Objects Detected, No Objects, Unknown).
Users can sort images by filename (ascending or descending) or detection status (Yes to No or No to Yes).
Filter and sort controls are placed next to the "Detailed Results" header for easy access.
The filtering and sorting happen instantly without page reload.
The summary statistics remain unchanged when filtering to show the overall counts.
Visual indicators show the active filter and sort options.
The filter and sort state persists during the session until explicitly changed.
A filter info text displays the current filter and sort criteria to the user.
Filtering uses direct DOM manipulation for optimal performance.

3.6 Full-Size Image Viewing:
Users can click on any thumbnail to view the full-size image in a modal dialog.
The modal displays:
- The full-size image with proper scaling to fit the screen.
- The image filename.
- The detection result with appropriate visual indicators (green for detected, red for not detected).
- For enhanced analysis results, also display the detailed analysis text.
- A delete button for convenient image removal directly from the full-size view.
The modal is responsive and works well on different screen sizes.

3.7 Image Deletion:
Users can delete individual images from the collection after analysis.
Deletion can be performed from both the grid view and the full-size image view.
A confirmation dialog appears before deletion to prevent accidental removals.
The deletion is reflected immediately in the UI with a smooth animation.
The summary statistics (total images, objects detected, no objects) update automatically after deletion.
A toast notification confirms successful deletion.

3.8 Settings Configuration:
Users can access a dedicated Settings page from the main navigation.
The Settings page allows users to configure:
  - The detection subject (e.g., "Flare", "Building", "Vehicle") that will be used throughout the application.
  - The initial analysis prompt used for binary classification (with a default value provided).
  - The enhanced analysis prompt template used for detailed analysis (with a default value provided).
  - Text areas with sufficient space for writing detailed prompts.
  - A "Reset to Default" button to revert to the original settings.
  - A "Save" button to apply changes.
Settings are persisted between sessions.
Changes to settings apply to future image analyses but do not affect previously analyzed images.
Clear feedback is provided when settings are successfully saved.
The detection subject is used consistently throughout the application, including in the results display, filtering options, and sorting options.

3.9 User Interface (UI):
Simple and intuitive design focusing on usability.
Clear instructions for users at each step of the process.
Responsive design that works on different screen sizes.
Interactive elements with hover effects and visual feedback.
Smooth animations for card loading and image deletion.
Clear visual distinction between initial and enhanced analysis stages.
Card-based layout for displaying image results with consistent styling.
Contextual visual indicators (colors, icons) to indicate detection status.

3.10 Debug Mode:
A toggleable debug mode for troubleshooting and development purposes.
Debug panel that displays:
  - Current settings (subject, filter, sort)
  - Debug log with timestamped entries
  - Action buttons for resetting filters, clearing session storage, and reloading the page
Comprehensive logging of filtering and sorting operations.
Toggle button in the navigation bar for easy access.
Visual verification of DOM elements and data attributes.
Detailed tracking of visibility states for all result items.

4. Technical Design

Frontend:
HTML, CSS, JavaScript with modern ES6+ features.
Bootstrap 5 for responsive layout and UI components.
Font Awesome for icons and visual indicators.
Custom JavaScript for interactive features and AJAX requests.
Progress tracking using XMLHttpRequest for upload monitoring and fetch API for polling analysis progress.
Direct DOM manipulation for performance-critical operations like filtering.
Session storage for persisting user preferences.

Backend:
Python Flask framework with a modular architecture.
Cohere Python SDK for interacting with the c4ai-aya-vision-32b model.
Base64 encoding for image processing.
In-memory progress tracking system with unique IDs for each batch of images.
Progress callback mechanism for image processing functions.
Flask Blueprints for route organization.
WTForms for form validation and rendering.

API Interaction:
Cohere Python SDK for reliable API calls.
Asynchronous processing to prevent blocking the main thread during batch operations.
RESTful API endpoints for image analysis, deletion, and progress tracking.
Progress tracking API endpoint (/api/analysis-progress/<progress_id>) for retrieving real-time status.

Deployment:
Local development environment using Flask's built-in development server.
Production deployment considerations include:
  - Gunicorn/uWSGI as WSGI servers
  - Containerization (Docker) for easier deployment and portability
  - Environment variable configuration for sensitive data

Data Storage: 
In-memory storage for image analysis results (both initial and enhanced).
In-memory storage for progress tracking information with unique progress IDs.
Persistent storage (using Flask's session or a simple file-based solution) for user settings.

5. Prototype Scope and MVP

The MVP includes the following core functionality:
- User can upload a batch of images
- Images are analyzed using the Cohere model for binary classification
- Results are displayed in a grid format with appropriate visual indicators
- Users can trigger enhanced analysis on positively identified images
- Enhanced analysis results are displayed in a dedicated view
- Users can view full-size images by clicking on thumbnails
- Users can delete individual images from the collection
- Users can filter and sort images by detection status
- Users can configure the detection subject and prompts
- Comprehensive progress tracking with real-time updates
- Debugging tools for troubleshooting filtering and sorting issues
- Basic error handling and user feedback

6. Testing

Unit Tests:
- Test individual functions (e.g., Base64 encoding, API interaction, response parsing)
- Test utility functions for image processing and data handling
- Test form validation and error handling

Integration Tests:
- Test the flow from image upload to result display
- Test filtering and sorting functionality
- Test enhanced analysis workflow
- Test settings configuration and persistence

Manual Testing:
- Test with various image sets (including edge cases)
- Test filtering and sorting under different conditions
- Test with different detection subjects
- Test error handling and recovery

7. Future Considerations

Scalability:
- Implement a task queue (e.g., Celery) for asynchronous image processing
- Consider database storage for persistent results

Enhanced Features:
- Support for video input analysis
- Multiple configurable detection subjects in a single session
- Advanced filtering options (by confidence score, date, etc.)
- Batch operations on filtered results

Deployment:
- Containerized deployment with Docker
- Cloud platform hosting (AWS, GCP, Azure)
- CI/CD pipeline for automated testing and deployment

8. Success Metrics

Usability:
- Solution Engineers report ease of use
- Minimal training required to use effectively
- Interface is intuitive and self-explanatory

Accuracy:
- Model correctly identifies objects in images
- Low rate of false positives/negatives
- Enhanced analysis provides meaningful insights

Performance:
- Acceptable processing time per image
- Responsive UI even with many images
- Efficient filtering and sorting operations

Debug Effectiveness:
- Debug mode helps identify and resolve issues
- Filter and sort operations work consistently
- Session state persists correctly between page loads