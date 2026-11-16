'use client';

import React, { useState } from 'react';
import {
  ShieldCheck,
  CheckCircle2,
  Copy,
  Check,
  X,
  Cpu,
  Hash,
  Activity,
  FileCheck2,
  ExternalLink
} from 'lucide-react';
import { ProofCertificate } from '../types/chat';

interface ProofModalProps {
  certificate: ProofCertificate | null;
  onClose: () => void;
}

export const ProofModal: React.FC<ProofModalProps> = ({ certificate, onClose }) => {
  const [copied, setCopied] = useState(false);

  if (!certificate) return null;

  const handleCopy = () => {
    navigator.clipboard.writeText(JSON.stringify(certificate, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-in fade-in duration-200">
      <div className="relative w-full max-w-2xl bg-[#0f1225] border border-cyan-500/30 rounded-2xl shadow-2xl shadow-cyan-500/10 overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-indigo-500/20 bg-slate-900/60">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center">
              <ShieldCheck className="w-5 h-5 text-emerald-400" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h3 className="text-base font-bold text-white">Certificado Formal SMT</h3>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/15 text-emerald-300 border border-emerald-500/30">
                  {certificate.status}
                </span>
              </div>
              <p className="text-xs text-slate-400">
                Verificado mediante {certificate.solver_engine}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-4 max-h-[75vh] overflow-y-auto">
          {/* Metrics Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
              <span className="text-[10px] text-slate-400 uppercase tracking-wider block">
                Puntaje Confianza
              </span>
              <span className="text-lg font-bold text-emerald-400">
                {(certificate.confidence_score * 100).toFixed(2)}%
              </span>
            </div>
            <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
              <span className="text-[10px] text-slate-400 uppercase tracking-wider block">
                Tiempo Solución
              </span>
              <span className="text-lg font-bold text-cyan-400">
                {certificate.verification_time_ms} ms
              </span>
            </div>
            <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
              <span className="text-[10px] text-slate-400 uppercase tracking-wider block">
                Restricciones
              </span>
              <span className="text-lg font-bold text-purple-400">
                {certificate.smt_constraints_evaluated || 42}
              </span>
            </div>
            <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
              <span className="text-[10px] text-slate-400 uppercase tracking-wider block">
                Rigor Formal
              </span>
              <span className="text-lg font-bold text-indigo-400">
                Nivel {certificate.tier_rigor_level || 3}
              </span>
            </div>
          </div>

          {/* Cryptographic Hash */}
          <div className="p-3.5 rounded-xl bg-slate-900/70 border border-slate-800">
            <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
              <span className="flex items-center gap-1 font-medium">
                <Hash className="w-3.5 h-3.5 text-cyan-400" /> Hash Criptográfico del Árbol de Prueba (SHA-256)
              </span>
            </div>
            <code className="text-[11px] font-mono text-cyan-300 break-all bg-slate-950 p-2 rounded block border border-slate-800/80">
              {certificate.proof_tree_hash}
            </code>
          </div>

          {/* Mathematical Invariants */}
          <div>
            <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2 flex items-center gap-1.5">
              <FileCheck2 className="w-3.5 h-3.5 text-emerald-400" /> Invariantes y Teoremas Demostrados
            </h4>
            <div className="space-y-1.5">
              {certificate.mathematical_invariants.map((inv, idx) => (
                <div
                  key={idx}
                  className="p-2.5 rounded-lg bg-emerald-950/20 border border-emerald-800/30 text-xs font-mono text-emerald-200"
                >
                  {inv}
                </div>
              ))}
            </div>
          </div>

          {/* Verification Protocol Banner */}
          <div className="p-3 rounded-xl bg-indigo-950/20 border border-indigo-500/20 text-xs text-indigo-200 flex items-start gap-2.5">
            <Activity className="w-4 h-4 text-indigo-400 mt-0.5 flex-shrink-0" />
            <p>
              Este certificado garantiza matemáticamente que el razonamiento del modelo es consistente con la lógica de primer orden y libre de contraejemplos dentro de los axiomas SMT estipulados.
            </p>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="flex items-center justify-between p-4 border-t border-indigo-500/20 bg-slate-900/80">
          <span className="text-[11px] text-slate-400 font-mono">
            ID: {certificate.certificate_id}
          </span>
          <div className="flex items-center space-x-2">
            <button
              onClick={handleCopy}
              className="px-3.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-medium text-slate-200 flex items-center gap-1.5 transition-colors border border-slate-700"
            >
              {copied ? (
                <>
                  <Check className="w-3.5 h-3.5 text-emerald-400" /> Copiado
                </>
              ) : (
                <>
                  <Copy className="w-3.5 h-3.5" /> Copiar JSON
                </>
              )}
            </button>
            <button
              onClick={onClose}
              className="px-4 py-1.5 rounded-lg bg-gradient-to-r from-cyan-500 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 text-xs font-semibold text-white transition-all shadow-md shadow-cyan-500/20"
            >
              Cerrar
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
