/**
 * TreePanel - Tree view component with search and expandable nodes
 * Matches ContentPage.html structure exactly
 * 
 * Search behavior matches Organizational Skill Map:
 * - 300ms debounce
 * - Minimum 2 characters to trigger search
 * - Case-insensitive matching
 * - Recursive filtering of tree nodes
 */
import React, { useState, useCallback, useMemo, useEffect } from 'react';

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
  errorContent = null,
  // Skill-level search support (optional) - used by SkillTaxonomyPage
  onSearchChange = null, // Called with debounced search query
  searchFallbackContent = null, // Custom content when tree filter returns empty but skill match exists
  hasSearchFallback = false // If true, don't show "No results found" - parent handles it
}) => {
  const [expandedNodes, setExpandedNodes] = useState(new Set());
  const [searchQuery, setSearchQuery] = useState('');
  // Debounced search query - actual value used for filtering
  const [debouncedSearchQuery, setDebouncedSearchQuery] = useState('');

  // Debounce search by 300ms (matches Org Skill Map behavior)
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      // Only apply search if 2+ characters (matches Org Skill Map behavior)
      let newDebouncedQuery = '';
      if (searchQuery && searchQuery.trim().length >= 2) {
        newDebouncedQuery = searchQuery.trim();
      }
      setDebouncedSearchQuery(newDebouncedQuery);
      // Notify parent of search change (for skill-level search)
      if (onSearchChange) {
        onSearchChange(newDebouncedQuery);
      }
    }, 300);
    return () => clearTimeout(timeoutId);
  }, [searchQuery, onSearchChange]);

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

  // Memoized filter function - recursively filters nodes AND their children
  const filterNodes = useCallback((nodes, query) => {
    if (!query) return nodes;
    
    const lowerQuery = query.toLowerCase();
    
    // Recursively filter nodes, preserving only matching nodes and their ancestors
    const filterRecursive = (nodeList) => {
      const result = [];
      
      for (const node of nodeList) {
        const label = getNodeLabel(node);
        const nodeMatches = label.toLowerCase().includes(lowerQuery);
        const children = getNodeChildren(node);
        
        // Recursively filter children
        const filteredChildren = children && children.length > 0
          ? filterRecursive(children)
          : [];
        
        // Include node if it matches OR has matching descendants
        if (nodeMatches || filteredChildren.length > 0) {
          // Create a shallow copy with filtered children
          result.push({
            ...node,
            children: filteredChildren
          });
        }
      }
      
      return result;
    };
    
    return filterRecursive(nodes);
  }, [getNodeLabel, getNodeChildren]);

  // Memoize filtered data to avoid re-computation (uses debounced query)
  const filteredData = useMemo(() => 
    filterNodes(treeData, debouncedSearchQuery),
    [treeData, debouncedSearchQuery, filterNodes]
  );

  // When searching, auto-expand all nodes
  const shouldExpand = (nodeId) => {
    return debouncedSearchQuery ? true : expandedNodes.has(nodeId);
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
      if (debouncedSearchQuery) {
        // If parent provides fallback content (e.g., skill match), use it instead of "No results"
        if (hasSearchFallback && searchFallbackContent) {
          return searchFallbackContent;
        }
        // Only show "No results found" if parent hasn't handled it
        if (!hasSearchFallback) {
          return (
            <div className="empty-state" style={{ padding: '24px', textAlign: 'center' }}>
              <div style={{ fontSize: '32px', marginBottom: '8px', opacity: 0.5 }}>🔍</div>
              <p style={{ color: 'var(--text-secondary)', fontSize: '14px', margin: 0 }}>
                No results found for "{debouncedSearchQuery}"
              </p>
            </div>
          );
        }
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
        <div className="search-box" style={{ position: 'relative' }}>
          <span className="search-icon">🔍</span>
          <input 
            type="text" 
            placeholder={searchPlaceholder}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            disabled={isLoading}
            style={{ paddingRight: searchQuery ? '28px' : undefined }}
          />
          {searchQuery && (
            <button
              type="button"
              onClick={() => setSearchQuery('')}
              style={{
                position: 'absolute',
                right: '8px',
                top: '50%',
                transform: 'translateY(-50%)',
                background: 'none',
                border: 'none',
                cursor: 'pointer',
                padding: '2px',
                fontSize: '14px',
                color: 'var(--text-secondary, #64748b)',
                lineHeight: 1,
              }}
              aria-label="Clear search"
              title="Clear search"
            >
              ✕
            </button>
          )}
        </div>
      </div>
      <div className="tree-content">
        {renderTreeContent()}
      </div>
    </div>
  );
};

export default TreePanel;
