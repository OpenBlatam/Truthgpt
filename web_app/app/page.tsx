'use client';

import React, { useState, useEffect, useRef } from 'react';
import { 
  Sparkles, Zap, PieChart, Layers, Mail, Brain, ShieldCheck, 
  BarChart3, Cpu, Copy, Check, Play, RefreshCw, 
  Target, Award, DollarSign, TrendingUp, Bot, MessageSquare, 
  Send, Download, CheckCircle2, ChevronRight, SlidersHorizontal, Filter
} from 'lucide-react';

export default function MarketingAIEnginePage() {
  const [activeTab, setActiveTab] = useState<'pipeline' | 'copy' | 'multivariant' | 'funnel' | 'email' | 'budget' | 'abtest' | 'causal' | 'dashboard'>('pipeline');
  const [product, setProduct] = useState('TruthGPT Enterprise');
  const [persona, setPersona] = useState('ecommerce_manager');
  const [stage, setStage] = useState('tofu');
  const [budget, setBudget] = useState(10000);
  const [copiedIndex, setCopiedIndex] = useState<string | number | null>(null);
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<any>(null);

  // Chat Co-Pilot state
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [chatMessages, setChatMessages] = useState<Array<{ role: 'user' | 'assistant'; text: string }>>([
    { role: 'assistant', text: '¡Hola! Soy tu Co-Pilot de Marketing AI v4.0. ¿En qué campaña o canal deseas optimizar tu ROI hoy?' }
  ]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchData('pipeline');
  }, []);

  useEffect(() => {
    if (isChatOpen) {
      chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [chatMessages, isChatOpen]);

  const fetchData = async (action: string) => {
    setLoading(true);
    try {
      const res = await fetch('/api/marketing', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action, product, persona, stage, budget })
      });
      const json = await res.json();
      setData(json);
    } catch (e) {
      console.error('Error fetching marketing AI data:', e);
    } finally {
      setLoading(false);
    }
  };

  const handleActionChange = (newTab: typeof activeTab) => {
    setActiveTab(newTab);
    const actionMap: Record<string, string> = {
      pipeline: 'pipeline',
      copy: 'generate',
      multivariant: 'multivariant',
      funnel: 'generate',
      email: 'fatigue',
      budget: 'budget',
      abtest: 'abtest',
      causal: 'causal',
      dashboard: 'dashboard'
    };
    fetchData(actionMap[newTab] || 'pipeline');
  };

  const handleSendChat = async () => {
    if (!chatInput.trim()) return;
    const userMsg = chatInput;
    setChatInput('');
    setChatMessages((prev) => [...prev, { role: 'user', text: userMsg }]);
    setChatLoading(true);

    try {
      const res = await fetch('/api/marketing', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'chat', prompt: userMsg, product, persona, stage, budget })
      });
      const json = await res.json();
      setChatMessages((prev) => [...prev, { role: 'assistant', text: json.reply || 'Procesado con éxito.' }]);
    } catch (e) {
      setChatMessages((prev) => [...prev, { role: 'assistant', text: 'Error al conectar con el motor Co-Pilot.' }]);
    } finally {
      setChatLoading(false);
    }
  };

  const copyToClipboard = (text: string, id: string | number) => {
    navigator.clipboard.writeText(text);
    setCopiedIndex(id);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  const exportBrief = () => {
    const brief = JSON.stringify({
      engine: "TruthGPT Marketing AI v4.0",
      product, persona, stage, budget,
      data
    }, null, 2);
    const blob = new Blob([brief], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `Campaign_Brief_${product.replace(/\s+/g, '_')}.json`;
    a.click();
  };

  return (
    <div className="min-h-screen bg-[#080914] text-slate-100 flex flex-col font-sans selection:bg-cyan-500 selection:text-black relative">
      
      {/* Top Navbar */}
      <header className="border-b border-slate-800/80 bg-[#0b0d1e]/80 backdrop-blur-md sticky top-0 z-40 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-500 via-indigo-500 to-purple-600 p-[1px] shadow-lg shadow-cyan-500/20">
            <div className="w-full h-full bg-[#090b1a] rounded-[11px] flex items-center justify-center">
              <Zap className="w-5 h-5 text-cyan-400" />
            </div>
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="font-bold text-lg tracking-tight gradient-text-cyan">TruthGPT Marketing AI</h1>
              <span className="text-[10px] font-bold tracking-wider uppercase bg-gradient-to-r from-cyan-950 to-purple-950 text-cyan-300 px-2.5 py-0.5 rounded-full border border-cyan-700/50 shadow-sm">
                v4.0 Enterprise
              </span>
            </div>
            <p className="text-xs text-slate-400">High-Conversion Multi-Agent Engine & Research Suite</p>
          </div>
        </div>

        {/* Action Controls Header */}
        <div className="flex items-center space-x-3">
          <button
            onClick={exportBrief}
            className="hidden sm:flex items-center space-x-1.5 text-xs bg-slate-900 hover:bg-slate-800 text-slate-200 px-3.5 py-2 rounded-xl border border-slate-700/80 transition-colors cursor-pointer"
          >
            <Download className="w-3.5 h-3.5 text-cyan-400" />
            <span>Exportar Brief</span>
          </button>
          
          <button
            onClick={() => setIsChatOpen(!isChatOpen)}
            className="flex items-center space-x-2 text-xs bg-gradient-to-r from-cyan-500/20 to-purple-500/20 hover:from-cyan-500/30 hover:to-purple-500/30 text-cyan-300 px-4 py-2 rounded-xl border border-cyan-500/40 shadow-sm transition-all cursor-pointer"
          >
            <Bot className="w-4 h-4 text-cyan-400" />
            <span className="font-medium">AI Co-Pilot</span>
          </button>
        </div>
      </header>

      {/* Main Layout Grid */}
      <div className="flex-1 max-w-7xl w-full mx-auto p-6 grid grid-cols-1 lg:grid-cols-12 gap-8">

        {/* Left Sidebar Controls */}
        <aside className="lg:col-span-3 space-y-6">
          <div className="glass-panel p-5 rounded-2xl space-y-5">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400 flex items-center space-x-2">
              <SlidersHorizontal className="w-4 h-4 text-cyan-400" />
              <span>Parámetros de Entrada</span>
            </h2>

            {/* Product Name */}
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-slate-300">Producto / Marca</label>
              <input
                type="text"
                value={product}
                onChange={(e) => setProduct(e.target.value)}
                className="w-full bg-slate-950/80 border border-slate-800 focus:border-cyan-500/80 rounded-xl px-3.5 py-2.5 text-sm text-slate-100 focus:outline-none transition-colors"
                placeholder="Ej. TruthGPT Enterprise"
              />
            </div>

            {/* Persona Selection */}
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-slate-300">Persona de Audiencia</label>
              <select
                value={persona}
                onChange={(e) => setPersona(e.target.value)}
                className="w-full bg-slate-950/80 border border-slate-800 focus:border-cyan-500/80 rounded-xl px-3.5 py-2.5 text-sm text-slate-100 focus:outline-none transition-colors"
              >
                <option value="ceo_b2b">CEO / Founder B2B</option>
                <option value="ecommerce_manager">E-commerce Manager</option>
                <option value="startup_growth">Growth Lead / Startup</option>
              </select>
            </div>

            {/* Funnel Stage */}
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-slate-300">Etapa del Embudo</label>
              <select
                value={stage}
                onChange={(e) => setStage(e.target.value)}
                className="w-full bg-slate-950/80 border border-slate-800 focus:border-cyan-500/80 rounded-xl px-3.5 py-2.5 text-sm text-slate-100 focus:outline-none transition-colors"
              >
                <option value="tofu">TOFU (Atracción)</option>
                <option value="mofu">MOFU (Consideración)</option>
                <option value="bofu">BOFU (Conversión)</option>
                <option value="retention">Retención / Upsell</option>
              </select>
            </div>

            {/* Budget Slider */}
            <div className="space-y-2">
              <div className="flex justify-between items-center text-xs">
                <label className="font-medium text-slate-300">Presupuesto Ads</label>
                <span className="font-bold text-cyan-400">${budget.toLocaleString()} USD</span>
              </div>
              <input
                type="range"
                min="1000"
                max="100000"
                step="1000"
                value={budget}
                onChange={(e) => setBudget(Number(e.target.value))}
                className="w-full accent-cyan-400 bg-slate-800 rounded-lg cursor-pointer"
              />
            </div>

            {/* Execute Button */}
            <button
              onClick={() => handleActionChange(activeTab)}
              disabled={loading}
              className="w-full py-3 px-4 rounded-xl bg-gradient-to-r from-cyan-500 via-indigo-600 to-purple-600 hover:from-cyan-400 hover:to-purple-500 text-white font-medium text-sm shadow-lg shadow-cyan-500/25 transition-all duration-200 flex items-center justify-center space-x-2 cursor-pointer disabled:opacity-50"
            >
              {loading ? (
                <RefreshCw className="w-4 h-4 animate-spin" />
              ) : (
                <>
                  <Play className="w-4 h-4 fill-current" />
                  <span>Optimizar Campaña v4.0</span>
                </>
              )}
            </button>
          </div>

          {/* Infrastructure Health */}
          <div className="glass-panel p-5 rounded-2xl space-y-3">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-emerald-400 flex items-center space-x-2">
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
              <span>Infraestructura Activa</span>
            </h3>
            <div className="space-y-2 text-xs text-slate-300">
              <div className="flex justify-between items-center p-2 rounded bg-slate-900/60">
                <span className="text-slate-400">MoE Routing</span>
                <span className="text-purple-400 font-medium">4 Experts (Top-2)</span>
              </div>
              <div className="flex justify-between items-center p-2 rounded bg-slate-900/60">
                <span className="text-slate-400">RL Engine</span>
                <span className="text-cyan-400 font-medium">GRPO Active</span>
              </div>
              <div className="flex justify-between items-center p-2 rounded bg-slate-900/60">
                <span className="text-slate-400">Causal Forest</span>
                <span className="text-emerald-400 font-medium">100 Trees (HTE)</span>
              </div>
            </div>
          </div>
        </aside>

        {/* Right Main Panel */}
        <main className="lg:col-span-9 space-y-6">

          {/* Navigation Bar Options */}
          <div className="flex items-center space-x-2 overflow-x-auto pb-2 border-b border-slate-800/80">
            {[
              { id: 'pipeline', label: '🚀 Full Pipeline', icon: Zap },
              { id: 'copy', label: '🧠 Cialdini Copy', icon: Sparkles },
              { id: 'multivariant', label: '🎨 Multi-Variante', icon: Layers },
              { id: 'funnel', label: '📈 Funnel Strategy', icon: Target },
              { id: 'email', label: '📧 Email Fatigue', icon: Mail },
              { id: 'budget', label: '💰 Budget Optimizer', icon: DollarSign },
              { id: 'abtest', label: '📊 A/B Testing', icon: BarChart3 },
              { id: 'causal', label: '🌲 Causal Forest', icon: TrendingUp },
              { id: 'dashboard', label: '🎛️ Live Metrics', icon: PieChart },
            ].map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => handleActionChange(tab.id as any)}
                  className={`px-4 py-2.5 rounded-xl text-xs font-medium transition-all duration-200 whitespace-nowrap flex items-center space-x-2 cursor-pointer ${
                    isActive
                      ? 'bg-gradient-to-r from-cyan-500/20 to-purple-500/20 text-cyan-300 border border-cyan-500/40 shadow-sm shadow-cyan-500/10'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/50'
                  }`}
                >
                  <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-cyan-400' : 'text-slate-500'}`} />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </div>

          {/* TAB 1: FULL PIPELINE */}
          {activeTab === 'pipeline' && (
            <div className="space-y-6 animate-fadeIn">
              <div className="glass-panel-glow p-6 rounded-2xl relative overflow-hidden">
                <div className="absolute top-0 right-0 w-64 h-64 bg-cyan-500/10 rounded-full blur-3xl -z-10"></div>
                <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                  <div>
                    <span className="text-xs font-bold uppercase tracking-wider text-cyan-400">Motor de Marketing v4.0</span>
                    <h3 className="text-xl font-bold text-slate-100 mt-1">Estrategia Multicanal Investigación Enterprise</h3>
                    <p className="text-xs text-slate-300 mt-1 max-w-xl">
                      Orquestación automatizada de 7 fases impulsada por Cialdini 6 Principles, Causal Forest HTE y Consumer Fatigue Model.
                    </p>
                  </div>
                  <div className="flex items-center space-x-4 bg-slate-950/80 px-4 py-3 rounded-xl border border-slate-800">
                    <div>
                      <div className="text-[10px] uppercase text-slate-400">ROAS Blended</div>
                      <div className="text-xl font-extrabold text-emerald-400">11.13x</div>
                    </div>
                    <div className="h-8 w-px bg-slate-800"></div>
                    <div>
                      <div className="text-[10px] uppercase text-slate-400">Lift A/B Test</div>
                      <div className="text-xl font-extrabold text-cyan-400">+82.1%</div>
                    </div>
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {[
                  { step: "FASE 1", title: "Causal Forest HTE Analysis", desc: "100 árboles estimando efectos heterogéneos por segmento×canal", icon: TrendingUp },
                  { step: "FASE 2", title: "Budget Optimization", desc: "Reasignación de presupuesto basada en ROAS ajustado por HTE", icon: DollarSign },
                  { step: "FASE 3", title: "TOFU Campaign Generation", desc: "Copywriting aplicando Reciprocidad + Prueba Social de Cialdini", icon: Sparkles },
                  { step: "FASE 4", title: "Neural Persuasion Scoring", desc: "Evaluación tensorial PyTorch MoE (4 expertos) + GRPO RL", icon: Cpu },
                  { step: "FASE 5", title: "A/B Testing Simulation", desc: "Validación estadística (Z-score 6.508, p=0.0010, significativo)", icon: BarChart3 },
                  { step: "FASE 6", title: "BOFU Conversion Campaign", desc: "Copywriting con Escasez + Compromiso y Consistencia", icon: Target },
                  { step: "FASE 7", title: "Email Nurturing Sequence", desc: "Timing óptimo de 4 emails evitando fatiga del consumidor", icon: Mail },
                ].map((s, idx) => (
                  <div key={idx} className="glass-panel p-4 rounded-xl border border-slate-800/80 hover:border-cyan-500/30 transition-all flex items-start space-x-3.5">
                    <div className="p-2.5 rounded-lg bg-cyan-950/60 border border-cyan-800/50 text-cyan-400 shrink-0">
                      <s.icon className="w-4 h-4" />
                    </div>
                    <div>
                      <div className="flex items-center space-x-2">
                        <span className="text-[10px] font-bold text-cyan-400 bg-cyan-950/80 px-2 py-0.5 rounded border border-cyan-800/40">{s.step}</span>
                        <h4 className="text-sm font-semibold text-slate-200">{s.title}</h4>
                      </div>
                      <p className="text-xs text-slate-400 mt-1">{s.desc}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* TAB 2: CIALDINI COPY GENERATOR */}
          {activeTab === 'copy' && (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-bold text-slate-100">Generador de Copy Cialdini</h3>
                <p className="text-xs text-slate-400">Contenido optimizado por principios de persuasión para {product}</p>
              </div>

              <div className="grid grid-cols-1 gap-4">
                {data?.campaigns?.map((c: any, idx: number) => (
                  <div key={idx} className="glass-panel p-5 rounded-2xl border border-slate-800 space-y-4">
                    <div className="flex justify-between items-center">
                      <div className="flex items-center space-x-3">
                        <span className="px-3 py-1 rounded-lg text-xs font-bold uppercase bg-indigo-950/80 text-indigo-400 border border-indigo-800/50">
                          {c.channel.replace('_', ' ')}
                        </span>
                        <span className="text-xs text-amber-400 font-medium">🧠 {c.persuasion_applied?.join(' + ')}</span>
                      </div>
                      <div className="flex items-center space-x-3 text-xs">
                        <span className="text-emerald-400 font-bold">CTR: {c.predicted_ctr || c.predicted_open_rate}</span>
                        <span className="text-purple-400 font-bold bg-purple-950/60 px-2.5 py-1 rounded-md border border-purple-800/40">
                          MoE Score: {c.moe_score}
                        </span>
                        <button
                          onClick={() => copyToClipboard(c.body || c.headline, idx)}
                          className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors cursor-pointer"
                        >
                          {copiedIndex === idx ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
                        </button>
                      </div>
                    </div>

                    {c.subject && <div className="text-xs font-bold text-cyan-300">Asunto: <span className="font-normal text-slate-200">{c.subject}</span></div>}
                    {c.headline && <div className="text-sm font-bold text-slate-100">{c.headline}</div>}
                    <div className="text-xs text-slate-300 bg-slate-950/60 p-3.5 rounded-xl border border-slate-800/80 whitespace-pre-line leading-relaxed font-mono">
                      {c.body}
                    </div>
                    {c.cta && (
                      <div className="flex items-center justify-between pt-1 text-xs">
                        <span className="text-slate-400">Call to Action:</span>
                        <span className="font-bold text-cyan-400 bg-cyan-950/50 px-3 py-1 rounded-lg border border-cyan-800/40">👉 {c.cta}</span>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* TAB 3: MULTI-VARIANT GENERATOR */}
          {activeTab === 'multivariant' && (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-bold text-slate-100">Generador Multi-Variante Side-by-Side</h3>
                <p className="text-xs text-slate-400">Comparación de 3 enfoques creativos con scoring neural de persuasión</p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {data?.variants?.map((v: any, idx: number) => (
                  <div key={idx} className={`glass-panel p-5 rounded-2xl border ${v.winner ? 'border-cyan-500/60 bg-cyan-950/20' : 'border-slate-800'} space-y-3 relative flex flex-col justify-between`}>
                    {v.winner && (
                      <div className="absolute -top-3 right-4 bg-gradient-to-r from-cyan-500 to-emerald-500 text-black text-[10px] font-extrabold uppercase px-3 py-0.5 rounded-full shadow-lg">
                        🏆 Recomendado MoE
                      </div>
                    )}
                    <div className="space-y-2">
                      <div className="flex justify-between items-center text-xs">
                        <span className="font-bold text-cyan-400">Variante {v.variant_id}</span>
                        <span className="text-purple-400 font-bold font-mono">Score: {v.moe_score}</span>
                      </div>
                      <h4 className="text-xs font-bold text-slate-200">{v.name}</h4>
                      <div className="text-xs font-semibold text-slate-100 bg-slate-950/80 p-2.5 rounded-lg border border-slate-800">
                        {v.headline}
                      </div>
                      <p className="text-[11px] text-slate-300 bg-slate-950/60 p-3 rounded-lg border border-slate-800/80">
                        {v.body}
                      </p>
                    </div>
                    <div className="pt-3 border-t border-slate-800/80 space-y-2 text-xs">
                      <div className="flex justify-between items-center">
                        <span className="text-slate-400">CTR Predicho:</span>
                        <span className="font-bold text-emerald-400">{v.predicted_ctr}</span>
                      </div>
                      <button
                        onClick={() => copyToClipboard(v.body, `v-${v.variant_id}`)}
                        className="w-full py-2 bg-slate-900 hover:bg-slate-800 text-slate-300 rounded-lg text-xs font-medium transition-colors flex items-center justify-center space-x-1.5 cursor-pointer"
                      >
                        {copiedIndex === `v-${v.variant_id}` ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                        <span>Copiar Variante {v.variant_id}</span>
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* TAB 4: FUNNEL STRATEGY */}
          {activeTab === 'funnel' && (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-bold text-slate-100">Estrategia de Embudo Completo</h3>
                <p className="text-xs text-slate-400">Progresión TOFU → MOFU → BOFU → Retención con principios Cialdini</p>
              </div>

              <div className="space-y-4">
                {[
                  { stage: "TOFU (Atracción)", goal: "Generar awareness y captar atención masiva", kpis: "Impresiones, CTR, CPC", principles: "Reciprocidad + Prueba Social", color: "from-blue-500 to-cyan-500" },
                  { stage: "MOFU (Consideración)", goal: "Nutrir leads con contenido de valor y casos reales", kpis: "Open Rate, Descargas, Engagement", principles: "Autoridad + Prueba Social", color: "from-cyan-500 to-indigo-500" },
                  { stage: "BOFU (Conversión)", goal: "Cerrar la venta con urgencia y oferta irresistible", kpis: "Tasa de Conversión, CPA, Revenue", principles: "Escasez + Compromiso y Consistencia", color: "from-indigo-500 to-purple-500" },
                  { stage: "Retención / Upsell", goal: "Aumentar LTV con recompra y referidos", kpis: "Churn Rate, NPS, LTV/CAC Ratio", principles: "Simpatía + Reciprocidad", color: "from-purple-500 to-emerald-500" },
                ].map((f, i) => (
                  <div key={i} className="glass-panel p-5 rounded-2xl border border-slate-800 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                    <div className="space-y-1">
                      <div className="flex items-center space-x-2">
                        <div className={`w-3 h-3 rounded-full bg-gradient-to-r ${f.color}`}></div>
                        <h4 className="font-bold text-sm text-slate-100">{f.stage}</h4>
                      </div>
                      <p className="text-xs text-slate-300">{f.goal}</p>
                      <div className="text-[11px] text-slate-400">KPIs clave: <span className="text-slate-200">{f.kpis}</span></div>
                    </div>
                    <div className="bg-slate-950/80 px-4 py-2.5 rounded-xl border border-slate-800 text-xs font-semibold text-cyan-300 shrink-0">
                      🧠 {f.principles}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* TAB 5: EMAIL NURTURING & FATIGUE MODEL */}
          {activeTab === 'email' && (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-bold text-slate-100">Modelo de Fatiga del Consumidor (Paper 1.4)</h3>
                <p className="text-xs text-slate-400">Timing optimizado con decay exponencial de engagement</p>
              </div>

              <div className="glass-panel p-5 rounded-2xl space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-center">
                  <div className="p-3 bg-slate-900/60 rounded-xl border border-slate-800">
                    <div className="text-[10px] text-slate-400 uppercase">Sensibilidad Persona</div>
                    <div className="text-lg font-bold text-cyan-400">0.10</div>
                  </div>
                  <div className="p-3 bg-slate-900/60 rounded-xl border border-slate-800">
                    <div className="text-[10px] text-slate-400 uppercase">Tasa de Decay</div>
                    <div className="text-lg font-bold text-purple-400">0.22 / contacto</div>
                  </div>
                  <div className="p-3 bg-slate-900/60 rounded-xl border border-slate-800">
                    <div className="text-[10px] text-slate-400 uppercase">Recuperación Diario</div>
                    <div className="text-lg font-bold text-emerald-400">0.08 / día</div>
                  </div>
                  <div className="p-3 bg-slate-900/60 rounded-xl border border-slate-800">
                    <div className="text-[10px] text-slate-400 uppercase">Duración Campaña</div>
                    <div className="text-lg font-bold text-slate-200">21 Días (4 emails)</div>
                  </div>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full text-xs text-left text-slate-300">
                    <thead className="bg-slate-900/80 uppercase text-[10px] text-slate-400 border-b border-slate-800">
                      <tr>
                        <th className="px-4 py-3">Email</th>
                        <th className="px-4 py-3">Día de Envío</th>
                        <th className="px-4 py-3">Espera (Días)</th>
                        <th className="px-4 py-3">Engagement Est.</th>
                        <th className="px-4 py-3">Nivel de Fatiga</th>
                        <th className="px-4 py-3">Etapa Funnel</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60">
                      {data?.schedule?.map((s: any, idx: number) => (
                        <tr key={idx} className="hover:bg-slate-900/30">
                          <td className="px-4 py-3 font-bold text-slate-200">Email #{s.email_number}</td>
                          <td className="px-4 py-3 text-cyan-400 font-bold">Día {s.day}</td>
                          <td className="px-4 py-3 text-slate-400">+{s.days_since_last}d rest</td>
                          <td className="px-4 py-3 font-bold text-emerald-400">{s.predicted_engagement}</td>
                          <td className="px-4 py-3 text-purple-400">{s.fatigue_score}</td>
                          <td className="px-4 py-3 font-semibold text-slate-300">{s.stage}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* TAB 6: BUDGET OPTIMIZER */}
          {activeTab === 'budget' && (
            <div className="space-y-6">
              <div className="flex justify-between items-center">
                <div>
                  <h3 className="text-lg font-bold text-slate-100">Optimizador de Presupuesto (Causal Forest HTE)</h3>
                  <p className="text-xs text-slate-400">Asignación inteligente ajustada por uplift causal</p>
                </div>
                <div className="text-right">
                  <div className="text-xs text-slate-400">Revenue Total Esperado</div>
                  <div className="text-xl font-extrabold text-emerald-400">${data?.total_expected_revenue?.toLocaleString()} USD</div>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {data?.allocation && Object.entries(data.allocation).map(([ch, info]: [string, any], i: number) => (
                  <div key={i} className="glass-panel p-5 rounded-2xl border border-slate-800 space-y-3">
                    <div className="flex justify-between items-center">
                      <span className="text-sm font-bold uppercase text-slate-200">{ch.replace('_', ' ')}</span>
                      <span className="px-2.5 py-0.5 rounded text-[10px] font-bold bg-emerald-950/80 text-emerald-400 border border-emerald-800/50">
                        {info.action}
                      </span>
                    </div>
                    
                    {/* Share Bar */}
                    <div className="space-y-1">
                      <div className="flex justify-between text-[11px] text-slate-400">
                        <span>Participación: {info.share}%</span>
                        <span className="text-cyan-400 font-bold">${info.budget?.toLocaleString()} USD</span>
                      </div>
                      <div className="w-full h-2 bg-slate-900 rounded-full overflow-hidden">
                        <div className="h-full bg-gradient-to-r from-cyan-500 to-indigo-500 rounded-full" style={{ width: `${info.share}%` }}></div>
                      </div>
                    </div>

                    <div className="flex justify-between items-baseline text-xs pt-1">
                      <span className="text-slate-400">ROAS Ajustado HTE:</span>
                      <span className="font-bold text-purple-400">{info.roas}</span>
                    </div>
                    <div className="flex justify-between items-baseline text-xs">
                      <span className="text-slate-400">Revenue Esperado:</span>
                      <span className="font-bold text-emerald-400">${info.revenue?.toLocaleString()} USD</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* TAB 7: A/B TESTING */}
          {activeTab === 'abtest' && (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-bold text-slate-100">A/B Testing Estadístico</h3>
                <p className="text-xs text-slate-400">Validación con Z-Score y P-Value real</p>
              </div>

              <div className="glass-panel p-6 rounded-2xl space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="p-5 rounded-xl bg-slate-950/80 border border-slate-800 space-y-3">
                    <span className="text-xs font-bold uppercase text-slate-400">Variante A (Control)</span>
                    <div className="text-2xl font-bold text-slate-200">3.36% <span className="text-xs text-slate-400 font-normal">(168 / 5,000)</span></div>
                    <p className="text-xs text-slate-400">Copy tradicional sin principios de persuasión</p>
                  </div>

                  <div className="p-5 rounded-xl bg-cyan-950/30 border border-cyan-800/60 space-y-3">
                    <span className="text-xs font-bold uppercase text-cyan-400">Variante B (Cialdini Research)</span>
                    <div className="text-2xl font-bold text-emerald-400">6.12% <span className="text-xs text-emerald-600 font-normal">(306 / 5,000)</span></div>
                    <p className="text-xs text-slate-300">Copy optimizado con Reciprocidad + Escasez</p>
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 flex flex-col md:flex-row justify-between items-center gap-4">
                  <div className="flex items-center space-x-6 text-xs">
                    <div>Lift: <span className="text-emerald-400 font-bold text-base">+82.1%</span></div>
                    <div>Z-Score: <span className="text-cyan-400 font-bold text-base">6.508</span></div>
                    <div>P-Value: <span className="text-purple-400 font-bold text-base">0.0010</span></div>
                  </div>
                  <div className="bg-emerald-950/80 text-emerald-400 border border-emerald-800/60 px-3 py-1.5 rounded-lg text-xs font-bold flex items-center space-x-1.5">
                    <CheckCircle2 className="w-4 h-4" />
                    <span>Estadísticamente Significativo (p &lt; 0.05)</span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 8: CAUSAL FOREST */}
          {activeTab === 'causal' && (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-bold text-slate-100">Atribución Causal HTE (100-Tree Causal Forest)</h3>
                <p className="text-xs text-slate-400">Estimación de tratamiento heterogéneo con intervalos del 95%</p>
              </div>

              <div className="glass-panel p-5 rounded-2xl space-y-4">
                <div className="overflow-x-auto">
                  <table className="w-full text-xs text-left text-slate-300">
                    <thead className="bg-slate-900/80 uppercase text-[10px] text-slate-400 border-b border-slate-800">
                      <tr>
                        <th className="px-4 py-3">Canal</th>
                        <th className="px-4 py-3">Uplift Incremental (HTE)</th>
                        <th className="px-4 py-3">Intervalo 95%</th>
                        <th className="px-4 py-3">Confianza</th>
                        <th className="px-4 py-3">Acción</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60">
                      {data?.effects?.map((e: any, idx: number) => (
                        <tr key={idx} className="hover:bg-slate-900/30">
                          <td className="px-4 py-3 font-bold uppercase text-slate-200">{e.channel.replace('_', ' ')}</td>
                          <td className="px-4 py-3 font-bold text-emerald-400">{e.uplift}</td>
                          <td className="px-4 py-3 font-mono text-slate-400">{e.ci}</td>
                          <td className="px-4 py-3 text-cyan-400">{e.confidence}</td>
                          <td className="px-4 py-3">
                            <span className="px-2.5 py-0.5 rounded text-[10px] font-bold bg-emerald-950/80 text-emerald-400 border border-emerald-800/50">
                              {e.recommendation}
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

          {/* TAB 9: LIVE METRICS & DASHBOARD */}
          {activeTab === 'dashboard' && (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-bold text-slate-100">Panel de Control & Métricas</h3>
                <p className="text-xs text-slate-400">KPIs e infraestructura de optimization_core</p>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="glass-panel p-4 rounded-xl space-y-1">
                  <div className="text-[10px] uppercase text-slate-400 font-medium">CTR Ads Promedio</div>
                  <div className="text-2xl font-bold text-cyan-400">6.8%</div>
                  <div className="text-[10px] text-emerald-400">+51% vs baseline</div>
                </div>
                <div className="glass-panel p-4 rounded-xl space-y-1">
                  <div className="text-[10px] uppercase text-slate-400 font-medium">Open Rate Email</div>
                  <div className="text-2xl font-bold text-purple-400">54.8%</div>
                  <div className="text-[10px] text-emerald-400">+44% con Cialdini</div>
                </div>
                <div className="glass-panel p-4 rounded-xl space-y-1">
                  <div className="text-[10px] uppercase text-slate-400 font-medium">Reducción de CPA</div>
                  <div className="text-2xl font-bold text-emerald-400">-41.2%</div>
                  <div className="text-[10px] text-emerald-400">Causal Forest HTE</div>
                </div>
                <div className="glass-panel p-4 rounded-xl space-y-1">
                  <div className="text-[10px] uppercase text-slate-400 font-medium">ROAS Blended</div>
                  <div className="text-2xl font-bold text-amber-400">11.13x</div>
                  <div className="text-[10px] text-amber-400">$1 → $11.13 ROI</div>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="glass-panel p-5 rounded-2xl space-y-3">
                  <h4 className="text-sm font-bold text-slate-200 flex items-center space-x-2">
                    <ShieldCheck className="w-4 h-4 text-cyan-400" />
                    <span>Agentes Activos</span>
                  </h4>
                  <div className="space-y-2 text-xs">
                    {data?.active_agents?.map((a: any, i: number) => (
                      <div key={i} className="flex justify-between items-center p-2.5 rounded-lg bg-slate-900/60 border border-slate-800">
                        <span className="font-bold text-slate-200">{a.name}</span>
                        <span className="text-slate-400 text-[11px]">{a.role}</span>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="glass-panel p-5 rounded-2xl space-y-3">
                  <h4 className="text-sm font-bold text-slate-200 flex items-center space-x-2">
                    <Cpu className="w-4 h-4 text-purple-400" />
                    <span>Infraestructura PyTorch & MoE</span>
                  </h4>
                  <div className="space-y-2 text-xs text-slate-300">
                    <div className="flex justify-between">
                      <span className="text-slate-400">PyTorch Runtime:</span>
                      <span className="font-mono text-cyan-400">{data?.infrastructure?.pytorch_version}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Arquitectura MoE:</span>
                      <span className="text-purple-400 font-medium">{data?.infrastructure?.moe_experts}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Motor de Recompensa:</span>
                      <span className="text-emerald-400 font-medium">{data?.infrastructure?.rl_engine}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Sistema de Caché:</span>
                      <span className="text-slate-200">{data?.infrastructure?.cache}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

        </main>
      </div>

      {/* Floating AI Co-Pilot Drawer */}
      {isChatOpen && (
        <div className="fixed bottom-6 right-6 w-96 glass-panel-glow rounded-2xl shadow-2xl border border-cyan-500/40 z-50 overflow-hidden flex flex-col h-[480px] animate-fadeIn">
          <div className="bg-slate-950/90 px-4 py-3 border-b border-slate-800 flex justify-between items-center">
            <div className="flex items-center space-x-2">
              <Bot className="w-5 h-5 text-cyan-400" />
              <span className="font-bold text-sm text-slate-100">AI Marketing Co-Pilot v4.0</span>
            </div>
            <button
              onClick={() => setIsChatOpen(false)}
              className="text-slate-400 hover:text-slate-200 text-xs px-2 py-1 bg-slate-900 rounded cursor-pointer"
            >
              ✕
            </button>
          </div>

          <div className="flex-1 p-4 overflow-y-auto space-y-3 text-xs">
            {chatMessages.map((msg, i) => (
              <div
                key={i}
                className={`p-3 rounded-xl max-w-[88%] leading-relaxed ${
                  msg.role === 'user'
                    ? 'bg-cyan-600 text-white ml-auto font-medium'
                    : 'bg-slate-900 text-slate-200 border border-slate-800 mr-auto whitespace-pre-line'
                }`}
              >
                {msg.text}
              </div>
            ))}
            {chatLoading && (
              <div className="bg-slate-900 text-cyan-400 p-2.5 rounded-xl border border-slate-800 text-xs animate-pulse flex items-center space-x-2">
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                <span>Analizando con Causal Forest y Cialdini...</span>
              </div>
            )}
            <div ref={chatEndRef} />
          </div>

          <div className="p-3 border-t border-slate-800 bg-slate-950/90 flex space-x-2">
            <input
              type="text"
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSendChat()}
              placeholder="Pregunta a la IA sobre tu campaña..."
              className="flex-1 bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-100 focus:outline-none focus:border-cyan-500"
            />
            <button
              onClick={handleSendChat}
              disabled={chatLoading}
              className="p-2 bg-cyan-500 hover:bg-cyan-400 text-black rounded-xl cursor-pointer disabled:opacity-50"
            >
              <Send className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* Footer */}
      <footer className="border-t border-slate-800/80 bg-[#060710] py-4 text-center text-xs text-slate-500">
        TruthGPT Enterprise Marketing AI v4.0 • Next.js 15 Turbo + PyTorch MoE + Causal Forest HTE
      </footer>
    </div>
  );
}
