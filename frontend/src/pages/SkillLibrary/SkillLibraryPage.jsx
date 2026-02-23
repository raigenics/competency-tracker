/**
 * SkillLibraryPage - Governance page for managing Skill Library
 * 
 * This page maintains the custom layout/CSS from the HTML wireframe but
 * uses the real API and reuses inline edit components from MasterData.
 * 
 * Features:
 * - Tree view (Categories → Sub-categories)
 * - Right panel with 3 states: Empty, Category selected, Sub-category selected
 * - Tree and list search functionality
 * - Full CRUD operations with inline add/edit behaviors
 * - Real API integration (no dummy data)
 */
import React, { useState, useMemo, useEffect, useCallback, useRef } from 'react';
import { Search } from 'lucide-react';
import './skillLibrary.css';

// Import API functions
import {
  fetchSkillTaxonomy,
  createCategory,
  updateCategoryName,
  deleteCategory,
  createSubcategory,
  updateSubcategoryName,
  deleteSubcategory,
  createSkill,
  updateSkillName,
  deleteSkill,
  createAlias,
  deleteAlias,
  importSkills,
  getImportJobStatus
} from '../../services/api/masterDataApi';

// Import MasterData components for inline behaviors and modals
import {
  CreateEditModal,
  DeleteConfirmModal,
  DependencyModal,
  ImportModal,
  ImportBlockingOverlay,
  TaxonomyCategorySubCategoriesPanel,
  SkillsTable
} from '../MasterData/components';

import { API_BASE_URL } from '../../config/apiConfig';

// Loading delay threshold (ms) - only show loader after this time to prevent flicker
const LOADING_DELAY_MS = 300;

// ─────────────────────────────────────────────────────────────────────────────
// HELPER FUNCTIONS
// ─────────────────────────────────────────────────────────────────────────────

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
 * Transform API response to UI-friendly structure
 */
function transformApiResponse(apiResponse) {
  const categories = [];
  const categoriesById = new Map();
  const subcategoriesById = new Map();
  const skillsBySubcategory = new Map();

  for (const category of apiResponse.categories) {
    const categoryNode = {
      id: `cat-${category.id}`,
      rawId: category.id,
      type: 'category',
      name: category.name,
      description: category.description || 'No description provided.',
      createdAt: category.created_at ? formatDate(category.created_at) : null,
      createdBy: category.created_by,
      subcategories: [],
      subcategoryCount: category.subcategories.length,
      skillCount: 0,
      employeeCount: 0,
    };

    for (const subcategory of category.subcategories) {
      // Transform skills
      const skills = subcategory.skills.map(skill => ({
        id: `skill-${skill.id}`,
        rawId: skill.id,
        type: 'skill',
        name: skill.name,
        description: skill.description,
        aliases: (skill.aliases || []).map(a => ({
          id: a.id,
          text: a.text,
          source: a.source,
          confidenceScore: a.confidence_score
        })),
        createdAt: skill.created_at ? formatDate(skill.created_at) : null,
        createdBy: skill.created_by,
        employeeCount: skill.employee_count || 0,
      }));

      const subcategoryNode = {
        id: `subcat-${subcategory.id}`,
        rawId: subcategory.id,
        type: 'subcategory',
        name: subcategory.name,
        description: subcategory.description,
        parentId: categoryNode.id,
        categoryId: categoryNode.id,
        categoryRawId: category.id,
        categoryName: categoryNode.name,
        createdAt: subcategory.created_at ? formatDate(subcategory.created_at) : null,
        createdBy: subcategory.created_by,
        skillCount: skills.length,
        employeeCount: skills.reduce((sum, s) => sum + (s.employeeCount || 0), 0),
      };

      // Store skills in map for table display
      skillsBySubcategory.set(subcategoryNode.id, skills);

      categoryNode.subcategories.push(subcategoryNode);
      categoryNode.skillCount += subcategoryNode.skillCount;
      categoryNode.employeeCount += subcategoryNode.employeeCount;
      subcategoriesById.set(subcategoryNode.id, subcategoryNode);
    }

    categories.push(categoryNode);
    categoriesById.set(categoryNode.id, categoryNode);
  }

  return { categories, categoriesById, subcategoriesById, skillsBySubcategory };
}

// ─────────────────────────────────────────────────────────────────────────────
// MAIN COMPONENT
// ─────────────────────────────────────────────────────────────────────────────

const SkillLibraryPage = () => {
  // ═══════════════════════════════════════════════════════════════════════════
  // DATA STATE
  // ═══════════════════════════════════════════════════════════════════════════
  
  const [categories, setCategories] = useState([]);
  const [lookupMaps, setLookupMaps] = useState({
    categoriesById: new Map(),
    subcategoriesById: new Map(),
    skillsBySubcategory: new Map(),
  });
  
  // Loading/error state
  const [isLoading, setIsLoading] = useState(true);
  const [showLoader, setShowLoader] = useState(false);
  const [error, setError] = useState(null);
  
  // Abort controller for cleanup
  const abortControllerRef = useRef(null);
  const loaderTimeoutRef = useRef(null);

  // ═══════════════════════════════════════════════════════════════════════════
  // SELECTION STATE
  // ═══════════════════════════════════════════════════════════════════════════
  
  const [selected, setSelected] = useState({ type: null, catId: null, subId: null });
  const [expandedCategories, setExpandedCategories] = useState(new Set());
  const [treeQuery, setTreeQuery] = useState('');
  const [_listQuery, setListQuery] = useState('');

  // ═══════════════════════════════════════════════════════════════════════════
  // MODAL STATE
  // ═══════════════════════════════════════════════════════════════════════════
  
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [createModalError, setCreateModalError] = useState(null);
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState(null); // { type, id, name }
  const [dependencyModalOpen, setDependencyModalOpen] = useState(false);
  const [dependencyInfo, setDependencyInfo] = useState({ itemName: '', dependencies: [] });
  const [importModalOpen, setImportModalOpen] = useState(false);

  // ═══════════════════════════════════════════════════════════════════════════
  // INLINE ADD/EDIT STATE (for skills)
  // ═══════════════════════════════════════════════════════════════════════════
  
  const [isAddingSkill, setIsAddingSkill] = useState(false);
  const [selectedSkillIds, setSelectedSkillIds] = useState(new Set());
  const [showBulkDeleteModal, setShowBulkDeleteModal] = useState(false);
  const [skillSearchQuery, setSkillSearchQuery] = useState('');

  // ═══════════════════════════════════════════════════════════════════════════
  // CATEGORY INLINE EDIT STATE
  // ═══════════════════════════════════════════════════════════════════════════
  
  const [isEditingCategoryName, setIsEditingCategoryName] = useState(false);
  const [editCategoryNameValue, setEditCategoryNameValue] = useState('');
  const [isEditingCategoryDescription, setIsEditingCategoryDescription] = useState(false);
  const [editCategoryDescriptionValue, setEditCategoryDescriptionValue] = useState('');
  const categoryNameInputRef = useRef(null);
  const categoryDescriptionInputRef = useRef(null);

  // ═══════════════════════════════════════════════════════════════════════════
  // SUBCATEGORY INLINE EDIT STATE
  // ═══════════════════════════════════════════════════════════════════════════
  
  const [isEditingSubcategoryName, setIsEditingSubcategoryName] = useState(false);
  const [editSubcategoryNameValue, setEditSubcategoryNameValue] = useState('');
  const subcategoryNameInputRef = useRef(null);
  const [isEditingSubcategoryDescription, setIsEditingSubcategoryDescription] = useState(false);
  const [editSubcategoryDescriptionValue, setEditSubcategoryDescriptionValue] = useState('');
  const subcategoryDescriptionInputRef = useRef(null);

  // ═══════════════════════════════════════════════════════════════════════════
  // IMPORT STATE
  // ═══════════════════════════════════════════════════════════════════════════
  
  const [_isImporting, setIsImporting] = useState(false);
  const [importOverlay, setImportOverlay] = useState({ visible: false, message: '' });
  const importPollingRef = useRef(null);

  // ═══════════════════════════════════════════════════════════════════════════
  // DATA LOADING
  // ═══════════════════════════════════════════════════════════════════════════

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
      
      const { categories: newCategories, categoriesById, subcategoriesById, skillsBySubcategory } = 
        transformApiResponse(response);
      
      setCategories(newCategories);
      setLookupMaps({ categoriesById, subcategoriesById, skillsBySubcategory });
      setError(null);
    } catch (err) {
      if (err.name === 'AbortError') return;
      console.error('Failed to load skill taxonomy:', err);
      setError(err.message || 'Failed to load skill taxonomy');
      setCategories([]);
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
      if (importPollingRef.current) {
        clearTimeout(importPollingRef.current);
      }
    };
  }, [loadTaxonomy]);

  // ═══════════════════════════════════════════════════════════════════════════
  // COMPUTED VALUES
  // ═══════════════════════════════════════════════════════════════════════════

  // Get selected category
  const selectedCategory = useMemo(() => {
    if (!selected.catId) return null;
    return lookupMaps.categoriesById.get(selected.catId) || 
           categories.find(c => c.id === selected.catId) || null;
  }, [selected.catId, lookupMaps.categoriesById, categories]);

  // Get selected subcategory
  const selectedSubcategory = useMemo(() => {
    if (!selected.subId) return null;
    return lookupMaps.subcategoriesById.get(selected.subId) || null;
  }, [selected.subId, lookupMaps.subcategoriesById]);

  // Get skills for selected subcategory
  const selectedSubcategorySkills = useMemo(() => {
    if (!selected.subId) return [];
    return lookupMaps.skillsBySubcategory.get(selected.subId) || [];
  }, [selected.subId, lookupMaps.skillsBySubcategory]);

  // Filter skills by search query
  const filteredSkills = useMemo(() => {
    if (!skillSearchQuery.trim()) return selectedSubcategorySkills;
    const q = skillSearchQuery.toLowerCase();
    return selectedSubcategorySkills.filter(skill =>
      skill.name.toLowerCase().includes(q) ||
      skill.aliases?.some(a => a.text.toLowerCase().includes(q))
    );
  }, [selectedSubcategorySkills, skillSearchQuery]);

  // Breadcrumb computation
  const breadcrumb = useMemo(() => {
    if (!selected.type) return 'Skill Library';
    if (selected.type === 'category' && selectedCategory) {
      return `Skill Library > ${selectedCategory.name}`;
    }
    if (selected.type === 'subcategory' && selectedCategory && selectedSubcategory) {
      return `Skill Library > ${selectedCategory.name} > ${selectedSubcategory.name}`;
    }
    return 'Skill Library';
  }, [selected, selectedCategory, selectedSubcategory]);

  // Filtered tree based on search
  const filteredTree = useMemo(() => {
    const q = treeQuery.trim().toLowerCase();
    if (!q) return categories;

    return categories.filter(cat => {
      const catMatch = cat.name.toLowerCase().includes(q);
      const subs = cat.subcategories.filter(s => s.name.toLowerCase().includes(q));
      return catMatch || subs.length > 0;
    }).map(cat => {
      const catMatch = cat.name.toLowerCase().includes(q);
      const subs = cat.subcategories.filter(s => s.name.toLowerCase().includes(q));
      return {
        ...cat,
        subcategories: catMatch ? cat.subcategories : subs
      };
    });
  }, [categories, treeQuery]);

  // ═══════════════════════════════════════════════════════════════════════════
  // NAVIGATION HANDLERS
  // ═══════════════════════════════════════════════════════════════════════════

  const toggleCategoryExpand = (catId, e) => {
    if (e) e.stopPropagation();
    setExpandedCategories(prev => {
      const next = new Set(prev);
      if (next.has(catId)) {
        next.delete(catId);
      } else {
        next.add(catId);
      }
      return next;
    });
  };

  const handleCategoryClick = (catId) => {
    setSelected({ type: 'category', catId, subId: null });
    // Expand the category when selected
    setExpandedCategories(prev => {
      const next = new Set(prev);
      next.add(catId);
      return next;
    });
    setListQuery('');
    setSkillSearchQuery('');
    setIsAddingSkill(false);
    setSelectedSkillIds(new Set());
  };

  const handleSubcategoryClick = (catId, subId, e) => {
    if (e) e.stopPropagation();
    setSelected({ type: 'subcategory', catId, subId });
    // Expand the parent category when subcategory is selected
    setExpandedCategories(prev => {
      const next = new Set(prev);
      next.add(catId);
      return next;
    });
    setListQuery('');
    setSkillSearchQuery('');
    setIsAddingSkill(false);
    setSelectedSkillIds(new Set());
  };

  // ═══════════════════════════════════════════════════════════════════════════
  // CATEGORY CRUD
  // ═══════════════════════════════════════════════════════════════════════════

  const handleAddCategory = () => {
    setCreateModalError(null);
    setCreateModalOpen(true);
  };

  const handleCreateCategory = async (formData) => {
    const { name, description } = formData;
    try {
      const response = await createCategory(name, description);
      
      const newCategoryNode = {
        id: `cat-${response.id}`,
        rawId: response.id,
        type: 'category',
        name: response.name,
        description: response.description || description || 'No description provided.',
        createdAt: response.created_at ? formatDate(response.created_at) : null,
        createdBy: response.created_by,
        subcategories: [],
        subcategoryCount: 0,
        skillCount: 0,
        employeeCount: 0,
      };
      
      setCategories(prev => {
        const updated = [...prev, newCategoryNode];
        return updated.sort((a, b) => a.name.localeCompare(b.name));
      });
      
      setLookupMaps(prev => {
        const newCategoriesById = new Map(prev.categoriesById);
        newCategoriesById.set(newCategoryNode.id, newCategoryNode);
        return { ...prev, categoriesById: newCategoriesById };
      });
      
      setSelected({ type: 'category', catId: newCategoryNode.id, subId: null });
      setCreateModalOpen(false);
      setCreateModalError(null);
    } catch (err) {
      const message = err.data?.detail || err.message || 'Failed to create category';
      if (err.status === 409) {
        setCreateModalError(message);
      } else {
        setCreateModalOpen(false);
        setError(message);
      }
    }
  };

  const handleEditCategoryName = async (newName) => {
    if (!selectedCategory) return;
    try {
      await updateCategoryName(selectedCategory.rawId, newName);
      
      setCategories(prev => prev.map(c =>
        c.id === selectedCategory.id ? { ...c, name: newName } : c
      ));
      
      setLookupMaps(prev => {
        const newCategoriesById = new Map(prev.categoriesById);
        const cat = newCategoriesById.get(selectedCategory.id);
        if (cat) {
          newCategoriesById.set(selectedCategory.id, { ...cat, name: newName });
        }
        return { ...prev, categoriesById: newCategoriesById };
      });
      setIsEditingCategoryName(false);
    } catch (err) {
      console.error('Failed to update category name:', err);
      setError(err.data?.detail || err.message || 'Failed to update category name');
    }
  };

  const handleEditCategoryDescription = async (newDescription) => {
    if (!selectedCategory) return;
    try {
      // Pass current name but update description
      await updateCategoryName(selectedCategory.rawId, selectedCategory.name, newDescription, true);
      
      const displayDescription = newDescription || 'No description provided.';
      
      setCategories(prev => prev.map(c =>
        c.id === selectedCategory.id ? { ...c, description: displayDescription } : c
      ));
      
      setLookupMaps(prev => {
        const newCategoriesById = new Map(prev.categoriesById);
        const cat = newCategoriesById.get(selectedCategory.id);
        if (cat) {
          newCategoriesById.set(selectedCategory.id, { ...cat, description: displayDescription });
        }
        return { ...prev, categoriesById: newCategoriesById };
      });
      setIsEditingCategoryDescription(false);
    } catch (err) {
      console.error('Failed to update category description:', err);
      setError(err.data?.detail || err.message || 'Failed to update category description');
    }
  };

  // Category name edit handlers
  const startEditCategoryName = () => {
    setEditCategoryNameValue(selectedCategory?.name || '');
    setIsEditingCategoryName(true);
    setTimeout(() => categoryNameInputRef.current?.focus(), 0);
  };

  const cancelEditCategoryName = () => {
    setIsEditingCategoryName(false);
    setEditCategoryNameValue('');
  };

  const saveCategoryName = () => {
    const trimmed = editCategoryNameValue.trim();
    if (!trimmed) {
      cancelEditCategoryName();
      return;
    }
    if (trimmed !== selectedCategory?.name) {
      handleEditCategoryName(trimmed);
    } else {
      cancelEditCategoryName();
    }
  };

  // Category description edit handlers
  const startEditCategoryDescription = () => {
    const currentDesc = selectedCategory?.description === 'No description provided.' 
      ? '' 
      : (selectedCategory?.description || '');
    setEditCategoryDescriptionValue(currentDesc);
    setIsEditingCategoryDescription(true);
    setTimeout(() => categoryDescriptionInputRef.current?.focus(), 0);
  };

  const cancelEditCategoryDescription = () => {
    setIsEditingCategoryDescription(false);
    setEditCategoryDescriptionValue('');
  };

  const saveCategoryDescription = () => {
    const trimmed = editCategoryDescriptionValue.trim();
    const currentDesc = selectedCategory?.description === 'No description provided.' 
      ? '' 
      : (selectedCategory?.description || '');
    if (trimmed !== currentDesc) {
      handleEditCategoryDescription(trimmed);
    } else {
      cancelEditCategoryDescription();
    }
  };

  const handleDeleteCategoryClick = () => {
    if (!selectedCategory) return;
    
    // Check for dependencies
    if (selectedCategory.subcategories.length > 0) {
      setDependencyInfo({
        itemName: selectedCategory.name,
        dependencies: [
          { icon: '📂', label: `${selectedCategory.subcategories.length} Sub-categor${selectedCategory.subcategories.length === 1 ? 'y' : 'ies'}` },
          ...(selectedCategory.skillCount > 0 ? [{ icon: '🏷️', label: `${selectedCategory.skillCount} Skill${selectedCategory.skillCount === 1 ? '' : 's'}` }] : [])
        ]
      });
      setDependencyModalOpen(true);
      return;
    }
    
    setDeleteTarget({ type: 'category', id: selectedCategory.id, rawId: selectedCategory.rawId, name: selectedCategory.name });
    setDeleteModalOpen(true);
  };

  const handleConfirmDeleteCategory = async () => {
    if (!deleteTarget || deleteTarget.type !== 'category') return;
    
    try {
      await deleteCategory(deleteTarget.rawId);
      
      setCategories(prev => prev.filter(c => c.id !== deleteTarget.id));
      setLookupMaps(prev => {
        const newCategoriesById = new Map(prev.categoriesById);
        newCategoriesById.delete(deleteTarget.id);
        return { ...prev, categoriesById: newCategoriesById };
      });
      
      setSelected({ type: null, catId: null, subId: null });
      setDeleteModalOpen(false);
      setDeleteTarget(null);
    } catch (err) {
      console.error('Failed to delete category:', err);
      setError(err.data?.detail || err.message || 'Failed to delete category');
      setDeleteModalOpen(false);
    }
  };

  // ═══════════════════════════════════════════════════════════════════════════
  // SUBCATEGORY CRUD (using TaxonomyCategorySubCategoriesPanel handlers)
  // ═══════════════════════════════════════════════════════════════════════════

  const handleCreateSubcategory = async (subCategoryName, description = null) => {
    if (!selectedCategory) return;
    
    try {
      const response = await createSubcategory(selectedCategory.rawId, subCategoryName, description);
      
      const newSubcategoryNode = {
        id: `subcat-${response.id}`,
        rawId: response.id,
        type: 'subcategory',
        name: response.name,
        description: response.description || null,
        parentId: selectedCategory.id,
        categoryId: selectedCategory.id,
        categoryRawId: selectedCategory.rawId,
        categoryName: selectedCategory.name,
        createdAt: response.created_at ? formatDate(response.created_at) : null,
        createdBy: response.created_by,
        skillCount: 0,
        employeeCount: 0,
      };
      
      // Update categories list
      setCategories(prev => prev.map(c => {
        if (c.id === selectedCategory.id) {
          const updatedSubs = [...c.subcategories, newSubcategoryNode];
          updatedSubs.sort((a, b) => a.name.localeCompare(b.name));
          return {
            ...c,
            subcategories: updatedSubs,
            subcategoryCount: c.subcategoryCount + 1,
          };
        }
        return c;
      }));
      
      // Update lookup maps - both subcategoriesById, categoriesById, and skillsBySubcategory
      setLookupMaps(prev => {
        const newSubcategoriesById = new Map(prev.subcategoriesById);
        const newSkillsBySubcategory = new Map(prev.skillsBySubcategory);
        const newCategoriesById = new Map(prev.categoriesById);
        
        newSubcategoriesById.set(newSubcategoryNode.id, newSubcategoryNode);
        newSkillsBySubcategory.set(newSubcategoryNode.id, []);
        
        // Update categoriesById with new subcategory
        const category = newCategoriesById.get(selectedCategory.id);
        if (category) {
          const updatedSubs = [...category.subcategories, newSubcategoryNode];
          updatedSubs.sort((a, b) => a.name.localeCompare(b.name));
          newCategoriesById.set(selectedCategory.id, {
            ...category,
            subcategories: updatedSubs,
            subcategoryCount: category.subcategoryCount + 1,
          });
        }
        
        return {
          ...prev,
          subcategoriesById: newSubcategoriesById,
          skillsBySubcategory: newSkillsBySubcategory,
          categoriesById: newCategoriesById,
        };
      });
    } catch (err) {
      console.error('Failed to create sub-category:', err);
      throw err; // Re-throw so panel can handle error display
    }
  };

  const handleEditSubcategory = async (subCategoryWithNewName) => {
    const { rawId, newName, newDescription, descriptionChanged } = subCategoryWithNewName;
    
    try {
      const response = await updateSubcategoryName(rawId, newName, newDescription, !!descriptionChanged);
      
      // Update in categories list
      setCategories(prev => prev.map(c => {
        if (c.id === selected.catId) {
          return {
            ...c,
            subcategories: c.subcategories.map(s =>
              s.rawId === rawId ? { ...s, name: response.name, description: response.description } : s
            ),
          };
        }
        return c;
      }));
      
      // Update lookup maps - both subcategoriesById AND categoriesById
      setLookupMaps(prev => {
        const newSubcategoriesById = new Map(prev.subcategoriesById);
        const newCategoriesById = new Map(prev.categoriesById);
        const subId = `subcat-${rawId}`;
        const existing = newSubcategoriesById.get(subId);
        if (existing) {
          newSubcategoriesById.set(subId, { ...existing, name: response.name, description: response.description });
        }
        // Update categoriesById as well if it contains subcategories
        const category = newCategoriesById.get(selected.catId);
        if (category) {
          newCategoriesById.set(selected.catId, {
            ...category,
            subcategories: category.subcategories.map(s =>
              s.rawId === rawId ? { ...s, name: response.name, description: response.description } : s
            ),
          });
        }
        return { 
          ...prev, 
          subcategoriesById: newSubcategoriesById,
          categoriesById: newCategoriesById 
        };
      });
    } catch (err) {
      console.error('Failed to update sub-category:', err);
      throw err;
    }
  };

  const handleDeleteSubcategory = async (subCategory) => {
    try {
      await deleteSubcategory(subCategory.rawId);
      
      // Update categories list
      setCategories(prev => prev.map(c => {
        if (c.id === selected.catId) {
          return {
            ...c,
            subcategories: c.subcategories.filter(s => s.id !== subCategory.id),
            subcategoryCount: Math.max(0, c.subcategoryCount - 1),
            skillCount: Math.max(0, c.skillCount - (subCategory.skillCount || 0)),
          };
        }
        return c;
      }));
      
      // Update lookup maps - including categoriesById
      setLookupMaps(prev => {
        const newSubcategoriesById = new Map(prev.subcategoriesById);
        const newSkillsBySubcategory = new Map(prev.skillsBySubcategory);
        const newCategoriesById = new Map(prev.categoriesById);
        
        newSubcategoriesById.delete(subCategory.id);
        newSkillsBySubcategory.delete(subCategory.id);
        
        // Update categoriesById
        const category = newCategoriesById.get(selected.catId);
        if (category) {
          newCategoriesById.set(selected.catId, {
            ...category,
            subcategories: category.subcategories.filter(s => s.id !== subCategory.id),
            subcategoryCount: Math.max(0, category.subcategoryCount - 1),
            skillCount: Math.max(0, category.skillCount - (subCategory.skillCount || 0)),
          });
        }
        
        return {
          ...prev,
          subcategoriesById: newSubcategoriesById,
          skillsBySubcategory: newSkillsBySubcategory,
          categoriesById: newCategoriesById,
        };
      });
      
      // If deleted subcategory was selected, go back to category view
      if (selected.subId === subCategory.id) {
        setSelected({ type: 'category', catId: selected.catId, subId: null });
      }
    } catch (err) {
      console.error('Failed to delete sub-category:', err);
      throw err;
    }
  };

  const handleBulkDeleteSubcategories = async (subCategories) => {
    for (const subCategory of subCategories) {
      await handleDeleteSubcategory(subCategory);
    }
  };

  const handleSubcategoryTableClick = (subCategory) => {
    handleSubcategoryClick(selected.catId, subCategory.id, null);
  };

  // ═══════════════════════════════════════════════════════════════════════════
  // SUBCATEGORY NAME EDIT (for title)
  // ═══════════════════════════════════════════════════════════════════════════

  const handleEditSubcategoryName = async (newName) => {
    if (!selectedSubcategory) return;
    try {
      await updateSubcategoryName(selectedSubcategory.rawId, newName);
      
      // Update in categories list
      setCategories(prev => prev.map(c => {
        if (c.id === selected.catId) {
          return {
            ...c,
            subcategories: c.subcategories.map(s =>
              s.id === selected.subId ? { ...s, name: newName } : s
            ),
          };
        }
        return c;
      }));
      
      // Update lookup maps
      setLookupMaps(prev => {
        const newSubcategoriesById = new Map(prev.subcategoriesById);
        const existing = newSubcategoriesById.get(selected.subId);
        if (existing) {
          newSubcategoriesById.set(selected.subId, { ...existing, name: newName });
        }
        return { ...prev, subcategoriesById: newSubcategoriesById };
      });
      setIsEditingSubcategoryName(false);
    } catch (err) {
      console.error('Failed to update sub-category name:', err);
      setError(err.data?.detail || err.message || 'Failed to update sub-category name');
    }
  };

  // Subcategory name edit handlers
  const startEditSubcategoryName = () => {
    setEditSubcategoryNameValue(selectedSubcategory?.name || '');
    setIsEditingSubcategoryName(true);
    setTimeout(() => subcategoryNameInputRef.current?.focus(), 0);
  };

  const cancelEditSubcategoryName = () => {
    setIsEditingSubcategoryName(false);
    setEditSubcategoryNameValue('');
  };

  const saveSubcategoryName = () => {
    const trimmed = editSubcategoryNameValue.trim();
    if (!trimmed) {
      cancelEditSubcategoryName();
      return;
    }
    if (trimmed !== selectedSubcategory?.name) {
      handleEditSubcategoryName(trimmed);
    } else {
      cancelEditSubcategoryName();
    }
  };

  // ═══════════════════════════════════════════════════════════════════════════
  // SUBCATEGORY DESCRIPTION EDIT
  // ═══════════════════════════════════════════════════════════════════════════

  const handleEditSubcategoryDescription = async (newDescription) => {
    if (!selectedSubcategory) return;
    try {
      // Pass current name but update description
      await updateSubcategoryName(selectedSubcategory.rawId, selectedSubcategory.name, newDescription, true);
      
      const displayDescription = newDescription || 'No description provided.';
      
      // Update in categories list
      setCategories(prev => prev.map(c => {
        if (c.id === selected.catId) {
          return {
            ...c,
            subcategories: c.subcategories.map(s =>
              s.id === selected.subId ? { ...s, description: displayDescription } : s
            ),
          };
        }
        return c;
      }));
      
      // Update lookup maps - both subcategoriesById AND categoriesById
      setLookupMaps(prev => {
        const newSubcategoriesById = new Map(prev.subcategoriesById);
        const newCategoriesById = new Map(prev.categoriesById);
        
        const existing = newSubcategoriesById.get(selected.subId);
        if (existing) {
          newSubcategoriesById.set(selected.subId, { ...existing, description: displayDescription });
        }
        
        // Update categoriesById as well if it contains subcategories
        const category = newCategoriesById.get(selected.catId);
        if (category) {
          newCategoriesById.set(selected.catId, {
            ...category,
            subcategories: category.subcategories.map(s =>
              s.id === selected.subId ? { ...s, description: displayDescription } : s
            ),
          });
        }
        
        return { 
          ...prev, 
          subcategoriesById: newSubcategoriesById,
          categoriesById: newCategoriesById 
        };
      });
      setIsEditingSubcategoryDescription(false);
    } catch (err) {
      console.error('Failed to update sub-category description:', err);
      setError(err.data?.detail || err.message || 'Failed to update sub-category description');
    }
  };

  // Subcategory description edit handlers
  const startEditSubcategoryDescription = () => {
    const currentDesc = selectedSubcategory?.description === 'No description provided.' 
      ? '' 
      : (selectedSubcategory?.description || '');
    setEditSubcategoryDescriptionValue(currentDesc);
    setIsEditingSubcategoryDescription(true);
    setTimeout(() => subcategoryDescriptionInputRef.current?.focus(), 0);
  };

  const cancelEditSubcategoryDescription = () => {
    setIsEditingSubcategoryDescription(false);
    setEditSubcategoryDescriptionValue('');
  };

  const saveSubcategoryDescription = () => {
    const trimmed = editSubcategoryDescriptionValue.trim();
    const currentDesc = selectedSubcategory?.description === 'No description provided.' 
      ? '' 
      : (selectedSubcategory?.description || '');
    if (trimmed !== currentDesc) {
      handleEditSubcategoryDescription(trimmed);
    } else {
      cancelEditSubcategoryDescription();
    }
  };

  const handleDeleteSubcategoryClick = () => {
    if (!selectedSubcategory) return;
    
    // Check for dependencies (skills)
    const skillCount = selectedSubcategorySkills.length;
    if (skillCount > 0) {
      setDependencyInfo({
        itemName: selectedSubcategory.name,
        dependencies: [
          { icon: '🏷️', label: `${skillCount} Skill${skillCount === 1 ? '' : 's'}` }
        ]
      });
      setDependencyModalOpen(true);
      return;
    }
    
    setDeleteTarget({
      type: 'subcategory',
      id: selectedSubcategory.id,
      rawId: selectedSubcategory.rawId,
      name: selectedSubcategory.name
    });
    setDeleteModalOpen(true);
  };

  const handleConfirmDeleteSubcategory = async () => {
    if (!deleteTarget || deleteTarget.type !== 'subcategory') return;
    
    try {
      await deleteSubcategory(deleteTarget.rawId);
      
      // Update categories list
      setCategories(prev => prev.map(c => {
        if (c.id === selected.catId) {
          return {
            ...c,
            subcategories: c.subcategories.filter(s => s.id !== deleteTarget.id),
            subcategoryCount: Math.max(0, c.subcategoryCount - 1),
          };
        }
        return c;
      }));
      
      // Update lookup maps
      setLookupMaps(prev => {
        const newSubcategoriesById = new Map(prev.subcategoriesById);
        const newSkillsBySubcategory = new Map(prev.skillsBySubcategory);
        newSubcategoriesById.delete(deleteTarget.id);
        newSkillsBySubcategory.delete(deleteTarget.id);
        return {
          ...prev,
          subcategoriesById: newSubcategoriesById,
          skillsBySubcategory: newSkillsBySubcategory,
        };
      });
      
      setSelected({ type: 'category', catId: selected.catId, subId: null });
      setDeleteModalOpen(false);
      setDeleteTarget(null);
    } catch (err) {
      console.error('Failed to delete sub-category:', err);
      setError(err.data?.detail || err.message || 'Failed to delete sub-category');
      setDeleteModalOpen(false);
    }
  };

  // ═══════════════════════════════════════════════════════════════════════════
  // SKILL CRUD (using SkillsTable handlers)
  // ═══════════════════════════════════════════════════════════════════════════

  const handleStartAddSkill = useCallback(() => {
    setIsAddingSkill(true);
  }, []);

  const handleAddSkillComplete = useCallback(async (newSkillData) => {
    if (!selectedSubcategory) return;
    
    try {
      const aliasText = newSkillData.aliases?.map(a => a.text).join(', ') || null;
      const response = await createSkill(selectedSubcategory.rawId, newSkillData.name, aliasText);
      
      const createdSkill = {
        id: `skill-${response.id}`,
        rawId: response.id,
        type: 'skill',
        name: response.name,
        aliases: response.aliases?.map(a => ({ id: a.id, text: a.alias_text })) || [],
        createdAt: response.created_at ? formatDate(response.created_at) : null,
        createdBy: response.created_by,
        employeeCount: 0
      };
      
      // Add to lookup maps - update skillsBySubcategory, categoriesById, and subcategoriesById
      setLookupMaps(prev => {
        const newSkillsBySubcategory = new Map(prev.skillsBySubcategory);
        const newCategoriesById = new Map(prev.categoriesById);
        const newSubcategoriesById = new Map(prev.subcategoriesById);
        
        // Add skill to subcategory's skills list
        const currentSkills = newSkillsBySubcategory.get(selected.subId) || [];
        newSkillsBySubcategory.set(selected.subId, [createdSkill, ...currentSkills]);
        
        // Update category skillCount in categoriesById
        const category = newCategoriesById.get(selected.catId);
        if (category) {
          const updatedSubcategories = category.subcategories.map(s =>
            s.id === selected.subId ? { ...s, skillCount: s.skillCount + 1 } : s
          );
          newCategoriesById.set(selected.catId, {
            ...category,
            skillCount: category.skillCount + 1,
            subcategories: updatedSubcategories,
          });
        }
        
        // Update subcategory skillCount in subcategoriesById
        const subcategory = newSubcategoriesById.get(selected.subId);
        if (subcategory) {
          newSubcategoriesById.set(selected.subId, {
            ...subcategory,
            skillCount: subcategory.skillCount + 1,
          });
        }
        
        return {
          ...prev,
          skillsBySubcategory: newSkillsBySubcategory,
          categoriesById: newCategoriesById,
          subcategoriesById: newSubcategoriesById,
        };
      });
      
      // Update skill count in categories array (for tree rendering)
      setCategories(prev => prev.map(c => {
        if (c.id === selected.catId) {
          return {
            ...c,
            skillCount: c.skillCount + 1,
            subcategories: c.subcategories.map(s =>
              s.id === selected.subId ? { ...s, skillCount: s.skillCount + 1 } : s
            ),
          };
        }
        return c;
      }));
      
      setIsAddingSkill(false);
    } catch (err) {
      console.error('Failed to create skill:', err);
      setError(err.data?.detail || err.message || 'Failed to create skill');
      setIsAddingSkill(false);
    }
  }, [selectedSubcategory, selected.catId, selected.subId]);

  const handleAddSkillCancel = useCallback(() => {
    setIsAddingSkill(false);
  }, []);

  const handleSkillSave = useCallback(async (updatedSkill) => {
    if (!selectedSubcategory) return;
    
    // OPTIMISTIC UPDATE: Apply changes immediately so UI shows new values
    // while API calls are in progress
    const optimisticAliases = updatedSkill.aliases || [];
    
    setLookupMaps(prev => {
      const newSkillsBySubcategory = new Map(prev.skillsBySubcategory);
      const skills = newSkillsBySubcategory.get(selected.subId) || [];
      const updatedSkills = skills.map(s =>
        s.rawId === updatedSkill.rawId
          ? { ...s, name: updatedSkill.name, aliases: optimisticAliases }
          : s
      );
      newSkillsBySubcategory.set(selected.subId, updatedSkills);
      return { ...prev, skillsBySubcategory: newSkillsBySubcategory };
    });
    
    try {
      // Update skill name if changed - use rawId for reliable matching
      const existingSkills = lookupMaps.skillsBySubcategory.get(selected.subId) || [];
      const originalSkill = existingSkills.find(s => s.rawId === updatedSkill.rawId);
      
      if (originalSkill && originalSkill.name !== updatedSkill.name) {
        await updateSkillName(updatedSkill.rawId, updatedSkill.name);
      }
      
      // Handle alias changes - guard against undefined/null alias IDs
      const removedAliasIds = (updatedSkill._removedAliasIds || [])
        .filter(id => id != null && Number.isInteger(id));
      for (const aliasId of removedAliasIds) {
        await deleteAlias(aliasId);
      }
      
      // Create new aliases (those without ID) and collect their responses
      const newAliases = (updatedSkill.aliases || []).filter(a => !a.id);
      const createdAliases = [];
      for (const alias of newAliases) {
        const response = await createAlias(updatedSkill.rawId, alias.text);
        // Backend returns 'id' not 'alias_id' for AliasCreateResponse
        createdAliases.push({ id: response.id, text: response.alias_text });
      }
      
      // Build final aliases list: kept aliases (with IDs) + newly created aliases
      const keptAliases = (updatedSkill.aliases || []).filter(a => a.id);
      const finalAliases = [...keptAliases, ...createdAliases];
      
      // Update local state with the skill including correct alias IDs from backend
      // Create new Maps for all parts of lookupMaps to ensure React detects the change
      setLookupMaps(prev => {
        const newSkillsBySubcategory = new Map(prev.skillsBySubcategory);
        const newCategoriesById = new Map(prev.categoriesById);
        const newSubcategoriesById = new Map(prev.subcategoriesById);
        
        // Update skill in skillsBySubcategory - use rawId for reliable matching
        const skills = newSkillsBySubcategory.get(selected.subId) || [];
        const updatedSkills = skills.map(s =>
          s.rawId === updatedSkill.rawId
            ? { ...s, name: updatedSkill.name, aliases: finalAliases }
            : s
        );
        newSkillsBySubcategory.set(selected.subId, updatedSkills);
        
        // Touch categoriesById to ensure complete state refresh
        const category = newCategoriesById.get(selected.catId);
        if (category) {
          newCategoriesById.set(selected.catId, { ...category });
        }
        
        // Touch subcategoriesById to ensure complete state refresh
        const subcategory = newSubcategoriesById.get(selected.subId);
        if (subcategory) {
          newSubcategoriesById.set(selected.subId, { ...subcategory });
        }
        
        return {
          ...prev,
          skillsBySubcategory: newSkillsBySubcategory,
          categoriesById: newCategoriesById,
          subcategoriesById: newSubcategoriesById,
        };
      });
    } catch (err) {
      console.error('Failed to update skill:', err);
      setError(err.data?.detail || err.message || 'Failed to update skill');
      // On error, revert to original values by re-fetching or restoring
      // For now, we'll leave the optimistic update in place since backend likely succeeded partially
    }
  }, [selectedSubcategory, selected.catId, selected.subId, lookupMaps.skillsBySubcategory]);

  const handleSkillDelete = useCallback(async (skill) => {
    if (!selectedSubcategory) return;
    
    try {
      await deleteSkill(skill.rawId);
      
      // Remove from lookup maps - update skillsBySubcategory, categoriesById, and subcategoriesById
      setLookupMaps(prev => {
        const newSkillsBySubcategory = new Map(prev.skillsBySubcategory);
        const newCategoriesById = new Map(prev.categoriesById);
        const newSubcategoriesById = new Map(prev.subcategoriesById);
        
        // Remove skill from subcategory's skills list
        const skills = newSkillsBySubcategory.get(selected.subId) || [];
        newSkillsBySubcategory.set(selected.subId, skills.filter(s => s.id !== skill.id));
        
        // Update category skillCount in categoriesById
        const category = newCategoriesById.get(selected.catId);
        if (category) {
          const updatedSubcategories = category.subcategories.map(s =>
            s.id === selected.subId ? { ...s, skillCount: Math.max(0, s.skillCount - 1) } : s
          );
          newCategoriesById.set(selected.catId, {
            ...category,
            skillCount: Math.max(0, category.skillCount - 1),
            subcategories: updatedSubcategories,
          });
        }
        
        // Update subcategory skillCount in subcategoriesById
        const subcategory = newSubcategoriesById.get(selected.subId);
        if (subcategory) {
          newSubcategoriesById.set(selected.subId, {
            ...subcategory,
            skillCount: Math.max(0, subcategory.skillCount - 1),
          });
        }
        
        return {
          ...prev,
          skillsBySubcategory: newSkillsBySubcategory,
          categoriesById: newCategoriesById,
          subcategoriesById: newSubcategoriesById,
        };
      });
      
      // Update skill count in categories array (for tree rendering)
      setCategories(prev => prev.map(c => {
        if (c.id === selected.catId) {
          return {
            ...c,
            skillCount: Math.max(0, c.skillCount - 1),
            subcategories: c.subcategories.map(s =>
              s.id === selected.subId ? { ...s, skillCount: Math.max(0, s.skillCount - 1) } : s
            ),
          };
        }
        return c;
      }));
      
      // Remove from selection
      setSelectedSkillIds(prev => {
        const newSet = new Set(prev);
        newSet.delete(skill.id);
        return newSet;
      });
    } catch (err) {
      // Handle 409 - skill has employees
      if (err.status === 409 && err.data) {
        const deps = err.data.dependencies || {};
        const dependencyList = [];
        if (deps.employee_skills) {
          dependencyList.push({ icon: '👥', label: `${deps.employee_skills} Employee${deps.employee_skills > 1 ? 's' : ''} have this skill` });
        }
        setDependencyInfo({ itemName: skill.name, dependencies: dependencyList });
        setDependencyModalOpen(true);
        return;
      }
      console.error('Failed to delete skill:', err);
      setError(err.data?.detail || err.message || 'Failed to delete skill');
    }
  }, [selectedSubcategory, selected.catId, selected.subId]);

  const handleBulkSkillDelete = useCallback(async (skillsToDelete) => {
    for (const skill of skillsToDelete) {
      await handleSkillDelete(skill);
    }
    setSelectedSkillIds(new Set());
    setShowBulkDeleteModal(false);
  }, [handleSkillDelete]);

  const handleSelectedSkillIdsChange = useCallback((newSelection) => {
    setSelectedSkillIds(newSelection);
  }, []);

  const handleHeaderBulkDeleteClick = useCallback(() => {
    if (selectedSkillIds.size > 0) {
      setShowBulkDeleteModal(true);
    }
  }, [selectedSkillIds.size]);

  const handleCloseBulkDeleteModal = useCallback(() => {
    setShowBulkDeleteModal(false);
  }, []);

  // ═══════════════════════════════════════════════════════════════════════════
  // IMPORT HANDLING (same as old page)
  // ═══════════════════════════════════════════════════════════════════════════

  const handleImportSkills = () => {
    setImportModalOpen(true);
  };

  const handleImport = async (data) => {
    if (data.type !== 'file' || !data.file) {
      window.alert('Please select an Excel file to import.');
      return;
    }
    
    setImportModalOpen(false);
    setIsImporting(true);
    
    try {
      const response = await importSkills(data.file);
      const jobId = response.job_id;
      
      if (!jobId) {
        throw new Error('No job ID returned from import');
      }
      
      setImportOverlay({ visible: true, message: 'Starting import...' });
      
      let pollInterval = 2000;
      let consecutiveErrors = 0;
      const maxErrors = 5;
      
      const pollStatus = async () => {
        try {
          const status = await getImportJobStatus(jobId);
          consecutiveErrors = 0;
          pollInterval = 2000;
          
          if (status.status === 'unavailable') {
            setImportOverlay(prev => ({
              ...prev,
              message: status.message || 'Still working... database busy'
            }));
            importPollingRef.current = setTimeout(pollStatus, 3000);
            return;
          }
          
          setImportOverlay({ visible: true, message: status.message || 'Processing...' });
          
          if (status.status === 'completed') {
            if (importPollingRef.current) {
              clearTimeout(importPollingRef.current);
              importPollingRef.current = null;
            }
            
            setImportOverlay({ visible: false, message: '' });
            setIsImporting(false);
            
            const result = status.result || {};
            const summary = result.summary || {};
            let message = `Import completed!\n\n`;
            message += `Categories: ${summary.categories?.inserted || 0} new, ${summary.categories?.existing || 0} existing\n`;
            message += `Sub-Categories: ${summary.subcategories?.inserted || 0} new, ${summary.subcategories?.existing || 0} existing\n`;
            message += `Skills: ${summary.skills?.inserted || 0} new, ${summary.skills?.existing || 0} existing\n`;
            message += `Aliases: ${summary.aliases?.inserted || 0} new, ${summary.aliases?.existing || 0} existing`;
            
            if (result.errors_count > 0) {
              message += `\n\n⚠️ ${result.errors_count} conflict(s) detected.`;
            }
            
            window.alert(message);
            loadTaxonomy();
            return;
          }
          
          if (status.status === 'failed') {
            if (importPollingRef.current) {
              clearTimeout(importPollingRef.current);
              importPollingRef.current = null;
            }
            setImportOverlay({ visible: false, message: '' });
            setIsImporting(false);
            setError(status.error || 'Import failed');
            return;
          }
          
          // Still processing
          importPollingRef.current = setTimeout(pollStatus, pollInterval);
        } catch (_pollErr) {
          consecutiveErrors++;
          if (consecutiveErrors >= maxErrors) {
            setImportOverlay({ visible: false, message: '' });
            setIsImporting(false);
            setError('Import status check failed repeatedly');
            return;
          }
          pollInterval = Math.min(pollInterval * 1.5, 10000);
          importPollingRef.current = setTimeout(pollStatus, pollInterval);
        }
      };
      
      importPollingRef.current = setTimeout(pollStatus, 1000);
    } catch (err) {
      console.error('Import failed:', err);
      setImportOverlay({ visible: false, message: '' });
      setIsImporting(false);
      setError(err.data?.detail || err.message || 'Import failed');
    }
  };

  const handleDownloadTemplate = () => {
    const templateUrl = `${API_BASE_URL}/static/templates/skill_import_template.xlsx`;
    window.open(templateUrl, '_blank');
  };

  // ═══════════════════════════════════════════════════════════════════════════
  // MODAL HANDLERS
  // ═══════════════════════════════════════════════════════════════════════════

  const handleConfirmDelete = async () => {
    if (!deleteTarget) return;
    
    if (deleteTarget.type === 'category') {
      await handleConfirmDeleteCategory();
    } else if (deleteTarget.type === 'subcategory') {
      await handleConfirmDeleteSubcategory();
    }
  };

  const handleCloseDependencyModal = () => {
    setDependencyModalOpen(false);
    setDependencyInfo({ itemName: '', dependencies: [] });
  };

  // ═══════════════════════════════════════════════════════════════════════════
  // RENDER HELPERS
  // ═══════════════════════════════════════════════════════════════════════════

  // Render tree
  const renderTree = () => {
    if (isLoading && showLoader) {
      return (
        <div style={{ padding: '24px', textAlign: 'center', color: '#64748b' }}>
          <div style={{ marginBottom: '8px' }}>Loading...</div>
        </div>
      );
    }
    
    if (error) {
      return (
        <div style={{ padding: '24px', textAlign: 'center', color: '#ef4444' }}>
          <div style={{ marginBottom: '8px' }}>⚠️ {error}</div>
          <button className="sl-btn" onClick={loadTaxonomy}>Retry</button>
        </div>
      );
    }
    
    if (filteredTree.length === 0) {
      return (
        <div style={{ padding: '24px', textAlign: 'center', color: '#64748b' }}>
          {treeQuery ? 'No matching categories or sub-categories.' : 'No categories yet. Create one to get started.'}
        </div>
      );
    }

    return (
      <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
        {filteredTree.map(cat => {
          const isExpanded = expandedCategories.has(cat.id);
          const hasSubs = cat.subcategories.length > 0;
          
          return (
            <li key={cat.id}>
              <div
                className={`sl-node ${selected.type === 'category' && selected.catId === cat.id ? 'selected' : ''}`}
                onClick={() => handleCategoryClick(cat.id)}
              >
                <div className="sl-node-left">
                  <span 
                    className="sl-caret" 
                    onClick={(e) => hasSubs && toggleCategoryExpand(cat.id, e)}
                    style={{ cursor: hasSubs ? 'pointer' : 'default' }}
                  >
                    {hasSubs ? (isExpanded ? '▾' : '▸') : ''}
                  </span>
                  <div className="sl-folder-icon"></div>
                  <span className="sl-label">{cat.name}</span>
                </div>
                <span className="sl-count">({cat.subcategories.length})</span>
              </div>

              {isExpanded && hasSubs && (
                <div className="sl-subtree">
                  {cat.subcategories.map(sub => (
                    <div
                      key={sub.id}
                      className={`sl-subnode ${selected.type === 'subcategory' && selected.subId === sub.id ? 'selected' : ''}`}
                      onClick={(e) => handleSubcategoryClick(cat.id, sub.id, e)}
                    >
                      <div className="sl-subnode-left">
                        <div className="sl-dot-icon"></div>
                        <span className="sl-label">{sub.name}</span>
                      </div>
                      <span className="sl-count">({sub.skillCount})</span>
                    </div>
                  ))}
                </div>
              )}
            </li>
          );
        })}
      </ul>
    );
  };

  // Render empty state panel
  const renderEmptyState = () => (
    <>
      <div className="sl-panel-header">
        <div>
          <div className="sl-crumb">{breadcrumb}</div>
          <h1 className="sl-panel-title">
            <span className="sl-pill">GOVERNANCE</span>
            No item selected
          </h1>
        </div>
      </div>

      <div className="sl-panel-body">
        <div className="sl-empty">
          <div style={{ fontSize: '42px' }}>📄</div>
          <h3>No item selected</h3>
          <p>
            Select a <b>Category</b> from the left to manage sub-categories.<br />
            Select a <b>Sub-category</b> to manage skills.<br />
            This keeps the taxonomy structured and consistent across the organization.
          </p>

          <div className="sl-steps">
            <div style={{ fontWeight: 800, letterSpacing: '0.06em', textTransform: 'uppercase', fontSize: '12px', color: '#475569' }}>
              How to use
            </div>
            <ul style={{ listStyleType: 'disc', paddingLeft: '20px', textAlign: 'left', margin: '10px auto', maxWidth: '320px' }}>
              <li>Pick a category from the left tree</li>
              <li>Add or edit sub-categories under that category</li>
              <li>Select a sub-category to add/edit skills</li>
            </ul>
          </div>
        </div>
      </div>
    </>
  );

  // Render category selected panel (uses TaxonomyCategorySubCategoriesPanel)
  const renderCategoryPanel = () => {
    if (!selectedCategory) return renderEmptyState();

    const totalSkills = selectedCategory.skillCount;
    
    // Transform subcategories for the panel component
    const subCategoriesForPanel = selectedCategory.subcategories.map(sub => ({
      id: sub.id,
      rawId: sub.rawId,
      name: sub.name,
      description: sub.description || null,
      skillCount: sub.skillCount,
    }));

    return (
      <>
        <div className="sl-panel-header">
          <div>
            <div className="sl-crumb">{breadcrumb}</div>
            <h1 className="sl-panel-title">
              <span className="sl-pill">CATEGORY</span>
              {isEditingCategoryName ? (
                <span className="sl-title-edit-container">
                  <input
                    ref={categoryNameInputRef}
                    type="text"
                    className="sl-title-input"
                    value={editCategoryNameValue}
                    onChange={(e) => setEditCategoryNameValue(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        e.preventDefault();
                        saveCategoryName();
                      } else if (e.key === 'Escape') {
                        cancelEditCategoryName();
                      }
                    }}
                  />
                  <button 
                    className="sl-iconbtn" 
                    title="Save" 
                    onMouseDown={(e) => { e.preventDefault(); saveCategoryName(); }}
                  >✓</button>
                  <button 
                    className="sl-iconbtn" 
                    title="Cancel" 
                    onMouseDown={(e) => { e.preventDefault(); cancelEditCategoryName(); }}
                  >✕</button>
                </span>
              ) : (
                <>
                  <span className="sl-title-text">{selectedCategory.name}</span>
                  <span className="sl-title-actions">
                    <button className="sl-iconbtn" title="Edit category name" onClick={startEditCategoryName}>✏️</button>
                    <button className="sl-iconbtn sl-iconbtn-danger" title="Delete category" onClick={handleDeleteCategoryClick}>🗑️</button>
                  </span>
                </>
              )}
            </h1>
          </div>
        </div>

        <div className="sl-panel-body">
          <div className="sl-kv">
            <div className="sl-k">Details</div>
            <div className="sl-kv-grid">
              <div className="sl-key">Description</div>
              <div className="sl-val sl-val-editable">
                {isEditingCategoryDescription ? (
                  <span className="sl-desc-edit-container">
                    <input
                      ref={categoryDescriptionInputRef}
                      type="text"
                      className="sl-desc-input"
                      value={editCategoryDescriptionValue}
                      onChange={(e) => setEditCategoryDescriptionValue(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') {
                          e.preventDefault();
                          saveCategoryDescription();
                        } else if (e.key === 'Escape') {
                          cancelEditCategoryDescription();
                        }
                      }}
                    />
                    <button 
                      className="sl-iconbtn" 
                      title="Save" 
                      onMouseDown={(e) => { e.preventDefault(); saveCategoryDescription(); }}
                    >✓</button>
                    <button 
                      className="sl-iconbtn" 
                      title="Cancel" 
                      onMouseDown={(e) => { e.preventDefault(); cancelEditCategoryDescription(); }}
                    >✕</button>
                  </span>
                ) : (
                  <>
                    <span>{selectedCategory.description}</span>
                    <button className="sl-iconbtn sl-iconbtn-inline" title="Edit description" onClick={startEditCategoryDescription}>✏️</button>
                  </>
                )}
              </div>
              <div className="sl-key">Sub-categories</div>
              <div className="sl-val">{selectedCategory.subcategories.length}</div>
              <div className="sl-key">Skills (total)</div>
              <div className="sl-val">{totalSkills}</div>
            </div>
          </div>

          {/* Use TaxonomyCategorySubCategoriesPanel for inline add/edit */}
          <TaxonomyCategorySubCategoriesPanel
            subCategories={subCategoriesForPanel}
            categoryName={selectedCategory.name}
            onCreateSubCategory={handleCreateSubcategory}
            onEditSubCategory={handleEditSubcategory}
            onDeleteSubCategory={handleDeleteSubcategory}
            onBulkDeleteSubCategories={handleBulkDeleteSubcategories}
            onSubCategoryClick={handleSubcategoryTableClick}
          />
        </div>
      </>
    );
  };

  // Render subcategory selected panel (uses SkillsTable)
  const renderSubcategoryPanel = () => {
    if (!selectedCategory || !selectedSubcategory) return renderEmptyState();

    return (
      <>
        <div className="sl-panel-header">
          <div>
            <div className="sl-crumb">{breadcrumb}</div>
            <h1 className="sl-panel-title">
              <span className="sl-pill">SUB-CATEGORY</span>
              {isEditingSubcategoryName ? (
                <span className="sl-title-edit-container">
                  <input
                    ref={subcategoryNameInputRef}
                    type="text"
                    className="sl-title-input"
                    value={editSubcategoryNameValue}
                    onChange={(e) => setEditSubcategoryNameValue(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        e.preventDefault();
                        saveSubcategoryName();
                      } else if (e.key === 'Escape') {
                        cancelEditSubcategoryName();
                      }
                    }}
                  />
                  <button 
                    className="sl-iconbtn" 
                    title="Save" 
                    onMouseDown={(e) => { e.preventDefault(); saveSubcategoryName(); }}
                  >✓</button>
                  <button 
                    className="sl-iconbtn" 
                    title="Cancel" 
                    onMouseDown={(e) => { e.preventDefault(); cancelEditSubcategoryName(); }}
                  >✕</button>
                </span>
              ) : (
                <>
                  <span className="sl-title-text">{selectedSubcategory.name}</span>
                  <span className="sl-title-actions">
                    <button className="sl-iconbtn sl-iconbtn-sm" title="Edit sub-category name" onClick={startEditSubcategoryName}>✏️</button>
                    <button className="sl-iconbtn sl-iconbtn-sm sl-iconbtn-danger" title="Delete sub-category" onClick={handleDeleteSubcategoryClick}>🗑️</button>
                  </span>
                </>
              )}
            </h1>
          </div>
        </div>

        <div className="sl-panel-body">
          <div className="sl-kv">
            <div className="sl-k">Details</div>
            <div className="sl-kv-grid">
              <div className="sl-key">Category</div>
              <div className="sl-val">{selectedCategory.name}</div>
              <div className="sl-key">Skills</div>
              <div className="sl-val">{selectedSubcategorySkills.length}</div>
              <div className="sl-key">Description</div>
              <div className="sl-val">
                {isEditingSubcategoryDescription ? (
                  <span className="sl-desc-edit-container">
                    <input
                      ref={subcategoryDescriptionInputRef}
                      type="text"
                      className="sl-desc-input"
                      value={editSubcategoryDescriptionValue}
                      onChange={(e) => setEditSubcategoryDescriptionValue(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Escape') cancelEditSubcategoryDescription();
                        if (e.key === 'Enter') saveSubcategoryDescription();
                      }}
                      onBlur={() => {
                        // Small delay to allow button clicks to process
                        setTimeout(() => {
                          if (isEditingSubcategoryDescription) cancelEditSubcategoryDescription();
                        }, 150);
                      }}
                      autoComplete="off"
                    />
                    <button
                      className="sl-iconbtn sl-iconbtn-inline"
                      title="Save"
                      onMouseDown={(e) => { e.preventDefault(); saveSubcategoryDescription(); }}
                    >✓</button>
                    <button
                      className="sl-iconbtn sl-iconbtn-inline"
                      title="Cancel"
                      onMouseDown={(e) => { e.preventDefault(); cancelEditSubcategoryDescription(); }}
                    >✕</button>
                  </span>
                ) : (
                  <span className="sl-editable-desc" onClick={startEditSubcategoryDescription} title="Click to edit">
                    {selectedSubcategory.description || 'No description provided.'}
                    <button className="sl-iconbtn sl-iconbtn-inline" title="Edit description" onClick={startEditSubcategoryDescription}>✏️</button>
                  </span>
                )}
              </div>
            </div>
          </div>

          {/* Skills section header with search and add button */}
          <div className="sl-list-head">
            <div className="sl-list-title">Skills in this sub-category</div>
            <div className="sl-list-actions">
              {selectedSubcategorySkills.length > 0 && (
                <div className="sl-mini-search">
                  <Search size={14} style={{ color: 'var(--sl-sub, #64748b)', flexShrink: 0 }} />
                  <input
                    type="text"
                    placeholder="Search skills..."
                    value={skillSearchQuery}
                    onChange={(e) => setSkillSearchQuery(e.target.value)}
                  />
                </div>
              )}
              {selectedSkillIds.size > 0 && (
                <button 
                  className="sl-btn ghost danger"
                  onClick={handleHeaderBulkDeleteClick}
                  title={`Delete ${selectedSkillIds.size} selected skill(s)`}
                >
                  🗑️ Delete Selected
                </button>
              )}
              <button className="sl-btn subtle" onClick={handleStartAddSkill} disabled={isAddingSkill}>
                {isAddingSkill ? 'Adding...' : '+ Add Skill'}
              </button>
            </div>
          </div>

          {/* Use SkillsTable for inline add/edit */}
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
        </div>
      </>
    );
  };

  // Render panel based on selection
  const renderPanel = () => {
    if (!selected.type) return renderEmptyState();
    if (selected.type === 'category') return renderCategoryPanel();
    if (selected.type === 'subcategory') return renderSubcategoryPanel();
    return renderEmptyState();
  };

  // ═══════════════════════════════════════════════════════════════════════════
  // MAIN RENDER
  // ═══════════════════════════════════════════════════════════════════════════

  return (
    <div className="skill-library">
      {/* Import blocking overlay */}
      {importOverlay.visible && (
        <ImportBlockingOverlay message={importOverlay.message} />
      )}

      {/* Topbar */}
      <header className="sl-topbar">
        <div className="sl-topbar-left">
          <div className="sl-title">Skill Library</div>
          <div className="sl-subtitle">Govern categories, sub-categories, and skills used across the organization</div>
        </div>
        <div className="sl-topbar-actions">
          <button className="sl-btn ghost" onClick={handleDownloadTemplate}>
            <span>⬇️</span>Download Template
          </button>
          <button className="sl-btn ghost" onClick={handleImportSkills}>
            <span>⬆️</span>Import Skills
          </button>
          <button className="sl-btn" onClick={handleAddCategory}>+ Add Category</button>
        </div>
      </header>

      {/* Error banner */}
      {error && (
        <div className="sl-error-banner">
          ⚠️ {error}
          <button onClick={() => setError(null)}>✕</button>
        </div>
      )}

      {/* Content */}
      <section className="sl-content">
        <div className="sl-grid">
          {/* Left: Tree */}
          <section className="sl-card">
            <div className="sl-card-h">
              <div className="sl-card-h-left">
                <div className="sl-h-title">Categories</div>
                <div className="sl-h-sub">Browse and select a category</div>
              </div>
            </div>

            <div className="sl-search">
              <input
                className="sl-input"
                placeholder="Search categories or sub-categories..."
                value={treeQuery}
                onChange={(e) => setTreeQuery(e.target.value)}
              />
            </div>

            <div className="sl-tree">
              {renderTree()}
            </div>
          </section>

          {/* Right: Details/List Panel */}
          <section className="sl-card sl-panel">
            {renderPanel()}
          </section>
        </div>
      </section>

      {/* Modals */}
      <CreateEditModal
        isOpen={createModalOpen}
        onClose={() => {
          setCreateModalOpen(false);
          setCreateModalError(null);
        }}
        mode="create"
        itemType="category"
        onSubmit={handleCreateCategory}
        parentOptions={[]}
        error={createModalError}
      />

      <DeleteConfirmModal
        isOpen={deleteModalOpen}
        onClose={() => {
          setDeleteModalOpen(false);
          setDeleteTarget(null);
        }}
        itemName={deleteTarget?.name}
        onConfirm={handleConfirmDelete}
      />

      <DependencyModal
        isOpen={dependencyModalOpen}
        onClose={handleCloseDependencyModal}
        itemName={dependencyInfo.itemName}
        dependencies={dependencyInfo.dependencies}
      />

      <ImportModal
        isOpen={importModalOpen}
        onClose={() => setImportModalOpen(false)}
        itemType="Skills"
        onImport={handleImport}
      />
    </div>
  );
};

export default SkillLibraryPage;
