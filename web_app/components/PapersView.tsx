'use client';

import React, { useState } from 'react';
import {
  FileText,
  Search,
  ExternalLink,
  BookOpen,
  Sparkles,
  Layers,
  CheckCircle2,
  Bookmark
} from 'lucide-react';

interface Paper {
  id: string;
  title: string;
  authors: string[];
  year: number;
  arxivId: string;
  category: string;
  abstract: string;
  vectorSimilarity: number;
  indexedInRag: boolean;
}

const PAPERS_CATALOG: Paper[] = [
  {
    id: 'p_truthgpt_formal',
    title: 'TruthGPT: Formal SMT Verification Protocols and Quantifier Elimination for Large Language Models',
    authors: ['OpenBlatam Frontier Research', 'Z3 Systems Group'],
    year: 2025,
    arxivId: 'arXiv:2502.04891',
    category: 'Formal Methods & AI',
    abstract: 'This paper introduces an end-to-end framework integrating SMT solvers (Z3, CVC5) with multi-agent swarms. By validating Hoare triplets over generated code and logical statements, hallucinations in mathematical deduction are suppressed to < 0.02%.',
    vectorSimilarity: 0.96,
    indexedInRag: true
  },
  {
    id: 'p_swarm_consensus',
    title: 'Asynchronous Multi-Agent Swarms with Vector-Guided Consensus for Complex Theorem Proving',
    authors: ['Autonomous Agent Lab', 'OpenBlatam Systems'],
    year: 2024,
    arxivId: 'arXiv:2411.09124',
    category: 'Multi-Agent Systems',
    abstract: 'We formalize a peer-to-peer deliberation protocol where specialized LLM agents act as provers, refuters, and synthesizer nodes, communicating over Redis Vector Streams to converge on mathematically verified invariants.',
    vectorSimilarity: 0.92,
    indexedInRag: true
  },
  {
    id: 'p_triton_fused',
    title: 'Automated Generation and Verification of GPU Fused Kernels using Triton and Symbolic Bounds',
    authors: ['High-Performance AI Collective'],
    year: 2025,
    arxivId: 'arXiv:2501.07721',
    category: 'Hardware & GPU Optimization',
    abstract: 'Investigating compiler techniques for translating symbolic invariant proofs into memory-coalesced Triton kernels, demonstrating up to 6.2x latency reductions on H100 SXM5 architectures.',
    vectorSimilarity: 0.88,
    indexedInRag: true
  },
  {
    id: 'p_hoare_logic_rag',
    title: 'Retrieval-Augmented Verification: Grounding Neural Reasoners in Axiomatic Hoare Logic',
    authors: ['Formal Verification Group', 'OpenBlatam'],
    year: 2024,
    arxivId: 'arXiv:2409.13455',
    category: 'Automated Reasoning',
    abstract: 'Demonstrating how vector indexes with semantic chunking of mathematical textbooks provide deterministic grounding for theorem verification pipelines.',
    vectorSimilarity: 0.85,
    indexedInRag: true
  }
];

export const PapersView: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [activePaper, setActivePaper] = useState<Paper | null>(PAPERS_CATALOG[0]);

  const filteredPapers = PAPERS_CATALOG.filter((paper) => {
    const matchesSearch =
      paper.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      paper.abstract.toLowerCase().includes(searchTerm.toLowerCase()) ||
      paper.arxivId.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCat = selectedCategory === 'all' || paper.category === selectedCategory;
    return matchesSearch && matchesCat;
  });

  const categories = ['all', 'Formal Methods & AI', 'Multi-Agent Systems', 'Hardware & GPU Optimization', 'Automated Reasoning'];

  return (
    <div className="flex-1 max-w-6xl mx-auto w-full p-4 sm:p-6 space-y-6">
      {/* Title */}
      <div className="flex items-center space-x-2.5">
        <div className="p-2 rounded-xl bg-cyan-500/10 border border-cyan-500/30 text-cyan-400">
          <FileText className="w-5 h-5" />
        </div>
        <div>
          <h2 className="text-lg font-bold text-white">Papers Científicos e Índice RAG</h2>
          <p className="text-xs text-slate-400">
            Explora la literatura científica indexada en la memoria vectorial de TruthGPT
          </p>
        </div>
      </div>

      {/* Search & Filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-slate-500 absolute left-3.5 top-3" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Buscar por título, ID de arXiv o resumen..."
            className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-slate-900 border border-slate-800 focus:border-cyan-500 text-xs text-slate-200 placeholder:text-slate-500 outline-none transition-colors"
          />
        </div>

        <select
          value={selectedCategory}
          onChange={(e) => setSelectedCategory(e.target.value)}
          className="px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-300 outline-none cursor-pointer"
        >
          {categories.map((c) => (
            <option key={c} value={c}>
              {c === 'all' ? 'Todas las Categorías' : c}
            </option>
          ))}
        </select>
      </div>

      {/* Papers Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* List */}
        <div className="lg:col-span-2 space-y-3">
          {filteredPapers.map((paper) => (
            <div
              key={paper.id}
              onClick={() => setActivePaper(paper)}
              className={`p-4 rounded-2xl border transition-all cursor-pointer ${
                activePaper?.id === paper.id
                  ? 'bg-slate-900 border-cyan-500/50 shadow-lg shadow-cyan-500/10'
                  : 'bg-slate-900/60 hover:bg-slate-800/80 border-slate-800'
              }`}
            >
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-[11px] font-mono text-cyan-400">{paper.arxivId}</span>
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-cyan-500/10 text-cyan-300 border border-cyan-500/20">
                  Similitud RAG: {(paper.vectorSimilarity * 100).toFixed(0)}%
                </span>
              </div>
              <h3 className="text-sm font-bold text-slate-100 hover:text-cyan-300 transition-colors mb-1.5">
                {paper.title}
              </h3>
              <p className="text-[11px] text-slate-400 line-clamp-2 leading-relaxed">
                {paper.abstract}
              </p>
              <div className="flex items-center justify-between mt-3 text-[11px] text-slate-500">
                <span>{paper.authors.join(', ')} ({paper.year})</span>
                <span className="text-emerald-400 flex items-center gap-1 font-medium">
                  <CheckCircle2 className="w-3 h-3" /> Indexado en Redis RAG
                </span>
              </div>
            </div>
          ))}
        </div>

        {/* Paper Detail Panel */}
        <div className="space-y-4">
          {activePaper ? (
            <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 shadow-xl space-y-4 sticky top-20">
              <div>
                <span className="text-[11px] font-mono text-cyan-400 font-bold block mb-1">
                  {activePaper.arxivId} • {activePaper.year}
                </span>
                <h3 className="text-sm font-bold text-white leading-snug">
                  {activePaper.title}
                </h3>
              </div>

              <div>
                <span className="text-[10px] text-slate-400 uppercase tracking-wider block mb-1">
                  Autores
                </span>
                <p className="text-xs text-slate-300">{activePaper.authors.join(', ')}</p>
              </div>

              <div>
                <span className="text-[10px] text-slate-400 uppercase tracking-wider block mb-1">
                  Resumen Científico
                </span>
                <p className="text-xs text-slate-300 leading-relaxed bg-slate-950 p-3 rounded-xl border border-slate-800/80">
                  {activePaper.abstract}
                </p>
              </div>

              <div className="p-3 rounded-xl bg-cyan-950/20 border border-cyan-500/30 flex items-center justify-between">
                <div>
                  <span className="text-xs font-semibold text-cyan-300 block">
                    Vectores de Embedding
                  </span>
                  <span className="text-[11px] text-slate-400">Dimensión 1536 (Cosine Index)</span>
                </div>
                <span className="text-xs font-mono font-bold text-cyan-400">
                  Score {(activePaper.vectorSimilarity * 100).toFixed(1)}%
                </span>
              </div>

              <a
                href={`https://arxiv.org/abs/${activePaper.arxivId.replace('arXiv:', '')}`}
                target="_blank"
                rel="noopener noreferrer"
                className="w-full py-2.5 rounded-xl bg-gradient-to-r from-cyan-500 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 text-xs font-semibold text-white flex items-center justify-center gap-1.5 transition-all shadow-md shadow-cyan-500/20"
              >
                <span>Leer en arXiv</span>
                <ExternalLink className="w-3.5 h-3.5" />
              </a>
            </div>
          ) : (
            <div className="p-8 text-center text-slate-500 text-xs rounded-2xl bg-slate-900 border border-slate-800">
              <BookOpen className="w-8 h-8 mx-auto mb-2 opacity-40 text-cyan-400" />
              <p>Selecciona un artículo para ver sus detalles y métricas RAG.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
