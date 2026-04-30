#!/usr/bin/env python3
"""
Minimal CORS-enabled HTTP server for the Blackbox Tournament Monitor.

Usage:
    python server.py [PORT]

Serves the blackbox_game directory (including index.html and shared/ JSON files).
"""

import http.server
import socketserver
import os
import sys

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
WWW_ROOT = os.path.dirname(os.path.abspath(__file__))

class CORSRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WWW_ROOT, **kwargs)

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, fmt, *args):
        print(f"[Server] {self.address_string()} - {fmt % args}")

class ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True

def run():
    with ReusableTCPServer(("", PORT), CORSRequestHandler) as httpd:
        print(f"Serving Blackbox Tournament Monitor at http://localhost:{PORT}/")
        print(f"WWW root: {WWW_ROOT}")
        print("Press Ctrl+C to stop.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server.")

if __name__ == "__main__":
    run()
