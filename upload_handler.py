"""
upload_handler.py

A module to handle file uploads for the Evernote export application.
"""

import os
import json
import uuid
from datetime import datetime
import knowledge_store_manager as ksm
from werkzeug.utils import secure_filename

# Directory paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")

# Ensure uploads directory exists
os.makedirs(UPLOADS_DIR, exist_ok=True)

def allowed_file(filename, allowed_extensions=None):
    """
    Check if a file has an allowed extension.
    
    Parameters:
        filename (str): The filename to check.
        allowed_extensions (list): List of allowed extensions. If None, all extensions are allowed.
        
    Returns:
        bool: True if the file has an allowed extension, False otherwise.
    """
    if allowed_extensions is None:
        allowed_extensions = ['pdf', 'png', 'jpg', 'jpeg', 'doc', 'docx', 'txt', 'enex']
    
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def handle_upload(file, event_id=None):
    """
    Handle a file upload.
    
    Parameters:
        file: The uploaded file object.
        event_id (str): The ID of the event to associate the file with, or None to create a new event.
        
    Returns:
        dict: Information about the uploaded file, or None if upload failed.
    """
    if file and allowed_file(file.filename):
        # Secure the filename
        filename = secure_filename(file.filename)
        
        # Handle the uploaded file
        file_info = ksm.handle_uploaded_file(file)
        
        if file_info:
            # Process the uploaded file
            processed_info = ksm.process_uploaded_file(file_info)
            
            if processed_info:
                # Add the file to the knowledge store
                event_id = ksm.add_uploaded_file_to_knowledge_store(processed_info, event_id)
                
                if event_id:
                    # Rebuild the vector store
                    ksm.rebuild_vector_store()
                    
                    return {
                        "success": True,
                        "file_info": processed_info,
                        "event_id": event_id
                    }
    
    return {
        "success": False,
        "error": "Failed to upload file."
    }

def get_uploaded_files():
    """
    Get all uploaded files.
    
    Returns:
        list: List of uploaded files.
    """
    uploaded_files = []
    
    for file_id in os.listdir(UPLOADS_DIR):
        info_path = os.path.join(UPLOADS_DIR, file_id, "info.json")
        
        if os.path.exists(info_path):
            with open(info_path, 'r') as f:
                file_info = json.load(f)
                uploaded_files.append(file_info)
    
    return uploaded_files

def get_uploaded_file(file_id):
    """
    Get information about an uploaded file.
    
    Parameters:
        file_id (str): The file ID.
        
    Returns:
        dict: Information about the uploaded file, or None if not found.
    """
    info_path = os.path.join(UPLOADS_DIR, file_id, "info.json")
    
    if os.path.exists(info_path):
        with open(info_path, 'r') as f:
            return json.load(f)
    
    return None

def delete_uploaded_file(file_id):
    """
    Delete an uploaded file.
    
    Parameters:
        file_id (str): The file ID.
        
    Returns:
        bool: True if successful, False otherwise.
    """
    upload_dir = os.path.join(UPLOADS_DIR, file_id)
    
    if os.path.exists(upload_dir):
        try:
            import shutil
            shutil.rmtree(upload_dir)
            return True
        except Exception as e:
            print(f"Error deleting uploaded file: {e}")
    
    return False
