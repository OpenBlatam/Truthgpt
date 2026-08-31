#!/usr/bin/env python3
"""
TruthGPT Local Documentation Server & Interactive Viewer.
Serves Markdown documentation locally with modern dark/light UI, live search,
syntax highlighting, code copy buttons, GitHub alert callouts, hash routing,
and Mermaid JS rendering without requiring external dependencies.
"""

import http.server
import os
import posixpath
import socketserver
import sys
import urllib.parse
import json

PORT = 8000
DOCS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_DIR = os.path.dirname(DOCS_DIR)

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TruthGPT Optimization Core - Documentation Hub</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github-dark.min.css" id="highlight-theme">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
    <style>
        :root[data-theme="dark"] {
            --bg-primary: #0b0f19;
            --bg-secondary: #111827;
            --bg-tertiary: #1f2937;
            --sidebar-bg: #0d1322;
            --text-primary: #f3f4f6;
            --text-secondary: #9ca3af;
            --text-muted: #6b7280;
            --accent-primary: #6366f1;
            --accent-hover: #4f46e5;
            --accent-glow: rgba(99, 102, 241, 0.25);
            --border-color: #1f293d;
            --card-bg: #131b2e;
            --code-bg: #0d121f;
            --table-header: #1e293b;
            --alert-note-bg: rgba(59, 130, 246, 0.1);
            --alert-note-border: #3b82f6;
            --alert-tip-bg: rgba(16, 185, 129, 0.1);
            --alert-tip-border: #10b981;
            --alert-important-bg: rgba(139, 92, 246, 0.1);
            --alert-important-border: #8b5cf6;
            --alert-warning-bg: rgba(245, 158, 11, 0.1);
            --alert-warning-border: #f59e0b;
            --alert-caution-bg: rgba(239, 68, 68, 0.1);
            --alert-caution-border: #ef4444;
        }

        :root[data-theme="light"] {
            --bg-primary: #f8fafc;
            --bg-secondary: #f1f5f9;
            --bg-tertiary: #e2e8f0;
            --sidebar-bg: #ffffff;
            --text-primary: #0f172a;
            --text-secondary: #475569;
            --text-muted: #94a3b8;
            --accent-primary: #4f46e5;
            --accent-hover: #4338ca;
            --accent-glow: rgba(79, 70, 229, 0.15);
            --border-color: #e2e8f0;
            --card-bg: #ffffff;
            --code-bg: #f1f5f9;
            --table-header: #e2e8f0;
            --alert-note-bg: rgba(59, 130, 246, 0.08);
            --alert-note-border: #2563eb;
            --alert-tip-bg: rgba(16, 185, 129, 0.08);
            --alert-tip-border: #059669;
            --alert-important-bg: rgba(139, 92, 246, 0.08);
            --alert-important-border: #7c3aed;
            --alert-warning-bg: rgba(245, 158, 11, 0.08);
            --alert-warning-border: #d97706;
            --alert-caution-bg: rgba(239, 68, 68, 0.08);
            --alert-caution-border: #dc2626;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background-color: var(--bg-primary);
            color: var(--text-primary);
            display: flex;
            height: 100vh;
            overflow: hidden;
            transition: background-color 0.2s ease, color 0.2s ease;
        }

        /* Sidebar */
        #sidebar {
            width: 320px;
            min-width: 320px;
            background: var(--sidebar-bg);
            border-right: 1px solid var(--border-color);
            display: flex;
            flex-direction: column;
            height: 100%;
            transition: all 0.25s ease;
            z-index: 50;
        }

        .brand-header {
            padding: 20px;
            border-bottom: 1px solid var(--border-color);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .brand-info {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .brand-logo {
            width: 36px;
            height: 36px;
            border-radius: 8px;
            background: linear-gradient(135deg, #6366f1, #06b6d4);
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 800;
            color: #fff;
            font-size: 1.1rem;
            box-shadow: 0 0 15px var(--accent-glow);
        }

        .brand-title {
            font-weight: 700;
            font-size: 1rem;
            letter-spacing: -0.02em;
        }

        .brand-subtitle {
            font-size: 0.75rem;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        .search-box {
            padding: 14px 20px;
            border-bottom: 1px solid var(--border-color);
            position: relative;
        }

        .search-input {
            width: 100%;
            background: var(--bg-primary);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 10px 14px 10px 36px;
            color: var(--text-primary);
            font-size: 0.875rem;
            outline: none;
            transition: all 0.2s ease;
        }

        .search-input:focus {
            border-color: var(--accent-primary);
            box-shadow: 0 0 0 3px var(--accent-glow);
        }

        .search-icon {
            position: absolute;
            left: 32px;
            top: 25px;
            font-size: 0.85rem;
            color: var(--text-muted);
            pointer-events: none;
        }

        .search-hint {
            position: absolute;
            right: 28px;
            top: 22px;
            font-size: 0.7rem;
            color: var(--text-muted);
            background: var(--border-color);
            padding: 2px 6px;
            border-radius: 4px;
            pointer-events: none;
        }

        .nav-tree {
            flex: 1;
            overflow-y: auto;
            padding: 16px 12px;
        }

        .nav-section-title {
            font-size: 0.75rem;
            font-weight: 700;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.08em;
            padding: 14px 10px 6px;
        }

        .nav-item {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 8px 12px;
            border-radius: 6px;
            color: var(--text-secondary);
            text-decoration: none;
            font-size: 0.875rem;
            font-weight: 500;
            transition: all 0.15s ease;
            cursor: pointer;
            margin-bottom: 2px;
        }

        .nav-item:hover {
            color: var(--text-primary);
            background: rgba(99, 102, 241, 0.08);
        }

        .nav-item.active {
            color: #ffffff;
            background: var(--accent-primary);
            box-shadow: 0 2px 8px var(--accent-glow);
            font-weight: 600;
        }

        /* Content Area */
        #content-wrapper {
            flex: 1;
            display: flex;
            flex-direction: column;
            height: 100%;
            overflow: hidden;
            background: var(--bg-primary);
        }

        .top-navbar {
            height: 60px;
            border-bottom: 1px solid var(--border-color);
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 32px;
            background: var(--sidebar-bg);
        }

        .nav-left {
            display: flex;
            align-items: center;
            gap: 16px;
        }

        .mobile-toggle {
            display: none;
            background: none;
            border: none;
            color: var(--text-primary);
            font-size: 1.25rem;
            cursor: pointer;
        }

        .current-path {
            font-size: 0.875rem;
            color: var(--text-secondary);
        }

        .current-path span {
            color: var(--text-primary);
            font-weight: 600;
        }

        .nav-controls {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .theme-btn {
            background: var(--bg-primary);
            border: 1px solid var(--border-color);
            color: var(--text-primary);
            padding: 6px 12px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.85rem;
            display: flex;
            align-items: center;
            gap: 6px;
            transition: all 0.2s ease;
        }

        .theme-btn:hover {
            border-color: var(--accent-primary);
        }

        .main-content {
            flex: 1;
            overflow-y: auto;
            padding: 40px 60px;
            max-width: 1150px;
            margin: 0 auto;
            width: 100%;
        }

        /* Markdown Styling */
        .markdown-body {
            line-height: 1.75;
            font-size: 1rem;
            color: var(--text-primary);
        }

        .markdown-body h1 {
            font-size: 2.25rem;
            font-weight: 800;
            margin-bottom: 24px;
            letter-spacing: -0.03em;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 16px;
        }

        .markdown-body h2 {
            font-size: 1.5rem;
            font-weight: 700;
            margin-top: 36px;
            margin-bottom: 16px;
            letter-spacing: -0.02em;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 8px;
        }

        .markdown-body h3 {
            font-size: 1.2rem;
            font-weight: 600;
            margin-top: 24px;
            margin-bottom: 12px;
        }

        .markdown-body p {
            margin-bottom: 16px;
            color: var(--text-secondary);
        }

        .markdown-body ul, .markdown-body ol {
            margin-bottom: 16px;
            padding-left: 24px;
            color: var(--text-secondary);
        }

        .markdown-body li {
            margin-bottom: 6px;
        }

        .markdown-body a {
            color: var(--accent-primary);
            text-decoration: none;
            border-bottom: 1px dashed rgba(99, 102, 241, 0.4);
            transition: all 0.2s ease;
        }

        .markdown-body a:hover {
            border-bottom-style: solid;
        }

        .code-container {
            position: relative;
            margin: 20px 0;
        }

        .copy-code-btn {
            position: absolute;
            top: 10px;
            right: 10px;
            background: rgba(30, 41, 59, 0.8);
            border: 1px solid rgba(255, 255, 255, 0.1);
            color: #cbd5e1;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.75rem;
            cursor: pointer;
            transition: all 0.2s ease;
            backdrop-filter: blur(4px);
            z-index: 10;
        }

        .copy-code-btn:hover {
            background: var(--accent-primary);
            color: #ffffff;
        }

        .markdown-body pre {
            background: var(--code-bg);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 18px;
            overflow-x: auto;
        }

        .markdown-body code {
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.9rem;
        }

        .markdown-body p code, .markdown-body li code, .markdown-body table code {
            background: rgba(99, 102, 241, 0.12);
            color: var(--accent-primary);
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 0.85rem;
        }

        .markdown-body table {
            width: 100%;
            border-collapse: collapse;
            margin: 24px 0;
            background: var(--card-bg);
            border-radius: 8px;
            overflow: hidden;
            border: 1px solid var(--border-color);
        }

        .markdown-body th {
            background: var(--table-header);
            text-align: left;
            padding: 12px 16px;
            font-weight: 600;
            font-size: 0.875rem;
            border-bottom: 1px solid var(--border-color);
        }

        .markdown-body td {
            padding: 12px 16px;
            border-bottom: 1px solid var(--border-color);
            color: var(--text-secondary);
            font-size: 0.875rem;
        }

        .markdown-body tr:last-child td {
            border-bottom: none;
        }

        .markdown-body blockquote {
            border-left: 4px solid var(--accent-primary);
            padding: 12px 20px;
            background: rgba(99, 102, 241, 0.08);
            border-radius: 0 8px 8px 0;
            margin: 20px 0;
            color: var(--text-primary);
        }

        /* GitHub Alert Callouts */
        .alert-box {
            border-left: 4px solid var(--accent-primary);
            padding: 14px 18px;
            border-radius: 0 8px 8px 0;
            margin: 20px 0;
        }

        .alert-header {
            display: flex;
            align-items: center;
            gap: 8px;
            font-weight: 700;
            font-size: 0.85rem;
            letter-spacing: 0.04em;
            text-transform: uppercase;
            margin-bottom: 6px;
        }

        .alert-note { background: var(--alert-note-bg); border-color: var(--alert-note-border); }
        .alert-note .alert-header { color: var(--alert-note-border); }

        .alert-tip { background: var(--alert-tip-bg); border-color: var(--alert-tip-border); }
        .alert-tip .alert-header { color: var(--alert-tip-border); }

        .alert-important { background: var(--alert-important-bg); border-color: var(--alert-important-border); }
        .alert-important .alert-header { color: var(--alert-important-border); }

        .alert-warning { background: var(--alert-warning-bg); border-color: var(--alert-warning-border); }
        .alert-warning .alert-header { color: var(--alert-warning-border); }

        .alert-caution { background: var(--alert-caution-bg); border-color: var(--alert-caution-border); }
        .alert-caution .alert-header { color: var(--alert-caution-border); }

        .alert-body p {
            margin-bottom: 0;
            color: var(--text-primary);
            font-size: 0.925rem;
        }

        .mermaid {
            background: var(--card-bg);
            padding: 20px;
            border-radius: 8px;
            border: 1px solid var(--border-color);
            margin: 20px 0;
            display: flex;
            justify-content: center;
        }

        @media (max-width: 900px) {
            #sidebar {
                position: fixed;
                left: -320px;
                box-shadow: 10px 0 30px rgba(0,0,0,0.5);
            }
            #sidebar.open {
                left: 0;
            }
            .mobile-toggle {
                display: block;
            }
            .main-content {
                padding: 24px 20px;
            }
        }
    </style>
</head>
<body>
    <div id="sidebar">
        <div class="brand-header">
            <div class="brand-info">
                <div class="brand-logo">⚡</div>
                <div>
                    <div class="brand-title">TruthGPT Core</div>
                    <div class="brand-subtitle">Documentation Hub</div>
                </div>
            </div>
        </div>
        <div class="search-box">
            <span class="search-icon">🔍</span>
            <input type="text" class="search-input" id="search" placeholder="Search documentation...">
            <span class="search-hint">/</span>
        </div>
        <div class="nav-tree" id="nav-tree">
            <!-- Populated dynamically -->
        </div>
    </div>

    <div id="content-wrapper">
        <div class="top-navbar">
            <div class="nav-left">
                <button class="mobile-toggle" id="sidebar-toggle">☰</button>
                <div class="current-path" id="breadcrumbs">Docs &rsaquo; <span>Overview</span></div>
            </div>
            <div class="nav-controls">
                <button class="theme-btn" id="theme-toggle">🌓 Theme</button>
            </div>
        </div>
        <div class="main-content">
            <div class="markdown-body" id="doc-content">
                Loading documentation...
            </div>
        </div>
    </div>

    <script>
        const navStructure = [
            {
                section: "Overview",
                items: [
                    { title: "Documentation Hub", path: "index.md" },
                    { title: "Documentation Map", path: "README.md" },
                    { title: "Table of Contents", path: "SUMMARY.md" }
                ]
            },
            {
                section: "Getting Started",
                items: [
                    { title: "Overview Portal", path: "getting_started/index.md" },
                    { title: "Installation Guide", path: "getting_started/installation.md" },
                    { title: "Quickstart: LLM Training", path: "getting_started/quickstart_training.md" },
                    { title: "Quickstart: OpenClaw Agents", path: "getting_started/quickstart_agents.md" },
                    { title: "Quickstart: Compiler", path: "getting_started/quickstart_compiler.md" },
                    { title: "Configuration System", path: "getting_started/configuration.md" },
                    { title: "Health & Diagnostics", path: "getting_started/health_and_diagnostics.md" }
                ]
            },
            {
                section: "Architecture & Design",
                items: [
                    { title: "Architecture Portal", path: "architecture/index.md" },
                    { title: "System Architecture", path: "architecture/overview.md" },
                    { title: "Polyglot Core Engine", path: "architecture/polyglot_core.md" },
                    { title: "Compiler Runtime Architecture", path: "architecture/compiler_runtime.md" },
                    { title: "Physics-Informed MoE (PiMoE)", path: "architecture/pimoe.md" },
                    { title: "OpenClaw Agent Framework", path: "architecture/agent_framework.md" },
                    { title: "Data Pipeline & Bucketing", path: "architecture/data_pipeline.md" },
                    { title: "Models & Modular Layers", path: "architecture/models_and_layers.md" }
                ]
            },
            {
                section: "API Reference",
                items: [
                    { title: "API Directory", path: "api/index.md" },
                    { title: "Trainers & Checkpointing", path: "api/trainers.md" },
                    { title: "Models & Modules", path: "api/models_modules.md" },
                    { title: "Optimizers & Schedulers", path: "api/optimizers.md" },
                    { title: "Compiler & Acceleration", path: "api/compiler.md" },
                    { title: "OpenClaw Agents SDK", path: "api/agents.md" },
                    { title: "Inference & Paged KV-Cache", path: "api/inference.md" },
                    { title: "Polyglot Core Bindings", path: "api/polyglot.md" },
                    { title: "Configuration Schema", path: "api/configuration.md" },
                    { title: "Research Papers Catalog", path: "api/papers.md" },
                    { title: "Utilities & Telemetry", path: "api/utilities.md" }
                ]
            },
            {
                section: "Guides & Deep Dives",
                items: [
                    { title: "Guides Overview", path: "guides/index.md" },
                    { title: "Optimization & Performance Tuning", path: "guides/optimization_tuning.md" },
                    { title: "Distributed Training Guide", path: "guides/distributed_training.md" },
                    { title: "Custom Agent Development", path: "guides/custom_agent_development.md" },
                    { title: "Compiler & Custom Kernels", path: "guides/compiler_and_kernels.md" },
                    { title: "KV-Cache Memory Optimization", path: "guides/kv_cache_optimization.md" },
                    { title: "Production Deployment & Serving", path: "guides/deployment_production.md" },
                    { title: "CLI & Interactive Terminals", path: "guides/cli_and_terminals.md" },
                    { title: "Swarm Ensemble vs Single Model", path: "guides/swarm_ensemble_vs_single_model.md" },
                    { title: "Troubleshooting & Diagnostics", path: "guides/troubleshooting.md" }
                ]
            },
            {
                section: "Tutorials",
                items: [
                    { title: "Tutorials Overview", path: "tutorials/index.md" },
                    { title: "LoRA & QLoRA Fine-Tuning", path: "tutorials/lora_finetuning.md" },
                    { title: "Building Custom Agents", path: "tutorials/building_custom_agents.md" },
                    { title: "High-Throughput Serving", path: "tutorials/high_throughput_serving.md" },
                    { title: "Custom Research Papers", path: "tutorials/custom_research_papers.md" },
                    { title: "Troubleshooting & FAQ", path: "tutorials/troubleshooting_and_faq.md" }
                ]
            },
            {
                section: "Examples & Benchmarks",
                items: [
                    { title: "Examples Overview", path: "examples/index.md" },
                    { title: "End-to-End LLM Fine-Tuning", path: "examples/basic_training.md" },
                    { title: "Autonomous Research Swarm", path: "examples/agent_swarms.md" },
                    { title: "Compiler & Kernel Benchmarks", path: "examples/compiler_benchmarks.md" }
                ]
            },
            {
                section: "Archive — Legacy READMEs",
                items: [
                    { title: "Archive Catalog & Records", path: "archive/index.md" },
                    { title: "Omnipotent Intelligence", path: "archive/legacy_readmes/OMNIPOTENT_INTELLIGENCE_README.md" },
                    { title: "Production README", path: "archive/legacy_readmes/PRODUCTION_README.md" },
                    { title: "Supreme Intelligence", path: "archive/legacy_readmes/SUPREME_INTELLIGENCE_README.md" },
                    { title: "Ultimate Intelligence", path: "archive/legacy_readmes/ULTIMATE_INTELLIGENCE_README.md" }
                ]
            },
            {
                section: "Archive — PiMoE Summaries",
                items: [
                    { title: "Absolute Perfection", path: "archive/pimoe_summaries/ABSOLUTE_PERFECTION_PIMOE_SUMMARY.md" },
                    { title: "Cosmic Intelligence", path: "archive/pimoe_summaries/COSMIC_INTELLIGENCE_PIMOE_SUMMARY.md" },
                    { title: "Infinite Divine", path: "archive/pimoe_summaries/INFINITE_DIVINE_PIMOE_SUMMARY.md" },
                    { title: "Infinite Reality", path: "archive/pimoe_summaries/INFINITE_REALITY_PIMOE_SUMMARY.md" },
                    { title: "Infinite Transcendence", path: "archive/pimoe_summaries/INFINITE_TRANSCENDENCE_PIMOE_SUMMARY.md" },
                    { title: "Infinite Understanding", path: "archive/pimoe_summaries/INFINITE_UNDERSTANDING_PIMOE_SUMMARY.md" },
                    { title: "Infinite Wisdom", path: "archive/pimoe_summaries/INFINITE_WISDOM_PIMOE_SUMMARY.md" },
                    { title: "Lightning Speed", path: "archive/pimoe_summaries/LIGHTNING_SPEED_PIMOE_SUMMARY.md" },
                    { title: "Transcendent Perfection", path: "archive/pimoe_summaries/TRANSCENDENT_PERFECTION_PIMOE_SUMMARY.md" },
                    { title: "Ultimate Awareness", path: "archive/pimoe_summaries/ULTIMATE_AWARENESS_PIMOE_SUMMARY.md" },
                    { title: "Ultimate Consciousness", path: "archive/pimoe_summaries/ULTIMATE_CONSCIOUSNESS_PIMOE_SUMMARY.md" },
                    { title: "Ultimate Creativity", path: "archive/pimoe_summaries/ULTIMATE_CREATIVITY_PIMOE_SUMMARY.md" },
                    { title: "Ultimate Excellence", path: "archive/pimoe_summaries/ULTIMATE_EXCELLENCE_PIMOE_SUMMARY.md" },
                    { title: "Ultimate Intelligence", path: "archive/pimoe_summaries/ULTIMATE_INTELLIGENCE_PIMOE_SUMMARY.md" },
                    { title: "Ultimate Optimization", path: "archive/pimoe_summaries/ULTIMATE_OPTIMIZATION_PIMOE_SUMMARY.md" },
                    { title: "Ultimate Enhancement", path: "archive/pimoe_summaries/ULTIMATE_PIMOE_ENHANCEMENT_SUMMARY.md" },
                    { title: "Ultimate Transcendence", path: "archive/pimoe_summaries/ULTIMATE_TRANSCENDENCE_PIMOE_SUMMARY.md" },
                    { title: "Ultimate Wisdom", path: "archive/pimoe_summaries/ULTIMATE_WISDOM_PIMOE_SUMMARY.md" },
                    { title: "Ultra Rapid Speed", path: "archive/pimoe_summaries/ULTRA_RAPID_SPEED_PIMOE_SUMMARY.md" }
                ]
            },
            {
                section: "Archive — Proposals & RFCs",
                items: [
                    { title: "Modular Architecture", path: "archive/proposals/MODULAR_ARCHITECTURE.md" },
                    { title: "Phase 1 Implementation Guide", path: "archive/proposals/IMPLEMENTATION_GUIDE_PHASE1.md" },
                    { title: "Compiler Integration Guide", path: "archive/proposals/COMPILER_INTEGRATION_GUIDE.md" },
                    { title: "KV-Cache Optimization Guide", path: "archive/proposals/KV_CACHE_OPTIMIZATION_GUIDE.md" },
                    { title: "Kernel Enhancement Master Plan", path: "archive/proposals/KERNEL_ENHANCEMENT_MASTER_PLAN.md" },
                    { title: "Kernel Improvement Proposal", path: "archive/proposals/KERNEL_IMPROVEMENT_PROPOSAL.md" },
                    { title: "Deprecated Optimizers", path: "archive/proposals/DEPRECATED_OPTIMIZERS.md" },
                    { title: "Directory Structure Guide", path: "archive/proposals/DIRECTORY_STRUCTURE_GUIDE.md" },
                    { title: "TruthGPT Improvement Plan", path: "archive/proposals/TRUTHGPT_IMPROVEMENT_PLAN.md" },
                    { title: "Kernel Enhancement Detailed", path: "archive/proposals/TRUTHGPT_KERNEL_ENHANCEMENT_DETAILED.md" },
                    { title: "Kernel Enhancement Proposal", path: "archive/proposals/TRUTHGPT_KERNEL_ENHANCEMENT_PROPOSAL.md" },
                    { title: "System Summary", path: "archive/proposals/TRUTHPGT_SYSTEM_SUMMARY.md" }
                ]
            },
            {
                section: "Archive — Refactoring History",
                items: [
                    { title: "Architecture Improvements", path: "archive/refactoring_history/ARCHITECTURE_IMPROVEMENTS.md" },
                    { title: "Architecture Improvements Summary", path: "archive/refactoring_history/ARCHITECTURE_IMPROVEMENTS_SUMMARY.md" },
                    { title: "Improvements Complete Summary", path: "archive/refactoring_history/IMPROVEMENTS_COMPLETE_SUMMARY.md" },
                    { title: "Modular Refactoring Complete", path: "archive/refactoring_history/MODULAR_REFACTORING_COMPLETE.md" },
                    { title: "Phase 1 Implementation Status", path: "archive/refactoring_history/PHASE1_IMPLEMENTATION_STATUS.md" },
                    { title: "Phase 2 Directory Reorganization", path: "archive/refactoring_history/PHASE2_DIRECTORY_REORGANIZATION.md" },
                    { title: "Phase 2 Implementation Status", path: "archive/refactoring_history/PHASE2_IMPLEMENTATION_STATUS.md" },
                    { title: "Compilers Models Adapters", path: "archive/refactoring_history/REFACTORING_COMPILERS_MODELS_ADAPTERS.md" },
                    { title: "Complete Summary", path: "archive/refactoring_history/REFACTORING_COMPLETE_SUMMARY.md" },
                    { title: "Comprehensive Refactoring", path: "archive/refactoring_history/REFACTORING_COMPREHENSIVE.md" },
                    { title: "Constants Refactoring", path: "archive/refactoring_history/REFACTORING_CONSTANTS.md" },
                    { title: "Core Optimizers", path: "archive/refactoring_history/REFACTORING_CORE_OPTIMIZERS.md" },
                    { title: "Core Organization", path: "archive/refactoring_history/REFACTORING_CORE_ORGANIZATION.md" },
                    { title: "Examples & Benchmarks", path: "archive/refactoring_history/REFACTORING_EXAMPLES_BENCHMARKS.md" },
                    { title: "Factories & Managers", path: "archive/refactoring_history/REFACTORING_FACTORIES_MANAGERS.md" },
                    { title: "Feed Forward", path: "archive/refactoring_history/REFACTORING_FEED_FORWARD.md" },
                    { title: "Final Session", path: "archive/refactoring_history/REFACTORING_FINAL_SESSION.md" },
                    { title: "Final Summary", path: "archive/refactoring_history/REFACTORING_FINAL_SUMMARY.md" },
                    { title: "Refactoring Guide", path: "archive/refactoring_history/REFACTORING_GUIDE.md" },
                    { title: "Inference Organization", path: "archive/refactoring_history/REFACTORING_INFERENCE_ORGANIZATION.md" },
                    { title: "Init.py Refactoring", path: "archive/refactoring_history/REFACTORING_INIT_PY.md" },
                    { title: "Mass Refactor", path: "archive/refactoring_history/REFACTORING_MASS_REFACTOR.md" },
                    { title: "Models Complete", path: "archive/refactoring_history/REFACTORING_MODELS_COMPLETE.md" },
                    { title: "Modules Data Optimization", path: "archive/refactoring_history/REFACTORING_MODULES_DATA_OPTIMIZATION.md" },
                    { title: "Opportunities", path: "archive/refactoring_history/REFACTORING_OPPORTUNITIES.md" },
                    { title: "Optimization Cores", path: "archive/refactoring_history/REFACTORING_OPTIMIZATION_CORES.md" },
                    { title: "Optimizers Refactoring", path: "archive/refactoring_history/REFACTORING_OPTIMIZERS.md" },
                    { title: "Optimizers Organization", path: "archive/refactoring_history/REFACTORING_OPTIMIZERS_ORGANIZATION.md" },
                    { title: "Papers Refactoring", path: "archive/refactoring_history/REFACTORING_PAPERS.md" },
                    { title: "Production Configs", path: "archive/refactoring_history/REFACTORING_PRODUCTION_CONFIGS.md" },
                    { title: "Progress", path: "archive/refactoring_history/REFACTORING_PROGRESS.md" },
                    { title: "Registries", path: "archive/refactoring_history/REFACTORING_REGISTRIES.md" },
                    { title: "Root Organization", path: "archive/refactoring_history/REFACTORING_ROOT_ORGANIZATION.md" },
                    { title: "Session Summary", path: "archive/refactoring_history/REFACTORING_SESSION_SUMMARY.md" },
                    { title: "Status", path: "archive/refactoring_history/REFACTORING_STATUS.md" },
                    { title: "Summary", path: "archive/refactoring_history/REFACTORING_SUMMARY.md" },
                    { title: "Trainers Complete", path: "archive/refactoring_history/REFACTORING_TRAINERS_COMPLETE.md" },
                    { title: "Training Complete", path: "archive/refactoring_history/REFACTORING_TRAINING_COMPLETE.md" },
                    { title: "Training Config", path: "archive/refactoring_history/REFACTORING_TRAINING_CONFIG.md" },
                    { title: "Utils Complete", path: "archive/refactoring_history/REFACTORING_UTILS_COMPLETE.md" },
                    { title: "Utils Organization", path: "archive/refactoring_history/REFACTORING_UTILS_ORGANIZATION.md" }
                ]
            },
            {
                section: "Archive — Test Reports",
                items: [
                    { title: "Enhanced Framework", path: "archive/test_reports/README_ENHANCED_FRAMEWORK.md" },
                    { title: "Enhanced Tests", path: "archive/test_reports/README_ENHANCED_TESTS.md" },
                    { title: "Enhanced Tests V4", path: "archive/test_reports/README_ENHANCED_TESTS_V4.md" },
                    { title: "Improved Tests", path: "archive/test_reports/README_IMPROVED_TESTS.md" },
                    { title: "Refactored Tests", path: "archive/test_reports/README_REFACTORED_TESTS.md" },
                    { title: "TensorFlow Optimizations", path: "archive/test_reports/README_TENSORFLOW_OPTIMIZATIONS.md" },
                    { title: "Tests", path: "archive/test_reports/README_TESTS.md" },
                    { title: "Ultra Enhanced Tests", path: "archive/test_reports/README_ULTRA_ENHANCED_TESTS.md" },
                    { title: "Ultra Enhanced Tests V3", path: "archive/test_reports/README_ULTRA_ENHANCED_TESTS_V3.md" }
                ]
            },
            {
                section: "Spanish — Portal & Guías",
                items: [
                    { title: "Portal Principal", path: "spanish/index.md" },
                    { title: "Centro de Documentación (README)", path: "spanish/README.md" },
                    { title: "Guía de Inicio Rápido", path: "spanish/QUICK_START.md" },
                    { title: "Modo Ensemble vs Modelo Único", path: "spanish/features/Ensemble_Vs_Single_Model.md" },
                    { title: "Guía de Inicio Rápido", path: "spanish/guides/quick_start_guide.md" },
                    { title: "Uso de TruthGPT", path: "spanish/guides/truthgpt_usage_guide.md" },
                    { title: "Adaptación a TruthGPT", path: "spanish/guides/truthgpt_adaptation_guide.md" },
                    { title: "Optimización Avanzada", path: "spanish/guides/advanced_optimization_guide.md" },
                    { title: "Guía de Despliegue", path: "spanish/guides/deployment_guide.md" },
                    { title: "Mejores Prácticas", path: "spanish/guides/best_practices_guide.md" },
                    { title: "Creación de Modelos", path: "spanish/guides/model_creation_guide.md" },
                    { title: "Referencia API", path: "spanish/guides/api_reference.md" },
                    { title: "Solución de Problemas", path: "spanish/guides/troubleshooting_guide.md" }
                ]
            },
            {
                section: "Spanish — Ejemplos & Tutoriales",
                items: [
                    { title: "Ejemplos Básicos", path: "spanish/examples/basic_examples.md" },
                    { title: "Ejemplos Avanzados", path: "spanish/examples/advanced_examples.md" },
                    { title: "Benchmarks", path: "spanish/examples/benchmark_examples.md" },
                    { title: "Ejemplos Enterprise", path: "spanish/examples/enterprise_examples.md" },
                    { title: "Integraciones", path: "spanish/examples/integration_examples.md" },
                    { title: "Rendimiento", path: "spanish/examples/performance_examples.md" },
                    { title: "Casos Reales", path: "spanish/examples/real_world_examples.md" },
                    { title: "Tutorial Básico", path: "spanish/tutorials/basic_tutorial.md" },
                    { title: "Tutorial Avanzado", path: "spanish/tutorials/advanced_tutorial.md" }
                ]
            },
            {
                section: "Root Specifications",
                items: [
                    { title: "Root Architecture Spec", path: "../ARCHITECTURE.md" },
                    { title: "Deployment Guide", path: "../DEPLOYMENT_GUIDE.md" },
                    { title: "Migration Guide", path: "../MIGRATION_GUIDE.md" },
                    { title: "FAQ", path: "../FAQ.md" },
                    { title: "Contributing Guide", path: "../CONTRIBUTING.md" },
                    { title: "Changelog", path: "../CHANGELOG.md" }
                ]
            }
        ];

        let currentDoc = "index.md";

        function renderNav() {
            const navTree = document.getElementById("nav-tree");
            navTree.innerHTML = "";

            navStructure.forEach(sec => {
                const secTitle = document.createElement("div");
                secTitle.className = "nav-section-title";
                secTitle.textContent = sec.section;
                navTree.appendChild(secTitle);

                sec.items.forEach(item => {
                    const navItem = document.createElement("div");
                    navItem.className = `nav-item ${item.path === currentDoc ? "active" : ""}`;
                    navItem.textContent = item.title;
                    navItem.onclick = () => {
                        loadDoc(item.path, item.title, sec.section, true);
                        if (window.innerWidth <= 900) {
                            document.getElementById("sidebar").classList.remove("open");
                        }
                    };
                    navTree.appendChild(navItem);
                });
            });
        }

        function parseAlertBlocks(html) {
            return html.replace(/<blockquote>\s*<p>\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]([\s\S]*?)<\/blockquote>/gi, (match, type, content) => {
                const lowerType = type.toLowerCase();
                const iconMap = {
                    note: 'ℹ️',
                    tip: '💡',
                    important: '❗',
                    warning: '⚠️',
                    caution: '🛑'
                };
                const icon = iconMap[lowerType] || 'ℹ️';
                return `<div class="alert-box alert-${lowerType}">
                    <div class="alert-header">
                        <span>${icon}</span>
                        <span>${type}</span>
                    </div>
                    <div class="alert-body"><p>${content.trim()}</p></div>
                </div>`;
            });
        }

        async function loadDoc(docPath, title, section, updateHash = true) {
            currentDoc = docPath;
            if (updateHash && window.location.hash !== '#' + docPath) {
                window.location.hash = '#' + docPath;
            }
            renderNav();
            
            document.getElementById("breadcrumbs").innerHTML = 
                `${section || 'Docs'} &rsaquo; <span>${title || 'Document'}</span>`;
            
            const contentEl = document.getElementById("doc-content");
            contentEl.innerHTML = "<p>Loading document...</p>";

            try {
                const res = await fetch(`/content?file=${encodeURIComponent(docPath)}`);
                if (!res.ok) throw new Error("Document not found");
                const text = await res.text();
                
                // Parse markdown
                marked.setOptions({
                    highlight: function(code, lang) {
                        if (lang === 'mermaid') {
                            return `<div class="mermaid">${code}</div>`;
                        }
                        const language = hljs.getLanguage(lang) ? lang : 'plaintext';
                        return hljs.highlight(code, { language }).value;
                    }
                });

                let parsedHtml = marked.parse(text);
                parsedHtml = parseAlertBlocks(parsedHtml);
                contentEl.innerHTML = parsedHtml;
                
                // Add copy buttons to code blocks
                contentEl.querySelectorAll('pre').forEach(pre => {
                    if (pre.querySelector('.mermaid')) return;
                    const container = document.createElement('div');
                    container.className = 'code-container';
                    pre.parentNode.insertBefore(container, pre);
                    container.appendChild(pre);

                    const btn = document.createElement('button');
                    btn.className = 'copy-code-btn';
                    btn.textContent = 'Copy';
                    btn.onclick = () => {
                        const code = pre.querySelector('code')?.innerText || pre.innerText;
                        navigator.clipboard.writeText(code).then(() => {
                            btn.textContent = 'Copied!';
                            setTimeout(() => { btn.textContent = 'Copy'; }, 2000);
                        });
                    };
                    container.appendChild(btn);
                });

                // Render Mermaid charts
                const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
                mermaid.initialize({ startOnLoad: false, theme: isDark ? 'dark' : 'default' });
                mermaid.run({ querySelector: '.mermaid' });
                
                // Intercept relative markdown links
                contentEl.querySelectorAll('a').forEach(a => {
                    const href = a.getAttribute('href');
                    if (href && (href.endsWith('.md') || href.includes('.md#'))) {
                        a.onclick = (e) => {
                            e.preventDefault();
                            let cleanHref = href.split('#')[0];
                            let fullPath = resolveRelativePath(currentDoc, cleanHref);
                            let matched = findNavItem(fullPath);
                            if (matched) {
                                loadDoc(matched.item.path, matched.item.title, matched.sec, true);
                            } else {
                                loadDoc(fullPath, cleanHref, "Documentation", true);
                            }
                        };
                    }
                });

                document.querySelector('.main-content').scrollTop = 0;
            } catch (err) {
                contentEl.innerHTML = `<div style="color: #ef4444; padding: 20px; background: rgba(239, 68, 68, 0.1); border-radius: 8px;">
                    <h3>Document Not Found</h3>
                    <p>Could not load <code>${docPath}</code></p>
                </div>`;
            }
        }

        function resolveRelativePath(base, relative) {
            if (relative.startsWith('/')) return relative.substring(1);
            let parts = base.split('/');
            parts.pop();
            let relParts = relative.split('/');
            for (let p of relParts) {
                if (p === '..') {
                    if (parts.length > 0 && parts[parts.length - 1] !== '..') {
                        parts.pop();
                    } else {
                        parts.push('..');
                    }
                } else if (p !== '.' && p !== '') {
                    parts.push(p);
                }
            }
            return parts.join('/');
        }

        function findNavItem(path) {
            for (let sec of navStructure) {
                for (let item of sec.items) {
                    if (item.path === path || item.path.endsWith(path)) {
                        return { sec: sec.section, item: item };
                    }
                }
            }
            return null;
        }

        // Search Filter
        const searchInput = document.getElementById("search");
        searchInput.addEventListener("input", (e) => {
            const query = e.target.value.toLowerCase();
            document.querySelectorAll(".nav-item").forEach(el => {
                const text = el.textContent.toLowerCase();
                el.style.display = text.includes(query) ? "flex" : "none";
            });
        });

        // Keyboard Shortcuts
        document.addEventListener("keydown", (e) => {
            if (e.key === "/" && document.activeElement !== searchInput) {
                e.preventDefault();
                searchInput.focus();
            } else if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
                e.preventDefault();
                searchInput.focus();
            } else if (e.key === "Escape" && document.activeElement === searchInput) {
                searchInput.value = "";
                searchInput.blur();
                document.querySelectorAll(".nav-item").forEach(el => el.style.display = "flex");
            }
        });

        // Mobile Sidebar Toggle
        document.getElementById("sidebar-toggle").addEventListener("click", () => {
            document.getElementById("sidebar").classList.toggle("open");
        });

        // Theme Toggle
        const themeBtn = document.getElementById("theme-toggle");
        themeBtn.addEventListener("click", () => {
            const currentTheme = document.documentElement.getAttribute("data-theme");
            const newTheme = currentTheme === "dark" ? "light" : "dark";
            document.documentElement.setAttribute("data-theme", newTheme);
            localStorage.setItem("truthgpt-docs-theme", newTheme);
            
            const hlTheme = document.getElementById("highlight-theme");
            if (newTheme === "light") {
                hlTheme.href = "https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github.min.css";
            } else {
                hlTheme.href = "https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github-dark.min.css";
            }

            // Re-render Mermaid charts with new theme
            mermaid.initialize({ startOnLoad: false, theme: newTheme === "dark" ? 'dark' : 'default' });
            mermaid.run({ querySelector: '.mermaid' });
        });

        // Hash Navigation Listener
        window.addEventListener("hashchange", () => {
            const hash = window.location.hash.substring(1);
            if (hash && hash !== currentDoc) {
                const matched = findNavItem(hash);
                if (matched) {
                    loadDoc(matched.item.path, matched.item.title, matched.sec, false);
                } else {
                    loadDoc(hash, hash.split('/').pop().replace('.md', ''), "Documentation", false);
                }
            }
        });

        // Restore Theme
        const savedTheme = localStorage.getItem("truthgpt-docs-theme") || "dark";
        document.documentElement.setAttribute("data-theme", savedTheme);
        const hlTheme = document.getElementById("highlight-theme");
        if (savedTheme === "light") {
            hlTheme.href = "https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github.min.css";
        }

        // Initial Load
        renderNav();
        const initialHash = window.location.hash.substring(1);
        if (initialHash) {
            const matched = findNavItem(initialHash);
            if (matched) {
                loadDoc(matched.item.path, matched.item.title, matched.sec, false);
            } else {
                loadDoc(initialHash, initialHash.split('/').pop().replace('.md', ''), "Documentation", false);
            }
        } else {
            loadDoc("index.md", "Documentation Hub", "Overview", false);
        }
    </script>
</body>
</html>
"""

class DocsHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/" or parsed.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode("utf-8"))
            return
        elif parsed.path == "/search-index" or parsed.path == "/api/docs":
            docs_list = []
            for root, dirs, files in os.walk(DOCS_DIR):
                for f in files:
                    if f.endswith(".md"):
                        full_p = os.path.join(root, f)
                        rel_p = os.path.relpath(full_p, DOCS_DIR).replace("\\", "/")
                        size = os.path.getsize(full_p)
                        title = f.replace(".md", "").replace("_", " ").title()
                        try:
                            with open(full_p, "r", encoding="utf-8", errors="ignore") as fh:
                                for line in fh:
                                    if line.startswith("# "):
                                        title = line.replace("# ", "").strip()
                                        break
                        except Exception:
                            pass
                        docs_list.append({"title": title, "path": rel_p, "size": size})
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(docs_list, indent=2).encode("utf-8"))
            return
        elif parsed.path == "/api/search":
            params = urllib.parse.parse_qs(parsed.query)
            query = params.get("q", [""])[0].lower()
            results = []
            if query:
                for root, dirs, files in os.walk(DOCS_DIR):
                    for f in files:
                        if f.endswith(".md"):
                            full_p = os.path.join(root, f)
                            rel_p = os.path.relpath(full_p, DOCS_DIR).replace("\\", "/")
                            try:
                                with open(full_p, "r", encoding="utf-8", errors="ignore") as fh:
                                    content = fh.read()
                                if query in content.lower() or query in f.lower():
                                    title = f.replace(".md", "").replace("_", " ").title()
                                    lines = content.splitlines()
                                    snippet = ""
                                    for line in lines:
                                        if line.startswith("# ") and title == f.replace(".md", "").replace("_", " ").title():
                                            title = line.replace("# ", "").strip()
                                        if query in line.lower() and not snippet:
                                            snippet = line.strip()
                                    results.append({
                                        "title": title,
                                        "path": rel_p,
                                        "snippet": snippet[:200]
                                    })
                            except Exception:
                                pass
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(results, indent=2).encode("utf-8"))
            return
        elif parsed.path == "/content":
            params = urllib.parse.parse_qs(parsed.query)
            file_rel = params.get("file", ["index.md"])[0]
            
            # Resolve relative to DOCS_DIR first, then REPO_DIR
            file_path = os.path.abspath(os.path.normpath(os.path.join(DOCS_DIR, file_rel)))
            if not os.path.exists(file_path):
                file_path = os.path.abspath(os.path.normpath(os.path.join(REPO_DIR, file_rel)))
            
            # Security check: prevent directory traversal outside REPO_DIR
            norm_repo = os.path.normcase(os.path.abspath(REPO_DIR))
            norm_file = os.path.normcase(file_path)
            if not norm_file.startswith(norm_repo) or not os.path.exists(file_path):
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b"File not found")
                return

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.end_headers()
                self.wfile.write(content.encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(str(e).encode("utf-8"))
            return

        return super().do_GET()

def run_server(port=PORT):
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    os.chdir(DOCS_DIR)
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", port), DocsHandler) as httpd:
        print("================================================================")
        print("  TruthGPT Optimization Core - Documentation Viewer")
        print(f"  Interactive Documentation Portal: http://localhost:{port}")
        print("  Press Ctrl+C to stop the server")
        print("================================================================")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down documentation server...")

if __name__ == "__main__":
    p = PORT
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        p = int(sys.argv[1])
    run_server(p)
