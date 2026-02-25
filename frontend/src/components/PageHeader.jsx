import './PageHeader.css';

/**
 * PageHeader - Standardized page header component
 * 
 * Structure matches headerstyle.html wireframe:
 * <div class="page-header">
 *   <div class="header-left">
 *     <h1 class="page-title">Title</h1>
 *     <p class="page-subtitle">Subtitle</p>
 *   </div>
 *   <div class="header-right">
 *     [utilities/actions]
 *   </div>
 * </div>
 * 
 * @param {string} title - Page title (required)
 * @param {string|ReactNode} subtitle - Optional subtitle/description
 * @param {ReactNode} actions - Optional right-aligned utilities (buttons, pills, etc.)
 */
const PageHeader = ({ title, subtitle, actions }) => {
  // Determine if subtitle/actions are empty for styling
  const hasSubtitle = Boolean(subtitle);
  const hasActions = Boolean(actions);

  return (
    <div className="page-header">
      <div className="header-left">
        <h1 className="page-title">{title}</h1>
        {/* Always render subtitle container to preserve consistent height */}
        <p className={`page-subtitle${hasSubtitle ? '' : ' page-subtitle--empty'}`}>
          {hasSubtitle ? subtitle : '\u00A0'}
        </p>
      </div>
      {/* Always render header-right to preserve layout structure */}
      <div className={`header-right${hasActions ? '' : ' header-right--empty'}`}>
        {actions}
      </div>
    </div>
  );
};

export default PageHeader;
