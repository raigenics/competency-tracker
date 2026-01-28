import React, { useState, useEffect } from 'react';
import { Search, TreePine } from 'lucide-react';
import TaxonomyTree from './components/TaxonomyTree';
import SkillDetailsPanel from './components/SkillDetailsPanel';
import LoadingState from '../../components/LoadingState';
import { skillApi } from '../../services/api/skillApi';

const SkillTaxonomyPage = () => {
  const [skillTree, setSkillTree] = useState([]);
  const [selectedSkill, setSelectedSkill] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filteredTree, setFilteredTree] = useState([]);
  const [showViewAll, setShowViewAll] = useState(false);

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
  const loadSkillTaxonomy = async () => {
    setIsLoading(true);
    try {
      // Fetch real taxonomy data from API
      const response = await skillApi.getTaxonomyTree();
      
      // Transform API response to match component's expected format
      const taxonomyData = response.categories.map(category => ({
        id: category.category_id,
        name: category.category_name,
        subcategories: category.subcategories.map(subcategory => ({
          id: subcategory.subcategory_id,
          name: subcategory.subcategory_name,
          skills: subcategory.skills.map(skill => ({
            id: skill.skill_id,        // Real DB skill_id
            skill_id: skill.skill_id,   // Keep both for compatibility
            name: skill.skill_name
          }))
        }))
      }));
      
      console.log(`Loaded ${taxonomyData.length} categories from database`);
      setSkillTree(taxonomyData);
      setFilteredTree(taxonomyData);
    } catch (error) {
      console.error('Failed to load skill taxonomy:', error);
      // Fallback to empty array on error
      setSkillTree([]);
      setFilteredTree([]);
    } finally {
      setIsLoading(false);
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
      return null;
    }).filter(Boolean);

    setFilteredTree(filtered);
  };  const handleSkillSelect = async (skill) => {
    setSelectedSkill(skill);
    setShowViewAll(false); // Reset to summary view when selecting a new skill
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
    } catch (error) {
      console.error('Failed to load skill details:', error);
    }
  };

  const handleViewAll = () => {
    setShowViewAll(true);
  };

  const handleBackToSummary = () => {
    setShowViewAll(false);
  };

  if (isLoading) {
    return <LoadingState message="Loading skill taxonomy..." />;
  }  return (
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
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400" />
            <input
              type="text"
              placeholder="Search categories, subcategories, or skills..."              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        </div>        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Skill Tree - Adjusted width */}
          <div className="lg:col-span-5">
            <div className="bg-white rounded-lg border border-slate-200">
              <div className="border-b border-slate-200 p-6">
                <h2 className="text-lg font-semibold text-slate-900 flex items-center gap-2">
                  <TreePine className="h-5 w-5" />
                  Capability Structure
                </h2>
                <p className="text-sm text-slate-600 mt-1">
                  {searchTerm ? `Showing results for "${searchTerm}"` : 'Category → Sub-Category → Skills'}
                </p>
              </div>
              <div className="p-6">
                <TaxonomyTree 
                  skillTree={filteredTree} 
                  onSkillSelect={handleSkillSelect}
                  selectedSkill={selectedSkill}
                  searchTerm={searchTerm}
                />
              </div>
            </div>
          </div>

          {/* Skill Details Panel - Expanded width */}
          <div className="lg:col-span-7">
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
  );
};

export default SkillTaxonomyPage;
