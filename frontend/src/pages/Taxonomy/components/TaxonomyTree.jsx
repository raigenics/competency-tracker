import React, { useState, useEffect, useRef, forwardRef, useImperativeHandle } from 'react';
import { Loader2, Folder } from 'lucide-react';

const TaxonomyTree = forwardRef(({ 
  skillTree, 
  onSkillSelect, 
  selectedSkill, 
  searchTerm = '',
  onLoadSubcategories,
  onLoadSkills
}, ref) => {
  const [expandedCategories, setExpandedCategories] = useState(new Set());
  const [expandedSubcategories, setExpandedSubcategories] = useState(new Set());
  const [loadingCategories, setLoadingCategories] = useState(new Set());
  const [loadingSubcategories, setLoadingSubcategories] = useState(new Set());
    // Reference to store scroll position
  const scrollContainerRef = useRef(null);

  // Effect to find and store reference to scroll container
  useEffect(() => {
    // Find the scroll container (parent with overflow-y-auto)
    const findScrollContainer = (element) => {
      if (!element) return null;
      
      const parent = element.parentElement;
      if (!parent) return null;
      
      const style = window.getComputedStyle(parent);
      if (style.overflowY === 'auto' || style.overflowY === 'scroll') {
        return parent;
      }
      
      return findScrollContainer(parent);
    };
    
    const treeContainer = document.querySelector('.co-tree');
    if (treeContainer) {
      scrollContainerRef.current = findScrollContainer(treeContainer);
    }
  }, []);

  // Auto-expand categories and subcategories that have the 'expanded' flag from search results
  // PRESERVE existing expansion state and ADD nodes with 'expanded' flag
  useEffect(() => {
    setExpandedCategories(prev => {
      const updated = new Set(prev); // Start with existing state
      
      skillTree.forEach(category => {
        if (category.expanded) {
          updated.add(category.id);
        }
      });
      
      return updated;
    });
    
    setExpandedSubcategories(prev => {
      const updated = new Set(prev); // Start with existing state
      
      skillTree.forEach(category => {
        if (category.subcategories) {
          category.subcategories.forEach(subcategory => {
            if (subcategory.expanded) {
              updated.add(subcategory.id);
            }
          });
        }
      });
      
      return updated;
    });
  }, [skillTree]);

  // Expose expandAll and collapseAll methods to parent via ref
  useImperativeHandle(ref, () => ({
    expandAll: () => {
      const allCategoryIds = new Set(skillTree.map(cat => cat.id));
      const allSubcategoryIds = new Set();
      skillTree.forEach(cat => {
        if (cat.subcategories) {
          cat.subcategories.forEach(sub => allSubcategoryIds.add(sub.id));
        }
      });
      setExpandedCategories(allCategoryIds);
      setExpandedSubcategories(allSubcategoryIds);
    },
    collapseAll: () => {
      setExpandedCategories(new Set());
      setExpandedSubcategories(new Set());
    }
  }), [skillTree]);

  // Helper function to highlight matching text
  const highlightText = (text, search) => {
    if (!search.trim()) return text;
    
    const parts = text.split(new RegExp(`(${search})`, 'gi'));
    return parts.map((part, index) => 
      part.toLowerCase() === search.toLowerCase() ? (
        <mark key={index} className="co-tree-highlight">{part}</mark>
      ) : (
        part
      )
    );
  };  const toggleCategory = async (categoryId, category) => {
    // Preserve scroll position
    const scrollTop = scrollContainerRef.current?.scrollTop || 0;
    
    const newExpanded = new Set(expandedCategories);
    const wasExpanded = newExpanded.has(categoryId);
    
    if (wasExpanded) {
      newExpanded.delete(categoryId);
    } else {
      newExpanded.add(categoryId);
      
      // Lazy-load subcategories if not already loaded
      if (!category.isLoaded && onLoadSubcategories) {
        setLoadingCategories(prev => new Set(prev).add(categoryId));
        try {
          await onLoadSubcategories(categoryId);
        } finally {
          setLoadingCategories(prev => {
            const next = new Set(prev);
            next.delete(categoryId);
            return next;
          });
        }
      }
    }
    setExpandedCategories(newExpanded);
    
    // Restore scroll position after state update
    requestAnimationFrame(() => {
      if (scrollContainerRef.current) {
        scrollContainerRef.current.scrollTop = scrollTop;
      }
    });
  };
  const toggleSubcategory = async (categoryId, subcategoryId, subcategory) => {
    // Preserve scroll position
    const scrollTop = scrollContainerRef.current?.scrollTop || 0;
    
    const newExpanded = new Set(expandedSubcategories);
    const wasExpanded = newExpanded.has(subcategoryId);
    
    if (wasExpanded) {
      newExpanded.delete(subcategoryId);
    } else {
      newExpanded.add(subcategoryId);
      
      // Lazy-load skills if not already loaded
      if (!subcategory.isLoaded && onLoadSkills) {
        setLoadingSubcategories(prev => new Set(prev).add(subcategoryId));
        try {
          await onLoadSkills(categoryId, subcategoryId);
        } finally {
          setLoadingSubcategories(prev => {
            const next = new Set(prev);
            next.delete(subcategoryId);
            return next;
          });
        }
      }
    }
    setExpandedSubcategories(newExpanded);
    
    // Restore scroll position after state update
    requestAnimationFrame(() => {
      if (scrollContainerRef.current) {
        scrollContainerRef.current.scrollTop = scrollTop;
      }
    });
  };const CategoryItem = ({ category }) => {
    const isExpanded = expandedCategories.has(category.id);
    const isLoading = loadingCategories.has(category.id);
    const skillCount = category.skill_count || category.subcategories.reduce((total, sub) => total + (sub.skill_count || sub.skills.length), 0);

    return (
      <div className="co-tree-node">
        <button
          onClick={() => toggleCategory(category.id, category)}
          tabIndex={0}
          className="co-tree-row"
          disabled={isLoading}
        >
          <div className="co-tree-left">
            {isLoading ? (
              <span className="co-tree-chev">
                <Loader2 className="animate-spin" style={{ width: 11, height: 11 }} />
              </span>
            ) : (
              <span className="co-tree-chev">{isExpanded ? '▼' : '▶'}</span>
            )}
            <span className="co-tree-type">Category</span>
            <span className="co-tree-name">
              {highlightText(category.name, searchTerm)}
            </span>
          </div>
          <div className="co-tree-meta">
            <span className="co-tree-badge">{skillCount} skills</span>
          </div>
        </button>
        {isExpanded && category.subcategories && category.subcategories.length > 0 && (
          <div className="co-tree-children">
            {category.subcategories.map((subcategory) => (
              <SubcategoryItem 
                key={subcategory.id} 
                subcategory={subcategory}
                categoryId={category.id}
                categoryName={category.name}
              />
            ))}
          </div>
        )}
      </div>
    );
  };  const SubcategoryItem = ({ subcategory, categoryId, categoryName }) => {
    const isExpanded = expandedSubcategories.has(subcategory.id);
    const isLoading = loadingSubcategories.has(subcategory.id);

    return (
      <div className="co-tree-node">
        <button
          onClick={() => toggleSubcategory(categoryId, subcategory.id, subcategory)}
          tabIndex={0}
          className="co-tree-row"
          disabled={isLoading}
        >
          <div className="co-tree-left">
            {isLoading ? (
              <span className="co-tree-chev">
                <Loader2 className="animate-spin" style={{ width: 11, height: 11 }} />
              </span>
            ) : (
              <span className="co-tree-chev">{isExpanded ? '▼' : '▶'}</span>
            )}
            <span className="co-tree-type">Sub</span>
            <span className="co-tree-name">
              {highlightText(subcategory.name, searchTerm)}
            </span>
          </div>
          <div className="co-tree-meta">
            <span className="co-tree-badge">{subcategory.skill_count || subcategory.skills.length} skills</span>
          </div>
        </button>
        {isExpanded && subcategory.skills && subcategory.skills.length > 0 && (
          <div className="co-tree-children">
            {subcategory.skills.map((skill) => (
              <SkillItem 
                key={skill.id} 
                skill={skill} 
                isSelected={selectedSkill?.id === skill.id}
                onClick={() => onSkillSelect({
                  ...skill,
                  category: categoryName,
                  subcategory: subcategory.name
                })}
              />
            ))}
          </div>
        )}
      </div>
    );
  };
  const SkillItem = ({ skill, isSelected, onClick }) => {
    return (
      <button
        onClick={onClick}
        tabIndex={0}
        className={`co-tree-row skill ${isSelected ? 'selected' : ''}`}
        aria-current={isSelected ? 'true' : undefined}
      >
        <div className="co-tree-left">
          <span className="co-tree-chev hidden">▶</span>
          <span className="co-tree-type skill">Skill</span>
          <span className="co-tree-name">
            {highlightText(skill.name, searchTerm)}
          </span>
        </div>
        <div className="co-tree-meta">
          {skill.isCore && (
            <span className="co-tree-badge">Core</span>
          )}
        </div>
      </button>
    );
  };

  return (
    <div className="co-tree">
      {skillTree.length === 0 ? (
        <div className="co-tree-empty">
          <Folder className="co-tree-empty-icon" />
          <p className="co-tree-empty-title">No skills found</p>
          <p className="co-tree-empty-subtitle">Try adjusting your search criteria</p>
        </div>
      ) : (
        skillTree.map((category) => (
          <CategoryItem key={category.id} category={category} />
        ))
      )}
    </div>
  );
});

TaxonomyTree.displayName = 'TaxonomyTree';

export default TaxonomyTree;
