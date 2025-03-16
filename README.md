# AYA Vision Detection Demo

A Flask-based web application that demonstrates the capabilities of Cohere's c4ai-aya-vision-32b model for object detection in images.

## Features

- **Configurable Detection Subject**: Set what you want to detect in images (e.g., flares, buildings, vehicles)
- **Image Upload**: Upload multiple images for batch processing
- **Image Analysis**: Process images using Cohere's c4ai-aya-vision-32b model
- **Results Display**: View detection results in a grid layout with thumbnails
- **Full-Size Image Viewing**: Click on thumbnails to view full-size images
- **Image Deletion**: Delete images from both grid and full-size views
- **Filtering and Sorting**: Filter and sort images by detection status
- **Responsive Design**: Works on desktop and mobile devices

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
   pip install -r requirements.txt
   ```

4. Set up your Cohere API key:
   ```
   export COHERE_API_KEY=your_api_key_here
   ```
   On Windows:
   ```
   set COHERE_API_KEY=your_api_key_here
   ```

## Usage

1. Start the application:
   ```
   python run.py
   ```

2. Open your web browser and navigate to:
   ```
   http://localhost:5001
   ```

3. Configure the detection subject and prompt in the Settings page

4. Upload images for analysis

5. View and interact with the results

## Project Structure

```
aya-vision-demo/
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── forms.py
│   ├── routes.py
│   ├── utils.py
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css
│   │   ├── js/
│   │   │   └── main.js
│   │   └── uploads/
│   └── templates/
│       ├── base.html
│       ├── index.html
│       ├── results.html
│       └── settings.html
├── requirements/
│   └── prd.md
├── requirements.txt
└── run.py
```

## Technologies Used

- **Flask**: Web framework
- **Cohere API**: For image analysis using the c4ai-aya-vision-32b model
- **Bootstrap 5**: For responsive design
- **Font Awesome**: For icons
- **JavaScript**: For interactive features

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- Cohere for providing the c4ai-aya-vision-32b model
- Flask community for the excellent web framework 