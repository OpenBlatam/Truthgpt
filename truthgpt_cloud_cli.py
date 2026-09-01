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
    print("=" * 80)
    print(" 🌌 TruthGPT Cloud CLI v2.2 - Frontier AI & Mathematical Formal Verification")
    print("    Z3 SMT Solvers • Merkle Proof Trees • Multi-Agent Swarms • SSE Streaming")
    print("=" * 80)


async def main_cli():
    print_banner()
    client = TruthGPTCloudClient()
    status = client.get_subscription_status()
    
    print(f"\n👤 Usuario Activo: {status['name']} ({status['email']})")
    print(f"💎 Nivel Actual: {status['tier_name']} [{status['tier_badge']}]")
    print(f"📊 Cuota Hoy: {status['metrics']['tokens_consumed_today']:,} / {status['metrics']['daily_token_limit']:,} tokens ({status['metrics']['percent_quota_used']}%)")
    print(f"⚡ Nivel Verificación SMT: Nivel {status['features']['smt_verification_depth']} | Latencia: {status['features']['latency_tier']}")
    print("-" * 80)

    while True:
        print("\nOpciones de TruthGPT Cloud:")
        print(" [1]  💬 Preguntar a TruthGPT Cloud (Inferencia con Z3 SMT & Merkle Proof)")
        print(" [2]  🌊 Streaming en Tiempo Real (SSE)")
        print(" [3]  🛡️ Verificar Teorema / Invariante Formal en Z3 Solver")
        print(" [4]  🐝 Ejecutar Swarm Autónomo Multi-Agente con Debate")
        print(" [5]  🔬 Explorar & Compilar Papers SOTA (ArXiv Hub)")
        print(" [6]  📊 Ver Métricas del Clúster, Telemetría & Caché Semántica")
        print(" [7]  💎 Ver Planes de Suscripción y Precios")
        print(" [8]  ⬆️ Actualizar Suscripción (Upgrade Tier)")
        print(" [9]  🔑 Gestionar y Revocar Claves de API")
        print(" [10] 🔔 Ver Registro de Webhooks y Eventos")
        print(" [11] 📜 Exportar Teorema a Formato SMT-LIB2")
        print(" [12] 🐍 Verificación Formal de Código Python (Hoare DbC & AST)")
        print(" [13] 📐 Exportar Teorema a Lean 4 / Coq")
        print(" [14] 🌳 Auditar Rama y Raíz del Árbol Merkle Criptográfico")
        print(" [15] 📐 Verificación Formal de Formas de Tensores (Z3 SMT)")
        print(" [16] 🔬 Verificación de Estabilidad Numérica y Gradientes")
        print(" [17] 🐝 Ejecutar Swarm con Topología Personalizada (Star, Ring, Mesh)")
        print(" [0]  🚪 Salir")
        
        choice = input("\nSeleccione una opción: ").strip()
        
        if choice == "1":
            prompt = input("\nIngrese su consulta matemática o técnica: ").strip()
            if not prompt:
                continue
            print("\n⏳ Enrutando a través de TruthGPT Cloud con aceleración GPU...")
            res = await client.ask_async(prompt, enable_formal_verification=True)
            print("\n" + "=" * 65)
            print(res.content)
            print("=" * 65)
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
            print(f" - Confianza Matemática: {round(cert.confidence_score * 100, 2)}%")
            print(f" - Invariantes Evaluados ({len(cert.mathematical_invariants)}):")
            for inv in cert.mathematical_invariants:
                print(f"   • {inv}")
            if cert.counterexample:
                print(f" ⚠️ Contraejemplo encontrado: {cert.counterexample}")
            
            sub = input("\n¿Desea exportar el script SMT-LIB2? (s/n): ").strip().lower()
            if sub == "s":
                print("\n" + "-" * 50)
                print(client.export_smt2(cert))
                print("-" * 50)
                
        elif choice == "4":
            prompt = input("\nIngrese el objetivo para el Swarm de Investigación: ").strip()
            if not prompt:
                continue
            print("⏳ Desplegando Swarm de Agentes Especializados en Paralelo...")
            trace = await client.run_swarm_async(prompt)
            print(f"\n🐝 Sesión Swarm Completada ({trace.execution_time_ms} ms, Consenso: {round(trace.consensus_score * 100, 1)}%):")
            for agt in trace.agents_involved:
                print(f"\n 🔹 [{agt.role_name}] (Confianza: {round(agt.confidence * 100, 1)}%):")
                if agt.reasoning_steps:
                    for step in agt.reasoning_steps:
                        print(f"    - {step}")
                print(f"    Contribución: {agt.contribution}")
            print(f"\nConsenso Final: {trace.consensus_summary}")

        elif choice == "5":
            papers = client.list_papers()
            print(f"\n🔬 SOTA AI RESEARCH PAPERS HUB ({len(papers)} papers disponibles):")
            for idx, p in enumerate(papers, 1):
                print(f"\n [{idx}] {p['title']} ({p['paper_id']})")
                print(f"     Categoría: {p['category']} | Impacto: {p.get('impact_factor', 9.8)}/10")
                print(f"     Planes compatibles: {', '.join(p['supported_tiers'])}")
            
            p_sel = input("\nIngrese el ID del paper a compilar (o Enter para omitir): ").strip()
            if p_sel:
                try:
                    res = client.compile_paper(p_sel)
                    print(f"✅ Resultado: {res['message']}")
                    print(f"   Optimización: {res['optimization_boost']}")
                except Exception as e:
                    print(f"❌ Error al compilar paper: {e}")

        elif choice == "6":
            metrics = client.get_telemetry_metrics()
            cache_stats = client.get_cache_stats()
            print("\n📊 TELEMETRÍA DEL CLÚSTER TRUTHGPT CLOUD:")
            print(f" - Tiempo en Línea: {metrics['uptime_seconds']} segundos")
            print(f" - Total Inferencias: {metrics['total_inferences']}")
            print(f" - Total Verificaciones: {metrics['total_verifications']}")
            print(f" - Solidez Formal: {metrics['formal_soundness_percent']}%")
            print(f" - Latencias de Inferencia: p50={metrics['inference_latency_ms']['p50']}ms | p95={metrics['inference_latency_ms']['p95']}ms | p99={metrics['inference_latency_ms']['p99']}ms")
            print("\n⚡ ESTADÍSTICAS DE CACHÉ SEMÁNTICA:")
            print(f" - Entradas en Caché: {cache_stats['cached_entries']} / {cache_stats['max_capacity']}")
            print(f" - Ratio de Aciertos (Hit Ratio): {cache_stats['hit_ratio_percent']}%")
            print(f" - Tokens Ahorrados: {cache_stats['total_tokens_saved']:,}")
            print(f" - Tiempo de Cómputo Ahorrado: {cache_stats['estimated_compute_ms_saved']} ms")
            
        elif choice == "7":
            tiers = get_all_tiers()
            print("\n💎 MATRIZ DE SUSCRIPCIÓN TRUTHGPT CLOUD:")
            for t in tiers:
                print(f"\n• {t['name']} ({t['badge']})")
                print(f"  Precio: ${t['price_monthly_usd']}/mes (${t['price_yearly_usd']}/año)")
                print(f"  Límites: {t['daily_token_limit']:,} tokens/día | {t['requests_per_minute']} RPM | Swarm: {t['max_swarm_agents']} agentes")
                print(f"  Verificación: {t['smt_verification_level']} | Latencia: {t['latency_tier']}")
                
        elif choice == "8":
            print("\nNiveles disponibles: pro, ultra, enterprise")
            target = input("Seleccione el nivel al que desea actualizar: ").strip().lower()
            if target in ["pro", "ultra", "enterprise"]:
                res = client.upgrade_tier(target)
                print(f"\n✅ ¡Felicidades! Has actualizado exitosamente a {res['tier_name']}.")
                print(f"Factura generada: {res['invoice']['invoice_id']} por ${res['invoice']['amount_usd']}")
            else:
                print("❌ Nivel no válido.")
                
        elif choice == "9":
            st = client.get_subscription_status()
            print(f"\n🔑 Claves de API registradas ({len(st['api_keys'])}):")
            for k in st['api_keys']:
                print(f" - {k}")
            print("\n [a] Generar nueva clave")
            print(" [r] Revocar clave existente")
            print(" [v] Volver")
            sub_opt = input("Opción: ").strip().lower()
            if sub_opt == "a":
                lbl = input("Etiqueta para la clave (ej. Servidor Producción): ").strip() or "Default Key"
                try:
                    new_k = client.generate_api_key(label=lbl)
                    print(f"✅ Nueva clave generada: {new_k}")
                except Exception as e:
                    print(f"❌ Error: {e}")
            elif sub_opt == "r":
                key_to_revoke = input("Pegue la clave a revocar: ").strip()
                if client.revoke_api_key(key_to_revoke):
                    print("✅ Clave revocada exitosamente.")
                else:
                    print("❌ No se encontró la clave.")

        elif choice == "10":
            webhooks = client.list_webhooks()
            print(f"\n🔔 Webhooks Registrados ({len(webhooks)}):")
            for w in webhooks:
                print(f" - ID: {w['webhook_id']} | URL: {w['target_url']} | Eventos: {w['subscribed_events']}")
            reg = input("\n¿Desea registrar un nuevo webhook? (s/n): ").strip().lower()
            if reg == "s":
                url = input("URL de destino (https://...): ").strip()
                if url:
                    sub = client.register_webhook(url)
                    print(f"✅ Webhook registrado: ID {sub['webhook_id']}")
        
        elif choice == "11":
            claim = input("\nIngrese el teorema o proposición matemática: ").strip()
            if claim:
                cert = client.verify_claim(claim)
                print("\n" + "=" * 60)
                print("📜 EXPORTACIÓN SMT-LIB2 (Estándar Formal):")
                print(client.export_smt2(cert))
                print("=" * 60)

        elif choice == "12":
            print("\n🐍 Ingrese el código Python a verificar (o presione Enter para usar función de ejemplo):")
            sample_code = (
                "def binary_search(arr: list, target: int) -> int:\n"
                "    '''\n"
                "    :pre: len(arr) >= 0 and is_sorted(arr)\n"
                "    :post: return_val >= -1 and return_val < len(arr)\n"
                "    :inv: low <= high and target not in arr[:low]\n"
                "    '''\n"
                "    low, high = 0, len(arr) - 1\n"
                "    while low <= high:\n"
                "        mid = (low + high) // 2\n"
                "        if arr[mid] == target:\n"
                "            return mid\n"
                "        elif arr[mid] < target:\n"
                "            low = mid + 1\n"
                "        else:\n"
                "            high = mid - 1\n"
                "    return -1"
            )
            print(f"Código de ejemplo:\n{sample_code}")
            custom = input("\n¿Desea usar este ejemplo? (s/n): ").strip().lower()
            code_to_verify = sample_code if custom != "n" else input("Pegue su código: ")
            
            print("⏳ Ejecutando análisis formal AST y verificación Hoare en Z3 SMT...")
            contract_res = client.verify_python_code(code_to_verify)
            print("\n" + "=" * 60)
            print(f"📜 RESULTADO DE VERIFICACIÓN FORMAL DE CÓDIGO:")
            print(f" • Función: {contract_res.function_name}")
            print(f" • Estado General: {contract_res.overall_status}")
            print(f" • Precondiciones Verificadas: {'✅ SI' if contract_res.preconditions_verified else '❌ NO'}")
            print(f" • Postcondiciones Verificadas: {'✅ SI' if contract_res.postconditions_verified else '❌ NO'}")
            print(f" • Invariantes de Bucle Preservados: {'✅ SI' if contract_res.invariants_preserved else '❌ NO'}")
            print(f" • Nodos AST Analizados: {contract_res.details.get('ast_nodes_evaluated', 0)}")
            print(f" • Raíz Merkle de Prueba: {contract_res.certificate.proof_tree_hash}")
            print("=" * 60)

        elif choice == "13":
            claim = input("\nIngrese la proposición matemática para exportar a Lean 4 / Coq / Isabelle: ").strip()
            if not claim:
                claim = "x^2 + y^2 >= 2*x*y"
            cert = client.verify_claim(claim)
            print(f"\n📐 [LEAN 4 THEOREM CODE]:\n{client.export_proof_to_lean4(cert)}\n")
            print(f"📐 [COQ LEMMA SCRIPT]:\n{client.export_proof_to_coq(cert)}\n")
            print(f"📐 [ISABELLE/HOL THEORY]:\n{client.export_proof_to_isabelle(cert)}\n")

        elif choice == "14":
            claim = input("\nIngrese afirmación para generar y auditar árbol Merkle: ").strip()
            if not claim:
                claim = "x >= 0 -> x + 1 > 0"
            cert = client.verify_claim(claim)
            print(f"\n🌳 Raíz Merkle Generada: {cert.proof_tree_hash}")
            if cert.merkle_proof_path:
                leaf_data = f"claim:{cert.theorem_or_claim}"
                is_valid = client.verify_merkle_branch(leaf_data, cert.merkle_proof_path, cert.proof_tree_hash)
                print(f" • Verificación de Rama Criptográfica: {'✅ VALIDADA (Inclusión demostrada)' if is_valid else '❌ INVÁLIDA'}")
                print(f" • Pasos en Rama Merkle: {len(cert.merkle_proof_path)}")
                for idx, node in enumerate(cert.merkle_proof_path):
                    print(f"   [{idx+1}] Posición: {node['position']} | Hash: {node['hash'][:16]}...")

        elif choice == "15":
            print("\n📐 VERIFICACIÓN DE CONTRATOS DE FORMA DE TENSORES:")
            print("Ejemplo: Matmul [B, S, H] @ [H, D] -> [B, S, D]")
            op = input("Operación (matmul / attention / conv2d): ").strip() or "matmul"
            res = client.verify_tensor_shapes([32, 128, 768], [768, 3072], operation=op)
            print(f"\n • Estado: {'✅ COMPATIBLE' if res['compatible'] else '❌ INCOMPATIBLE'}")
            print(f" • Forma Resultante: {res['resulting_shape']}")
            print(f" • Raíz Merkle Z3: {res['proof_certificate']['proof_tree_hash']}")
            print(f" • Invariantes Demostrados: {res['proof_certificate']['mathematical_invariants']}")

        elif choice == "16":
            print("\n🔬 VERIFICACIÓN DE ESTABILIDAD NUMÉRICA:")
            loss_expr = input("Expresión / Función de Pérdida (o Enter para Cross-Entropy con Log-Sum-Exp): ").strip()
            if not loss_expr:
                loss_expr = "loss = -sum(y * log(softmax(z) + eps))"
            res = client.verify_numerical_stability(loss_expr, gradient_clipping_bound=1.0, epsilon=1e-8)
            print(f"\n • Estado: {'✅ ESTABLE' if res['stable'] else '⚠️ RIESGO DETECTADO'}")
            print(f" • Grado de Riesgo Desvanecimiento/Explosión: {res['risk_level']}")
            print(f" • Certificado Z3: {res['proof_certificate']['proof_tree_hash']}")
            print(f" • Garantías: {res['proof_certificate']['mathematical_invariants']}")

        elif choice == "17":
            print("\n🐝 EJECUCIÓN DE SWARM CON TOPOLOGÍA:")
            print("Topologías: hierarchical, star, mesh, ring")
            top = input("Seleccione topología: ").strip().lower() or "hierarchical"
            obj = input("Objetivo de investigación: ").strip() or "Diseño de un optimizador de gradiente estocástico con Z3 SMT"
            trace = await client.run_swarm_async(obj, topology=top)
            print(f"\n✅ Swarm completado con Topología [{trace.topology.upper()}]:")
            print(f" • Consenso: {round(trace.consensus_score * 100, 1)}%")
            print(f" • Resumen: {trace.consensus_summary}")
                    
        elif choice == "0":
            print("\n👋 ¡Gracias por usar TruthGPT Cloud!")
            break


if __name__ == "__main__":
    asyncio.run(main_cli())
