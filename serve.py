#!/usr/bin/env python3
"""Static file server with no-cache headers for prototype development."""
import http.server
import sys

class NoCacheHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    def log_message(self, format, *args):
        pass  # suppress request logs

if __name__ == "__main__":
    import os
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8090
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    http.server.test(HandlerClass=NoCacheHandler, port=port)
