import React, { useState, useEffect, useRef } from 'react';
import { ChevronDown, ChevronRight, Folder, FolderOpen, Tag, Loader2 } from 'lucide-react';

const TaxonomyTree = ({ 
  skillTree, 
  onSkillSelect, 
  selectedSkill, 
  searchTerm = '',
  onLoadSubcategories,
  onLoadSkills
}) => {
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
    
    const treeContainer = document.querySelector('.space-y-2');
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

  // Helper function to highlight matching text
  const highlightText = (text, search) => {
    if (!search.trim()) return text;
    
    const parts = text.split(new RegExp(`(${search})`, 'gi'));
    return parts.map((part, index) => 
      part.toLowerCase() === search.toLowerCase() ? (
        <mark key={index} className="bg-yellow-200 font-medium">{part}</mark>
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
      <div className="mb-2">
        <button
          onClick={() => toggleCategory(category.id, category)}
          tabIndex={0}
          className="flex items-center gap-2 w-full text-left p-2 rounded-lg hover:bg-gray-100 group focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
          disabled={isLoading}
        >
          {isLoading ? (
            <Loader2 className="h-4 w-4 text-gray-600 animate-spin" />
          ) : isExpanded ? (
            <ChevronDown className="h-4 w-4 text-gray-600" />
          ) : (
            <ChevronRight className="h-4 w-4 text-gray-600" />
          )}
          {isExpanded ? (
            <FolderOpen className="h-5 w-5 text-blue-600" />
          ) : (
            <Folder className="h-5 w-5 text-blue-600" />
          )}
          <span className="font-medium text-gray-900 group-hover:text-blue-600">
            {highlightText(category.name, searchTerm)}
          </span>
          <span className="text-sm text-gray-500 ml-auto">
            {skillCount} skills
          </span>
        </button>        {isExpanded && category.subcategories && category.subcategories.length > 0 && (
          <div className="ml-6 mt-2 space-y-1">
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
      <div>
        <button
          onClick={() => toggleSubcategory(categoryId, subcategory.id, subcategory)}
          tabIndex={0}
          className="flex items-center gap-2 w-full text-left p-2 rounded-lg hover:bg-gray-50 group focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
          disabled={isLoading}
        >
          {isLoading ? (
            <Loader2 className="h-3 w-3 text-gray-600 animate-spin" />
          ) : isExpanded ? (
            <ChevronDown className="h-3 w-3 text-gray-600" />
          ) : (
            <ChevronRight className="h-3 w-3 text-gray-600" />
          )}
          <Tag className="h-4 w-4 text-green-600" />
          <span className="text-sm font-medium text-gray-700 group-hover:text-green-600">
            {highlightText(subcategory.name, searchTerm)}
          </span>
          <span className="text-xs text-gray-500 ml-auto">
            {subcategory.skill_count || subcategory.skills.length}
          </span>
        </button>        {isExpanded && subcategory.skills && subcategory.skills.length > 0 && (
          <div className="ml-6 mt-1 space-y-1">
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
        className={`flex items-center gap-2 w-full text-left p-2 rounded-lg transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 relative
          ${isSelected
            ? 'bg-blue-50 text-gray-900'
            : 'hover:bg-gray-50 text-gray-900 hover:text-gray-900'}
        `}
        aria-current={isSelected ? 'true' : undefined}
      >
        {/* Left accent for selected */}
        {isSelected && (
          <span className="absolute left-0 top-1 bottom-1 w-1 rounded bg-blue-500" aria-hidden="true"></span>
        )}
        <span className="text-sm ml-2">{highlightText(skill.name, searchTerm)}</span>
        {skill.isCore && (
          <span className="text-xs px-1.5 py-0.5 bg-yellow-100 text-yellow-800 rounded">
            Core
          </span>
        )}
      </button>
    );
  };

  return (
    <div className="space-y-2">
      {skillTree.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          <Folder className="h-12 w-12 mx-auto mb-4 text-gray-400" />
          <p className="text-lg font-medium text-gray-600">No skills found</p>
          <p className="text-sm text-gray-500">Try adjusting your search criteria</p>
        </div>
      ) : (
        skillTree.map((category) => (
          <CategoryItem key={category.id} category={category} />
        ))
      )}
    </div>
  );
};

export default TaxonomyTree;
