"""
evernote_utils.py

Utilities for working with Evernote notes and links.
"""

import re
import os
import base64
import tempfile
import subprocess
import webbrowser
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET

def extract_note_guid(xml_note):
    """
    Extract the GUID from an Evernote note XML element.
    
    Parameters:
        xml_note (Element): XML element representing an Evernote note.
        
    Returns:
        str: The note GUID if found, otherwise None.
    """
    # Try to find the GUID in note-attributes
    if xml_note.find('note-attributes') is not None:
        guid_elem = xml_note.find('note-attributes/source-url')
        if guid_elem is not None and guid_elem.text:
            # Try to extract GUID from source-url
            guid_match = re.search(r'([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})', guid_elem.text)
            if guid_match:
                return guid_match.group(1)
    
    # If not found in note-attributes, check if there's a GUID attribute directly
    guid_elem = xml_note.find('guid')
    if guid_elem is not None and guid_elem.text:
        return guid_elem.text
    
    return None

def generate_evernote_link(note_id, title, guid=None):
    """
    Generate links to open the note in Evernote.
    
    Parameters:
        note_id (str): Note ID.
        title (str): Note title.
        guid (str): Note GUID if available.
        
    Returns:
        dict: Dictionary with different types of Evernote links.
    """
    # Clean the title for use in URLs
    clean_title = re.sub(r'[^a-zA-Z0-9]+', '-', title).strip('-').lower()
    
    links = {
        "app_link": f"evernote:///view/notes/{note_id}",
        "web_share_link": ""
    }
    
    # If we have a GUID, we can create a web share link
    if guid:
        links["web_share_link"] = f"https://share.evernote.com/note/{guid}"
    else:
        # Try to create a web link using the note ID and title
        links["web_link"] = f"https://www.evernote.com/shard/s0/nl/0/{note_id}/{clean_title}"
    
    return links

def open_evernote_note(note_id, links):
    """
    Try to open an Evernote note using various methods.
    
    Parameters:
        note_id (str): Note ID.
        links (dict): Dictionary with different types of Evernote links.
        
    Returns:
        bool: True if successful, False otherwise.
    """
    # Try web share link first if available
    if links.get("web_share_link"):
        try:
            webbrowser.open(links["web_share_link"])
            return True
        except Exception as e:
            print(f"Error opening web share link: {e}")
    
    # Try app link
    try:
        # For macOS
        if os.name == 'posix':
            subprocess.Popen(['open', links["app_link"]])
        # For Windows
        elif os.name == 'nt':
            os.startfile(links["app_link"])
        else:
            webbrowser.open(links["app_link"])
        return True
    except Exception as e:
        print(f"Error opening app link: {e}")
    
    # Try web link if available
    if links.get("web_link"):
        try:
            webbrowser.open(links["web_link"])
            return True
        except Exception as e:
            print(f"Error opening web link: {e}")
    
    return False

def extract_attachments(xml_note):
    """
    Extract attachments from an Evernote note XML element.
    
    Parameters:
        xml_note (Element): XML element representing an Evernote note.
        
    Returns:
        list: List of dictionaries with attachment information.
    """
    attachments = []
    
    # Find all resources (attachments)
    resources = xml_note.findall('resource')
    
    for resource in resources:
        # Get mime type
        mime_elem = resource.find('mime')
        mime_type = mime_elem.text if mime_elem is not None else "application/octet-stream"
        
        # Get file name
        file_name = "attachment"
        resource_attributes = resource.find('resource-attributes')
        if resource_attributes is not None:
            file_name_elem = resource_attributes.find('file-name')
            if file_name_elem is not None and file_name_elem.text:
                file_name = file_name_elem.text
        
        # Get data
        data_elem = resource.find('data')
        if data_elem is not None and data_elem.text:
            # Get the base64-encoded data
            data = base64.b64decode(data_elem.text)
            
            # Get hash for identification
            hash_elem = resource.find('data-hash')
            hash_value = hash_elem.text if hash_elem is not None else None
            
            attachments.append({
                "file_name": file_name,
                "mime_type": mime_type,
                "data": data,
                "hash": hash_value
            })
    
    return attachments

def save_attachment(attachment, output_dir):
    """
    Save an attachment to disk.
    
    Parameters:
        attachment (dict): Attachment information.
        output_dir (str): Directory to save the attachment.
        
    Returns:
        str: Path to the saved attachment.
    """
    # Create the output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate a file path
    file_path = os.path.join(output_dir, attachment["file_name"])
    
    # Ensure the file name is unique
    counter = 1
    base_name, ext = os.path.splitext(file_path)
    while os.path.exists(file_path):
        file_path = f"{base_name}_{counter}{ext}"
        counter += 1
    
    # Write the data to the file
    with open(file_path, 'wb') as f:
        f.write(attachment["data"])
    
    return file_path

def extract_and_save_attachments(xml_note, output_dir):
    """
    Extract and save all attachments from an Evernote note.
    
    Parameters:
        xml_note (Element): XML element representing an Evernote note.
        output_dir (str): Directory to save the attachments.
        
    Returns:
        list: List of dictionaries with saved attachment information.
    """
    attachments = extract_attachments(xml_note)
    saved_attachments = []
    
    for attachment in attachments:
        file_path = save_attachment(attachment, output_dir)
        saved_attachments.append({
            "file_name": attachment["file_name"],
            "mime_type": attachment["mime_type"],
            "file_path": file_path,
            "hash": attachment["hash"]
        })
    
    return saved_attachments

def parse_enex_file_with_guids(file_path):
    """
    Parse an ENEX file and extract notes with their GUIDs.
    
    Parameters:
        file_path (str): Path to the ENEX file.
        
    Returns:
        list: List of tuples (note_element, guid).
    """
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        notes_with_guids = []
        
        for note in root.findall('note'):
            guid = extract_note_guid(note)
            notes_with_guids.append((note, guid))
        
        return notes_with_guids
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
        return []
