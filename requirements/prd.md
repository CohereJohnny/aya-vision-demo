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
3. Features

3.1  Image Upload:

Users can upload a batch of 40-50 images simultaneously.
Supported file formats: JPG, PNG (and potentially other common image formats; specify if needed).
Upload method: File selection dialog (using HTML <input type="file" multiple>) and drag-and-drop functionality (for a better user experience).
Error handling:
Handle cases where the user uploads files that are not images.
Handle cases where the user uploads too few or too many images (enforce the 40-50 image range). Provide clear error messages.
Handle cases where the file size is too large (set a reasonable maximum file size limit per image and for the total upload).
Progress Indicator: Display a progress bar or similar indicator during the upload and processing phase.
3.2 Two-Stage Analysis Pipeline:

The application implements a two-stage analysis pipeline:
  - Stage 1: Initial Analysis - Binary classification of all uploaded images
  - Stage 2: Enhanced Analysis - Detailed generative analysis of images that were positively identified in Stage 1

3.2.1 Initial Analysis (Stage 1):
Convert each uploaded image to Base64 encoding (required for the Cohere API). This should happen in the backend (Flask).
Send each encoded image to the Cohere c4ai-aya-vision-32b model.
Prompt: The prompt is configurable through the Settings page. A default prompt is provided: "Is a flare burning in this image? Answer with only 'true' or 'false'."
Handle API responses and errors:
Gracefully handle potential API errors (e.g., network issues, rate limits, model errors). Display informative error messages to the user.
Implement retry logic (with exponential backoff) for transient errors.
Log all API interactions (requests and responses) for debugging and analysis.

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
Image Thumbnail (small preview of the uploaded image).
File Name.
Detection Result (True/False) - This is the direct output from the model.
Actions - Including a delete button to remove individual images from the collection.
Provide clear visual cues (e.g., green checkmark for "True," red X for "False") to improve readability.
Include an "Enhanced Analysis" button that is enabled when at least one image has been positively identified.

3.4 Enhanced Results Display:

Present the enhanced analysis results in a dedicated page.
Display only the images that were positively identified in the initial analysis.
Each card includes:
Image Thumbnail (larger than in the initial results view).
File Name.
Enhanced Analysis Result - The detailed text response from the model.
Option to expand/collapse the full analysis text.
Provide a way to navigate back to the initial results page.
Include options to copy or download the enhanced analysis results.

3.5 Filtering and Sorting:
Users can filter images by detection status (All, Objects Detected, No Objects, Unknown).
Users can sort images by filename or detection status.
Filter and sort controls are placed next to the "Detailed Results" header for easy access.
The filtering and sorting happen instantly without page reload.
The summary statistics remain unchanged when filtering to show the overall counts.
Visual indicators show the active filter and sort options.
The filter and sort state persists during the session until explicitly changed.

3.6 Full-Size Image Viewing:
Users can click on any thumbnail to view the full-size image in a modal dialog.
The modal displays:
The full-size image with proper scaling to fit the screen.
The image filename.
The detection result with appropriate visual indicators (green for detected, red for not detected).
For enhanced analysis results, also display the detailed analysis text.
A delete button for convenient image removal directly from the full-size view.
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

Simple and intuitive design. Focus on usability.
Clear instructions for the user (e.g., "Upload 40-50 images for analysis").
Responsive design (should work reasonably well on different screen sizes, but this is not a primary focus for the prototype).
Interactive elements with hover effects and visual feedback.
Smooth animations for card loading and image deletion.
Clear visual distinction between initial and enhanced analysis stages.
4.  Technical Design

Frontend:
HTML, CSS, JavaScript. Consider a lightweight JavaScript library like Dropzone.js for drag-and-drop functionality.
Bootstrap 5 for responsive layout and UI components.
Font Awesome for icons and visual indicators.
Custom JavaScript for interactive features and AJAX requests.
Backend:
Python Flask framework.
Cohere Python SDK (for interacting with the c4ai-aya-vision-32b model).
Base64 encoding library (built-in to Python).
API Interaction:
Use the Cohere Python SDK to make API calls.
Asynchronous requests (consider using async and await if the Cohere SDK supports it, or threading/multiprocessing if not, to prevent blocking the main thread). This is important for handling the batch processing without freezing the UI.
RESTful API endpoints for image analysis and deletion.
Deployment (Initial):
Local development environment (Flask's built-in development server).
Future: Consider containerization (Docker) for easier deployment and portability.
Data Storage: 
In-memory storage for image analysis results (both initial and enhanced).
Persistent storage (using Flask's session or a simple file-based solution) for user settings.
5.  Prototype Scope and MVP (Minimum Viable Product)

The MVP will focus on the core functionality:

User can upload a batch of images.
Images are sent to the Cohere model for initial analysis (binary classification).
Initial results (True/False) are displayed in a grid format.
Users can trigger enhanced analysis on positively identified images.
Enhanced analysis results are displayed in a dedicated view.
Users can view full-size images by clicking on thumbnails.
Users can delete individual images from the collection.
Users can filter and sort images by detection status.
Users can configure the detection subject and prompts used for both analysis stages.
Basic error handling is implemented.
The following are NOT in the MVP, but are good candidates for future iterations:

User authentication.
Image persistence (saving images to a database or cloud storage).
Detailed model confidence scores.
Advanced UI features (e.g., image zooming, advanced filtering).
Support for video input.
Multiple configurable prompts for different analysis types.
6.  Testing

Unit Tests: Test individual functions (e.g., Base64 encoding, API interaction, response parsing).
Integration Tests: Test the flow from image upload to result display for both analysis stages.
Manual Testing: Thoroughly test the application with various image sets (including edge cases and images that might be difficult to classify).
User Acceptance Testing (UAT): Have Cohere Solution Engineers use the application and provide feedback.
7.  Future Considerations

Scalability: If the application needs to handle a significantly larger number of images or users, consider using a task queue (e.g., Celery) to manage the image processing asynchronously.
Monitoring: Implement logging and monitoring to track API usage, error rates, and performance.
Deployment: Explore deployment options like cloud platforms (AWS, GCP, Azure) for wider accessibility.
8.  Success Metrics

Usability: Solution Engineers find the application easy to use and understand.
Accuracy: The model correctly identifies objects in the images (qualitative assessment during demos).
Performance: The application processes images and displays results within an acceptable timeframe (aim for a few seconds per image, but this depends on the Cohere API's latency).
Value of Enhanced Analysis: The enhanced analysis provides meaningful and insightful information beyond the binary classification.