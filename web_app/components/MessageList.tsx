'use client';

import React, { useState } from 'react';
import {
  User,
  Brain,
  ShieldCheck,
  Clock,
  Coins,
  Copy,
  Check,
  FileCheck2,
  Users,
  Code2
} from 'lucide-react';
import { ChatMessage, ProofCertificate } from '../types/chat';
import { AgentSteps } from './AgentSteps';

interface MessageListProps {
  messages: ChatMessage[];
  onOpenProofModal: (cert: ProofCertificate) => void;
  isSending?: boolean;
}

// Markdown renderer for code blocks, tables, bold text, and formulas
function FormattedContent({ content }: { content: string }) {
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);

  const handleCopyCode = (codeText: string, idx: number) => {
    navigator.clipboard.writeText(codeText);
    setCopiedIndex(idx);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  // Split content by code blocks ```
  const codeBlockRegex = /```([a-zA-Z0-9_-]*)\n([\s\S]*?)```/g;
  const parts: React.ReactNode[] = [];
  let lastIndex = 0;
  let match: RegExpExecArray | null;
  let blockCounter = 0;

  while ((match = codeBlockRegex.exec(content)) !== null) {
    const textBefore = content.substring(lastIndex, match.index);
    if (textBefore) {
      parts.push(<TextSection key={`text_${lastIndex}`} text={textBefore} />);
    }

    const lang = match[1] || 'plaintext';
    const code = match[2];
    const currentBlockId = blockCounter++;

    parts.push(
      <div
        key={`code_${currentBlockId}`}
        className="my-3 rounded-xl border border-slate-700/80 bg-slate-950 overflow-hidden shadow-lg shadow-black/30"
      >
        <div className="flex items-center justify-between px-3.5 py-1.5 bg-slate-900 border-b border-slate-800 text-xs">
          <span className="font-mono text-cyan-400 font-semibold uppercase tracking-wider text-[11px] flex items-center gap-1.5">
            <Code2 className="w-3.5 h-3.5 text-cyan-400" /> {lang}
          </span>
          <button
            onClick={() => handleCopyCode(code, currentBlockId)}
            className="flex items-center space-x-1 text-slate-400 hover:text-white px-2 py-0.5 rounded bg-slate-800/80 hover:bg-slate-700 transition-colors text-[11px]"
          >
            {copiedIndex === currentBlockId ? (
              <>
                <Check className="w-3 h-3 text-emerald-400" />
                <span className="text-emerald-400">Copiado</span>
              </>
            ) : (
              <>
                <Copy className="w-3 h-3" />
                <span>Copiar</span>
              </>
            )}
          </button>
        </div>
        <pre className="p-3.5 text-xs font-mono text-slate-200 overflow-x-auto leading-relaxed bg-[#0a0d1e]">
          <code>{code}</code>
        </pre>
      </div>
    );

    lastIndex = match.index + match[0].length;
  }

  const remaining = content.substring(lastIndex);
  if (remaining) {
    parts.push(<TextSection key={`text_final`} text={remaining} />);
  }

  return <div className="space-y-2">{parts}</div>;
}

// Sub-component for regular markdown text, lists, headers, quotes, and math
function TextSection({ text }: { text: string }) {
  const lines = text.split('\n');
  return (
    <div className="space-y-1.5 text-xs sm:text-sm text-slate-200 leading-relaxed">
      {lines.map((line, idx) => {
        const trimmed = line.trim();

        if (trimmed.startsWith('### ')) {
          return (
            <h3 key={idx} className="text-sm sm:text-base font-bold text-white mt-3 mb-1">
              {trimmed.replace('### ', '')}
            </h3>
          );
        }
        if (trimmed.startsWith('#### ')) {
          return (
            <h4 key={idx} className="text-xs sm:text-sm font-semibold text-cyan-300 mt-2 mb-1">
              {trimmed.replace('#### ', '')}
            </h4>
          );
        }
        if (trimmed.startsWith('> ')) {
          return (
            <blockquote
              key={idx}
              className="pl-3 py-1 my-2 border-l-2 border-indigo-500/50 bg-indigo-950/20 rounded-r-lg text-slate-300 italic"
            >
              {trimmed.replace('> ', '')}
            </blockquote>
          );
        }
        if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
          return (
            <li key={idx} className="ml-4 list-disc list-outside text-slate-300">
              {trimmed.substring(2)}
            </li>
          );
        }
        if (trimmed.match(/^\d+\.\s/)) {
          return (
            <li key={idx} className="ml-4 list-decimal list-outside text-slate-300">
              {trimmed.replace(/^\d+\.\s/, '')}
            </li>
          );
        }
        if (trimmed === '') {
          return <div key={idx} className="h-1" />;
        }

        // Render inline bold, inline code, and math symbols
        return (
          <p key={idx} className="text-slate-200">
            {renderInlineMarkdown(line)}
          </p>
        );
      })}
    </div>
  );
}

function renderInlineMarkdown(str: string) {
  // Simple parser for **bold** and `code`
  const parts = str.split(/(\*\*.*?\*\*|`.*?`|\$\$.*?\$\$)/g);
  return parts.map((part, i) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return (
        <strong key={i} className="font-semibold text-white">
          {part.slice(2, -2)}
        </strong>
      );
    }
    if (part.startsWith('`') && part.endsWith('`')) {
      return (
        <code
          key={i}
          className="px-1.5 py-0.5 rounded bg-slate-800 text-cyan-300 font-mono text-xs border border-slate-700/60"
        >
          {part.slice(1, -1)}
        </code>
      );
    }
    if (part.startsWith('$$') && part.endsWith('$$')) {
      return (
        <span
          key={i}
          className="font-mono text-cyan-300 font-medium px-2 py-0.5 bg-slate-900 rounded border border-cyan-500/20 inline-block my-1"
        >
          {part.slice(2, -2)}
        </span>
      );
    }
    return part;
  });
}

export const MessageList: React.FC<MessageListProps> = ({
  messages,
  onOpenProofModal,
  isSending = false
}) => {
  return (
    <div className="space-y-6 pb-6">
      {messages.map((message) => {
        const isUser = message.role === 'user';

        return (
          <div
            key={message.id}
            className={`flex items-start space-x-3 ${
              isUser ? 'flex-row-reverse space-x-reverse' : ''
            }`}
          >
            {/* Avatar */}
            <div
              className={`w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0 shadow-md ${
                isUser
                  ? 'bg-slate-800 border border-slate-700 text-slate-300'
                  : 'bg-gradient-to-tr from-cyan-500 to-indigo-600 text-white shadow-cyan-500/20'
              }`}
            >
              {isUser ? <User className="w-4 h-4" /> : <Brain className="w-4 h-4" />}
            </div>

            {/* Bubble Container */}
            <div
              className={`flex-1 max-w-3xl rounded-2xl p-4 sm:p-5 transition-all ${
                isUser
                  ? 'bg-gradient-to-r from-indigo-950/50 to-slate-900 border border-indigo-500/30 text-white shadow-lg'
                  : 'bg-slate-900/80 border border-slate-800 text-slate-100 shadow-xl'
              }`}
            >
              {/* Header Info */}
              <div className="flex items-center justify-between mb-2 pb-1.5 border-b border-slate-800/80">
                <div className="flex items-center space-x-2">
                  <span className="text-xs font-bold text-slate-200">
                    {isUser ? 'Tú (Investigador)' : 'TruthGPT Engine'}
                  </span>
                  {message.model_used && (
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 font-mono">
                      {message.model_used}
                    </span>
                  )}
                </div>

                <div className="flex items-center space-x-2 text-[11px] text-slate-400">
                  {message.execution_time_ms && (
                    <span className="hidden sm:flex items-center gap-1">
                      <Clock className="w-3 h-3 text-slate-500" />
                      {message.execution_time_ms}ms
                    </span>
                  )}
                  {message.tokens_consumed && (
                    <span className="hidden sm:flex items-center gap-1 font-mono">
                      <Coins className="w-3 h-3 text-slate-500" />
                      {message.tokens_consumed} tokens
                    </span>
                  )}
                  <span>{message.timestamp}</span>
                </div>
              </div>

              {/* Agent Steps Accordion (Reasoning / RAG / SMT) */}
              {!isUser && message.agent_steps && message.agent_steps.length > 0 && (
                <AgentSteps steps={message.agent_steps} defaultOpen={false} />
              )}

              {/* Message Body */}
              <FormattedContent content={message.content} />

              {/* Proof Certificate Action Banner */}
              {!isUser && message.proof_certificate && (
                <div className="mt-4 p-3 rounded-xl bg-emerald-950/20 border border-emerald-500/30 flex items-center justify-between">
                  <div className="flex items-center space-x-2.5">
                    <div className="p-1.5 rounded-lg bg-emerald-500/10 text-emerald-400">
                      <ShieldCheck className="w-4 h-4" />
                    </div>
                    <div>
                      <div className="flex items-center space-x-2">
                        <span className="text-xs font-semibold text-emerald-300">
                          Certificado de Prueba SMT Generado
                        </span>
                        <span className="text-[10px] px-1.5 py-0.2 rounded bg-emerald-500/20 text-emerald-300 font-mono">
                          {message.proof_certificate.status}
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-400">
                        {message.proof_certificate.solver_engine} • Confianza:{' '}
                        {(message.proof_certificate.confidence_score * 100).toFixed(1)}%
                      </p>
                    </div>
                  </div>

                  <button
                    onClick={() => onOpenProofModal(message.proof_certificate!)}
                    className="px-3 py-1.5 rounded-lg bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-300 text-xs font-medium border border-emerald-500/30 flex items-center gap-1.5 transition-colors shadow-sm"
                  >
                    <FileCheck2 className="w-3.5 h-3.5" />
                    <span>Ver Certificado</span>
                  </button>
                </div>
              )}

              {/* Swarm Trace Banner */}
              {!isUser && message.swarm_trace && (
                <div className="mt-2 text-[11px] text-purple-300 bg-purple-950/20 p-2 rounded-lg border border-purple-800/30 flex items-center gap-2">
                  <Users className="w-3.5 h-3.5 text-purple-400 flex-shrink-0" />
                  <span>{message.swarm_trace.consensus_summary}</span>
                </div>
              )}
            </div>
          </div>
        );
      })}

      {/* Typing Indicator / Sending Loader */}
      {isSending && (
        <div className="flex items-start space-x-3 animate-in fade-in duration-200">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-cyan-500 to-indigo-600 text-white flex items-center justify-center flex-shrink-0 shadow-md shadow-cyan-500/20">
            <Brain className="w-4 h-4 animate-spin" />
          </div>
          <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4 text-slate-300 flex items-center space-x-3">
            <div className="flex space-x-1.5">
              <span className="w-2 h-2 rounded-full bg-cyan-400 animate-bounce"></span>
              <span className="w-2 h-2 rounded-full bg-indigo-400 animate-bounce [animation-delay:0.2s]"></span>
              <span className="w-2 h-2 rounded-full bg-purple-400 animate-bounce [animation-delay:0.4s]"></span>
            </div>
            <span className="text-xs text-slate-400 font-medium">
              TruthGPT orquestando agentes, recuperando vectores y verificando con Z3 SMT...
            </span>
          </div>
        </div>
      )}
    </div>
  );
};
