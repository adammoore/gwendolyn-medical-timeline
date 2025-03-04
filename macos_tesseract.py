"""
macos_tesseract.py

A module to use macOS-specific approaches to access Tesseract OCR functionality.
"""

import os
import subprocess
import tempfile
from PIL import Image

def is_tesseract_installed():
    """
    Check if Tesseract is installed on the system.
    
    Returns:
        bool: True if Tesseract is installed, False otherwise.
    """
    try:
        # Try to run tesseract command
        result = subprocess.run(
            ["which", "tesseract"], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            check=False
        )
        return result.returncode == 0
    except Exception:
        return False

def image_to_string(image):
    """
    Use Tesseract OCR to extract text from an image.
    
    Parameters:
        image: PIL Image or numpy array.
        
    Returns:
        str: Extracted text from the image.
    """
    if not is_tesseract_installed():
        return "Tesseract is not installed on this system."
    
    try:
        # Create a temporary file for the image
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_img:
            temp_img_path = temp_img.name
        
        # Save the image to the temporary file
        if isinstance(image, Image.Image):
            image.save(temp_img_path)
        else:
            # Assume it's a numpy array
            Image.fromarray(image).save(temp_img_path)
        
        # Create a temporary file for the output
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as temp_out:
            temp_out_path = temp_out.name
        
        # Run tesseract command
        subprocess.run(
            ["tesseract", temp_img_path, temp_out_path.replace('.txt', '')],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )
        
        # Read the output
        with open(temp_out_path, 'r') as f:
            text = f.read()
        
        # Clean up temporary files
        os.unlink(temp_img_path)
        os.unlink(temp_out_path)
        
        return text
    except Exception as e:
        return f"Error using Tesseract: {str(e)}"
