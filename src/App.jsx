import { useState } from 'react'
import './App.css'

function App() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [downloadUrl, setDownloadUrl] = useState('');
  const [message, setMessage] = useState('');

  const handleFileChange = (e) => {
    setSelectedFile(e.target.files[0]);
    setDownloadUrl('');
    setMessage('');
    setProgress(0);
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setMessage('Please select a ZIP file first.');
      return;
    }
    setUploading(true);
    setMessage('');
    setProgress(0);
    setDownloadUrl('');

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const response = await fetch('http://localhost:5000/upload', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Upload failed');
      }

      // We expect backend to respond with the processed ZIP file as blob
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      setDownloadUrl(url);
      setMessage('File processed successfully! Your download should start automatically.');

      // Trigger automatic download
      const a = document.createElement('a');
      a.href = url;
      a.download = 'processed_markdown.zip';
      document.body.appendChild(a);
      a.click();
      a.remove();

    } catch (err) {
      setMessage('Error processing file: ' + err.message);
    } finally {
      setUploading(false);
      setProgress(0);
    }
  };

  return (
    <div className='app-container'>
      <h1 className='app-title'>Markdown ZIP Merge</h1>

      <div className='upload-form'>
        <span class="form-title">Upload your file</span>
        <p class="form-paragraph">Should be a zip file</p>
        <div className='file-input-container'>
          <span class="drop-title">Drop file here</span>
          or
          <input
            type="file"
            accept=".zip"
            onChange={handleFileChange}
            disabled={uploading}
            className='file-input'
          />
        </div>

        {uploading && (
          <div className='progress-container'>
            <progress value={progress} max="100" />
            <div>{progress}%</div>
          </div>
        )}

        {message && <p className='message'>{message}</p>}

        {downloadUrl && (
          <p className="download-link">
            Or download manually: <a href={downloadUrl} download="processed_markdown.zip">Download ZIP</a>
          </p>
        )}

        <button
          onClick={handleUpload}
          disabled={uploading || !selectedFile}
          className="upload-button"
        >
          {uploading ? 'Processing...' : 'Upload & Merge'}
        </button>
      </div>
    </div>
  );
}

export default App;
