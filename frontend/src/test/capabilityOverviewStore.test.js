/**
 * Unit tests for capabilityOverviewStore
 * Tests Zustand store actions and state management for Capability Overview page
 */
import { describe, it, expect, beforeEach } from 'vitest';
import useCapabilityOverviewStore from '../pages/Taxonomy/capabilityOverviewStore';

describe('useCapabilityOverviewStore', () => {
  // Reset store state before each test
  beforeEach(() => {
    useCapabilityOverviewStore.getState().clearCache();
  });

  describe('initial state', () => {
    it('should have correct initial values', () => {
      const state = useCapabilityOverviewStore.getState();
      
      expect(state.skillTree).toBeNull();
      expect(state.filteredTree).toBeNull();
      expect(state.selectedSkill).toBeNull();
      expect(state.searchTerm).toBe('');
      expect(state.showViewAll).toBe(false);
      expect(state.leftPanelScrollTop).toBe(0);
      expect(state.rightPanelScrollTop).toBe(0);
      expect(state.hasCachedData).toBe(false);
    });
  });

  describe('setSkillTree', () => {
    it('should set skillTree and hasCachedData to true', () => {
      const mockTree = [
        { id: 1, name: 'Category 1', subcategories: [] }
      ];
      
      useCapabilityOverviewStore.getState().setSkillTree(mockTree);
      const state = useCapabilityOverviewStore.getState();
      
      expect(state.skillTree).toEqual(mockTree);
      expect(state.hasCachedData).toBe(true);
    });

    it('should handle null skillTree', () => {
      useCapabilityOverviewStore.getState().setSkillTree(null);
      const state = useCapabilityOverviewStore.getState();
      
      expect(state.skillTree).toBeNull();
      expect(state.hasCachedData).toBe(true);
    });

    it('should handle complex tree structure', () => {
      const complexTree = [
        {
          id: 1,
          name: 'Programming',
          subcategories: [
            {
              id: 101,
              name: 'Languages',
              skills: [
                { id: 1001, name: 'Python' },
                { id: 1002, name: 'JavaScript' }
              ]
            }
          ]
        }
      ];
      
      useCapabilityOverviewStore.getState().setSkillTree(complexTree);
      
      expect(useCapabilityOverviewStore.getState().skillTree).toEqual(complexTree);
    });
  });

  describe('setFilteredTree', () => {
    it('should set filteredTree', () => {
      const filteredTree = [{ id: 1, name: 'Filtered Category' }];
      
      useCapabilityOverviewStore.getState().setFilteredTree(filteredTree);
      
      expect(useCapabilityOverviewStore.getState().filteredTree).toEqual(filteredTree);
    });

    it('should set filteredTree to null', () => {
      // First set a value
      useCapabilityOverviewStore.getState().setFilteredTree([{ id: 1 }]);
      // Then set to null
      useCapabilityOverviewStore.getState().setFilteredTree(null);
      
      expect(useCapabilityOverviewStore.getState().filteredTree).toBeNull();
    });
  });

  describe('setSelectedSkill', () => {
    it('should set selectedSkill', () => {
      const mockSkill = { id: 100, name: 'React', category_id: 1 };
      
      useCapabilityOverviewStore.getState().setSelectedSkill(mockSkill);
      
      expect(useCapabilityOverviewStore.getState().selectedSkill).toEqual(mockSkill);
    });

    it('should clear selectedSkill when set to null', () => {
      useCapabilityOverviewStore.getState().setSelectedSkill({ id: 1 });
      useCapabilityOverviewStore.getState().setSelectedSkill(null);
      
      expect(useCapabilityOverviewStore.getState().selectedSkill).toBeNull();
    });
  });

  describe('setSearchTerm', () => {
    it('should set searchTerm', () => {
      useCapabilityOverviewStore.getState().setSearchTerm('python');
      
      expect(useCapabilityOverviewStore.getState().searchTerm).toBe('python');
    });

    it('should set empty searchTerm', () => {
      useCapabilityOverviewStore.getState().setSearchTerm('test');
      useCapabilityOverviewStore.getState().setSearchTerm('');
      
      expect(useCapabilityOverviewStore.getState().searchTerm).toBe('');
    });

    it('should handle special characters in searchTerm', () => {
      useCapabilityOverviewStore.getState().setSearchTerm('C++/C#');
      
      expect(useCapabilityOverviewStore.getState().searchTerm).toBe('C++/C#');
    });
  });

  describe('setShowViewAll', () => {
    it('should set showViewAll to true', () => {
      useCapabilityOverviewStore.getState().setShowViewAll(true);
      
      expect(useCapabilityOverviewStore.getState().showViewAll).toBe(true);
    });

    it('should set showViewAll to false', () => {
      useCapabilityOverviewStore.getState().setShowViewAll(true);
      useCapabilityOverviewStore.getState().setShowViewAll(false);
      
      expect(useCapabilityOverviewStore.getState().showViewAll).toBe(false);
    });
  });

  describe('setLeftPanelScrollTop', () => {
    it('should set leftPanelScrollTop', () => {
      useCapabilityOverviewStore.getState().setLeftPanelScrollTop(150);
      
      expect(useCapabilityOverviewStore.getState().leftPanelScrollTop).toBe(150);
    });

    it('should not update state if value is the same', () => {
      useCapabilityOverviewStore.getState().setLeftPanelScrollTop(100);
      const stateBefore = useCapabilityOverviewStore.getState();
      
      useCapabilityOverviewStore.getState().setLeftPanelScrollTop(100);
      const stateAfter = useCapabilityOverviewStore.getState();
      
      // Since value is the same, the state object should be identical
      expect(stateAfter.leftPanelScrollTop).toBe(stateBefore.leftPanelScrollTop);
    });

    it('should update state when value changes', () => {
      useCapabilityOverviewStore.getState().setLeftPanelScrollTop(100);
      useCapabilityOverviewStore.getState().setLeftPanelScrollTop(200);
      
      expect(useCapabilityOverviewStore.getState().leftPanelScrollTop).toBe(200);
    });
  });

  describe('setRightPanelScrollTop', () => {
    it('should set rightPanelScrollTop', () => {
      useCapabilityOverviewStore.getState().setRightPanelScrollTop(250);
      
      expect(useCapabilityOverviewStore.getState().rightPanelScrollTop).toBe(250);
    });

    it('should not update state if value is the same', () => {
      useCapabilityOverviewStore.getState().setRightPanelScrollTop(150);
      const stateBefore = useCapabilityOverviewStore.getState();
      
      useCapabilityOverviewStore.getState().setRightPanelScrollTop(150);
      const stateAfter = useCapabilityOverviewStore.getState();
      
      expect(stateAfter.rightPanelScrollTop).toBe(stateBefore.rightPanelScrollTop);
    });

    it('should update state when value changes', () => {
      useCapabilityOverviewStore.getState().setRightPanelScrollTop(150);
      useCapabilityOverviewStore.getState().setRightPanelScrollTop(300);
      
      expect(useCapabilityOverviewStore.getState().rightPanelScrollTop).toBe(300);
    });
  });

  describe('restoreState', () => {
    it('should restore partial state', () => {
      useCapabilityOverviewStore.getState().restoreState({
        searchTerm: 'restored search',
        showViewAll: true
      });
      
      const state = useCapabilityOverviewStore.getState();
      expect(state.searchTerm).toBe('restored search');
      expect(state.showViewAll).toBe(true);
    });

    it('should restore full state', () => {
      const fullState = {
        skillTree: [{ id: 1, name: 'Category' }],
        filteredTree: [{ id: 1, name: 'Filtered' }],
        selectedSkill: { id: 100, name: 'Skill' },
        searchTerm: 'search term',
        showViewAll: true,
        leftPanelScrollTop: 100,
        rightPanelScrollTop: 200,
        hasCachedData: true
      };
      
      useCapabilityOverviewStore.getState().restoreState(fullState);
      const state = useCapabilityOverviewStore.getState();
      
      expect(state.skillTree).toEqual(fullState.skillTree);
      expect(state.filteredTree).toEqual(fullState.filteredTree);
      expect(state.selectedSkill).toEqual(fullState.selectedSkill);
      expect(state.searchTerm).toBe(fullState.searchTerm);
      expect(state.showViewAll).toBe(fullState.showViewAll);
      expect(state.leftPanelScrollTop).toBe(fullState.leftPanelScrollTop);
      expect(state.rightPanelScrollTop).toBe(fullState.rightPanelScrollTop);
      expect(state.hasCachedData).toBe(fullState.hasCachedData);
    });

    it('should preserve non-restored properties', () => {
      // Set initial values
      useCapabilityOverviewStore.getState().setSearchTerm('initial');
      useCapabilityOverviewStore.getState().setShowViewAll(true);
      
      // Restore only partial state
      useCapabilityOverviewStore.getState().restoreState({
        leftPanelScrollTop: 500
      });
      
      const state = useCapabilityOverviewStore.getState();
      // Non-restored values should remain
      expect(state.searchTerm).toBe('initial');
      expect(state.showViewAll).toBe(true);
      // Restored value should update
      expect(state.leftPanelScrollTop).toBe(500);
    });
  });

  describe('clearCache', () => {
    it('should reset all state to initial values', () => {
      // Set various state values
      useCapabilityOverviewStore.getState().setSkillTree([{ id: 1 }]);
      useCapabilityOverviewStore.getState().setFilteredTree([{ id: 2 }]);
      useCapabilityOverviewStore.getState().setSelectedSkill({ id: 100 });
      useCapabilityOverviewStore.getState().setSearchTerm('test');
      useCapabilityOverviewStore.getState().setShowViewAll(true);
      useCapabilityOverviewStore.getState().setLeftPanelScrollTop(100);
      useCapabilityOverviewStore.getState().setRightPanelScrollTop(200);
      
      // Clear cache
      useCapabilityOverviewStore.getState().clearCache();
      
      const state = useCapabilityOverviewStore.getState();
      expect(state.skillTree).toBeNull();
      expect(state.filteredTree).toBeNull();
      expect(state.selectedSkill).toBeNull();
      expect(state.searchTerm).toBe('');
      expect(state.showViewAll).toBe(false);
      expect(state.leftPanelScrollTop).toBe(0);
      expect(state.rightPanelScrollTop).toBe(0);
      expect(state.hasCachedData).toBe(false);
    });

    it('should be idempotent', () => {
      useCapabilityOverviewStore.getState().clearCache();
      useCapabilityOverviewStore.getState().clearCache();
      
      const state = useCapabilityOverviewStore.getState();
      expect(state.skillTree).toBeNull();
      expect(state.hasCachedData).toBe(false);
    });
  });

  describe('store integration', () => {
    it('should handle typical user workflow', () => {
      const store = useCapabilityOverviewStore.getState();
      
      // 1. User loads page, taxonomy data is fetched
      const taxonomyData = [
        {
          id: 1,
          name: 'Development',
          subcategories: [
            { id: 101, name: 'Frontend', skills: [{ id: 1001, name: 'React' }] }
          ]
        }
      ];
      store.setSkillTree(taxonomyData);
      expect(useCapabilityOverviewStore.getState().hasCachedData).toBe(true);
      
      // 2. User searches
      useCapabilityOverviewStore.getState().setSearchTerm('react');
      expect(useCapabilityOverviewStore.getState().searchTerm).toBe('react');
      
      // 3. User selects a skill
      const selectedSkill = { id: 1001, name: 'React' };
      useCapabilityOverviewStore.getState().setSelectedSkill(selectedSkill);
      expect(useCapabilityOverviewStore.getState().selectedSkill).toEqual(selectedSkill);
      
      // 4. User scrolls
      useCapabilityOverviewStore.getState().setLeftPanelScrollTop(150);
      
      // 5. User navigates away and comes back - state should be preserved
      const preservedState = useCapabilityOverviewStore.getState();
      expect(preservedState.skillTree).toEqual(taxonomyData);
      expect(preservedState.searchTerm).toBe('react');
      expect(preservedState.selectedSkill).toEqual(selectedSkill);
      expect(preservedState.leftPanelScrollTop).toBe(150);
    });

    it('should handle filtered tree workflow', () => {
      // Set original tree
      const originalTree = [{ id: 1, name: 'All Categories', subcategories: [] }];
      useCapabilityOverviewStore.getState().setSkillTree(originalTree);
      
      // Search filters the tree
      useCapabilityOverviewStore.getState().setSearchTerm('python');
      const filteredTree = [{ id: 2, name: 'Filtered Results', subcategories: [] }];
      useCapabilityOverviewStore.getState().setFilteredTree(filteredTree);
      
      // Both should be available
      const state = useCapabilityOverviewStore.getState();
      expect(state.skillTree).toEqual(originalTree);
      expect(state.filteredTree).toEqual(filteredTree);
      
      // Clear search
      useCapabilityOverviewStore.getState().setSearchTerm('');
      useCapabilityOverviewStore.getState().setFilteredTree(null);
      
      // Original tree still available
      expect(useCapabilityOverviewStore.getState().skillTree).toEqual(originalTree);
      expect(useCapabilityOverviewStore.getState().filteredTree).toBeNull();
    });
  });
});
