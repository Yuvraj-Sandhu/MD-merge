from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os, io
import zipfile
import tempfile

app = Flask(__name__)
CORS(app)

MAX_FILES_PER_MERGE = 50
MAX_WORDS = 50000

@app.route("/upload", methods=["POST"])
def upload_zip():
    if "file" not in request.files:
        return jsonify({"error": "No file part in request"}),400
    
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400
    
    if not file.filename.endswith(".zip"):
        return jsonify({"error": "Only ZIP files are allowed"}), 400
    
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

        if md_count <= 50:
            mem_zip = io.BytesIO()
            with zipfile.ZipFile(mem_zip, "w") as out_zip:
                for path in md_files:
                    arcname = os.path.basename(path)
                    out_zip.write(path, arcname=arcname)
                mem_zip.seek(0)
                return send_file(mem_zip, as_attachment=True, download_name=file.filename)
            
        merged_files = []
        for i in range(0,md_count,MAX_FILES_PER_MERGE):
            batch = md_files[i:i+MAX_FILES_PER_MERGE]
            merged_content = ""
            for file_path in batch:
                with open(file_path, "r", encoding="utf-8") as f:
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

        return send_file(mem_zip, as_attachment=True, download_name="merged_files.zip")

    
def count_words(text):
    return len(text.split())

if __name__ == "__main__":
    app.run(debug=True)