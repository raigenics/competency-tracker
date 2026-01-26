import React, { useState } from 'react';
import { ChevronDown, ChevronRight, Folder, FolderOpen, Tag } from 'lucide-react';

const TaxonomyTree = ({ skillTree, onSkillSelect, selectedSkill }) => {
  const [expandedCategories, setExpandedCategories] = useState(new Set());
  const [expandedSubcategories, setExpandedSubcategories] = useState(new Set());

  const toggleCategory = (categoryId) => {
    const newExpanded = new Set(expandedCategories);
    if (newExpanded.has(categoryId)) {
      newExpanded.delete(categoryId);
    } else {
      newExpanded.add(categoryId);
    }
    setExpandedCategories(newExpanded);
  };

  const toggleSubcategory = (subcategoryId) => {
    const newExpanded = new Set(expandedSubcategories);
    if (newExpanded.has(subcategoryId)) {
      newExpanded.delete(subcategoryId);
    } else {
      newExpanded.add(subcategoryId);
    }
    setExpandedSubcategories(newExpanded);
  };

  const CategoryItem = ({ category }) => {
    const isExpanded = expandedCategories.has(category.id);
    const skillCount = category.subcategories.reduce((total, sub) => total + sub.skills.length, 0);

    return (
      <div className="mb-2">
        <button
          onClick={() => toggleCategory(category.id)}
          className="flex items-center gap-2 w-full text-left p-2 rounded-lg hover:bg-gray-100 group"
        >
          {isExpanded ? (
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
            {category.name}
          </span>
          <span className="text-sm text-gray-500 ml-auto">
            {skillCount} skills
          </span>
        </button>

        {isExpanded && (
          <div className="ml-6 mt-2 space-y-1">
            {category.subcategories.map((subcategory) => (
              <SubcategoryItem key={subcategory.id} subcategory={subcategory} />
            ))}
          </div>
        )}
      </div>
    );
  };

  const SubcategoryItem = ({ subcategory }) => {
    const isExpanded = expandedSubcategories.has(subcategory.id);

    return (
      <div>
        <button
          onClick={() => toggleSubcategory(subcategory.id)}
          className="flex items-center gap-2 w-full text-left p-2 rounded-lg hover:bg-gray-50 group"
        >
          {isExpanded ? (
            <ChevronDown className="h-3 w-3 text-gray-600" />
          ) : (
            <ChevronRight className="h-3 w-3 text-gray-600" />
          )}
          <Tag className="h-4 w-4 text-green-600" />
          <span className="text-sm font-medium text-gray-700 group-hover:text-green-600">
            {subcategory.name}
          </span>
          <span className="text-xs text-gray-500 ml-auto">
            {subcategory.skills.length}
          </span>
        </button>

        {isExpanded && (
          <div className="ml-6 mt-1 space-y-1">
            {subcategory.skills.map((skill) => (
              <SkillItem 
                key={skill.id} 
                skill={skill} 
                isSelected={selectedSkill?.id === skill.id}
                onClick={() => onSkillSelect(skill)}
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
        className={`flex items-center gap-2 w-full text-left p-2 rounded-lg transition-colors ${
          isSelected 
            ? 'bg-blue-100 text-blue-900 border border-blue-300' 
            : 'hover:bg-gray-50 text-gray-700 hover:text-gray-900'
        }`}
      >
        <div className={`w-2 h-2 rounded-full ${isSelected ? 'bg-blue-600' : 'bg-gray-400'}`} />
        <span className="text-sm">{skill.name}</span>
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
