/**
 * Settings Page
 * =============
 * Placeholder page for System Settings.
 * 
 * Route: /system/settings
 * Section: SYSTEM (Super admin only)
 */

const SettingsPage = () => {
  return (
    <main style={{ padding: '22px' }}>
      <div className="pagehead">
        <h1 style={{ fontSize: '20px', fontWeight: 600, color: '#1e293b', margin: 0 }}>
          Settings
        </h1>
      </div>
      
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
