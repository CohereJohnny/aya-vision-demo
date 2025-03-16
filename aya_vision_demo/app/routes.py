import io
import os
import uuid
import time
from flask import (
    Blueprint, render_template, request, redirect, 
    url_for, flash, current_app, session, jsonify
)
from werkzeug.utils import secure_filename
from app.forms import ImageUploadForm, SettingsForm
from app.utils import (
    is_valid_file_extension, process_image_batch
)

# Create a blueprint for the main routes
main_bp = Blueprint('main', __name__)

# In-memory storage for results (in a production app, this would be a database)
results_storage = {}

# Default settings
DEFAULT_PROMPT = "Is a flare burning in this image? Answer with only 'true' or 'false'."
DEFAULT_SUBJECT = "Flare"

@main_bp.route('/', methods=['GET', 'POST'])
def index():
    """
    Handle the index page with image upload form.
    
    Returns:
        str: Rendered HTML template
    """
    form = ImageUploadForm()
    
    if form.validate_on_submit():
        # Get the uploaded files
        uploaded_files = request.files.getlist('images')
        
        # Validate the number of files
        if len(uploaded_files) < current_app.config['MIN_IMAGES']:
            flash(f"Please upload at least {current_app.config['MIN_IMAGES']} images.", 'error')
            return render_template('index.html', form=form)
        
        if len(uploaded_files) > current_app.config['MAX_IMAGES']:
            flash(f"Please upload no more than {current_app.config['MAX_IMAGES']} images.", 'error')
            return render_template('index.html', form=form)
        
        # Validate file extensions
        valid_files = []
        for file in uploaded_files:
            if file.filename == '':
                continue
                
            if not is_valid_file_extension(file.filename, current_app.config['UPLOAD_EXTENSIONS']):
                flash(f"File {file.filename} has an invalid extension. Allowed extensions: {', '.join(current_app.config['UPLOAD_EXTENSIONS'])}", 'error')
                return render_template('index.html', form=form)
            
            # Read the file data
            file_data = file.read()
            file.seek(0)  # Reset file pointer for potential future use
            
            valid_files.append({
                'filename': secure_filename(file.filename),
                'data': file_data
            })
        
        if not valid_files:
            flash("No valid files were uploaded.", 'error')
            return render_template('index.html', form=form)
        
        # Process the images
        try:
            # Log the start of processing
            current_app.logger.info(f"Starting to process {len(valid_files)} images with Cohere API")
            start_time = time.time()
            
            # Get the custom prompt from session or use the default
            custom_prompt = session.get('custom_prompt', current_app.config['PROMPT'])
            
            # Process the batch of images using Cohere's Chat V2 API
            results = process_image_batch(
                images=valid_files,
                api_key=current_app.config['COHERE_API_KEY'],
                model_name=current_app.config['MODEL_NAME'],
                prompt=custom_prompt
            )
            
            # Log processing completion
            processing_time = time.time() - start_time
            current_app.logger.info(f"Completed processing {len(valid_files)} images in {processing_time:.2f} seconds")
            
            # Get the subject from session or use the default
            subject = session.get('custom_subject', DEFAULT_SUBJECT)
            
            # Count successful detections
            detected = sum(1 for r in results if r['detection_result'] is True)
            not_detected = sum(1 for r in results if r['detection_result'] is False)
            unknown = sum(1 for r in results if r['detection_result'] is None)
            
            current_app.logger.info(f"Results summary: {detected} {subject}s detected, {not_detected} no {subject}s, {unknown} unknown")
            
            # Generate a unique ID for this batch of results
            result_id = str(uuid.uuid4())
            
            # Store results in server-side storage
            results_storage[result_id] = {
                'results': results,
                'subject': subject  # Store the subject with the results
            }
            
            # Store only the result ID in the session
            session['result_id'] = result_id
            
            # Redirect to results page
            return redirect(url_for('main.results'))
            
        except Exception as e:
            current_app.logger.error(f"Error processing images: {str(e)}")
            flash(f"An error occurred while processing the images: {str(e)}", 'error')
            return render_template('index.html', form=form)
    
    return render_template('index.html', form=form)

@main_bp.route('/settings', methods=['GET', 'POST'])
def settings():
    """
    Handle the settings page for configuring application parameters.
    
    Returns:
        str: Rendered HTML template
    """
    # Initialize the form with the current custom settings or the defaults
    form = SettingsForm(
        prompt=session.get('custom_prompt', DEFAULT_PROMPT),
        subject=session.get('custom_subject', DEFAULT_SUBJECT)
    )
    
    if form.validate_on_submit():
        if 'submit' in request.form:
            # Save the custom settings to the session
            session['custom_prompt'] = form.prompt.data
            session['custom_subject'] = form.subject.data
            current_app.logger.info(f"Updated custom prompt: {form.prompt.data}")
            current_app.logger.info(f"Updated custom subject: {form.subject.data}")
            flash("Settings saved successfully!", 'success')
        elif 'reset' in request.form:
            # Reset to default settings
            session['custom_prompt'] = DEFAULT_PROMPT
            session['custom_subject'] = DEFAULT_SUBJECT
            form.prompt.data = DEFAULT_PROMPT
            form.subject.data = DEFAULT_SUBJECT
            current_app.logger.info("Reset to default settings")
            flash("Settings reset to default values.", 'info')
    
    return render_template('settings.html', form=form)

@main_bp.route('/results')
def results():
    """
    Display the results of the image analysis.
    
    Returns:
        str: Rendered HTML template
    """
    # Get result ID from session
    result_id = session.get('result_id')
    
    # Get results from storage
    result_data = results_storage.get(result_id, {})
    results = result_data.get('results', [])
    subject = result_data.get('subject', session.get('custom_subject', DEFAULT_SUBJECT))
    
    if not results:
        flash("No results to display. Please upload images first.", 'warning')
        return redirect(url_for('main.index'))
    
    return render_template('results.html', results=results, subject=subject)

@main_bp.route('/delete_image/<int:image_index>', methods=['POST'])
def delete_image(image_index):
    """
    Delete an image from the results collection.
    
    Args:
        image_index: Index of the image to delete
        
    Returns:
        flask.Response: JSON response indicating success or failure
    """
    # Get result ID from session
    result_id = session.get('result_id')
    
    # Get results from storage
    result_data = results_storage.get(result_id, {})
    results = result_data.get('results', [])
    
    # Check if the index is valid
    if not results or image_index < 0 or image_index >= len(results):
        current_app.logger.warning(f"Invalid image index for deletion: {image_index}")
        return jsonify({'success': False, 'error': 'Invalid image index'}), 400
    
    try:
        # Remove the image from the results
        current_app.logger.info(f"Deleting image {results[image_index]['filename']} at index {image_index}")
        deleted_image = results.pop(image_index)
        
        # Update the results in storage
        results_storage[result_id]['results'] = results
        
        # Return success response
        return jsonify({
            'success': True, 
            'message': f"Image {deleted_image['filename']} deleted successfully",
            'remaining_count': len(results)
        }), 200
    except Exception as e:
        current_app.logger.error(f"Error deleting image: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@main_bp.route('/api/analyze', methods=['POST'])
def api_analyze():
    """
    API endpoint for analyzing images.
    
    Returns:
        flask.Response: JSON response with analysis results
    """
    # Check if files were uploaded
    if 'images' not in request.files:
        return jsonify({'error': 'No files uploaded'}), 400
    
    uploaded_files = request.files.getlist('images')
    
    # Validate the number of files
    if len(uploaded_files) < current_app.config['MIN_IMAGES']:
        return jsonify({'error': f"Please upload at least {current_app.config['MIN_IMAGES']} images."}), 400
    
    if len(uploaded_files) > current_app.config['MAX_IMAGES']:
        return jsonify({'error': f"Please upload no more than {current_app.config['MAX_IMAGES']} images."}), 400
    
    # Validate file extensions
    valid_files = []
    for file in uploaded_files:
        if file.filename == '':
            continue
            
        if not is_valid_file_extension(file.filename, current_app.config['UPLOAD_EXTENSIONS']):
            return jsonify({'error': f"File {file.filename} has an invalid extension. Allowed extensions: {', '.join(current_app.config['UPLOAD_EXTENSIONS'])}"}), 400
        
        # Read the file data
        file_data = file.read()
        file.seek(0)  # Reset file pointer for potential future use
        
        valid_files.append({
            'filename': secure_filename(file.filename),
            'data': file_data
        })
    
    if not valid_files:
        return jsonify({'error': "No valid files were uploaded."}), 400
    
    # Process the images
    try:
        # Log the start of processing
        current_app.logger.info(f"API: Starting to process {len(valid_files)} images with Cohere API")
        start_time = time.time()
        
        # Get the custom prompt from session or use the default
        custom_prompt = session.get('custom_prompt', current_app.config['PROMPT'])
        
        # Process the batch of images using Cohere's Chat V2 API
        results = process_image_batch(
            images=valid_files,
            api_key=current_app.config['COHERE_API_KEY'],
            model_name=current_app.config['MODEL_NAME'],
            prompt=custom_prompt
        )
        
        # Log processing completion
        processing_time = time.time() - start_time
        current_app.logger.info(f"API: Completed processing {len(valid_files)} images in {processing_time:.2f} seconds")
        
        # Get the subject from session or use the default
        subject = session.get('custom_subject', DEFAULT_SUBJECT)
        
        # Format the results for API response
        api_results = []
        for result in results:
            api_results.append({
                'filename': result['filename'],
                'detection_result': result['detection_result'],
                'subject': subject,
                'success': result['success'],
                'error': result['error'],
                'response_text': result['raw_response'].text if result['success'] and result['raw_response'] else None
            })
        
        return jsonify({'results': api_results, 'subject': subject}), 200
        
    except Exception as e:
        current_app.logger.error(f"API Error processing images: {str(e)}")
        return jsonify({'error': f"An error occurred while processing the images: {str(e)}"}), 500

@main_bp.route('/api/delete_image/<int:image_index>', methods=['DELETE'])
def api_delete_image(image_index):
    """
    API endpoint for deleting an image from the results collection.
    
    Args:
        image_index: Index of the image to delete
        
    Returns:
        flask.Response: JSON response indicating success or failure
    """
    # Get result ID from session
    result_id = session.get('result_id')
    
    if not result_id:
        return jsonify({'success': False, 'error': 'No results found in session. Please upload images first.'}), 400
    
    # Get results from storage
    result_data = results_storage.get(result_id, {})
    results = result_data.get('results', [])
    subject = result_data.get('subject', session.get('custom_subject', DEFAULT_SUBJECT))
    
    # Check if the index is valid
    if not results or image_index < 0 or image_index >= len(results):
        current_app.logger.warning(f"API: Invalid image index for deletion: {image_index}")
        return jsonify({'success': False, 'error': 'Invalid image index'}), 400
    
    try:
        # Remove the image from the results
        current_app.logger.info(f"API: Deleting image {results[image_index]['filename']} at index {image_index}")
        deleted_image = results.pop(image_index)
        
        # Update the results in storage
        results_storage[result_id]['results'] = results
        
        # Return success response
        return jsonify({
            'success': True, 
            'message': f"Image {deleted_image['filename']} deleted successfully",
            'remaining_count': len(results),
            'results': results,
            'subject': subject
        }), 200
    except Exception as e:
        current_app.logger.error(f"API Error deleting image: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
