import http.server, socketserver, os, sys
PORT = 8080
DIR  = sys.argv[1] if len(sys.argv) > 1 else "."
os.chdir(DIR)
Handler = http.server.SimpleHTTPRequestHandler
Handler.log_message = lambda *a: None
print(f"\n  Open in Brave:  http://localhost:8080/visualization.html\n  Ctrl+C to stop\n")
with socketserver.TCPServer(("", PORT), Handler) as httpd:
    httpd.serve_forever()
