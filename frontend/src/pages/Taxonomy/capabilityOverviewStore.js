/**
 * Page-scoped state store for Capability Overview (SkillTaxonomyPage)
 * Preserves taxonomy data, UI state, and scroll position across navigation
 * to avoid re-fetching and losing user context when navigating back from Employee Profile.
 */

import { create } from 'zustand';

const useCapabilityOverviewStore = create((set) => ({
  // Cached taxonomy data (avoids re-fetching on back navigation)
  skillTree: null,
  filteredTree: null,
  
  // UI state
  selectedSkill: null,
  searchTerm: '',
  showViewAll: false,
  
  // Scroll positions (for restoration)
  leftPanelScrollTop: 0,
  rightPanelScrollTop: 0,
  
  // Flag to indicate if we have cached data (prevents loading state flash)
  hasCachedData: false,
  
  // Actions to update state
  setSkillTree: (skillTree) => set({ 
    skillTree, 
    hasCachedData: true 
  }),
  
  setFilteredTree: (filteredTree) => set({ filteredTree }),
  
  setSelectedSkill: (selectedSkill) => set({ selectedSkill }),
  
  setSearchTerm: (searchTerm) => set({ searchTerm }),
    setShowViewAll: (showViewAll) => set({ showViewAll }),
  
  setLeftPanelScrollTop: (leftPanelScrollTop) => set((state) => 
    state.leftPanelScrollTop === leftPanelScrollTop ? state : { leftPanelScrollTop }
  ),
  
  setRightPanelScrollTop: (rightPanelScrollTop) => set((state) => 
    state.rightPanelScrollTop === rightPanelScrollTop ? state : { rightPanelScrollTop }
  ),
  
  // Bulk update for restoration
  restoreState: (state) => set(state),
  
  // Clear cache (for hard refresh scenarios if needed)
  clearCache: () => set({
    skillTree: null,
    filteredTree: null,
    selectedSkill: null,
    searchTerm: '',
    showViewAll: false,
    leftPanelScrollTop: 0,
    rightPanelScrollTop: 0,
    hasCachedData: false
  })
}));

export default useCapabilityOverviewStore;
