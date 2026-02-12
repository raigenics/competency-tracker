/**
 * OrgHierarchyPage - Master Data page for managing Organization Hierarchy
 * Segments > SubSegments > Projects > Teams hierarchy
 * Loads data from backend API: GET /api/org-hierarchy
 */
import React, { useState, useMemo, useEffect, useCallback, useRef } from 'react';
import { fetchOrgHierarchy, createSegment, createSubSegment, createProject, createTeam, updateSegmentName, updateSubSegmentName, updateProjectName, updateTeamName, checkCanDeleteSegment, checkCanDeleteSubSegment, deleteSegment, deleteSubSegment, checkCanDeleteProject, deleteProject, deleteTeam } from '../../services/api/orgHierarchyApi';
import {
  MasterDataLayout,
  TreePanel,
  DetailsPanel,
  CreateEditModal,
  DeleteConfirmModal,
  DependencyModal,
  ImportModal,
  AuditModal,
  InfoSection,
  InfoBox,
  InfoGrid,
  InfoItem,
  StatsGrid,
  StatCard,
  Alert,
  EmptyState,
  InlineEditableTitle,
  OrgSubSegmentProjectsPanel,
  OrgProjectTeamsPanel
} from './components';

// Helper to find item by ID in nested structure
const findItemById = (items, id) => {
  for (const item of items) {
    if (item.id === id) return item;
    if (item.children) {
      const found = findItemById(item.children, id);
      if (found) return found;
    }
  }
  return null;
};

// Get type icon
const getTypeIcon = (type) => {
  switch (type) {
    case 'segment': return '🏢';
    case 'subsegment': return '🏬';
    case 'project': return '📋';
    case 'team': return '👥';
    default: return '📄';
  }
};

// Get type label
const getTypeLabel = (type) => {
  switch (type) {
    case 'segment': return 'Segment';
    case 'subsegment': return 'Sub-Segment';
    case 'project': return 'Project';
    case 'team': return 'Team';
    default: return 'Item';
  }
};

/**
 * Loading Indicator Component
 */
const LoadingIndicator = () => (
  <div className="loading-container">
    <div className="loading-spinner" />
    <div className="loading-message">
      Loading Organization Hierarchy...
    </div>
  </div>
);

/**
 * Error State Component
 */
const ErrorState = ({ error, onRetry }) => (
  <div className="error-container">
    <div className="error-icon">⚠️</div>
    <div className="error-title">Failed to Load Hierarchy</div>
    <div className="error-message">{error}</div>
    <button className="btn btn-primary" onClick={onRetry}>
      🔄 Retry
    </button>
  </div>
);

/**
 * Transform API response to tree structure for TreePanel
 * API returns: { segments: [...], total_segments, total_sub_segments, total_projects, total_teams }
 */
function transformApiResponse(apiResponse) {
  if (!apiResponse?.segments) return [];
  
  return apiResponse.segments.map(segment => ({
    id: `seg-${segment.segment_id}`,
    rawId: segment.segment_id,
    type: 'segment',
    name: segment.segment_name,
    description: '',
    createdAt: null,
    createdBy: null,
    subSegmentCount: segment.sub_segments?.length || 0,
    projectCount: segment.sub_segments?.reduce((sum, ss) => sum + (ss.projects?.length || 0), 0) || 0,
    teamCount: segment.sub_segments?.reduce((sum, ss) => 
      sum + (ss.projects?.reduce((pSum, p) => pSum + (p.teams?.length || 0), 0) || 0), 0) || 0,
    employeeCount: 0,
    children: (segment.sub_segments || []).map(subSeg => ({
      id: `subseg-${subSeg.sub_segment_id}`,
      rawId: subSeg.sub_segment_id,
      type: 'subsegment',
      name: subSeg.sub_segment_name,
      description: '',
      parentId: `seg-${segment.segment_id}`,
      createdAt: null,
      createdBy: null,
      projectCount: subSeg.projects?.length || 0,
      teamCount: subSeg.projects?.reduce((sum, p) => sum + (p.teams?.length || 0), 0) || 0,
      employeeCount: 0,
      children: (subSeg.projects || []).map(project => ({
        id: `proj-${project.project_id}`,
        rawId: project.project_id,
        type: 'project',
        name: project.project_name,
        description: '',
        parentId: `subseg-${subSeg.sub_segment_id}`,
        createdAt: null,
        createdBy: null,
        status: 'Active',
        teamCount: project.teams?.length || 0,
        employeeCount: 0,
        children: [], // Teams not shown in tree
        // Store teams separately for panel display
        teams: (project.teams || []).map(team => ({
          id: `team-${team.team_id}`,
          rawId: team.team_id,
          type: 'team',
          name: team.team_name,
          description: '',
          parentId: `proj-${project.project_id}`,
          createdAt: null,
          createdBy: null,
          employeeCount: 0,
          lead: null
        }))
      }))
    }))
  }));
}

const OrgHierarchyPage = () => {
  // Data state - initially empty, loaded from API
  const [treeData, setTreeData] = useState([]);
  const [selectedNodeId, setSelectedNodeId] = useState(null);
  
  // Loading state
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Abort controller ref for cleanup
  const abortControllerRef = useRef(null);
  
  /**
   * Load hierarchy data from API
   */
  const loadHierarchy = useCallback(async () => {
    // Cancel any pending request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    abortControllerRef.current = new AbortController();
    
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await fetchOrgHierarchy({
        signal: abortControllerRef.current.signal,
      });
      
      const transformedData = transformApiResponse(response);
      setTreeData(transformedData);
      setError(null);
    } catch (err) {
      if (err.name === 'AbortError') {
        return;
      }
      console.error('Failed to load org hierarchy:', err);
      setError(err.message || 'Failed to load organization hierarchy');
      setTreeData([]);
    } finally {
      setIsLoading(false);
    }
  }, []);
  
  // Load data on mount
  useEffect(() => {
    loadHierarchy();
    
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, [loadHierarchy]);
  
  // Modal states
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [dependencyModalOpen, setDependencyModalOpen] = useState(false);
  const [importModalOpen, setImportModalOpen] = useState(false);
  const [auditModalOpen, setAuditModalOpen] = useState(false);
  
  const [createType, setCreateType] = useState('segment');
  const [isSaving, setIsSaving] = useState(false);
  const [createError, setCreateError] = useState(null);
  
  // Delete state
  const [isDeleting, setIsDeleting] = useState(false);
  const [apiDependencies, setApiDependencies] = useState(null);  // Dependencies from API 409 response

  // Get selected item
  const selectedItem = useMemo(() => {
    if (!selectedNodeId) return null;
    return findItemById(treeData, selectedNodeId);
  }, [selectedNodeId, treeData]);

  // Handlers
  const handleNodeSelect = (nodeId) => {
    setSelectedNodeId(nodeId);
  };

  const handleEdit = () => {
    setEditModalOpen(true);
  };

  const handleDelete = async () => {
    // Only segment and subsegment support delete via API
    if (selectedItem?.type === 'segment' || selectedItem?.type === 'subsegment') {
      // Check for dependencies first (dry run) before showing any dialog
      try {
        let result;
        if (selectedItem.type === 'segment') {
          result = await checkCanDeleteSegment(selectedItem.rawId);
        } else {
          result = await checkCanDeleteSubSegment(selectedItem.rawId);
        }
        
        if (result.canDelete) {
          // No dependencies - show "Are you sure?" confirmation dialog
          setApiDependencies(null);
          setDeleteModalOpen(true);
        } else {
          // Has dependencies - show dependency modal directly (no confirmation)
          setApiDependencies(result.conflict.dependencies);
          setDependencyModalOpen(true);
        }
      } catch (err) {
        console.error('Failed to check delete dependencies:', err);
        // Could show error toast here
      }
    } else {
      // For project/team, check local dependencies (not implemented via API yet)
      if (selectedItem?.children?.length > 0 || selectedItem?.employeeCount > 0) {
        setApiDependencies(null);
        setDependencyModalOpen(true);
      } else {
        setDeleteModalOpen(true);
      }
    }
  };

  const handleAddChild = () => {
    if (selectedItem?.type === 'segment') {
      setCreateType('subsegment');
    } else if (selectedItem?.type === 'subsegment') {
      setCreateType('project');
    } else if (selectedItem?.type === 'project') {
      setCreateType('team');
    } else {
      setCreateType('segment');
    }
    setCreateError(null);
    setCreateModalOpen(true);
  };

  const handleCreate = async (formData) => {
    // Validate required name
    if (!formData.name || !formData.name.trim()) {
      setCreateError('Name is required');
      return;
    }
    
    setIsSaving(true);
    setCreateError(null);
    
    try {
      if (createType === 'segment') {
        await createSegment(formData.name.trim());
      } else if (createType === 'subsegment') {
        // Get parent segment's rawId from the selected parent
        const parentSegment = treeData.find(s => s.id === formData.parent);
        if (!parentSegment?.rawId) {
          setCreateError('Please select a parent segment');
          setIsSaving(false);
          return;
        }
        await createSubSegment(parentSegment.rawId, formData.name.trim());
      } else if (createType === 'project') {
        // For project, parent is the currently selected sub-segment
        if (!selectedItem || selectedItem.type !== 'subsegment') {
          setCreateError('Please select a sub-segment first');
          setIsSaving(false);
          return;
        }
        await createProject(selectedItem.rawId, formData.name.trim());
      } else if (createType === 'team') {
        // For team, parent is the currently selected project
        if (!selectedItem || selectedItem.type !== 'project') {
          setCreateError('Please select a project first');
          setIsSaving(false);
          return;
        }
        await createTeam(selectedItem.rawId, formData.name.trim());
      }
      
      // Success - close modal and refresh data
      setCreateModalOpen(false);
      setCreateError(null);
      
      // Refresh hierarchy to show new item
      await loadHierarchy();
      
    } catch (err) {
      console.error(`Failed to create ${createType}:`, err);
      // Extract error message from response
      const errorMsg = err?.response?.data?.detail 
        || err?.message 
        || `Failed to create ${createType}`;
      setCreateError(errorMsg);
    } finally {
      setIsSaving(false);
    }
  };

  const handleUpdate = (formData) => {
    console.log('Updating:', selectedItem?.id, formData);
    setEditModalOpen(false);
  };

  const handleConfirmDelete = useCallback(async () => {
    if (!selectedItem) return;
    
    const itemType = selectedItem.type;
    const rawId = selectedItem.rawId;
    
    // Only segment and subsegment are supported
    if (itemType !== 'segment' && itemType !== 'subsegment') {
      console.log('Delete not implemented for:', itemType);
      setDeleteModalOpen(false);
      return;
    }
    
    setIsDeleting(true);
    
    try {
      // Actually delete (we already checked for dependencies in handleDelete)
      if (itemType === 'segment') {
        await deleteSegment(rawId);
      } else {
        await deleteSubSegment(rawId);
      }
      
      // Success - close modal, clear selection, refresh hierarchy
      setDeleteModalOpen(false);
      setSelectedNodeId(null);
      await loadHierarchy();
    } catch (err) {
      console.error('Failed to delete:', err);
      setDeleteModalOpen(false);
      // Could show error toast here
    } finally {
      setIsDeleting(false);
    }
  }, [selectedItem, loadHierarchy]);

  const handleImport = (importData) => {
    console.log('Importing:', importData);
    setImportModalOpen(false);
  };

  const handleViewAudit = () => {
    setAuditModalOpen(true);
  };

  // Get dependencies for modal
  // Uses API-returned dependencies if available, otherwise falls back to local state
  const getDependencies = () => {
    // If we have API-returned dependencies with pre-built dependency list (from 409 response)
    if (apiDependencies?.dependencies) {
      return apiDependencies.dependencies;
    }
    
    // If we have API-returned dependencies (from 409 response) - legacy format
    if (apiDependencies) {
      const deps = [];
      if (apiDependencies.sub_segments) {
        deps.push({ icon: '🏬', label: `${apiDependencies.sub_segments} Sub-Segments` });
      }
      if (apiDependencies.projects) {
        deps.push({ icon: '📋', label: `${apiDependencies.projects} Projects` });
      }
      if (apiDependencies.teams) {
        deps.push({ icon: '👥', label: `${apiDependencies.teams} Teams` });
      }
      return deps;
    }
    
    // Fallback to local state (for project/team which don't have API delete yet)
    if (!selectedItem) return [];
    const deps = [];
    if (selectedItem.subSegmentCount) {
      deps.push({ icon: '🏬', label: `${selectedItem.subSegmentCount} Sub-Segments` });
    }
    if (selectedItem.projectCount) {
      deps.push({ icon: '📋', label: `${selectedItem.projectCount} Projects` });
    }
    if (selectedItem.teamCount) {
      deps.push({ icon: '👥', label: `${selectedItem.teamCount} Teams` });
    }
    if (selectedItem.employeeCount) {
      deps.push({ icon: '🧑', label: `${selectedItem.employeeCount} Employees` });
    }
    return deps;
  };

  // Get item name for dependency modal
  const getDependencyItemName = () => {
    if (apiDependencies?.itemName) {
      return apiDependencies.itemName;
    }
    return selectedItem?.name;
  };

  // Handle closing dependency modal
  const handleCloseDependencyModal = () => {
    setDependencyModalOpen(false);
    setApiDependencies(null);
  };

  // Determine what child type can be added
  const getChildType = () => {
    if (!selectedItem) return null;
    if (selectedItem.type === 'segment') return 'Sub-Segment';
    if (selectedItem.type === 'subsegment') return 'Project';
    if (selectedItem.type === 'project') return 'Team';
    return null;
  };

  // Handler specifically for adding sub-segment when a segment is selected
  const handleAddSubSegment = () => {
    setCreateType('subsegment');
    setCreateError(null);
    setCreateModalOpen(true);
  };

  /**
   * Handle inline title save for Segment/Sub-Segment names.
   * Uses optimistic update with rollback on failure.
   */
  const handleTitleSave = useCallback(async (newName) => {
    console.log('[handleTitleSave] Called with newName:', newName);
    console.log('[handleTitleSave] selectedItem:', selectedItem);
    
    if (!selectedItem || !newName?.trim()) {
      console.log('[handleTitleSave] Early return - no selectedItem or empty name');
      return;
    }
    
    const itemId = selectedItem.id;
    const rawId = selectedItem.rawId;
    const type = selectedItem.type;
    const oldName = selectedItem.name;
    const trimmedName = newName.trim();
    
    console.log('[handleTitleSave] Updating:', { itemId, rawId, type, oldName, trimmedName });
    
    // Skip if name didn't change
    if (trimmedName === oldName) {
      console.log('[handleTitleSave] Name unchanged, skipping');
      return;
    }
    
    // Only support segment and subsegment updates
    if (type !== 'segment' && type !== 'subsegment') {
      console.log('[handleTitleSave] Unsupported type:', type);
      return;
    }
    
    // Helper to update name in tree data recursively
    const updateNameInTree = (nodes, targetId, name) => {
      return nodes.map(node => {
        if (node.id === targetId) {
          return { ...node, name };
        }
        if (node.children) {
          return { ...node, children: updateNameInTree(node.children, targetId, name) };
        }
        return node;
      });
    };
    
    // Optimistic update
    console.log('[handleTitleSave] Applying optimistic update...');
    setTreeData(prev => updateNameInTree(prev, itemId, trimmedName));
    
    try {
      console.log('[handleTitleSave] Calling API...');
      if (type === 'segment') {
        await updateSegmentName(rawId, trimmedName);
      } else if (type === 'subsegment') {
        await updateSubSegmentName(rawId, trimmedName);
      }
      console.log('[handleTitleSave] API call successful');
      // Success - data already updated optimistically
    } catch (err) {
      console.error(`[handleTitleSave] Failed to update ${type} name:`, err);
      // Rollback on failure
      setTreeData(prev => updateNameInTree(prev, itemId, oldName));
    }
  }, [selectedItem]);

  // Render header content with InlineEditableTitle for Segment/Sub-Segment
  // and category badge matching Skill Taxonomy UI
  const renderHeaderContent = () => {
    if (!selectedItem) return null;
    
    const isEditable = selectedItem.type === 'segment' || selectedItem.type === 'subsegment';
    
    return (
      <>
        <div className="category-badge">{getTypeLabel(selectedItem.type)}</div>
        {isEditable ? (
          <InlineEditableTitle
            value={selectedItem.name}
            onSave={handleTitleSave}
            onDelete={handleDelete}
            onAddChild={null}
            addChildLabel={null}
            disabled={isDeleting}
          />
        ) : (
          <div className="details-title-row">
            <div className="details-title-left">
              <div className="details-title">{selectedItem.name}</div>
            </div>
          </div>
        )}
      </>
    );
  };

  // Render header action buttons (Download Template, Import, Add) matching Skill Taxonomy UI
  const renderHeaderActions = () => {
    if (!selectedItem) return null;
    
    // Determine child type based on current selection
    const getChildTypeLabel = () => {
      switch (selectedItem.type) {
        case 'segment': return 'Sub-Segment';
        case 'subsegment': return 'Project';
        case 'project': return 'Team';
        default: return null;
      }
    };
    
    const childType = getChildTypeLabel();
    
    
  };

  // Render details content based on selected item type
  const renderDetailsContent = () => {
    // Show loading state
    if (isLoading) {
      return <LoadingIndicator />;
    }
    
    // Show error state
    if (error) {
      return <ErrorState error={error} onRetry={loadHierarchy} />;
    }
    
    // Show empty state when no data or no selection
    if (!selectedItem) {
      // Check if hierarchy is empty
      if (treeData.length === 0) {
        return (
          <EmptyState
            onAddRoot={() => {
              setCreateType('segment');
              setCreateError(null);
              setCreateModalOpen(true);
            }}
            addButtonLabel="➕ Add New Segment"
          />
        );
      }
      return (
        <EmptyState
          onAddRoot={() => {
            setCreateType('segment');
            setCreateError(null);
            setCreateModalOpen(true);
          }}
          addButtonLabel="➕ Add New Segment"
        />
      );
    }

    // Segment details
    if (selectedItem.type === 'segment') {
      return (
        <>
          {/* Metadata */}
          <InfoSection title="Details">
            <InfoGrid>
              <InfoItem label="Name" value={selectedItem.name} />
              <InfoItem label="Type" value={getTypeLabel(selectedItem.type)} />
            </InfoGrid>
            {selectedItem.description && (
              <InfoBox style={{ marginTop: '12px' }}>
                <p style={{ color: 'var(--text-secondary)', fontSize: '14px', margin: 0 }}>
                  {selectedItem.description}
                </p>
              </InfoBox>
            )}
          </InfoSection>

          {/* Statistics */}
          <InfoSection title="Statistics">
            <StatsGrid>
              <StatCard label="Sub-Segments" value={selectedItem.subSegmentCount || 0} />
              <StatCard label="Projects" value={selectedItem.projectCount || 0} />
              <StatCard label="Teams" value={selectedItem.teamCount || 0} />
              <StatCard label="Employees" value={selectedItem.employeeCount || 0} />
            </StatsGrid>
          </InfoSection>

          {/* Audit Info */}
          <InfoSection title="Audit Trail">
            <InfoGrid>
              <InfoItem label="Created At" value={selectedItem.createdAt || '-'} />
              <InfoItem label="Created By" value={selectedItem.createdBy || '-'} />
            </InfoGrid>
            <button
              className="btn btn-ghost"
              style={{ marginTop: '12px', fontSize: '13px' }}
              onClick={handleViewAudit}
            >
              📋 View Full History
            </button>
          </InfoSection>

          {/* Warnings */}
          {selectedItem.employeeCount > 30 && (
            <Alert type="warning">
              This segment has {selectedItem.employeeCount} employees. Changes may affect many team members.
            </Alert>
          )}
        </>
      );
    }

    // Sub-Segment details + Projects table
    if (selectedItem.type === 'subsegment') {
      return (
        <>
          {/* Details */}
          <InfoSection title="Details">
            <InfoBox>
              <InfoItem label="Description" value={selectedItem.description || '-'} style={{ marginBottom: '16px' }} />
              <InfoItem label="Parent Segment" value={findItemById(treeData, selectedItem.parentId)?.name || '-'} />
            </InfoBox>
          </InfoSection>

          {/* Projects Table */}
          <OrgSubSegmentProjectsPanel
            projects={selectedItem.children || []}
            subSegmentName={selectedItem.name}
            onCreateProject={async (projectName) => {
              // Call API to create project using selectedItem.rawId as parent sub-segment
              try {
                await createProject(selectedItem.rawId, projectName);
                // Refresh hierarchy to show new project
                await loadHierarchy();
              } catch (err) {
                console.error('Failed to create project:', err);
                throw err; // Re-throw so the panel keeps add mode open
              }
            }}
            onEditProject={async (projectWithNewName) => {
              const { id, newName } = projectWithNewName;
              // Extract raw ID (remove prefix like 'project-')
              const rawId = typeof id === 'string' && id.includes('-') ? parseInt(id.split('-').pop(), 10) : id;
              
              try {
                await updateProjectName(rawId, newName);
                // Update tree data
                setTreeData(prev => {
                  const updateProjectInTree = (nodes) => {
                    return nodes.map(node => {
                      if (node.id === id) {
                        return { ...node, name: newName };
                      }
                      if (node.children) {
                        return { ...node, children: updateProjectInTree(node.children) };
                      }
                      return node;
                    });
                  };
                  return updateProjectInTree(prev);
                });
              } catch (err) {
                console.error('Failed to update project name:', err);
                throw err; // Re-throw so the panel keeps edit mode open
              }
            }}
            onDeleteProject={async (project) => {
              // Extract raw ID (remove prefix like 'project-')
              const rawId = typeof project.id === 'string' && project.id.includes('-') 
                ? parseInt(project.id.split('-').pop(), 10) 
                : project.id;
              
              try {
                // First check for dependencies
                const checkResult = await checkCanDeleteProject(rawId);
                if (!checkResult.canDelete) {
                  // Has dependencies - show warning
                  alert(`Cannot delete "${project.name}": it has ${checkResult.conflict.dependencies.teams} team(s). Delete the teams first.`);
                  return;
                }
                
                // No dependencies - delete
                await deleteProject(rawId);
                // Refresh hierarchy
                await loadHierarchy();
              } catch (err) {
                console.error('Failed to delete project:', err);
                alert('Failed to delete project');
              }
            }}
            onBulkDeleteProjects={async (projectsToDelete) => {
              try {
                // Delete each project in sequence
                for (const project of projectsToDelete) {
                  const rawId = typeof project.id === 'string' && project.id.includes('-') 
                    ? parseInt(project.id.split('-').pop(), 10) 
                    : project.id;
                  
                  // Check for dependencies first
                  const checkResult = await checkCanDeleteProject(rawId);
                  if (!checkResult.canDelete) {
                    // Skip this project - has dependencies
                    alert(`Cannot delete "${project.name}": it has ${checkResult.conflict.dependencies.teams} team(s). Skipping.`);
                    continue;
                  }
                  
                  await deleteProject(rawId);
                }
                // Refresh hierarchy
                await loadHierarchy();
              } catch (err) {
                console.error('Failed to bulk delete projects:', err);
                alert('Failed to delete some projects');
              }
            }}
          />
        </>
      );
    }

    // Project details + Teams table
    if (selectedItem.type === 'project') {
      return (
        <>
          {/* Details */}
          <InfoSection title="Details">
            <InfoBox>
              <InfoItem label="Description" value={selectedItem.description || '-'} style={{ marginBottom: '16px' }} />
              <InfoItem label="Parent Sub-Segment" value={findItemById(treeData, selectedItem.parentId)?.name || '-'} />
            </InfoBox>
          </InfoSection>

          {/* Teams Table */}
          <OrgProjectTeamsPanel
            teams={selectedItem.teams || []}
            projectName={selectedItem.name}
            onCreateTeam={async (teamName) => {
              // Call API to create team using selectedItem.rawId as parent project
              try {
                await createTeam(selectedItem.rawId, teamName);
                // Refresh hierarchy to show new team
                await loadHierarchy();
              } catch (err) {
                console.error('Failed to create team:', err);
                throw err; // Re-throw so the panel keeps add mode open
              }
            }}
            onEditTeam={async (teamWithNewName) => {
              const { id, newName } = teamWithNewName;
              // Extract raw ID (remove prefix like 'team-')
              const rawId = typeof id === 'string' && id.includes('-') ? parseInt(id.split('-').pop(), 10) : id;
              
              try {
                await updateTeamName(rawId, newName);
                // Update tree data - teams are nested within projects
                setTreeData(prev => {
                  const updateTeamInTree = (nodes) => {
                    return nodes.map(node => {
                      // Check if this node has teams (project node)
                      if (node.teams) {
                        return {
                          ...node,
                          teams: node.teams.map(team => 
                            team.id === id ? { ...team, name: newName } : team
                          )
                        };
                      }
                      // Recurse into children
                      if (node.children) {
                        return { ...node, children: updateTeamInTree(node.children) };
                      }
                      return node;
                    });
                  };
                  return updateTeamInTree(prev);
                });
              } catch (err) {
                console.error('Failed to update team name:', err);
                throw err; // Re-throw so the panel keeps edit mode open
              }
            }}
            onDeleteTeam={async (team) => {
              // Extract raw ID (remove prefix like 'team-')
              const rawId = typeof team.id === 'string' && team.id.includes('-') 
                ? parseInt(team.id.split('-').pop(), 10) 
                : team.id;
              
              try {
                await deleteTeam(rawId);
                // Refresh hierarchy
                await loadHierarchy();
              } catch (err) {
                console.error('Failed to delete team:', err);
                
                // Handle 409 Conflict - team has dependencies (employees assigned)
                if (err.status === 409 && err.data) {
                  const deps = err.data.dependencies || {};
                  const dependencyList = [];
                  if (deps.employees) {
                    dependencyList.push({ icon: '👥', label: `${deps.employees} Employee${deps.employees > 1 ? 's' : ''} assigned` });
                  }
                  setApiDependencies({
                    itemName: team.name,
                    dependencies: dependencyList
                  });
                  setDependencyModalOpen(true);
                  return;
                }
                
                alert('Failed to delete team');
              }
            }}
            onBulkDeleteTeams={async (teamsToDelete) => {
              const deletedTeams = [];
              let blockedTeam = null;
              
              try {
                // Delete each team in sequence
                for (const team of teamsToDelete) {
                  const rawId = typeof team.id === 'string' && team.id.includes('-') 
                    ? parseInt(team.id.split('-').pop(), 10) 
                    : team.id;
                  
                  try {
                    await deleteTeam(rawId);
                    deletedTeams.push(team);
                  } catch (err) {
                    // Handle 409 Conflict - team has dependencies
                    if (err.status === 409 && err.data) {
                      blockedTeam = { team, error: err };
                      break; // Stop on first blocked team
                    }
                    throw err; // Re-throw other errors
                  }
                }
                
                // Refresh hierarchy if any teams were deleted
                if (deletedTeams.length > 0) {
                  await loadHierarchy();
                }
                
                // If a team was blocked, show dependency modal
                if (blockedTeam) {
                  const deps = blockedTeam.error.data.dependencies || {};
                  const dependencyList = [];
                  if (deps.employees) {
                    dependencyList.push({ icon: '👥', label: `${deps.employees} Employee${deps.employees > 1 ? 's' : ''} assigned` });
                  }
                  setApiDependencies({
                    itemName: blockedTeam.team.name,
                    dependencies: dependencyList,
                    message: deletedTeams.length > 0 
                      ? `${deletedTeams.length} team${deletedTeams.length > 1 ? 's' : ''} deleted successfully, but "${blockedTeam.team.name}" could not be deleted.`
                      : null
                  });
                  setDependencyModalOpen(true);
                }
              } catch (err) {
                console.error('Failed to bulk delete teams:', err);
                alert('Failed to delete some teams');
              }
            }}
          />
        </>
      );
    }

    return null;
  };

  // Get parent options for create modal
  const getParentOptions = () => {
    if (createType === 'subsegment') {
      return treeData.map(s => ({ id: s.id, name: s.name }));
    } else if (createType === 'project') {
      return treeData.flatMap(seg => seg.children || []).map(s => ({ id: s.id, name: s.name }));
    } else if (createType === 'team') {
      return treeData.flatMap(seg => (seg.children || []).flatMap(sub => sub.children || [])).map(p => ({ id: p.id, name: p.name }));
    }
    return [];
  };

  return (
    <MasterDataLayout pageTitle="Organization Hierarchy">
      <>
        <TreePanel
          title="Organization Hierarchy"
          treeData={treeData}
          selectedNodeId={selectedNodeId}
          onNodeSelect={handleNodeSelect}
          renderNodeIcon={(node) => getTypeIcon(node.type)}
          getNodeChildren={(node) => node.children || []}
          searchPlaceholder="Search segments, projects, teams..."
          addRootLabel="+ Add Segment"
          onAddRoot={() => {
            setCreateType('segment');
            setCreateError(null);
            setCreateModalOpen(true);
          }}
        />
        
        <DetailsPanel
          title={selectedItem ? `${selectedItem.name}` : 'Details'}
          subtitle={null}
          headerContent={selectedItem ? renderHeaderContent() : null}
          headerActions={selectedItem ? renderHeaderActions() : null}
          showActions={false}
          onEdit={handleEdit}
          onDelete={handleDelete}
          onAddChild={null}
          addChildLabel={null}
        >
          {renderDetailsContent()}
        </DetailsPanel>
      </>

      {/* Modals */}
      <CreateEditModal
        isOpen={createModalOpen}
        onClose={() => {
          if (!isSaving) {
            setCreateModalOpen(false);
            setCreateError(null);
          }
        }}
        mode="create"
        itemType={createType}
        onSubmit={handleCreate}
        parentOptions={getParentOptions()}
        defaultParentId={selectedItem?.id}
        isSaving={isSaving}
        error={createError}
      />

      <CreateEditModal
        isOpen={editModalOpen}
        onClose={() => setEditModalOpen(false)}
        mode="edit"
        itemType={selectedItem?.type}
        initialData={selectedItem}
        onSubmit={handleUpdate}
      />

      <DeleteConfirmModal
        isOpen={deleteModalOpen}
        onClose={() => setDeleteModalOpen(false)}
        itemName={selectedItem?.name}
        itemType={getTypeLabel(selectedItem?.type)}
        onConfirm={handleConfirmDelete}
      />

      <DependencyModal
        isOpen={dependencyModalOpen}
        onClose={handleCloseDependencyModal}
        itemName={getDependencyItemName()}
        dependencies={getDependencies()}
      />

      <ImportModal
        isOpen={importModalOpen}
        onClose={() => setImportModalOpen(false)}
        itemType="Organization Units"
        onImport={handleImport}
      />

      <AuditModal
        isOpen={auditModalOpen}
        onClose={() => setAuditModalOpen(false)}
        itemName={selectedItem?.name}
      />
    </MasterDataLayout>
  );
};

export default OrgHierarchyPage;
