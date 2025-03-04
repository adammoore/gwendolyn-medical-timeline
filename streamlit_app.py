"""
streamlit_app.py

A Streamlit application that:
1. Reads Evernote export (.enex) files.
2. Extracts timeline events with PHB integration.
3. Renders an interactive PHB-centric timeline.
4. Provides a diagnostic journey timeline.
5. Includes patient information.
6. Handles attachments and Evernote links.
7. Processes attachments with OCR and adds content to knowledge base.
8. Provides semantic search across all content.
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

# Import our modules
from enex_parser import get_all_events_from_directory, extract_diagnostic_journey
import improved_phb_details as phb_details
import patient_info
import evernote_utils
import attachment_processor

# Set page config
st.set_page_config(
    page_title="Gwendolyn's Medical Timeline",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Directory containing Evernote export files
ENEX_DIR = os.path.dirname(os.path.abspath(__file__))

# Directory for attachments
ATTACHMENTS_DIR = os.path.join(ENEX_DIR, "attachments")

# Cache the events to avoid re-parsing on every page refresh
@st.cache_data
def get_events():
    """
    Get all events, using cache if available.
    """
    return get_all_events_from_directory(ENEX_DIR)

@st.cache_data
def get_diagnostic_journey():
    """
    Get the diagnostic journey, using cache if available.
    """
    events = get_events()
    return extract_diagnostic_journey(events)

def get_file_content_as_base64(file_path):
    """
    Get file content as base64 encoded string for embedding in HTML.
    """
    with open(file_path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

def display_attachment(attachment):
    """
    Display an attachment based on its mime type.
    """
    file_path = attachment["file_path"]
    mime_type = attachment["mime_type"]
    file_name = attachment["file_name"]
    
    if not os.path.exists(file_path):
        st.warning(f"File not found: {file_name}")
        return
    
    if mime_type.startswith("image/"):
        try:
            image = Image.open(file_path)
            st.image(image, caption=file_name)
        except Exception as e:
            st.error(f"Error displaying image: {e}")
    
    elif mime_type == "application/pdf":
        # Display PDF using an iframe
        base64_pdf = get_file_content_as_base64(file_path)
        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600" type="application/pdf"></iframe>'
        st.markdown(pdf_display, unsafe_allow_html=True)
    
    else:
        # For other file types, provide a download link
        with open(file_path, "rb") as file:
            btn = st.download_button(
                label=f"Download {file_name}",
                data=file,
                file_name=file_name,
                mime=mime_type
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
    
    # Create a Plotly figure
    fig = px.timeline(
        df,
        x_start="date",
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
    for event in events:
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
                for attachment in event["attachments"]:
                    st.markdown(f"**{attachment['file_name']}**")
                    display_attachment(attachment)
                    
                    # Display extracted text if available
                    if "extracted_text" in attachment and attachment["extracted_text"]:
                        with st.expander("View Extracted Text"):
                            st.text(attachment["extracted_text"])

def display_phb_categories():
    """
    Display PHB categories.
    """
    st.subheader("Personal Health Budget (PHB) Categories")
    
    # Create columns for the categories
    cols = st.columns(3)
    
    # Display each category in a card
    for i, (category, info) in enumerate(phb_details.PHB_CATEGORIES.items()):
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
    
    # Calculate current age
    current_age = patient_info.get_age()
    current_age_str = patient_info.format_age(current_age)
    
    # Display basic information
    st.markdown(f"**Name:** {patient_info.PATIENT_INFO['name']}")
    st.markdown(f"**Date of Birth:** {patient_info.PATIENT_INFO['dob']}")
    st.markdown(f"**Current Age:** {current_age_str}")
    st.markdown(f"**Birth Location:** {patient_info.PATIENT_INFO['birth_location']}")
    
    # Display family information
    st.markdown("### Family")
    for family_member in patient_info.PATIENT_INFO['family']:
        notes = f" - {family_member['notes']}" if 'notes' in family_member else ""
        st.markdown(f"- **{family_member['name']}** ({family_member['relation']}){notes}")
    
    # Display identifiers if available
    if "identifiers" in patient_info.PATIENT_INFO and patient_info.PATIENT_INFO["identifiers"]:
        st.markdown("### Identifiers")
        for key, value in patient_info.PATIENT_INFO["identifiers"].items():
            st.markdown(f"- **{key.replace('_', ' ').title()}:** {value}")
    
    # Display key dates
    st.markdown("### Key Dates")
    for date_info in patient_info.PATIENT_INFO['key_dates']:
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
                    display_attachment(result["attachment"])

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
    
    # Create a Plotly figure
    fig = px.timeline(
        df,
        x_start="date",
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

def main():
    """
    Main function to run the Streamlit app.
    """
    st.title("Gwendolyn's Medical Timeline")
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Go to",
        ["Timeline", "Diagnostic Journey", "PHB Categories", "PHB Supports", "Patient Info", "Search"]
    )
    
    # Display the selected page
    if page == "Timeline":
        events = get_events()
        display_timeline(events, "Complete Medical Timeline")
    
    elif page == "Diagnostic Journey":
        display_diagnostic_journey()
    
    elif page == "PHB Categories":
        display_phb_categories()
    
    elif page == "PHB Supports":
        display_phb_supports()
    
    elif page == "Patient Info":
        display_patient_info()
    
    elif page == "Search":
        display_search_interface()
    
    # Footer
    st.sidebar.markdown("---")
    st.sidebar.markdown("© 2025 Vials Moore Family")

if __name__ == "__main__":
    main()
