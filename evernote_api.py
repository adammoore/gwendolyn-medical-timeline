"""
evernote_api.py

A module to interact with the Evernote API for retrieving notes and notebooks.
"""

import os
import hashlib
import binascii
import time
from datetime import datetime
import evernote.edam.type.ttypes as Types
from evernote.api.client import EvernoteClient
import evernote.edam.notestore.NoteStore as NoteStore
import evernote.edam.error.ttypes as Errors
import evernote_utils

# Evernote API credentials
EVERNOTE_CONSUMER_KEY = "medtimeline-9556"
EVERNOTE_CONSUMER_SECRET = "158d10b8408319f9b95aed1e668e18b4beaedef24325f08afd5214ad"
EVERNOTE_SANDBOX = False  # Set to True for sandbox environment, False for production

# Directory to save attachments
ATTACHMENTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "attachments")

class EvernoteAPI:
    """
    A class to interact with the Evernote API.
    """
    
    def __init__(self, auth_token=None):
        """
        Initialize the Evernote API client.
        
        Parameters:
            auth_token (str): Evernote authentication token.
        """
        self.auth_token = auth_token
        self.client = None
        self.note_store = None
        self.user_store = None
        self.connected = False
        
        # Initialize the client if auth_token is provided
        if auth_token:
            self.connect(auth_token)
    
    def connect(self, auth_token):
        """
        Connect to the Evernote API.
        
        Parameters:
            auth_token (str): Evernote authentication token.
            
        Returns:
            bool: True if connection successful, False otherwise.
        """
        try:
            # Initialize the client
            self.client = EvernoteClient(
                token=auth_token,
                sandbox=EVERNOTE_SANDBOX,
                china=False  # Set to True for Evernote China service
            )
            
            # Get the note store
            self.note_store = self.client.get_note_store()
            
            # Get the user store
            self.user_store = self.client.get_user_store()
            
            # Test the connection
            user = self.user_store.getUser()
            
            self.auth_token = auth_token
            self.connected = True
            
            return True
        except Exception as e:
            print(f"Error connecting to Evernote API: {e}")
            self.client = None
            self.note_store = None
            self.user_store = None
            self.connected = False
            return False
    
    def get_notebooks(self):
        """
        Get all notebooks.
        
        Returns:
            list: List of notebooks.
        """
        if not self.connected:
            return []
        
        try:
            notebooks = self.note_store.listNotebooks()
            return notebooks
        except Exception as e:
            print(f"Error getting notebooks: {e}")
            return []
    
    def get_notes_in_notebook(self, notebook_guid, max_notes=100, offset=0):
        """
        Get notes in a notebook.
        
        Parameters:
            notebook_guid (str): Notebook GUID.
            max_notes (int): Maximum number of notes to return.
            offset (int): Offset for pagination.
            
        Returns:
            list: List of notes.
        """
        if not self.connected:
            return []
        
        try:
            # Create a filter
            filter = NoteStore.NoteFilter()
            filter.notebookGuid = notebook_guid
            
            # Create a result spec
            result_spec = NoteStore.NotesMetadataResultSpec()
            result_spec.includeTitle = True
            result_spec.includeCreated = True
            result_spec.includeUpdated = True
            result_spec.includeNotebookGuid = True
            result_spec.includeTagGuids = True
            result_spec.includeAttributes = True
            
            # Get the notes
            notes_metadata = self.note_store.findNotesMetadata(
                self.auth_token,
                filter,
                offset,
                max_notes,
                result_spec
            )
            
            return notes_metadata.notes
        except Exception as e:
            print(f"Error getting notes in notebook: {e}")
            return []
    
    def get_note_content(self, note_guid):
        """
        Get the content of a note.
        
        Parameters:
            note_guid (str): Note GUID.
            
        Returns:
            dict: Note content and metadata.
        """
        if not self.connected:
            return None
        
        try:
            # Get the note with content
            note = self.note_store.getNote(
                self.auth_token,
                note_guid,
                True,  # Include content
                True,  # Include resource data
                True,  # Include resource recognition
                True   # Include resource alternate data
            )
            
            # Extract text content from ENML
            text_content = evernote_utils.extract_text_from_content(note.content)
            
            # Extract and save attachments
            attachments = []
            if note.resources:
                note_attachments_dir = os.path.join(ATTACHMENTS_DIR, note_guid)
                os.makedirs(note_attachments_dir, exist_ok=True)
                
                for resource in note.resources:
                    # Get mime type
                    mime_type = resource.mime if resource.mime else "application/octet-stream"
                    
                    # Get file name
                    file_name = "attachment"
                    if resource.attributes and resource.attributes.fileName:
                        file_name = resource.attributes.fileName
                    
                    # Get data
                    data = resource.data.body
                    
                    # Get hash for identification
                    hash_value = binascii.hexlify(resource.data.bodyHash).decode('utf-8')
                    
                    # Save the attachment
                    file_path = os.path.join(note_attachments_dir, file_name)
                    
                    # Ensure the file name is unique
                    counter = 1
                    base_name, ext = os.path.splitext(file_path)
                    while os.path.exists(file_path):
                        file_path = f"{base_name}_{counter}{ext}"
                        counter += 1
                    
                    # Write the data to the file
                    with open(file_path, 'wb') as f:
                        f.write(data)
                    
                    attachments.append({
                        "file_name": file_name,
                        "mime_type": mime_type,
                        "file_path": file_path,
                        "hash": hash_value
                    })
            
            # Generate a unique ID for this note
            note_id = hashlib.md5(f"{note.title}_{note.created}".encode()).hexdigest()
            
            # Generate Evernote links
            evernote_links = evernote_utils.generate_evernote_link(note_id, note.title, note.guid)
            
            # Get tags
            tags = []
            if note.tagGuids:
                for tag_guid in note.tagGuids:
                    try:
                        tag = self.note_store.getTag(self.auth_token, tag_guid)
                        tags.append(tag.name)
                    except Exception as e:
                        print(f"Error getting tag {tag_guid}: {e}")
            
            # Format created and updated timestamps
            created = datetime.fromtimestamp(note.created / 1000).strftime('%Y%m%dT%H%M%SZ')
            updated = datetime.fromtimestamp(note.updated / 1000).strftime('%Y%m%dT%H%M%SZ')
            
            # Create note info
            note_info = {
                "id": note_id,
                "guid": note.guid,
                "title": note.title,
                "content": note.content,
                "text_content": text_content,
                "created": created,
                "updated": updated,
                "tags": tags,
                "notebook_guid": note.notebookGuid,
                "evernote_links": evernote_links,
                "attachments": attachments
            }
            
            # Add source URL if available
            if note.attributes and note.attributes.sourceURL:
                note_info["source_url"] = note.attributes.sourceURL
            
            # Add author if available
            if note.attributes and note.attributes.author:
                note_info["author"] = note.attributes.author
            
            # Add source application if available
            if note.attributes and note.attributes.sourceApplication:
                note_info["source_application"] = note.attributes.sourceApplication
            
            return note_info
        except Exception as e:
            print(f"Error getting note content: {e}")
            return None
    
    def search_notes(self, query, max_notes=100, offset=0):
        """
        Search for notes.
        
        Parameters:
            query (str): Search query.
            max_notes (int): Maximum number of notes to return.
            offset (int): Offset for pagination.
            
        Returns:
            list: List of notes.
        """
        if not self.connected:
            return []
        
        try:
            # Create a filter
            filter = NoteStore.NoteFilter()
            filter.words = query
            
            # Create a result spec
            result_spec = NoteStore.NotesMetadataResultSpec()
            result_spec.includeTitle = True
            result_spec.includeCreated = True
            result_spec.includeUpdated = True
            result_spec.includeNotebookGuid = True
            result_spec.includeTagGuids = True
            result_spec.includeAttributes = True
            
            # Get the notes
            notes_metadata = self.note_store.findNotesMetadata(
                self.auth_token,
                filter,
                offset,
                max_notes,
                result_spec
            )
            
            return notes_metadata.notes
        except Exception as e:
            print(f"Error searching notes: {e}")
            return []
    
    def create_note(self, title, content, notebook_guid=None, tags=None):
        """
        Create a new note.
        
        Parameters:
            title (str): Note title.
            content (str): Note content in ENML format.
            notebook_guid (str): Notebook GUID.
            tags (list): List of tags.
            
        Returns:
            str: GUID of the created note, or None if creation failed.
        """
        if not self.connected:
            return None
        
        try:
            # Create a new note
            note = Types.Note()
            note.title = title
            
            # Set content (must be valid ENML)
            if not content.startswith('<?xml'):
                content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd">
<en-note>{content}</en-note>"""
            
            note.content = content
            
            # Set notebook if provided
            if notebook_guid:
                note.notebookGuid = notebook_guid
            
            # Set tags if provided
            if tags:
                note.tagNames = tags
            
            # Create the note
            created_note = self.note_store.createNote(self.auth_token, note)
            
            return created_note.guid
        except Exception as e:
            print(f"Error creating note: {e}")
            return None
    
    def update_note(self, note_guid, title=None, content=None, tags=None):
        """
        Update an existing note.
        
        Parameters:
            note_guid (str): Note GUID.
            title (str): New title.
            content (str): New content in ENML format.
            tags (list): New list of tags.
            
        Returns:
            bool: True if update successful, False otherwise.
        """
        if not self.connected:
            return False
        
        try:
            # Get the existing note
            note = self.note_store.getNote(
                self.auth_token,
                note_guid,
                True,  # Include content
                False,  # Don't include resource data
                False,  # Don't include resource recognition
                False   # Don't include resource alternate data
            )
            
            # Update title if provided
            if title:
                note.title = title
            
            # Update content if provided
            if content:
                # Set content (must be valid ENML)
                if not content.startswith('<?xml'):
                    content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd">
<en-note>{content}</en-note>"""
                
                note.content = content
            
            # Update tags if provided
            if tags:
                note.tagNames = tags
            
            # Update the note
            self.note_store.updateNote(self.auth_token, note)
            
            return True
        except Exception as e:
            print(f"Error updating note: {e}")
            return False
    
    def delete_note(self, note_guid):
        """
        Delete a note.
        
        Parameters:
            note_guid (str): Note GUID.
            
        Returns:
            bool: True if deletion successful, False otherwise.
        """
        if not self.connected:
            return False
        
        try:
            # Delete the note
            self.note_store.deleteNote(self.auth_token, note_guid)
            
            return True
        except Exception as e:
            print(f"Error deleting note: {e}")
            return False
    
    def get_all_notes_with_tag(self, tag_name, max_notes=1000):
        """
        Get all notes with a specific tag.
        
        Parameters:
            tag_name (str): Tag name.
            max_notes (int): Maximum number of notes to return.
            
        Returns:
            list: List of notes.
        """
        if not self.connected:
            return []
        
        try:
            # Find the tag by name
            tag = None
            tags = self.note_store.listTags(self.auth_token)
            
            for t in tags:
                if t.name.lower() == tag_name.lower():
                    tag = t
                    break
            
            if not tag:
                return []
            
            # Create a filter
            filter = NoteStore.NoteFilter()
            filter.tagGuids = [tag.guid]
            
            # Create a result spec
            result_spec = NoteStore.NotesMetadataResultSpec()
            result_spec.includeTitle = True
            result_spec.includeCreated = True
            result_spec.includeUpdated = True
            result_spec.includeNotebookGuid = True
            result_spec.includeTagGuids = True
            result_spec.includeAttributes = True
            
            # Get the notes
            notes_metadata = self.note_store.findNotesMetadata(
                self.auth_token,
                filter,
                0,
                max_notes,
                result_spec
            )
            
            return notes_metadata.notes
        except Exception as e:
            print(f"Error getting notes with tag: {e}")
            return []
    
    def get_all_notes_with_keyword(self, keyword, max_notes=1000):
        """
        Get all notes containing a specific keyword.
        
        Parameters:
            keyword (str): Keyword to search for.
            max_notes (int): Maximum number of notes to return.
            
        Returns:
            list: List of notes.
        """
        return self.search_notes(keyword, max_notes)
    
    def get_all_gwendolyn_notes(self, max_notes=1000):
        """
        Get all notes related to Gwendolyn.
        
        Parameters:
            max_notes (int): Maximum number of notes to return.
            
        Returns:
            list: List of notes.
        """
        # Search for notes with "gwen" or "gwendolyn" in the title or content
        gwen_notes = self.search_notes("intitle:gwen OR intitle:gwendolyn OR gwen OR gwendolyn", max_notes)
        
        # Also search for notes with the "gwen" or "gwendolyn" tag
        gwen_tag_notes = []
        try:
            gwen_tag_notes = self.get_all_notes_with_tag("gwen", max_notes)
        except Exception:
            pass
        
        try:
            gwendolyn_tag_notes = self.get_all_notes_with_tag("gwendolyn", max_notes)
            gwen_tag_notes.extend(gwendolyn_tag_notes)
        except Exception:
            pass
        
        # Combine the results, removing duplicates
        all_notes = gwen_notes
        
        # Add notes from tags if they're not already in the list
        existing_guids = {note.guid for note in all_notes}
        
        for note in gwen_tag_notes:
            if note.guid not in existing_guids:
                all_notes.append(note)
                existing_guids.add(note.guid)
        
        return all_notes
    
    def get_note_content_batch(self, note_guids):
        """
        Get the content of multiple notes.
        
        Parameters:
            note_guids (list): List of note GUIDs.
            
        Returns:
            list: List of note content and metadata.
        """
        if not self.connected:
            return []
        
        note_contents = []
        
        for guid in note_guids:
            try:
                note_content = self.get_note_content(guid)
                if note_content:
                    note_contents.append(note_content)
                
                # Add a small delay to avoid rate limiting
                time.sleep(0.1)
            except Exception as e:
                print(f"Error getting content for note {guid}: {e}")
        
        return note_contents

# Create a singleton instance
evernote_api = EvernoteAPI()

def connect_to_evernote(auth_token):
    """
    Connect to the Evernote API.
    
    Parameters:
        auth_token (str): Evernote authentication token.
        
    Returns:
        bool: True if connection successful, False otherwise.
    """
    return evernote_api.connect(auth_token)

def get_all_gwendolyn_notes():
    """
    Get all notes related to Gwendolyn.
    
    Returns:
        list: List of notes.
    """
    return evernote_api.get_all_gwendolyn_notes()

def get_note_content(note_guid):
    """
    Get the content of a note.
    
    Parameters:
        note_guid (str): Note GUID.
        
    Returns:
        dict: Note content and metadata.
    """
    return evernote_api.get_note_content(note_guid)

def get_note_content_batch(note_guids):
    """
    Get the content of multiple notes.
    
    Parameters:
        note_guids (list): List of note GUIDs.
        
    Returns:
        list: List of note content and metadata.
    """
    return evernote_api.get_note_content_batch(note_guids)

def search_notes(query, max_notes=100):
    """
    Search for notes.
    
    Parameters:
        query (str): Search query.
        max_notes (int): Maximum number of notes to return.
        
    Returns:
        list: List of notes.
    """
    return evernote_api.search_notes(query, max_notes)

def get_notebooks():
    """
    Get all notebooks.
    
    Returns:
        list: List of notebooks.
    """
    return evernote_api.get_notebooks()

def get_notes_in_notebook(notebook_guid, max_notes=100):
    """
    Get notes in a notebook.
    
    Parameters:
        notebook_guid (str): Notebook GUID.
        max_notes (int): Maximum number of notes to return.
        
    Returns:
        list: List of notes.
    """
    return evernote_api.get_notes_in_notebook(notebook_guid, max_notes)

def create_note(title, content, notebook_guid=None, tags=None):
    """
    Create a new note.
    
    Parameters:
        title (str): Note title.
        content (str): Note content in ENML format.
        notebook_guid (str): Notebook GUID.
        tags (list): List of tags.
        
    Returns:
        str: GUID of the created note, or None if creation failed.
    """
    return evernote_api.create_note(title, content, notebook_guid, tags)

def update_note(note_guid, title=None, content=None, tags=None):
    """
    Update an existing note.
    
    Parameters:
        note_guid (str): Note GUID.
        title (str): New title.
        content (str): New content in ENML format.
        tags (list): New list of tags.
        
    Returns:
        bool: True if update successful, False otherwise.
    """
    return evernote_api.update_note(note_guid, title, content, tags)

def delete_note(note_guid):
    """
    Delete a note.
    
    Parameters:
        note_guid (str): Note GUID.
        
    Returns:
        bool: True if deletion successful, False otherwise.
    """
    return evernote_api.delete_note(note_guid)

def index_evernote_notes():
    """
    Index all Gwendolyn-related notes from Evernote.
    
    Returns:
        list: List of indexed notes.
    """
    # Get all Gwendolyn-related notes
    metadata_notes = get_all_gwendolyn_notes()
    
    if not metadata_notes:
        print("No Gwendolyn-related notes found in Evernote.")
        return []
    
    print(f"Found {len(metadata_notes)} Gwendolyn-related notes in Evernote.")
    
    # Get the content of each note
    note_guids = [note.guid for note in metadata_notes]
    notes = get_note_content_batch(note_guids)
    
    print(f"Retrieved content for {len(notes)} notes.")
    
    return notes
