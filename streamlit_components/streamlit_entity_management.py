"""
streamlit_entity_management.py

A module that provides entity management components for the Streamlit app, including:
1. Practitioner management (view, edit, merge)
2. Facility management
3. Specialty management
4. Entity normalization and standardization
"""

import streamlit as st
import pandas as pd
import re
from datetime import datetime
import uuid

# Import our modules
import knowledge_store_manager as ksm
import knowledge_store_reader as ks
import improved_phb_details as phb_details

# Clear the cache to reload events after changes
def clear_cache():
    """
    Clear the Streamlit cache to force reloading data.
    """
    st.cache_data.clear()

def normalize_name(name):
    """
    Normalize a name by removing extra spaces, titles, etc.
    
    Parameters:
        name (str): The name to normalize.
        
    Returns:
        str: The normalized name.
    """
    if not name:
        return ""
    
    # Convert to lowercase
    name = name.lower()
    
    # Remove titles
    titles = ["dr", "dr.", "doctor", "prof", "prof.", "professor", "mr", "mr.", "mrs", "mrs.", "ms", "ms.", "miss"]
    for title in titles:
        if name.startswith(title + " "):
            name = name[len(title) + 1:]
    
    # Remove extra spaces
    name = re.sub(r'\s+', ' ', name).strip()
    
    # Capitalize first letter of each word
    name = name.title()
    
    return name

@st.cache_data
def get_all_practitioners():
    """
    Get all practitioners from all events.
    
    Returns:
        dict: Dictionary of practitioners with counts and event references.
    """
    events = ks.get_events()
    
    # Collect all personnel from events
    all_personnel = {}
    
    for event in events:
        if "personnel" in event and event["personnel"]:
            for person in event["personnel"]:
                if person["name"] != "Unknown":
                    name = person["name"]
                    
                    if name not in all_personnel:
                        all_personnel[name] = {
                            "name": name,
                            "normalized_name": normalize_name(name),
                            "type": person["type"],
                            "specialty": person["specialty"],
                            "count": 0,
                            "events": []
                        }
                    
                    all_personnel[name]["count"] += 1
                    all_personnel[name]["events"].append({
                        "event_id": event["id"],
                        "event_date": event["date"],
                        "event_title": event["title"]
                    })
    
    return all_personnel

@st.cache_data
def get_all_facilities():
    """
    Get all facilities from all events.
    
    Returns:
        dict: Dictionary of facilities with counts and event references.
    """
    events = ks.get_events()
    
    # Collect all facilities from events
    all_facilities = {}
    
    for event in events:
        if "facilities" in event and event["facilities"]:
            for facility in event["facilities"]:
                if facility["name"] != "Unknown":
                    name = facility["name"]
                    
                    if name not in all_facilities:
                        all_facilities[name] = {
                            "name": name,
                            "normalized_name": normalize_name(name),
                            "type": facility["type"],
                            "specialty": facility["specialty"],
                            "count": 0,
                            "events": []
                        }
                    
                    all_facilities[name]["count"] += 1
                    all_facilities[name]["events"].append({
                        "event_id": event["id"],
                        "event_date": event["date"],
                        "event_title": event["title"]
                    })
    
    return all_facilities

@st.cache_data
def find_similar_practitioners(practitioners):
    """
    Find practitioners with similar names.
    
    Parameters:
        practitioners (dict): Dictionary of practitioners.
        
    Returns:
        list: List of groups of similar practitioners.
    """
    similar_groups = []
    processed = set()
    
    for name1, info1 in practitioners.items():
        if name1 in processed:
            continue
        
        group = [name1]
        normalized1 = info1["normalized_name"]
        
        # Skip if name is too short (likely an initial)
        if len(normalized1) <= 2:
            continue
        
        # Find similar names
        for name2, info2 in practitioners.items():
            if name1 != name2 and name2 not in processed:
                normalized2 = info2["normalized_name"]
                
                # Check if names are similar
                if normalized1 and normalized2:
                    # Check if one name is contained in the other
                    if normalized1 in normalized2 or normalized2 in normalized1:
                        group.append(name2)
                    # Check if they share the same last name
                    elif normalized1.split()[-1] == normalized2.split()[-1]:
                        # Check if first initials match
                        if normalized1[0] == normalized2[0]:
                            group.append(name2)
        
        if len(group) > 1:
            similar_groups.append(group)
            processed.update(group)
    
    return similar_groups

def merge_practitioners(source_name, target_name):
    """
    Merge two practitioners by updating all events.
    
    Parameters:
        source_name (str): The name to merge from.
        target_name (str): The name to merge to.
        
    Returns:
        bool: True if successful, False otherwise.
    """
    if source_name == target_name:
        return False
    
    # Create a backup first
    backup_dir = ksm.backup_knowledge_store()
    if not backup_dir:
        return False
    
    # Get all events
    events = ks.get_events()
    updated = False
    
    # Update personnel in all events
    for event in events:
        if "personnel" in event and event["personnel"]:
            event_updated = False
            
            # Check if source name exists in this event
            for i, person in enumerate(event["personnel"]):
                if person["name"] == source_name:
                    # Replace with target name
                    event["personnel"][i]["name"] = target_name
                    event_updated = True
            
            # If event was updated, save it
            if event_updated:
                updated = True
                ksm.update_event(event["id"], event)
    
    # If any events were updated, rebuild the vector store
    if updated:
        ksm.rebuild_vector_store()
    
    return updated

def merge_facilities(source_name, target_name):
    """
    Merge two facilities by updating all events.
    
    Parameters:
        source_name (str): The name to merge from.
        target_name (str): The name to merge to.
        
    Returns:
        bool: True if successful, False otherwise.
    """
    if source_name == target_name:
        return False
    
    # Create a backup first
    backup_dir = ksm.backup_knowledge_store()
    if not backup_dir:
        return False
    
    # Get all events
    events = ks.get_events()
    updated = False
    
    # Update facilities in all events
    for event in events:
        if "facilities" in event and event["facilities"]:
            event_updated = False
            
            # Check if source name exists in this event
            for i, facility in enumerate(event["facilities"]):
                if facility["name"] == source_name:
                    # Replace with target name
                    event["facilities"][i]["name"] = target_name
                    event_updated = True
            
            # If event was updated, save it
            if event_updated:
                updated = True
                ksm.update_event(event["id"], event)
    
    # If any events were updated, rebuild the vector store
    if updated:
        ksm.rebuild_vector_store()
    
    return updated

def display_practitioner_management():
    """
    Display the practitioner management interface.
    """
    st.subheader("Practitioner Management")
    
    # Get all practitioners
    practitioners = get_all_practitioners()
    
    if not practitioners:
        st.warning("No practitioners found.")
        return
    
    # Create tabs for different operations
    list_tab, merge_tab, edit_tab = st.tabs(["List Practitioners", "Merge Similar Practitioners", "Edit Practitioner"])
    
    with list_tab:
        # Create a DataFrame for the practitioners
        df = pd.DataFrame([
            {
                "Name": name,
                "Type": info["type"],
                "Specialty": info["specialty"],
                "Occurrences": info["count"]
            }
            for name, info in practitioners.items()
        ])
        
        # Sort by occurrences (highest first)
        df = df.sort_values("Occurrences", ascending=False)
        
        # Display the table
        st.dataframe(df, use_container_width=True, hide_index=True)
    
    with merge_tab:
        # Find similar practitioners
        similar_groups = find_similar_practitioners(practitioners)
        
        if not similar_groups:
            st.info("No similar practitioners found.")
        else:
            st.markdown(f"Found {len(similar_groups)} groups of similar practitioners.")
            
            # Display each group
            for i, group in enumerate(similar_groups):
                with st.expander(f"Group {i+1}: {', '.join(group)}"):
                    # Display practitioners in this group
                    group_df = pd.DataFrame([
                        {
                            "Name": name,
                            "Type": practitioners[name]["type"],
                            "Specialty": practitioners[name]["specialty"],
                            "Occurrences": practitioners[name]["count"]
                        }
                        for name in group
                    ])
                    
                    st.dataframe(group_df, use_container_width=True, hide_index=True)
                    
                    # Create columns for source and target selection
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        source_name = st.selectbox(f"Source (will be merged)", group, key=f"source_{i}")
                    
                    with col2:
                        target_name = st.selectbox(f"Target (will remain)", group, key=f"target_{i}")
                    
                    # Merge button
                    if st.button(f"Merge {source_name} into {target_name}", key=f"merge_{i}"):
                        if source_name == target_name:
                            st.error("Source and target cannot be the same.")
                        else:
                            if merge_practitioners(source_name, target_name):
                                st.success(f"Successfully merged {source_name} into {target_name}.")
                                # Clear cache to reload practitioners
                                clear_cache()
                                # Rerun to refresh the page
                                st.rerun()
                            else:
                                st.error(f"Failed to merge {source_name} into {target_name}.")
    
    with edit_tab:
        # Select a practitioner to edit
        selected_name = st.selectbox("Select practitioner to edit", list(practitioners.keys()))
        
        if selected_name:
            practitioner = practitioners[selected_name]
            
            # Display practitioner details
            st.markdown(f"### Editing: {selected_name}")
            st.markdown(f"**Type:** {practitioner['type']}")
            st.markdown(f"**Specialty:** {practitioner['specialty']}")
            st.markdown(f"**Occurrences:** {practitioner['count']}")
            
            # Display events
            st.markdown("### Events")
            events_df = pd.DataFrame([
                {
                    "Date": event["event_date"],
                    "Title": event["event_title"],
                    "ID": event["event_id"]
                }
                for event in practitioner["events"]
            ])
            
            st.dataframe(events_df, use_container_width=True, hide_index=True)
            
            # Edit form
            with st.form("edit_practitioner_form"):
                new_name = st.text_input("New Name", selected_name)
                new_type = st.selectbox("Type", list(phb_details.PERSONNEL_TYPES.keys()), index=list(phb_details.PERSONNEL_TYPES.keys()).index(practitioner["type"]) if practitioner["type"] in phb_details.PERSONNEL_TYPES else 0)
                new_specialty = st.selectbox("Specialty", list(phb_details.PHB_CATEGORIES.keys()), index=list(phb_details.PHB_CATEGORIES.keys()).index(practitioner["specialty"]) if practitioner["specialty"] in phb_details.PHB_CATEGORIES else 0)
                
                # Submit button
                submit = st.form_submit_button("Update Practitioner")
                
                if submit:
                    if new_name != selected_name:
                        # Merge the old name into the new name
                        if merge_practitioners(selected_name, new_name):
                            st.success(f"Successfully renamed {selected_name} to {new_name}.")
                            # Clear cache to reload practitioners
                            clear_cache()
                            # Rerun to refresh the page
                            st.rerun()
                        else:
                            st.error(f"Failed to rename {selected_name} to {new_name}.")
                    else:
                        st.info("No changes made to the name.")

def display_facility_management():
    """
    Display the facility management interface.
    """
    st.subheader("Facility Management")
    
    # Get all facilities
    facilities = get_all_facilities()
    
    if not facilities:
        st.warning("No facilities found.")
        return
    
    # Create tabs for different operations
    list_tab, merge_tab, edit_tab = st.tabs(["List Facilities", "Merge Similar Facilities", "Edit Facility"])
    
    with list_tab:
        # Create a DataFrame for the facilities
        df = pd.DataFrame([
            {
                "Name": name,
                "Type": info["type"],
                "Specialty": info["specialty"],
                "Occurrences": info["count"]
            }
            for name, info in facilities.items()
        ])
        
        # Sort by occurrences (highest first)
        df = df.sort_values("Occurrences", ascending=False)
        
        # Display the table
        st.dataframe(df, use_container_width=True, hide_index=True)
    
    with merge_tab:
        # Select facilities to merge
        st.markdown("### Select Facilities to Merge")
        
        # Create columns for source and target selection
        col1, col2 = st.columns(2)
        
        with col1:
            source_name = st.selectbox("Source (will be merged)", list(facilities.keys()), key="facility_source")
        
        with col2:
            target_name = st.selectbox("Target (will remain)", list(facilities.keys()), key="facility_target")
        
        # Merge button
        if st.button("Merge Facilities"):
            if source_name == target_name:
                st.error("Source and target cannot be the same.")
            else:
                if merge_facilities(source_name, target_name):
                    st.success(f"Successfully merged {source_name} into {target_name}.")
                    # Clear cache to reload facilities
                    clear_cache()
                    # Rerun to refresh the page
                    st.rerun()
                else:
                    st.error(f"Failed to merge {source_name} into {target_name}.")
    
    with edit_tab:
        # Select a facility to edit
        selected_name = st.selectbox("Select facility to edit", list(facilities.keys()))
        
        if selected_name:
            facility = facilities[selected_name]
            
            # Display facility details
            st.markdown(f"### Editing: {selected_name}")
            st.markdown(f"**Type:** {facility['type']}")
            st.markdown(f"**Specialty:** {facility['specialty']}")
            st.markdown(f"**Occurrences:** {facility['count']}")
            
            # Display events
            st.markdown("### Events")
            events_df = pd.DataFrame([
                {
                    "Date": event["event_date"],
                    "Title": event["event_title"],
                    "ID": event["event_id"]
                }
                for event in facility["events"]
            ])
            
            st.dataframe(events_df, use_container_width=True, hide_index=True)
            
            # Edit form
            with st.form("edit_facility_form"):
                new_name = st.text_input("New Name", selected_name)
                new_type = st.selectbox("Type", list(phb_details.FACILITY_TYPES.keys()), index=list(phb_details.FACILITY_TYPES.keys()).index(facility["type"]) if facility["type"] in phb_details.FACILITY_TYPES else 0)
                new_specialty = st.selectbox("Specialty", list(phb_details.PHB_CATEGORIES.keys()), index=list(phb_details.PHB_CATEGORIES.keys()).index(facility["specialty"]) if facility["specialty"] in phb_details.PHB_CATEGORIES else 0)
                
                # Submit button
                submit = st.form_submit_button("Update Facility")
                
                if submit:
                    if new_name != selected_name:
                        # Merge the old name into the new name
                        if merge_facilities(selected_name, new_name):
                            st.success(f"Successfully renamed {selected_name} to {new_name}.")
                            # Clear cache to reload facilities
                            clear_cache()
                            # Rerun to refresh the page
                            st.rerun()
                        else:
                            st.error(f"Failed to rename {selected_name} to {new_name}.")
                    else:
                        st.info("No changes made to the name.")

def display_reindexing_interface():
    """
    Display the reindexing interface.
    """
    st.subheader("Reindex Knowledge Store")
    
    st.markdown("""
    Reindexing will process all documents and rebuild the vector store for search functionality.
    This can take several minutes depending on the number of documents.
    """)
    
    # Create tabs for different operations
    rebuild_tab, full_tab = st.tabs(["Rebuild Vector Store", "Full Reindexing"])
    
    with rebuild_tab:
        st.markdown("""
        Rebuilding the vector store will update the search index without reprocessing documents.
        This is faster than a full reindexing but won't update any extracted information.
        """)
        
        if st.button("Rebuild Vector Store"):
            with st.spinner("Rebuilding vector store..."):
                if ksm.rebuild_vector_store():
                    st.success("Vector store rebuilt successfully.")
                    # Clear cache to reload data
                    clear_cache()
                else:
                    st.error("Failed to rebuild vector store.")
    
    with full_tab:
        st.markdown("""
        Full reindexing will reprocess all documents and rebuild the vector store.
        This will update all extracted information and may take several minutes.
        """)
        
        if st.button("Run Full Reindexing"):
            with st.spinner("Running full reindexing..."):
                try:
                    # Import the indexing module
                    import index_documents
                    
                    # Run the indexing
                    result = index_documents.run_indexing()
                    
                    if result:
                        st.success("Full reindexing completed successfully.")
                        # Clear cache to reload data
                        clear_cache()
                    else:
                        st.error("Failed to complete full reindexing.")
                except Exception as e:
                    st.error(f"Error during reindexing: {str(e)}")

def display_entity_management_dashboard():
    """
    Display the main entity management dashboard.
    """
    st.title("Entity Management Dashboard")
    
    # Create tabs for different entity types
    practitioner_tab, facility_tab, reindex_tab = st.tabs([
        "Practitioner Management", 
        "Facility Management", 
        "Reindexing"
    ])
    
    with practitioner_tab:
        display_practitioner_management()
    
    with facility_tab:
        display_facility_management()
    
    with reindex_tab:
        display_reindexing_interface()
