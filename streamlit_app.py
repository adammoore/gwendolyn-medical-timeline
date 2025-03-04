"""
streamlit_app.py

A Streamlit application that:
1. Reads from the knowledge store created by the indexing script.
2. Renders an interactive PHB-centric timeline.
3. Provides a diagnostic journey timeline.
4. Includes patient information.
5. Handles attachments and Evernote links.
6. Provides semantic search across all content.
7. Supports document addition, editing, and merging curation features.
8. Allows category management.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os
import json
import base64
from PIL import Image
import io
from collections import defaultdict
import uuid

# Import our modules
import knowledge_store_reader as ks
import knowledge_store_manager as ksm
import improved_phb_details as phb_details
import patient_info
import evernote_utils
import attachment_processor
import upload_handler
from streamlit_components.streamlit_curation import display_curation_dashboard
from streamlit_components.streamlit_entity_management import display_entity_management_dashboard

# Set page config
st.set_page_config(
    page_title="Gwendolyn's Medical Timeline",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Directory containing Evernote export files
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ATTACHMENTS_DIR = os.path.join(BASE_DIR, "attachments")

# Cache the events to avoid re-loading on every page refresh
@st.cache_data
def get_events():
    """
    Get all events from the knowledge store.
    """
    return ks.get_events()

@st.cache_data
def get_diagnostic_journey():
    """
    Get the diagnostic journey from the knowledge store.
    """
    events = get_events()
    return ks.get_diagnostic_journey(events)

@st.cache_data
def get_patient_info():
    """
    Get patient information from the knowledge store.
    """
    # Try to get from knowledge store first
    ks_patient_info = ks.get_patient_info()
    if ks_patient_info:
        return ks_patient_info
    
    # Fall back to the module
    return patient_info.PATIENT_INFO

@st.cache_data
def get_phb_categories():
    """
    Get PHB categories from the knowledge store.
    """
    # Try to get from knowledge store first
    ks_phb_categories = ks.get_phb_categories()
    if ks_phb_categories:
        return ks_phb_categories
    
    # Fall back to the module
    return phb_details.PHB_CATEGORIES

def get_file_content_as_base64(file_path):
    """
    Get file content as base64 encoded string for embedding in HTML.
    """
    with open(file_path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

def display_attachment(attachment, key_prefix=""):
    """
    Display an attachment based on its mime type.
    
    Parameters:
        attachment (dict): Attachment information.
        key_prefix (str): Prefix for unique keys.
    """
    file_path = attachment["file_path"]
    mime_type = attachment["mime_type"]
    file_name = attachment["file_name"]
    
    # Generate a unique key for this attachment
    unique_key = f"{key_prefix}_{file_name}_{str(uuid.uuid4())}"
    
    if not os.path.exists(file_path):
        st.warning(f"File not found: {file_name}")
        return
    
    if mime_type.startswith("image/"):
        try:
            image = Image.open(file_path)
            st.image(image, caption=file_name)
        except Exception as e:
            st.error(f"Error displaying image: {e}")
            with open(file_path, "rb") as file:
                st.download_button(
                    label=f"Download {file_name}",
                    data=file,
                    file_name=file_name,
                    mime=mime_type,
                    key=f"download_img_{unique_key}"
                )
    
    elif mime_type == "application/pdf":
        # Display PDF using an iframe
        try:
            base64_pdf = get_file_content_as_base64(file_path)
            pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600" type="application/pdf"></iframe>'
            st.markdown(pdf_display, unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Error displaying PDF: {e}")
            # Provide a download link as fallback
            with open(file_path, "rb") as file:
                st.download_button(
                    label=f"Download {file_name}",
                    data=file,
                    file_name=file_name,
                    mime=mime_type,
                    key=f"download_pdf_{unique_key}"
                )
    
    else:
        # For other file types, provide a download link
        with open(file_path, "rb") as file:
            st.download_button(
                label=f"Download {file_name}",
                data=file,
                file_name=file_name,
                mime=mime_type,
                key=f"download_other_{unique_key}"
            )
    
    # Display extracted text if available
    if "extracted_text" in attachment and attachment["extracted_text"]:
        st.markdown("**Extracted Text:**")
        st.text_area(
            "Content", 
            attachment["extracted_text"], 
            height=200,
            key=f"text_{unique_key}"
        )

def display_timeline(events, title="Medical Timeline"):
    """
    Display a timeline of events using Plotly.
    """
    if not events:
        st.warning("No events to display.")
        return
    
    # Create a DataFrame for the timeline
    df = pd.DataFrame([
        {
            "id": event["id"],
            "date": event["date"],
            "title": event["title"],
            "specialty": event["specialty"],
            "age": event["age"],
            "content": event["content"][:100] + "..." if len(event["content"]) > 100 else event["content"]
        }
        for event in events
    ])
    
    # Sort by date
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")
    
    # Create a simple bar chart instead of a timeline
    fig = px.bar(
        df,
        x="date",
        y="specialty",
        color="specialty",
        hover_name="title",
        hover_data=["age", "content"],
        title=title,
        height=600
    )
    
    # Update layout
    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Specialty",
        yaxis={"categoryorder": "category ascending"},
        showlegend=True
    )
    
    # Display the figure
    st.plotly_chart(fig, use_container_width=True)
    
    # Display events as a table
    st.subheader("Events")
    
    # Add clickable links to the DataFrame
    df["View Details"] = df.apply(lambda row: f"[View Details](#{row['id']})", axis=1)
    
    # Display the table
    st.dataframe(
        df[["date", "title", "specialty", "age", "View Details"]],
        use_container_width=True,
        hide_index=True
    )
    
    # Display event details
    for i, event in enumerate(events):
        st.markdown(f"<a id='{event['id']}'></a>", unsafe_allow_html=True)
        with st.expander(f"{event['date']} - {event['title']}"):
            st.markdown(f"**Date:** {event['date']}")
            st.markdown(f"**Age:** {event['age']}")
            st.markdown(f"**Specialty:** {event['specialty']}")
            
            # Display content
            st.markdown("### Content")
            st.markdown(event["content"])
            
            # Display PHB categories
            if "phb_categories" in event and event["phb_categories"]:
                st.markdown("### PHB Categories")
                for category in event["phb_categories"]:
                    st.markdown(f"- **{category['category']}** ({category['severity']}): {category['description']}")
            
            # Display PHB supports
            if "phb_supports" in event and event["phb_supports"]:
                st.markdown("### PHB Supports")
                for support in event["phb_supports"]:
                    st.markdown(f"- **{support['support']}**: {support['description']}")
            
            # Display personnel
            if "personnel" in event and event["personnel"]:
                st.markdown("### Personnel")
                for person in event["personnel"]:
                    st.markdown(f"- **{person['name']}** ({person['type']})")
            
            # Display facilities
            if "facilities" in event and event["facilities"]:
                st.markdown("### Facilities")
                for facility in event["facilities"]:
                    st.markdown(f"- **{facility['name']}** ({facility['type']})")
            
            # Display attachments
            if "attachments" in event and event["attachments"]:
                st.markdown("### Attachments")
                for j, attachment in enumerate(event["attachments"]):
                    st.markdown(f"**{attachment['file_name']}**")
                    display_attachment(attachment, key_prefix=f"event_{i}_attachment_{j}")

def display_phb_categories():
    """
    Display PHB categories.
    """
    st.subheader("Personal Health Budget (PHB) Categories")
    
    # Get PHB categories
    phb_categories = get_phb_categories()
    
    # Create columns for the categories
    cols = st.columns(3)
    
    # Display each category in a card
    for i, (category, info) in enumerate(phb_categories.items()):
        col = cols[i % 3]
        with col:
            st.markdown(f"### {category}")
            st.markdown(f"**Severity:** {info['severity']}")
            st.markdown(f"**Description:** {info['description']}")
            with st.expander("Details"):
                for detail in info['details']:
                    st.markdown(f"- {detail}")

def display_phb_supports():
    """
    Display PHB supports.
    """
    st.subheader("Personal Health Budget (PHB) Supports")
    
    # Create columns for the supports
    cols = st.columns(2)
    
    # Display each support in a card
    for i, (support, info) in enumerate(phb_details.PHB_SUPPORTS.items()):
        col = cols[i % 2]
        with col:
            st.markdown(f"### {support}")
            st.markdown(f"**Description:** {info['description']}")
            with st.expander("Details"):
                for detail in info['details']:
                    st.markdown(f"- {detail}")

def display_patient_info():
    """
    Display patient information.
    """
    st.subheader("Patient Information")
    
    # Get patient info
    patient_info_data = get_patient_info()
    
    # Calculate current age
    dob = patient_info_data.get("dob", "")
    if dob:
        current_age = patient_info.get_age()
        current_age_str = patient_info.format_age(current_age)
    else:
        current_age_str = "Unknown"
    
    # Display basic information
    st.markdown(f"**Name:** {patient_info_data.get('name', 'Unknown')}")
    st.markdown(f"**Date of Birth:** {dob}")
    st.markdown(f"**Current Age:** {current_age_str}")
    st.markdown(f"**Birth Location:** {patient_info_data.get('birth_location', 'Unknown')}")
    
    # Display family information
    st.markdown("### Family")
    for family_member in patient_info_data.get('family', []):
        notes = f" - {family_member['notes']}" if 'notes' in family_member else ""
        st.markdown(f"- **{family_member['name']}** ({family_member['relation']}){notes}")
    
    # Display identifiers if available
    if "identifiers" in patient_info_data and patient_info_data["identifiers"]:
        st.markdown("### Identifiers")
        for key, value in patient_info_data["identifiers"].items():
            st.markdown(f"- **{key.replace('_', ' ').title()}:** {value}")
    
    # Display key dates
    st.markdown("### Key Dates")
    for date_info in patient_info_data.get('key_dates', []):
        st.markdown(f"- **{date_info['date']}:** {date_info['event']} at {date_info['location']}")

def display_search_interface():
    """
    Display search interface.
    """
    st.subheader("Search Medical Records")
    
    # Search input
    query = st.text_input("Enter search query")
    
    if query:
        # Perform semantic search
        results = attachment_processor.semantic_search(query, k=10)
        
        if not results:
            st.warning("No results found.")
            return
        
        # Get events for the search results
        events = get_events()
        search_results = []
        
        for result in results:
            metadata = result.metadata
            event_id = metadata.get("id")
            event = next((e for e in events if e["id"] == event_id), None)
            
            if event:
                result_type = metadata.get("type", "unknown")
                
                if result_type == "event":
                    search_results.append({
                        "type": "event",
                        "event": event,
                        "content": result.page_content,
                        "score": 1.0  # Placeholder for score
                    })
                elif result_type == "attachment":
                    attachment_index = metadata.get("attachment_index", 0)
                    if attachment_index < len(event.get("attachments", [])):
                        attachment = event["attachments"][attachment_index]
                        search_results.append({
                            "type": "attachment",
                            "event": event,
                            "attachment": attachment,
                            "content": result.page_content,
                            "score": 1.0  # Placeholder for score
                        })
        
        # Display search results
        st.subheader(f"Search Results for '{query}'")
        
        for i, result in enumerate(search_results):
            with st.expander(f"Result {i+1}: {result['event']['date']} - {result['event']['title']}"):
                st.markdown(f"**Date:** {result['event']['date']}")
                st.markdown(f"**Type:** {result['type'].title()}")
                
                # Display matching content
                st.markdown("### Matching Content")
                st.markdown(result["content"])
                
                # Display link to event
                st.markdown(f"[View Full Event](#{result['event']['id']})")
                
                # If it's an attachment, display it
                if result["type"] == "attachment":
                    st.markdown("### Attachment")
                    display_attachment(result["attachment"], key_prefix=f"search_result_{i}")

def display_diagnostic_journey():
    """
    Display the diagnostic journey.
    """
    journey = get_diagnostic_journey()
    
    if not journey:
        st.warning("No diagnostic journey to display.")
        return
    
    st.subheader("Diagnostic Journey")
    
    # Create a DataFrame for the journey
    df = pd.DataFrame([
        {
            "id": event["id"],
            "date": event["date"],
            "title": event["title"],
            "specialty": event["specialty"],
            "age": event["age"],
            "new_specialty": "Yes" if event["new_specialty"] else "No",
            "new_diagnosis": "Yes" if event["new_diagnosis"] else "No",
            "diagnoses": ", ".join([d["content"] for d in event["diagnoses"]]) if event["diagnoses"] else "None"
        }
        for event in journey
    ])
    
    # Sort by date
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")
    
    # Create a simple bar chart instead of a timeline
    fig = px.bar(
        df,
        x="date",
        y="specialty",
        color="specialty",
        hover_name="title",
        hover_data=["age", "new_specialty", "new_diagnosis", "diagnoses"],
        title="Diagnostic Journey Timeline",
        height=600
    )
    
    # Update layout
    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Specialty",
        yaxis={"categoryorder": "category ascending"},
        showlegend=True
    )
    
    # Display the figure
    st.plotly_chart(fig, use_container_width=True)
    
    # Display journey as a table
    st.subheader("Diagnostic Events")
    
    # Add clickable links to the DataFrame
    df["View Details"] = df.apply(lambda row: f"[View Details](#{row['id']})", axis=1)
    
    # Display the table
    st.dataframe(
        df[["date", "title", "specialty", "age", "new_specialty", "new_diagnosis", "diagnoses", "View Details"]],
        use_container_width=True,
        hide_index=True
    )

def display_medical_practitioners():
    """
    Display a list of all medical practitioners and their associated resources.
    """
    st.subheader("Medical Practitioners")
    
    events = get_events()
    
    # Collect all personnel from events
    all_personnel = defaultdict(list)
    
    for event in events:
        if "personnel" in event and event["personnel"]:
            for person in event["personnel"]:
                if person["name"] != "Unknown":
                    # Add this event to the person's list
                    all_personnel[person["name"]].append({
                        "event_id": event["id"],
                        "event_date": event["date"],
                        "event_title": event["title"],
                        "specialty": event["specialty"],
                        "person_type": person["type"],
                        "person_specialty": person["specialty"],
                        "attachments": event.get("attachments", [])
                    })
    
    # Sort personnel by name
    sorted_personnel = sorted(all_personnel.items())
    
    # Display each practitioner
    for i, (name, events) in enumerate(sorted_personnel):
        with st.expander(f"{name} ({events[0]['person_type']})"):
            st.markdown(f"**Specialty:** {events[0]['person_specialty']}")
            st.markdown(f"**Number of Interactions:** {len(events)}")
            
            # Display events table
            events_df = pd.DataFrame([
                {
                    "Date": e["event_date"],
                    "Title": e["event_title"],
                    "Specialty": e["specialty"],
                    "Attachments": len(e["attachments"])
                }
                for e in events
            ])
            
            st.dataframe(events_df, use_container_width=True, hide_index=True)
            
            # Display attachments
            all_attachments = []
            for e in events:
                for attachment in e["attachments"]:
                    all_attachments.append({
                        "event_date": e["event_date"],
                        "event_title": e["event_title"],
                        "file_name": attachment["file_name"],
                        "file_path": attachment["file_path"],
                        "mime_type": attachment["mime_type"],
                        "attachment": attachment
                    })
            
            if all_attachments:
                st.markdown("### Related Documents")
                
                for j, attachment_info in enumerate(all_attachments):
                    st.markdown(f"**{attachment_info['event_date']} - {attachment_info['file_name']}**")
                    
                    # Display the attachment with a unique key
                    display_attachment(
                        attachment_info["attachment"], 
                        key_prefix=f"practitioner_{i}_attachment_{j}"
                    )

def display_medical_facilities():
    """
    Display a list of all medical facilities and their associated resources.
    """
    st.subheader("Medical Facilities")
    
    events = get_events()
    
    # Collect all facilities from events
    all_facilities = defaultdict(list)
    
    for event in events:
        if "facilities" in event and event["facilities"]:
            for facility in event["facilities"]:
                if facility["name"] != "Unknown":
                    # Add this event to the facility's list
                    all_facilities[facility["name"]].append({
                        "event_id": event["id"],
                        "event_date": event["date"],
                        "event_title": event["title"],
                        "specialty": event["specialty"],
                        "facility_type": facility["type"],
                        "facility_specialty": facility["specialty"],
                        "attachments": event.get("attachments", [])
                    })
    
    # Sort facilities by name
    sorted_facilities = sorted(all_facilities.items())
    
    # Display each facility
    for i, (name, events) in enumerate(sorted_facilities):
        with st.expander(f"{name} ({events[0]['facility_type']})"):
            st.markdown(f"**Specialty:** {events[0]['facility_specialty']}")
            st.markdown(f"**Number of Interactions:** {len(events)}")
            
            # Display events table
            events_df = pd.DataFrame([
                {
                    "Date": e["event_date"],
                    "Title": e["event_title"],
                    "Specialty": e["specialty"],
                    "Attachments": len(e["attachments"])
                }
                for e in events
            ])
            
            st.dataframe(events_df, use_container_width=True, hide_index=True)
            
            # Display attachments
            all_attachments = []
            for e in events:
                for attachment in e["attachments"]:
                    all_attachments.append({
                        "event_date": e["event_date"],
                        "event_title": e["event_title"],
                        "file_name": attachment["file_name"],
                        "file_path": attachment["file_path"],
                        "mime_type": attachment["mime_type"],
                        "attachment": attachment
                    })
            
            if all_attachments:
                st.markdown("### Related Documents")
                
                for j, attachment_info in enumerate(all_attachments):
                    st.markdown(f"**{attachment_info['event_date']} - {attachment_info['file_name']}**")
                    
                    # Display the attachment with a unique key
                    display_attachment(
                        attachment_info["attachment"], 
                        key_prefix=f"facility_{i}_attachment_{j}"
                    )

def display_system_status():
    """
    Display system status information.
    """
    st.subheader("System Status")
    
    # Get OCR status
    ocr_status = attachment_processor.get_ocr_status()
    
    # Display status in a table
    status_data = {
        "Component": [
            "Tesseract OCR", 
            "PDF to Image Conversion", 
            "OpenCV Image Processing", 
            "DOCX Processing", 
            "PDF Text Extraction",
            "Vector Database"
        ],
        "Status": [
            "✅ Available" if ocr_status["tesseract_available"] else "❌ Not Available",
            "✅ Available" if ocr_status["pdf_image_available"] else "❌ Not Available",
            "✅ Available" if ocr_status["cv2_available"] else "❌ Not Available",
            "✅ Available" if ocr_status["docx_available"] else "❌ Not Available",
            "✅ Available" if ocr_status["pdf_available"] else "❌ Not Available",
            "✅ Available" if ocr_status["vector_db_available"] else "❌ Not Available"
        ]
    }
    
    status_df = pd.DataFrame(status_data)
    st.dataframe(status_df, use_container_width=True, hide_index=True)
    
    # Display knowledge store status
    st.subheader("Knowledge Store Status")
    
    if ks.is_knowledge_store_available():
        try:
            stats = ks.get_knowledge_store_stats()
            
            # Display stats in a table
            stats_data = {
                "Metric": [
                    "Events", 
                    "Notes", 
                    "External Documents", 
                    "Attachments", 
                    "Personnel", 
                    "Facilities",
                    "Specialties",
                    "Date Range",
                    "Last Updated"
                ],
                "Value": [
                    str(stats["events_count"]),
                    str(stats["notes_count"]),
                    str(stats["external_docs_count"]),
                    str(stats["attachment_count"]),
                    str(stats["personnel_count"]),
                    str(stats["facilities_count"]),
                    str(stats["specialties_count"]),
                    str(stats["date_range"]),
                    str(stats["last_updated"])
                ]
            }
            
            stats_df = pd.DataFrame(stats_data)
            st.dataframe(stats_df, use_container_width=True, hide_index=True)
        except Exception as e:
            st.error(f"Error displaying knowledge store stats: {str(e)}")
            st.info("Knowledge store is available but there was an error displaying the statistics.")
    else:
        st.warning("""
        Knowledge store not found. Please run the indexing script to create the knowledge store:
        
        ```
        python index_documents.py
        ```
        """)
    
    # Display installation instructions
    st.markdown("### Installation Instructions")
    
    if not ocr_status["tesseract_available"]:
        st.markdown("""
        #### Tesseract OCR Installation
        
        To enable OCR functionality for images and PDFs, install Tesseract OCR:
        
        - **macOS**: `brew install tesseract`
        - **Ubuntu/Debian**: `apt-get install tesseract-ocr`
        - **Windows**: Download and install from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)
        """)
    
    if not ocr_status["pdf_image_available"]:
        st.markdown("""
        #### Poppler Installation (for PDF processing)
        
        To enable PDF to image conversion for OCR:
        
        - **macOS**: `brew install poppler`
        - **Ubuntu/Debian**: `apt-get install poppler-utils`
        - **Windows**: Download and install from [poppler for Windows](http://blog.alivate.com.au/poppler-windows/)
        """)
    
    # Display note about limited functionality
    if not all([ocr_status["tesseract_available"], ocr_status["pdf_image_available"], ocr_status["cv2_available"]]):
        st.warning("""
        **Note:** Some document processing features are limited due to missing dependencies. 
        The application will still function, but text extraction from images and PDFs will be limited.
        Basic information about documents will still be displayed.
        """)

def main():
    """
    Main function to run the Streamlit app.
    """
    st.title("Gwendolyn's Medical Timeline")
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Go to",
        ["Timeline", "Diagnostic Journey", "Medical Practitioners", "Medical Facilities", 
         "PHB Categories", "PHB Supports", "Patient Info", "Search", "Curation Dashboard", 
         "Entity Management", "System Status"]
    )
    
    # Check if knowledge store is available
    if not ks.is_knowledge_store_available() and page not in ["System Status", "Curation Dashboard"]:
        st.warning("""
        Knowledge store not found. Please run the indexing script to create the knowledge store:
        
        ```
        python index_documents.py
        ```
        
        Switching to System Status page.
        """)
        page = "System Status"
    
    # Display the selected page
    if page == "Timeline":
        events = get_events()
        display_timeline(events, "Complete Medical Timeline")
    
    elif page == "Diagnostic Journey":
        display_diagnostic_journey()
    
    elif page == "Medical Practitioners":
        display_medical_practitioners()
    
    elif page == "Medical Facilities":
        display_medical_facilities()
    
    elif page == "PHB Categories":
        display_phb_categories()
    
    elif page == "PHB Supports":
        display_phb_supports()
    
    elif page == "Patient Info":
        display_patient_info()
    
    elif page == "Search":
        display_search_interface()
    
    elif page == "Curation Dashboard":
        display_curation_dashboard()
    
    elif page == "Entity Management":
        display_entity_management_dashboard()
    
    elif page == "System Status":
        display_system_status()
    
    # Footer
    st.sidebar.markdown("---")
    st.sidebar.markdown("© 2025 Vials Moore Family")

if __name__ == "__main__":
    main()
