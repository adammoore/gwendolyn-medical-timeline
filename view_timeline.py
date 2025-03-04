#!/usr/bin/env python3
import os
import webbrowser
import http.server
import socketserver
import threading
import time

# Configuration
PORT = 8000
TIMELINE_FILE = "gwendolyn_medical_timeline_enhanced.html"

def start_server():
    """Start a simple HTTP server in the current directory"""
    handler = http.server.SimpleHTTPRequestHandler
    httpd = socketserver.TCPServer(("", PORT), handler)
    print(f"Serving at http://localhost:{PORT}")
    httpd.serve_forever()

def main():
    # Check if the timeline file exists
    if not os.path.exists(TIMELINE_FILE):
        print(f"Error: {TIMELINE_FILE} not found. Run create_enhanced_timeline.py first.")
        return
    
    # Start the server in a separate thread
    server_thread = threading.Thread(target=start_server)
    server_thread.daemon = True
    server_thread.start()
    
    # Give the server a moment to start
    time.sleep(1)
    
    # Open the timeline in the default web browser
    url = f"http://localhost:{PORT}/{TIMELINE_FILE}"
    print(f"Opening {url} in your web browser...")
    webbrowser.open(url)
    
    print("\nPress Ctrl+C to stop the server when you're done viewing the timeline.")
    
    try:
        # Keep the main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")

if __name__ == "__main__":
    main()
