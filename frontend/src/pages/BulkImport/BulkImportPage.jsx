import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import PageHeader from '../../components/PageHeader.jsx';
import { bulkImportApi } from '../../services/api/bulkImportApi.js';

const BulkImportPage = () => {
  const navigate = useNavigate();
  
  // File state
  const [selectedFile, setSelectedFile] = useState(null);
  const fileInputRef = useRef(null);
  
  // Import state
  const [isImporting, setIsImporting] = useState(false);
  const [importResults, setImportResults] = useState(null);
  const [importError, setImportError] = useState(null);
    // Progress tracking state
  const [jobId, setJobId] = useState(null);
  const [progressData, setProgressData] = useState(null);
  const pollingIntervalRef = useRef(null);
  
  // UI smoothing state for progress animation
  const [displayPercent, setDisplayPercent] = useState(0);
  const animationFrameRef = useRef(null);

  // File handlers
  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (file && (file.name.endsWith('.xlsx') || file.name.endsWith('.xls'))) {
      setSelectedFile(file);
      setImportResults(null);
      setImportError(null);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file && (file.name.endsWith('.xlsx') || file.name.endsWith('.xls'))) {
      setSelectedFile(file);
      setImportResults(null);
      setImportError(null);
    }
  };

  const removeFile = () => {
    setSelectedFile(null);
    setImportResults(null);
    setImportError(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };
  // Import handler
  const startImport = async () => {
    if (!selectedFile) return;

    setIsImporting(true);
    setImportError(null);
    setImportResults(null);
    setProgressData(null);

    try {
      console.log('Starting import with file:', selectedFile.name);
      const result = await bulkImportApi.importExcel(selectedFile);
      console.log('Import job started:', result);
      
      // New async flow: backend returns job_id immediately
      if (result.job_id) {
        setJobId(result.job_id);
        setProgressData({
          status: 'pending',
          percent_complete: 0,
          message: 'Initializing import...'
        });
        // Polling will be handled by useEffect
      } else {
        // Fallback: old synchronous response (backward compatibility)
        setImportResults(result);
        setIsImporting(false);
      }
    } catch (error) {
      console.error('Import failed:', error);
      setIsImporting(false);
      setImportError(error.response?.data?.detail || error.message || 'Failed to start import');
    }
  };

  // Poll for job status
  useEffect(() => {
    if (!jobId) return;

    const pollJobStatus = async () => {
      try {
        const status = await bulkImportApi.getJobStatus(jobId);
        console.log('Job status:', status);
        
        setProgressData({
          status: status.status,
          percent_complete: status.percent_complete || 0,
          message: status.message || 'Processing...',
          employees_processed: status.employees_processed,
          skills_processed: status.skills_processed
        });        // Check if job is complete
        if (status.status === 'completed') {
          setImportResults(status.result);
          // BUGFIX: Don't immediately hide progress - let animation complete first
          // Only hide progress UI after displayPercent reaches 100%
          // (This is handled in the animation effect cleanup)
          // setIsImporting(false); // MOVED - see animation effect
          setJobId(null);
          clearInterval(pollingIntervalRef.current);
        } else if (status.status === 'failed') {
          setImportError(status.error || 'Import failed');
          setIsImporting(false);
          setJobId(null);
          clearInterval(pollingIntervalRef.current);
        }
      } catch (error) {
        console.error('Failed to poll job status:', error);
        // Don't immediately fail - the job might still be running
        // Only fail after multiple attempts or on specific errors
        if (error.response?.status === 404) {
          setImportError('Job not found. It may have expired.');
          setIsImporting(false);
          setJobId(null);
          clearInterval(pollingIntervalRef.current);
        }
      }
    };

    // Start polling every 1 second
    pollingIntervalRef.current = setInterval(pollJobStatus, 1000);
    
    // Initial poll
    pollJobStatus();

    // Cleanup on unmount
    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
      }
    };
  }, [jobId]);
  // Smooth progress animation effect
  useEffect(() => {
    if (!progressData) {
      setDisplayPercent(0);
      return;
    }

    const targetPercent = progressData.percent_complete || 0;
    
    // COMPLETION ANIMATION: When backend completes quickly, animate to 100% smoothly
    if (progressData.status === 'completed' && displayPercent < 100) {
      const startPercent = displayPercent;
      const diff = 100 - startPercent;
      
      if (diff > 0) {
        // Animate to 100% over 1.5-2 seconds for smooth completion
        const duration = 1800; // 1.8 seconds
        const startTime = Date.now();
        
        const animate = () => {
          const elapsed = Date.now() - startTime;
          const progress = Math.min(elapsed / duration, 1);
          
          // Ease-out cubic for smooth deceleration
          const easeProgress = 1 - Math.pow(1 - progress, 3);
          const newPercent = startPercent + (diff * easeProgress);
          
          setDisplayPercent(newPercent);
          
          if (progress < 1) {
            animationFrameRef.current = requestAnimationFrame(animate);
          } else {
            setDisplayPercent(100);
          }
        };
        
        // Cancel any existing animation
        if (animationFrameRef.current) {
          cancelAnimationFrame(animationFrameRef.current);
        }
        
        animationFrameRef.current = requestAnimationFrame(animate);
      } else {
        setDisplayPercent(100);
      }
    } 
    // NORMAL PROGRESS: Update immediately for in-progress states
    else if (progressData.status !== 'completed') {
      // Cancel any existing animation when status changes back to processing
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
      setDisplayPercent(targetPercent);
    }
    // If already at 100%, just set it
    else if (displayPercent >= 100) {
      setDisplayPercent(100);
    }
    
    // Cleanup
    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [progressData, displayPercent]);
  // BUGFIX: Hide progress UI only after animation completes to prevent Import Report regression
  // This ensures the Import Report appears after smooth completion animation finishes
  // ROOT CAUSE: The completion animation (1.8s) + 100ms delay kept isImporting=true too long,
  // causing spinner to run even after import report was visible.
  // FIX: Progress section now checks `!importResults` to hide immediately when report appears.
  useEffect(() => {
    if (progressData?.status === 'completed' && displayPercent >= 100) {
      // Small delay to ensure final frame is rendered
      const timer = setTimeout(() => {
        setIsImporting(false);
      }, 100);
      return () => clearTimeout(timer);
    }
  }, [progressData?.status, displayPercent]);

  // Utility
  const downloadTemplate = () => {
    alert('Template download would start here.\n\nTemplate includes:\n• Pre-formatted columns\n• Sample data\n• Validation rules\n• Instructions sheet');
  };
  const resetFlow = () => {
    setSelectedFile(null);
    setImportResults(null);
    setImportError(null);
    setIsImporting(false);
    setJobId(null);
    setProgressData(null);
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
    }
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className="min-h-screen bg-[#f8fafc]">
      <PageHeader 
        title="Bulk Import – Employee & Skill Data"
        subtitle="Upload an Excel file to bulk add or update employee and skill records."
      />

      <div className="px-8 py-8">
        <div className="max-w-[1200px] mx-auto">
          
          {/* Upload Section */}
          <div className="bg-white rounded-xl border-2 border-[#e2e8f0] mb-6 overflow-hidden">
            <div className="px-6 py-5 border-b-2 border-[#e2e8f0]">
              <h2 className="text-lg font-semibold text-[#1e293b]">Upload Excel File</h2>
            </div>
            
            <div className="p-6">
              {/* Template Section */}
              <div className="bg-[#f0f9ff] border border-[#bae6fd] rounded-lg p-4 flex items-center gap-4 mb-6">
                <div className="w-10 h-10 bg-[#0284c7] rounded-lg flex items-center justify-center text-white text-xl flex-shrink-0">
                  📥
                </div>
                <div className="flex-1">
                  <h4 className="text-sm font-semibold text-[#0c4a6e] mb-1">Step 1: Download Excel Template</h4>
                  <p className="text-xs text-[#075985]">Use this template to ensure correct format and avoid validation errors.</p>
                </div>
                <button 
                  onClick={downloadTemplate}
                  className="px-5 py-2.5 bg-white text-[#475569] border-2 border-[#e2e8f0] rounded-lg text-sm font-medium hover:bg-[#f8fafc] hover:border-[#cbd5e1] transition-colors"
                >
                  Download Template
                </button>
              </div>

              {/* Upload Section */}
              <div>
                <h4 className="text-sm font-semibold mb-3 text-[#1e293b]">Step 2: Upload Your File</h4>
                <div 
                  className={`border-3 border-dashed rounded-xl p-16 text-center cursor-pointer transition-all ${
                    selectedFile 
                      ? 'border-[#16a34a] bg-[#f0fdf4]' 
                      : 'border-[#cbd5e1] bg-[#f8fafc] hover:border-[#667eea] hover:bg-[#f0f4ff]'
                  }`}
                  onClick={() => !isImporting && fileInputRef.current?.click()}
                  onDragOver={handleDragOver}
                  onDrop={handleDrop}
                >
                  <div className={`w-16 h-16 rounded-full mx-auto mb-5 flex items-center justify-center text-3xl ${
                    selectedFile ? 'bg-[#dcfce7]' : 'bg-[#e0e7ff]'
                  }`}>
                    {selectedFile ? '✅' : '📤'}
                  </div>
                  <div className="text-base text-[#475569] mb-2">
                    {selectedFile ? 'File uploaded successfully!' : 'Drag & drop your Excel file here, or click to browse'}
                  </div>
                  <div className="text-[13px] text-[#94a3b8]">Accepts .xlsx files only</div>
                  <div className="text-xs text-[#64748b] mt-2">Max file size: 10 MB | Max rows: 5,000</div>
                  <input 
                    ref={fileInputRef}
                    type="file" 
                    accept=".xlsx" 
                    className="hidden" 
                    onChange={handleFileSelect}
                    disabled={isImporting}
                  />
                </div>
                
                {selectedFile && (
                  <div className="mt-5 flex items-center justify-between gap-3 p-4 bg-white border border-[#e2e8f0] rounded-lg">
                    <div>
                      <div className="text-sm text-[#1e293b] font-medium">{selectedFile.name}</div>
                      <div className="text-xs text-[#64748b]">{formatFileSize(selectedFile.size)}</div>
                    </div>
                    <div className="flex gap-2">
                      <button 
                        onClick={(e) => { e.stopPropagation(); removeFile(); }}
                        disabled={isImporting}
                        className="px-3 py-1.5 bg-[#fee2e2] text-[#dc2626] rounded-md text-xs font-medium hover:bg-[#fecaca] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        Remove
                      </button>
                      <button 
                        onClick={(e) => { e.stopPropagation(); startImport(); }}
                        disabled={isImporting}
                        className="px-5 py-2.5 bg-[#667eea] text-white rounded-lg text-sm font-medium hover:bg-[#5568d3] hover:-translate-y-0.5 hover:shadow-lg hover:shadow-[#667eea]/30 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {isImporting ? 'Importing...' : 'Start Import'}
                      </button>
                    </div>
                  </div>
                )}
                
                <p className="text-xs text-[#64748b] mt-3">
                  💡 <strong>Tip:</strong> Please use the provided template. Extra or renamed columns may cause errors.
                </p>
              </div>
            </div>
          </div>          {/* Import Progress */}
          {/* FIX: Hide spinner immediately when import results are available (don't wait for animation) */}
          {isImporting && !importResults && (
            <div className="bg-white rounded-xl border-2 border-[#e2e8f0] mb-6 overflow-hidden">
              <div className="px-6 py-5 border-b-2 border-[#e2e8f0]">
                <h2 className="text-lg font-semibold text-[#1e293b]">Import in Progress</h2>
              </div><div className="p-6">
                <div className="text-center py-10">
                  <div className="w-12 h-12 border-4 border-[#e2e8f0] border-t-[#667eea] rounded-full mx-auto mb-4 animate-spin"></div>
                  <div className="text-base text-[#475569] mb-2">
                    {progressData?.status === 'completed' && displayPercent < 100
                      ? 'Finalizing import...' 
                      : progressData?.message || 'Importing data... Please wait'}
                  </div>
                  
                  {/* Progress Bar */}
                  {progressData && progressData.percent_complete !== undefined && (
                    <div className="max-w-[600px] mx-auto mt-6">
                      <div className="flex items-center justify-between mb-2">
                        <div className="text-sm text-[#64748b]">Progress</div>
                        <div className="text-sm font-semibold text-[#667eea]">
                          {Math.round(displayPercent)}%
                        </div>
                      </div>
                      <div className="w-full bg-[#e2e8f0] rounded-full h-3 overflow-hidden">
                        <div 
                          className="bg-gradient-to-r from-[#667eea] to-[#764ba2] h-full rounded-full transition-all duration-500 ease-out"
                          style={{ width: `${displayPercent}%` }}
                        ></div>
                      </div>
                        {/* Detailed counts */}
                      {(progressData.employees_processed !== undefined || progressData.skills_processed !== undefined) && (
                        <div className="flex gap-6 justify-center mt-4 text-sm text-[#64748b]">
                          {progressData.employees_processed !== undefined && (
                            <div>
                              <span className="font-medium">Employees:</span> {progressData.employees_processed}
                            </div>
                          )}
                          {progressData.skills_processed !== undefined && (
                            <div>
                              <span className="font-medium">Skills:</span> {progressData.skills_processed}
                            </div>
                          )}
                        </div>
                      )}
                      
                      {/* Context-aware helper text */}
                      {progressData.percent_complete < 50 && (
                        <div className="text-xs text-[#64748b] mt-3 italic">
                          📋 Preparing data and clearing previous imports... (this is fast)
                        </div>
                      )}
                      {progressData.percent_complete >= 50 && progressData.percent_complete < 85 && (
                        <div className="text-xs text-[#64748b] mt-3 italic">
                          ⏳ Importing and validating skills... (this may take 1-2 minutes for large files)
                        </div>
                      )}
                      {progressData.percent_complete >= 85 && progressData.percent_complete < 100 && (
                        <div className="text-xs text-[#64748b] mt-3 italic">
                          💾 Finalizing and saving to database... (almost done!)
                        </div>
                      )}
                    </div>
                  )}
                  
                  <div className="bg-[#fef3c7] border border-[#fde047] px-4 py-3 rounded-lg text-[13px] text-[#854d0e] max-w-[600px] mx-auto mt-6">
                    ⚠️ Do not close this page while import is in progress.
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Import Error */}
          {importError && (
            <div className="bg-white rounded-xl border-2 border-[#e2e8f0] mb-6 overflow-hidden">
              <div className="px-6 py-5 border-b-2 border-[#e2e8f0]">
                <h2 className="text-lg font-semibold text-[#dc2626]">Import Failed</h2>
              </div>
              <div className="p-6">
                <div className="bg-[#fef2f2] border-2 border-[#fca5a5] rounded-lg p-4 mb-6">
                  <div className="flex items-center gap-3">
                    <div className="text-2xl">❌</div>
                    <div className="flex-1">
                      <h4 className="text-sm font-semibold text-[#dc2626] mb-1">Import Failed</h4>
                      <p className="text-xs text-[#991b1b]">{importError}</p>
                    </div>
                  </div>
                </div>
                <button 
                  onClick={resetFlow}
                  className="px-5 py-2.5 bg-white text-[#475569] border-2 border-[#e2e8f0] rounded-lg text-sm font-medium hover:bg-[#f8fafc] hover:border-[#cbd5e1] transition-colors"
                >
                  ← Try Again
                </button>
              </div>
            </div>
          )}

          {/* Import Results */}
          {importResults && (
            <div className="bg-white rounded-xl border-2 border-[#e2e8f0] overflow-hidden">
              <div className="px-6 py-5 border-b-2 border-[#e2e8f0]">
                <h2 className="text-lg font-semibold text-[#1e293b]">
                  {importResults.status === 'completed_with_errors' ? 'Import Completed with Errors' : 'Import Completed Successfully'}
                </h2>
              </div>
              
              <div className="p-6">
                <div className="text-center py-10">
                  <div className={`w-20 h-20 rounded-full mx-auto mb-6 flex items-center justify-center text-5xl ${
                    importResults.status === 'completed_with_errors' ? 'bg-[#fef3c7]' : 'bg-[#dcfce7]'
                  }`}>
                    {importResults.status === 'completed_with_errors' ? '⚠️' : '✅'}
                  </div>                  <h2 className="text-3xl font-bold text-[#1e293b] mb-8">
                    {importResults.status === 'completed_with_errors' 
                      ? `Import Completed with ${(importResults.employee_failed || 0) + (importResults.skill_failed || 0)} Error(s)`
                      : 'All Records Imported Successfully!'
                    }
                  </h2>{/* Summary Stats - Separate Employee and Skill Sections */}
                  <div className="space-y-6 max-w-[800px] mx-auto mb-8">
                    {/* Employee Summary */}
                    <div>
                      <h3 className="text-sm font-semibold text-[#475569] mb-3 text-left">Employee Import</h3>
                      <div className="grid grid-cols-3 gap-4">
                        <div className="bg-[#f8fafc] border-2 border-[#e2e8f0] rounded-lg p-4">
                          <div className="text-xl mb-1">👥</div>
                          <div className="text-2xl font-bold text-[#1e293b] mb-1">
                            {importResults.employee_total || 0}
                          </div>
                          <div className="text-xs text-[#64748b] font-medium">Total Employees</div>
                        </div>
                        <div className="bg-[#f0fdf4] border-2 border-[#86efac] rounded-lg p-4">
                          <div className="text-xl mb-1">✅</div>
                          <div className="text-2xl font-bold text-[#16a34a] mb-1">
                            {importResults.employee_imported || 0}
                          </div>
                          <div className="text-xs text-[#64748b] font-medium">Imported</div>
                        </div>
                        <div className="bg-[#fef2f2] border-2 border-[#fca5a5] rounded-lg p-4">
                          <div className="text-xl mb-1">❌</div>
                          <div className="text-2xl font-bold text-[#dc2626] mb-1">
                            {importResults.employee_failed || 0}
                          </div>
                          <div className="text-xs text-[#64748b] font-medium">Failed</div>
                        </div>
                      </div>
                    </div>

                    {/* Skill Summary */}
                    <div>
                      <h3 className="text-sm font-semibold text-[#475569] mb-3 text-left">Skill Import</h3>
                      <div className="grid grid-cols-3 gap-4">
                        <div className="bg-[#f8fafc] border-2 border-[#e2e8f0] rounded-lg p-4">
                          <div className="text-xl mb-1">🎯</div>
                          <div className="text-2xl font-bold text-[#1e293b] mb-1">
                            {importResults.skill_total || 0}
                          </div>
                          <div className="text-xs text-[#64748b] font-medium">Total Skills</div>
                          {importResults.skill_original_total && importResults.skill_original_total !== importResults.skill_total && (
                            <div className="text-[10px] text-[#94a3b8] mt-1">
                              ({importResults.skill_original_total} rows, expanded from comma-separated)
                            </div>
                          )}
                        </div>
                        <div className="bg-[#f0fdf4] border-2 border-[#86efac] rounded-lg p-4">
                          <div className="text-xl mb-1">✅</div>
                          <div className="text-2xl font-bold text-[#16a34a] mb-1">
                            {importResults.skill_imported || importResults.skills_imported || 0}
                          </div>
                          <div className="text-xs text-[#64748b] font-medium">Imported</div>
                        </div>
                        <div className="bg-[#fef2f2] border-2 border-[#fca5a5] rounded-lg p-4">
                          <div className="text-xl mb-1">❌</div>
                          <div className="text-2xl font-bold text-[#dc2626] mb-1">
                            {importResults.skill_failed || 0}
                          </div>
                          <div className="text-xs text-[#64748b] font-medium">Failed</div>
                        </div>
                      </div>
                    </div>
                  </div>                  {/* Failed Rows Table */}
                  {importResults.failed_rows && importResults.failed_rows.length > 0 && (
                    <div className="max-w-[1000px] mx-auto mb-8">
                      <h3 className="text-lg font-semibold text-[#1e293b] mb-4 text-left">Failed Rows Details</h3>
                      <div className="border-2 border-[#e2e8f0] rounded-lg overflow-hidden">
                        <div className="overflow-x-auto">
                          <table className="w-full">
                            <thead>
                              <tr className="bg-[#f8fafc] border-b-2 border-[#e2e8f0]">
                                <th className="px-4 py-3 text-left text-xs font-semibold text-[#64748b] uppercase whitespace-nowrap">Sheet</th>
                                <th className="px-4 py-3 text-left text-xs font-semibold text-[#64748b] uppercase whitespace-nowrap">Excel Row</th>
                                <th className="px-4 py-3 text-left text-xs font-semibold text-[#64748b] uppercase whitespace-nowrap">ZID</th>
                                <th className="px-4 py-3 text-left text-xs font-semibold text-[#64748b] uppercase whitespace-nowrap">Employee Name</th>
                                <th className="px-4 py-3 text-left text-xs font-semibold text-[#64748b] uppercase whitespace-nowrap">Skill</th>
                                <th className="px-4 py-3 text-left text-xs font-semibold text-[#64748b] uppercase whitespace-nowrap">Category</th>
                                <th className="px-4 py-3 text-left text-xs font-semibold text-[#64748b] uppercase whitespace-nowrap">Error</th>
                              </tr>
                            </thead>
                            <tbody>
                              {importResults.failed_rows.map((row, idx) => (
                                <tr key={idx} className="border-b border-[#e2e8f0] hover:bg-[#f8fafc]">
                                  <td className="px-4 py-3 text-[13px] text-[#475569] whitespace-nowrap">
                                    <span className={`inline-block px-2 py-1 rounded text-xs font-medium ${
                                      row.sheet === 'Employee' 
                                        ? 'bg-[#dbeafe] text-[#1e40af]' 
                                        : 'bg-[#fef3c7] text-[#92400e]'
                                    }`}>
                                      {row.sheet || 'Unknown'}
                                    </span>
                                  </td>
                                  <td className="px-4 py-3 text-[13px] text-[#475569] whitespace-nowrap">
                                    {row.excel_row_number || row.row_number || '-'}
                                  </td>
                                  <td className="px-4 py-3 text-[13px] text-[#475569] whitespace-nowrap">
                                    {row.zid || '-'}
                                  </td>
                                  <td className="px-4 py-3 text-[13px] text-[#475569]">
                                    {row.employee_name || row.full_name || '-'}
                                  </td>
                                  <td className="px-4 py-3 text-[13px] text-[#475569]">
                                    {row.skill_name || '-'}
                                  </td>
                                  <td className="px-4 py-3 text-[13px] text-[#475569]">
                                    {row.category && row.subcategory 
                                      ? `${row.category} → ${row.subcategory}`
                                      : (row.category || row.subcategory || '-')
                                    }
                                  </td>
                                  <td className="px-4 py-3 text-[13px] text-[#dc2626]">
                                    {row.error_code && <span className="font-semibold">[{row.error_code}]</span>} {row.message}
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Action Buttons */}
                  <div className="flex flex-wrap gap-3 justify-center">
                    <button
                      onClick={() => navigate('/employees')}
                      className="px-5 py-2.5 bg-[#667eea] text-white rounded-lg text-sm font-medium hover:bg-[#5568d3] hover:-translate-y-0.5 hover:shadow-lg hover:shadow-[#667eea]/30 transition-all"
                    >
                      Go to Employees Page →
                    </button>
                    <button 
                      onClick={resetFlow}
                      className="px-5 py-2.5 bg-white text-[#475569] border-2 border-[#e2e8f0] rounded-lg text-sm font-medium hover:bg-[#f8fafc] hover:border-[#cbd5e1] transition-colors"
                    >
                      Import Another File
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default BulkImportPage;
