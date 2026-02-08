const EmptyState = ({ icon: Icon, title, description, message, action = null }) => {
  return (
    <div className="flex items-center justify-center p-12">
      <div className="text-center">
        {Icon ? (
          <div className="flex items-center justify-center mx-auto mb-4">
            <Icon className="w-12 h-12 text-slate-400" />
          </div>
        ) : (
          <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <div className="w-8 h-8 bg-slate-300 rounded-full"></div>
          </div>
        )}
        <h3 className="text-lg font-semibold text-slate-900 mb-2">{title}</h3>
        <p className="text-sm text-slate-500">{description || message}</p>
        {action && <div className="mt-4">{action}</div>}
      </div>
    </div>
  );
};

export default EmptyState;
