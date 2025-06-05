import { useState } from 'react'
import './App.css'

function App() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [progressMessage, setProgressMessage] = useState('');
  const [downloadUrl, setDownloadUrl] = useState('');
  const [message, setMessage] = useState('');

  const handleFileChange = (e) => {
    setSelectedFile(e.target.files[0]);
    setDownloadUrl('');
    setMessage('');
    setProgress(0);
    setProgressMessage('');
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setMessage('Please select a ZIP file first.');
      return;
    }

    const sessionId = crypto.randomUUID();
    setUploading(true);
    setMessage('');
    setProgress(0);
    setProgressMessage('');
    setDownloadUrl('');

    const formData = new FormData();
    formData.append('file', selectedFile);

    // Listen for real-time updates
    const eventSource = new EventSource(`http://localhost:5000/progress/${sessionId}`);
    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        const { total_files, current_index, done } = data;

        if (total_files > 0) {
          const percent = Math.floor((current_index / total_files) * 100);
          setProgress(percent);
          setProgressMessage(`Merging file ${current_index} of ${total_files}...`);
        }

        if (done) {
          eventSource.close();
        }
      } catch (err) {
        console.error('Error parsing SSE data:', err);
      }
    };

    try {
      const response = await fetch(`http://localhost:5000/upload/${sessionId}`, {
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
      a.download = 'merged_files.zip';
      document.body.appendChild(a);
      a.click();
      a.remove();

    } catch (err) {
      setMessage('Error processing file: ' + err.message);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className='app-container'>
      <h1 className='app-title'>Markdown ZIP Merge</h1>

      <div className='upload-form'>
        <span className="form-title">Upload your file</span>
        <p className="form-paragraph">Should be a zip file</p>
        <div className='file-input-container'>
          <span className="drop-title">Drop file here</span>
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
            <p>{progressMessage}</p>
          </div>
        )}

        {message && <p className='message'>{message}</p>}

        {downloadUrl && (
          <p className="download-link">
            Or download manually: <a className='link' href={downloadUrl} download="merged_files.zip">Download ZIP file</a>
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
