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
# Add progress tracking storage
analysis_progress = {}
enhanced_analysis_progress = {}

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
            
            # Get the custom prompt from session or use the default
            custom_prompt = session.get('custom_initial_prompt', current_app.config['PROMPT'])
            
            # Generate a unique ID for this batch of results and progress tracking
            result_id = str(uuid.uuid4())
            progress_id = str(uuid.uuid4())
            
            # Initialize progress tracking
            analysis_progress[progress_id] = {
                'total': len(valid_files),
                'completed': 0,
                'status': 'initialized',  # Initialize with 'initialized' status
                'percent': 0
            }
            
            # Store IDs in the session
            session['result_id'] = result_id
            session['progress_id'] = progress_id
            current_app.logger.info(f"Created new initial analysis progress ID: {progress_id}")
            current_app.logger.info(f"Stored progress ID in session: {progress_id}")
            
            # Clear any existing enhanced results for this session
            if 'enhanced_result_id' in session:
                enhanced_id = session.pop('enhanced_result_id')
                if enhanced_id in enhanced_results_storage:
                    del enhanced_results_storage[enhanced_id]
            
            # If this is an AJAX request, return immediately with the progress ID
            if is_ajax:
                current_app.logger.info(f"Returning progress ID to client immediately: {progress_id}")
                
                # Create a comprehensive response with all needed data
                response_data = {
                    'success': True,
                    'redirect': url_for('main.results'),
                    'progress_id': progress_id,
                    'result_id': result_id,
                    'timestamp': int(time.time()),
                    'session_has_progress_id': 'progress_id' in session,
                    'session_progress_id': session.get('progress_id', 'not_set'),
                    'total_images': len(valid_files)
                }
                
                # Final confirmation log of the complete response
                current_app.logger.info(f"Sending immediate initial analysis response: {response_data}")
                
                # Start background processing
                import threading
                thread = threading.Thread(
                    target=process_image_batch_background,
                    args=(current_app._get_current_object(), valid_files, current_app.config['COHERE_API_KEY'], 
                          current_app.config['MODEL_NAME'], custom_prompt, progress_id, result_id, subject)
                )
                thread.daemon = True  # Daemonize thread to avoid blocking app shutdown
                thread.start()
                
                current_app.logger.info(f"Started background processing thread for progress ID: {progress_id}")
                
                # Set cache-control headers to ensure the response isn't cached
                response = jsonify(response_data)
                response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                response.headers['Pragma'] = 'no-cache'
                response.headers['Expires'] = '0'
                return response
            
            # For non-AJAX requests, redirect to a waiting page
            return redirect(url_for('main.analysis_progress_page', progress_id=progress_id))
            
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
    
    # Check if this is a request for a new analysis
    is_new_analysis = request.args.get('new') == 'true'
    if is_new_analysis:
        # Remove the enhanced result and progress IDs from the session to force a new analysis
        current_app.logger.info("===== STARTING NEW ENHANCED ANALYSIS =====")
        current_app.logger.info("Clearing previous enhanced results and progress IDs from session")
        
        # Log the current session values before clearing
        current_app.logger.info(f"BEFORE CLEARING - enhanced_result_id: {session.get('enhanced_result_id', 'None')}, enhanced_progress_id: {session.get('enhanced_progress_id', 'None')}")
        
        # Explicitly remove the IDs from the session - using pop with None default to ensure they're removed even if not present
        session.pop('enhanced_result_id', None)
        session.pop('enhanced_progress_id', None)
        
        # Additional step: directly clear the values in enhanced_analysis_progress
        if 'enhanced_progress_id' in session:
            previous_id = session['enhanced_progress_id']
            if previous_id in enhanced_analysis_progress:
                current_app.logger.info(f"Clearing progress data for previous ID: {previous_id}")
                del enhanced_analysis_progress[previous_id]
        
        # Force the session to update immediately
        session.modified = True
        
        # Log the session values after clearing to confirm
        current_app.logger.info(f"AFTER CLEARING - enhanced_result_id: {session.get('enhanced_result_id', 'None')}, enhanced_progress_id: {session.get('enhanced_progress_id', 'None')}")
    
    # Check if we already have enhanced results
    enhanced_result_id = session.get('enhanced_result_id')
    if enhanced_result_id in enhanced_results_storage and not is_new_analysis:
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
            # Check if this is an AJAX request
            is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
            
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
                error_msg = "No images selected for enhanced analysis."
                if is_ajax:
                    return jsonify({'error': error_msg}), 400
                flash(error_msg, 'warning')
                return render_template(
                    'enhanced_analysis.html', 
                    form=form, 
                    subject=subject, 
                    results=positive_results,
                    total_count=len(results),
                    detected_count=len(positive_results),
                    default_prompt=default_prompt
                )
            
            # ===== IMMEDIATE RESPONSE APPROACH =====
            # Generate a unique ID for this batch of enhanced results and progress tracking
            enhanced_id = str(uuid.uuid4())
            progress_id = str(uuid.uuid4())
            
            # IMPORTANT: Initialize progress tracking before starting processing
            enhanced_analysis_progress[progress_id] = {
                'total': len(images_to_analyze),
                'completed': 0,
                'current_file': '',
                'status': 'initialized',  # New status to indicate it's just starting
                'percent': 0
            }
            
            # Store the enhanced result ID and progress ID in the session
            session['enhanced_result_id'] = enhanced_id
            session['enhanced_progress_id'] = progress_id
            current_app.logger.info(f"Created new progress ID: {progress_id}")
            current_app.logger.info(f"Stored progress ID in session: {progress_id}")
            
            # Store the form data for background processing
            prompt = form.custom_prompt.data
            
            # If this is an AJAX request, return immediately with the progress ID
            if is_ajax:
                current_app.logger.info(f"Returning progress ID to client immediately: {progress_id}")
                
                # Create a comprehensive response with all needed data
                response_data = {
                    'success': True,
                    'redirect': url_for('main.enhanced_results'),
                    'progress_id': progress_id,
                    'result_id': enhanced_id,
                    'timestamp': int(time.time()),
                    'session_has_progress_id': 'enhanced_progress_id' in session,
                    'session_progress_id': session.get('enhanced_progress_id', 'not_set'),
                    'total_images': len(images_to_analyze)
                }
                
                # Final confirmation log of the complete response
                current_app.logger.info(f"Sending immediate enhanced analysis response: {response_data}")
                
                # Start background processing
                import threading
                thread = threading.Thread(
                    target=process_enhanced_analysis_background,
                    args=(current_app._get_current_object(), images_to_analyze, current_app.config['COHERE_API_KEY'], 
                          current_app.config['MODEL_NAME'], prompt, progress_id, enhanced_id, subject)
                )
                thread.daemon = True  # Daemonize thread to avoid blocking app shutdown
                thread.start()
                
                current_app.logger.info(f"Started background processing thread for progress ID: {progress_id}")
                
                # Set cache-control headers to ensure the response isn't cached
                response = jsonify(response_data)
                response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                response.headers['Pragma'] = 'no-cache'
                response.headers['Expires'] = '0'
                return response
                
            # For non-AJAX requests, redirect to a waiting page
            return redirect(url_for('main.enhanced_analysis_progress', progress_id=progress_id))
            
        except Exception as e:
            current_app.logger.error(f"Error setting up enhanced analysis: {str(e)}")
            error_msg = f"An error occurred setting up enhanced analysis: {str(e)}"
            if is_ajax:
                return jsonify({'error': error_msg}), 500
            flash(error_msg, 'error')
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

# Add a function to handle initial analysis background processing
def process_image_batch_background(app, images, api_key, model_name, prompt, progress_id, result_id, subject):
    """
    Process initial image analysis in the background.
    This function is called in a separate thread.
    """
    # Create an application context for this thread
    with app.app_context():
        try:
            # Import logging locally to ensure we have access
            import logging
            logger = logging.getLogger('app')
            
            # Verify we have the progress ID in the tracking data
            if progress_id not in analysis_progress:
                logger.error(f"[BG] CRITICAL ERROR: Initial analysis progress ID {progress_id} not found in analysis_progress")
                return
                
            # Log the start of initial processing with the progress ID
            logger.info(f"[BG] Starting initial analysis for {len(images)} images with progress ID: {progress_id}")
            logger.info(f"[BG] Initial progress data: {analysis_progress[progress_id]}")
            start_time = time.time()
            
            # Update status to processing
            analysis_progress[progress_id]['status'] = 'processing'
            logger.info(f"[BG] Updated status to 'processing' for ID: {progress_id}")
            
            # Define a progress callback function with more logging
            def update_progress(index, filename):
                completed = index + 1
                logger.info(f"[BG] Initial analysis progress callback called: index={index}, filename={filename}")
                
                # Verify progress ID still exists
                if progress_id not in analysis_progress:
                    logger.error(f"[BG] ERROR: Progress ID {progress_id} no longer exists in tracking data!")
                    return
                    
                # Update progress data
                analysis_progress[progress_id]['completed'] = completed
                analysis_progress[progress_id]['percent'] = int((completed / len(images)) * 100)
                # Add current filename to the progress data
                analysis_progress[progress_id]['current_file'] = filename
                
                # Log updated progress
                progress_data = analysis_progress[progress_id]
                logger.info(f"[BG] Initial Analysis Progress: {completed}/{len(images)} images processed ({progress_data['percent']}%)")
                logger.info(f"[BG] Current progress data: {progress_data}")
            
            # Process the images
            logger.info(f"[BG] Calling process_image_batch with {len(images)} images")
            results = process_image_batch(
                images=images,
                api_key=api_key,
                model_name=model_name,
                prompt=prompt,
                progress_callback=update_progress
            )
            
            # Log what we got back
            logger.info(f"[BG] Received {len(results) if results else 0} results from process_image_batch")
            
            # Verify progress ID still exists
            if progress_id not in analysis_progress:
                logger.error(f"[BG] ERROR: Initial analysis progress ID {progress_id} no longer exists in tracking data after processing!")
                return
                
            # Mark progress as complete
            analysis_progress[progress_id]['status'] = 'complete'
            analysis_progress[progress_id]['percent'] = 100
            logger.info(f"[BG] Initial analysis progress tracking complete for ID: {progress_id}")
            logger.info(f"[BG] Final progress data: {analysis_progress[progress_id]}")
            
            # Log processing completion
            processing_time = time.time() - start_time
            logger.info(f"[BG] Completed initial analysis in {processing_time:.2f} seconds")
            
            # Count successful detections
            detected = sum(1 for r in results if r['detection_result'] is True)
            not_detected = sum(1 for r in results if r['detection_result'] is False)
            unknown = sum(1 for r in results if r['detection_result'] is None)
            
            # Get plural suffix based on subject
            plural_suffix = get_plural_suffix(subject)
            
            logger.info(f"[BG] Results summary: {detected} {subject}{plural_suffix} detected, {not_detected} no {subject}{plural_suffix}, {unknown} unknown")
            
            # Store results in server-side storage
            results_storage[result_id] = {
                'results': results,
                'subject': subject  # Store the subject with the results
            }
            
            logger.info(f"[BG] Stored initial analysis results with ID: {result_id}")
            
        except Exception as e:
            import traceback
            import logging
            logger = logging.getLogger('app')
            logger.error(f"[BG] Error during background initial analysis: {str(e)}")
            logger.error(f"[BG] Traceback: {traceback.format_exc()}")
            
            # Update progress status to error
            if progress_id in analysis_progress:
                analysis_progress[progress_id]['status'] = 'error'
                analysis_progress[progress_id]['error'] = str(e)
                logger.info(f"[BG] Updated progress status to 'error' for ID: {progress_id}")

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
    subject = result_data.get('subject', session.get('custom_subject', DEFAULT_SUBJECT))
    
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
        # Calculate counts for the remaining results
        detected_count = sum(1 for r in results if r.get('detection_result') is True)
        not_detected_count = sum(1 for r in results if r.get('detection_result') is False)
        unknown_count = sum(1 for r in results if r.get('detection_result') is None)
        
        return jsonify({
            'success': True, 
            'message': f"Image {deleted_image['filename']} deleted successfully",
            'remaining_count': len(results),
            'counts': {
                'total': len(results),
                'detected': detected_count,
                'not_detected': not_detected_count,
                'unknown': unknown_count
            },
            'results': results,
            'subject': subject
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
        # Calculate counts for the remaining results
        detected_count = sum(1 for r in results if r.get('detection_result') is True)
        not_detected_count = sum(1 for r in results if r.get('detection_result') is False)
        unknown_count = sum(1 for r in results if r.get('detection_result') is None)
        
        return jsonify({
            'success': True, 
            'message': f"Image {deleted_image['filename']} deleted successfully",
            'remaining_count': len(results),
            'counts': {
                'total': len(results),
                'detected': detected_count,
                'not_detected': not_detected_count,
                'unknown': unknown_count
            },
            'results': results,
            'subject': subject
        }), 200
    except Exception as e:
        current_app.logger.error(f"API Error deleting image: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@main_bp.route('/api/analysis-progress/<string:progress_id>', methods=['GET'])
def get_analysis_progress(progress_id):
    """
    API endpoint to get the current progress of image analysis.
    
    Args:
        progress_id: The ID of the analysis progress to retrieve
        
    Returns:
        flask.Response: JSON response with progress information
    """
    # Log request details
    timestamp = time.time()
    client_ip = request.remote_addr
    user_agent = request.headers.get('User-Agent', 'Unknown')
    request_id = str(uuid.uuid4())[:8]  # Short ID for logging
    
    # Log request with detailed info
    current_app.logger.info(f"[{timestamp}][{request_id}] Initial analysis progress request received from {client_ip}")
    current_app.logger.info(f"[{request_id}] Headers: Cache-Control={request.headers.get('Cache-Control', 'None')}, Pragma={request.headers.get('Pragma', 'None')}")
    current_app.logger.info(f"[{request_id}] Query params: {dict(request.args)}")
    
    # Log all available progress IDs for debugging
    available_ids = list(analysis_progress.keys())
    current_app.logger.info(f"[{request_id}] Available analysis progress IDs: {available_ids}")
    
    # Get progress from storage
    progress_data = analysis_progress.get(progress_id, {})
    
    # If no progress data found, return 404
    if not progress_data:
        current_app.logger.warning(f"[{request_id}] Analysis progress ID not found: {progress_id}")
        return jsonify({'error': 'Progress ID not found'}), 404
    
    # Log the progress data with timestamp
    current_app.logger.info(f"[{request_id}] Progress data for {progress_id}: {progress_data}")
    
    # Create response with progress information
    response_data = {
        'status': progress_data.get('status', 'unknown'),
        'percent': progress_data.get('percent', 0),
        'completed': progress_data.get('completed', 0),
        'total': progress_data.get('total', 0),
        'timestamp': timestamp,
        'request_id': request_id
    }
    
    # Add result ID from session for redirection when analysis completes
    response_data['result_id'] = session.get('result_id')
    
    # Add current file information if available
    if 'current_file' in progress_data:
        response_data['current_file'] = progress_data['current_file']
    
    # Add error information if status is error
    if progress_data.get('status') == 'error' and 'error' in progress_data:
        response_data['error'] = progress_data['error']
    
    # Create response with progress data
    response = jsonify(response_data)
    
    # Add strong cache control headers to prevent caching
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    
    # Add extra headers to further prevent caching
    response.headers['X-Progress-ID'] = progress_id
    response.headers['X-Request-ID'] = request_id
    response.headers['X-Timestamp'] = str(timestamp)
    
    current_app.logger.info(f"[{request_id}] Sending response with percent: {response_data['percent']}%, completed: {response_data['completed']}/{response_data['total']}")
    
    return response

@main_bp.route('/api/enhanced-analysis-progress/<string:progress_id>', methods=['GET'])
def get_enhanced_analysis_progress(progress_id):
    """
    API endpoint to get the current progress of enhanced image analysis.
    
    Args:
        progress_id: The ID of the enhanced analysis progress to retrieve
        
    Returns:
        flask.Response: JSON response with progress information
    """
    # Log request details
    timestamp = time.time()
    client_ip = request.remote_addr
    user_agent = request.headers.get('User-Agent', 'Unknown')
    request_id = str(uuid.uuid4())[:8]  # Short ID for logging
    
    # Log request with detailed info
    current_app.logger.info(f"[{timestamp}][{request_id}] Progress request received from {client_ip}")
    current_app.logger.info(f"[{request_id}] Headers: Cache-Control={request.headers.get('Cache-Control', 'None')}, Pragma={request.headers.get('Pragma', 'None')}")
    current_app.logger.info(f"[{request_id}] Query params: {dict(request.args)}")
    
    # Log all available progress IDs for debugging
    available_ids = list(enhanced_analysis_progress.keys())
    current_app.logger.info(f"[{request_id}] Available enhanced analysis progress IDs: {available_ids}")
    
    # Get progress from storage
    progress_data = enhanced_analysis_progress.get(progress_id, {})
    
    # If no progress data found, return 404
    if not progress_data:
        current_app.logger.warning(f"[{request_id}] Enhanced analysis progress ID not found: {progress_id}")
        return jsonify({'error': 'Progress ID not found'}), 404
    
    # Log the progress data with timestamp
    current_app.logger.info(f"[{request_id}] Progress data for {progress_id}: {progress_data}")
    
    # Create response with progress information
    response_data = {
        'total': progress_data.get('total', 0),
        'completed': progress_data.get('completed', 0),
        'status': progress_data.get('status', 'unknown'),
        'percent': progress_data.get('percent', 0),
        'timestamp': timestamp,
        'request_id': request_id
    }
    
    # Create response with progress data
    response = jsonify(response_data)
    
    # Add strong cache control headers to prevent caching
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    
    # Add extra headers to further prevent caching
    response.headers['X-Progress-ID'] = progress_id
    response.headers['X-Request-ID'] = request_id
    response.headers['X-Timestamp'] = str(timestamp)
    
    current_app.logger.info(f"[{request_id}] Sending response with percent: {response_data['percent']}%, completed: {response_data['completed']}/{response_data['total']}")
    
    return response

@main_bp.route('/api/test-polling/<string:progress_id>', methods=['GET'])
def test_polling(progress_id):
    """Special endpoint for testing polling functionality"""
    # Generate a unique request ID
    request_id = uuid.uuid4().hex[:8]
    
    # Log detailed request information
    current_app.logger.info(f"[POLL_TEST][{time.time()}][{request_id}] Test polling request from {request.remote_addr}")
    current_app.logger.info(f"[POLL_TEST][{request_id}] User-Agent: {request.headers.get('User-Agent')}")
    current_app.logger.info(f"[POLL_TEST][{request_id}] Headers: {dict(request.headers)}")
    current_app.logger.info(f"[POLL_TEST][{request_id}] Query params: {dict(request.args)}")
    
    # Get or create progress data
    # Use enhanced_analysis_progress from the global scope
    
    # Special handling for 'test' progress ID
    if progress_id == 'test':
        # Look for an existing test ID to reuse
        test_id = None
        # Check available progress IDs
        available_ids = list(enhanced_analysis_progress.keys())
        current_app.logger.info(f"[POLL_TEST][{request_id}] Available progress IDs: {available_ids}")
        
        # Find an existing test ID
        for pid in available_ids:
            if pid.startswith('test-'):
                test_id = pid
                current_app.logger.info(f"[POLL_TEST][{request_id}] Reusing existing test ID: {test_id}")
                break
        
        # If no existing test ID found, create a new one
        if not test_id:
            test_id = f"test-{uuid.uuid4().hex[:8]}"
            enhanced_analysis_progress[test_id] = {
                'total': 8,
                'completed': 0,  # Start at 0
                'current_file': 'test-image-1.jpg',
                'status': 'processing',
                'percent': 0  # Start at 0%
            }
            current_app.logger.info(f"[POLL_TEST][{request_id}] Created new test progress ID: {test_id}")
        
        # Use the test ID instead of 'test'
        progress_id = test_id
    
    # If it's a normal progress ID but not found, create it
    if progress_id not in enhanced_analysis_progress:
        enhanced_analysis_progress[progress_id] = {
            'total': 8,
            'completed': 0,
            'current_file': 'test-image-1.jpg',
            'status': 'processing',
            'percent': 0
        }
        current_app.logger.info(f"[POLL_TEST][{request_id}] Created new progress data for ID: {progress_id}")
    
    # Get the current progress data
    progress_data = enhanced_analysis_progress[progress_id]
    
    # Check if we should auto-advance the progress (test mode)
    test_mode = request.args.get('test_mode') == 'true'
    if test_mode and progress_data['status'] != 'complete':
        # Increment progress
        old_completed = progress_data['completed']
        if old_completed < progress_data['total']:
            progress_data['completed'] += 1
            
            # Update percent
            progress_data['percent'] = int((progress_data['completed'] / progress_data['total']) * 100)
            
            # Update current file
            file_num = progress_data['completed'] + 1
            progress_data['current_file'] = f"test-image-{file_num}.jpg"
            
            # Mark as complete if all done
            if progress_data['completed'] >= progress_data['total']:
                progress_data['status'] = 'complete'
                
            current_app.logger.info(f"[POLL_TEST][{request_id}] Advanced test progress: {old_completed} -> {progress_data['completed']} ({progress_data['percent']}%)")
    
    # Log the progress data
    current_app.logger.info(f"[POLL_TEST][{request_id}] Progress data: {progress_data}")
    
    # Create response
    response = jsonify({
        'percent': progress_data['percent'],
        'completed': progress_data['completed'],
        'total': progress_data['total'],
        'current_file': progress_data['current_file'],
        'status': progress_data['status'],
        'request_id': request_id
    })
    
    # Add cache control headers
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    
    current_app.logger.info(f"[POLL_TEST][{request_id}] Sending response with percent: {progress_data['percent']}%")
    
    return response

@main_bp.route('/polling-test/<string:progress_id>')
def polling_test_page(progress_id):
    """Render a dedicated page for testing polling functionality"""
    return render_template('polling_test.html', progress_id=progress_id)

@main_bp.route('/enhanced-analysis-progress/<string:progress_id>')
def enhanced_analysis_progress_page(progress_id):
    """
    Display a waiting page that shows progress for enhanced analysis.
    
    Args:
        progress_id: The ID of the analysis progress to track
        
    Returns:
        str: Rendered HTML template
    """
    # Verify that this progress ID exists
    if progress_id not in enhanced_analysis_progress:
        flash("Invalid progress ID. Please start a new enhanced analysis.", "error")
        return redirect(url_for('main.results'))
        
    # Get the current subject
    subject = session.get('custom_subject', DEFAULT_SUBJECT)
    
    # Render a template that will poll for progress
    return render_template(
        'enhanced_analysis_progress.html',
        progress_id=progress_id,
        subject=subject
    )

@main_bp.route('/analysis-progress/<string:progress_id>')
def analysis_progress_page(progress_id):
    """
    Route to display the analysis progress page for initial image analysis.
    """
    # Get result ID from the session
    result_id = session.get('result_id')
    if not result_id:
        flash("No analysis session found. Please start a new analysis.", "error")
        return redirect(url_for('main.index'))

    # Check if the progress ID exists in the tracking data
    if progress_id not in analysis_progress:
        flash("Invalid progress ID or analysis session expired.", "error")
        return redirect(url_for('main.index'))

    # Get debug mode from request
    debug = request.args.get('debug', False)
    
    # Log the progress page access
    current_app.logger.info(f"Serving analysis progress page for progress_id={progress_id}, result_id={result_id}")
    
    # Render the progress page template
    return render_template(
        'analysis_progress.html',
        progress_id=progress_id,
        result_id=result_id,
        debug=debug
    )

# Add a new route for analysis results by ID
@main_bp.route('/analysis-results/<result_id>')
def analysis_results(result_id):
    """
    Route to display the results of an initial image analysis by result ID.
    """
    current_app.logger.info(f"Accessing results for ID: {result_id}")
    
    # Check if the result ID exists in the storage
    if result_id not in results_storage:
        flash("Invalid result ID or results have expired.", "error")
        return redirect(url_for('main.index'))
    
    # Get the results data
    results_data = results_storage[result_id]
    current_app.logger.info(f"Found results for ID {result_id}")
    
    # Get the subject from the results data
    subject = results_data.get('subject', 'item')
    
    # Render the results template
    return render_template(
        'results.html',
        results=results_data['results'],
        subject=subject
    )

# Add a function to handle enhanced analysis background processing
def process_enhanced_analysis_background(app, images, api_key, model_name, prompt, progress_id, enhanced_id, subject):
    """
    Process enhanced analysis in the background.
    This function is called in a separate thread.
    """
    # Create an application context for this thread
    with app.app_context():
        try:
            # Import logging locally to ensure we have access
            import logging
            logger = logging.getLogger('app')
            
            # Verify we have the progress ID in the tracking data
            if progress_id not in enhanced_analysis_progress:
                logger.error(f"[BG] CRITICAL ERROR: Progress ID {progress_id} not found in enhanced_analysis_progress")
                return
                
            # Log the start of enhanced processing with the progress ID
            logger.info(f"[BG] Starting enhanced analysis for {len(images)} images with progress ID: {progress_id}")
            logger.info(f"[BG] Initial progress data: {enhanced_analysis_progress[progress_id]}")
            start_time = time.time()
            
            # Update status to processing
            enhanced_analysis_progress[progress_id]['status'] = 'processing'
            logger.info(f"[BG] Updated status to 'processing' for ID: {progress_id}")
            
            # Define a progress callback function with more logging
            def update_progress(index, filename):
                completed = index + 1
                logger.info(f"[BG] Progress callback called: index={index}, filename={filename}")
                
                # Verify progress ID still exists
                if progress_id not in enhanced_analysis_progress:
                    logger.error(f"[BG] ERROR: Progress ID {progress_id} no longer exists in tracking data!")
                    return
                    
                # Update progress data
                enhanced_analysis_progress[progress_id]['completed'] = completed
                enhanced_analysis_progress[progress_id]['current_file'] = filename
                enhanced_analysis_progress[progress_id]['percent'] = int((completed / len(images)) * 100)
                
                # Log updated progress
                progress_data = enhanced_analysis_progress[progress_id]
                logger.info(f"[BG] Enhanced Analysis Progress: {completed}/{len(images)} images processed ({progress_data['percent']}%)")
                logger.info(f"[BG] Current progress data: {progress_data}")
            
            # Process the selected images with enhanced analysis
            logger.info(f"[BG] Calling process_enhanced_analysis with {len(images)} images")
            enhanced_results = process_enhanced_analysis(
                images=images,
                api_key=api_key,
                model_name=model_name,
                prompt=prompt,
                progress_callback=update_progress
            )
            
            # Log what we got back
            logger.info(f"[BG] Received {len(enhanced_results) if enhanced_results else 0} results from process_enhanced_analysis")
            
            # Verify progress ID still exists
            if progress_id not in enhanced_analysis_progress:
                logger.error(f"[BG] ERROR: Progress ID {progress_id} no longer exists in tracking data after processing!")
                return
                
            # Mark progress as complete
            enhanced_analysis_progress[progress_id]['status'] = 'complete'
            enhanced_analysis_progress[progress_id]['percent'] = 100
            logger.info(f"[BG] Enhanced analysis progress tracking complete for ID: {progress_id}")
            logger.info(f"[BG] Final progress data: {enhanced_analysis_progress[progress_id]}")
            
            # Log processing completion
            processing_time = time.time() - start_time
            logger.info(f"[BG] Completed enhanced analysis in {processing_time:.2f} seconds")
            
            # Store enhanced results
            enhanced_results_storage[enhanced_id] = {
                'results': enhanced_results,
                'subject': subject,
                'prompt': prompt
            }
            
            logger.info(f"[BG] Stored enhanced results with ID: {enhanced_id}")
            
        except Exception as e:
            import traceback
            import logging
            logger = logging.getLogger('app')
            logger.error(f"[BG] Error during background enhanced analysis: {str(e)}")
            logger.error(f"[BG] Traceback: {traceback.format_exc()}")
            
            # Update progress status to error
            if progress_id in enhanced_analysis_progress:
                enhanced_analysis_progress[progress_id]['status'] = 'error'
                enhanced_analysis_progress[progress_id]['error'] = str(e)
                logger.info(f"[BG] Updated progress status to 'error' for ID: {progress_id}")
