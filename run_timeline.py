#!/usr/bin/env python3
"""
Script to run the PHB-centric timeline application.
"""
import os
import webbrowser
import threading
import time
from app import app

def open_browser():
    """Open the browser after a short delay."""
    time.sleep(1.5)
    webbrowser.open('http://127.0.0.1:5000/')

if __name__ == '__main__':
    # Start a thread to open the browser
    threading.Thread(target=open_browser).start()
    
    # Run the Flask application
    app.run(debug=True)
