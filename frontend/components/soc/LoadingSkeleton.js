export default function LoadingSkeleton({ rows = 4 }) {
  return (
    <div className="space-y-3">
      {Array.from({ length: rows }).map((_, index) => (
        <div key={index} className="soc-skeleton h-16 w-full" />
      ))}
    </div>
  );
}
