'use client';

import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Zap, ShieldCheck, Cpu, Copy, Check, Play, RefreshCw,
  DollarSign, Bot, MessageSquare,
  Send, Download, CheckCircle2,
  Code2, Key, FileText,
  CreditCard, Lock, Activity, Brain,
  SlidersHorizontal, ChevronRight
} from 'lucide-react';

interface Tier {
  tier_id: string;
  name: string;
  tagline: string;
  price_monthly_usd: number;
  price_yearly_usd: number;
  badge: string;
  context_window_tokens: number;
  daily_token_limit: number;
  requests_per_minute: number;
  max_swarm_agents: number;
  smt_verification_level: string;
  proof_certificates: boolean;
  latency_tier: string;
  available_models: string[];
  features_list: string[];
}

interface UserState {
  user_id: string;
  email: string;
  name: string;
  tier: string;
  tier_name: string;
  tier_badge: string;
  billing_cycle: string;
  status: string;
  api_keys: string[];
  metrics: {
    tokens_consumed_today: number;
    daily_token_limit: number;
    remaining_tokens: number;
    percent_quota_used: number;
    total_tokens: number;
    verifications_completed: number;
    swarm_runs: number;
  };
  features: {
    context_window: number;
    max_swarm_agents: number;
    smt_verification_level: string;
    proof_certificates: boolean;
    latency_tier: string;
    available_models: string[];
  };
  invoices: Array<{
    invoice_id: string;
    amount_usd: number;
    tier_id: string;
    billing_cycle: string;
    date: string;
    status: string;
  }>;
}

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  model_used?: string;
  tier_used?: string;
  execution_time_ms?: number;
  tokens_consumed?: number;
  proof_certificate?: {
    certificate_id: string;
    status: string;
    solver_engine: string;
    verification_time_ms: number;
    confidence_score: number;
    proof_tree_hash: string;
    mathematical_invariants: string[];
  };
  swarm_trace?: {
    session_id: string;
    consensus_summary: string;
    agents_involved: Array<{ role_name: string; status: string; contribution: string }>;
  } | null;
}

type CloudTab = 'chat' | 'pricing' | 'smt_lab' | 'papers' | 'developer' | 'billing';

interface ProofCertificateData {
  certificate_id: string;
  status: string;
  solver_engine: string;
  verification_time_ms: number;
  confidence_score: number;
  proof_tree_hash: string;
  mathematical_invariants: string[];
}

interface SmtResultData {
  certificate_id: string;
  status: string;
  solver_engine: string;
  verification_time_ms: number;
  confidence_score: number;
  proof_tree_hash: string;
  mathematical_invariants: string[];
  smt_constraints_evaluated?: number;
  tier_rigor_level?: number;
}

interface PaperItem {
  paper_id: string;
  title: string;
  authors: string[];
  published: string;
  impact_factor: number;
  category: string;
  abstract: string;
  cloud_status: string;
  supported_tiers: string[];
}

export default function TruthGPTCloudPage() {
  const [activeTab, setActiveTab] = useState<CloudTab>('chat');
  const [tiers, setTiers] = useState<Tier[]>([]);
  const [userData, setUserData] = useState<UserState | null>(null);
  const [billingCycle, setBillingCycle] = useState<'monthly' | 'yearly'>('monthly');
  const [selectedTierForUpgrade, setSelectedTierForUpgrade] = useState<Tier | null>(null);
  const [isUpgradeModalOpen, setIsUpgradeModalOpen] = useState(false);
  const [paymentMethod, setPaymentMethod] = useState<'stripe_card' | 'crypto_usdc'>('stripe_card');
  const [isUpgrading, setIsUpgrading] = useState(false);
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  // Chat State
  const [selectedModel, setSelectedModel] = useState<string>('deepseek-v3');
  const [enableSwarm, setEnableSwarm] = useState<boolean>(true);
  const [enableFormalVerification, setEnableFormalVerification] = useState<boolean>(true);
  const [chatInput, setChatInput] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome_msg',
      role: 'assistant',
      content: '👋 ¡Bienvenido a **TruthGPT Cloud**! Soy tu asistente de inteligencia matemática y formal. ¿En qué teorema, algoritmo o investigación de IA deseas trabajar hoy?',
      timestamp: 'Ahora'
    }
  ]);
  const [activeProofModal, setActiveProofModal] = useState<ProofCertificateData | null>(null);

  // SMT Lab State
  const [smtFormula, setSmtFormula] = useState<string>('∀x, y ∈ ℝ: (x + y)^2 = x^2 + 2xy + y^2 ∧ (x ≥ 0 → √x ≥ 0)');
  const [smtLoading, setSmtLoading] = useState<boolean>(false);
  const [smtResult, setSmtResult] = useState<SmtResultData | null>(null);

  // Papers State
  const [papers, setPapers] = useState<PaperItem[]>([]);
  const [applyingPaperId, setApplyingPaperId] = useState<string | null>(null);
  const [appliedPapers, setAppliedPapers] = useState<string[]>([]);

  const chatEndRef = useRef<HTMLDivElement>(null);

  const fetchCloudTiers = useCallback(async () => {
    try {
      const res = await fetch('/api/cloud', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'get_tiers' })
      });
      const data = await res.json();
      if (data.success) {
        setTiers(data.tiers);
      }
    } catch (e) {
      console.error('Error fetching tiers:', e);
    }
  }, []);

  const fetchUserStatus = useCallback(async () => {
    try {
      const res = await fetch('/api/cloud', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'get_status' })
      });
      const data = await res.json();
      if (data.success) {
        setUserData(data.user);
        if (data.user.features?.available_models?.length) {
          setSelectedModel(data.user.features.available_models[0]);
        }
      }
    } catch (e) {
      console.error('Error fetching user status:', e);
    }
  }, []);

  const fetchPapers = useCallback(async () => {
    try {
      const res = await fetch('/api/cloud', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'get_papers' })
      });
      const data = await res.json();
      if (data.success) {
        setPapers(data.papers);
      }
    } catch (e) {
      console.error('Error fetching papers:', e);
    }
  }, []);

  // Fetch initial cloud data on mount
  useEffect(() => {
    let active = true;
    const loadAll = async () => {
      try {
        const [tiersRes, statusRes, papersRes] = await Promise.all([
          fetch('/api/cloud', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action: 'get_tiers' })
          }).then((r) => r.json()),
          fetch('/api/cloud', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action: 'get_status' })
          }).then((r) => r.json()),
          fetch('/api/cloud', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action: 'get_papers' })
          }).then((r) => r.json())
        ]);

        if (active) {
          if (tiersRes?.success) setTiers(tiersRes.tiers);
          if (statusRes?.success) {
            setUserData(statusRes.user);
            if (statusRes.user?.features?.available_models?.length) {
              setSelectedModel(statusRes.user.features.available_models[0]);
            }
          }
          if (papersRes?.success) setPapers(papersRes.papers);
        }
      } catch (e) {
        console.error('Initial load error:', e);
      }
    };
    loadAll();
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSendMessage = async () => {
    if (!chatInput.trim() || isSending) return;
    const promptText = chatInput;
    setChatInput('');

    const userMsg: ChatMessage = {
      id: 'msg_' + Date.now(),
      role: 'user',
      content: promptText,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };
    setMessages((prev) => [...prev, userMsg]);
    setIsSending(true);

    try {
      const res = await fetch('/api/cloud', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'chat',
          prompt: promptText,
          model: selectedModel,
          enable_swarm: enableSwarm,
          enable_formal_verification: enableFormalVerification
        })
      });
      const data = await res.json();

      if (data.success && data.response) {
        const resp = data.response;
        const assistantMsg: ChatMessage = {
          id: resp.response_id || 'resp_' + Date.now(),
          role: 'assistant',
          content: resp.content,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          model_used: resp.model_name,
          tier_used: resp.tier_used,
          execution_time_ms: resp.execution_time_ms,
          tokens_consumed: resp.tokens_consumed,
          proof_certificate: resp.proof_certificate,
          swarm_trace: resp.swarm_trace
        };
        setMessages((prev) => [...prev, assistantMsg]);
        fetchUserStatus(); // Refresh remaining token quota
      }
    } catch (e) {
      console.error('Chat error:', e);
      setMessages((prev) => [
        ...prev,
        {
          id: 'err_' + Date.now(),
          role: 'assistant',
          content: '❌ Error de comunicación con el clúster de TruthGPT Cloud. Por favor verifique su conexión o cuota de tokens.',
          timestamp: 'Ahora'
        }
      ]);
    } finally {
      setIsSending(false);
    }
  };

  const handleRunSmtVerification = async () => {
    if (!smtFormula.trim()) return;
    setSmtLoading(true);
    try {
      const res = await fetch('/api/cloud', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'verify', claim: smtFormula })
      });
      const data = await res.json();
      if (data.success) {
        setSmtResult(data.certificate);
      }
    } catch (e) {
      console.error('SMT verify error:', e);
    } finally {
      setSmtLoading(false);
    }
  };

  const handleApplyPaper = async (paperId: string) => {
    setApplyingPaperId(paperId);
    try {
      const res = await fetch('/api/cloud', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'apply_paper', paper_id: paperId })
      });
      const data = await res.json();
      if (data.success) {
        setAppliedPapers((prev) => [...prev, paperId]);
        fetchPapers();
      }
    } catch (e) {
      console.error('Apply paper error:', e);
    } finally {
      setApplyingPaperId(null);
    }
  };

  const handleUpgradeSubscription = async () => {
    if (!selectedTierForUpgrade) return;
    setIsUpgrading(true);
    try {
      const res = await fetch('/api/cloud', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'upgrade',
          target_tier: selectedTierForUpgrade.tier_id,
          billing_cycle: billingCycle,
          payment_method: paymentMethod
        })
      });
      const data = await res.json();
      if (data.success) {
        setIsUpgradeModalOpen(false);
        await fetchUserStatus();
        await fetchCloudTiers();
        alert(`🎉 ¡Plan actualizado con éxito a ${selectedTierForUpgrade.name}!`);
      }
    } catch (e) {
      console.error('Upgrade error:', e);
    } finally {
      setIsUpgrading(false);
    }
  };

  const handleGenerateApiKey = async () => {
    try {
      const res = await fetch('/api/cloud', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'generate_key' })
      });
      const data = await res.json();
      if (data.success) {
        fetchUserStatus();
      }
    } catch (e) {
      console.error('Generate key error:', e);
    }
  };

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(id);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  return (
    <div className="min-h-screen bg-[#080914] text-slate-100 flex flex-col font-sans selection:bg-cyan-500 selection:text-black">
      {/* 🌟 TOP NAVIGATION BAR */}
      <header className="sticky top-0 z-40 bg-[#0c0f24]/90 backdrop-blur-xl border-b border-indigo-500/20 px-6 py-3.5">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center space-x-3 cursor-pointer" onClick={() => setActiveTab('chat')}>
            <div className="relative">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-500 via-indigo-500 to-purple-600 flex items-center justify-center shadow-lg shadow-cyan-500/25">
                <Brain className="w-5 h-5 text-white" />
              </div>
              <span className="absolute -top-1 -right-1 flex h-3 w-3">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-3 w-3 bg-cyan-500"></span>
              </span>
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-bold text-lg tracking-tight bg-gradient-to-r from-white via-cyan-200 to-indigo-300 bg-clip-text text-transparent">
                  TruthGPT <span className="text-cyan-400 font-extrabold text-sm uppercase px-1.5 py-0.5 rounded bg-cyan-500/10 border border-cyan-500/30">Cloud</span>
                </span>
                <span className="text-xs text-slate-400 hidden sm:inline">v2.0 Frontier</span>
              </div>
              <p className="text-[11px] text-slate-400 flex items-center gap-1.5">
                <ShieldCheck className="w-3 h-3 text-emerald-400" /> Z3 Formal SMT Verified
              </p>
            </div>
          </div>

          {/* Navigation Pills */}
          <nav className="hidden md:flex items-center space-x-1 bg-slate-900/80 p-1 rounded-xl border border-slate-800">
            {[
              { id: 'chat' as CloudTab, label: 'Chat & Studio', icon: MessageSquare },
              { id: 'pricing' as CloudTab, label: 'Planes & Precios', icon: DollarSign, badge: 'Suscripciones' },
              { id: 'smt_lab' as CloudTab, label: 'Lab SMT / Z3', icon: Activity },
              { id: 'papers' as CloudTab, label: 'SOTA Papers Hub', icon: FileText },
              { id: 'developer' as CloudTab, label: 'API & Claves', icon: Code2 },
              { id: 'billing' as CloudTab, label: 'Facturación', icon: CreditCard }
            ].map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center space-x-2 px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all ${
                    isActive
                      ? 'bg-gradient-to-r from-cyan-500/20 to-indigo-500/20 text-cyan-300 border border-cyan-500/40 shadow-sm'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                  }`}
                >
                  <Icon className="w-3.5 h-3.5" />
                  <span>{tab.label}</span>
                  {tab.badge && (
                    <span className="text-[9px] uppercase px-1.5 py-0.2 rounded bg-indigo-500/30 text-indigo-200 font-bold border border-indigo-400/30">
                      {tab.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </nav>

          {/* User Tier & Quick Upgrade Header Badge */}
          <div className="flex items-center space-x-3">
            {userData && (
              <div className="hidden lg:flex flex-col items-end text-right">
                <div className="flex items-center space-x-1.5">
                  <span className="text-xs font-semibold text-slate-200">{userData.name}</span>
                  <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-gradient-to-r from-purple-500/20 to-cyan-500/20 text-cyan-300 border border-cyan-500/30">
                    {userData.tier_name}
                  </span>
                </div>
                <div className="text-[10px] text-slate-400">
                  Cuota: <strong className="text-slate-200">{userData.metrics.remaining_tokens.toLocaleString()}</strong> tokens restantes
                </div>
              </div>
            )}

            <button
              onClick={() => {
                setActiveTab('pricing');
              }}
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-gradient-to-r from-cyan-500 via-indigo-600 to-purple-600 hover:from-cyan-400 hover:to-purple-500 text-white text-xs font-semibold shadow-lg shadow-indigo-500/20 transition-transform active:scale-95"
            >
              <Zap className="w-3.5 h-3.5 fill-current" />
              <span>Upgrade Plan</span>
            </button>
          </div>
        </div>
      </header>

      {/* 📱 MOBILE NAVIGATION BAR */}
      <div className="md:hidden flex overflow-x-auto bg-slate-900 border-b border-slate-800 p-2 gap-1 text-xs">
        {[
          { id: 'chat' as CloudTab, label: 'Chat', icon: MessageSquare },
          { id: 'pricing' as CloudTab, label: 'Planes', icon: DollarSign },
          { id: 'smt_lab' as CloudTab, label: 'Lab SMT', icon: Activity },
          { id: 'papers' as CloudTab, label: 'Papers', icon: FileText },
          { id: 'developer' as CloudTab, label: 'API Keys', icon: Code2 },
          { id: 'billing' as CloudTab, label: 'Facturas', icon: CreditCard }
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center space-x-1 px-3 py-1.5 rounded-lg whitespace-nowrap ${
                isActive ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40' : 'text-slate-400'
              }`}
            >
              <Icon className="w-3 h-3" />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* 🚀 MAIN CONTENT BODY */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8">
        {/* ========================================================================= */}
        {/* 💬 TAB 1: CHAT & STUDIO */}
        {/* ========================================================================= */}
        {activeTab === 'chat' && (
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 h-[calc(100vh-180px)] min-h-[600px]">
            {/* Sidebar: Engine & Verifier Configuration */}
            <div className="lg:col-span-1 bg-[#0f1225]/80 backdrop-blur-md rounded-2xl border border-indigo-500/15 p-4 flex flex-col justify-between space-y-4">
              <div className="space-y-4">
                <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                  <h2 className="font-semibold text-sm text-slate-200 flex items-center gap-2">
                    <SlidersHorizontal className="w-4 h-4 text-cyan-400" /> Configuración Cloud
                  </h2>
                  <span className="text-[10px] uppercase font-bold text-cyan-400 bg-cyan-500/10 px-2 py-0.5 rounded border border-cyan-500/30">
                    {userData?.tier_badge || 'PRO'}
                  </span>
                </div>

                {/* Model Selector */}
                <div>
                  <label className="text-xs font-medium text-slate-300 mb-1.5 block">Motor de Inferencia:</label>
                  <select
                    value={selectedModel}
                    onChange={(e) => setSelectedModel(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-xs text-slate-100 focus:outline-none focus:border-cyan-400"
                  >
                    {userData?.features?.available_models ? (
                      userData.features.available_models.map((m) => (
                        <option key={m} value={m}>
                          {m.toUpperCase()}
                        </option>
                      ))
                    ) : (
                      <>
                        <option value="deepseek-v3">DEEPSEEK V3</option>
                        <option value="claude-3-7-sonnet">CLAUDE 3.7 SONNET</option>
                        <option value="gpt-4o">GPT-4O FRONTIER</option>
                        <option value="truthgpt-pro-smt">TRUTHGPT PRO SMT</option>
                      </>
                    )}
                  </select>
                </div>

                {/* Verification & Swarm Switches */}
                <div className="space-y-3 pt-2">
                  <div className="flex items-center justify-between p-2.5 rounded-xl bg-slate-900/60 border border-slate-800">
                    <div>
                      <div className="text-xs font-medium text-slate-200 flex items-center gap-1.5">
                        <ShieldCheck className="w-3.5 h-3.5 text-cyan-400" /> Z3 SMT Formal Verifier
                      </div>
                      <div className="text-[10px] text-slate-400">Emisión de certificados matemáticos</div>
                    </div>
                    <input
                      type="checkbox"
                      checked={enableFormalVerification}
                      onChange={(e) => setEnableFormalVerification(e.target.checked)}
                      className="w-4 h-4 text-cyan-500 rounded bg-slate-800 border-slate-700 focus:ring-0 cursor-pointer"
                    />
                  </div>

                  <div className="flex items-center justify-between p-2.5 rounded-xl bg-slate-900/60 border border-slate-800">
                    <div>
                      <div className="text-xs font-medium text-slate-200 flex items-center gap-1.5">
                        <Bot className="w-3.5 h-3.5 text-purple-400" /> Swarm Multi-Agente
                      </div>
                      <div className="text-[10px] text-slate-400">Orquestación de {userData?.features?.max_swarm_agents || 5} agentes</div>
                    </div>
                    <input
                      type="checkbox"
                      checked={enableSwarm}
                      onChange={(e) => setEnableSwarm(e.target.checked)}
                      className="w-4 h-4 text-purple-500 rounded bg-slate-800 border-slate-700 focus:ring-0 cursor-pointer"
                    />
                  </div>
                </div>

                {/* Quota Gauge */}
                {userData && (
                  <div className="p-3 rounded-xl bg-gradient-to-b from-slate-900/80 to-slate-950/80 border border-slate-800 space-y-2">
                    <div className="flex justify-between text-[11px]">
                      <span className="text-slate-400">Uso de Cuota Diaria</span>
                      <span className="text-cyan-400 font-semibold">{userData.metrics.percent_quota_used}%</span>
                    </div>
                    <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
                      <div
                        className="bg-gradient-to-r from-cyan-500 to-indigo-500 h-1.5 rounded-full transition-all duration-500"
                        style={{ width: `${userData.metrics.percent_quota_used}%` }}
                      ></div>
                    </div>
                    <div className="flex justify-between text-[10px] text-slate-400">
                      <span>{userData.metrics.tokens_consumed_today.toLocaleString()} tokens</span>
                      <span>Límite: {userData.metrics.daily_token_limit.toLocaleString()}</span>
                    </div>
                  </div>
                )}
              </div>

              {/* Hardware / Latency Banner */}
              <div className="p-3 rounded-xl bg-cyan-950/20 border border-cyan-500/20 text-[11px] text-cyan-200 space-y-1">
                <div className="font-semibold flex items-center gap-1.5">
                  <Cpu className="w-3.5 h-3.5 text-cyan-400" /> Aceleración: {userData?.features?.latency_tier || 'TensorRT-LLM'}
                </div>
                <p className="text-[10px] text-slate-400">
                  Cola prioritaria activada. Invariantes matemáticos verificados en tiempo real.
                </p>
              </div>
            </div>

            {/* Main Chat Conversation Area */}
            <div className="lg:col-span-3 bg-[#0f1225]/80 backdrop-blur-md rounded-2xl border border-indigo-500/15 flex flex-col overflow-hidden">
              {/* Message List */}
              <div className="flex-1 p-4 sm:p-6 overflow-y-auto space-y-4">
                {messages.map((msg) => (
                  <div
                    key={msg.id}
                    className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-[85%] rounded-2xl p-4 sm:p-5 space-y-3 ${
                        msg.role === 'user'
                          ? 'bg-gradient-to-r from-cyan-600 to-indigo-600 text-white rounded-br-none shadow-md shadow-cyan-500/10'
                          : 'bg-slate-900/90 text-slate-100 rounded-bl-none border border-slate-800'
                      }`}
                    >
                      <div className="flex items-center justify-between text-[11px] opacity-75 border-b border-white/10 pb-2">
                        <span className="font-semibold flex items-center gap-1.5">
                          {msg.role === 'user' ? '👤 Tú' : '🧠 TruthGPT Cloud Engine'}
                          {msg.model_used && (
                            <span className="text-[10px] uppercase font-mono px-1.5 py-0.2 bg-white/10 rounded">
                              {msg.model_used}
                            </span>
                          )}
                        </span>
                        <span>{msg.timestamp}</span>
                      </div>

                      {/* Message Content */}
                      <div className="text-xs sm:text-sm whitespace-pre-wrap leading-relaxed space-y-2">
                        {msg.content}
                      </div>

                      {/* Swarm Trace Expansion */}
                      {msg.swarm_trace && (
                        <div className="p-3 rounded-xl bg-purple-950/30 border border-purple-500/30 space-y-2">
                          <div className="text-[11px] font-semibold text-purple-300 flex items-center gap-1.5">
                            <Bot className="w-3.5 h-3.5 text-purple-400" /> Trazabilidad Swarm Multi-Agente
                          </div>
                          <p className="text-[11px] text-slate-300 italic">{msg.swarm_trace.consensus_summary}</p>
                          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 pt-1">
                            {msg.swarm_trace.agents_involved.map((ag, idx) => (
                              <div key={idx} className="p-2 rounded bg-slate-900/80 border border-slate-800 text-[10px]">
                                <strong className="text-purple-300 block">{ag.role_name}</strong>
                                <span className="text-slate-400">{ag.contribution}</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Z3 SMT Proof Certificate Badge / Card */}
                      {msg.proof_certificate && (
                        <div className="flex items-center justify-between p-2.5 rounded-xl bg-cyan-950/40 border border-cyan-500/30 text-[11px]">
                          <div className="flex items-center space-x-2">
                            <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
                            <div>
                              <span className="font-semibold text-cyan-200">Certificado de Verdad Z3 SMT</span>
                              <span className="text-[10px] text-slate-400 block font-mono">
                                Hash: {msg.proof_certificate.proof_tree_hash} | {msg.proof_certificate.verification_time_ms} ms
                              </span>
                            </div>
                          </div>
                          <button
                            onClick={() => setActiveProofModal(msg.proof_certificate || null)}
                            className="px-2.5 py-1 rounded bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-300 text-[10px] font-semibold border border-cyan-500/40 transition-colors"
                          >
                            Inspeccionar Prueba
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
                <div ref={chatEndRef} />
              </div>

              {/* Chat Input Bar */}
              <div className="p-3 sm:p-4 bg-slate-900/90 border-t border-slate-800">
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    handleSendMessage();
                  }}
                  className="flex items-center space-x-2"
                >
                  <input
                    type="text"
                    value={chatInput}
                    onChange={(e) => setChatInput(e.target.value)}
                    placeholder="Escribe tu consulta matemática, demostración formal o problema algorítmico..."
                    className="flex-1 bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-xs sm:text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-400 transition-colors"
                    disabled={isSending}
                  />
                  <button
                    type="submit"
                    disabled={isSending || !chatInput.trim()}
                    className="px-5 py-3 rounded-xl bg-gradient-to-r from-cyan-500 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 disabled:opacity-50 text-white text-xs sm:text-sm font-semibold flex items-center space-x-1.5 transition-transform active:scale-95 shadow-md shadow-cyan-500/20"
                  >
                    {isSending ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                    <span className="hidden sm:inline">Enviar</span>
                  </button>
                </form>
              </div>
            </div>
          </div>
        )}

        {/* ========================================================================= */}
        {/* 💎 TAB 2: PLANES & PRECIOS (SUBSCRIPTION HUB) */}
        {/* ========================================================================= */}
        {activeTab === 'pricing' && (
          <div className="space-y-10">
            {/* Header Banner */}
            <div className="text-center max-w-3xl mx-auto space-y-4">
              <span className="px-3 py-1 rounded-full text-xs font-semibold bg-cyan-500/10 text-cyan-300 border border-cyan-500/30">
                TruthGPT Cloud Subscriptions
              </span>
              <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight bg-gradient-to-r from-white via-slate-100 to-slate-400 bg-clip-text text-transparent">
                Elige el nivel de verdad y potencia matemática para tu clúster
              </h1>
              <p className="text-sm text-slate-400 leading-relaxed">
                A diferencia de Gemini Advanced o ChatGPT Plus, TruthGPT Cloud integra <strong>Verificación Formal Z3 SMT</strong>, contratos Hoare y enjambres multi-agente libres de alucinaciones.
              </p>

              {/* Billing Toggle (Monthly / Yearly) */}
              <div className="flex items-center justify-center space-x-3 pt-2">
                <span className={`text-xs font-semibold ${billingCycle === 'monthly' ? 'text-cyan-300' : 'text-slate-400'}`}>
                  Facturación Mensual
                </span>
                <button
                  onClick={() => setBillingCycle((prev) => (prev === 'monthly' ? 'yearly' : 'monthly'))}
                  className="w-12 h-6 rounded-full bg-slate-800 p-1 border border-slate-700 relative transition-colors focus:outline-none"
                >
                  <div
                    className={`w-4 h-4 rounded-full bg-cyan-400 transition-transform ${
                      billingCycle === 'yearly' ? 'translate-x-6' : 'translate-x-0'
                    }`}
                  ></div>
                </button>
                <div className="flex items-center space-x-1.5">
                  <span className={`text-xs font-semibold ${billingCycle === 'yearly' ? 'text-cyan-300' : 'text-slate-400'}`}>
                    Facturación Anual
                  </span>
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-400/30">
                    Ahorra 20% 🔥
                  </span>
                </div>
              </div>
            </div>

            {/* Pricing Cards Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {tiers.map((tier) => {
                const isCurrent = userData?.tier === tier.tier_id;
                const isPopular = tier.tier_id === 'pro';
                const isUltra = tier.tier_id === 'ultra';

                const price = billingCycle === 'yearly' ? tier.price_yearly_usd : tier.price_monthly_usd;

                return (
                  <div
                    key={tier.tier_id}
                    className={`rounded-2xl p-6 flex flex-col justify-between relative transition-all duration-300 ${
                      isPopular
                        ? 'bg-gradient-to-b from-[#131738] to-[#0c0f24] border-2 border-cyan-500 shadow-2xl shadow-cyan-500/15 -translate-y-1'
                        : isUltra
                        ? 'bg-gradient-to-b from-[#191138] to-[#0c0f24] border-2 border-purple-500 shadow-2xl shadow-purple-500/15'
                        : 'bg-[#0f1225]/90 border border-slate-800 hover:border-slate-700'
                    }`}
                  >
                    {/* Badge */}
                    <div className="flex justify-between items-center mb-4">
                      <span
                        className={`text-[11px] font-bold px-2.5 py-0.5 rounded-full border ${
                          isPopular
                            ? 'bg-cyan-500/20 text-cyan-300 border-cyan-400/40'
                            : isUltra
                            ? 'bg-purple-500/20 text-purple-300 border-purple-400/40'
                            : 'bg-slate-800 text-slate-300 border-slate-700'
                        }`}
                      >
                        {tier.badge}
                      </span>
                      {isCurrent && (
                        <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 flex items-center gap-1">
                          <CheckCircle2 className="w-3 h-3" /> Plan Actual
                        </span>
                      )}
                    </div>

                    {/* Plan Title & Price */}
                    <div className="space-y-3 mb-6">
                      <h3 className="text-xl font-bold text-white">{tier.name}</h3>
                      <p className="text-xs text-slate-400 min-h-[36px]">{tier.tagline}</p>
                      <div className="pt-2">
                        <div className="flex items-baseline space-x-1">
                          <span className="text-3xl sm:text-4xl font-extrabold text-white">
                            ${price}
                          </span>
                          <span className="text-xs text-slate-400">
                            /{billingCycle === 'yearly' ? 'año' : 'mes'}
                          </span>
                        </div>
                        {billingCycle === 'yearly' && price > 0 && (
                          <span className="text-[10px] text-emerald-400 block pt-0.5 font-medium">
                            Equivalente a ${(price / 12).toFixed(2)}/mes
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Feature Highlights */}
                    <div className="space-y-2.5 mb-8 flex-1 border-t border-slate-800 pt-4">
                      <div className="text-[11px] font-semibold text-slate-300 uppercase tracking-wider">Incluye:</div>
                      {tier.features_list.map((feat, idx) => (
                        <div key={idx} className="flex items-start space-x-2 text-xs text-slate-300">
                          <Check className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
                          <span>{feat}</span>
                        </div>
                      ))}
                    </div>

                    {/* Action Button */}
                    <button
                      onClick={() => {
                        if (isCurrent) return;
                        setSelectedTierForUpgrade(tier);
                        setIsUpgradeModalOpen(true);
                      }}
                      disabled={isCurrent}
                      className={`w-full py-3 rounded-xl font-semibold text-xs transition-all active:scale-95 flex items-center justify-center space-x-2 ${
                        isCurrent
                          ? 'bg-slate-800 text-slate-500 cursor-default border border-slate-700'
                          : isPopular
                          ? 'bg-gradient-to-r from-cyan-500 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 text-white shadow-lg shadow-cyan-500/25'
                          : isUltra
                          ? 'bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white shadow-lg shadow-purple-500/25'
                          : 'bg-slate-800 hover:bg-slate-700 text-white border border-slate-700'
                      }`}
                    >
                      <span>{isCurrent ? 'Plan Activo' : `Elegir ${tier.name}`}</span>
                      {!isCurrent && <ChevronRight className="w-4 h-4" />}
                    </button>
                  </div>
                );
              })}
            </div>

            {/* Comparison Matrix with Frontier Models */}
            <div className="bg-[#0f1225]/80 backdrop-blur-md rounded-2xl border border-indigo-500/15 p-6 sm:p-8 space-y-6">
              <div className="text-center space-y-2">
                <h3 className="text-xl font-bold text-white">¿Cómo se compara TruthGPT Cloud con Gemini y ChatGPT?</h3>
                <p className="text-xs text-slate-400">Diseñado con rigor matemático y 0% de tolerancia a alucinaciones lógicas.</p>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="border-b border-slate-800 text-slate-400">
                      <th className="py-3 px-4">Capacidad / Característica</th>
                      <th className="py-3 px-4 font-bold text-cyan-400 bg-cyan-950/20">TruthGPT Cloud (Pro/Ultra)</th>
                      <th className="py-3 px-4">Google Gemini Advanced</th>
                      <th className="py-3 px-4">ChatGPT Plus (o1/o3)</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800 text-slate-300">
                    <tr>
                      <td className="py-3 px-4 font-medium">Solucionador Z3 SMT Formal</td>
                      <td className="py-3 px-4 font-bold text-emerald-400 bg-cyan-950/20">✅ Integrado en Tiempo Real</td>
                      <td className="py-3 px-4 text-red-400">❌ No disponible</td>
                      <td className="py-3 px-4 text-red-400">❌ No disponible</td>
                    </tr>
                    <tr>
                      <td className="py-3 px-4 font-medium">Certificados Criptográficos de Verdad</td>
                      <td className="py-3 px-4 font-bold text-emerald-400 bg-cyan-950/20">✅ Emitidos en cada inferencia</td>
                      <td className="py-3 px-4 text-red-400">❌ No</td>
                      <td className="py-3 px-4 text-red-400">❌ No</td>
                    </tr>
                    <tr>
                      <td className="py-3 px-4 font-medium">Swarm Multi-Agente Autónomo</td>
                      <td className="py-3 px-4 font-bold text-emerald-400 bg-cyan-950/20">✅ Hasta 20 agentes en paralelo</td>
                      <td className="py-3 px-4 text-slate-400">Agente único</td>
                      <td className="py-3 px-4 text-slate-400">Agente único</td>
                    </tr>
                    <tr>
                      <td className="py-3 px-4 font-medium">Consenso Multi-Modelo Cuántico</td>
                      <td className="py-3 px-4 font-bold text-emerald-400 bg-cyan-950/20">✅ DeepSeek + Claude + GPT-4o</td>
                      <td className="py-3 px-4 text-slate-400">Solo Gemini</td>
                      <td className="py-3 px-4 text-slate-400">Solo OpenAI</td>
                    </tr>
                    <tr>
                      <td className="py-3 px-4 font-medium">Compilación de Papers SOTA (1-Click)</td>
                      <td className="py-3 px-4 font-bold text-emerald-400 bg-cyan-950/20">✅ ArXiv / NeurIPS Live Hub</td>
                      <td className="py-3 px-4 text-red-400">❌ No</td>
                      <td className="py-3 px-4 text-red-400">❌ No</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* ========================================================================= */}
        {/* 🛡️ TAB 3: SMT & FORMAL VERIFICATION LAB */}
        {/* ========================================================================= */}
        {activeTab === 'smt_lab' && (
          <div className="space-y-6">
            <div className="bg-[#0f1225]/80 backdrop-blur-md rounded-2xl border border-indigo-500/15 p-6 sm:p-8 space-y-6">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 rounded-xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
                  <Activity className="w-5 h-5" />
                </div>
                <div>
                  <h2 className="text-xl font-bold text-white">Laboratorio de Verificación Formal Z3 SMT</h2>
                  <p className="text-xs text-slate-400">Demuestra teoremas matemáticos, invariantes de software y contratos Hoare en la nube.</p>
                </div>
              </div>

              {/* Formula Editor */}
              <div className="space-y-2">
                <label className="text-xs font-semibold text-slate-300">Proposición Matemática o Invariante Lógico:</label>
                <textarea
                  rows={4}
                  value={smtFormula}
                  onChange={(e) => setSmtFormula(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl p-4 text-xs sm:text-sm font-mono text-cyan-300 focus:outline-none focus:border-cyan-400"
                ></textarea>
              </div>

              {/* Example Presets */}
              <div className="flex flex-wrap gap-2 text-xs">
                <span className="text-slate-400 py-1">Plantillas rápidas:</span>
                {[
                  { name: 'Identidad Cuadrática', formula: '∀x, y ∈ ℝ: (x + y)^2 = x^2 + 2xy + y^2' },
                  { name: 'Criterio de Estabilidad de Lyapunov', formula: 'V(x) > 0 ∧ dV/dt ≤ -α V(x) ⇒ lim_{t→∞} x(t) = 0' },
                  { name: 'Invariante de Partición Quicksort', formula: '∀i < pivot_idx: A[i] ≤ pivot ∧ ∀j > pivot_idx: A[j] ≥ pivot' }
                ].map((p, idx) => (
                  <button
                    key={idx}
                    onClick={() => setSmtFormula(p.formula)}
                    className="px-3 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-[11px] border border-slate-700"
                  >
                    {p.name}
                  </button>
                ))}
              </div>

              {/* Execute Button */}
              <button
                onClick={handleRunSmtVerification}
                disabled={smtLoading}
                className="px-6 py-3 rounded-xl bg-gradient-to-r from-cyan-500 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 text-white text-xs font-bold flex items-center space-x-2 transition-transform active:scale-95 shadow-lg shadow-cyan-500/20"
              >
                {smtLoading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4 fill-current" />}
                <span>{smtLoading ? 'Resolviendo con Z3 SMT Solver...' : 'Ejecutar Verificación Formal'}</span>
              </button>
            </div>

            {/* Results Certificate */}
            {smtResult && (
              <div className="bg-[#0f1225]/80 backdrop-blur-md rounded-2xl border border-emerald-500/30 p-6 space-y-4">
                <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                  <div className="flex items-center space-x-2">
                    <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                    <h3 className="font-bold text-sm text-emerald-300">Certificado de Demostración Formal Emitido</h3>
                  </div>
                  <span className="font-mono text-xs px-2.5 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
                    Status: {smtResult.status}
                  </span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
                  <div className="p-3 rounded-xl bg-slate-900 border border-slate-800">
                    <span className="text-slate-400 block">Motor Solucionador:</span>
                    <strong className="text-slate-200">{smtResult.solver_engine}</strong>
                  </div>
                  <div className="p-3 rounded-xl bg-slate-900 border border-slate-800">
                    <span className="text-slate-400 block">Tiempo de Cómputo:</span>
                    <strong className="text-slate-200">{smtResult.verification_time_ms} ms</strong>
                  </div>
                  <div className="p-3 rounded-xl bg-slate-900 border border-slate-800">
                    <span className="text-slate-400 block">Confianza Axiomática:</span>
                    <strong className="text-emerald-400">{(smtResult.confidence_score * 100).toFixed(2)}%</strong>
                  </div>
                </div>

                <div className="p-3 rounded-xl bg-slate-950 font-mono text-xs text-cyan-300 border border-slate-800 space-y-1">
                  <div className="text-[10px] text-slate-400 uppercase">Invariantes Comprobados:</div>
                  {smtResult.mathematical_invariants.map((inv: string, i: number) => (
                    <div key={i} className="flex items-center space-x-2">
                      <span className="text-emerald-400">✓</span>
                      <span>{inv}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* ========================================================================= */}
        {/* 📚 TAB 4: SOTA PAPERS CLOUD HUB */}
        {/* ========================================================================= */}
        {activeTab === 'papers' && (
          <div className="space-y-6">
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
              <div>
                <h2 className="text-2xl font-bold text-white">SOTA AI Research Cloud Hub</h2>
                <p className="text-xs text-slate-400">Descubre y compila los últimos avances de investigación directamente en tu entorno Cloud.</p>
              </div>
              <span className="text-xs px-3 py-1 rounded-full bg-cyan-500/10 text-cyan-300 border border-cyan-500/30 font-semibold">
                {papers.length} Papers Indexados
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {papers.map((p) => {
                const isApplied = appliedPapers.includes(p.paper_id);
                const isApplying = applyingPaperId === p.paper_id;

                return (
                  <div
                    key={p.paper_id}
                    className="bg-[#0f1225]/80 backdrop-blur-md rounded-2xl border border-indigo-500/15 p-6 flex flex-col justify-between space-y-4 hover:border-cyan-500/30 transition-all"
                  >
                    <div className="space-y-3">
                      <div className="flex justify-between items-center text-[10px]">
                        <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-medium">{p.category}</span>
                        <span className="text-amber-400 font-bold">★ {p.impact_factor}/10</span>
                      </div>
                      <h3 className="font-bold text-sm text-white leading-snug">{p.title}</h3>
                      <p className="text-xs text-slate-400 leading-relaxed">{p.abstract}</p>
                    </div>

                    <div className="space-y-3 border-t border-slate-800 pt-4">
                      <div className="text-[10px] text-slate-400 flex justify-between">
                        <span>Autores: {p.authors.join(', ')}</span>
                        <span>{p.published}</span>
                      </div>

                      <button
                        onClick={() => handleApplyPaper(p.paper_id)}
                        disabled={isApplied || isApplying}
                        className={`w-full py-2.5 rounded-xl font-semibold text-xs flex items-center justify-center space-x-2 transition-transform active:scale-95 ${
                          isApplied
                            ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 cursor-default'
                            : 'bg-gradient-to-r from-cyan-500 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 text-white shadow-md shadow-cyan-500/20'
                        }`}
                      >
                        {isApplying ? (
                          <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                        ) : isApplied ? (
                          <Check className="w-3.5 h-3.5" />
                        ) : (
                          <Download className="w-3.5 h-3.5" />
                        )}
                        <span>{isApplied ? 'Técnica Compilada & Activa' : isApplying ? 'Compilando Pesos...' : '1-Click Cloud Compile'}</span>
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* ========================================================================= */}
        {/* 🔑 TAB 5: DEVELOPER API & CLAVES */}
        {/* ========================================================================= */}
        {activeTab === 'developer' && (
          <div className="space-y-6">
            <div className="bg-[#0f1225]/80 backdrop-blur-md rounded-2xl border border-indigo-500/15 p-6 sm:p-8 space-y-6">
              <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                <div>
                  <h2 className="text-xl font-bold text-white">Claves de API & SDK de Desarrollo</h2>
                  <p className="text-xs text-slate-400">Integra TruthGPT Cloud en tus aplicaciones Python, Node.js y flujos empresariales.</p>
                </div>
                <button
                  onClick={handleGenerateApiKey}
                  className="px-4 py-2 rounded-xl bg-gradient-to-r from-cyan-500 to-indigo-600 text-white text-xs font-semibold flex items-center space-x-1.5 shadow-md shadow-cyan-500/20"
                >
                  <Key className="w-3.5 h-3.5" />
                  <span>Generar Nueva Clave</span>
                </button>
              </div>

              {/* API Keys List */}
              <div className="space-y-3">
                <label className="text-xs font-semibold text-slate-300">Tus Claves de API Activas:</label>
                {userData?.api_keys.map((k, idx) => (
                  <div key={idx} className="flex items-center justify-between p-3 rounded-xl bg-slate-950 border border-slate-800">
                    <span className="font-mono text-xs text-cyan-300">{k}</span>
                    <button
                      onClick={() => copyToClipboard(k, k)}
                      className="flex items-center space-x-1 px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs transition-colors"
                    >
                      {copiedKey === k ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                      <span>{copiedKey === k ? 'Copiado' : 'Copiar'}</span>
                    </button>
                  </div>
                ))}
              </div>

              {/* Code Snippet Tabs */}
              <div className="space-y-3 pt-4 border-t border-slate-800">
                <div className="flex items-center justify-between">
                  <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider">Ejemplo de Integración en Python (SDK)</h3>
                  <span className="text-[10px] text-slate-400">truthgpt_cloud v2.0</span>
                </div>
                <pre className="p-4 rounded-xl bg-slate-950 border border-slate-800 text-xs font-mono text-cyan-300 overflow-x-auto">
{`from truthgpt_cloud import TruthGPTCloudClient, CloudTier

# Inicializar cliente con tu API Key
client = TruthGPTCloudClient(api_key="${userData?.api_keys[0] || 'tgpt_cloud_live_demo'}")

# Inferencia con Verificación Formal Z3 en la Nube
response = client.ask(
    prompt="Demostrar convergencia del optimizador en Espacios de Hilbert",
    enable_formal_verification=True,
    enable_swarm=True
)

print(response.content)
print(f"Hash del Certificado: {response.proof_certificate['proof_tree_hash']}")`}
                </pre>
              </div>
            </div>
          </div>
        )}

        {/* ========================================================================= */}
        {/* 📊 TAB 6: FACTURACIÓN & INVOICES */}
        {/* ========================================================================= */}
        {activeTab === 'billing' && (
          <div className="space-y-6">
            <div className="bg-[#0f1225]/80 backdrop-blur-md rounded-2xl border border-indigo-500/15 p-6 sm:p-8 space-y-6">
              <div className="flex items-center justify-between border-b border-slate-800 pb-4">
                <div>
                  <h2 className="text-xl font-bold text-white">Historial de Facturación & Suscripción</h2>
                  <p className="text-xs text-slate-400">Administra tus métodos de pago, ciclo de renovación y recibos.</p>
                </div>
                <button
                  onClick={() => setActiveTab('pricing')}
                  className="px-3.5 py-1.5 rounded-xl bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 text-xs font-semibold"
                >
                  Cambiar Plan
                </button>
              </div>

              {/* Invoices Table */}
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="border-b border-slate-800 text-slate-400">
                      <th className="py-3 px-4">ID Factura</th>
                      <th className="py-3 px-4">Plan / Nivel</th>
                      <th className="py-3 px-4">Monto</th>
                      <th className="py-3 px-4">Ciclo</th>
                      <th className="py-3 px-4">Fecha</th>
                      <th className="py-3 px-4">Estado</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800 text-slate-300">
                    {userData?.invoices?.map((inv) => (
                      <tr key={inv.invoice_id}>
                        <td className="py-3 px-4 font-mono text-cyan-300">{inv.invoice_id}</td>
                        <td className="py-3 px-4 uppercase font-bold">{inv.tier_id}</td>
                        <td className="py-3 px-4 font-semibold text-white">${inv.amount_usd} USD</td>
                        <td className="py-3 px-4 capitalize">{inv.billing_cycle}</td>
                        <td className="py-3 px-4">{inv.date}</td>
                        <td className="py-3 px-4">
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
                            PAGADO
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* ========================================================================= */}
      {/* 💳 MODAL: UPGRADE & CHECKOUT PASS */}
      {/* ========================================================================= */}
      {isUpgradeModalOpen && selectedTierForUpgrade && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-center justify-center p-4">
          <div className="bg-[#0f1225] border border-cyan-500/40 rounded-3xl p-6 sm:p-8 max-w-md w-full shadow-2xl shadow-cyan-500/20 space-y-6">
            <div className="flex justify-between items-start">
              <div>
                <span className="text-[10px] uppercase font-bold text-cyan-400 bg-cyan-500/10 px-2 py-0.5 rounded border border-cyan-500/30">
                  Upgrade Instantáneo
                </span>
                <h3 className="text-xl font-bold text-white mt-1">Suscribirse a {selectedTierForUpgrade.name}</h3>
              </div>
              <button
                onClick={() => setIsUpgradeModalOpen(false)}
                className="text-slate-400 hover:text-white text-lg font-bold"
              >
                ✕
              </button>
            </div>

            {/* Price Summary */}
            <div className="p-4 rounded-2xl bg-slate-900 border border-slate-800 space-y-2">
              <div className="flex justify-between text-xs text-slate-400">
                <span>Plan Seleccionado:</span>
                <strong className="text-white">{selectedTierForUpgrade.name}</strong>
              </div>
              <div className="flex justify-between text-xs text-slate-400">
                <span>Ciclo de Facturación:</span>
                <strong className="text-white capitalize">{billingCycle}</strong>
              </div>
              <div className="flex justify-between text-sm font-bold text-cyan-300 border-t border-slate-800 pt-2">
                <span>Total a Pagar Hoy:</span>
                <span>
                  ${billingCycle === 'yearly' ? selectedTierForUpgrade.price_yearly_usd : selectedTierForUpgrade.price_monthly_usd} USD
                </span>
              </div>
            </div>

            {/* Payment Method Selector */}
            <div className="space-y-2">
              <label className="text-xs font-semibold text-slate-300">Método de Pago:</label>
              <div className="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={() => setPaymentMethod('stripe_card')}
                  className={`p-3 rounded-xl border flex items-center justify-center space-x-2 text-xs font-semibold transition-all ${
                    paymentMethod === 'stripe_card'
                      ? 'bg-cyan-500/20 border-cyan-400 text-cyan-300'
                      : 'bg-slate-900 border-slate-800 text-slate-400'
                  }`}
                >
                  <CreditCard className="w-4 h-4" />
                  <span>Tarjeta / Stripe</span>
                </button>
                <button
                  type="button"
                  onClick={() => setPaymentMethod('crypto_usdc')}
                  className={`p-3 rounded-xl border flex items-center justify-center space-x-2 text-xs font-semibold transition-all ${
                    paymentMethod === 'crypto_usdc'
                      ? 'bg-cyan-500/20 border-cyan-400 text-cyan-300'
                      : 'bg-slate-900 border-slate-800 text-slate-400'
                  }`}
                >
                  <Lock className="w-4 h-4" />
                  <span>Crypto (USDC)</span>
                </button>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="space-y-2 pt-2">
              <button
                onClick={handleUpgradeSubscription}
                disabled={isUpgrading}
                className="w-full py-3 rounded-xl bg-gradient-to-r from-cyan-500 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 text-white font-bold text-xs flex items-center justify-center space-x-2 transition-transform active:scale-95 shadow-lg shadow-cyan-500/25"
              >
                {isUpgrading ? (
                  <RefreshCw className="w-4 h-4 animate-spin" />
                ) : (
                  <CheckCircle2 className="w-4 h-4" />
                )}
                <span>{isUpgrading ? 'Procesando Pago y Asignando Cuota...' : 'Confirmar y Activar Suscripción'}</span>
              </button>
              <button
                onClick={() => setIsUpgradeModalOpen(false)}
                className="w-full py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-slate-400 text-xs font-medium"
              >
                Cancelar
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* 📜 MODAL: PROOF CERTIFICATE INSPECTOR */}
      {/* ========================================================================= */}
      {activeProofModal && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-center justify-center p-4">
          <div className="bg-[#0f1225] border border-cyan-500/40 rounded-3xl p-6 sm:p-8 max-w-lg w-full shadow-2xl shadow-cyan-500/25 space-y-4">
            <div className="flex justify-between items-center border-b border-slate-800 pb-3">
              <div className="flex items-center space-x-2">
                <ShieldCheck className="w-5 h-5 text-emerald-400" />
                <h3 className="font-bold text-sm text-white">Certificado de Verdad & Prueba Z3 SMT</h3>
              </div>
              <button
                onClick={() => setActiveProofModal(null)}
                className="text-slate-400 hover:text-white font-bold"
              >
                ✕
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                <span className="text-slate-400 block text-[10px] uppercase">Hash Criptográfico de la Prueba:</span>
                <span className="font-mono text-cyan-300 text-xs break-all">{activeProofModal.proof_tree_hash}</span>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div className="p-2.5 rounded-xl bg-slate-900 border border-slate-800">
                  <span className="text-slate-400 block text-[10px]">Motor Solucionador:</span>
                  <strong className="text-slate-200">{activeProofModal.solver_engine}</strong>
                </div>
                <div className="p-2.5 rounded-xl bg-slate-900 border border-slate-800">
                  <span className="text-slate-400 block text-[10px]">Tiempo de Resolución:</span>
                  <strong className="text-slate-200">{activeProofModal.verification_time_ms} ms</strong>
                </div>
              </div>

              <div className="p-3 rounded-xl bg-slate-900 border border-slate-800 space-y-1.5">
                <span className="text-[10px] text-slate-400 uppercase font-semibold">Invariantes Verificados:</span>
                {activeProofModal.mathematical_invariants?.map((inv: string, idx: number) => (
                  <div key={idx} className="text-slate-300 font-mono text-[11px] flex items-center space-x-1.5">
                    <span className="text-emerald-400">✓</span>
                    <span>{inv}</span>
                  </div>
                ))}
              </div>
            </div>

            <button
              onClick={() => setActiveProofModal(null)}
              className="w-full py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-white font-semibold text-xs"
            >
              Cerrar Inspector
            </button>
          </div>
        </div>
      )}

      {/* 🚀 FOOTER */}
      <footer className="border-t border-slate-800 bg-[#080914] px-6 py-6 mt-auto">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between text-xs text-slate-400 gap-4">
          <div className="flex items-center space-x-2">
            <span className="font-bold text-white">TruthGPT Cloud Platform</span>
            <span>• Frontier Model Run Polyglot Architecture</span>
          </div>
          <div className="flex items-center space-x-4 text-[11px]">
            <span>SLA: 99.99% Uptime</span>
            <span>•</span>
            <span>SMT Kernel: Z3 / SymPy</span>
            <span>•</span>
            <span className="text-cyan-400">Latencia: Ultra-Baja TensorRT</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
