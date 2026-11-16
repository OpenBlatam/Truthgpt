'use client';

import React, { useState, useRef, useEffect } from 'react';
import {
  Send,
  Sparkles,
  ShieldCheck,
  Users,
  Trash2,
  Terminal,
  Cpu,
  HelpCircle,
  FileSearch,
  Zap,
  ArrowRight
} from 'lucide-react';
import { ChatMessage, ChatSettings, ProofCertificate, PredefinedPrompt } from '../types/chat';
import { MessageList } from './MessageList';
import { ProofModal } from './ProofModal';

interface ChatInterfaceProps {
  settings: ChatSettings;
  onUpdateSettings: (newSettings: Partial<ChatSettings>) => void;
}

const PREDEFINED_PROMPTS: PredefinedPrompt[] = [
  {
    id: 'p1',
    title: 'Verificar Teorema Algebraico con Z3',
    description: 'Demostración formal de (x + y)² = x² + 2xy + y² con eliminación de contraejemplos',
    prompt: 'Demuestra formalmente con Z3 SMT la identidad algebraica (x + y)^2 = x^2 + 2xy + y^2 para todo x, y en los números reales y genera el certificado SAT.',
    badge: 'Z3 SMT',
    category: 'smt'
  },
  {
    id: 'p2',
    title: 'Kernel Triton Optimizado',
    description: 'Fusión de operadores y paralelización SIMD para GPU NVIDIA',
    prompt: 'Escribe un kernel Triton en Python para fusionar sin(x) * y + sqrt(x) con bloques de memoria compartida SRAM optimizados.',
    badge: 'GPU Kernel',
    category: 'code'
  },
  {
    id: 'p3',
    title: 'Búsqueda RAG de Papers ArXiv',
    description: 'Consulta semántica en corpus de verificación formal y razonamiento multi-agente',
    prompt: 'Explica los métodos de formal reasoning con solvers SMT y agentes cooperativos descritos en el paper de TruthGPT v2.',
    badge: 'Redis RAG',
    category: 'rag'
  },
  {
    id: 'p4',
    title: 'Invariantes de Hoare y Contratos',
    description: 'Verificación estricta de precondiciones, postcondiciones y terminación',
    prompt: 'Genera una especificación de lógica de Hoare para un algoritmo de búsqueda binaria y verifica sus invariantes de ciclo.',
    badge: 'Swarm Consensus',
    category: 'swarm'
  }
];

export const ChatInterface: React.FC<ChatInterfaceProps> = ({
  settings,
  onUpdateSettings
}) => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome_init',
      role: 'assistant',
      content: `👋 ¡Hola! Bienvenido a **TruthGPT Web Studio**.

Soy el motor de inteligencia formal y razonamiento matemático de TruthGPT. Cuento con:
- 🛡️ **Verificador Formal Z3 SMT:** Validación rigurosa de teoremas e invariantes.
- 🐝 **Enjambre Multi-Agente (Swarm):** Orquestación, auditoría y consenso en paralelo.
- 🔍 **Recuperación Vectorial RAG:** Indexación de papers y conocimiento verificado.

Puedes probar una de las consultas de inicio rápido a continuación o escribir tu propia proposición matemática o técnica.`,
      timestamp: 'Ahora'
    }
  ]);
  const [input, setInput] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [selectedProofCert, setSelectedProofCert] = useState<ProofCertificate | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isSending]);

  const handleSendMessage = async (textToSend?: string) => {
    const promptText = (textToSend || input).trim();
    if (!promptText || isSending) return;

    setInput('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }

    const userMessage: ChatMessage = {
      id: 'msg_user_' + Date.now(),
      role: 'user',
      content: promptText,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsSending(true);

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt: promptText,
          model: settings.model,
          enable_swarm: settings.enableSwarm,
          enable_formal_verification: settings.enableFormalVerification,
          api_url: settings.apiUrl,
          api_key: settings.apiKey,
          temperature: settings.temperature,
          max_tokens: settings.maxTokens
        })
      });

      const data = await res.json();

      if (data.success && data.response) {
        const resp = data.response;
        const assistantMessage: ChatMessage = {
          id: resp.response_id || 'resp_' + Date.now(),
          role: 'assistant',
          content: resp.content,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          model_used: resp.model_name,
          execution_time_ms: resp.execution_time_ms,
          tokens_consumed: resp.tokens_consumed,
          agent_steps: resp.agent_steps,
          proof_certificate: resp.proof_certificate,
          swarm_trace: resp.swarm_trace
        };
        setMessages((prev) => [...prev, assistantMessage]);
      } else {
        throw new Error(data.error || 'Respuesta inválida del servidor');
      }
    } catch (err: unknown) {
      console.error('Chat error:', err);
      const errorMessage: ChatMessage = {
        id: 'err_' + Date.now(),
        role: 'assistant',
        content: `❌ **Error de Inferencia:** No se pudo completar la solicitud con el backend configurado.

Detalles: ${err instanceof Error ? err.message : String(err)}.
Verifica la URL en **Configuración** o utiliza el simulador local integrado.`,
        timestamp: 'Ahora'
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsSending(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleClearHistory = () => {
    if (confirm('¿Deseas reiniciar la conversación?')) {
      setMessages([
        {
          id: 'welcome_restart',
          role: 'assistant',
          content: 'Sesión reiniciada. ¿En qué teorema o algoritmo te gustaría trabajar hoy?',
          timestamp: 'Ahora'
        }
      ]);
    }
  };

  const handleTextareaInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    e.target.style.height = 'auto';
    e.target.style.height = Math.min(e.target.scrollHeight, 180) + 'px';
  };

  return (
    <div className="flex-1 flex flex-col h-[calc(100vh-65px)] max-w-5xl mx-auto w-full px-4 sm:px-6">
      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto pt-6 px-1">
        {/* Predefined Prompts (Show when only 1 welcome message is present) */}
        {messages.length === 1 && (
          <div className="mb-8">
            <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-cyan-400" /> Consultas Rápidas de TruthGPT
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {PREDEFINED_PROMPTS.map((item) => (
                <button
                  key={item.id}
                  onClick={() => handleSendMessage(item.prompt)}
                  className="p-3.5 rounded-xl bg-slate-900/60 hover:bg-slate-800/80 border border-slate-800 hover:border-cyan-500/40 text-left transition-all group flex flex-col justify-between shadow-md hover:shadow-cyan-500/5"
                >
                  <div>
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="text-xs font-bold text-slate-200 group-hover:text-cyan-300 transition-colors">
                        {item.title}
                      </span>
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-indigo-500/10 text-indigo-300 border border-indigo-500/20 font-mono">
                        {item.badge}
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-400 line-clamp-2">
                      {item.description}
                    </p>
                  </div>
                  <div className="mt-2 text-[10px] text-cyan-400 flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity font-medium">
                    Ejecutar consulta <ArrowRight className="w-3 h-3" />
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Message Stream */}
        <MessageList
          messages={messages}
          onOpenProofModal={(cert) => setSelectedProofCert(cert)}
          isSending={isSending}
        />
        <div ref={messagesEndRef} />
      </div>

      {/* Input Box Footer */}
      <div className="py-4 border-t border-indigo-500/20 bg-[#080914]/90 backdrop-blur-md">
        {/* Controls Toolbar */}
        <div className="flex items-center justify-between mb-2 text-xs">
          <div className="flex items-center space-x-2">
            {/* Quick Swarm Toggle */}
            <button
              onClick={() => onUpdateSettings({ enableSwarm: !settings.enableSwarm })}
              className={`flex items-center space-x-1 px-2.5 py-1 rounded-lg border text-[11px] font-medium transition-colors ${
                settings.enableSwarm
                  ? 'bg-purple-950/40 text-purple-300 border-purple-500/40'
                  : 'bg-slate-900 text-slate-500 border-slate-800'
              }`}
            >
              <Users className="w-3 h-3" />
              <span>Swarm {settings.enableSwarm ? 'Activo' : 'Off'}</span>
            </button>

            {/* Quick SMT Toggle */}
            <button
              onClick={() =>
                onUpdateSettings({
                  enableFormalVerification: !settings.enableFormalVerification
                })
              }
              className={`flex items-center space-x-1 px-2.5 py-1 rounded-lg border text-[11px] font-medium transition-colors ${
                settings.enableFormalVerification
                  ? 'bg-emerald-950/40 text-emerald-300 border-emerald-500/40'
                  : 'bg-slate-900 text-slate-500 border-slate-800'
              }`}
            >
              <ShieldCheck className="w-3 h-3" />
              <span>Z3 SMT {settings.enableFormalVerification ? 'Activo' : 'Off'}</span>
            </button>
          </div>

          {/* Clear history */}
          <button
            onClick={handleClearHistory}
            title="Limpiar conversación"
            className="text-slate-500 hover:text-slate-300 p-1 rounded transition-colors"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Text Input Box */}
        <div className="relative rounded-2xl bg-slate-900 border border-slate-800 focus-within:border-cyan-500/80 focus-within:ring-1 focus-within:ring-cyan-500/50 shadow-xl transition-all">
          <textarea
            ref={textareaRef}
            rows={1}
            value={input}
            onChange={handleTextareaInput}
            onKeyDown={handleKeyDown}
            placeholder="Pregunta a TruthGPT (ej: Demuestra el binomio con Z3 SMT o genera un kernel Triton)..."
            className="w-full pl-4 pr-14 py-3.5 bg-transparent text-sm text-slate-100 placeholder:text-slate-500 resize-none outline-none max-h-44 font-sans"
          />

          <button
            onClick={() => handleSendMessage()}
            disabled={!input.trim() || isSending}
            className={`absolute right-2.5 bottom-2.5 p-2 rounded-xl flex items-center justify-center transition-all ${
              input.trim() && !isSending
                ? 'bg-gradient-to-r from-cyan-500 to-indigo-600 text-white shadow-md shadow-cyan-500/30 hover:scale-105 active:scale-95'
                : 'bg-slate-800 text-slate-600 cursor-not-allowed'
            }`}
          >
            <Send className="w-4 h-4" />
          </button>
        </div>

        <div className="flex items-center justify-between text-[11px] text-slate-500 mt-2 px-1">
          <span>Presiona <strong>Enter</strong> para enviar, <strong>Shift + Enter</strong> para salto de línea</span>
          <span>TruthGPT v2.0 Frontier • Orquestación Multi-Agente & SMT</span>
        </div>
      </div>

      {/* Modal for SMT Proof Certificates */}
      <ProofModal
        certificate={selectedProofCert}
        onClose={() => setSelectedProofCert(null)}
      />
    </div>
  );
};
