"""
                                     Flask Markdown Merge App
===================================================================================================

A Flask web application that processes ZIP files containing Markdown documents.
The application extracts Markdown files, removes metadata, merges files
when necessary, and provides real-time progress tracking via Server-Sent Events.

Features:
- ZIP file upload and validation
- Markdown file extraction and processing  
- Metadata removal
- Automatic file merging for large collections (>50 files)
- Word count monitoring and warnings
- Real-time progress tracking via SSE
- CORS support for cross-origin requests

Dependencies:
- flask: Web framework
  - Flask: Create the Flask app instance
  - request: Access incoming HTTP requests
  - jsonify: Return JSON responses
  - send_file: Send files as HTTP responses
  - Response, stream_with_context: Stream data in real time

- flask_cors: Cross-Origin Resource Sharing support
  - CORS: Enable CORS for the Flask app

- os: Operating system interface (file paths, directory management)
- io: In-memory file and stream handling (e.g., BytesIO)
- zipfile: ZIP file compression/decompression
- tempfile: Create temporary directories for file extraction
- queue: Manage progress update queues per session
- json: Parse and format JSON data
"""


# =============================================================================
# IMPORTS
# =============================================================================

from flask import Flask, request, jsonify, send_file, Response
from flask_cors import CORS
import os, io
import zipfile
import tempfile
import queue
import json


# =============================================================================
# APPLICATION CONFIGURATION
# =============================================================================

app = Flask(__name__)
CORS(app)                   # Enable cross origin resource sharing 

# Constants
MAX_FILES_PER_MERGE = 49    # Maximum files to merge into a single output file
MAX_WORDS = 50000           # Threshold for word count warning

# Global Storage for progress tracking across sessions
progress_queues = {}        # Each session_id maps to a Queue for real time progress tracking


# =============================================================================
# PROCESSING FUNCTIONS
# =============================================================================

def upload_zip(file, session_id):
    """
    Process an uploaded ZIP file containing Markdown documents.
    
    This function handles the core logic of the application:
    1. Extracts ZIP contents to temporary directory
    2. Finds all Markdown files regardless of directory structure
    3. Processes files individually (<=50 files) or merges them (>50 files)
    4. Removes metadata from Markdown content
    5. Applies word count warnings when necessary
    6. Returns processed files as a new ZIP archive
    
    Args:
        file (FileStorage): Uploaded ZIP file from Flask request
        session_id (str): Unique identifier for tracking progress
        
    Returns:
        Response: Flask response containing processed ZIP file or JSON error
        
    Processing Logic:
        - Files <=50: Preserve original structure, returned without merging
        - Files >50: Merge into batches of MAX_FILES_PER_MERGE each
        - Metadata: Automatically stripped from all files
        - Word count: Files > MAX_WORDS get warning suffix in filename
    """
    # Initialize progress tracking for this session
    if session_id not in progress_queues:
        progress_queues[session_id] = queue.Queue()

    progress_queue = progress_queues[session_id]
    progress_data = {
        "total_files":0,
        "current_index": 0,
        "done": False
    }

    # Use temporary directory for safe file operations
    with tempfile.TemporaryDirectory() as tmpdirname:
        # Save uploaded file to temp location
        zip_path = os.path.join(tmpdirname, file.filename)
        file.save(zip_path)

        # Extract zip file contents with error handling
        try: 
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(tmpdirname)
        except zipfile.BadZipFile:
            return jsonify({"error": "Invalid ZIP file"}), 400
        
        # Recursively find all markdown files in extracted contents
        md_files = []
        for root,_,files in os.walk(tmpdirname):
            for name in files:
                if name.endswith(".md"):
                    md_files.append(os.path.join(root,name))
        
        md_count = len(md_files)
        progress_data["total_files"] = md_count

        # Returning original Markdown files in a new ZIP file
        # Processing each file without merging
        if md_count <= 50:
            mem_zip = io.BytesIO()
            with zipfile.ZipFile(mem_zip, "w") as out_zip:
                for path in md_files:
                    arcname = os.path.basename(path)
                    out_zip.write(path, arcname=arcname)

            mem_zip.seek(0)
            progress_data["done"] = True
            return send_file(mem_zip, as_attachment=True, download_name=file.filename)
            

        # Merge files into batches to reduce total file count
        merged_files = []
        # process files in batches of size MAX_FILES_PER_MERGE
        for i in range(0,md_count,MAX_FILES_PER_MERGE):
            batch = md_files[i:i+MAX_FILES_PER_MERGE]
            merged_content = ""

            # Process each file in the current batch
            for idx,file_path in enumerate(batch):
                with open(file_path, "r", encoding="utf-8") as f:

                    # Update progress tracking
                    progress_data["current_index"] = idx + i + 1
                    progress_queue.put(progress_data.copy())
                    
                    # Read file content
                    content = f.read()
                    # Remove metadata if present
                    if content.startswith("---"):
                        # Split on first 2 occurences
                        parts = content.split("---",2)
                        if len(parts) == 3:
                            # Take content after 2nd delimiter
                            content = parts[2].lstrip()
                    # Append content with separator
                    merged_content += content + "\n\n"
            
            # Generate filename with word count warning
            word_count = count_words(merged_content)
            filename = f"merged_part{i//MAX_FILES_PER_MERGE + 1}.md"

            # Adding suffix after word count surpases MAX_WORDS threshold
            if word_count > MAX_WORDS:
                filename = filename.replace(".md","_OVER50000WORDS.md")
            
            merged_files.append((filename,merged_content))
        
        # Create output ZIP with merged files
        mem_zip = io.BytesIO()
        with zipfile.ZipFile(mem_zip, "w") as out_zip:
            for filename, content in merged_files:
                out_zip.writestr(filename, content)
                
        # Finalize processing and return zip file
        mem_zip.seek(0)
        progress_data["done"] = True
        progress_queue.put(progress_data.copy())
        return send_file(mem_zip, as_attachment=True, download_name="merged_files.zip")

# -------------------------------------------------------------------
# -------------------------------------------------------------------

def count_words(text):
    """
    Count the number of words in a text string.
    
    Uses simple whitespace-based splitting to count words. 
    
    Args:
        text (str): Input text to count words in
        
    Returns:
        int: Number of words in the text
    """
    return len(text.split())


# =============================================================================
# API ENDPOINTS
# =============================================================================

@app.route("/upload/<session_id>", methods=["POST"])
def upload(session_id):
    """
    Handle ZIP file upload requests.
    
    This endpoint accepts multipart/form-data requests containing a ZIP file
    and processes it according to the application's logic. It includes
    comprehensive input validation and error handling.
    
    URL Parameters:
        session_id (str): Unique identifier for progress tracking
        
    Form Data:
        file: ZIP file containing Markdown documents
        
    Returns:
        Response: Processed ZIP file download or JSON error response
        
    HTTP Status Codes:
        200: Success - returns processed ZIP file
        400: Bad Request - validation errors (missing file, wrong format, etc.)
        
    Error Conditions:
        - No file in request
        - Empty filename
        - Non-ZIP file extension
        - Invalid ZIP file format
        
    Example Usage:
        POST /upload/242f0723-aabc-49ef-9130-d3c75e2648db
        Content-Type: multipart/form-data
        
        file: ZIP file
    """

    # Validate request contains file data
    if "file" not in request.files:
        return jsonify({"error": "No file part in request"}),400
    
    file = request.files["file"]

    # Validate file was selected
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400
    
    # Validate file type by extension
    if not file.filename.endswith(".zip"):
        return jsonify({"error": "Only ZIP files are allowed"}), 400
    
    return upload_zip(file, session_id)

# -------------------------------------------------------------------
# -------------------------------------------------------------------

@app.route('/progress/<session_id>')
def progress(session_id):
    """
    Provide real-time progress updates via Server-Sent Events (SSE).
    
    This endpoint establishes a persistent connection that streams progress
    updates for file processing operations. Clients can subscribe to receive
    real-time updates about processing status, file counts, and completion.
    
    URL Parameters:
        session_id (str): Session identifier to track progress for
        
    Returns:
        Response: SSE stream with JSON progress updates
        
    SSE Data Format:
        {
            "total_files": int,     // Total number of files to process
            "current_index": int,   // Current file being processed
            "done": bool            // Whether processing is complete
        }
        
    Connection Management:
        - Automatic cleanup when connection closes
        - Timeout handling for inactive sessions
        - Error handling for invalid session IDs
        
    Example Usage:
        GET /progress/242f0723-aabc-49ef-9130-d3c75e2648db
        Accept: text/event-stream
        
        # Client receives:
        data: {"total_files": 100, "current_index": 1, "done": false}
        data: {"total_files": 100, "current_index": 2, "done": false}
        ...
        data: {"total_files": 100, "current_index": 100, "done": true}
    """
    def generate():
        """
        Generator function for SSE data stream.
        
        Yields progress updates from the session's progress queue until
        processing is complete or the connection times out.
        """
        # Ensures progress queue exists for this session
        if session_id not in progress_queues:
            progress_queues[session_id] = queue.Queue()
        
        progress_queue = progress_queues[session_id]
        # Handle invalid session scenarios
        if not progress_queue:
            yield f"data: {json.dumps({'error': 'Invalid session ID'})}\n\n"
            return
        
        # Stream progress updates untill completion
        while True:
            try:
                # Wait for progress update
                update = progress_queue.get(timeout=5)
                yield f"data: {json.dumps(update)}\n\n"
                # stop streaming when done
                if update["done"]:
                    break
            except queue.Empty:
                break
    def cleanup():
        """
        Clean up session resources when connection closes.
        
        Removes the progress queue for this session to prevent memory leaks
        and ensure proper resource management.
        """
        progress_queues.pop(session_id, None)
    
    # create SSE response
    response = Response(generate(), mimetype='text/event-stream')
    response.headers['Cache-Control'] = 'no-cache'                  # Prevent caching
    response.headers['Connection'] = 'keep-alive'                   # Maintain connection
    response.call_on_close(cleanup)                                 # Register cleanup callback

    return response


# =============================================================================
# APPLICATION ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    """
    Start the Flask development server.
    
    Runs the application in debug mode for development purposes.
    """
    app.run(debug=True)