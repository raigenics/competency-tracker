/**
 * TreePanel - Tree view component with search and expandable nodes
 * Matches ContentPage.html structure exactly
 */
import React, { useState, useCallback, useMemo } from 'react';

const TreePanel = ({
  title,
  addRootLabel = '+ Add',
  treeData = [],
  selectedNodeId,
  onNodeSelect,
  onAddRoot,
  renderNodeIcon = () => '📄',
  getNodeChildren = (node) => node.children || [],
  getNodeId = (node) => node.id,
  getNodeLabel = (node) => node.name || node.label || 'Unnamed',
  searchPlaceholder = 'Search skills, categories...',
  // Import/Export actions
  onImport = null,
  onDownloadTemplate = null,
  downloadTemplateHref = null,
  // Loading/error state props
  isLoading = false,
  loadingContent = null,
  errorContent = null
}) => {
  const [expandedNodes, setExpandedNodes] = useState(new Set());
  const [searchQuery, setSearchQuery] = useState('');

  const toggleExpand = (nodeId, e) => {
    e.stopPropagation();
    setExpandedNodes(prev => {
      const next = new Set(prev);
      if (next.has(nodeId)) {
        next.delete(nodeId);
      } else {
        next.add(nodeId);
      }
      return next;
    });
  };

  const handleNodeClick = (node) => {
    const nodeId = getNodeId(node);
    onNodeSelect(nodeId);
  };

  // Memoized filter function
  const filterNodes = useCallback((nodes, query) => {
    if (!query) return nodes;
    
    const lowerQuery = query.toLowerCase();
    
    const matchesSearch = (node) => {
      const label = getNodeLabel(node);
      if (label.toLowerCase().includes(lowerQuery)) return true;
      
      const children = getNodeChildren(node);
      if (children && children.length > 0) {
        return children.some(child => matchesSearch(child));
      }
      return false;
    };
    
    return nodes.filter(matchesSearch);
  }, [getNodeLabel, getNodeChildren]);

  // Memoize filtered data to avoid re-computation
  const filteredData = useMemo(() => 
    filterNodes(treeData, searchQuery),
    [treeData, searchQuery, filterNodes]
  );

  // When searching, auto-expand all nodes
  const shouldExpand = (nodeId) => {
    return searchQuery ? true : expandedNodes.has(nodeId);
  };

  const renderTreeNode = (node, depth = 0) => {
    const nodeId = getNodeId(node);
    const children = getNodeChildren(node);
    const hasChildren = children && children.length > 0;
    const isExpanded = shouldExpand(nodeId);
    const isSelected = selectedNodeId === nodeId;

    return (
      <div key={nodeId} className="tree-node">
        <div 
          className={`tree-item ${isSelected ? 'active' : ''}`}
          onClick={() => handleNodeClick(node)}
        >
          <span 
            className="expand-icon" 
            onClick={(e) => hasChildren && toggleExpand(nodeId, e)}
          >
            {hasChildren ? (isExpanded ? '▼' : '▶') : ''}
          </span>
          <span className="node-icon">{renderNodeIcon(node)}</span>
          <span className="node-label">{getNodeLabel(node)}</span>
        </div>
        {hasChildren && (
          <div className={`tree-children ${isExpanded ? 'expanded' : ''}`}>
            {children.map(child => renderTreeNode(child, depth + 1))}
          </div>
        )}
      </div>
    );
  };

  // Render tree content based on state
  const renderTreeContent = () => {
    // Show error content if provided
    if (errorContent) {
      return errorContent;
    }
    
    // Show loading content if loading
    if (isLoading && loadingContent) {
      return loadingContent;
    }
    
    // Show empty state if no data
    if (filteredData.length === 0) {
      if (searchQuery) {
        return (
          <div className="empty-state" style={{ padding: '24px', textAlign: 'center' }}>
            <div style={{ fontSize: '32px', marginBottom: '8px', opacity: 0.5 }}>🔍</div>
            <p style={{ color: 'var(--text-secondary)', fontSize: '14px', margin: 0 }}>
              No results found for "{searchQuery}"
            </p>
          </div>
        );
      }
      return (
        <div className="empty-state" style={{ padding: '24px', textAlign: 'center' }}>
          <div style={{ fontSize: '32px', marginBottom: '8px', opacity: 0.5 }}>📁</div>
          <p style={{ color: 'var(--text-secondary)', fontSize: '14px', margin: 0 }}>
            No items yet. Click "+ Add" to create one.
          </p>
        </div>
      );
    }
    
    // Render tree nodes
    return filteredData.map(node => renderTreeNode(node));
  };

  return (
    <div className="tree-panel">
      <div className="tree-header">
        <div className="tree-header-top">
          <h2>{title}</h2>
          <div className="tree-header-actions">
            {(onDownloadTemplate || downloadTemplateHref) && (
              <a 
                className="btn btn-ghost btn-sm" 
                href={downloadTemplateHref || '#'}
                onClick={onDownloadTemplate ? (e) => { e.preventDefault(); onDownloadTemplate(); } : undefined}
                download={downloadTemplateHref ? true : undefined}
                title="Download import template"
              >
                ⬇ Template
              </a>
            )}
            {onImport && (
              <button className="btn btn-secondary btn-sm" onClick={onImport} title="Import from file">
                ⤓ Import
              </button>
            )}
            <button className="btn btn-primary btn-sm" onClick={onAddRoot}>
              {addRootLabel}
            </button>
          </div>
        </div>
        <div className="search-box">
          <span className="search-icon">🔍</span>
          <input 
            type="text" 
            placeholder={searchPlaceholder}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            disabled={isLoading}
          />
        </div>
      </div>
      <div className="tree-content">
        {renderTreeContent()}
      </div>
    </div>
  );
};

export default TreePanel;
