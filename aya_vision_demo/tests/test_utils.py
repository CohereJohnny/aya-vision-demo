import io
import base64
from PIL import Image
from app.utils import (
    is_valid_file_extension, 
    create_thumbnail, 
    parse_flare_detection_result
)

def test_is_valid_file_extension():
    """Test the is_valid_file_extension function."""
    # Valid extensions
    assert is_valid_file_extension('image.jpg', ['.jpg', '.jpeg', '.png']) is True
    assert is_valid_file_extension('image.jpeg', ['.jpg', '.jpeg', '.png']) is True
    assert is_valid_file_extension('image.png', ['.jpg', '.jpeg', '.png']) is True
    
    # Invalid extensions
    assert is_valid_file_extension('image.gif', ['.jpg', '.jpeg', '.png']) is False
    assert is_valid_file_extension('image.txt', ['.jpg', '.jpeg', '.png']) is False
    assert is_valid_file_extension('image', ['.jpg', '.jpeg', '.png']) is False

def test_create_thumbnail():
    """Test the create_thumbnail function."""
    # Create a test image
    img = Image.new('RGB', (200, 200), color='red')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0)
    
    # Create a thumbnail
    thumbnail = create_thumbnail(img_bytes.getvalue(), size=(100, 100))
    
    # Decode the thumbnail
    thumbnail_bytes = base64.b64decode(thumbnail)
    thumbnail_img = Image.open(io.BytesIO(thumbnail_bytes))
    
    # Check the size
    assert thumbnail_img.width <= 100
    assert thumbnail_img.height <= 100

def test_parse_flare_detection_result():
    """Test the parse_flare_detection_result function."""
    # True responses
    assert parse_flare_detection_result('true') is True
    assert parse_flare_detection_result('True') is True
    assert parse_flare_detection_result('TRUE') is True
    assert parse_flare_detection_result('  true  ') is True
    assert parse_flare_detection_result('Yes, there is a flare burning in this image. true') is True
    
    # False responses
    assert parse_flare_detection_result('false') is False
    assert parse_flare_detection_result('False') is False
    assert parse_flare_detection_result('FALSE') is False
    assert parse_flare_detection_result('  false  ') is False
    assert parse_flare_detection_result('No, there is no flare burning in this image. false') is False
    
    # Ambiguous responses
    assert parse_flare_detection_result('maybe') is None
    assert parse_flare_detection_result('I cannot determine') is None
    assert parse_flare_detection_result('true and false') is None
