/**
 * MasterDataLayout - Simple wrapper for Master Data pages
 * Provides the master-data-page class scope and main-content container
 */
import React from 'react';
import '../contentPage.css';

const MasterDataLayout = ({ children }) => {
  return (
    <div className="master-data-page" style={{ height: '100%' }}>
      <div className="main-content">
        {children}
      </div>
    </div>
  );
};

export default MasterDataLayout;
