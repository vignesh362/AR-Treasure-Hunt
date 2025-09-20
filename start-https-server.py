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
import tempfile
import atexit

PORT = 8443

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Add CORS headers for AR.js
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

def create_self_signed_cert():
    """Create a self-signed certificate for HTTPS"""
    try:
        import cryptography
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        from datetime import datetime, timedelta
    except ImportError:
        print("❌ cryptography library not found. Installing...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'cryptography'], check=True)
        import cryptography
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        from datetime import datetime, timedelta

    # Generate private key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    # Create certificate
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "CA"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, "San Francisco"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "AR Treasure Hunt"),
        x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
    ])

    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        private_key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.utcnow()
    ).not_valid_after(
        datetime.utcnow() + timedelta(days=365)
    ).add_extension(
        x509.SubjectAlternativeName([
            x509.DNSName("localhost"),
            x509.IPAddress("127.0.0.1"),
        ]),
        critical=False,
    ).sign(private_key, hashes.SHA256())

    # Write certificate and key to temporary files
    cert_file = tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.pem')
    key_file = tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.pem')

    cert_file.write(cert.public_bytes(serialization.Encoding.PEM))
    key_file.write(private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    ))

    cert_file.close()
    key_file.close()

    # Register cleanup function
    def cleanup():
        try:
            os.unlink(cert_file.name)
            os.unlink(key_file.name)
        except:
            pass

    atexit.register(cleanup)

    return cert_file.name, key_file.name

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
    
    print(f"🚀 AR Game HTTPS Server starting...")
    print(f"🔍 Checking port {PORT}...")
    
    # Kill any existing processes on port 8443
    kill_port_processes(PORT)
    
    try:
        # Create self-signed certificate
        print("🔐 Creating self-signed certificate...")
        cert_file, key_file = create_self_signed_cert()
        print("✅ Certificate created successfully")
        
        with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
            # Wrap socket with SSL
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            context.load_cert_chain(cert_file, key_file)
            httpd.socket = context.wrap_socket(httpd.socket, server_side=True)
            
            print(f"✅ HTTPS Server started successfully!")
            print(f"📱 Server running at: https://localhost:{PORT}")
            print(f"🎯 Open your browser and go to: https://localhost:{PORT}")
            print(f"📱 Mobile access: https://10.50.7.23:{PORT}")
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
            print(f"❌ Error starting server: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error creating HTTPS server: {e}")
        print("💡 Falling back to HTTP server...")
        print("💡 Note: Some features may not work without HTTPS")
        sys.exit(1)

if __name__ == "__main__":
    main()
