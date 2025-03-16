# AYA Vision Flare Detection Demo

A Flask-based web application that demonstrates the capabilities of Cohere's c4ai-aya-vision-32b model for image analysis, specifically in detecting burning flares in oil field imagery.

## Features

- Upload multiple images (40-50 for production use)
- Drag-and-drop interface for easy image uploading
- Real-time image analysis using Cohere's c4ai-aya-vision-32b model
- Clear visualization of results with thumbnails and status indicators
- Summary statistics of detection results
- Image deletion capability to remove individual images from the collection
- RESTful API endpoint for programmatic access

## Requirements

- Python 3.8+
- Flask 2.3.3
- Cohere API key

## Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd aya-vision-demo
   ```

2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the dependencies:
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

3. Upload images using the web interface and view the results.

## API Usage

The application provides RESTful API endpoints for programmatic access:

```
POST /api/analyze
```

Example using curl:
```
curl -X POST -F "images=@image1.jpg" -F "images=@image2.jpg" http://localhost:5001/api/analyze
```

Response format:
```json
{
  "results": [
    {
      "filename": "image1.jpg",
      "flare_detected": true,
      "success": true,
      "error": null
    },
    {
      "filename": "image2.jpg",
      "flare_detected": false,
      "success": true,
      "error": null
    }
  ]
}
```

```
DELETE /api/delete_image/<image_index>?result_id=<result_id>
```

Example using curl:
```
curl -X DELETE "http://localhost:5001/api/delete_image/0?result_id=your-result-id"
```

Response format:
```json
{
  "success": true,
  "message": "Image image1.jpg deleted successfully",
  "remaining_count": 1,
  "results": [
    {
      "filename": "image2.jpg",
      "flare_detected": false,
      "success": true,
      "error": null
    }
  ]
}
```

## Configuration

The application has three configuration environments:

- Development: For local development (default)
- Testing: For running tests
- Production: For deployment

You can change the environment by setting the `FLASK_CONFIG` environment variable.

## Implementation Notes

- The application uses an in-memory storage for results instead of Flask's session to avoid size limitations when handling multiple images.
- For a production deployment, this should be replaced with a proper database.
- The default minimum number of images is set to 1 for development, but can be configured to 40-50 for production as per the PRD.

## Testing

Run the tests using pytest:
```
cd aya_vision_demo
pytest
```

## Deployment

For production deployment, set the following environment variables:
```
FLASK_CONFIG=production
SECRET_KEY=your-secure-secret-key
COHERE_API_KEY=your-cohere-api-key
```

## License

This project is for demonstration purposes only and is not licensed for public use.
