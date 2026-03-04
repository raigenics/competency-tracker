/**
 * Settings Page
 * =============
 * Placeholder page for System Settings.
 * 
 * Route: /system/settings
 * Section: SYSTEM (Super admin only)
 */
import PageHeader from '../../components/PageHeader';

const SettingsPage = () => {
  return (
    <main style={{ padding: '22px' }}>
      <PageHeader
        title="Settings"
        subtitle="Configure system-wide settings"
      />
      
      <div style={{
        marginTop: '24px',
        padding: '40px',
        textAlign: 'center',
        background: '#ffffff',
        border: '1px solid #e2e8f0',
        borderRadius: '12px'
      }}>
        <div style={{ fontSize: '48px', marginBottom: '16px' }}>⚙️</div>
        <h2 style={{ fontSize: '18px', fontWeight: 600, color: '#1e293b', margin: '0 0 8px' }}>
          System Settings
        </h2>
        <p style={{ color: '#64748b', fontSize: '14px', margin: 0 }}>
          This feature is coming soon. Configure system-wide settings.
        </p>
      </div>
    </main>
  );
};

export default SettingsPage;
