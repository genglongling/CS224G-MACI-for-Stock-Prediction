#!/usr/bin/env python
"""
CheckCo System Startup Script
This script starts the server and automatically opens the browser frontend page
"""

import os
import sys
import time
import webbrowser
import subprocess
import platform
import threading

def check_dependencies():
    """Check and install required dependencies"""
    try:
        import http.server
        import json
        import urllib.parse
        
        # Try to import packages that might need additional installation
        try:
            import langchain_together
            import langgraph
        except ImportError:
            print("Installing required dependency packages...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", 
                                  "langchain-together", "langgraph-core"])
            print("Dependencies installed successfully!")
    except ImportError as e:
        print(f"Error: Missing required dependency - {e}")
        print("Please ensure Python environment is properly installed")
        sys.exit(1)

def start_server():
    """Start the server directly in the current process"""
    # Import server module
    print("Starting server...")
    
    try:
        # Method 1: Directly import and run the server.py run function in a new thread
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        import server
        
        # Create a thread to run the server
        server_thread = threading.Thread(target=server.run)
        server_thread.daemon = True  # Set as daemon thread so it exits when main program exits
        server_thread.start()
        
        return server_thread
    except ImportError:
        print("Unable to import server module, attempting to start using subprocess...")
        # Method 2: If import fails, use subprocess with output redirected to current console
        process = subprocess.Popen(
            [sys.executable, "server.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1  # Line buffering
        )
        
        # Create a thread to read and display server output in real-time
        def output_reader():
            for line in process.stdout:
                print(f"[Server] {line.strip()}")
        
        reader_thread = threading.Thread(target=output_reader)
        reader_thread.daemon = True
        reader_thread.start()
        
        return process

def open_browser():
    """Open the browser frontend page"""
    # Get the absolute path of the current script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Build the path to the frontend HTML file
    html_path = os.path.join(current_dir, "static/front.html")
    
    # Check if file exists
    if not os.path.exists(html_path):
        print(f"Error: Frontend file not found at {html_path}")
        return False
    
    # Convert file path to URL format
    file_url = f"file://{html_path}"
    if platform.system() == "Windows":
        file_url = file_url.replace("\\", "/")
    
    print(f"Opening browser: {file_url}")
    webbrowser.open(file_url)
    return True

def main():
    """Main function"""
    print("CheckCo System starting...")
    
    # Check dependencies
    check_dependencies()
    
    # Start server
    server_process = start_server()
    
    # Wait for server to start
    print("Waiting for server to start...")
    time.sleep(3)
    
    # Open browser
    if not open_browser():
        print("Unable to open frontend page, please manually open front.html file")
    
    print("\nCheckCo System has started!")
    print("Server running at: http://localhost:8000")
    print("Frontend page has been opened in browser")
    print("Press Ctrl+C to stop the server")
    
    try:
        # Keep main program running until user interrupts
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping server...")
        if isinstance(server_process, subprocess.Popen):
            server_process.terminate()
        print("System has been shut down")

if __name__ == "__main__":
    main()