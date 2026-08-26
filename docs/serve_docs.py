#!/usr/bin/env python3
"""
TruthGPT Local Documentation Server & Interactive Viewer.
Serves Markdown documentation locally with modern dark/light UI, live search,
syntax highlighting, and Mermaid JS rendering without requiring external dependencies.
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

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TruthGPT Optimization Core - Documentation Hub</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github-dark.min.css">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
    <style>
        :root {
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
        }

        .brand-header {
            padding: 20px;
            border-bottom: 1px solid var(--border-color);
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
            color: #ffffff;
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
        }

        .search-input {
            width: 100%;
            background: var(--bg-primary);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 10px 14px;
            color: var(--text-primary);
            font-size: 0.875rem;
            outline: none;
            transition: all 0.2s ease;
        }

        .search-input:focus {
            border-color: var(--accent-primary);
            box-shadow: 0 0 0 3px var(--accent-glow);
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
            padding: 12px 10px 6px;
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
            color: #ffffff;
            background: rgba(255, 255, 255, 0.05);
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

        .current-path {
            font-size: 0.875rem;
            color: var(--text-secondary);
        }

        .current-path span {
            color: var(--text-primary);
            font-weight: 600;
        }

        .main-content {
            flex: 1;
            overflow-y: auto;
            padding: 40px 60px;
            max-width: 1100px;
            margin: 0 auto;
            width: 100%;
        }

        /* Markdown Styling */
        .markdown-body {
            line-height: 1.7;
            font-size: 1rem;
            color: #e5e7eb;
        }

        .markdown-body h1 {
            font-size: 2.25rem;
            font-weight: 800;
            color: #ffffff;
            margin-bottom: 24px;
            letter-spacing: -0.03em;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 16px;
        }

        .markdown-body h2 {
            font-size: 1.5rem;
            font-weight: 700;
            color: #f3f4f6;
            margin-top: 36px;
            margin-bottom: 16px;
            letter-spacing: -0.02em;
        }

        .markdown-body h3 {
            font-size: 1.2rem;
            font-weight: 600;
            color: #e5e7eb;
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
            color: #818cf8;
            text-decoration: none;
            border-bottom: 1px dashed rgba(129, 140, 248, 0.4);
            transition: all 0.2s ease;
        }

        .markdown-body a:hover {
            color: #a5b4fc;
            border-bottom-style: solid;
        }

        .markdown-body pre {
            background: var(--code-bg);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 16px;
            margin: 20px 0;
            overflow-x: auto;
            position: relative;
        }

        .markdown-body code {
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.9rem;
        }

        .markdown-body p code, .markdown-body li code, .markdown-body table code {
            background: rgba(99, 102, 241, 0.15);
            color: #a5b4fc;
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
            background: #1e293b;
            color: #f8fafc;
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
            color: #cbd5e1;
        }

        .mermaid {
            background: #0f172a;
            padding: 20px;
            border-radius: 8px;
            border: 1px solid var(--border-color);
            margin: 20px 0;
            display: flex;
            justify-content: center;
        }
    </style>
</head>
<body>
    <div id="sidebar">
        <div class="brand-header">
            <div class="brand-logo">T</div>
            <div>
                <div class="brand-title">TruthGPT Core</div>
                <div class="brand-subtitle">Documentation Hub</div>
            </div>
        </div>
        <div class="search-box">
            <input type="text" class="search-input" id="search" placeholder="Search documentation...">
        </div>
        <div class="nav-tree" id="nav-tree">
            <!-- Dynamically populated navigation -->
        </div>
    </div>

    <div id="content-wrapper">
        <div class="top-navbar">
            <div class="current-path" id="breadcrumbs">Docs &rsaquo; <span>Overview</span></div>
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
                    { title: "Documentation Map", path: "README.md" }
                ]
            },
            {
                section: "Getting Started",
                items: [
                    { title: "Overview Portal", path: "getting_started/index.md" },
                    { title: "Installation Guide", path: "getting_started/installation.md" },
                    { title: "Quickstart: LLM Training", path: "getting_started/quickstart_training.md" },
                    { title: "Quickstart: OpenClaw Agents", path: "getting_started/quickstart_agents.md" },
                    { title: "Quickstart: Compiler & Acceleration", path: "getting_started/quickstart_compiler.md" }
                ]
            },
            {
                section: "Architecture & Design",
                items: [
                    { title: "System Architecture", path: "architecture/overview.md" },
                    { title: "Polyglot Core Engine", path: "architecture/polyglot_core.md" },
                    { title: "Compiler Runtime Architecture", path: "architecture/compiler_runtime.md" },
                    { title: "Physics-Informed MoE (PiMoE)", path: "architecture/pimoe.md" },
                    { title: "OpenClaw Agent Framework", path: "architecture/agent_framework.md" }
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
                    { title: "Polyglot Core Bindings", path: "api/polyglot.md" },
                    { title: "Configuration Schema", path: "api/configuration.md" },
                    { title: "Research Papers Registry", path: "api/papers.md" },
                    { title: "Utilities & Diagnostics", path: "api/utilities.md" }
                ]
            },
            {
                section: "Guides & Deep Dives",
                items: [
                    { title: "Optimization & Performance Tuning", path: "guides/optimization_tuning.md" },
                    { title: "Distributed Training Guide", path: "guides/distributed_training.md" },
                    { title: "Custom Agent Development", path: "guides/custom_agent_development.md" },
                    { title: "Compiler & Custom Kernels", path: "guides/compiler_and_kernels.md" },
                    { title: "Production Deployment & Serving", path: "guides/deployment_production.md" },
                    { title: "Troubleshooting & Diagnostics", path: "guides/troubleshooting.md" }
                ]
            },
            {
                section: "Examples & Benchmarks",
                items: [
                    { title: "End-to-End LLM Fine-Tuning", path: "examples/basic_training.md" },
                    { title: "Autonomous Research Swarm", path: "examples/agent_swarms.md" },
                    { title: "Compiler & Kernel Benchmarks", path: "examples/compiler_benchmarks.md" }
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
                    navItem.onclick = () => loadDoc(item.path, item.title, sec.section);
                    navTree.appendChild(navItem);
                });
            });
        }

        async function loadDoc(docPath, title, section) {
            currentDoc = docPath;
            renderNav();
            
            document.getElementById("breadcrumbs").innerHTML = 
                `${section || 'Docs'} &rsaquo; <span>${title || 'Document'}</span>`;
            
            const contentEl = document.getElementById("doc-content");
            contentEl.innerHTML = "Loading document...";

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

                contentEl.innerHTML = marked.parse(text);
                
                // Re-render Mermaid charts
                mermaid.initialize({ startOnLoad: false, theme: 'dark' });
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
                                loadDoc(matched.item.path, matched.item.title, matched.sec);
                            } else {
                                loadDoc(fullPath, cleanHref, "Documentation");
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
                if (p === '..') parts.pop();
                else if (p !== '.') parts.push(p);
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

        // Live Search Filter
        document.getElementById("search").addEventListener("input", (e) => {
            const query = e.target.value.toLowerCase();
            document.querySelectorAll(".nav-item").forEach(el => {
                const text = el.textContent.toLowerCase();
                el.style.display = text.includes(query) ? "flex" : "none";
            });
        });

        // Initialize
        renderNav();
        loadDoc("index.md", "Documentation Hub", "Overview");
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
        elif parsed.path == "/content":
            params = urllib.parse.parse_qs(parsed.query)
            file_rel = params.get("file", ["index.md"])[0]
            file_path = os.path.normpath(os.path.join(DOCS_DIR, file_rel))
            
            # Security check: prevent directory traversal
            if not file_path.startswith(DOCS_DIR) or not os.path.exists(file_path):
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
    os.chdir(DOCS_DIR)
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", port), DocsHandler) as httpd:
        print(f"================================================================")
        print(f"  TruthGPT Optimization Core - Documentation Viewer")
        print(f"  Interactive Documentation Portal: http://localhost:{port}")
        print(f"  Press Ctrl+C to stop the server")
        print(f"================================================================")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down documentation server...")

if __name__ == "__main__":
    p = PORT
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        p = int(sys.argv[1])
    run_server(p)
