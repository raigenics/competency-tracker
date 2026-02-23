import { useNavigate } from 'react-router-dom';

/**
 * SkillDistributionTable - Top Skills by Employee Count
 * 
 * Uses existing API data from dashboardApi.getSkillDistribution
 * 
 * IMPORTANT COLOR RULE (per wireframe):
 * - Expert uses emerald/green (--db-expert: #0f9d73)
 * - Proficient uses teal/cyan (--db-proficient: #0ea5b7) - NOT brand blue
 * - Beginner uses slate/grey (--db-beginner: #94a3b8)
 */
const SkillDistributionTable = ({ skillDistribution, topSkillsCount, scopeLevel }) => {
  const navigate = useNavigate();

  const handleSkillClick = () => {
    navigate('/query');
  };

  return (
    <section className="db-card" style={{ gridColumn: '1 / span 1' }}>
      <div className="db-card-h">
        <div className="left">
          <h4>Top 8 Skills by Employee Count</h4>
          <p>Skills ranked by employee count (filtered view)</p>
        </div>
        
      </div>

      <div className="db-card-b">
        <table className="db-table">
          <thead>
            <tr>
              <th style={{ width: '32%' }}>Skill</th>
              <th style={{ width: '12%' }}>Total</th>
              <th style={{ width: '12%' }}>Expert</th>
              <th style={{ width: '12%' }}>Proficient</th>
              <th>Breakdown</th>
            </tr>
          </thead>
          <tbody>
            {skillDistribution.map((skill, i) => {
              const expertPercent = (skill.expert / skill.total) * 100;
              const proficientPercent = (skill.proficient / skill.total) * 100;
              const otherPercent = 100 - expertPercent - proficientPercent;

              return (
                <tr key={i}>
                  <td className="skill-name">{skill.skill}</td>
                  <td><span className="count">{skill.total}</span></td>
                  <td>
                    {skill.expert} <span className="mini">({expertPercent.toFixed(0)}%)</span>
                  </td>
                  <td>
                    {skill.proficient} <span className="mini">({proficientPercent.toFixed(0)}%)</span>
                  </td>
                  <td>
                    <div className="db-bar" aria-label={`${skill.skill} proficiency breakdown`}>
                      <div className="seg expert" style={{ width: `${expertPercent}%` }}></div>
                      <div className="seg prof" style={{ width: `${proficientPercent}%` }}></div>
                      <div className="seg beg" style={{ width: `${otherPercent}%` }}></div>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>

        <div className="db-legend">
          <div className="key"><span className="swatch expert"></span> Expert</div>
          <div className="key"><span className="swatch prof"></span> Proficient</div>
          <div className="key"><span className="swatch beg"></span> Intermediate/Beginner</div>
        </div>
      </div>
    </section>
  );
};

export default SkillDistributionTable;
