export default function DotSpinner({ size = "md" }) {
  const sizeClass = size === "sm" ? "dot-spinner-sm" : "dot-spinner";

  return (
    <div className={sizeClass}>
      {Array.from({ length: 8 }).map((_, index) => (
        <div key={index} className="dot-spinner__dot" />
      ))}
    </div>
  );
}