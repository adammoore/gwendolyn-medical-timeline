"""
app.py

A Flask application that:
1. Reads Evernote export (.enex) files.
2. Extracts timeline events with PHB integration.
3. Renders an interactive PHB-centric timeline.
4. Provides a diagnostic journey timeline.
5. Includes patient information.
6. Handles attachments and Evernote links.
7. Processes attachments with OCR and adds content to knowledge base.
8. Provides semantic search across all content.
"""

from flask import Flask, render_template, jsonify, request, redirect, url_for, send_file
from enex_parser import get_all_events_from_directory, extract_diagnostic_journey
import improved_phb_details as phb_details
import patient_info
import evernote_utils
import attachment_processor
import os
import json
import webbrowser
import subprocess

app = Flask(__name__)

# Directory containing Evernote export files
ENEX_DIR = os.path.dirname(os.path.abspath(__file__))

# Directory for attachments
ATTACHMENTS_DIR = os.path.join(ENEX_DIR, "attachments")

# Cache for events to avoid re-parsing on every request
cached_events = None
cached_diagnostic_journey = None

def get_events():
    """
    Get all events, using cache if available.
    """
    global cached_events
    if cached_events is None:
        cached_events = get_all_events_from_directory(ENEX_DIR)
    return cached_events

def get_diagnostic_journey():
    """
    Get the diagnostic journey, using cache if available.
    """
    global cached_diagnostic_journey
    if cached_diagnostic_journey is None:
        events = get_events()
        cached_diagnostic_journey = extract_diagnostic_journey(events)
    return cached_diagnostic_journey

@app.route('/')
def index():
    """
    Main route that renders the PHB-centric timeline.
    """
    events = get_events()
    return render_template(
        "phb_timeline.html", 
        events=events,
        phb_categories=phb_details.PHB_CATEGORIES,
        phb_supports=phb_details.PHB_SUPPORTS,
        patient_info=patient_info.PATIENT_INFO
    )

@app.route('/diagnostic')
def diagnostic_journey():
    """
    Route that renders the diagnostic journey timeline.
    """
    journey = get_diagnostic_journey()
    return render_template(
        "diagnostic_journey.html",
        journey=journey,
        patient_info=patient_info.PATIENT_INFO
    )

@app.route('/phb/<category>')
def phb_category(category):
    """
    Route to show events for a specific PHB category.
    """
    events = get_events()
    
    # Filter events by PHB category
    filtered_events = []
    for event in events:
        for cat in event.get("phb_categories", []):
            if cat["category"] == category:
                filtered_events.append(event)
                break
    
    return render_template(
        "phb_timeline.html", 
        events=filtered_events,
        phb_categories=phb_details.PHB_CATEGORIES,
        phb_supports=phb_details.PHB_SUPPORTS,
        active_category=category,
        patient_info=patient_info.PATIENT_INFO
    )

@app.route('/support/<support>')
def phb_support(support):
    """
    Route to show events for a specific PHB support.
    """
    events = get_events()
    
    # Filter events by PHB support
    filtered_events = []
    for event in events:
        for sup in event.get("phb_supports", []):
            if sup["support"] == support:
                filtered_events.append(event)
                break
    
    return render_template(
        "phb_timeline.html", 
        events=filtered_events,
        phb_categories=phb_details.PHB_CATEGORIES,
        phb_supports=phb_details.PHB_SUPPORTS,
        active_support=support,
        patient_info=patient_info.PATIENT_INFO
    )

@app.route('/specialty/<specialty>')
def specialty(specialty):
    """
    Route to show events for a specific medical specialty.
    """
    events = get_events()
    
    # Filter events by specialty
    filtered_events = [event for event in events if event["specialty"] == specialty]
    
    return render_template(
        "phb_timeline.html", 
        events=filtered_events,
        phb_categories=phb_details.PHB_CATEGORIES,
        phb_supports=phb_details.PHB_SUPPORTS,
        active_specialty=specialty,
        patient_info=patient_info.PATIENT_INFO
    )

@app.route('/personnel/<personnel_name>')
def personnel(personnel_name):
    """
    Route to show events for a specific medical personnel.
    """
    events = get_events()
    
    # Filter events by personnel name
    filtered_events = []
    for event in events:
        for person in event.get("personnel", []):
            if person["name"] == personnel_name:
                filtered_events.append(event)
                break
    
    return render_template(
        "phb_timeline.html", 
        events=filtered_events,
        phb_categories=phb_details.PHB_CATEGORIES,
        phb_supports=phb_details.PHB_SUPPORTS,
        active_personnel=personnel_name,
        patient_info=patient_info.PATIENT_INFO
    )

@app.route('/facility/<facility_name>')
def facility(facility_name):
    """
    Route to show events for a specific medical facility.
    """
    events = get_events()
    
    # Filter events by facility name
    filtered_events = []
    for event in events:
        for fac in event.get("facilities", []):
            if fac["name"] == facility_name:
                filtered_events.append(event)
                break
    
    return render_template(
        "phb_timeline.html", 
        events=filtered_events,
        phb_categories=phb_details.PHB_CATEGORIES,
        phb_supports=phb_details.PHB_SUPPORTS,
        active_facility=facility_name,
        patient_info=patient_info.PATIENT_INFO
    )

@app.route('/event/<event_id>')
def event_detail(event_id):
    """
    Route to show details for a specific event.
    """
    events = get_events()
    
    # Find the event with the given ID
    event = next((e for e in events if e["id"] == event_id), None)
    
    if event is None:
        return redirect(url_for('index'))
    
    return render_template(
        "event_detail.html", 
        event=event,
        phb_categories=phb_details.PHB_CATEGORIES,
        phb_supports=phb_details.PHB_SUPPORTS,
        patient_info=patient_info.PATIENT_INFO
    )

@app.route('/open_evernote/<event_id>')
def open_evernote(event_id):
    """
    Route to open an event in Evernote.
    """
    events = get_events()
    
    # Find the event with the given ID
    event = next((e for e in events if e["id"] == event_id), None)
    
    if event is None:
        return jsonify({"success": False, "message": "Event not found"}), 404
    
    # Try to open the Evernote link
    try:
        if "evernote_links" in event and event["evernote_links"]:
            success = evernote_utils.open_evernote_note(event["id"], event["evernote_links"])
            if success:
                return jsonify({"success": True})
            else:
                return jsonify({"success": False, "message": "Failed to open Evernote note"}), 500
        else:
            return jsonify({"success": False, "message": "No Evernote links available"}), 404
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/attachment/<event_id>/<path:filename>')
def get_attachment(event_id, filename):
    """
    Route to get an attachment for a specific event.
    """
    events = get_events()
    
    # Find the event with the given ID
    event = next((e for e in events if e["id"] == event_id), None)
    
    if event is None:
        return jsonify({"error": "Event not found"}), 404
    
    # Find the attachment with the given filename
    attachment = next((a for a in event.get("attachments", []) if os.path.basename(a["file_path"]) == filename), None)
    
    if attachment is None:
        return jsonify({"error": "Attachment not found"}), 404
    
    # Return the attachment
    return send_file(attachment["file_path"], mimetype=attachment["mime_type"])

@app.route('/attachments/<event_id>')
def list_attachments(event_id):
    """
    Route to list all attachments for a specific event.
    """
    events = get_events()
    
    # Find the event with the given ID
    event = next((e for e in events if e["id"] == event_id), None)
    
    if event is None:
        return jsonify({"error": "Event not found"}), 404
    
    # Return the list of attachments
    return jsonify(event.get("attachments", []))

@app.route('/patient')
def patient():
    """
    Route to show patient information.
    """
    return render_template(
        "patient_info.html",
        patient_info=patient_info.PATIENT_INFO
    )

@app.route('/search')
def search():
    """
    Route to search for events and attachments.
    """
    query = request.args.get('q', '')
    if not query:
        return render_template(
            "search.html",
            query='',
            results=[],
            patient_info=patient_info.PATIENT_INFO
        )
    
    # Perform semantic search
    results = attachment_processor.semantic_search(query, k=10)
    
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
    
    return render_template(
        "search.html",
        query=query,
        results=search_results,
        patient_info=patient_info.PATIENT_INFO
    )

@app.route('/api/events')
def api_events():
    """
    API endpoint that returns all events as JSON.
    """
    events = get_events()
    return jsonify(events)

@app.route('/api/diagnostic_journey')
def api_diagnostic_journey():
    """
    API endpoint that returns the diagnostic journey as JSON.
    """
    journey = get_diagnostic_journey()
    return jsonify(journey)

@app.route('/api/patient_info')
def api_patient_info():
    """
    API endpoint that returns patient information as JSON.
    """
    return jsonify(patient_info.PATIENT_INFO)

@app.route('/api/phb_categories')
def api_phb_categories():
    """
    API endpoint that returns PHB categories as JSON.
    """
    return jsonify(phb_details.PHB_CATEGORIES)

@app.route('/api/phb_supports')
def api_phb_supports():
    """
    API endpoint that returns PHB supports as JSON.
    """
    return jsonify(phb_details.PHB_SUPPORTS)

@app.route('/api/events/by_phb_category/<category>')
def api_events_by_phb_category(category):
    """
    API endpoint that returns events for a specific PHB category.
    """
    events = get_events()
    
    # Filter events by PHB category
    filtered_events = []
    for event in events:
        for cat in event.get("phb_categories", []):
            if cat["category"] == category:
                filtered_events.append(event)
                break
    
    return jsonify(filtered_events)

@app.route('/api/events/by_phb_support/<support>')
def api_events_by_phb_support(support):
    """
    API endpoint that returns events for a specific PHB support.
    """
    events = get_events()
    
    # Filter events by PHB support
    filtered_events = []
    for event in events:
        for sup in event.get("phb_supports", []):
            if sup["support"] == support:
                filtered_events.append(event)
                break
    
    return jsonify(filtered_events)

@app.route('/api/events/by_specialty/<specialty>')
def api_events_by_specialty(specialty):
    """
    API endpoint that returns events for a specific medical specialty.
    """
    events = get_events()
    
    # Filter events by specialty
    filtered_events = [event for event in events if event["specialty"] == specialty]
    
    return jsonify(filtered_events)

@app.route('/api/events/by_personnel/<personnel_name>')
def api_events_by_personnel(personnel_name):
    """
    API endpoint that returns events for a specific medical personnel.
    """
    events = get_events()
    
    # Filter events by personnel name
    filtered_events = []
    for event in events:
        for person in event.get("personnel", []):
            if person["name"] == personnel_name:
                filtered_events.append(event)
                break
    
    return jsonify(filtered_events)

@app.route('/api/events/by_facility/<facility_name>')
def api_events_by_facility(facility_name):
    """
    API endpoint that returns events for a specific medical facility.
    """
    events = get_events()
    
    # Filter events by facility name
    filtered_events = []
    for event in events:
        for fac in event.get("facilities", []):
            if fac["name"] == facility_name:
                filtered_events.append(event)
                break
    
    return jsonify(filtered_events)

@app.route('/api/event/<event_id>')
def api_event_detail(event_id):
    """
    API endpoint that returns details for a specific event.
    """
    events = get_events()
    
    # Find the event with the given ID
    event = next((e for e in events if e["id"] == event_id), None)
    
    if event is None:
        return jsonify({"error": "Event not found"}), 404
    
    return jsonify(event)

@app.route('/api/search')
def api_search():
    """
    API endpoint that returns search results as JSON.
    """
    query = request.args.get('q', '')
    if not query:
        return jsonify([])
    
    # Perform semantic search
    results = attachment_processor.semantic_search(query, k=10)
    
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
                    "event_id": event["id"],
                    "title": event["title"],
                    "date": event["date"],
                    "content": result.page_content,
                    "score": 1.0  # Placeholder for score
                })
            elif result_type == "attachment":
                attachment_index = metadata.get("attachment_index", 0)
                if attachment_index < len(event.get("attachments", [])):
                    attachment = event["attachments"][attachment_index]
                    search_results.append({
                        "type": "attachment",
                        "event_id": event["id"],
                        "title": event["title"],
                        "date": event["date"],
                        "attachment_name": attachment["file_name"],
                        "content": result.page_content,
                        "score": 1.0  # Placeholder for score
                    })
    
    return jsonify(search_results)

if __name__ == '__main__':
    app.run(debug=True)
