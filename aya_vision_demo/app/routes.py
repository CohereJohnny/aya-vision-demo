import io
import os
import uuid
import time
import re
from flask import (
    Blueprint, render_template, request, redirect, 
    url_for, flash, current_app, session, jsonify
)
from werkzeug.utils import secure_filename
from app.forms import ImageUploadForm, SettingsForm, EnhancedAnalysisForm
from app.utils import (
    is_valid_file_extension, process_image_batch, process_enhanced_analysis
)

# Create a blueprint for the main routes
main_bp = Blueprint('main', __name__)

# In-memory storage for results (in a production app, this would be a database)
results_storage = {}
enhanced_results_storage = {}

# Default settings
DEFAULT_INITIAL_PROMPT = "Is a flare burning in this image? Answer with only 'true' or 'false'."
DEFAULT_ENHANCED_PROMPT = "Describe in detail what you see in this image, focusing on [subject]. Provide information about its appearance, surroundings, and any notable characteristics."
DEFAULT_SUBJECT = "Flare"

# Helper function to check if a word is already plural
def get_plural_suffix(word):
    """
    Check if a word is already plural and return appropriate suffix.
    
    Args:
        word (str): The word to check
        
    Returns:
        str: Empty string if word is already plural, 's' otherwise
    """
    # Common plural endings
    plural_endings = ['s', 'es', 'ies', 'ves', 'en', 'a', 'i']
    
    # Irregular plurals
    irregular_plurals = {
        'person': 'people',
        'child': 'children',
        'man': 'men',
        'woman': 'women',
        'tooth': 'teeth',
        'foot': 'feet',
        'mouse': 'mice',
        'goose': 'geese'
    }
    
    # Check if it's an irregular plural
    if word.lower() in irregular_plurals.values():
        return ''
    
    # Check for common plural endings
    for ending in plural_endings:
        if word.lower().endswith(ending) and not word.lower() in ['lens', 'bus', 'gas', 'bias', 'atlas', 'virus', 'campus']:
            return ''
    
    return 's'

@main_bp.route('/', methods=['GET', 'POST'])
def index():
    """
    Handle the index page with image upload form.
    
    Returns:
        str: Rendered HTML template
    """
    form = ImageUploadForm()
    
    # Get the subject from session or use the default
    subject = session.get('custom_subject', DEFAULT_SUBJECT)
    
    if form.validate_on_submit():
        # Get the uploaded files
        uploaded_files = request.files.getlist('images')
        
        # Check if this is an AJAX request
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        # Validate the number of files
        if len(uploaded_files) < current_app.config['MIN_IMAGES']:
            error_msg = f"Please upload at least {current_app.config['MIN_IMAGES']} images."
            if is_ajax:
                return jsonify({'error': error_msg}), 400
            flash(error_msg, 'error')
            return render_template('index.html', form=form, subject=subject)
        
        if len(uploaded_files) > current_app.config['MAX_IMAGES']:
            error_msg = f"Please upload no more than {current_app.config['MAX_IMAGES']} images."
            if is_ajax:
                return jsonify({'error': error_msg}), 400
            flash(error_msg, 'error')
            return render_template('index.html', form=form, subject=subject)
        
        # Validate file extensions
        valid_files = []
        for file in uploaded_files:
            if file.filename == '':
                continue
                
            if not is_valid_file_extension(file.filename, current_app.config['UPLOAD_EXTENSIONS']):
                error_msg = f"File {file.filename} has an invalid extension. Allowed extensions: {', '.join(current_app.config['UPLOAD_EXTENSIONS'])}"
                if is_ajax:
                    return jsonify({'error': error_msg}), 400
                flash(error_msg, 'error')
                return render_template('index.html', form=form, subject=subject)
            
            # Read the file data
            file_data = file.read()
            file.seek(0)  # Reset file pointer for potential future use
            
            valid_files.append({
                'filename': secure_filename(file.filename),
                'data': file_data
            })
        
        if not valid_files:
            error_msg = "No valid files were uploaded."
            if is_ajax:
                return jsonify({'error': error_msg}), 400
            flash(error_msg, 'error')
            return render_template('index.html', form=form, subject=subject)
        
        # Process the images
        try:
            # Log the start of processing
            current_app.logger.info(f"Starting to process {len(valid_files)} images with Cohere API")
            start_time = time.time()
            
            # Get the custom prompt from session or use the default
            custom_prompt = session.get('custom_initial_prompt', current_app.config['PROMPT'])
            
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
            
            # Count successful detections
            detected = sum(1 for r in results if r['detection_result'] is True)
            not_detected = sum(1 for r in results if r['detection_result'] is False)
            unknown = sum(1 for r in results if r['detection_result'] is None)
            
            # Get plural suffix based on subject
            plural_suffix = get_plural_suffix(subject)
            
            current_app.logger.info(f"Results summary: {detected} {subject}{plural_suffix} detected, {not_detected} no {subject}{plural_suffix}, {unknown} unknown")
            
            # Generate a unique ID for this batch of results
            result_id = str(uuid.uuid4())
            
            # Store results in server-side storage
            results_storage[result_id] = {
                'results': results,
                'subject': subject  # Store the subject with the results
            }
            
            # Store only the result ID in the session
            session['result_id'] = result_id
            
            # Clear any existing enhanced results for this session
            if 'enhanced_result_id' in session:
                enhanced_id = session.pop('enhanced_result_id')
                if enhanced_id in enhanced_results_storage:
                    del enhanced_results_storage[enhanced_id]
            
            # Redirect to results page
            if is_ajax:
                # Add a small delay to allow the frontend to update the progress bar
                time.sleep(1)
                return jsonify({
                    'success': True,
                    'redirect': url_for('main.results')
                })
            return redirect(url_for('main.results'))
            
        except Exception as e:
            current_app.logger.error(f"Error processing images: {str(e)}")
            error_msg = f"An error occurred while processing the images: {str(e)}"
            if is_ajax:
                return jsonify({'error': error_msg}), 500
            flash(error_msg, 'error')
            return render_template('index.html', form=form, subject=subject)
    
    return render_template('index.html', form=form, subject=subject)

@main_bp.route('/settings', methods=['GET', 'POST'])
def settings():
    """
    Handle the settings page for configuring application parameters.
    
    Returns:
        str: Rendered HTML template
    """
    # Initialize the form with the current custom settings or the defaults
    form = SettingsForm(
        initial_prompt=session.get('custom_initial_prompt', DEFAULT_INITIAL_PROMPT),
        enhanced_prompt=session.get('custom_enhanced_prompt', DEFAULT_ENHANCED_PROMPT),
        subject=session.get('custom_subject', DEFAULT_SUBJECT)
    )
    
    if form.validate_on_submit():
        if 'submit' in request.form:
            # Save the custom settings to the session
            session['custom_initial_prompt'] = form.initial_prompt.data
            session['custom_enhanced_prompt'] = form.enhanced_prompt.data
            session['custom_subject'] = form.subject.data
            current_app.logger.info(f"Updated initial prompt: {form.initial_prompt.data}")
            current_app.logger.info(f"Updated enhanced prompt: {form.enhanced_prompt.data}")
            current_app.logger.info(f"Updated custom subject: {form.subject.data}")
            flash("Settings saved successfully!", 'success')
        elif 'reset' in request.form:
            # Reset to default settings
            session['custom_initial_prompt'] = DEFAULT_INITIAL_PROMPT
            session['custom_enhanced_prompt'] = DEFAULT_ENHANCED_PROMPT
            session['custom_subject'] = DEFAULT_SUBJECT
            form.initial_prompt.data = DEFAULT_INITIAL_PROMPT
            form.enhanced_prompt.data = DEFAULT_ENHANCED_PROMPT
            form.subject.data = DEFAULT_SUBJECT
            current_app.logger.info("Reset to default settings")
            flash("Settings reset to default values.", 'info')
    
    return render_template('settings.html', form=form)

@main_bp.route('/results')
def results():
    """
    Display the results of the initial image analysis.
    
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
    
    # Check if enhanced analysis is available
    enhanced_result_id = session.get('enhanced_result_id')
    has_enhanced_results = enhanced_result_id in enhanced_results_storage
    
    # Count positive detections to determine if enhanced analysis is possible
    positive_detections = sum(1 for r in results if r['detection_result'] is True)
    can_perform_enhanced_analysis = positive_detections > 0
    
    return render_template(
        'results.html', 
        results=results, 
        subject=subject, 
        has_enhanced_results=has_enhanced_results,
        can_perform_enhanced_analysis=can_perform_enhanced_analysis
    )

@main_bp.route('/enhanced-analysis', methods=['GET', 'POST'])
def enhanced_analysis():
    """
    Handle the enhanced analysis form and display enhanced analysis results.
    
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
        flash("No results to analyze. Please upload images first.", 'warning')
        return redirect(url_for('main.index'))
    
    # Filter for positive detections only
    positive_results = [r for r in results if r['detection_result'] is True]
    
    if not positive_results:
        flash("No positive detections found. Enhanced analysis requires at least one positive detection.", 'warning')
        return redirect(url_for('main.results'))
    
    # Check if we already have enhanced results
    enhanced_result_id = session.get('enhanced_result_id')
    if enhanced_result_id in enhanced_results_storage:
        # Display existing enhanced results
        enhanced_data = enhanced_results_storage[enhanced_result_id]
        return render_template(
            'enhanced_results.html',
            results=enhanced_data.get('results', []),
            subject=enhanced_data.get('subject', subject),
            prompt=enhanced_data.get('prompt', '')
        )
    
    # Initialize the form with the default enhanced prompt
    default_prompt = session.get('custom_enhanced_prompt', DEFAULT_ENHANCED_PROMPT)
    # Replace [subject] placeholder with actual subject
    default_prompt = default_prompt.replace('[subject]', subject)
    
    form = EnhancedAnalysisForm(custom_prompt=default_prompt)
    
    if form.validate_on_submit():
        try:
            # Get selected images indices from the form
            selected_images_str = request.form.get('selected_images', '')
            
            # If no images are selected, use all positive results
            if not selected_images_str:
                images_to_analyze = positive_results
                current_app.logger.info("No specific images selected, analyzing all positive results")
            else:
                # Parse the selected image indices
                try:
                    selected_indices = [int(idx) for idx in selected_images_str.split(',') if idx]
                    # Filter the positive results based on selected indices
                    images_to_analyze = [positive_results[idx] for idx in selected_indices if 0 <= idx < len(positive_results)]
                    current_app.logger.info(f"Analyzing {len(images_to_analyze)} selected images out of {len(positive_results)} positive results")
                except (ValueError, IndexError) as e:
                    current_app.logger.error(f"Error parsing selected images: {str(e)}")
                    images_to_analyze = positive_results
                    current_app.logger.info("Falling back to analyzing all positive results")
            
            # Check if we have any images to analyze
            if not images_to_analyze:
                flash("No images selected for enhanced analysis.", 'warning')
                return render_template(
                    'enhanced_analysis.html', 
                    form=form, 
                    subject=subject, 
                    results=positive_results,
                    total_count=len(results),
                    detected_count=len(positive_results),
                    default_prompt=default_prompt
                )
            
            # Log the start of enhanced processing
            current_app.logger.info(f"Starting enhanced analysis for {len(images_to_analyze)} images")
            start_time = time.time()
            
            # Process the selected images with enhanced analysis
            enhanced_results = process_enhanced_analysis(
                images=images_to_analyze,
                api_key=current_app.config['COHERE_API_KEY'],
                model_name=current_app.config['MODEL_NAME'],
                prompt=form.custom_prompt.data
            )
            
            # Log processing completion
            processing_time = time.time() - start_time
            current_app.logger.info(f"Completed enhanced analysis in {processing_time:.2f} seconds")
            
            # Generate a unique ID for this batch of enhanced results
            enhanced_id = str(uuid.uuid4())
            
            # Store enhanced results
            enhanced_results_storage[enhanced_id] = {
                'results': enhanced_results,
                'subject': subject,
                'prompt': form.custom_prompt.data
            }
            
            # Store the enhanced result ID in the session
            session['enhanced_result_id'] = enhanced_id
            
            # Redirect to enhanced results page
            return redirect(url_for('main.enhanced_results'))
            
        except Exception as e:
            current_app.logger.error(f"Error during enhanced analysis: {str(e)}")
            flash(f"An error occurred during enhanced analysis: {str(e)}", 'error')
            return render_template(
                'enhanced_analysis.html', 
                form=form, 
                subject=subject, 
                results=positive_results,
                total_count=len(results),
                detected_count=len(positive_results),
                default_prompt=default_prompt
            )
    
    # Calculate counts for the template
    total_count = len(results)
    detected_count = len(positive_results)
    
    return render_template(
        'enhanced_analysis.html', 
        form=form, 
        subject=subject, 
        results=positive_results,
        total_count=total_count,
        detected_count=detected_count,
        default_prompt=default_prompt
    )

@main_bp.route('/enhanced-results')
def enhanced_results():
    """
    Display the results of the enhanced analysis.
    
    Returns:
        str: Rendered HTML template
    """
    # Get enhanced result ID from session
    enhanced_result_id = session.get('enhanced_result_id')
    
    # Get enhanced results from storage
    if not enhanced_result_id or enhanced_result_id not in enhanced_results_storage:
        flash("No enhanced analysis results to display. Please perform enhanced analysis first.", 'warning')
        return redirect(url_for('main.results'))
    
    enhanced_data = enhanced_results_storage[enhanced_result_id]
    
    return render_template(
        'enhanced_results.html',
        results=enhanced_data.get('results', []),
        subject=enhanced_data.get('subject', session.get('custom_subject', DEFAULT_SUBJECT)),
        prompt=enhanced_data.get('prompt', '')
    )

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
        
        # If we have enhanced results, we should clear them as they may be invalid now
        if 'enhanced_result_id' in session:
            enhanced_id = session.pop('enhanced_result_id')
            if enhanced_id in enhanced_results_storage:
                del enhanced_results_storage[enhanced_id]
        
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
        custom_prompt = session.get('custom_initial_prompt', current_app.config['PROMPT'])
        
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

@main_bp.route('/api/enhanced-analyze', methods=['POST'])
def api_enhanced_analyze():
    """
    API endpoint for enhanced analysis of positively identified images.
    
    Returns:
        flask.Response: JSON response with enhanced analysis results
    """
    # Get result ID from session
    result_id = session.get('result_id')
    
    # Get results from storage
    result_data = results_storage.get(result_id, {})
    results = result_data.get('results', [])
    subject = result_data.get('subject', session.get('custom_subject', DEFAULT_SUBJECT))
    
    if not results:
        return jsonify({'error': 'No results found. Please upload and analyze images first.'}), 400
    
    # Filter for positive detections only
    positive_results = [r for r in results if r['detection_result'] is True]
    
    if not positive_results:
        return jsonify({'error': 'No positive detections found. Enhanced analysis requires at least one positive detection.'}), 400
    
    # Get the custom prompt from the request or use the default
    custom_prompt = request.json.get('prompt') if request.is_json else None
    if not custom_prompt:
        # Get from session or use default
        custom_prompt = session.get('custom_enhanced_prompt', DEFAULT_ENHANCED_PROMPT)
        # Replace [subject] placeholder with actual subject
        custom_prompt = custom_prompt.replace('[subject]', subject)
    
    try:
        # Log the start of enhanced processing
        current_app.logger.info(f"API: Starting enhanced analysis for {len(positive_results)} images")
        start_time = time.time()
        
        # Process the positive results with enhanced analysis
        enhanced_results = process_enhanced_analysis(
            images=positive_results,
            api_key=current_app.config['COHERE_API_KEY'],
            model_name=current_app.config['MODEL_NAME'],
            prompt=custom_prompt
        )
        
        # Log processing completion
        processing_time = time.time() - start_time
        current_app.logger.info(f"API: Completed enhanced analysis in {processing_time:.2f} seconds")
        
        # Generate a unique ID for this batch of enhanced results
        enhanced_id = str(uuid.uuid4())
        
        # Store enhanced results
        enhanced_results_storage[enhanced_id] = {
            'results': enhanced_results,
            'subject': subject,
            'prompt': custom_prompt
        }
        
        # Store the enhanced result ID in the session
        session['enhanced_result_id'] = enhanced_id
        
        # Format the results for API response
        api_results = []
        for result in enhanced_results:
            api_results.append({
                'filename': result['filename'],
                'enhanced_analysis': result['enhanced_analysis'],
                'subject': subject,
                'success': result['success'],
                'error': result['error']
            })
        
        return jsonify({
            'results': api_results, 
            'subject': subject,
            'prompt': custom_prompt,
            'redirect': url_for('main.enhanced_results')
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"API Error during enhanced analysis: {str(e)}")
        return jsonify({'error': f"An error occurred during enhanced analysis: {str(e)}"}), 500

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
        
        # If we have enhanced results, we should clear them as they may be invalid now
        if 'enhanced_result_id' in session:
            enhanced_id = session.pop('enhanced_result_id')
            if enhanced_id in enhanced_results_storage:
                del enhanced_results_storage[enhanced_id]
        
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
