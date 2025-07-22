import { useState, useEffect } from 'react'
import { useAuth0 } from '@auth0/auth0-react'
import apiClient from '../utils/apiClient'

const FileList = () => {
  const { getAccessTokenSilently } = useAuth0()
  const [files, setFiles] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const fetchFiles = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const token = await getAccessTokenSilently()
      const response = await apiClient.get('/files', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      
      setFiles(response.data)
    } catch (error) {
      console.error('Error fetching files:', error)
      setError('Failed to load files. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchFiles()
    
    // Listen for file upload events to refresh the list
    const handleFileUploaded = () => {
      fetchFiles()
    }
    
    window.addEventListener('fileUploaded', handleFileUploaded)
    
    return () => {
      window.removeEventListener('fileUploaded', handleFileUploaded)
    }
  }, [])

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const formatDate = (dateString) => {
    const date = new Date(dateString)
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit' 
    })
  }

  if (loading) {
    return (
      <div className="file-list">
        <h3>Your Images</h3>
        <div className="loading-state">Loading your files...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="file-list">
        <h3>Your Images</h3>
        <div className="error-state">
          {error}
          <br />
          <button className="btn btn-primary" onClick={fetchFiles} style={{ marginTop: '10px' }}>
            Try Again
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="file-list">
      <h3>Your Images ({files.length})</h3>
      
      {files.length === 0 ? (
        <div className="empty-state">
          <p>No images uploaded yet.</p>
          <p>Upload your first image using the form above!</p>
        </div>
      ) : (
        <div className="file-grid">
          {files.map((file) => (
            <div key={file.id} className="file-item">
              <img 
                src={file.file_url} 
                alt={file.original_filename}
                className="file-preview"
                onError={(e) => {
                  e.target.style.display = 'none'
                }}
              />
              <div className="file-info">
                <div className="file-name">{file.original_filename}</div>
                <div className="file-details">
                  <div className="file-size">Size: {formatFileSize(file.file_size)}</div>
                  <div className="file-date">Uploaded: {formatDate(file.uploaded_at)}</div>
                  <a 
                    href={file.file_url} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="file-url"
                  >
                    View Full Size
                  </a>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default FileList
