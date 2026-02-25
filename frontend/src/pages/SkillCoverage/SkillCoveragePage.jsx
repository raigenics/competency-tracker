/**
 * Skill Coverage Page
 * ===================
 * Placeholder page for Skill Coverage feature.
 * 
 * Route: /skill-coverage
 * Section: INSIGHTS
 */
import PageHeader from '../../components/PageHeader';

const SkillCoveragePage = () => {
  return (
    <main style={{ padding: '0 26px 40px' }}>
      <PageHeader
        title="Skill Coverage"
        subtitle="Monitor skill coverage across your organization"
      />
      
      <div style={{
        marginTop: '24px',
        padding: '40px',
        textAlign: 'center',
        background: '#ffffff',
        border: '1px solid #e2e8f0',
        borderRadius: '12px'
      }}>
        <div style={{ fontSize: '48px', marginBottom: '16px' }}>🗺️</div>
        <h2 style={{ fontSize: '18px', fontWeight: 600, color: '#1e293b', margin: '0 0 8px' }}>
          Skill Coverage
        </h2>
        <p style={{ color: '#64748b', fontSize: '14px', margin: 0 }}>
          This feature is coming soon. Monitor skill coverage across your organization.
        </p>
      </div>
    </main>
  );
};

export default SkillCoveragePage;
