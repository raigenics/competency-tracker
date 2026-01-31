const PageHeader = ({ title, subtitle, actions }) => {
  return (
    <div className="bg-white border-b-2 border-[#e2e8f0] px-8 py-6 flex justify-between items-center">
      <div>
        <h1 className="text-2xl font-semibold text-[#1a1a1a]">{title}</h1>
        {subtitle && (
          <p className="text-sm text-[#64748b] mt-1">{subtitle}</p>
        )}
      </div>
      {actions && (
        <div className="flex gap-3">
          {actions}
        </div>
      )}
    </div>
  );
};

export default PageHeader;
