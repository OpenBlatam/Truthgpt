"""
💻 TruthGPT Cloud - Interactive Command Line Interface (CLI)
Query models with streaming, verify theorems with Z3 SMT, audit Merkle trees, inspect swarms, and manage subscriptions.
"""

import sys
import os
import asyncio
from pathlib import Path

# Ensure UTF-8 output encoding on Windows consoles
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Ensure paths
_current = Path(__file__).resolve().parent
if str(_current) not in sys.path:
    sys.path.insert(0, str(_current))

from truthgpt_cloud import (
    TruthGPTCloudClient,
    CloudTier,
    get_all_tiers,
    subscription_manager
)


def print_banner():
    print("=" * 75)
    print(" 🚀 TruthGPT Cloud CLI - Frontier AI & Formal Verification Platform")
    print("    Mathematical Veracity • Z3 SMT Solvers • Merkle Proofs • Swarms")
    print("=" * 75)


async def main_cli():
    print_banner()
    client = TruthGPTCloudClient()
    status = client.get_subscription_status()
    
    print(f"\n👤 Usuario Activo: {status['name']} ({status['email']})")
    print(f"💎 Nivel Actual: {status['tier_name']} [{status['tier_badge']}]")
    print(f"📊 Cuota Hoy: {status['metrics']['tokens_consumed_today']:,} / {status['metrics']['daily_token_limit']:,} tokens ({status['metrics']['percent_quota_used']}%)")
    print(f"⚡ Nivel Verificación SMT: Nivel {status['features']['smt_verification_depth']} | Latencia: {status['features']['latency_tier']}")
    print("-" * 75)

    while True:
        print("\nOpciones de TruthGPT Cloud:")
        print(" [1] 💬 Preguntar a TruthGPT Cloud (Inferencia con Z3 SMT & Merkle Proof)")
        print(" [2] 🌊 Streaming en Tiempo Real (SSE)")
        print(" [3] 🛡️ Verificar Teorema / Invariante Formal en Z3 Solver")
        print(" [4] 🐝 Ejecutar Swarm Autónomo Multi-Agente con Debate")
        print(" [5] 💎 Ver Planes de Suscripción y Precios")
        print(" [6] ⬆️ Actualizar Suscripción (Upgrade Tier)")
        print(" [7] 🔑 Gestionar y Revocar Claves de API")
        print(" [8] 🔔 Ver Registro de Webhooks y Eventos")
        print(" [0] 🚪 Salir")
        
        choice = input("\nSeleccione una opción: ").strip()
        
        if choice == "1":
            prompt = input("\nIngrese su consulta matemática o técnica: ").strip()
            if not prompt:
                continue
            print("\n⏳ Enrutando a través de TruthGPT Cloud con aceleración GPU...")
            res = await client.ask_async(prompt, enable_formal_verification=True)
            print("\n" + "=" * 60)
            print(res.content)
            print("=" * 60)
            if res.proof_certificate:
                cert = res.proof_certificate
                print(f"📜 Certificado de Verdad: {cert['proof_tree_hash']} | Status: {cert['status']} ({cert['verification_time_ms']} ms)")
                if cert.get("mathematical_invariants"):
                    print("   Invariantes Formales:")
                    for inv in cert["mathematical_invariants"]:
                        print(f"   • {inv}")
            print(f"⏱️ Tiempo: {res.execution_time_ms} ms | TTFT: {res.time_to_first_token_ms} ms | Tokens: {res.tokens_consumed}")
            
        elif choice == "2":
            prompt = input("\nIngrese su consulta para streaming en vivo: ").strip()
            if not prompt:
                continue
            print("\n🌊 Iniciando stream de tokens:\n")
            async for token in client.ask_stream_async(prompt):
                sys.stdout.write(token)
                sys.stdout.flush()
            print("\n\n✅ Stream completado.")

        elif choice == "3":
            claim = input("\nIngrese la afirmación lógica o matemática a verificar: ").strip()
            if not claim:
                continue
            print("⏳ Ejecutando Solucionador Z3 SMT en la nube...")
            cert = client.verify_claim(claim)
            print("\n📜 Certificado de Prueba Formal:")
            print(f" - ID Certificado: {cert.certificate_id}")
            print(f" - Estado Lógico: {cert.status}")
            print(f" - Motor Solver: {cert.solver_engine}")
            print(f" - Raíz Merkle (SHA-256): {cert.proof_tree_hash}")
            print(f" - Confianza Matemática: {cert.confidence_score * 100}%")
            print(f" - Invariantes Evaluados ({len(cert.mathematical_invariants)}):")
            for inv in cert.mathematical_invariants:
                print(f"   • {inv}")
            if cert.counterexample:
                print(f" ⚠️ Contraejemplo encontrado: {cert.counterexample}")
                
        elif choice == "4":
            prompt = input("\nIngrese el objetivo para el Swarm de Investigación: ").strip()
            if not prompt:
                continue
            print("⏳ Desplegando Swarm de Agentes Especializados en Paralelo...")
            trace = await client.run_swarm_async(prompt)
            print(f"\n🐝 Sesión Swarm Completada ({trace.execution_time_ms} ms, Consenso: {round(trace.consensus_score * 100, 1)}%):")
            for agt in trace.agents_involved:
                print(f"\n 🔹 [{agt.role_name}] (Confianza: {round(agt.confidence * 100, 1)}%):")
                for step in agt.reasoning_steps:
                    print(f"    - {step}")
                print(f"    Contribución: {agt.contribution}")
            print(f"\nConsenso Final: {trace.consensus_summary}")
            
        elif choice == "5":
            tiers = get_all_tiers()
            print("\n💎 MATRIZ DE SUSCRIPCIÓN TRUTHGPT CLOUD:")
            for t in tiers:
                print(f"\n• {t['name']} ({t['badge']})")
                print(f"  Precio: ${t['price_monthly_usd']}/mes (${t['price_yearly_usd']}/año)")
                print(f"  Límites: {t['daily_token_limit']:,} tokens/día | {t['requests_per_minute']} RPM | Swarm: {t['max_swarm_agents']} agentes")
                print(f"  Verificación: {t['smt_verification_level']} | Latencia: {t['latency_tier']}")
                
        elif choice == "6":
            print("\nNiveles disponibles: pro, ultra, enterprise")
            target = input("Seleccione el nivel al que desea actualizar: ").strip().lower()
            if target in ["pro", "ultra", "enterprise"]:
                res = client.upgrade_tier(target)
                print(f"\n✅ ¡Felicidades! Has actualizado exitosamente a {res['tier_name']}.")
                print(f"Factura generada: {res['invoice']['invoice_id']} por ${res['invoice']['amount_usd']}")
            else:
                print("❌ Nivel no válido.")
                
        elif choice == "7":
            st = client.get_subscription_status()
            print(f"\n🔑 Claves de API registradas ({len(st['api_keys'])}):")
            for k in st['api_keys']:
                print(f" - {k}")
            print("\n [a] Generar nueva clave")
            print(" [r] Revocar clave existente")
            print(" [v] Volver")
            sub_opt = input("Opción: ").strip().lower()
            if sub_opt == "a":
                try:
                    new_k = client.generate_api_key()
                    print(f"✅ Nueva clave generada: {new_k}")
                except Exception as e:
                    print(f"❌ Error: {e}")
            elif sub_opt == "r":
                key_to_revoke = input("Pegue la clave a revocar: ").strip()
                if client.revoke_api_key(key_to_revoke):
                    print("✅ Clave revocada exitosamente.")
                else:
                    print("❌ No se encontró la clave.")

        elif choice == "8":
            webhooks = client.list_webhooks()
            print(f"\n🔔 Webhooks Registrados ({len(webhooks)}):")
            for w in webhooks:
                print(f" - ID: {w['webhook_id']} | URL: {w['target_url']} | Eventos: {w['subscribed_events']}")
            reg = input("¿Desea registrar un nuevo webhook? (s/n): ").strip().lower()
            if reg == "s":
                url = input("URL de destino (https://...): ").strip()
                if url:
                    sub = client.register_webhook(url)
                    print(f"✅ Webhook registrado: ID {sub['webhook_id']}")
                    
        elif choice == "0":
            print("\n👋 ¡Gracias por usar TruthGPT Cloud!")
            break


if __name__ == "__main__":
    asyncio.run(main_cli())
