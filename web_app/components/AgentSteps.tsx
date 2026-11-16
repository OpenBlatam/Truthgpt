'use client';

import React, { useState } from 'react';
import {
  ChevronDown,
  ChevronUp,
  Cpu,
  Search,
  Users,
  ShieldCheck,
  CheckCircle2,
  Sparkles,
  ExternalLink,
  Clock
} from 'lucide-react';
import { AgentStep } from '../types/chat';

interface AgentStepsProps {
  steps: AgentStep[];
  defaultOpen?: boolean;
}

export const AgentSteps: React.FC<AgentStepsProps> = ({ steps, defaultOpen = false }) => {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  if (!steps || steps.length === 0) return null;

  const totalDuration = steps.reduce((acc, s) => acc + (s.duration_ms || 0), 0);
  const completedCount = steps.filter((s) => s.status === 'completed').length;

  const getStepIcon = (type: string) => {
    switch (type) {
      case 'vector_search':
      case 'rag':
        return <Search className="w-3.5 h-3.5 text-cyan-400" />;
      case 'swarm':
        return <Users className="w-3.5 h-3.5 text-purple-400" />;
      case 'smt_verify':
        return <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />;
      case 'synthesis':
        return <Sparkles className="w-3.5 h-3.5 text-amber-400" />;
      default:
        return <Cpu className="w-3.5 h-3.5 text-indigo-400" />;
    }
  };

  return (
    <div className="my-3 border border-indigo-500/20 bg-slate-900/60 rounded-xl overflow-hidden backdrop-blur-sm transition-all shadow-lg shadow-black/20">
      {/* Header Accordion Toggle */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between px-3.5 py-2.5 bg-slate-900/90 hover:bg-slate-800/80 transition-colors text-left"
      >
        <div className="flex items-center space-x-2.5">
          <div className="w-6 h-6 rounded-lg bg-indigo-500/15 border border-indigo-500/30 flex items-center justify-center">
            <Cpu className="w-3.5 h-3.5 text-indigo-400 animate-pulse" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-xs font-semibold text-slate-200">
                Flujo de Razonamiento del Agente
              </span>
              <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 font-medium">
                {completedCount}/{steps.length} pasos completados
              </span>
            </div>
            <p className="text-[11px] text-slate-400">
              RAG Vectorial, Enjambre y Solucionador Z3 SMT
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2 text-slate-400">
          {totalDuration > 0 && (
            <span className="text-[11px] flex items-center gap-1 text-slate-400">
              <Clock className="w-3 h-3" />
              {totalDuration}ms
            </span>
          )}
          {isOpen ? (
            <ChevronUp className="w-4 h-4 text-slate-400" />
          ) : (
            <ChevronDown className="w-4 h-4 text-slate-400" />
          )}
        </div>
      </button>

      {/* Accordion Body */}
      {isOpen && (
        <div className="p-3.5 space-y-3 bg-slate-950/40 border-t border-indigo-500/10">
          {steps.map((step, index) => (
            <div
              key={step.id || index}
              className="flex items-start space-x-3 p-2.5 rounded-lg bg-slate-900/50 border border-slate-800/80 hover:border-slate-700/80 transition-colors"
            >
              {/* Icon Status */}
              <div className="mt-0.5 p-1.5 rounded-md bg-slate-800 border border-slate-700 flex-shrink-0">
                {getStepIcon(step.type)}
              </div>

              {/* Step Content */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-medium text-slate-200 flex items-center gap-1.5">
                    {step.title}
                    {step.status === 'completed' && (
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 inline" />
                    )}
                  </h4>
                  {step.duration_ms && (
                    <span className="text-[10px] text-slate-500 font-mono">
                      {step.duration_ms}ms
                    </span>
                  )}
                </div>
                <p className="text-[11px] text-slate-400 mt-0.5 leading-relaxed">
                  {step.description}
                </p>

                {/* Sources if RAG */}
                {step.details?.sources && step.details.sources.length > 0 && (
                  <div className="mt-2 space-y-1.5 pl-2 border-l-2 border-cyan-500/30">
                    <span className="text-[10px] font-semibold text-cyan-400 uppercase tracking-wider block">
                      Documentos Recuperados (RAG):
                    </span>
                    {step.details.sources.map((src, idx) => (
                      <div
                        key={idx}
                        className="text-[11px] bg-slate-900/80 p-1.5 rounded border border-slate-800 text-slate-300"
                      >
                        <div className="flex items-center justify-between font-medium text-cyan-300">
                          <span className="truncate">{src.title}</span>
                          <span className="text-[10px] text-slate-400 font-mono ml-2">
                            Sim: {(src.score * 100).toFixed(0)}%
                          </span>
                        </div>
                        <p className="text-[10px] text-slate-400 mt-0.5 line-clamp-2">
                          {src.snippet}
                        </p>
                      </div>
                    ))}
                  </div>
                )}

                {/* Invariants if SMT */}
                {step.details?.invariants && step.details.invariants.length > 0 && (
                  <div className="mt-2 space-y-1 pl-2 border-l-2 border-emerald-500/30">
                    <span className="text-[10px] font-semibold text-emerald-400 uppercase tracking-wider block">
                      Invariantes Matemáticas Evaluadas:
                    </span>
                    {step.details.invariants.map((inv, idx) => (
                      <code
                        key={idx}
                        className="block text-[10px] font-mono bg-emerald-950/30 text-emerald-300 p-1 rounded border border-emerald-800/40"
                      >
                        {inv}
                      </code>
                    ))}
                  </div>
                )}

                {/* Swarm details */}
                {step.details?.action && (
                  <div className="mt-1.5 text-[10px] text-purple-300 bg-purple-950/30 px-2 py-1 rounded border border-purple-800/30">
                    {step.details.action}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
