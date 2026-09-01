# 🌌 TruthGPT Cloud - Plataforma Nube de Frontier AI y Verificación Formal

**TruthGPT Cloud** es el ecosistema en la nube de nivel de producción para **TruthGPT**, diseñado para ofrecer inferencia acelerada por GPU, orquestación de swarms multi-agente autónomos, compilación JIT de papers SOTA y **garantías matemáticas de veracidad mediante Solucionadores Formales Z3 SMT, Lógica de Hoare y Árboles Merkle**.

TruthGPT Cloud implementa un modelo de **suscripciones por niveles escalonados** análogo a los modelos de frontier AI líderes (**Google Gemini, OpenAI ChatGPT, Anthropic Claude**), potenciado con una ventaja diferencial única en la industria: **demostrabilidad formal con emisión de certificados criptográficos de verdad**.

---

## 💎 Matriz Comparativa de Niveles de Suscripción (TruthGPT vs Gemini)

| Característica | 🟢 TruthGPT Lite | ⚡ TruthGPT Pro | 🌌 TruthGPT Ultra | 🏢 TruthGPT Enterprise |
| :--- | :--- | :--- | :--- | :--- |
| **Equivalente de Mercado** | *Gemini Free / ChatGPT Free* | *Gemini Advanced / ChatGPT Plus* | *Gemini Ultra / ChatGPT Pro* | *Gemini Enterprise / Claude Enterprise* |
| **Precio Mensual** | **$0.00 / mes** | **$19.99 / mes** | **$99.99 / mes** | **$499.00 / mes** (o Personalizado) |
| **Precio Anual (2 meses gratis)** | $0.00 | $199.90 / año | $999.00 / año | $4,990.00 / año |
| **Límite Diario de Tokens** | 50,000 tokens/día | 2,000,000 tokens/día | 20,000,000 tokens/día | 100,000,000+ tokens/día |
| **Ventana de Contexto** | 32,768 tokens | 200,000 tokens | 2,000,000 tokens | 4,000,000+ tokens |
| **Peticiones por Minuto (RPM)**| 15 RPM | 120 RPM | 600 RPM | 2,000+ RPM |
| **Modelos Frontier Disponibles**| `deepseek-chat`, `truthgpt-lite` | `deepseek-v3`, `claude-3-7-sonnet`, `gpt-4o`, `gemini-2-5-pro`, `truthgpt-pro-smt` | `truthgpt-quantum-singularity`, `ensemble-supreme`, `deepseek-r1`, `claude-3-7-thinking` | `truthgpt-sovereign-cluster`, Modelos Fine-Tuned Privados |
| **Verificación Formal Z3 SMT** | Nivel 1: SymPy Algebraico | Nivel 2: Z3 SMT Solver & Contratos Hoare | Nivel 3: Demostrador Cuántico & Consenso | Nivel 4: Auditoría Formal Soberana & DbC |
| **Certificados Criptográficos** | ❌ No | ✅ SHA-256 Proof Trees | ✅ SHA-256 + Merkle Audit | ✅ Criptográfico con Firma HMAC/HSM |
| **Swarm de Agentes Autónomos** | 1 Agente | Swarm de hasta 5 Agentes | Swarm Masivo de 20 Agentes | Agentes Ilimitados en Paralelo |
| **Topologías de Swarm** | Star | Star, Hierarchical | Star, Hierarchical, Mesh, Ring | Topologías Personalizadas Dinámicas |
| **Infraestructura & GPU** | Cola Estándar CPU/GPU | GPU Prioritaria (TensorRT-LLM) | Zero-Queue Dedicado (H100/H200) | Clúster Soberano Dedicado / On-Prem |
| **Claves de API Dedicadas** | 1 Clave | 5 Claves (con Scopes RBAC) | 20 Claves | Ilimitadas |
| **Garantía SLA Uptime** | 99.0% | 99.9% | 99.99% | 99.999% |

---

## 🏛️ Arquitectura Modular del Paquete `truthgpt_cloud`

El sistema ha sido refactorizado en submódulos canónicos con alta cohesión y bajo acoplamiento:

```
truthgpt_cloud/
├── __init__.py               # Re-exporta la API pública completa
├── core/                     # Dominio central: Tiers, configuraciones y excepciones
│   ├── tiers.py              # Definición de CloudTier y TierConfig
│   ├── exceptions.py         # Jerarquía tipada de errores de dominio
│   └── __init__.py
├── billing/                  # Motor de suscripciones, límites y pagos
│   ├── models.py             # UserSubscription, Invoice, UsageRecord
│   ├── subscription.py       # SubscriptionManager con soporte concurrente
│   ├── rate_limiter.py       # SlidingWindowRateLimiter y TokenBucketRateLimiter
│   ├── webhooks.py           # WebhookManager para eventos asíncronos
│   ├── gateways.py           # Stripe, Crypto USDC y Mock Payment Gateways
│   ├── storage.py            # Adaptador de almacenamiento de billing
│   └── __init__.py
├── cache/                    # Caché semántica LRU de pruebas formales y KV
│   ├── models.py             # CachedProofEntry
│   ├── proof_cache.py        # CloudProofCache y singleton proof_cache
│   └── __init__.py
├── telemetry/                # Telemetría de clúster, percentiles p50/p95/p99 y Prometheus
│   ├── models.py             # AuditLogEntry
│   ├── collector.py          # CloudTelemetryCollector y singleton cloud_telemetry
│   ├── prometheus.py         # Formateador de métricas Prometheus
│   └── __init__.py
├── security/                 # Seguridad, RBAC, hash SHA-256 de claves y rate limiter
│   ├── scopes.py             # ApiKeyScope
│   ├── models.py             # ApiKeyMetadata
│   ├── rate_limiter.py       # TokenBucketRateLimiter de seguridad
│   ├── manager.py            # CloudSecurityManager y singleton cloud_security
│   └── __init__.py
├── rate_limiting/            # Controladores de tasa de ventana deslizante
│   ├── sliding_window.py     # SlidingWindowRateLimiter y cloud_rate_limiter
│   └── __init__.py
├── verification/             # Demostración formal y criptografía
│   ├── verifier.py           # CloudFormalVerifier (Z3 SMT, Hoare, AST, Tensores)
│   ├── certificate.py        # ProofCertificate (JSON-LD, SMT2, Lean4, Coq)
│   ├── merkle.py             # MerkleTree criptográfico con validación de ramas
│   └── __init__.py
├── swarm/                    # Orquestación multi-agente
│   ├── agents.py             # SwarmAgentNode y agentes especializados
│   ├── orchestrator.py       # CloudSwarmOrchestrator con topologías
│   └── __init__.py
├── routing/                  # Enrutamiento de inferencia
│   ├── router.py             # CloudIntelligenceRouter con cuotas y fallback GPU
│   └── __init__.py
├── client/                   # SDK Cliente
│   ├── client.py             # TruthGPTCloudClient con sync, async y streaming SSE
│   └── __init__.py
├── storage/                  # Capa de persistencia
│   ├── base.py               # Protocolo StorageBackend
│   ├── json_storage.py       # JsonFileStorageBackend con respaldos atómicos
│   └── __init__.py
├── papers/                   # Catálogo y compilador JIT de investigación SOTA
│   ├── registry.py           # SOTA_PAPERS_CATALOG (FlashAttention-3, DeepSeek, etc.)
│   ├── compiler.py           # CloudPaperCompiler (JIT runtime hooks)
│   └── __init__.py
└── [Bridges de compatibilidad]: billing.py, cache.py, client.py, engine_router.py,
                                 exceptions.py, rate_limiter.py, security.py,
                                 swarm_cloud.py, telemetry.py, tiers.py, verifier.py
```

---

## 🚀 Guía de Inicio Rápido

### 1. Iniciar el Servidor FastAPI de TruthGPT Cloud
```bash
python truthgpt_cloud_server.py
```
*El servidor iniciará en `http://localhost:8000` con documentación OpenAPI interactiva en `http://localhost:8000/docs`.*

### 2. Uso mediante el SDK de Python
```python
import asyncio
from truthgpt_cloud import TruthGPTCloudClient, CloudTier

# Inicializar cliente
client = TruthGPTCloudClient(api_key="tgpt_cloud_live_tu_clave_aqui")

# Consultar estado de la suscripción y cuotas
status = client.get_subscription_status()
print(f"Plan Activo: {status['tier_name']} - Tokens restantes: {status['metrics']['remaining_tokens']}")

# Realizar consulta con Verificación Formal Z3
async def main():
    res = await client.ask_async(
        prompt="Demostrar la invariante de convergencia de gradiente conjugado",
        enable_formal_verification=True
    )
    print("Respuesta:", res.content)
    if res.proof_certificate:
        print("Certificado Z3 (Merkle Root):", res.proof_certificate["proof_tree_hash"])
        print("Estado:", res.proof_certificate["status"])

asyncio.run(main())
```

### 3. Verificación Formal de Contratos de Código Python
```python
code = """
def is_even(n: int) -> bool:
    '''
    :pre: n >= 0
    :post: (return_val == True and n % 2 == 0) or (return_val == False and n % 2 == 1)
    '''
    return n % 2 == 0
"""
result = client.verify_python_code(code)
print("Verificado:", result.overall_status)
print("Merkle Root:", result.certificate.proof_tree_hash)
```

### 4. Verificación de Formas de Tensores, Atención Transformer y Cuantización
```python
# Verificación de atención Transformer (FlashAttention-3 / GQA)
attn_res = client.verify_attention_invariants(
    query_shape=[1, 2048, 4096],
    key_shape=[1, 2048, 1024],
    value_shape=[1, 2048, 1024],
    num_heads_q=32,
    num_heads_kv=8,
    head_dim=128
)
print("Atención Validada:", attn_res["is_valid"])

# Verificación de seguridad de cuantización (FP8 / INT8 / BitNet b1.58)
quant_res = client.verify_quantization_safety(min_val=-12.0, max_val=12.0, quant_format="INT8")
print("Escala Delta:", quant_res["scale_factor"])

# Verificación de convergencia de optimizadores (AdamW, Muon, Lion, Sophia)
opt_res = client.verify_optimizer_convergence(optimizer_name="Muon", learning_rate=0.02)
print("Convergencia:", opt_res["is_valid"])
```

### 5. Debate Adversarial Multi-Agente y Ledger Criptográfico
```python
# Debate Red Team vs Blue Team
debate_res = client.execute_adversarial_debate(
    topic="Convergencia de FlashAttention en FP8",
    proponent_claim="Softmax renormalizado previene divergencia numérica"
)
print("Consenso:", debate_res["consensus_verdict"])

# Inspección de integridad del Ledger Criptográfico SHA-256
ledger_integrity = client.verify_ledger_integrity()
print("Integridad Ledger:", ledger_integrity["is_valid"])
```

### 6. CLI Interactiva y Comandos de Terminal
```bash
python truthgpt_cloud_cli.py
# O vía truth_cli
python truth_cli.py cloud verify-attention --heads-q 32 --heads-kv 8 --head-dim 128
python truth_cli.py cloud audit-ledger
python truth_cli.py cloud swarm-debate "Convergencia de Muon" "Muon acelera 2.5x"
```

---

## 🧪 Validación y Tests Automatizados

La plataforma cuenta con 69 tests automatizados que garantizan cobertura total en 7 suites:

```bash
python -m pytest tests/test_truthgpt_cloud.py tests/test_truthgpt_cloud_refactor.py tests/unit/test_truthgpt_cloud_modular_refactor.py test_truthgpt_cloud_complete.py test_truthgpt_cloud_comprehensive.py test_truthgpt_cloud_suite.py tests/unit/test_truthgpt_cloud_enhancements.py -v
```

**Resultado: 69/69 tests superados exitosamente (100% OK)**.

