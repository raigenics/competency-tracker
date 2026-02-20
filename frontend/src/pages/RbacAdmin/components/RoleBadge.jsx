/**
 * Role Badge Component
 * 
 * Displays a role assignment as colored badges showing role name and scope.
 */
const RoleBadge = ({ assignment }) => {
  const { role_name, scope_name } = assignment;

  // Color scheme for role badges (matching HTML spec)
  const getRoleColor = (role) => {
    const colors = {
      'SUPER_ADMIN': 'bg-purple-100 text-purple-800 border-purple-300',
      'SEGMENT_HEAD': 'bg-blue-100 text-blue-800 border-blue-300',
      'SUBSEGMENT_HEAD': 'bg-cyan-100 text-cyan-800 border-cyan-300',
      'PROJECT_MANAGER': 'bg-green-100 text-green-800 border-green-300',
      'TEAM_LEAD': 'bg-yellow-100 text-yellow-800 border-yellow-300',
      'TEAM_MEMBER': 'bg-gray-100 text-gray-800 border-gray-300',
    };
    return colors[role] || 'bg-gray-100 text-gray-800 border-gray-300';
  };

  return (
    <div className="inline-flex items-center gap-1">
      {/* Role Badge */}
      <span
        className={`
          inline-flex px-2 py-1 text-xs font-semibold rounded border
          ${getRoleColor(role_name)}
        `}
      >
        {role_name}
      </span>

      {/* Scope Badge */}
      <span className="inline-flex px-2 py-1 text-xs font-medium rounded bg-gray-100 text-gray-700 border border-gray-300">
        {scope_name || 'All Systems'}
      </span>
    </div>
  );
};

export default RoleBadge;
