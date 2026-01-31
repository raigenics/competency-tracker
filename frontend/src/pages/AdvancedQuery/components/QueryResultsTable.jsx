import React from 'react';
import TalentResultsTable from '../../../components/TalentResultsTable';

/**
 * Wrapper component for backward compatibility
 * Delegates to the reusable TalentResultsTable component
 */
const QueryResultsTable = ({ 
  results, 
  selectedIds = new Set(), 
  onSelectionChange = () => {}
}) => {
  return (
    <TalentResultsTable
      results={results}
      selectedIds={selectedIds}
      onSelectionChange={onSelectionChange}
    />
  );
};

export default QueryResultsTable;
