"""
streamlit_evernote.py

A module that provides Evernote integration components for the Streamlit app, including:
1. Evernote authentication
2. Notebook and note browsing
3. Note import and indexing
4. Direct note access
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import os
import tempfile
import shutil
import time

# Import our modules
import evernote_api
import knowledge_store_manager as ksm
import knowledge_store_reader as ks
import index_documents
import attachment_processor

# Clear the cache to reload events after changes
def clear_cache():
    """
    Clear the Streamlit cache to force reloading data.
    """
    st.cache_data.clear()

def display_evernote_authentication():
    """
    Display the Evernote authentication interface.
    """
    st.subheader("Evernote Authentication")
    
    # Check if already authenticated
    if "evernote_authenticated" in st.session_state and st.session_state["evernote_authenticated"]:
        st.success("Connected to Evernote API")
        
        # Display logout button
        if st.button("Disconnect from Evernote"):
            st.session_state["evernote_authenticated"] = False
            st.session_state["evernote_auth_token"] = None
            st.rerun()
    else:
        # Display authentication form
        st.markdown("""
        To connect to Evernote, you need to provide your authentication token.
        
        Your Evernote authentication token is already set in the application:
        - Consumer Key: medtimeline-9556
        - Consumer Secret: 158d10b8408319f9b95aed1e668e18b4beaedef24325f08afd5214ad
        """)
        
        # Auth token input
        auth_token = st.text_input("Enter your Evernote authentication token (optional)", 
                                  value=st.session_state.get("evernote_auth_token", ""),
                                  type="password")
        
        # Connect button
        if st.button("Connect to Evernote"):
            if auth_token:
                with st.spinner("Connecting to Evernote..."):
                    if evernote_api.connect_to_evernote(auth_token):
                        st.session_state["evernote_authenticated"] = True
                        st.session_state["evernote_auth_token"] = auth_token
                        st.success("Successfully connected to Evernote API")
                        st.rerun()
                    else:
                        st.error("Failed to connect to Evernote API. Please check your authentication token.")
            else:
                st.warning("Please enter your Evernote authentication token.")

def display_notebook_browser():
    """
    Display the Evernote notebook browser.
    """
    st.subheader("Evernote Notebooks")
    
    # Check if authenticated
    if "evernote_authenticated" not in st.session_state or not st.session_state["evernote_authenticated"]:
        st.warning("Please authenticate with Evernote first.")
        return
    
    # Get notebooks
    with st.spinner("Loading notebooks..."):
        notebooks = evernote_api.get_notebooks()
    
    if not notebooks:
        st.warning("No notebooks found.")
        return
    
    # Create a DataFrame for the notebooks
    df = pd.DataFrame([
        {
            "Name": notebook.name,
            "GUID": notebook.guid,
            "Default": "Yes" if notebook.defaultNotebook else "No"
        }
        for notebook in notebooks
    ])
    
    # Sort by name
    df = df.sort_values("Name")
    
    # Display the table
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # Notebook selection
    selected_notebook = st.selectbox("Select notebook to browse", [notebook.name for notebook in notebooks])
    
    if selected_notebook:
        # Get the selected notebook
        notebook = next((n for n in notebooks if n.name == selected_notebook), None)
        
        if notebook:
            st.markdown(f"### Notes in {notebook.name}")
            
            # Get notes in the notebook
            with st.spinner(f"Loading notes from {notebook.name}..."):
                notes = evernote_api.get_notes_in_notebook(notebook.guid)
            
            if not notes:
                st.info(f"No notes found in {notebook.name}.")
                return
            
            # Create a DataFrame for the notes
            notes_df = pd.DataFrame([
                {
                    "Title": note.title,
                    "GUID": note.guid,
                    "Created": datetime.fromtimestamp(note.created / 1000).strftime('%Y-%m-%d'),
                    "Updated": datetime.fromtimestamp(note.updated / 1000).strftime('%Y-%m-%d')
                }
                for note in notes
            ])
            
            # Sort by created date (newest first)
            notes_df["Created"] = pd.to_datetime(notes_df["Created"])
            notes_df = notes_df.sort_values("Created", ascending=False)
            
            # Display the table
            st.dataframe(notes_df, use_container_width=True, hide_index=True)
            
            # Note selection
            selected_note_guid = st.selectbox("Select note to view", notes_df["GUID"].tolist())
            
            if selected_note_guid:
                # Get the note content
                with st.spinner("Loading note content..."):
                    note_content = evernote_api.get_note_content(selected_note_guid)
                
                if note_content:
                    st.markdown(f"### {note_content['title']}")
                    st.markdown(f"**Created:** {datetime.strptime(note_content['created'], '%Y%m%dT%H%M%SZ').strftime('%Y-%m-%d %H:%M:%S')}")
                    st.markdown(f"**Updated:** {datetime.strptime(note_content['updated'], '%Y%m%dT%H%M%SZ').strftime('%Y-%m-%d %H:%M:%S')}")
                    
                    # Display tags
                    if note_content["tags"]:
                        st.markdown(f"**Tags:** {', '.join(note_content['tags'])}")
                    
                    # Display content
                    st.markdown("### Content")
                    st.text_area("Note Content", note_content["text_content"], height=300)
                    
                    # Display attachments
                    if note_content["attachments"]:
                        st.markdown("### Attachments")
                        for i, attachment in enumerate(note_content["attachments"]):
                            st.markdown(f"**{i+1}. {attachment['file_name']}**")
                            
                            # Display attachment download link
                            with open(attachment["file_path"], "rb") as file:
                                st.download_button(
                                    label=f"Download {attachment['file_name']}",
                                    data=file,
                                    file_name=attachment['file_name'],
                                    mime=attachment['mime_type'],
                                    key=f"download_{i}"
                                )
                    
                    # Import button
                    if st.button("Import Note to Knowledge Store"):
                        with st.spinner("Importing note..."):
                            # Create a temporary directory for the note
                            with tempfile.TemporaryDirectory() as temp_dir:
                                # Create a temporary ENEX file
                                temp_enex_path = os.path.join(temp_dir, f"{note_content['title']}.enex")
                                
                                # Create a simple ENEX file with just this note
                                with open(temp_enex_path, "w") as f:
                                    f.write(f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE en-export SYSTEM "http://xml.evernote.com/pub/evernote-export3.dtd">
<en-export export-date="{datetime.now().strftime('%Y%m%dT%H%M%SZ')}" application="Evernote" version="10.56.9">
<note>
<title>{note_content['title']}</title>
<content>{note_content['content']}</content>
<created>{note_content['created']}</created>
<updated>{note_content['updated']}</updated>
<note-attributes>
<source-url>{note_content.get('source_url', '')}</source-url>
<source-application>{note_content.get('source_application', '')}</source-application>
<author>{note_content.get('author', '')}</author>
</note-attributes>
""")
                                    
                                    # Add tags
                                    for tag in note_content["tags"]:
                                        f.write(f"<tag>{tag}</tag>\n")
                                    
                                    f.write("</note>\n</en-export>")
                                
                                # Copy the ENEX file to the project directory
                                project_enex_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), f"{note_content['title']}.enex")
                                shutil.copy2(temp_enex_path, project_enex_path)
                                
                                # Copy attachments
                                for attachment in note_content["attachments"]:
                                    # Create attachment directory if it doesn't exist
                                    attachment_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "attachments", note_content["id"])
                                    os.makedirs(attachment_dir, exist_ok=True)
                                    
                                    # Copy attachment
                                    dest_path = os.path.join(attachment_dir, attachment["file_name"])
                                    shutil.copy2(attachment["file_path"], dest_path)
                            
                            # Run the indexing script on the new ENEX file
                            result = index_documents.run_indexing(enex_only=True)
                            
                            if result:
                                st.success(f"Note '{note_content['title']}' imported successfully.")
                                # Clear cache to reload events
                                clear_cache()
                            else:
                                st.error(f"Failed to import note '{note_content['title']}'.")

def display_note_search():
    """
    Display the Evernote note search interface.
    """
    st.subheader("Search Evernote Notes")
    
    # Check if authenticated
    if "evernote_authenticated" not in st.session_state or not st.session_state["evernote_authenticated"]:
        st.warning("Please authenticate with Evernote first.")
        return
    
    # Search input
    query = st.text_input("Enter search query")
    
    if query:
        # Perform search
        with st.spinner(f"Searching for '{query}'..."):
            notes = evernote_api.search_notes(query)
        
        if not notes:
            st.info(f"No notes found for '{query}'.")
            return
        
        # Create a DataFrame for the notes
        notes_df = pd.DataFrame([
            {
                "Title": note.title,
                "GUID": note.guid,
                "Created": datetime.fromtimestamp(note.created / 1000).strftime('%Y-%m-%d'),
                "Updated": datetime.fromtimestamp(note.updated / 1000).strftime('%Y-%m-%d')
            }
            for note in notes
        ])
        
        # Sort by created date (newest first)
        notes_df["Created"] = pd.to_datetime(notes_df["Created"])
        notes_df = notes_df.sort_values("Created", ascending=False)
        
        # Display the table
        st.dataframe(notes_df, use_container_width=True, hide_index=True)
        
        # Note selection
        selected_note_guid = st.selectbox("Select note to view", notes_df["GUID"].tolist())
        
        if selected_note_guid:
            # Get the note content
            with st.spinner("Loading note content..."):
                note_content = evernote_api.get_note_content(selected_note_guid)
            
            if note_content:
                st.markdown(f"### {note_content['title']}")
                st.markdown(f"**Created:** {datetime.strptime(note_content['created'], '%Y%m%dT%H%M%SZ').strftime('%Y-%m-%d %H:%M:%S')}")
                st.markdown(f"**Updated:** {datetime.strptime(note_content['updated'], '%Y%m%dT%H%M%SZ').strftime('%Y-%m-%d %H:%M:%S')}")
                
                # Display tags
                if note_content["tags"]:
                    st.markdown(f"**Tags:** {', '.join(note_content['tags'])}")
                
                # Display content
                st.markdown("### Content")
                st.text_area("Note Content", note_content["text_content"], height=300)
                
                # Display attachments
                if note_content["attachments"]:
                    st.markdown("### Attachments")
                    for i, attachment in enumerate(note_content["attachments"]):
                        st.markdown(f"**{i+1}. {attachment['file_name']}**")
                        
                        # Display attachment download link
                        with open(attachment["file_path"], "rb") as file:
                            st.download_button(
                                label=f"Download {attachment['file_name']}",
                                data=file,
                                file_name=attachment['file_name'],
                                mime=attachment['mime_type'],
                                key=f"download_search_{i}"
                            )
                
                # Import button
                if st.button("Import Note to Knowledge Store"):
                    with st.spinner("Importing note..."):
                        # Create a temporary directory for the note
                        with tempfile.TemporaryDirectory() as temp_dir:
                            # Create a temporary ENEX file
                            temp_enex_path = os.path.join(temp_dir, f"{note_content['title']}.enex")
                            
                            # Create a simple ENEX file with just this note
                            with open(temp_enex_path, "w") as f:
                                f.write(f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE en-export SYSTEM "http://xml.evernote.com/pub/evernote-export3.dtd">
<en-export export-date="{datetime.now().strftime('%Y%m%dT%H%M%SZ')}" application="Evernote" version="10.56.9">
<note>
<title>{note_content['title']}</title>
<content>{note_content['content']}</content>
<created>{note_content['created']}</created>
<updated>{note_content['updated']}</updated>
<note-attributes>
<source-url>{note_content.get('source_url', '')}</source-url>
<source-application>{note_content.get('source_application', '')}</source-application>
<author>{note_content.get('author', '')}</author>
</note-attributes>
""")
                                
                                # Add tags
                                for tag in note_content["tags"]:
                                    f.write(f"<tag>{tag}</tag>\n")
                                
                                f.write("</note>\n</en-export>")
                            
                            # Copy the ENEX file to the project directory
                            project_enex_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), f"{note_content['title']}.enex")
                            shutil.copy2(temp_enex_path, project_enex_path)
                            
                            # Copy attachments
                            for attachment in note_content["attachments"]:
                                # Create attachment directory if it doesn't exist
                                attachment_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "attachments", note_content["id"])
                                os.makedirs(attachment_dir, exist_ok=True)
                                
                                # Copy attachment
                                dest_path = os.path.join(attachment_dir, attachment["file_name"])
                                shutil.copy2(attachment["file_path"], dest_path)
                        
                        # Run the indexing script on the new ENEX file
                        result = index_documents.run_indexing(enex_only=True)
                        
                        if result:
                            st.success(f"Note '{note_content['title']}' imported successfully.")
                            # Clear cache to reload events
                            clear_cache()
                        else:
                            st.error(f"Failed to import note '{note_content['title']}'.")

def display_bulk_import():
    """
    Display the bulk import interface.
    """
    st.subheader("Bulk Import from Evernote")
    
    # Check if authenticated
    if "evernote_authenticated" not in st.session_state or not st.session_state["evernote_authenticated"]:
        st.warning("Please authenticate with Evernote first.")
        return
    
    st.markdown("""
    This tool allows you to import all Gwendolyn-related notes from Evernote.
    
    Notes will be identified by:
    - Having "Gwen" or "Gwendolyn" in the title or content
    - Having the "Gwen" or "Gwendolyn" tag
    
    This process may take several minutes depending on the number of notes.
    """)
    
    # Import button
    if st.button("Start Bulk Import"):
        with st.spinner("Searching for Gwendolyn-related notes..."):
            # Get all Gwendolyn-related notes
            metadata_notes = evernote_api.get_all_gwendolyn_notes()
            
            if not metadata_notes:
                st.warning("No Gwendolyn-related notes found in Evernote.")
                return
            
            st.info(f"Found {len(metadata_notes)} Gwendolyn-related notes in Evernote.")
            
            # Create a progress bar
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Create a temporary directory for the notes
            with tempfile.TemporaryDirectory() as temp_dir:
                # Create a combined ENEX file
                combined_enex_path = os.path.join(temp_dir, "gwendolyn_notes.enex")
                
                # Start the ENEX file
                with open(combined_enex_path, "w") as f:
                    f.write(f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE en-export SYSTEM "http://xml.evernote.com/pub/evernote-export3.dtd">
<en-export export-date="{datetime.now().strftime('%Y%m%dT%H%M%SZ')}" application="Evernote" version="10.56.9">
""")
                
                # Process each note
                for i, metadata_note in enumerate(metadata_notes):
                    # Update progress
                    progress = (i + 1) / len(metadata_notes)
                    progress_bar.progress(progress)
                    status_text.text(f"Processing note {i+1} of {len(metadata_notes)}: {metadata_note.title}")
                    
                    # Get the note content
                    note_content = evernote_api.get_note_content(metadata_note.guid)
                    
                    if note_content:
                        # Add the note to the ENEX file
                        with open(combined_enex_path, "a") as f:
                            f.write(f"""<note>
<title>{note_content['title']}</title>
<content>{note_content['content']}</content>
<created>{note_content['created']}</created>
<updated>{note_content['updated']}</updated>
<note-attributes>
<source-url>{note_content.get('source_url', '')}</source-url>
<source-application>{note_content.get('source_application', '')}</source-application>
<author>{note_content.get('author', '')}</author>
</note-attributes>
""")
                            
                            # Add tags
                            for tag in note_content["tags"]:
                                f.write(f"<tag>{tag}</tag>\n")
                            
                            f.write("</note>\n")
                        
                        # Copy attachments
                        for attachment in note_content["attachments"]:
                            # Create attachment directory if it doesn't exist
                            attachment_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "attachments", note_content["id"])
                            os.makedirs(attachment_dir, exist_ok=True)
                            
                            # Copy attachment
                            dest_path = os.path.join(attachment_dir, attachment["file_name"])
                            shutil.copy2(attachment["file_path"], dest_path)
                    
                    # Add a small delay to avoid rate limiting
                    time.sleep(0.1)
                
                # Finish the ENEX file
                with open(combined_enex_path, "a") as f:
                    f.write("</en-export>")
                
                # Copy the ENEX file to the project directory
                project_enex_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "gwendolyn_notes.enex")
                shutil.copy2(combined_enex_path, project_enex_path)
            
            # Run the indexing script on the new ENEX file
            status_text.text("Running indexing on imported notes...")
            result = index_documents.run_indexing(enex_only=True)
            
            if result:
                st.success(f"Successfully imported {len(metadata_notes)} notes from Evernote.")
                # Clear cache to reload events
                clear_cache()
            else:
                st.error("Failed to index imported notes.")

def display_evernote_dashboard():
    """
    Display the main Evernote dashboard.
    """
    st.title("Evernote Integration")
    
    # Create tabs for different Evernote features
    auth_tab, notebook_tab, search_tab, bulk_tab = st.tabs([
        "Authentication", 
        "Browse Notebooks", 
        "Search Notes", 
        "Bulk Import"
    ])
    
    with auth_tab:
        display_evernote_authentication()
    
    with notebook_tab:
        display_notebook_browser()
    
    with search_tab:
        display_note_search()
    
    with bulk_tab:
        display_bulk_import()
