#!/usr/bin/env python3
"""
HTTPS server for AR Game with device sensor access
Run this script to start a local HTTPS server for the WebAR app
"""

import http.server
import socketserver
import webbrowser
import os
import sys
import subprocess
import signal
import time
import ssl

PORT = 8443

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

def create_ssl_cert():
    """Create self-signed SSL certificate using openssl"""
    cert_file = 'server.pem'
    key_file = 'server.key'
    
    if os.path.exists(cert_file) and os.path.exists(key_file):
        print("✅ SSL certificate already exists")
        return cert_file, key_file
    
    print("🔐 Creating self-signed SSL certificate...")
    try:
        # Create private key and certificate
        subprocess.run([
            'openssl', 'req', '-new', '-x509', '-keyout', key_file, 
            '-out', cert_file, '-days', '365', '-nodes',
            '-subj', '/C=US/ST=CA/L=SF/O=AR/CN=localhost'
        ], check=True, capture_output=True)
        print("✅ SSL certificate created successfully")
        return cert_file, key_file
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to create SSL certificate: {e}")
        print("💡 Please install OpenSSL: brew install openssl")
        return None, None
    except FileNotFoundError:
        print("❌ OpenSSL not found")
        print("💡 Please install OpenSSL: brew install openssl")
        return None, None

def main():
    # Change to the directory containing this script
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    print(f"🚀 AR Game HTTPS Server starting...")
    print(f"🔍 Checking port {PORT}...")
    
    # Kill any existing processes on port 8443
    kill_port_processes(PORT)
    
    # Create SSL certificate
    cert_file, key_file = create_ssl_cert()
    
    if not cert_file or not key_file:
        print("❌ Cannot start HTTPS server without SSL certificate")
        print("💡 Falling back to HTTP server on port 8000...")
        fallback_port = 8000
        kill_port_processes(fallback_port)
        
        try:
            with socketserver.TCPServer(("0.0.0.0", fallback_port), MyHTTPRequestHandler) as httpd:
                print(f"✅ HTTP Server started!")
                print(f"📱 Server running at: http://localhost:{fallback_port}")
                print(f"📱 Mobile access: http://[YOUR_IP]:{fallback_port}")
                print(f"⚠️  Note: Some features may not work without HTTPS")
                print(f"⏹️  Press Ctrl+C to stop the server")
                print("-" * 50)
                
                try:
                    webbrowser.open(f'http://localhost:{fallback_port}')
                    print("🌐 Browser opened automatically")
                except:
                    print("⚠️  Could not open browser automatically")
                
                httpd.serve_forever()
        except OSError as e:
            print(f"❌ Error starting HTTP server: {e}")
            sys.exit(1)
        return
    
    try:
        with socketserver.TCPServer(("0.0.0.0", PORT), MyHTTPRequestHandler) as httpd:
            # Create SSL context
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            context.load_cert_chain(cert_file, key_file)
            
            # Wrap socket with SSL
            httpd.socket = context.wrap_socket(httpd.socket, server_side=True)
            
            print(f"✅ HTTPS Server started successfully!")
            print(f"📱 Server running at: https://localhost:{PORT}")
            print(f"📱 Mobile access: https://[YOUR_IP]:{PORT}")
            print(f"🎯 Open your browser and go to: https://localhost:{PORT}")
            print(f"🔒 HTTPS enabled for device sensor access!")
            print(f"⚠️  Browser will show security warning - click 'Advanced' and 'Proceed'")
            print(f"⏹️  Press Ctrl+C to stop the server")
            print("-" * 50)
            
            # Try to open browser automatically
            try:
                webbrowser.open(f'https://localhost:{PORT}')
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
            print("💡 Try running: python3 -m http.server 8444")
            print("💡 Or manually kill processes: sudo lsof -ti :8443 | xargs kill -9")
        else:
            print(f"❌ Error starting HTTPS server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
