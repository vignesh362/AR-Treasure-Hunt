#!/usr/bin/env python3
"""
Simple HTTPS server using built-in SSL
"""

import http.server
import socketserver
import ssl
import os
import sys

PORT = 8443

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Add CORS headers for AR.js
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

def main():
    # Change to the directory containing this script
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    print(f"🚀 Starting HTTPS server on port {PORT}...")
    
    try:
        with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
            # Create SSL context
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            
            # Create self-signed certificate
            context.load_cert_chain('server.pem', 'server.key')
            
            # Wrap socket with SSL
            httpd.socket = context.wrap_socket(httpd.socket, server_side=True)
            
            print(f"✅ HTTPS Server started!")
            print(f"📱 Access at: https://localhost:{PORT}")
            print(f"📱 Mobile: https://10.50.7.23:{PORT}")
            print(f"⚠️  Accept the security warning in your browser")
            print(f"⏹️  Press Ctrl+C to stop")
            
            httpd.serve_forever()
            
    except FileNotFoundError:
        print("❌ SSL certificate files not found!")
        print("💡 Creating self-signed certificate...")
        create_cert()
        main()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

def create_cert():
    """Create self-signed certificate using openssl"""
    import subprocess
    
    try:
        # Create private key
        subprocess.run([
            'openssl', 'req', '-new', '-x509', '-keyout', 'server.key', 
            '-out', 'server.pem', '-days', '365', '-nodes',
            '-subj', '/C=US/ST=CA/L=SF/O=AR/CN=localhost'
        ], check=True)
        print("✅ Certificate created successfully")
    except subprocess.CalledProcessError:
        print("❌ Failed to create certificate")
        print("💡 Please install OpenSSL or use HTTP server instead")
        sys.exit(1)
    except FileNotFoundError:
        print("❌ OpenSSL not found")
        print("💡 Please install OpenSSL or use HTTP server instead")
        sys.exit(1)

if __name__ == "__main__":
    main()
