import { ChevronRight } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const OrgCoverageTable = ({ coverageData, onSegmentSelect }) => {
  const navigate = useNavigate();

  const handleRowClick = (segment) => {
    onSegmentSelect(segment);
  };

  const handleExploreClick = () => {
    navigate('/query');
  };

  // Handle loading state
  if (!coverageData || !coverageData.sub_segments) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
        <h3 className="text-lg font-semibold text-slate-900">Organizational Skill Coverage</h3>
        <div className="flex items-center justify-center py-8">
          <div className="text-slate-600">Loading...</div>
        </div>
      </div>
    );
  }

  const { sub_segments, organization_total } = coverageData;

  return (
    <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold text-slate-900">Organizational Skill Coverage</h3>
          <p className="text-sm text-slate-600 mt-1">Employee count by role across sub-segments</p>
        </div>
        <button
          onClick={handleExploreClick}
          className="text-sm text-blue-600 hover:text-blue-700 font-medium flex items-center space-x-1"
        >
          <span>Explore in Detail</span>
          <ChevronRight className="w-4 h-4" />
        </button>
      </div>
      
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 border-b-2 border-slate-200">
            <tr>
              <th className="text-left py-3 px-4 font-semibold text-slate-700">Sub-Segment</th>
              <th className="text-center py-3 px-4 font-semibold text-slate-700">Total</th>
              <th className="text-center py-3 px-4 font-semibold text-slate-700">Frontend Dev</th>
              <th className="text-center py-3 px-4 font-semibold text-slate-700">Backend Dev</th>
              <th className="text-center py-3 px-4 font-semibold text-slate-700">Full Stack</th>
              <th className="text-center py-3 px-4 font-semibold text-slate-700">Cloud Eng</th>
              <th className="text-center py-3 px-4 font-semibold text-slate-700">DevOps</th>
              <th className="text-center py-3 px-4 font-semibold text-slate-700">Certified %</th>
            </tr>
          </thead>          <tbody>
            {sub_segments.map((row, i) => (
              <tr 
                key={i} 
                className="border-b border-slate-100 hover:bg-slate-50 cursor-pointer" 
                onClick={() => handleRowClick(row.sub_segment_name)}
              >
                <td className="py-3 px-4 font-medium text-slate-800">{row.sub_segment_name}</td>
                <td className="py-3 px-4 text-center">
                  <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded font-semibold text-xs">
                    {row.total_employees}
                  </span>
                </td>
                <td className="py-3 px-4 text-center text-slate-700">{row.frontend_dev}</td>
                <td className="py-3 px-4 text-center text-slate-700">{row.backend_dev}</td>
                <td className="py-3 px-4 text-center text-slate-700">{row.full_stack}</td>
                <td className="py-3 px-4 text-center text-slate-700">{row.cloud_eng}</td>
                <td className="py-3 px-4 text-center text-slate-700">{row.devops}</td>
                <td className="py-3 px-4 text-center">
                  <span className={`px-2 py-1 rounded text-xs font-semibold ${
                    row.certified_pct >= 70 ? 'bg-green-100 text-green-700' :
                    row.certified_pct >= 60 ? 'bg-yellow-100 text-yellow-700' :
                    'bg-red-100 text-red-700'
                  }`}>
                    {row.certified_pct}%
                  </span>
                </td>
              </tr>
            ))}
          </tbody>          <tfoot className="bg-slate-50 border-t-2 border-slate-200 font-semibold">
            <tr>
              <td className="py-3 px-4 text-slate-900">Organization Total</td>
              <td className="py-3 px-4 text-center">
                <span className="px-2 py-1 bg-blue-600 text-white rounded font-semibold text-xs">
                  {organization_total.total_employees}
                </span>
              </td>
              <td className="py-3 px-4 text-center text-slate-900">{organization_total.frontend_dev}</td>
              <td className="py-3 px-4 text-center text-slate-900">{organization_total.backend_dev}</td>
              <td className="py-3 px-4 text-center text-slate-900">{organization_total.full_stack}</td>
              <td className="py-3 px-4 text-center text-slate-900">{organization_total.cloud_eng}</td>
              <td className="py-3 px-4 text-center text-slate-900">{organization_total.devops}</td>
              <td className="py-3 px-4 text-center">
                <span className={`px-2 py-1 rounded text-xs font-semibold ${
                  organization_total.certified_pct >= 70 ? 'bg-green-100 text-green-700' :
                  organization_total.certified_pct >= 60 ? 'bg-yellow-100 text-yellow-700' :
                  'bg-red-100 text-red-700'
                }`}>
                  {organization_total.certified_pct}%
                </span>
              </td>
            </tr>
          </tfoot>
        </table>
      </div>
    </div>
  );
};

export default OrgCoverageTable;
