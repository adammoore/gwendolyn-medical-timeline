"""
streamlit_curation.py

A module that provides curation components for the Streamlit app, including:
1. Document upload interface
2. Event editing interface
3. Event merging interface
4. Category management interface
"""

import streamlit as st
import os
import uuid
import pandas as pd
from datetime import datetime
import tempfile
import shutil

# Import our modules
import knowledge_store_manager as ksm
import knowledge_store_reader as ks
import upload_handler
import improved_phb_details as phb_details
import attachment_processor

# Clear the cache to reload events after changes
def clear_cache():
    """
    Clear the Streamlit cache to force reloading data.
    """
    st.cache_data.clear()

def display_document_upload():
    """
    Display the document upload interface.
    """
    st.subheader("Upload Documents")
    
    # Get events for associating uploads with existing events
    events = ks.get_events()
    
    # Create tabs for different upload options
    upload_tab, manage_tab = st.tabs(["Upload New Document", "Manage Uploaded Documents"])
    
    with upload_tab:
        # File uploader
        uploaded_file = st.file_uploader("Choose a file to upload", type=["pdf", "png", "jpg", "jpeg", "doc", "docx", "txt", "enex"])
        
        # Event selection
        event_options = ["Create New Event"] + [f"{e['date']} - {e['title']}" for e in events]
        selected_event = st.selectbox("Associate with event", event_options)
        
        # Upload button
        if uploaded_file is not None:
            if st.button("Upload Document"):
                # Save the uploaded file to a temporary location
                with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{uploaded_file.name}") as tmp:
                    tmp.write(uploaded_file.getvalue())
                    temp_file_path = tmp.name
                
                try:
                    # Determine event ID
                    event_id = None
                    if selected_event != "Create New Event":
                        # Extract event ID from the selected event
                        event_index = event_options.index(selected_event) - 1  # Adjust for "Create New Event" option
                        event_id = events[event_index]["id"]
                    
                    # Handle the file upload
                    with open(temp_file_path, "rb") as file:
                        # Create a file-like object that upload_handler can use
                        class UploadedFile:
                            def __init__(self, file, filename):
                                self.file = file
                                self.filename = filename
                            
                            def read(self):
                                return self.file.read()
                        
                        file_obj = UploadedFile(file, uploaded_file.name)
                        result = upload_handler.handle_upload(file_obj, event_id)
                    
                    # Display result
                    if result["success"]:
                        st.success(f"Document uploaded successfully and associated with event ID: {result['event_id']}")
                        # Clear cache to reload events
                        clear_cache()
                    else:
                        st.error(f"Failed to upload document: {result.get('error', 'Unknown error')}")
                
                finally:
                    # Clean up the temporary file
                    if os.path.exists(temp_file_path):
                        os.remove(temp_file_path)
    
    with manage_tab:
        # Get all uploaded files
        uploaded_files = upload_handler.get_uploaded_files()
        
        if not uploaded_files:
            st.info("No uploaded documents found.")
        else:
            # Create a DataFrame for the uploaded files
            df = pd.DataFrame([
                {
                    "ID": file_info["id"],
                    "File Name": file_info["file_name"],
                    "Upload Time": file_info.get("upload_time", "Unknown"),
                    "File Type": file_info.get("file_type", "Unknown"),
                    "Mime Type": file_info.get("mime_type", "Unknown")
                }
                for file_info in uploaded_files
            ])
            
            # Display the table
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Allow deletion of uploaded files
            selected_file_id = st.selectbox("Select file to manage", df["ID"].tolist())
            
            if selected_file_id:
                selected_file = next((f for f in uploaded_files if f["id"] == selected_file_id), None)
                
                if selected_file:
                    st.markdown(f"**Selected File:** {selected_file['file_name']}")
                    
                    # Display file details
                    st.markdown(f"**Upload Time:** {selected_file.get('upload_time', 'Unknown')}")
                    st.markdown(f"**File Type:** {selected_file.get('file_type', 'Unknown')}")
                    st.markdown(f"**Mime Type:** {selected_file.get('mime_type', 'Unknown')}")
                    
                    # Delete button
                    if st.button("Delete File"):
                        if upload_handler.delete_uploaded_file(selected_file_id):
                            st.success(f"File '{selected_file['file_name']}' deleted successfully.")
                            # Clear cache to reload events
                            clear_cache()
                        else:
                            st.error(f"Failed to delete file '{selected_file['file_name']}'.")

def display_event_editing():
    """
    Display the event editing interface.
    """
    st.subheader("Edit Events")
    
    # Get events
    events = ks.get_events()
    
    if not events:
        st.warning("No events found to edit.")
        return
    
    # Create a DataFrame for the events
    df = pd.DataFrame([
        {
            "ID": event["id"],
            "Date": event["date"],
            "Title": event["title"],
            "Specialty": event["specialty"],
            "Age": event["age"],
            "Attachments": len(event.get("attachments", []))
        }
        for event in events
    ])
    
    # Sort by date
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values("Date")
    
    # Display the table
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # Event selection
    selected_event_id = st.selectbox("Select event to edit", df["ID"].tolist())
    
    if selected_event_id:
        # Get the selected event
        event = next((e for e in events if e["id"] == selected_event_id), None)
        
        if event:
            # Create a form for editing
            with st.form("edit_event_form"):
                st.markdown(f"### Editing Event: {event['date']} - {event['title']}")
                
                # Basic event details
                title = st.text_input("Title", event["title"])
                date = st.date_input("Date", datetime.strptime(event["date"], "%Y-%m-%d"))
                specialty = st.text_input("Specialty", event["specialty"])
                content = st.text_area("Content", event["content"], height=300)
                
                # PHB categories
                st.markdown("### PHB Categories")
                
                # Get all categories
                all_categories = ksm.get_categories()
                
                # Get current categories for the event
                event_categories = [cat["category"] for cat in event.get("phb_categories", [])]
                
                # Create checkboxes for each category
                selected_categories = []
                for category, info in all_categories.items():
                    if st.checkbox(f"{category} ({info['severity']})", value=category in event_categories):
                        selected_categories.append(category)
                
                # PHB supports
                st.markdown("### PHB Supports")
                
                # Get current supports for the event
                event_supports = [sup["support"] for sup in event.get("phb_supports", [])]
                
                # Create checkboxes for each support
                selected_supports = []
                for support, info in phb_details.PHB_SUPPORTS.items():
                    if st.checkbox(f"{support}", value=support in event_supports):
                        selected_supports.append(support)
                
                # Submit button
                submit = st.form_submit_button("Update Event")
                
                if submit:
                    # Create updated event data
                    updated_event = event.copy()
                    updated_event["title"] = title
                    updated_event["date"] = date.strftime("%Y-%m-%d")
                    updated_event["specialty"] = specialty
                    updated_event["content"] = content
                    
                    # Update PHB categories
                    updated_phb_categories = []
                    for category in selected_categories:
                        if category in all_categories:
                            updated_phb_categories.append({
                                "category": category,
                                "severity": all_categories[category]["severity"],
                                "description": all_categories[category]["description"]
                            })
                    
                    updated_event["phb_categories"] = updated_phb_categories
                    
                    # Update PHB supports
                    updated_phb_supports = []
                    for support in selected_supports:
                        if support in phb_details.PHB_SUPPORTS:
                            updated_phb_supports.append({
                                "support": support,
                                "description": phb_details.PHB_SUPPORTS[support]["description"]
                            })
                    
                    updated_event["phb_supports"] = updated_phb_supports
                    
                    # Save the updated event
                    if ksm.update_event(selected_event_id, updated_event):
                        st.success("Event updated successfully.")
                        # Clear cache to reload events
                        clear_cache()
                    else:
                        st.error("Failed to update event.")
            
            # Attachment management
            st.markdown("### Manage Attachments")
            
            # Display current attachments
            if "attachments" in event and event["attachments"]:
                for i, attachment in enumerate(event["attachments"]):
                    st.markdown(f"**{i+1}. {attachment['file_name']}**")
                    
                    # Delete attachment button
                    if st.button(f"Delete Attachment {i+1}"):
                        # Create a copy of the event
                        updated_event = event.copy()
                        
                        # Remove the attachment
                        updated_event["attachments"].pop(i)
                        
                        # Save the updated event
                        if ksm.update_event(selected_event_id, updated_event):
                            st.success(f"Attachment '{attachment['file_name']}' deleted successfully.")
                            # Clear cache to reload events
                            clear_cache()
                        else:
                            st.error(f"Failed to delete attachment '{attachment['file_name']}'.")
            else:
                st.info("No attachments found for this event.")
            
            # Add attachment button
            st.markdown("### Add Attachment")
            
            # File uploader for adding attachment
            new_attachment = st.file_uploader("Choose a file to add as attachment", type=["pdf", "png", "jpg", "jpeg", "doc", "docx", "txt"])
            
            if new_attachment is not None:
                if st.button("Add Attachment"):
                    # Save the uploaded file to a temporary location
                    with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{new_attachment.name}") as tmp:
                        tmp.write(new_attachment.getvalue())
                        temp_file_path = tmp.name
                    
                    try:
                        # Handle the file upload
                        with open(temp_file_path, "rb") as file:
                            # Create a file-like object that upload_handler can use
                            class UploadedFile:
                                def __init__(self, file, filename):
                                    self.file = file
                                    self.filename = filename
                                
                                def read(self):
                                    return self.file.read()
                            
                            file_obj = UploadedFile(file, new_attachment.name)
                            result = upload_handler.handle_upload(file_obj, selected_event_id)
                        
                        # Display result
                        if result["success"]:
                            st.success(f"Attachment added successfully to event.")
                            # Clear cache to reload events
                            clear_cache()
                        else:
                            st.error(f"Failed to add attachment: {result.get('error', 'Unknown error')}")
                    
                    finally:
                        # Clean up the temporary file
                        if os.path.exists(temp_file_path):
                            os.remove(temp_file_path)

def display_event_merging():
    """
    Display the event merging interface.
    """
    st.subheader("Merge Events")
    
    # Get events
    events = ks.get_events()
    
    if not events:
        st.warning("No events found to merge.")
        return
    
    # Create a DataFrame for the events
    df = pd.DataFrame([
        {
            "ID": event["id"],
            "Date": event["date"],
            "Title": event["title"],
            "Specialty": event["specialty"],
            "Age": event["age"],
            "Attachments": len(event.get("attachments", []))
        }
        for event in events
    ])
    
    # Sort by date
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values("Date")
    
    # Display the table
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # Create columns for source and target event selection
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Source Event")
        source_event_id = st.selectbox("Select source event", df["ID"].tolist(), key="source_event")
    
    with col2:
        st.markdown("### Target Event")
        # Filter out the source event from the target options
        target_options = [id for id in df["ID"].tolist() if id != source_event_id]
        target_event_id = st.selectbox("Select target event", target_options, key="target_event")
    
    # Display preview of merged event
    if source_event_id and target_event_id:
        # Get the source and target events
        source_event = next((e for e in events if e["id"] == source_event_id), None)
        target_event = next((e for e in events if e["id"] == target_event_id), None)
        
        if source_event and target_event:
            st.markdown("### Merge Preview")
            
            # Display source event details
            st.markdown("#### Source Event")
            st.markdown(f"**Date:** {source_event['date']}")
            st.markdown(f"**Title:** {source_event['title']}")
            st.markdown(f"**Specialty:** {source_event['specialty']}")
            st.markdown(f"**Attachments:** {len(source_event.get('attachments', []))}")
            
            # Display target event details
            st.markdown("#### Target Event")
            st.markdown(f"**Date:** {target_event['date']}")
            st.markdown(f"**Title:** {target_event['title']}")
            st.markdown(f"**Specialty:** {target_event['specialty']}")
            st.markdown(f"**Attachments:** {len(target_event.get('attachments', []))}")
            
            # Display merged event details
            st.markdown("#### Merged Event (Preview)")
            st.markdown(f"**Date:** {source_event['date']}")
            st.markdown(f"**Title:** {source_event['title']} + {target_event['title']}")
            st.markdown(f"**Specialty:** {source_event['specialty']}")
            
            # Calculate total attachments
            total_attachments = len(source_event.get('attachments', [])) + len(target_event.get('attachments', []))
            st.markdown(f"**Attachments:** {total_attachments}")
            
            # Merge button
            if st.button("Merge Events"):
                # Merge the events
                merged_id = ksm.merge_events(source_event_id, target_event_id)
                
                if merged_id:
                    st.success(f"Events merged successfully into event ID: {merged_id}")
                    # Clear cache to reload events
                    clear_cache()
                else:
                    st.error("Failed to merge events.")

def display_category_management():
    """
    Display the category management interface.
    """
    st.subheader("Manage PHB Categories")
    
    # Get categories
    categories = ksm.get_categories()
    
    # Create tabs for different category operations
    list_tab, add_tab = st.tabs(["Edit Categories", "Add New Category"])
    
    with list_tab:
        if not categories:
            st.warning("No categories found.")
        else:
            # Create a DataFrame for the categories
            df = pd.DataFrame([
                {
                    "Category": category,
                    "Severity": info["severity"],
                    "Description": info["description"],
                    "Details": len(info.get("details", []))
                }
                for category, info in categories.items()
            ])
            
            # Display the table
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Category selection
            selected_category = st.selectbox("Select category to edit", list(categories.keys()))
            
            if selected_category:
                # Get the selected category
                category_info = categories[selected_category]
                
                # Create a form for editing
                with st.form("edit_category_form"):
                    st.markdown(f"### Editing Category: {selected_category}")
                    
                    # Category details
                    severity = st.text_input("Severity", category_info["severity"])
                    description = st.text_area("Description", category_info["description"])
                    
                    # Details
                    st.markdown("### Details")
                    details = category_info.get("details", [])
                    
                    # Create text inputs for existing details
                    updated_details = []
                    for i, detail in enumerate(details):
                        detail_input = st.text_input(f"Detail {i+1}", detail)
                        if detail_input:
                            updated_details.append(detail_input)
                    
                    # Add new detail
                    new_detail = st.text_input("New Detail")
                    if new_detail:
                        updated_details.append(new_detail)
                    
                    # Submit button
                    submit = st.form_submit_button("Update Category")
                    
                    if submit:
                        # Create updated category data
                        updated_data = {
                            "severity": severity,
                            "description": description,
                            "details": updated_details
                        }
                        
                        # Save the updated category
                        if ksm.update_category(selected_category, updated_data):
                            st.success(f"Category '{selected_category}' updated successfully.")
                            # Clear cache to reload categories
                            clear_cache()
                        else:
                            st.error(f"Failed to update category '{selected_category}'.")
                
                # Delete category button
                if st.button(f"Delete Category '{selected_category}'"):
                    if ksm.delete_category(selected_category):
                        st.success(f"Category '{selected_category}' deleted successfully.")
                        # Clear cache to reload categories
                        clear_cache()
                    else:
                        st.error(f"Failed to delete category '{selected_category}'.")
    
    with add_tab:
        # Create a form for adding a new category
        with st.form("add_category_form"):
            st.markdown("### Add New Category")
            
            # Category details
            category_name = st.text_input("Category Name")
            severity = st.text_input("Severity")
            description = st.text_area("Description")
            
            # Details
            st.markdown("### Details")
            detail1 = st.text_input("Detail 1")
            detail2 = st.text_input("Detail 2")
            detail3 = st.text_input("Detail 3")
            
            # Submit button
            submit = st.form_submit_button("Add Category")
            
            if submit:
                if not category_name:
                    st.error("Category name is required.")
                else:
                    # Create category data
                    details = [d for d in [detail1, detail2, detail3] if d]
                    category_data = {
                        "severity": severity,
                        "description": description,
                        "details": details
                    }
                    
                    # Add the category
                    if ksm.add_category(category_name, category_data):
                        st.success(f"Category '{category_name}' added successfully.")
                        # Clear cache to reload categories
                        clear_cache()
                    else:
                        st.error(f"Failed to add category '{category_name}'.")

def display_curation_dashboard():
    """
    Display the main curation dashboard.
    """
    st.title("Curation Dashboard")
    
    # Create tabs for different curation features
    upload_tab, edit_tab, merge_tab, category_tab = st.tabs([
        "Document Upload", 
        "Event Editing", 
        "Event Merging", 
        "Category Management"
    ])
    
    with upload_tab:
        display_document_upload()
    
    with edit_tab:
        display_event_editing()
    
    with merge_tab:
        display_event_merging()
    
    with category_tab:
        display_category_management()