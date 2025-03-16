aya_vision_demo/          # Root directory of your project
├── app/                 # Main application package
│   ├── __init__.py      # Initializes the Flask app, configurations, etc.
│   ├── models.py        # (Optional) For database models, if you add persistence later.
│   ├── routes.py        # Defines the application's routes and view functions.
│   ├── forms.py         # (Optional) For WTForms or similar form handling.
│   ├── utils.py         # Utility functions (e.g., Base64 encoding, API interaction).
│   ├── templates/       # HTML templates
│   │   ├── base.html    # Base template with common elements (layout, navbar, etc.).
│   │   ├── index.html   # Main page for image upload and results display.
│   │   ├── results.html # (Optional) Separate template for displaying results.
│   │   └── errors/      # (Optional) For custom error pages (e.g., 404, 500)
│   │       ├── 404.html
│   │       └── 500.html
│   └── static/          # Static files (CSS, JavaScript, images)
│       ├── css/
│       │   └── style.css  # Main stylesheet.
│       ├── js/
│       │   └── main.js    # Custom JavaScript (e.g., for drag-and-drop, progress bar).
│       └── img/         # (Optional) For any static images used in the UI.
├── config.py            # Configuration settings (e.g., API keys, debug mode).
├── run.py             # Script to start the Flask development server.
├── requirements.txt    # Lists project dependencies (Flask, Cohere SDK, etc.).
├── tests/              # (Highly recommended) Unit and integration tests
│   ├── __init__.py
│   ├── conftest.py     # (Optional) pytest configuration and fixtures
│   ├── test_utils.py    # Tests for utility functions
│   ├── test_routes.py   # Tests for routes and view functions
│   └── test_models.py  # (Optional) Tests for database models
├── .env                # (Optional, but recommended) Environment variables (e.g., API keys).
├── README.md           # Project description and instructions.
└── .gitignore          # Specifies intentionally untracked files (e.g., .env, __pycache__).