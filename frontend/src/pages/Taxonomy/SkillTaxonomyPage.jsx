import React, { useState, useEffect } from 'react';
import { Search, TreePine } from 'lucide-react';
import TaxonomyTree from './components/TaxonomyTree';
import SkillDetailsPanel from './components/SkillDetailsPanel';
import LoadingState from '../../components/LoadingState';
import { skillApi } from '../../services/api/skillApi';
import { mockSkillTree } from '../../data/mockSkillTree';

const SkillTaxonomyPage = () => {
  const [skillTree, setSkillTree] = useState([]);
  const [selectedSkill, setSelectedSkill] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filteredTree, setFilteredTree] = useState([]);

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
      // TODO: Replace with actual API call
      const taxonomyData = await new Promise(resolve => 
        setTimeout(() => resolve(mockSkillTree), 500)
      );
      setSkillTree(taxonomyData);
      setFilteredTree(taxonomyData);
    } catch (error) {
      console.error('Failed to load skill taxonomy:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const filterSkillTree = (term) => {
    const filtered = skillTree.map(category => {
      const filteredSubcategories = category.subcategories.map(subcategory => {
        const filteredSkills = subcategory.skills.filter(skill =>
          skill.name.toLowerCase().includes(term.toLowerCase()) ||
          skill.description?.toLowerCase().includes(term.toLowerCase())
        );
        return {
          ...subcategory,
          skills: filteredSkills
        };
      }).filter(subcategory => subcategory.skills.length > 0);

      const categoryMatches = category.name.toLowerCase().includes(term.toLowerCase());
      
      if (categoryMatches || filteredSubcategories.length > 0) {
        return {
          ...category,
          subcategories: categoryMatches ? category.subcategories : filteredSubcategories
        };
      }
      return null;
    }).filter(Boolean);

    setFilteredTree(filtered);
  };

  const handleSkillSelect = async (skill) => {
    setSelectedSkill(skill);
    try {
      // TODO: Load additional skill details from API
      const skillDetails = await skillApi.getSkill(skill.id);
      setSelectedSkill({ ...skill, ...skillDetails });
    } catch (error) {
      console.error('Failed to load skill details:', error);
    }
  };

  if (isLoading) {
    return <LoadingState message="Loading skill taxonomy..." />;
  }
  return (
    <div className="p-8 bg-slate-50 min-h-screen">
      <div className="max-w-screen-2xl mx-auto">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-slate-900 mb-2">Skill Taxonomy</h1>
          <p className="text-slate-600">
            Explore the complete hierarchy of skills and competencies
          </p>
        </div>

        {/* Search Bar */}
        <div className="mb-6">
          <div className="relative max-w-md">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400" />
            <input
              type="text"
              placeholder="Search skills..."              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Skill Tree */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-lg border border-slate-200">
              <div className="border-b border-slate-200 p-6">
                <h2 className="text-lg font-semibold text-slate-900 flex items-center gap-2">
                  <TreePine className="h-5 w-5" />
                  Skill Categories
                </h2>
                <p className="text-sm text-slate-600 mt-1">
                  {searchTerm ? `Showing results for "${searchTerm}"` : 'Complete skill taxonomy'}
                </p>
              </div>
              <div className="p-6">
                <TaxonomyTree 
                  skillTree={filteredTree} 
                  onSkillSelect={handleSkillSelect}
                  selectedSkill={selectedSkill}
                />
              </div>
            </div>
          </div>

          {/* Skill Details Panel */}
          <div className="lg:col-span-1">
            <SkillDetailsPanel skill={selectedSkill} />
          </div>
        </div>
      </div>
    </div>
  );
};

export default SkillTaxonomyPage;
