#!/usr/bin/env python3
"""
Enterprise High-Conversion Marketing AI Master Engine CLI v3.0
Full-funnel, multi-channel, persona-driven, research-backed marketing system.

Powered by optimization_core: AgentRegistry, MoE, CausalInference,
EnterpriseCache, RewardFunctions, GRPO Training, Experience Replay,
Cialdini Persuasion Principles, Causal Forest HTE & Consumer Fatigue Model.
"""

from __future__ import annotations

import sys
import os
import argparse
import logging

# Ensure UTF-8 output encoding on Windows consoles
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("MarketingAIEngine")

try:
    from marketing import IntegratedMarketingAITerminal
except ImportError:
    from optimization_core.marketing import IntegratedMarketingAITerminal


def main():
    parser = argparse.ArgumentParser(description="High-Conversion Marketing AI Engine v5.0 (Enterprise-SOTA & Production-Line)")
    parser.add_argument("--pipeline", type=str, help="Pipeline completo research-backed")
    parser.add_argument("--funnel", type=str, help="Funnel completo con Cialdini")
    parser.add_argument("--email-sequence", type=str, help="Emails con Fatigue Model")
    parser.add_argument("--budget", type=str, help="Presupuesto con Causal Forest uplift")
    parser.add_argument("--dashboard", action="store_true", help="Mostrar panel de control v3.0")
    args = parser.parse_args()

    app = IntegratedMarketingAITerminal()

    if args.pipeline:
        app.cmd_pipeline(args.pipeline)
    elif args.funnel:
        app.cmd_funnel(args.funnel)
    elif args.email_sequence:
        app.cmd_email_sequence(args.email_sequence)
    elif args.budget:
        app.cmd_budget(args.budget)
    elif args.dashboard:
        app.cmd_dashboard()
    else:
        app.interactive_loop()


if __name__ == "__main__":
    main()
