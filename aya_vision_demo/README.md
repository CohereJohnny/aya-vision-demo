# AYA Vision Detection Demo

A Flask-based web application that demonstrates the capabilities of Cohere's c4ai-aya-vision-32b model for image analysis, specifically designed for configurable object detection in images.

## Features

- **Configurable Detection Subject**: Set what you want to detect in images (e.g., flares, buildings, vehicles)
- **Two-Stage Analysis Pipeline**:
  - Stage 1: Initial binary classification ("Is a [subject] in this image?")
  - Stage 2: Enhanced detailed analysis for positively identified images
- **Image Upload**:
  - Support for multiple image upload
  - Drag-and-drop interface with live preview
  - File type validation and size checking
- **Real-time Progress Tracking**:
  - Upload progress (percentage, speed, estimated time)
  - Analysis progress (current image, completion count)
  - Dynamic status messages and visual progress indicators
- **Results Management**:
  - Card-based grid layout for image results
  - Visual indicators for detection status (green/red/gray)
  - Image deletion with confirmation and animation
  - Full-size image viewing in modal dialog
- **Advanced Filtering and Sorting**:
  - Filter by detection status (All, Detected, Not Detected, Unknown)
  - Sort by filename (A-Z, Z-A) or detection status
  - Session persistence for filter/sort preferences
  - Real-time DOM updates without page reload
- **Enhanced Analysis**:
  - Detailed generative descriptions for detected objects
  - Custom prompt support for targeted analysis
  - Expandable/collapsible analysis text
- **Settings Configuration**:
  - Configure detection subject
  - Customize prompts for both analysis stages
  - Settings persistence between sessions
- **Debug Mode**:
  - Toggleable debug interface
  - Real-time logging of filtering and sorting operations
  - Current state display (subject, filter, sort)
  - Debug actions (reset filters, clear storage, refresh)
- **Responsive UI**:
  - Mobile-friendly design
  - Bootstrap 5 components and layout
  - Smooth animations and transitions

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/aya-vision-demo.git
   cd aya-vision-demo
   ```

2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the required packages:
   ```
   pip install -r aya_vision_demo/requirements.txt
   ```

4. Create a `.env` file in the project root with the following content:
   ```
   FLASK_APP=run.py
   FLASK_CONFIG=development
   SECRET_KEY=your-secret-key
   COHERE_API_KEY=your-cohere-api-key
   LOG_LEVEL=INFO
   ```

## Usage

1. Start the Flask development server:
   ```
   cd aya_vision_demo
   python run.py
   ```

2. Open your web browser and navigate to:
   ```
   http://localhost:5001
   ```
   Note: The application runs on port 5001 by default to avoid conflicts with AirPlay on macOS.

3. Configuration:
   - Click on "Settings" in the navigation bar
   - Set your detection subject (e.g., "Flare", "Building", "Vehicle")
   - Customize the prompts for initial and enhanced analysis
   - Save your settings

4. Upload and analyze images:
   - Use the upload form on the main page
   - Drag and drop images or use the file selector
   - Track the upload and analysis progress
   - View results in the grid layout

5. Filter and sort results:
   - Use the filter dropdown to show specific detection categories
   - Use the sort dropdown to change the display order
   - Filter information will be displayed above the results

6. Enhanced analysis:
   - For images with detected objects, click the "Enhanced Analysis" button
   - Enter a custom prompt or use the default
   - View detailed descriptions for each detected object

7. Debugging (optional):
   - Toggle debug mode by clicking "Debug" in the navigation bar
   - Use the debug panel to track filtering and sorting operations
   - Reset filters or clear session storage as needed

## Docker Deployment

You can run the AYA Vision Detection Demo as a containerized application using Docker for easier deployment and consistency across environments.

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) installed on your system
- A valid Cohere API key

### Building and Running the Container

1. **Build the Docker image**:
   ```bash
   # From the project root directory (where the Dockerfile is located)
   docker build -t aya-vision-demo .
   ```
   This command builds a Docker image named "aya-vision-demo" based on the Dockerfile.

2. **Run the container**:
   ```bash
   docker run -d -p 5001:5001 \
     -e COHERE_API_KEY=your-cohere-api-key \
     -e SECRET_KEY=your-secure-secret-key \
     -e FLASK_CONFIG=production \
     --name aya-vision-app \
     aya-vision-demo
   ```
   Replace `your-cohere-api-key` and `your-secure-secret-key` with your actual values.

   Parameters explained:
   - `-d`: Run in detached mode (background)
   - `-p 5001:5001`: Map port 5001 from the container to port 5001 on the host
   - `-e`: Set environment variables
   - `--name`: Assign a name to the container

3. **Access the application**:
   Open your browser and navigate to:
   ```
   http://localhost:5001
   ```

### Docker Management Commands

- **View logs**:
  ```bash
  docker logs aya-vision-app
  ```
  Add `-f` flag to follow the logs in real-time:
  ```bash
  docker logs -f aya-vision-app
  ```

- **Stop the container**:
  ```bash
  docker stop aya-vision-app
  ```

- **Restart the container**:
  ```bash
  docker restart aya-vision-app
  ```

- **Remove the container** (must be stopped first):
  ```bash
  docker rm aya-vision-app
  ```

### Custom Configuration

- **Change the port mapping**:
  ```bash
  docker run -d -p 8080:5001 -e COHERE_API_KEY=your-key -e SECRET_KEY=your-secret --name aya-vision-app aya-vision-demo
  ```
  This maps the container's port 5001 to the host's port 8080.

- **Use a volume for persistent data** (if you've added persistence to the app):
  ```bash
  docker run -d -p 5001:5001 \
    -v $(pwd)/data:/app/data \
    -e COHERE_API_KEY=your-key \
    -e SECRET_KEY=your-secret \
    --name aya-vision-app \
    aya-vision-demo
  ```

- **Run in development mode**:
  ```bash
  docker run -d -p 5001:5001 \
    -e COHERE_API_KEY=your-key \
    -e SECRET_KEY=your-secret \
    -e FLASK_CONFIG=development \
    --name aya-vision-app \
    aya-vision-demo
  ```

### Docker Compose (Optional)

For easier management, you can create a `docker-compose.yml` file in the project root:

```yaml
version: '3'

services:
  aya-vision-app:
    build: .
    container_name: aya-vision-app
    ports:
      - "5001:5001"
    environment:
      - COHERE_API_KEY=your-cohere-api-key
      - SECRET_KEY=your-secure-secret-key
      - FLASK_CONFIG=production
    restart: unless-stopped
```

Then run:
```bash
docker-compose up -d
```

And to stop:
```bash
docker-compose down
```

## Project Structure

```
aya-vision-demo/
├── app/                      # Main application package
│   ├── __init__.py           # Flask app initialization
│   ├── routes.py             # View functions and API endpoints
│   ├── utils.py              # Utility functions
│   ├── forms.py              # WTForms definitions
│   ├── static/               # Static assets
│   │   ├── css/              # CSS styles
│   │   ├── js/               # JavaScript files
│   │   └── img/              # Images and icons
│   └── templates/            # Jinja2 HTML templates
│       ├── base.html         # Base template with layout
│       ├── index.html        # Upload page
│       ├── results.html      # Results display
│       ├── settings.html     # Settings configuration
│       ├── enhanced_analysis.html    # Enhanced analysis
│       ├── analysis_progress.html    # Progress tracking
│       └── errors/           # Error pages
├── config.py                 # Configuration settings
├── requirements.txt          # Dependencies
├── requirements/             # Documentation
│   └── prd.md                # Product Requirements Document
├── .env                      # Environment variables (not in repo)
├── Dockerfile                # Container definition for Docker
└── run.py                    # Application entry point
```

## API Usage

The application provides RESTful API endpoints:

```
POST /api/analyze
```
Uploads and analyzes images

```
GET /api/analysis-progress/<progress_id>
```
Retrieves progress information for a batch

```
DELETE /api/delete_image/<image_index>
```
Deletes an image from the results

```
POST /api/enhanced-analysis
```
Triggers enhanced analysis for detected objects

## Technologies Used

- **Frontend**:
  - HTML5, CSS3, JavaScript (ES6+)
  - Bootstrap 5 for responsive design
  - Font Awesome for icons
  - Fetch API for AJAX requests
  - XMLHttpRequest for upload progress tracking
  - Session storage for state persistence

- **Backend**:
  - Python 3.8+
  - Flask web framework
  - Flask-WTF for form handling
  - Cohere Python SDK
  - Base64 for image encoding
  - Unique IDs for progress tracking

## Development and Debugging

- Enable debug mode by clicking the "Debug" toggle in the navigation bar
- Use the debug panel on the results page to:
  - View current settings (subject, filter, sort)
  - Reset filters to default values
  - Clear session storage
  - View detailed logs of filtering and sorting operations
- Debug logs show:
  - DOM element details
  - Filter/sort operations
  - Visibility status of each item

## License

This project is licensed under the MIT License.

## Acknowledgements

- Cohere for providing the c4ai-aya-vision-32b model
- The Flask community for the excellent web framework
- Bootstrap team for the responsive UI components
