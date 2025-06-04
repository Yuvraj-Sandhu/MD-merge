from flask import Flask, request, jsonify, send_file, Response, stream_with_context
from flask_cors import CORS
import os, io
import zipfile
import tempfile
import time
import queue
import json

app = Flask(__name__)
CORS(app)

MAX_FILES_PER_MERGE = 50
MAX_WORDS = 50000

progress_queues = {} 

def upload_zip(file, session_id):
    if session_id not in progress_queues:
        progress_queues[session_id] = queue.Queue()

    progress_queue = progress_queues[session_id]
    progress_data = {
        "total_files":0,
        "current_index": 0,
        "done": False
    }

    with tempfile.TemporaryDirectory() as tmpdirname:
        zip_path = os.path.join(tmpdirname, file.filename)
        file.save(zip_path)

        try: 
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(tmpdirname)
        except zipfile.BadZipFile:
            return jsonify({"error": "Invalid ZIP file"}), 400
        
        md_files = []
        for root,_,files in os.walk(tmpdirname):
            for name in files:
                if name.endswith(".md"):
                    md_files.append(os.path.join(root,name))
        
        md_count = len(md_files)
        progress_data["total_files"] = md_count

        if md_count <= 50:
            mem_zip = io.BytesIO()
            with zipfile.ZipFile(mem_zip, "w") as out_zip:
                for path in md_files:
                    arcname = os.path.basename(path)
                    out_zip.write(path, arcname=arcname)
                mem_zip.seek(0)
                progress_data["done"] = True
                return send_file(mem_zip, as_attachment=True, download_name=file.filename)
            
        merged_files = []
        for i in range(0,md_count,MAX_FILES_PER_MERGE):
            batch = md_files[i:i+MAX_FILES_PER_MERGE]
            merged_content = ""
            for idx,file_path in enumerate(batch):
                with open(file_path, "r", encoding="utf-8") as f:
                    
                    progress_data["current_index"] = idx + i + 1
                    progress_queue.put(progress_data.copy())
                    merged_content += f.read() + "\n\n"
            
            word_count = count_words(merged_content)
            filename = f"merged_part{i//MAX_FILES_PER_MERGE + 1}.md"
            if word_count > MAX_WORDS:
                filename = filename.replace(".md","_OVER50000WORDS.md")
            
            merged_files.append((filename,merged_content))
        
        mem_zip = io.BytesIO()
        with zipfile.ZipFile(mem_zip, "w") as out_zip:
            for filename, content in merged_files:
                out_zip.writestr(filename, content)
                
        
        mem_zip.seek(0)
        progress_data["done"] = True
        progress_queue.put(progress_data.copy())
        return send_file(mem_zip, as_attachment=True, download_name="merged_files.zip")


@app.route("/upload/<session_id>", methods=["POST"])
def upload(session_id):
    if "file" not in request.files:
        return jsonify({"error": "No file part in request"}),400
    
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400
    
    if not file.filename.endswith(".zip"):
        return jsonify({"error": "Only ZIP files are allowed"}), 400
    
    return upload_zip(file, session_id)

@app.route('/progress/<session_id>')
def progress(session_id):
    def generate():
        if session_id not in progress_queues:
            progress_queues[session_id] = queue.Queue()
        progress_queue = progress_queues[session_id]
        if not progress_queue:
            yield f"data: {json.dumps({'error': 'Invalid session ID'})}\n\n"
            return
        while True:
            try:
                update = progress_queue.get(timeout=5)
                yield f"data: {json.dumps(update)}\n\n"
                if update["done"]:
                    break
            except queue.Empty:
                break
    def cleanup():
        progress_queues.pop(session_id, None)
    
    response = Response(generate(), mimetype='text/event-stream')
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['Connection'] = 'keep-alive'
    response.call_on_close(cleanup)

    return response

    
def count_words(text):
    return len(text.split())

if __name__ == "__main__":
    app.run(debug=True)