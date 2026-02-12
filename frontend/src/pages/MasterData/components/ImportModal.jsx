/**
 * ImportModal - Modal for importing data via file upload or copy/paste
 * Matches ContentPage.html modal structure exactly
 */
import React, { useState, useRef } from 'react';

const ImportModal = ({
  isOpen,
  onClose,
  itemType = 'items',
  onImport
}) => {
  const [activeTab, setActiveTab] = useState('file');
  const [pasteContent, setPasteContent] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);
  const fileInputRef = useRef(null);

  const handleOverlayClick = (e) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setSelectedFile(e.dataTransfer.files[0]);
    }
  };

  const handleImport = () => {
    if (onImport) {
      if (activeTab === 'file' && selectedFile) {
        onImport({ type: 'file', file: selectedFile });
      } else if (activeTab === 'paste' && pasteContent) {
        onImport({ type: 'paste', content: pasteContent });
      }
    }
    onClose();
  };

  const resetState = () => {
    setActiveTab('file');
    setPasteContent('');
    setSelectedFile(null);
  };

  const handleClose = () => {
    resetState();
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay active" onClick={handleOverlayClick}>
      <div className="modal modal-large">
        <div className="modal-header">
          <div className="modal-title">📥 Import {itemType}</div>
          <button className="modal-close" onClick={handleClose}>✕</button>
        </div>
        <div className="modal-body">
          {/* Tab Navigation */}
          <div className="import-tabs">
            <button
              className={`import-tab ${activeTab === 'file' ? 'active' : ''}`}
              onClick={() => setActiveTab('file')}
            >
              📁 File Upload
            </button>
            <button
              className={`import-tab ${activeTab === 'paste' ? 'active' : ''}`}
              onClick={() => setActiveTab('paste')}
            >
              📋 Copy & Paste
            </button>
          </div>

          {/* File Upload Tab */}
          {activeTab === 'file' && (
            <div className="import-content">
              <div
                className="file-drop-zone"
                onClick={() => fileInputRef.current?.click()}
                onDragOver={handleDragOver}
                onDrop={handleDrop}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".csv,.xlsx,.xls"
                  style={{ display: 'none' }}
                  onChange={handleFileChange}
                />
                {selectedFile ? (
                  <div className="file-selected">
                    <div className="file-icon">📄</div>
                    <div className="file-name">{selectedFile.name}</div>
                    <div className="file-size">
                      {(selectedFile.size / 1024).toFixed(1)} KB
                    </div>
                  </div>
                ) : (
                  <>
                    <div className="drop-icon">📁</div>
                    <div className="drop-text">
                      Drop file here or click to browse
                    </div>
                    <div className="drop-hint">
                      Supports CSV, Excel (.xlsx, .xls)
                    </div>
                  </>
                )}
              </div>
              <div className="import-format-info">
                <h4>Expected Format:</h4>
                <p>The first row should contain column headers:</p>
                <code>Name, Description, Parent (optional)</code>
              </div>
            </div>
          )}

          {/* Copy & Paste Tab */}
          {activeTab === 'paste' && (
            <div className="import-content">
              <textarea
                className="import-textarea"
                placeholder={`Paste your ${itemType} here, one per line...\n\nFormat:\nName | Description | Parent (optional)\n\nExample:\nReact | A JavaScript library for building UIs | Frontend Frameworks\nTypeScript | Typed superset of JavaScript`}
                value={pasteContent}
                onChange={(e) => setPasteContent(e.target.value)}
                rows={10}
              />
              <div className="import-format-info">
                <h4>Format Options:</h4>
                <ul>
                  <li>One item per line (name only)</li>
                  <li>Pipe-separated: <code>Name | Description | Parent</code></li>
                  <li>Tab-separated (paste from Excel)</li>
                </ul>
              </div>
            </div>
          )}
        </div>
        <div className="modal-footer">
          <button className="btn btn-secondary" onClick={handleClose}>
            Cancel
          </button>
          <button
            className="btn btn-primary"
            onClick={handleImport}
            disabled={activeTab === 'file' ? !selectedFile : !pasteContent.trim()}
          >
            Import
          </button>
        </div>
      </div>
    </div>
  );
};

export default ImportModal;
