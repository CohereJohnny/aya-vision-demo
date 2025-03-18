import base64
import io
import logging
import os
import time
from typing import Dict, List, Tuple, Optional, Any, Callable
from PIL import Image
import cohere
from werkzeug.utils import secure_filename

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_client() -> cohere.ClientV2:
    """
    Create and configure a Cohere ClientV2 instance.
    
    Returns:
        cohere.ClientV2: Configured Cohere client
    """
    client = cohere.ClientV2(
        api_key=os.getenv("COHERE_API_KEY"),
        log_warning_experimental_features=False
    )
    return client

def is_valid_file_extension(filename: str, allowed_extensions: List[str]) -> bool:
    """
    Check if the file has an allowed extension.
    
    Args:
        filename: The name of the file to check
        allowed_extensions: List of allowed file extensions
        
    Returns:
        bool: True if the file extension is allowed, False otherwise
    """
    return os.path.splitext(filename)[1].lower() in allowed_extensions

def encode_image_to_base64(image_file) -> Tuple[str, str]:
    """
    Encode an image file to base64.
    
    Args:
        image_file: The image file object from request.files
        
    Returns:
        Tuple[str, str]: A tuple containing the base64 encoded image and the MIME type
    """
    # Read the image file
    image_content = image_file.read()
    
    # Get the MIME type
    image = Image.open(io.BytesIO(image_content))
    mime_type = f"image/{image.format.lower()}"
    
    # Encode to base64
    encoded_image = base64.b64encode(image_content).decode('utf-8')
    
    return encoded_image, mime_type

def create_thumbnail(image_data: bytes, size: Tuple[int, int] = (300, 300)) -> str:
    """
    Create a thumbnail from image data.
    
    Args:
        image_data: The binary image data
        size: The size of the thumbnail (width, height)
        
    Returns:
        str: Base64 encoded thumbnail
    """
    # Create a thumbnail
    image = Image.open(io.BytesIO(image_data))
    
    # Calculate new dimensions while preserving aspect ratio
    width, height = image.size
    aspect_ratio = width / height
    
    if width > height:
        new_width = min(width, size[0])
        new_height = int(new_width / aspect_ratio)
    else:
        new_height = min(height, size[1])
        new_width = int(new_height * aspect_ratio)
    
    # Resize the image with high quality (LANCZOS is high quality)
    image = image.resize((new_width, new_height), Image.LANCZOS)
    
    # Save the thumbnail to a bytes buffer with high quality
    buffer = io.BytesIO()
    
    # For JPEG format, specify high quality
    if image.format == 'JPEG':
        image.save(buffer, format='JPEG', quality=90)
    else:
        # For other formats, use their default settings
        image.save(buffer, format=image.format or 'PNG')
    
    buffer.seek(0)
    
    # Encode to base64
    encoded_thumbnail = base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    return encoded_thumbnail

def analyze_image_with_cohere(
    api_key: str,
    base64_image: str,
    mime_type: str,
    model_name: str,
    prompt: str,
    max_retries: int = 3,
    retry_delay: int = 1,
    temperature: float = 0.3
) -> Dict[str, Any]:
    """
    Send an image to Cohere API for analysis using the Chat V2 API.
    
    Args:
        api_key: Cohere API key
        base64_image: Base64 encoded image
        mime_type: MIME type of the image
        model_name: Name of the Cohere model to use
        prompt: Prompt to send to the model
        max_retries: Maximum number of retries for transient errors
        retry_delay: Initial delay between retries (will be exponentially increased)
        temperature: Temperature setting for the model (0.0-1.0, lower for more deterministic responses)
        
    Returns:
        Dict[str, Any]: The API response
        
    Raises:
        Exception: If the API call fails after all retries
    """
    if not api_key:
        raise ValueError("Cohere API key is required")
    
    # Set the API key in the environment for the setup_client method
    os.environ["COHERE_API_KEY"] = api_key
    
    # Initialize the Cohere client using the setup_client method
    co = setup_client()
    
    # Format the image for the API
    image_uri = f"data:{mime_type};base64,{base64_image}"
    
    # Prepare the request using V2 Chat API format
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": prompt
                },
                {
                    "type": "image_url",
                    "image_url": {"url": image_uri}
                }
            ]
        }
    ]
    
    # Implement retry logic with exponential backoff
    for attempt in range(max_retries):
        try:
            logger.info(f"Sending request to Cohere Chat V2 API (attempt {attempt + 1}/{max_retries})")
            
            # Make the API call using the V2 Chat API
            response = co.chat(
                model=model_name,
                messages=messages,
                temperature=temperature,  # Use the provided temperature parameter
            )
            
            # Extract the text response from the message content
            response_text = response.message.content[0].text
            
            return {
                "success": True,
                "response": response_text,
                "raw_response": response
            }
        except Exception as e:
            logger.error(f"Error calling Cohere API: {str(e)}")
            if attempt < max_retries - 1:
                # Calculate exponential backoff delay
                sleep_time = retry_delay * (2 ** attempt)
                logger.info(f"Retrying in {sleep_time} seconds...")
                time.sleep(sleep_time)
            else:
                return {
                    "success": False,
                    "error": str(e)
                }

def parse_detection_result(response: str) -> Optional[bool]:
    """
    Parse the model's response to determine if the subject is detected.
    
    Args:
        response: The text response from the model
        
    Returns:
        Optional[bool]: True if detected, False if not, None if the response couldn't be parsed
    """
    # Convert to lowercase and strip whitespace
    response = response.lower().strip()
    
    # Check for true/false responses
    if response == "true":
        return True
    elif response == "false":
        return False
    
    # If the response is not a simple true/false, try to extract it from the text
    if "true" in response and "false" not in response:
        return True
    elif "false" in response and "true" not in response:
        return False
    
    # If we can't determine the result
    logger.warning(f"Could not parse detection result from response: {response}")
    return None

def process_image_batch(
    images: List[Dict], 
    api_key: str, 
    model_name: str, 
    prompt: str,
    progress_callback: Optional[Callable[[int, str], None]] = None
) -> List[Dict]:
    """
    Process a batch of images with the Cohere API for initial binary classification.
    
    Args:
        images: List of image dictionaries with filename, data, and mime_type
        api_key: Cohere API key
        model_name: Name of the Cohere model to use
        prompt: Prompt to send to the model
        progress_callback: Optional callback function to report progress
        
    Returns:
        List[Dict]: List of results with original image info and analysis results
    """
    results = []
    
    for i, image in enumerate(images):
        # Create a thumbnail
        thumbnail = create_thumbnail(image['data'])
        
        # Encode the image to base64
        base64_image, mime_type = encode_image_to_base64(io.BytesIO(image['data']))
        
        # Analyze the image
        analysis_result = analyze_image_with_cohere(
            api_key=api_key,
            base64_image=base64_image,
            mime_type=mime_type,
            model_name=model_name,
            prompt=prompt
        )
        
        # Parse the result
        detection_result = None
        if analysis_result['success']:
            detection_result = parse_detection_result(analysis_result['response'])
        
        # Add to results
        results.append({
            'filename': image['filename'],
            'thumbnail': thumbnail,
            'full_image': base64_image,
            'mime_type': mime_type,
            'detection_result': detection_result,
            'success': analysis_result['success'],
            'error': analysis_result.get('error', None),
            'raw_response': analysis_result.get('raw_response', None)
        })
        
        # Report progress if callback is provided - MOVED HERE to update after processing
        if progress_callback:
            progress_callback(i, image['filename'])
    
    return results

def process_enhanced_analysis(
    images: List[Dict], 
    api_key: str, 
    model_name: str, 
    prompt: str,
    progress_callback: Optional[Callable[[int, str], None]] = None
) -> List[Dict]:
    """
    Process a batch of images with the Cohere API for enhanced detailed analysis.
    This function is used for the second stage of analysis on positively identified images.
    
    Args:
        images: List of image dictionaries from the initial analysis results
        api_key: Cohere API key
        model_name: Name of the Cohere model to use
        prompt: Detailed analysis prompt to send to the model
        progress_callback: Optional callback function to report progress
        
    Returns:
        List[Dict]: List of results with original image info and enhanced analysis results
    """
    enhanced_results = []
    
    for i, image in enumerate(images):
        logger.info(f"Performing enhanced analysis for image: {image['filename']}")
        
        # We already have the base64 image from the initial analysis
        base64_image = image['full_image']
        mime_type = image['mime_type']
        
        # Analyze the image with the enhanced prompt
        analysis_result = analyze_image_with_cohere(
            api_key=api_key,
            base64_image=base64_image,
            mime_type=mime_type,
            model_name=model_name,
            prompt=prompt,
            temperature=0.7  # Higher temperature for more creative responses
        )
        
        # Add to results
        enhanced_results.append({
            'filename': image['filename'],
            'thumbnail': image['thumbnail'],
            'full_image': base64_image,
            'mime_type': mime_type,
            'detection_result': image['detection_result'],  # Keep the original detection result
            'enhanced_analysis': analysis_result['response'] if analysis_result['success'] else None,
            'success': analysis_result['success'],
            'error': analysis_result.get('error', None),
            'raw_response': analysis_result.get('raw_response', None)
        })
        
        # Report progress if callback is provided
        if progress_callback:
            progress_callback(i, image['filename'])
    
    return enhanced_results
