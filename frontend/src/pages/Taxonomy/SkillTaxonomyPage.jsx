import React, { useState, useEffect, useRef } from 'react';
import { Search, TreePine } from 'lucide-react';
import TaxonomyTree from './components/TaxonomyTree';
import SkillDetailsPanel from './components/SkillDetailsPanel';
import LoadingState from '../../components/LoadingState';
import { skillApi } from '../../services/api/skillApi';
import useCapabilityOverviewStore from './capabilityOverviewStore';

const SkillTaxonomyPage = () => {
  // Page-scoped store for state persistence across navigation
  // Use selective subscriptions to prevent infinite update loops
  const skillTreeCached = useCapabilityOverviewStore(s => s.skillTree);
  const filteredTreeCached = useCapabilityOverviewStore(s => s.filteredTree);
  const selectedSkillCached = useCapabilityOverviewStore(s => s.selectedSkill);
  const searchTermCached = useCapabilityOverviewStore(s => s.searchTerm);
  const showViewAllCached = useCapabilityOverviewStore(s => s.showViewAll);
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
  const isRestoringScroll = useRef(false);
  
  const [skillTree, setSkillTree] = useState(skillTreeCached || []);
  const [selectedSkill, setSelectedSkill] = useState(selectedSkillCached || null);
  const [isLoading, setIsLoading] = useState(!hasCachedData);
  const [searchTerm, setSearchTerm] = useState(searchTermCached || '');
  const [filteredTree, setFilteredTree] = useState(filteredTreeCached || []);
  const [showViewAll, setShowViewAll] = useState(showViewAllCached || false);
  useEffect(() => {
    loadSkillTaxonomy();
  }, []);

  useEffect(() => {
    if (searchTerm) {
      filterSkillTree(searchTerm);
    } else {
      setFilteredTree(skillTree);
    }
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
        isRestoringScroll.current = false;
      });
    }
  }, [isLoading, skillTree.length, hasCachedData, leftPanelScrollTopCached, rightPanelScrollTopCached]);
    // Save scroll position when unmounting or navigating away
  useEffect(() => {
    return () => {
      // Use getState() to avoid subscription loops during unmount
      const { setLeftPanelScrollTop, setRightPanelScrollTop } = useCapabilityOverviewStore.getState();
      
      if (leftPanelRef.current) {
        setLeftPanelScrollTop(leftPanelRef.current.scrollTop);
      }
      if (rightPanelRef.current) {
        setRightPanelScrollTop(rightPanelRef.current.scrollTop);
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
      
      console.log(`Loaded ${subcategories.length} subcategories for category ${categoryId}`);
    } catch (error) {
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

  const filterSkillTree = (term) => {
    const lowerTerm = term.toLowerCase();
    
    const filtered = skillTree.map(category => {
      const categoryMatches = category.name.toLowerCase().includes(lowerTerm);
      
      // Filter subcategories and their skills
      const filteredSubcategories = category.subcategories.map(subcategory => {
        const subcategoryMatches = subcategory.name.toLowerCase().includes(lowerTerm);
        
        // Filter skills within this subcategory
        const filteredSkills = subcategory.skills.filter(skill =>
          skill.name.toLowerCase().includes(lowerTerm) ||
          skill.description?.toLowerCase().includes(lowerTerm)
        );
        
        // Include subcategory if:
        // 1. Category matches (show all subcategories under matching category)
        // 2. Subcategory name matches (show all skills under matching subcategory)
        // 3. At least one skill matches (show only matching skills)
        if (categoryMatches) {
          return { ...subcategory, expanded: true }; // Show all skills
        } else if (subcategoryMatches) {
          return { ...subcategory, skills: subcategory.skills, expanded: true }; // Show all skills in matching subcategory
        } else if (filteredSkills.length > 0) {
          return { ...subcategory, skills: filteredSkills, expanded: true }; // Show only matching skills
        }
        return null;
      }).filter(Boolean);

      // Include category if it matches or has matching subcategories
      if (categoryMatches || filteredSubcategories.length > 0) {
        return {
          ...category,
          subcategories: filteredSubcategories,
          expanded: true // Auto-expand for search results
        };
      }
      return null;    }).filter(Boolean);    setFilteredTree(filtered);
    
    // Update store with filtered results
    setFilteredTreeStore(filtered);
  };  const handleSkillSelect = async (skill) => {
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
      }        // TODO: Load additional skill details from API
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

  // Compute taxonomy counts from filtered tree
  const taxonomyCounts = React.useMemo(() => {
    const categories = filteredTree.length;
    const subCategories = filteredTree.reduce((sum, category) => 
      sum + (category.subcategories?.length || 0), 0
    );
    const skills = filteredTree.reduce((sum, category) => 
      sum + (category.subcategories?.reduce((subSum, sub) => 
        subSum + (sub.skills?.length || 0), 0) || 0), 0
    );
    return { categories, subCategories, skills };
  }, [filteredTree]);

  if (isLoading) {
    return <LoadingState message="Loading skill taxonomy..." />;
  }return (
    <div className="p-8 bg-slate-50 min-h-screen">
      <div className="max-w-screen-2xl mx-auto">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-slate-900 mb-2">Skill Overview</h1>
          <p className="text-slate-600">
            Browse and explore organizational capabilities and skill structure
          </p>
        </div>

        {/* Search Bar */}
        <div className="mb-6">
          <div className="relative max-w-md">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400" />            <input
              type="text"
              placeholder="Search categories, subcategories, or skills..."              value={searchTerm}
              onChange={handleSearchChange}
              className="w-full pl-10 pr-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            /></div>        </div>        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 lg:h-[calc(100vh-280px)] lg:overflow-hidden lg:min-h-0">
          {/* Skill Tree - Adjusted width */}
          <div className="lg:col-span-5 h-full min-h-0">            <div className="bg-white rounded-lg border border-slate-200 h-full flex flex-col min-h-0">
              <div className="border-b border-slate-200 p-6">
                <h2 className="text-lg font-semibold text-slate-900 flex items-center gap-2">
                  <TreePine className="h-5 w-5" />
                  Capability Structure
                </h2>
                <p className="text-sm text-slate-600 mt-1">
                  {searchTerm ? `Showing results for "${searchTerm}"` : 'Category → Sub-Category → Skills'}
                </p>
                
                {/* Summary Counts */}
                <div className="flex items-center gap-3 mt-3">
                  <div className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-slate-100 rounded-md">
                    <span className="text-xs font-medium text-slate-700">{taxonomyCounts.categories}</span>
                    <span className="text-xs text-slate-500">Categories</span>
                  </div>
                  <div className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-slate-100 rounded-md">
                    <span className="text-xs font-medium text-slate-700">{taxonomyCounts.subCategories}</span>
                    <span className="text-xs text-slate-500">Sub-Categories</span>
                  </div>
                  <div className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-slate-100 rounded-md">
                    <span className="text-xs font-medium text-slate-700">{taxonomyCounts.skills}</span>
                    <span className="text-xs text-slate-500">Skills</span>
                  </div>                </div>
              </div>              <div ref={leftPanelRef} className="p-6 pb-12 flex-1 overflow-y-auto min-h-0">
                <TaxonomyTree 
                  skillTree={filteredTree} 
                  onSkillSelect={handleSkillSelect}
                  selectedSkill={selectedSkill}
                  searchTerm={searchTerm}
                  onLoadSubcategories={loadSubcategories}
                  onLoadSkills={loadSkills}
                />
              </div>
            </div>
          </div>{/* Skill Details Panel - Expanded width */}
          <div className="lg:col-span-7 h-full min-h-0">
            <div ref={rightPanelRef} className="h-full overflow-y-auto min-h-0">
              <SkillDetailsPanel 
                skill={selectedSkill}
                showViewAll={showViewAll}
                onViewAll={handleViewAll}
                onBackToSummary={handleBackToSummary}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SkillTaxonomyPage;
