#!/usr/bin/env python3
"""
Simple HTTP server for AR Game
Run this script to start a local server for the WebAR app
"""

import http.server
import socketserver
import webbrowser
import os
import sys
import subprocess
import signal
import time

PORT = 8000

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Add CORS headers for AR.js
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

def kill_port_processes(port):
    """Kill any processes using the specified port"""
    try:
        # Find processes using the port
        result = subprocess.run(['lsof', '-ti', f':{port}'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0 and result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            print(f"🔍 Found {len(pids)} process(es) using port {port}")
            
            for pid in pids:
                if pid.strip():
                    try:
                        print(f"🔄 Killing process {pid}...")
                        os.kill(int(pid), signal.SIGTERM)
                        time.sleep(1)  # Give it time to die
                        
                        # Check if it's still running and force kill if needed
                        try:
                            os.kill(int(pid), 0)  # Check if process exists
                            print(f"⚡ Force killing process {pid}...")
                            os.kill(int(pid), signal.SIGKILL)
                        except ProcessLookupError:
                            print(f"✅ Process {pid} terminated successfully")
                            
                    except (ValueError, ProcessLookupError, PermissionError) as e:
                        print(f"⚠️  Could not kill process {pid}: {e}")
            
            print(f"✅ Cleaned up port {port}")
            time.sleep(2)  # Wait a bit more for cleanup
        else:
            print(f"✅ Port {port} is free")
            
    except FileNotFoundError:
        print("⚠️  lsof command not found, trying alternative method...")
        # Alternative method for systems without lsof
        try:
            result = subprocess.run(['netstat', '-tulpn'], capture_output=True, text=True)
            if f':{port}' in result.stdout:
                print(f"⚠️  Port {port} appears to be in use, but cannot kill processes automatically")
                print("💡 Please manually stop any server running on this port")
        except FileNotFoundError:
            print("⚠️  Cannot check port status automatically")

def main():
    # Change to the directory containing this script
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    print(f"🚀 AR Game Server starting...")
    print(f"🔍 Checking port {PORT}...")
    
    # Kill any existing processes on port 8000
    kill_port_processes(PORT)
    
    try:
        with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
            print(f"✅ Server started successfully!")
            print(f"📱 Server running at: http://localhost:{PORT}")
            print(f"🎯 Open your browser and go to: http://localhost:{PORT}")
            print(f"📋 Make sure to print the Hiro marker from: https://jeromeetienne.github.io/AR.js/data/images/HIRO.jpg")
            print(f"⏹️  Press Ctrl+C to stop the server")
            print("-" * 50)
            
            # Try to open browser automatically
            try:
                webbrowser.open(f'http://localhost:{PORT}')
                print("🌐 Browser opened automatically")
            except:
                print("⚠️  Could not open browser automatically")
            
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
        sys.exit(0)
    except OSError as e:
        if e.errno == 48:  # Address already in use
            print(f"❌ Port {PORT} is still in use after cleanup attempt.")
            print("💡 Try running: python3 -m http.server 8001")
            print("💡 Or manually kill processes: sudo lsof -ti :8000 | xargs kill -9")
        else:
            print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
