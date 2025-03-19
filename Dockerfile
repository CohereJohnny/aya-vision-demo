FROM python:3.9-slim

WORKDIR /app

# Copy requirements first for better caching
COPY aya_vision_demo/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn

# Copy application code
COPY aya_vision_demo/ .

# Environment variables
ENV FLASK_APP=run.py
ENV FLASK_CONFIG=production
ENV MIN_IMAGES=40
ENV MAX_IMAGES=50
ENV LOG_LEVEL=WARNING

# Run gunicorn
EXPOSE 5001
CMD ["gunicorn", "--bind", "0.0.0.0:5001", "--workers", "4", "--timeout", "120", "run:app"]