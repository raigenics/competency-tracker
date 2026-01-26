const LoadingState = ({ message = "Loading..." }) => {
  return (
    <div className="flex items-center justify-center p-12">
      <div className="text-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
        <p className="text-slate-600">{message}</p>
      </div>
    </div>
  );
};

export default LoadingState;
