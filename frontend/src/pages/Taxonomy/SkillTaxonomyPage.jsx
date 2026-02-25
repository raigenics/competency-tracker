// Helper: filter out empty categories/subcategories (SRP, pure)
// Option 1: filter using skill_count for lazy-loading support
function filterCapabilityTree(tree) {
  if (!Array.isArray(tree)) return [];
  return tree
    .filter(category => {
      // If skill_count is a number, use it for filtering
      if (typeof category.skill_count === 'number') {
        return category.skill_count > 0;
      }
      // Fallback: compute from loaded subcategories
      if (Array.isArray(category.subcategories)) {
        return category.subcategories.some(sub => {
          if (typeof sub.skill_count === 'number') {
            return sub.skill_count > 0;
          }
          if (Array.isArray(sub.skills)) {
            return sub.skills.length > 0;
          }
          return false;
        });
      }
      return false;
    })
    .map(category => {
      // Filter subcategories using skill_count or skills array
      const subcategories = Array.isArray(category.subcategories)
        ? category.subcategories.filter(sub => {
            if (typeof sub.skill_count === 'number') {
              return sub.skill_count > 0;
            }
            if (Array.isArray(sub.skills)) {
              return sub.skills.length > 0;
            }
            return false;
          })
        : [];
      // Preserve original object, update subcategories
      return {
        ...category,
        subcategories
      };
    });
}
import React, { useState, useEffect, useRef } from 'react';
import { Search, X } from 'lucide-react';
import TaxonomyTree from './components/TaxonomyTree';
import SkillDetailsPanel from './components/SkillDetailsPanel';
import TwoPaneLayout from '../../layouts/TwoPaneLayout.jsx';
import { skillApi } from '../../services/api/skillApi';
import { dropdownApi } from '../../services/api/dropdownApi';
import useCapabilityOverviewStore from './capabilityOverviewStore';
import './CapabilityOverview.css';

// ─────────────────────────────────────────────────────────────────────────────
// LOCAL SKELETON COMPONENTS
// Minimal skeleton placeholders for initial load - keeps shell visible.
// ─────────────────────────────────────────────────────────────────────────────
const skeletonStyle = {
  background: 'linear-gradient(90deg, #e2e8f0 25%, #f1f5f9 50%, #e2e8f0 75%)',
  backgroundSize: '200% 100%',
  animation: 'shimmer 1.5s infinite',
  borderRadius: '6px',
};

// Inject shimmer keyframes once (shared with Dashboard if loaded)
if (typeof document !== 'undefined' && !document.getElementById('taxonomy-skeleton-keyframes')) {
  const style = document.createElement('style');
  style.id = 'taxonomy-skeleton-keyframes';
  style.textContent = `@keyframes shimmer { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }`;
  document.head.appendChild(style);
}

const SkeletonBox = ({ width = '100%', height = '20px', style: extraStyle = {} }) => (
  <div style={{ ...skeletonStyle, width, height, ...extraStyle }} />
);

const TreeSkeleton = () => (
  <div style={{ padding: '12px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
    {/* Category skeletons */}
    {[1, 2, 3, 4].map(i => (
      <div key={i} style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        <SkeletonBox width="60%" height="18px" />
        <div style={{ marginLeft: '20px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
          <SkeletonBox width="45%" height="14px" />
          <SkeletonBox width="50%" height="14px" />
        </div>
      </div>
    ))}
  </div>
);

const DetailsPanelSkeleton = () => (
  <div style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
    <SkeletonBox width="50%" height="22px" />
    <SkeletonBox width="100%" height="14px" />
    <SkeletonBox width="80%" height="14px" />
    <div style={{ marginTop: '16px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
      <SkeletonBox width="100%" height="40px" />
      <SkeletonBox width="100%" height="40px" />
      <SkeletonBox width="100%" height="40px" />
    </div>
  </div>
);

const SkillTaxonomyPage = () => {
  // Page-scoped store for state persistence across navigation
  // Use selective subscriptions to prevent infinite update loops
  const skillTreeCached = useCapabilityOverviewStore(s => s.skillTree);
  const filteredTreeCached = useCapabilityOverviewStore(s => s.filteredTree);
  const searchTermCached = useCapabilityOverviewStore(s => s.searchTerm);
  const hasCachedData = useCapabilityOverviewStore(s => s.hasCachedData);
  const leftPanelScrollTopCached = useCapabilityOverviewStore(s => s.leftPanelScrollTop);
  const rightPanelScrollTopCached = useCapabilityOverviewStore(s => s.rightPanelScrollTop);
  
  // Get setters separately to avoid subscription loops
  const setSkillTreeStore = useCapabilityOverviewStore(s => s.setSkillTree);
  const setFilteredTreeStore = useCapabilityOverviewStore(s => s.setFilteredTree);
  const setSelectedSkillStore = useCapabilityOverviewStore(s => s.setSelectedSkill);
  const setSearchTermStore = useCapabilityOverviewStore(s => s.setSearchTerm);
  const setShowViewAllStore = useCapabilityOverviewStore(s => s.setShowViewAll);
  
  // Refs for scroll restoration
  const leftPanelRef = useRef(null);
  const rightPanelRef = useRef(null);
  const treeRef = useRef(null);
  const isRestoringScroll = useRef(false);
  const [skillTree, setSkillTree] = useState(skillTreeCached || []);
  // Always start with no skill selected - user must explicitly click to select
  const [selectedSkill, setSelectedSkill] = useState(null);
  const [isLoading, setIsLoading] = useState(!hasCachedData);
  const [showLoadingUI, setShowLoadingUI] = useState(false); // Flicker avoidance: only show skeleton after 200ms
  const loadingTimerRef = useRef(null); // Timer for flicker avoidance
  const [searchTerm, setSearchTerm] = useState(searchTermCached || '');
  const [filteredTree, setFilteredTree] = useState(filteredTreeCached || []);
  // Scope data for header
  const [scopeData, setScopeData] = useState(null);
  // KPI data for Capability Overview
  const [kpiData, setKpiData] = useState(null);
  const [kpiLoading, setKpiLoading] = useState(true);
  const [kpiError, setKpiError] = useState(null);
  // Category coverage data for Details panel default state
  const [categoryCoverage, setCategoryCoverage] = useState(null);
  const [categoryCoverageLoading, setCategoryCoverageLoading] = useState(true);
  const [categoryCoverageError, setCategoryCoverageError] = useState(null);
  // Derived: filtered for non-empty nodes
  const visibleTree = React.useMemo(() => filterCapabilityTree(filteredTree), [filteredTree]);

  // Derived: category distribution for bar chart (sorted by skill_count desc)
  const categoryDistribution = React.useMemo(() => {
    if (!skillTree?.length) return [];
    return skillTree
      .filter(cat => cat.skill_count > 0)
      .map(cat => ({
        category_id: cat.category_id,
        category_name: cat.name || cat.category_name,
        skill_count: cat.skill_count
      }))
      .sort((a, b) => b.skill_count - a.skill_count);
  }, [skillTree]);

  // If selected skill is not present in visible tree, clear selection
  React.useEffect(() => {
    if (!selectedSkill) return;
    // Flatten all visible skills
    const allSkills = visibleTree.flatMap(cat =>
      (cat.subcategories || []).flatMap(sub => Array.isArray(sub.skills) ? sub.skills : [])
    );
    const found = allSkills.some(s => s.id === selectedSkill.id || s.skill_id === selectedSkill.skill_id);
    if (!found) {
      setSelectedSkill(null);
      setSelectedSkillStore(null);
    }
  }, [visibleTree, selectedSkill, setSelectedSkillStore]);

  // If selected skill is not present in visible tree, clear selection
  React.useEffect(() => {
    if (!selectedSkill) return;
    // Flatten all visible skills
    const allSkills = visibleTree.flatMap(cat =>
      (cat.subcategories || []).flatMap(sub => sub.skills || [])
    );
    const found = allSkills.some(s => s.id === selectedSkill.id || s.skill_id === selectedSkill.skill_id);
    if (!found) {
      setSelectedSkill(null);
      setSelectedSkillStore(null);
    }
  }, [visibleTree, selectedSkill, setSelectedSkillStore]);
  
  // Always start with summary view, not employee list
  const [showViewAll, setShowViewAll] = useState(false);

  // Flicker avoidance: delay showing loading UI by 200ms to avoid flash on fast loads
  useEffect(() => {
    if (isLoading) {
      loadingTimerRef.current = setTimeout(() => {
        setShowLoadingUI(true);
      }, 200);
    } else {
      // Clear timer and hide loading UI immediately when done
      if (loadingTimerRef.current) {
        clearTimeout(loadingTimerRef.current);
        loadingTimerRef.current = null;
      }
      setShowLoadingUI(false);
    }
    return () => {
      if (loadingTimerRef.current) {
        clearTimeout(loadingTimerRef.current);
      }
    };
  }, [isLoading]);
  
  useEffect(() => {
    loadSkillTaxonomy();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Fetch scope data for header (sub-segments with fullnames + counts)
  useEffect(() => {
    const fetchScopeData = async () => {
      try {
        const data = await dropdownApi.getSubSegmentsScope();
        setScopeData(data);
      } catch (error) {
        console.error('Failed to load scope data:', error);
      }
    };
    fetchScopeData();
  }, []);

  // Fetch KPI data for Capability Overview
  useEffect(() => {
    const fetchKpiData = async () => {
      setKpiLoading(true);
      setKpiError(null);
      try {
        const data = await skillApi.getCapabilityKpis();
        setKpiData(data);
      } catch (error) {
        console.error('Failed to load KPI data:', error);
        setKpiError('Failed to load KPIs');
      } finally {
        setKpiLoading(false);
      }
    };
    fetchKpiData();
  }, []);

  // Fetch category coverage for Details panel default state
  useEffect(() => {
    const fetchCategoryCoverage = async () => {
      setCategoryCoverageLoading(true);
      setCategoryCoverageError(null);
      try {
        const data = await skillApi.getCategoryCoverage();
        setCategoryCoverage(data);
      } catch (error) {
        console.error('Failed to load category coverage:', error);
        setCategoryCoverageError('Failed to load category coverage');
      } finally {
        setCategoryCoverageLoading(false);
      }
    };
    fetchCategoryCoverage();
  }, []);

  // Server-side search effect with debounce
  useEffect(() => {
    const performSearch = async () => {
      // If search term is less than 2 characters, reset to base tree
      if (!searchTerm || searchTerm.trim().length < 2) {
        setFilteredTree(skillTree);
        return;
      }

      try {
        const response = await skillApi.searchSkillsInTaxonomy(searchTerm.trim());
        
        // Build tree from search results
        const searchTree = buildTreeFromSearchResults(response.results || []);
        setFilteredTree(searchTree);
      } catch (error) {
        console.error('Search failed:', error);
        setFilteredTree([]);
      }
    };

    // Debounce search by 300ms
    const timeoutId = setTimeout(performSearch, 300);
    return () => clearTimeout(timeoutId);
  }, [searchTerm, skillTree]);
  
  // Restore scroll position after data is loaded
  useEffect(() => {
    if (!isLoading && skillTree.length > 0 && hasCachedData && !isRestoringScroll.current) {
      isRestoringScroll.current = true;
      
      // Restore scroll positions on next tick to ensure DOM is ready
      requestAnimationFrame(() => {
        if (leftPanelRef.current && leftPanelScrollTopCached > 0) {
          leftPanelRef.current.scrollTop = leftPanelScrollTopCached;
        }
        if (rightPanelRef.current && rightPanelScrollTopCached > 0) {
          rightPanelRef.current.scrollTop = rightPanelScrollTopCached;
        }
        isRestoringScroll.current = false;      });
    }
  }, [isLoading, skillTree.length, hasCachedData, leftPanelScrollTopCached, rightPanelScrollTopCached]);
  
  // Save scroll position when unmounting or navigating away
  useEffect(() => {
    const leftPanel = leftPanelRef.current;
    const rightPanel = rightPanelRef.current;
    
    return () => {
      // Use getState() to avoid subscription loops during unmount
      const { setLeftPanelScrollTop, setRightPanelScrollTop } = useCapabilityOverviewStore.getState();
      
      if (leftPanel) {
        setLeftPanelScrollTop(leftPanel.scrollTop);
      }
      if (rightPanel) {
        setRightPanelScrollTop(rightPanel.scrollTop);
      }
    };
  }, []);
  
  const loadSkillTaxonomy = async () => {
    // If we have cached data, use it instead of fetching
    if (hasCachedData && skillTreeCached) {
      setSkillTree(skillTreeCached);
      setFilteredTree(filteredTreeCached || skillTreeCached);
      setIsLoading(false);
      return;
    }
    
    setIsLoading(true);
    try {
      // Use lazy-loading: fetch only categories with counts
      const response = await skillApi.getCategories();
      
      // Transform API response to match component's expected format
      // Initially, categories have no subcategories (will be loaded on expand)
      const taxonomyData = response.categories.map(category => ({
        id: category.category_id,
        name: category.category_name,
        subcategory_count: category.subcategory_count,
        skill_count: category.skill_count,
        subcategories: [], // Empty initially - lazy load on expand
        isLoaded: false // Track if subcategories have been loaded
      }));

      console.log(`Loaded ${taxonomyData.length} categories (lazy-loading mode)`);
      setSkillTree(taxonomyData);
      setFilteredTree(taxonomyData);
      
      // Cache taxonomy data in store for future navigation
      setSkillTreeStore(taxonomyData);
      setFilteredTreeStore(taxonomyData);
    } catch (error) {
      console.error('Failed to load skill taxonomy:', error);
      // Fallback to empty array on error
      setSkillTree([]);
      setFilteredTree([]);
    } finally {
      setIsLoading(false);
    }
  };

  // Build tree structure from search results with full hierarchy
  const buildTreeFromSearchResults = (results) => {
    if (!results || results.length === 0) {
      return [];
    }

    // Group results by category
    const categoryMap = new Map();
    
    results.forEach(result => {
      const { category_id, category_name, subcategory_id, subcategory_name, skill_id, skill_name } = result;
      
      // Get or create category
      if (!categoryMap.has(category_id)) {
        categoryMap.set(category_id, {
          id: category_id,
          name: category_name,
          subcategories: new Map(),
          expanded: true, // Auto-expand for search results
          isLoaded: true
        });
      }
      
      const category = categoryMap.get(category_id);
      
      // Get or create subcategory
      if (!category.subcategories.has(subcategory_id)) {
        category.subcategories.set(subcategory_id, {
          id: subcategory_id,
          name: subcategory_name,
          skills: [],
          expanded: true, // Auto-expand for search results
          isLoaded: true
        });
      }
      
      const subcategory = category.subcategories.get(subcategory_id);
      
      // Add skill (avoid duplicates)
      if (!subcategory.skills.some(s => s.skill_id === skill_id)) {
        subcategory.skills.push({
          id: skill_id,
          skill_id: skill_id,
          name: skill_name
        });
      }
    });
    
    // Convert maps to arrays
    const tree = Array.from(categoryMap.values()).map(category => ({
      ...category,
      subcategories: Array.from(category.subcategories.values()),
      subcategory_count: category.subcategories.size,
      skill_count: Array.from(category.subcategories.values()).reduce((sum, sub) => sum + sub.skills.length, 0)
    }));
    
    return tree;
  };

  // Lazy-load subcategories when a category is expanded
  const loadSubcategories = async (categoryId) => {
    try {
      console.log(`Lazy-loading subcategories for category ${categoryId}`);
      const response = await skillApi.getSubcategories(categoryId);
      
      // Transform subcategories
      const subcategories = response.subcategories.map(subcategory => ({
        id: subcategory.subcategory_id,
        name: subcategory.subcategory_name,
        skill_count: subcategory.skill_count,
        skills: [], // Empty initially - lazy load on expand
        isLoaded: false // Track if skills have been loaded
      }));
      
      // Update the category in skillTree with loaded subcategories
      const updatedTree = skillTree.map(category => {
        if (category.id === categoryId) {
          return {
            ...category,
            subcategories,
            isLoaded: true
          };
        }
        return category;
      });
      
      setSkillTree(updatedTree);
      setFilteredTree(updatedTree);
      
      // Update cache
      setSkillTreeStore(updatedTree);
      setFilteredTreeStore(updatedTree);
      
      console.log(`Loaded ${subcategories.length} subcategories for category ${categoryId}`);    } catch (error) {
      console.error(`Failed to load subcategories for category ${categoryId}:`, error);
    }
  };

  // Lazy-load skills when a subcategory is expanded
  const loadSkills = async (categoryId, subcategoryId) => {
    try {
      console.log(`Lazy-loading skills for subcategory ${subcategoryId}`);
      const response = await skillApi.getSkills(subcategoryId);
      
      // Transform skills
      const skills = response.skills.map(skill => ({
        id: skill.skill_id,
        skill_id: skill.skill_id,
        name: skill.skill_name
      }));
      
      // Update the subcategory in skillTree with loaded skills
      const updatedTree = skillTree.map(category => {
        if (category.id === categoryId) {
          return {
            ...category,
            subcategories: category.subcategories.map(subcategory => {
              if (subcategory.id === subcategoryId) {
                return {
                  ...subcategory,
                  skills,
                  isLoaded: true
                };
              }
              return subcategory;
            })
          };
        }
        return category;
      });
      
      setSkillTree(updatedTree);
      setFilteredTree(updatedTree);
      
      // Update cache
      setSkillTreeStore(updatedTree);
      setFilteredTreeStore(updatedTree);
        console.log(`Loaded ${skills.length} skills for subcategory ${subcategoryId}`);
    } catch (error) {
      console.error(`Failed to load skills for subcategory ${subcategoryId}:`, error);
    }
  };

  const handleSkillSelect = async (skill) => {
    setSelectedSkill(skill);
    setShowViewAll(false); // Reset to summary view when selecting a new skill
    
    // Update store
    setSelectedSkillStore(skill);
    setShowViewAllStore(false);
    
    try {
      // Normalize skill ID - handle both 'id' (from mock data) and 'skill_id' (from API)
      const skillId = skill?.skill_id || skill?.id;
      if (!skillId) {
        console.warn('Skill selected without valid ID:', skill);
        return;
      }
      
      // TODO: Load additional skill details from API
      const skillDetails = await skillApi.getSkill(skillId);
      setSelectedSkill({ ...skill, ...skillDetails });
      
      // Update store with full skill details
      setSelectedSkillStore({ ...skill, ...skillDetails });
    } catch (error) {
      console.error('Failed to load skill details:', error);
    }
  };
  const handleViewAll = () => {
    setShowViewAll(true);
    setShowViewAllStore(true);
  };
  
  const handleBackToSummary = () => {
    setShowViewAll(false);
    setShowViewAllStore(false);
  };
  
  // Update store when search term changes
  const handleSearchChange = (e) => {
    const newSearchTerm = e.target.value;
    setSearchTerm(newSearchTerm);
    setSearchTermStore(newSearchTerm);
  };

  // Clear search and restore default tree
  const handleClearSearch = () => {
    setSearchTerm('');
    setSearchTermStore('');
  };

  // Expand/collapse all tree nodes
  const handleExpandAll = () => {
    treeRef.current?.expandAll();
  };

  const handleCollapseAll = () => {
    treeRef.current?.collapseAll();
  };

  // Compute taxonomy counts from visible tree (support lazy-loading)
  const _taxonomyCounts = React.useMemo(() => {
    const categories = visibleTree.length;
    // Sub-Categories: use loaded subcategories if present, else fallback to category.subcategory_count
    let subCategories = 0;
    let skills = 0;
    visibleTree.forEach(category => {
      if (Array.isArray(category.subcategories) && category.subcategories.length > 0) {
        subCategories += category.subcategories.length;
        category.subcategories.forEach(sub => {
          if (typeof sub.skill_count === 'number') {
            skills += sub.skill_count;
          } else if (Array.isArray(sub.skills)) {
            skills += sub.skills.length;
          }
        });
      } else if (typeof category.subcategory_count === 'number') {
        subCategories += category.subcategory_count;
        // If subcategories not loaded, use category.skill_count for skills
        if (typeof category.skill_count === 'number') {
          skills += category.skill_count;
        }
      }
    });
    return { categories, subCategories, skills };
  }, [visibleTree]);


  // If selected skill is not present in visible tree, clear selection
  React.useEffect(() => {
    if (!selectedSkill) return;
    // Flatten all visible skills
    const allSkills = visibleTree.flatMap(cat =>
      (cat.subcategories || []).flatMap(sub => sub.skills || [])
    );
    const found = allSkills.some(s => s.id === selectedSkill.id || s.skill_id === selectedSkill.skill_id);
    if (!found) {
      setSelectedSkill(null);
      setSelectedSkillStore(null);
    }
  }, [visibleTree, selectedSkill, setSelectedSkillStore]);

  // Do not use page-level loading return; keep shell rendered for better UX.
  // Skeleton placeholders are shown inline instead of replacing entire content.
  
  // Determine if we should show skeletons (loading AND past the 200ms delay)
  const showSkeletons = isLoading && showLoadingUI;

  // Show empty state ONLY if not loading and visibleTree is truly empty
  const showEmptyState = !isLoading && visibleTree.length === 0;

  // Build scope subtitle for header
  const scopeSubtitle = React.useMemo(() => {
    if (!scopeData) return null;
    
    // Build sub-segment names (use fullname if available, fallback to name)
    const subSegmentNames = (scopeData.sub_segments || [])
      .map(ss => ss.fullname || ss.name)
      .join(', ');
    
    return {
      subSegments: subSegmentNames,
      employees: scopeData.total_employees || 0,
      projects: scopeData.total_projects || 0
    };
  }, [scopeData]);

  return (
    <div className="capability-overview">
      {/* Header matching capabilityOverview.html wireframe */}
      <header className="co-page-header">
        <div className="co-page-header-top">
          <div className="co-page-header-left">
            <h1 className="co-page-title">Capability Overview</h1>
            <p className="co-page-description">
              Browse active capabilities across your organisation. Select a category or skill to explore depth and coverage.
            </p>
          </div>
        </div>
        {/* Metrics strip - shows key stats inline (replaces KPI cards) */}
        <div className="co-metrics-strip">
          <span className="co-metrics-scope">ADT - AU</span>
          <div className="co-metrics-item">
            <span className="co-metrics-value">
              {kpiLoading ? '...' : (kpiError ? '—' : (kpiData?.total_skills ?? '—'))}
            </span>
            <span className="co-metrics-label">skills</span>
          </div>
          <div className="co-metrics-sep" />
          <div className="co-metrics-item">
            <span className="co-metrics-value">
              {/* Employee count from scopeData */}
              {scopeSubtitle?.employees ?? '—'}
            </span>
            <span className="co-metrics-label">employees</span>
          </div>
          <div className="co-metrics-sep" />
          <div className="co-metrics-item">
            <span className="co-metrics-value">
              {kpiLoading ? '...' : (kpiError ? '—' : (kpiData?.avg_proficiency != null ? kpiData.avg_proficiency.toFixed(2) : '—'))}
            </span>
            <span className="co-metrics-label">aver. proficiency</span>
          </div>
          <div className="co-metrics-sep" />
          <div className="co-metrics-item">
            <span className="co-metrics-value">
              {kpiLoading ? '...' : (kpiError ? '—' : (kpiData?.total_certifications ?? '—'))}
            </span>
            <span className="co-metrics-label">certifications</span>
          </div>
        </div>
      </header>
      <div className="co-content">

        {/* Two-Pane Layout: Tree (left) + Details (right) */}
        <TwoPaneLayout
          leftWidth="420px"
          gap="0"
          leftScrollable={true}
          rightScrollable={false}
          leftPaneClassName="co-tree-panel"
          rightPaneClassName="co-detail-pane"
          minHeight="calc(100vh - 180px)"
          leftHeader={
            <div className="co-tree-toolbar">
              {/* Search box */}
              <div className="co-tree-search-box">
                <Search className="co-tree-search-icon" />
                <input
                  type="text"
                  placeholder="Search categories, skills, technologies..."
                  value={searchTerm}
                  onChange={handleSearchChange}
                  disabled={isLoading}
                />
                {searchTerm && (
                  <button
                    onClick={handleClearSearch}
                    className="co-tree-search-clear"
                    aria-label="Clear search"
                  >
                    <X style={{ width: '12px', height: '12px' }} />
                  </button>
                )}
              </div>
              
              {/* Tree actions row */}
              <div className="co-tree-actions-row">
                <div className="co-tree-actions-left">
                  <button className="co-tree-action-btn" onClick={handleExpandAll} disabled={isLoading}>
                    Expand All
                  </button>
                  <button className="co-tree-action-btn" onClick={handleCollapseAll} disabled={isLoading}>
                    Collapse All
                  </button>
                </div>
                <span className="co-tree-path-legend">Category → Sub-Category → Skills</span>
              </div>

              {searchTerm && (
                <p className="co-tree-search-hint">
                  Showing results for "{searchTerm}"
                </p>
              )}
            </div>
          }
          leftPane={
            <div ref={leftPanelRef} className="co-tree-body">
              {/* Organisation Summary button */}
              <button 
                className={`co-org-summary-btn ${!selectedSkill ? 'active' : ''}`}
                onClick={() => handleSkillSelect(null)}
                type="button"
              >
                <span className="co-org-dot"></span>
                Organisation Summary
              </button>
              
              {showSkeletons ? (
                <TreeSkeleton />
              ) : showEmptyState ? (
                <div style={{ textAlign: 'center', padding: '32px 0', color: '#64748b' }}>
                  <p style={{ fontSize: '14px', fontWeight: '500' }}>No skills available to display.</p>
                </div>
              ) : (
                <TaxonomyTree 
                  ref={treeRef}
                  skillTree={visibleTree}
                  onSkillSelect={handleSkillSelect}
                  selectedSkill={selectedSkill}
                  searchTerm={searchTerm}
                  onLoadSubcategories={loadSubcategories}
                  onLoadSkills={loadSkills}
                />
              )}
            </div>
          }
          rightPane={
            <div ref={rightPanelRef} style={{ minHeight: '320px', height: '100%', width: '100%', minWidth: 0, display: 'flex', flexDirection: 'column' }}>
              {showSkeletons ? (
                <DetailsPanelSkeleton />
              ) : (
                <SkillDetailsPanel 
                  skill={selectedSkill}
                  showViewAll={showViewAll}
                  onViewAll={handleViewAll}
                  onBackToSummary={handleBackToSummary}
                  categoryCoverage={categoryCoverage}
                  categoryCoverageLoading={categoryCoverageLoading}
                  categoryCoverageError={categoryCoverageError}
                  kpiData={kpiData}
                  kpiLoading={kpiLoading}
                  kpiError={kpiError}
                  employeeCount={scopeSubtitle?.employees}
                  categoryDistribution={categoryDistribution}
                />
              )}
            </div>
          }
        />
      </div>
    </div>
  );
};

export default SkillTaxonomyPage;
