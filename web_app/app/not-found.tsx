import Link from "next/link";

export default function NotFound() {
  return (
    <div className="min-h-screen bg-slate-950 text-white flex flex-col items-center justify-center p-6 text-center">
      <h2 className="text-4xl font-extrabold text-cyan-400 mb-4">404 - Página no encontrada</h2>
      <p className="text-slate-400 mb-6 max-w-md">
        La página de TruthGPT Cloud que buscas no existe o ha sido trasladada al motor cuántico.
      </p>
      <Link
        href="/"
        className="px-6 py-3 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white rounded-xl font-medium shadow-lg transition-all"
      >
        Volver a TruthGPT Cloud
      </Link>
    </div>
  );
}
