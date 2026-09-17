import { Link } from "react-router-dom";
import { FileQuestion } from "lucide-react";

export default function NotFound() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center text-center px-6 bg-canvas">
      <div className="h-14 w-14 rounded-full bg-brand-pastel text-brand-deep flex items-center justify-center mb-5">
        <FileQuestion size={26} />
      </div>
      <h1 className="text-2xl font-semibold text-ink">This page couldn't be found</h1>
      <p className="text-inkmuted mt-2 max-w-sm">
        The page you're looking for doesn't exist, or may have moved.
      </p>
      <Link to="/" className="mt-6 bg-brand-deep text-white font-medium px-5 py-2.5 rounded-lg hover:bg-brand-deep/90 transition-colors">
        Back to home
      </Link>
    </div>
  );
}
