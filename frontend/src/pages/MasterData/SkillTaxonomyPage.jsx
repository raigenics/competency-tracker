/**
 * SkillTaxonomyPage - Master Data page for viewing Skill Taxonomy
 * Categories > SubCategories hierarchy (Skills shown in right panel table)
 * 
 * Updated per UIUpdates.html requirements:
 * - Tree shows only Category → Sub-Category (no skill nodes)
 * - Inline editable title for Category/Sub-Category names
 * - Skills table displayed when Sub-Category is selected
 * - Removed Edit button from action bar (inline edit handles it)
 */
import React, { useState, useMemo, useEffect, useCallback, useRef } from 'react';
import { Trash2, Search } from 'lucide-react';
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
  SkillsTable,
  ImportBlockingOverlay
} from './components';
import { 
  fetchSkillTaxonomy, 
  updateCategoryName, 
  updateSubcategoryName, 
  updateSkillName,
  createAlias,
  updateAliasText,
  deleteAlias,
  deleteCategory,
  deleteSubcategory,
  deleteSkill,
  createCategory,
  createSubcategory,
  createSkill,
  importSkills,
  getImportJobStatus
} from '../../services/api/masterDataApi';
import { API_BASE_URL } from '../../config/apiConfig';

// Loading delay threshold (ms) - only show loader after this time to prevent flicker
const LOADING_DELAY_MS = 500;

/**
 * Transform API response to tree structure (Category → SubCategory only, no skills in tree)
 * Skills are stored in skillsBySubcategory map for table display
 */
function transformApiResponse(apiResponse) {
  const treeData = [];
  const categoriesById = new Map();
  const subcategoriesById = new Map();
  const skillsBySubcategory = new Map(); // Map<subcategoryId, skill[]>

  for (const category of apiResponse.categories) {
    const categoryNode = {
      id: `cat-${category.id}`,
      rawId: category.id,
      type: 'category',
      name: category.name,
      description: category.description,
      createdAt: category.created_at ? formatDate(category.created_at) : null,
      createdBy: category.created_by,
      children: [], // Only subcategories, no skills
      subcategoryCount: category.subcategories.length,
      skillCount: 0,
      employeeCount: 0,
    };

    for (const subcategory of category.subcategories) {
      // Collect skills for this subcategory (for table display)
      const skills = subcategory.skills.map(skill => ({
        id: `skill-${skill.id}`,
        rawId: skill.id,
        type: 'skill',
        name: skill.name,
        description: skill.description,
        // Parse aliases from API response (array of {id, text, source, confidence_score})
        aliases: (skill.aliases || []).map(a => ({
          id: a.id,
          text: a.text,
          source: a.source,
          confidenceScore: a.confidence_score
        })),
        createdAt: skill.created_at ? formatDate(skill.created_at) : null,
        createdBy: skill.created_by,
        employeeCount: skill.employee_count,
      }));

      const subcategoryNode = {
        id: `subcat-${subcategory.id}`,
        rawId: subcategory.id,
        type: 'subcategory',
        name: subcategory.name,
        description: subcategory.description,
        parentId: categoryNode.id,
        categoryName: categoryNode.name, // For display
        createdAt: subcategory.created_at ? formatDate(subcategory.created_at) : null,
        createdBy: subcategory.created_by,
        children: [], // No children in tree - skills shown in table
        skillCount: skills.length,
        employeeCount: skills.reduce((sum, s) => sum + (s.employeeCount || 0), 0),
      };

      // Store skills in separate map for table display
      skillsBySubcategory.set(subcategoryNode.id, skills);

      categoryNode.children.push(subcategoryNode);
      categoryNode.skillCount += subcategoryNode.skillCount;
      categoryNode.employeeCount += subcategoryNode.employeeCount;
      subcategoriesById.set(subcategoryNode.id, subcategoryNode);
    }

    treeData.push(categoryNode);
    categoriesById.set(categoryNode.id, categoryNode);
  }

  return { treeData, categoriesById, subcategoriesById, skillsBySubcategory };
}

/**
 * Format ISO date string to user-friendly format
 */
function formatDate(isoString) {
  if (!isoString) return null;
  try {
    const date = new Date(isoString);
    return date.toLocaleDateString('en-US', { 
      year: 'numeric', 
      month: 'short', 
      day: 'numeric' 
    });
  } catch {
    return isoString;
  }
}

/**
 * Helper to find item by ID in nested structure
 */
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

/**
 * Get type icon for tree node
 */
const getTypeIcon = (type) => {
  switch (type) {
    case 'category': return '📁';
    case 'subcategory': return '📂';
    case 'skill': return '🏷️';
    default: return '📄';
  }
};

/**
 * Get type label for display
 */
const getTypeLabel = (type) => {
  switch (type) {
    case 'category': return 'Category';
    case 'subcategory': return 'Sub-Category';
    case 'skill': return 'Skill';
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
      Loading Category → Sub-Category → Skill, Please wait
    </div>
  </div>
);

/**
 * Error State Component
 */
const ErrorState = ({ error, onRetry }) => (
  <div className="error-container">
    <div className="error-icon">⚠️</div>
    <div className="error-title">Failed to Load Taxonomy</div>
    <div className="error-message">{error}</div>
    <button className="btn btn-primary" onClick={onRetry}>
      🔄 Retry
    </button>
  </div>
);

const SkillTaxonomyPage = () => {
  // Data state
  const [treeData, setTreeData] = useState([]);
  const [selectedNodeId, setSelectedNodeId] = useState(null);
  
  // Loading state with delay to prevent flicker
  const [isLoading, setIsLoading] = useState(true);
  const [showLoader, setShowLoader] = useState(false);
  const [error, setError] = useState(null);
  
  // Lookup maps for quick access
  const [lookupMaps, setLookupMaps] = useState({
    categoriesById: new Map(),
    subcategoriesById: new Map(),
    skillsBySubcategory: new Map(),
  });
  
  // Abort controller ref for cleanup
  const abortControllerRef = useRef(null);
  const loaderTimeoutRef = useRef(null);
  
  // Modal states
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [dependencyModalOpen, setDependencyModalOpen] = useState(false);
  const [importModalOpen, setImportModalOpen] = useState(false);
  const [auditModalOpen, setAuditModalOpen] = useState(false);
  const [createType, setCreateType] = useState('category');
  
  // Inline add skill state
  const [isAddingSkill, setIsAddingSkill] = useState(false);

  // Bulk selection state for skills table
  const [selectedSkillIds, setSelectedSkillIds] = useState(new Set());
  const [showBulkDeleteModal, setShowBulkDeleteModal] = useState(false);

  // Skill dependency info (for 409 conflict responses)
  const [skillDependencyInfo, setSkillDependencyInfo] = useState(null);

  // Skill search query (for filtering skills table)
  const [skillSearchQuery, setSkillSearchQuery] = useState('');

  // Import loading state
  const [isImporting, setIsImporting] = useState(false);

  // Import overlay state (for blocking UI during import)
  const [importOverlay, setImportOverlay] = useState({
    visible: false,
    message: 'Starting import...'
  });
  const importPollingRef = useRef(null);

  /**
   * Fetch taxonomy data from API
   */
  const loadTaxonomy = useCallback(async () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    
    if (loaderTimeoutRef.current) {
      clearTimeout(loaderTimeoutRef.current);
    }
    
    abortControllerRef.current = new AbortController();
    
    setIsLoading(true);
    setError(null);
    setShowLoader(false);
    
    loaderTimeoutRef.current = setTimeout(() => {
      setShowLoader(true);
    }, LOADING_DELAY_MS);
    
    try {
      const response = await fetchSkillTaxonomy({
        signal: abortControllerRef.current.signal,
      });
      
      const { treeData: newTreeData, categoriesById, subcategoriesById, skillsBySubcategory } = 
        transformApiResponse(response);
      
      setTreeData(newTreeData);
      setLookupMaps({ categoriesById, subcategoriesById, skillsBySubcategory });
      setError(null);
    } catch (err) {
      if (err.name === 'AbortError') {
        return;
      }
      console.error('Failed to load skill taxonomy:', err);
      setError(err.message || 'Failed to load skill taxonomy');
      setTreeData([]);
    } finally {
      if (loaderTimeoutRef.current) {
        clearTimeout(loaderTimeoutRef.current);
        loaderTimeoutRef.current = null;
      }
      setIsLoading(false);
      setShowLoader(false);
    }
  }, []);

  // Initial load
  useEffect(() => {
    loadTaxonomy();
    
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
      if (loaderTimeoutRef.current) {
        clearTimeout(loaderTimeoutRef.current);
      }
      // Cleanup import polling on unmount
      if (importPollingRef.current) {
        clearTimeout(importPollingRef.current);
      }
    };
  }, [loadTaxonomy]);

  // Get selected item
  const selectedItem = useMemo(() => {
    if (!selectedNodeId) return null;
    return findItemById(treeData, selectedNodeId);
  }, [selectedNodeId, treeData]);

  // Get skills for selected subcategory
  const selectedSubcategorySkills = useMemo(() => {
    if (!selectedItem || selectedItem.type !== 'subcategory') return [];
    return lookupMaps.skillsBySubcategory.get(selectedItem.id) || [];
  }, [selectedItem, lookupMaps.skillsBySubcategory]);

  // Filter skills by search query
  const filteredSkills = useMemo(() => {
    if (!skillSearchQuery.trim()) return selectedSubcategorySkills;
    const query = skillSearchQuery.toLowerCase();
    return selectedSubcategorySkills.filter(skill => {
      // Match skill name
      if (skill.name.toLowerCase().includes(query)) return true;
      // Match aliases (if any)
      if (skill.aliases && skill.aliases.some(alias => 
        alias.text && alias.text.toLowerCase().includes(query)
      )) return true;
      return false;
    });
  }, [selectedSubcategorySkills, skillSearchQuery]);

  // Handlers
  const handleNodeSelect = (nodeId) => {
    setSelectedNodeId(nodeId);
    // Clear skill selection when changing nodes
    setSelectedSkillIds(new Set());
    // Clear skill search when changing nodes
    setSkillSearchQuery('');
  };

  /**
   * Handle inline title save for Category/Sub-Category
   */
  const handleTitleSave = useCallback(async (newName) => {
    if (!selectedItem) return;
    
    const previousName = selectedItem.name;
    
    // Optimistic update - update local state immediately
    setTreeData(prevTree => {
      const updateNode = (nodes) => {
        return nodes.map(node => {
          if (node.id === selectedItem.id) {
            return { ...node, name: newName };
          }
          if (node.children) {
            return { ...node, children: updateNode(node.children) };
          }
          return node;
        });
      };
      return updateNode(prevTree);
    });
    
    try {
      // Call appropriate API based on item type
      if (selectedItem.type === 'category') {
        await updateCategoryName(selectedItem.rawId, newName);
      } else if (selectedItem.type === 'subcategory') {
        await updateSubcategoryName(selectedItem.rawId, newName);
      }
      setError(null);
    } catch (err) {
      // Revert optimistic update on failure
      setTreeData(prevTree => {
        const revertNode = (nodes) => {
          return nodes.map(node => {
            if (node.id === selectedItem.id) {
              return { ...node, name: previousName };
            }
            if (node.children) {
              return { ...node, children: revertNode(node.children) };
            }
            return node;
          });
        };
        return revertNode(prevTree);
      });
      
      // Display error message
      const message = err.data?.detail || err.message || 'Failed to update name';
      setError(message);
      console.error('Error updating name:', err);
    }
  }, [selectedItem]);

  /**
   * Handle skill inline edit save
   * Persists both skill name and alias changes via API
   */
  const handleSkillSave = useCallback(async (updatedSkill) => {
    if (!selectedItem || selectedItem.type !== 'subcategory') return;
    
    // Get current skill for comparison and potential rollback
    const currentSkills = lookupMaps.skillsBySubcategory.get(selectedItem.id) || [];
    const currentSkill = currentSkills.find(s => s.id === updatedSkill.id);
    
    // Extract removed alias IDs and new aliases
    const removedAliasIds = updatedSkill._removedAliasIds || [];
    const newAliases = (updatedSkill.aliases || []).filter(a => !a.id); // No ID = new
    
    // Clean skill object for state (remove internal fields)
    const cleanSkill = {
      ...updatedSkill,
      aliases: updatedSkill.aliases?.filter(a => a.id) || [] // Only keep existing aliases for now
    };
    delete cleanSkill._removedAliasIds;
    
    // Optimistic update - update local state immediately
    setLookupMaps(prev => {
      const newSkillsBySubcategory = new Map(prev.skillsBySubcategory);
      const skills = newSkillsBySubcategory.get(selectedItem.id) || [];
      const updatedSkills = skills.map(s => 
        s.id === updatedSkill.id ? cleanSkill : s
      );
      newSkillsBySubcategory.set(selectedItem.id, updatedSkills);
      
      return { ...prev, skillsBySubcategory: newSkillsBySubcategory };
    });
    
    try {
      const errors = [];
      
      // 1. Update skill name if changed
      if (currentSkill && currentSkill.name !== updatedSkill.name) {
        try {
          await updateSkillName(updatedSkill.rawId, updatedSkill.name);
        } catch (err) {
          errors.push(`Skill name: ${err.data?.detail || err.message}`);
        }
      }
      
      // 2. Delete removed aliases
      for (const aliasId of removedAliasIds) {
        try {
          await deleteAlias(aliasId);
        } catch (err) {
          errors.push(`Delete alias ${aliasId}: ${err.data?.detail || err.message}`);
        }
      }
      
      // 3. Create new aliases
      const createdAliases = [];
      for (const newAlias of newAliases) {
        try {
          const result = await createAlias(updatedSkill.rawId, newAlias.text);
          createdAliases.push({
            id: result.id,
            text: result.alias_text,
            source: result.source,
            confidenceScore: result.confidence_score
          });
        } catch (err) {
          errors.push(`Create alias '${newAlias.text}': ${err.data?.detail || err.message}`);
        }
      }
      
      // Update state with created aliases (now have IDs)
      if (createdAliases.length > 0) {
        setLookupMaps(prev => {
          const newSkillsBySubcategory = new Map(prev.skillsBySubcategory);
          const skills = newSkillsBySubcategory.get(selectedItem.id) || [];
          const updatedSkills = skills.map(s => {
            if (s.id === updatedSkill.id) {
              return {
                ...s,
                aliases: [...(s.aliases || []), ...createdAliases]
              };
            }
            return s;
          });
          newSkillsBySubcategory.set(selectedItem.id, updatedSkills);
          return { ...prev, skillsBySubcategory: newSkillsBySubcategory };
        });
      }
      
      if (errors.length > 0) {
        setError(errors.join('; '));
      } else {
        setError(null);
      }
    } catch (err) {
      // Revert optimistic update on failure
      setLookupMaps(prev => {
        const newSkillsBySubcategory = new Map(prev.skillsBySubcategory);
        const skills = newSkillsBySubcategory.get(selectedItem.id) || [];
        const revertedSkills = skills.map(s => 
          s.id === updatedSkill.id ? currentSkill : s
        );
        newSkillsBySubcategory.set(selectedItem.id, revertedSkills);
        
        return { ...prev, skillsBySubcategory: newSkillsBySubcategory };
      });
      
      const message = err.data?.detail || err.message || 'Failed to update skill';
      setError(message);
      console.error('Error updating skill:', err);
    }
  }, [selectedItem, lookupMaps.skillsBySubcategory]);

  /**
   * Handle skill delete - calls API to soft delete the skill
   */
  const handleSkillDelete = useCallback(async (skillToDelete) => {
    if (!selectedItem || selectedItem.type !== 'subcategory') return;
    
    try {
      // Call API to soft delete the skill (use rawId for numeric ID)
      await deleteSkill(skillToDelete.rawId);
      
      // Update local state only after successful API call
      setLookupMaps(prev => {
        const newSkillsBySubcategory = new Map(prev.skillsBySubcategory);
        const skills = newSkillsBySubcategory.get(selectedItem.id) || [];
        const filteredSkills = skills.filter(s => s.id !== skillToDelete.id);
        newSkillsBySubcategory.set(selectedItem.id, filteredSkills);
        
        return { ...prev, skillsBySubcategory: newSkillsBySubcategory };
      });
      
      // Update skill count in tree
      setTreeData(prevTree => {
        const updateCounts = (nodes) => {
          return nodes.map(node => {
            if (node.id === selectedItem.id) {
              return { ...node, skillCount: node.skillCount - 1 };
            }
            if (node.id === selectedItem.parentId) {
              return { 
                ...node, 
                skillCount: node.skillCount - 1,
                children: updateCounts(node.children)
              };
            }
            if (node.children) {
              return { ...node, children: updateCounts(node.children) };
            }
            return node;
          });
        };
        return updateCounts(prevTree);
      });
      
      setError(null);
    } catch (err) {
      // Handle 409 Conflict - skill has dependencies (employees have this skill)
      if (err.status === 409 && err.data) {
        const deps = err.data.dependencies || {};
        const dependencyList = [];
        if (deps.employee_skills) {
          dependencyList.push({ icon: '👥', label: `${deps.employee_skills} Employee${deps.employee_skills > 1 ? 's' : ''} have this skill assigned` });
        }
        setSkillDependencyInfo({
          itemName: skillToDelete.name,
          dependencies: dependencyList
        });
        setDependencyModalOpen(true);
        return;
      }
      
      const message = err.data?.detail || err.message || 'Failed to delete skill';
      setError(message);
      console.error('Error deleting skill:', err);
    }
  }, [selectedItem]);

  const handleDelete = () => {
    if (selectedItem?.children?.length > 0 || selectedItem?.employeeCount > 0 || 
        (selectedItem?.type === 'subcategory' && selectedSubcategorySkills.length > 0)) {
      setDependencyModalOpen(true);
    } else {
      setDeleteModalOpen(true);
    }
  };

  const handleAddChild = () => {
    if (selectedItem?.type === 'category') {
      setCreateType('subcategory');
      setCreateModalOpen(true);
    } else if (selectedItem?.type === 'subcategory') {
      // For skills, use inline add instead of modal
      setIsAddingSkill(true);
    } else {
      setCreateType('category');
      setCreateModalOpen(true);
    }
  };

  /**
   * Handle inline add skill - start adding
   */
  const handleStartAddSkill = useCallback(() => {
    setIsAddingSkill(true);
  }, []);

  /**
   * Handle inline add skill - complete (save via API)
   */
  const handleAddSkillComplete = useCallback(async (newSkillData) => {
    if (!selectedItem || selectedItem.type !== 'subcategory') return;
    
    try {
// Join all aliases as comma-separated string for API
      const aliasText = newSkillData.aliases?.map(a => a.text).join(', ') || null;
      
      // Call API to create skill
      const response = await createSkill(
        selectedItem.rawId,
        newSkillData.name,
        aliasText
      );
      
      // Transform API response to match our skill object structure
      const createdSkill = {
        id: `skill-${response.id}`,
        rawId: response.id,
        type: 'skill',
        name: response.name,
        aliases: response.aliases?.map(a => ({ id: a.id, text: a.alias_text })) || [],
        createdAt: response.created_at 
          ? new Date(response.created_at).toLocaleDateString('en-US', { 
              year: 'numeric', 
              month: 'short', 
              day: 'numeric' 
            })
          : null,
        createdBy: response.created_by,
        employeeCount: 0
      };
      
      // Add to local state (insert at top)
      setLookupMaps(prev => {
        const newSkillsBySubcategory = new Map(prev.skillsBySubcategory);
        const currentSkills = newSkillsBySubcategory.get(selectedItem.id) || [];
        newSkillsBySubcategory.set(selectedItem.id, [createdSkill, ...currentSkills]);
        return { ...prev, skillsBySubcategory: newSkillsBySubcategory };
      });
      
      // Update skill count in tree
      setTreeData(prevTree => {
        const updateCounts = (nodes) => {
          return nodes.map(node => {
            if (node.id === selectedItem.id) {
              return { ...node, skillCount: node.skillCount + 1 };
            }
            if (node.id === selectedItem.parentId) {
              return { 
                ...node, 
                skillCount: node.skillCount + 1,
                children: updateCounts(node.children)
              };
            }
            if (node.children) {
              return { ...node, children: updateCounts(node.children) };
            }
            return node;
          });
        };
        return updateCounts(prevTree);
      });
      
      setIsAddingSkill(false);
      setError(null);
    } catch (err) {
      console.error('Failed to create skill:', err);
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to create skill';
      setError(errorMessage);
      // Keep the add row open so user can retry
    }
  }, [selectedItem]);

  /**
   * Handle inline add skill - cancel
   */
  const handleAddSkillCancel = useCallback(() => {
    setIsAddingSkill(false);
  }, []);

  /**
   * Handle bulk selection change
   */
  const handleSelectedSkillIdsChange = useCallback((newSelection) => {
    setSelectedSkillIds(newSelection);
  }, []);

  /**
   * Handle header trash icon click - open bulk delete modal
   */
  const handleHeaderBulkDeleteClick = useCallback(() => {
    if (selectedSkillIds.size > 0) {
      setShowBulkDeleteModal(true);
    }
  }, [selectedSkillIds.size]);

  /**
   * Handle closing bulk delete modal from external trigger
   */
  const handleCloseBulkDeleteModal = useCallback(() => {
    setShowBulkDeleteModal(false);
  }, []);

  /**
   * Handle bulk delete - delete multiple skills at once
   */
  const handleBulkSkillDelete = useCallback(async (skillsToDelete) => {
    if (!selectedItem || selectedItem.type !== 'subcategory') return;
    
    const deletedSkills = [];
    let blockedSkill = null;
    
    try {
      // Delete all selected skills via API (sequentially to avoid race conditions)
      for (const skill of skillsToDelete) {
        try {
          await deleteSkill(skill.rawId);
          deletedSkills.push(skill);
        } catch (err) {
          // Handle 409 Conflict - skill has dependencies
          if (err.status === 409 && err.data) {
            blockedSkill = { skill, error: err };
            break; // Stop on first blocked skill
          }
          throw err; // Re-throw other errors
        }
      }
      
      // Update local state with successfully deleted skills
      if (deletedSkills.length > 0) {
        const deletedIds = new Set(deletedSkills.map(s => s.id));
        
        setLookupMaps(prev => {
          const newSkillsBySubcategory = new Map(prev.skillsBySubcategory);
          const skills = newSkillsBySubcategory.get(selectedItem.id) || [];
          const filteredSkills = skills.filter(s => !deletedIds.has(s.id));
          newSkillsBySubcategory.set(selectedItem.id, filteredSkills);
          
          return { ...prev, skillsBySubcategory: newSkillsBySubcategory };
        });
        
        // Update skill count in tree
        const deleteCount = deletedSkills.length;
        setTreeData(prevTree => {
          const updateCounts = (nodes) => {
            return nodes.map(node => {
              if (node.id === selectedItem.id) {
                return { ...node, skillCount: Math.max(0, node.skillCount - deleteCount) };
              }
              if (node.id === selectedItem.parentId) {
                return { 
                  ...node, 
                  skillCount: Math.max(0, node.skillCount - deleteCount),
                  children: updateCounts(node.children)
                };
              }
              if (node.children) {
                return { ...node, children: updateCounts(node.children) };
              }
              return node;
            });
          };
          return updateCounts(prevTree);
        });
      }
      
      // Clear selection
      setSelectedSkillIds(new Set());
      setShowBulkDeleteModal(false);
      setError(null);
      
      // If a skill was blocked, show dependency modal
      if (blockedSkill) {
        const deps = blockedSkill.error.data.dependencies || {};
        const dependencyList = [];
        if (deps.employee_skills) {
          dependencyList.push({ icon: '👥', label: `${deps.employee_skills} Employee${deps.employee_skills > 1 ? 's' : ''} have this skill assigned` });
        }
        setSkillDependencyInfo({
          itemName: blockedSkill.skill.name,
          dependencies: dependencyList,
          message: deletedSkills.length > 0 
            ? `${deletedSkills.length} skill${deletedSkills.length > 1 ? 's' : ''} deleted successfully, but "${blockedSkill.skill.name}" could not be deleted.`
            : null
        });
        setDependencyModalOpen(true);
      }
    } catch (err) {
      const message = err.data?.detail || err.message || 'Failed to delete skills';
      setError(message);
      console.error('Error deleting skills:', err);
    }
  }, [selectedItem]);

  /**
   * Handle create for Category or Subcategory
   */
  const handleCreate = async (formData) => {
    const { name } = formData;
    
    try {
      if (createType === 'category') {
        // Create category via API
        const response = await createCategory(name);
        
        // Create new category node for tree
        const newCategoryNode = {
          id: `cat-${response.id}`,
          rawId: response.id,
          type: 'category',
          name: response.name,
          description: null,
          createdAt: response.created_at ? formatDate(response.created_at) : null,
          createdBy: response.created_by,
          children: [],
          subcategoryCount: 0,
          skillCount: 0,
          employeeCount: 0,
        };
        
        // Update tree data - insert sorted by name
        setTreeData(prevTree => {
          const updatedTree = [...prevTree, newCategoryNode];
          return updatedTree.sort((a, b) => a.name.localeCompare(b.name));
        });
        
        // Update lookup maps
        setLookupMaps(prev => {
          const newCategoriesById = new Map(prev.categoriesById);
          newCategoriesById.set(newCategoryNode.id, newCategoryNode);
          return { ...prev, categoriesById: newCategoriesById };
        });
        
        // Auto-select the new category
        setSelectedNodeId(newCategoryNode.id);
        setError(null);
        
      } else if (createType === 'subcategory' && selectedItem?.type === 'category') {
        // Create subcategory via API
        const response = await createSubcategory(selectedItem.rawId, name);
        
        // Create new subcategory node
        const newSubcategoryNode = {
          id: `subcat-${response.id}`,
          rawId: response.id,
          type: 'subcategory',
          name: response.name,
          description: null,
          parentId: selectedItem.id,
          categoryName: selectedItem.name,
          createdAt: response.created_at ? formatDate(response.created_at) : null,
          createdBy: response.created_by,
          children: [],
          skillCount: 0,
          employeeCount: 0,
        };
        
        // Update tree data - add to parent category's children sorted by name
        setTreeData(prevTree => {
          return prevTree.map(category => {
            if (category.id === selectedItem.id) {
              const updatedChildren = [...category.children, newSubcategoryNode];
              updatedChildren.sort((a, b) => a.name.localeCompare(b.name));
              return {
                ...category,
                children: updatedChildren,
                subcategoryCount: category.subcategoryCount + 1,
              };
            }
            return category;
          });
        });
        
        // Update lookup maps
        setLookupMaps(prev => {
          const newSubcategoriesById = new Map(prev.subcategoriesById);
          const newSkillsBySubcategory = new Map(prev.skillsBySubcategory);
          newSubcategoriesById.set(newSubcategoryNode.id, newSubcategoryNode);
          newSkillsBySubcategory.set(newSubcategoryNode.id, []); // Empty skills array
          return { 
            ...prev, 
            subcategoriesById: newSubcategoriesById,
            skillsBySubcategory: newSkillsBySubcategory,
          };
        });
        
        // Auto-select the new subcategory
        setSelectedNodeId(newSubcategoryNode.id);
        setError(null);
        
      } else if (createType === 'skill') {
        // Skill creation - not implemented yet
        console.log('Skill creation not implemented yet');
      }
      
    } catch (err) {
      const message = err.data?.detail || err.message || `Failed to create ${createType}`;
      setError(message);
      console.error(`Error creating ${createType}:`, err);
    } finally {
      setCreateModalOpen(false);
    }
  };

  const handleConfirmDelete = async () => {
    if (!selectedItem) return;
    
    // Capture parent info before delete for subcategory navigation
    const parentId = selectedItem.parentId;
    const deletedNodeId = selectedItem.id;
    const deletedType = selectedItem.type;
    const deletedSkillCount = selectedItem.skillCount || 0;
    const deletedEmployeeCount = selectedItem.employeeCount || 0;
    
    try {
      if (deletedType === 'category') {
        await deleteCategory(selectedItem.rawId);
        
        // Remove category from treeData
        setTreeData(prevTree => prevTree.filter(node => node.id !== deletedNodeId));
        
        // Remove from lookupMaps
        setLookupMaps(prev => {
          const newCategoriesById = new Map(prev.categoriesById);
          newCategoriesById.delete(deletedNodeId);
          return { ...prev, categoriesById: newCategoriesById };
        });
        
        // Clear selection
        setSelectedNodeId(null);
        
      } else if (deletedType === 'subcategory') {
        await deleteSubcategory(selectedItem.rawId);
        
        // Remove subcategory from parent's children and update parent counts
        setTreeData(prevTree => {
          return prevTree.map(category => {
            if (category.id === parentId) {
              return {
                ...category,
                children: category.children.filter(child => child.id !== deletedNodeId),
                subcategoryCount: category.subcategoryCount - 1,
                skillCount: category.skillCount - deletedSkillCount,
                employeeCount: category.employeeCount - deletedEmployeeCount,
              };
            }
            return category;
          });
        });
        
        // Remove from lookupMaps
        setLookupMaps(prev => {
          const newSubcategoriesById = new Map(prev.subcategoriesById);
          const newSkillsBySubcategory = new Map(prev.skillsBySubcategory);
          newSubcategoriesById.delete(deletedNodeId);
          newSkillsBySubcategory.delete(deletedNodeId);
          return { 
            ...prev, 
            subcategoriesById: newSubcategoriesById,
            skillsBySubcategory: newSkillsBySubcategory,
          };
        });
        
        // Navigate selection to parent category
        setSelectedNodeId(parentId);
        
      } else {
        // Skill delete - not implemented yet
        console.log('Skill delete not implemented yet');
        setDeleteModalOpen(false);
        return;
      }
      
    } catch (error) {
      console.error('Delete failed:', error);
      // Handle error (could show a toast/notification)
    } finally {
      setDeleteModalOpen(false);
    }
  };

  const handleViewAudit = () => {
    setAuditModalOpen(true);
  };

  // Get dependencies for modal
  const getDependencies = () => {
    // If we have skill-specific dependency info from 409 response, use that
    if (skillDependencyInfo?.dependencies) {
      return skillDependencyInfo.dependencies;
    }
    
    if (!selectedItem) return [];
    const deps = [];
    if (selectedItem.subcategoryCount) {
      deps.push({ icon: '📂', label: `${selectedItem.subcategoryCount} Sub-Categories` });
    }
    if (selectedItem.type === 'subcategory' && selectedSubcategorySkills.length > 0) {
      deps.push({ icon: '🏷️', label: `${selectedSubcategorySkills.length} Skills` });
    } else if (selectedItem.skillCount) {
      deps.push({ icon: '🏷️', label: `${selectedItem.skillCount} Skills` });
    }
    if (selectedItem.employeeCount) {
      deps.push({ icon: '👥', label: `${selectedItem.employeeCount} Employees` });
    }
    return deps;
  };

  // Get item name for dependency modal
  const getDependencyItemName = () => {
    if (skillDependencyInfo?.itemName) {
      return skillDependencyInfo.itemName;
    }
    return selectedItem?.name;
  };

  // Handle closing dependency modal
  const handleCloseDependencyModal = () => {
    setDependencyModalOpen(false);
    setSkillDependencyInfo(null);
  };

  // Determine what child type can be added
  const getChildType = () => {
    if (!selectedItem) return null;
    if (selectedItem.type === 'category') return 'Sub-Category';
    if (selectedItem.type === 'subcategory') return 'Skill';
    return null;
  };

  // Render header content with InlineEditableTitle
  const renderHeaderContent = () => {
    if (!selectedItem) return null;
    
    return (
      <>
        <div className="category-badge">{getTypeLabel(selectedItem.type)}</div>
        <InlineEditableTitle
          value={selectedItem.name}
          onSave={handleTitleSave}
          onDelete={handleDelete}
          onAddChild={null}
          addChildLabel={null}
        />
      </>
    );
  };

  // Render header action buttons (Download Template, Import, Add)
  // Download Template and Import Skills are ALWAYS visible
  // + Add Sub-Category only appears when a Category is selected
  const renderHeaderActions = () => {
    // Get backend base URL (without /api suffix) for static file access
    const backendBaseUrl = API_BASE_URL.replace(/\/api$/, '');
    const templateUrl = `${backendBaseUrl}/static/templates/SkillMasterData_Template.xlsx`;
    
    return (
      <>
        <a 
          className="btn btn-secondary" 
          href={templateUrl}
          download="SkillMasterData_Template.xlsx"
          title="Download Excel template to add skills in bulk"
          style={{ textDecoration: 'none' }}
        >
          📥 Download Template
        </a>
        <button 
          className="btn btn-outline" 
          onClick={() => setImportModalOpen(true)}
          title="Upload completed template to import skills"
          disabled={isImporting}
        >
          {isImporting ? '⏳ Importing...' : '📤 Import Skills'}
        </button>
        {selectedItem?.type === 'category' && (
          <button 
            className="btn btn-primary" 
            onClick={handleAddChild}
          >
            + Add Sub-Category
          </button>
        )}
      </>
    );
  };

  // Render details content based on selected item type
  const renderDetailsContent = () => {
    if (isLoading && showLoader) {
      return <LoadingIndicator />;
    }
    
    if (error) {
      return <ErrorState error={error} onRetry={loadTaxonomy} />;
    }
    
    if (!selectedItem) {
      return (
        <EmptyState
          onAddRoot={() => {
            setCreateType('category');
            setCreateModalOpen(true);
          }}
          addButtonLabel="➕ Add New Category"
        />
      );
    }

    // Category details
    if (selectedItem.type === 'category') {
      return (
        <>
          <InfoSection title="Details">
            <InfoBox>
              <InfoItem label="Description" value={selectedItem.description || '-'} style={{ marginBottom: '16px' }} />
            </InfoBox>
          </InfoSection>

          <InfoSection title="Statistics">
            <StatsGrid>
              <StatCard label="Sub-Categories" value={selectedItem.subcategoryCount || 0} />
              <StatCard label="Total Skills" value={selectedItem.skillCount || 0} />
            </StatsGrid>
          </InfoSection>

          <InfoSection title="Audit Information">
            <InfoBox>
              <InfoGrid>
                <InfoItem label="Created" value={selectedItem.createdAt || '-'} />
                <InfoItem label="Created By" value={selectedItem.createdBy || '-'} />
              </InfoGrid>
            </InfoBox>
          </InfoSection>
        </>
      );
    }

    // Sub-Category details + Skills table
    if (selectedItem.type === 'subcategory') {
      return (
        <>
          <InfoSection title="Details">
            <InfoBox>
              <InfoItem label="Description" value={selectedItem.description || '-'} style={{ marginBottom: '16px' }} />
              <InfoItem label="Parent Category" value={selectedItem.categoryName || '-'} />
            </InfoBox>
          </InfoSection>

          <InfoSection 
            title="Skills in this Sub-Category"
            action={
              <div style={{ display: 'flex', gap: '8px', alignItems: 'center', marginBottom: '8px' }}>
                {/* Search box - only show if skills exist */}
                {selectedSubcategorySkills.length > 0 && (
                  <div className="search-box" style={{ position: 'relative' }}>
                    <Search 
                      size={16} 
                      style={{ 
                        position: 'absolute', 
                        left: '12px', 
                        top: '50%', 
                        transform: 'translateY(-50%)', 
                        color: 'var(--text-muted)' 
                      }} 
                    />
                    <input
                      type="text"
                      placeholder="Search skills..."
                      value={skillSearchQuery}
                      onChange={(e) => setSkillSearchQuery(e.target.value)}
                      style={{
                        width: '200px',
                        padding: '8px 12px 8px 36px',
                        border: '1px solid var(--border)',
                        borderRadius: '6px',
                        fontSize: '13px',
                        fontFamily: 'inherit'
                      }}
                    />
                  </div>
                )}
                {selectedSkillIds.size > 0 && (
                  <button 
                    className="btn btn-danger btn-sm"
                    onClick={handleHeaderBulkDeleteClick}
                    title={`Delete ${selectedSkillIds.size} selected skill(s)`}
                  >
                    <Trash2 size={14} />
                  </button>
                )}
                <button 
                  className="btn btn-primary btn-sm" 
                  onClick={handleStartAddSkill}
                  disabled={isAddingSkill}
                >
                  {isAddingSkill ? 'Adding...' : '+ Add Skill'}
                </button>
              </div>
            }
          >
            <SkillsTable
              skills={filteredSkills}
              onSkillSave={handleSkillSave}
              onSkillDelete={handleSkillDelete}
              onBulkDelete={handleBulkSkillDelete}
              onAddSkill={handleStartAddSkill}
              isAddingSkill={isAddingSkill}
              onAddSkillComplete={handleAddSkillComplete}
              onAddSkillCancel={handleAddSkillCancel}
              selectedSkillIds={selectedSkillIds}
              onSelectedSkillIdsChange={handleSelectedSkillIdsChange}
              showBulkDeleteModal={showBulkDeleteModal}
              onCloseBulkDeleteModal={handleCloseBulkDeleteModal}
            />
          </InfoSection>
        </>
      );
    }

    return null;
  };

  return (
    <MasterDataLayout pageTitle="Skill Taxonomy">
      <>
        <TreePanel
          title="Skill Taxonomy"
          treeData={treeData}
          selectedNodeId={selectedNodeId}
          onNodeSelect={handleNodeSelect}
          renderNodeIcon={(node) => getTypeIcon(node.type)}
          getNodeChildren={(node) => node.children || []}
          searchPlaceholder="Search categories..."
          onAddRoot={() => {
            setCreateType('category');
            setCreateModalOpen(true);
          }}
          addRootLabel="+ Category"
          isLoading={isLoading && showLoader}
          loadingContent={<LoadingIndicator />}
          errorContent={error ? <ErrorState error={error} onRetry={loadTaxonomy} /> : null}
        />
        
        <DetailsPanel
          title={selectedItem ? `${selectedItem.name}` : 'Skill Taxonomy'}
          subtitle={null}
          headerContent={selectedItem ? renderHeaderContent() : null}
          headerActions={renderHeaderActions()}
          showActions={false}
        >
          {renderDetailsContent()}
        </DetailsPanel>
      </>

      {/* Modals */}
      <CreateEditModal
        isOpen={createModalOpen}
        onClose={() => setCreateModalOpen(false)}
        mode="create"
        itemType={createType}
        onSubmit={handleCreate}
        parentOptions={createType === 'subcategory' ? treeData.map(c => ({ id: c.id, name: c.name })) : 
                       createType === 'skill' ? Array.from(lookupMaps.subcategoriesById.values()).map(s => ({ id: s.id, name: s.name })) : 
                       []}
        defaultParentId={selectedItem?.id}
      />

      <DeleteConfirmModal
        isOpen={deleteModalOpen}
        onClose={() => setDeleteModalOpen(false)}
        itemName={selectedItem?.name}
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
        itemType="Skills"
        onImport={async (data) => {
          if (data.type !== 'file' || !data.file) {
            window.alert('Please select an Excel file to import.');
            return;
          }
          
          setImportModalOpen(false);
          setIsImporting(true);
          
          try {
            // Start import - returns job_id immediately
            const response = await importSkills(data.file);
            const jobId = response.job_id;
            
            if (!jobId) {
              throw new Error('No job ID returned from import');
            }
            
            // Show blocking overlay
            setImportOverlay({
              visible: true,
              message: 'Starting import...'
            });
            
            // Polling logic with exponential backoff on errors
            let pollInterval = 2000;
            let consecutiveErrors = 0;
            const maxErrors = 5;
            
            const pollStatus = async () => {
              try {
                const status = await getImportJobStatus(jobId);
                consecutiveErrors = 0;
                pollInterval = 2000; // Reset on success
                
                // Handle 503 "unavailable" response (DB busy but import still running)
                if (status.status === 'unavailable') {
                  // Keep polling - this is a transient DB issue, NOT an error
                  setImportOverlay(prev => ({
                    ...prev,
                    message: status.message || 'Still working... database busy'
                  }));
                  // Don't increment errors, keep polling
                  importPollingRef.current = setTimeout(pollStatus, 3000);
                  return;
                }
                
                // Update overlay
                setImportOverlay({
                  visible: true,
                  message: status.message || 'Processing...'
                });
                
                // Check completion
                if (status.status === 'completed') {
                  // Stop polling
                  if (importPollingRef.current) {
                    clearTimeout(importPollingRef.current);
                    importPollingRef.current = null;
                  }
                  
                  // Hide overlay
                  setImportOverlay({ visible: false, message: '' });
                  setIsImporting(false);
                  
                  // Build success message from result
                  const result = status.result || {};
                  const summary = result.summary || {};
                  let message = `Import completed!\n\n`;
                  message += `Categories: ${summary.categories?.inserted || 0} new, ${summary.categories?.existing || 0} existing\n`;
                  message += `Sub-Categories: ${summary.subcategories?.inserted || 0} new, ${summary.subcategories?.existing || 0} existing\n`;
                  message += `Skills: ${summary.skills?.inserted || 0} new, ${summary.skills?.existing || 0} existing\n`;
                  message += `Aliases: ${summary.aliases?.inserted || 0} new, ${summary.aliases?.existing || 0} existing`;
                  
                  if (result.errors_count > 0) {
                    message += `\n\n⚠️ ${result.errors_count} conflict(s) detected. Check data for duplicates.`;
                  }
                  
                  window.alert(message);
                  loadTaxonomy();
                  return;
                }
                
                if (status.status === 'failed') {
                  // Stop polling
                  if (importPollingRef.current) {
                    clearTimeout(importPollingRef.current);
                    importPollingRef.current = null;
                  }
                  
                  // Hide overlay
                  setImportOverlay({ visible: false, message: '' });
                  setIsImporting(false);
                  
                  window.alert(`❌ Import Failed:\n${status.error || status.message || 'Unknown error'}`);
                  return;
                }
                
                // Continue polling
                importPollingRef.current = setTimeout(pollStatus, pollInterval);
                
              } catch (err) {
                // Check if this is a 503 (transient DB busy) - don't count as error
                const is503 = err?.message?.includes('503') || err?.status === 503;
                
                if (is503) {
                  // Transient DB issue - keep polling without incrementing error count
                  setImportOverlay(prev => ({
                    ...prev,
                    message: 'Still working... database busy, checking status'
                  }));
                  // Retry after short delay
                  importPollingRef.current = setTimeout(pollStatus, 3000);
                  return;
                }
                
                consecutiveErrors++;
                
                // Update overlay with reconnect message
                setImportOverlay(prev => ({
                  ...prev,
                  message: 'Still working... attempting to reconnect'
                }));
                
                if (consecutiveErrors >= maxErrors) {
                  // Stop polling after too many errors
                  if (importPollingRef.current) {
                    clearTimeout(importPollingRef.current);
                    importPollingRef.current = null;
                  }
                  setImportOverlay({ visible: false, message: '' });
                  setIsImporting(false);
                  window.alert('❌ Lost connection to import job. Please check the data and try again.');
                  return;
                }
                
                // Exponential backoff: 2s -> 4s -> 6s -> 8s -> 10s (capped)
                pollInterval = Math.min(pollInterval + 2000, 10000);
                importPollingRef.current = setTimeout(pollStatus, pollInterval);
              }
            };
            
            // Start polling
            importPollingRef.current = setTimeout(pollStatus, pollInterval);
            
          } catch (err) {
            setImportOverlay({ visible: false, message: '' });
            setIsImporting(false);
            const errorMsg = err?.message || err?.detail || 'Import failed. Please check the file format.';
            window.alert(`❌ Import Error:\n${errorMsg}`);
          }
        }}
      />

      {/* Import blocking overlay */}
      <ImportBlockingOverlay
        isVisible={importOverlay.visible}
        message={importOverlay.message}
        title="Import in progress"
      />

      <AuditModal
        isOpen={auditModalOpen}
        onClose={() => setAuditModalOpen(false)}
        itemName={selectedItem?.name}
      />
    </MasterDataLayout>
  );
};

export default SkillTaxonomyPage;
