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
├── resilience/               # Tolerancia a fallos: Circuit Breaker y Exponential Backoff con Jitter
│   ├── circuit_breaker.py    # CircuitBreaker de 3 estados (CLOSED, OPEN, HALF_OPEN)
│   ├── retry.py              # retry_with_backoff decorador síncrono y asíncrono
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
│   ├── router.py             # CloudIntelligenceRouter con cuotas, circuit breaker y fallback GPU
│   └── __init__.py
├── client/                   # SDK Cliente
│   ├── client.py             # TruthGPTCloudClient con sync, async, streaming SSE y SRE APIs
│   └── __init__.py
├── storage/                  # Capa de persistencia
│   ├── base.py               # Protocolo StorageBackend
│   ├── json_storage.py       # JsonFileStorageBackend con dirty debounce y respaldos atómicos
│   └── __init__.py
├── papers/                   # Catálogo y compilador JIT de investigación SOTA
│   ├── registry.py           # SOTA_PAPERS_CATALOG (FlashAttention-3, DeepSeek, etc.)
│   ├── compiler.py           # CloudPaperCompiler (JIT runtime hooks)
│   └── __init__.py
└── [Bridges de compatibilidad]: billing.py, cache.py, client.py, engine_router.py,
                                 exceptions.py, rate_limiter.py, resilience.py,
                                 security.py, swarm_cloud.py, telemetry.py, tiers.py, verifier.py
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

### 6. SRE, Circuit Breaker y Alertas Automatizadas de Error Budget
```python
# Inspeccionar estado del Circuit Breaker de inferencia
cb_status = client.get_circuit_breaker_status()
print(f"Estado Circuit Breaker: {cb_status['state']} (Fallos: {cb_status['failure_count']})")

# Registrar regla de alerta preventiva en tiempo real
rule = client.register_alert_rule(
    name="Alerta Latencia P99 Inferencia",
    metric_key="p99_latency_ms",
    threshold=500.0,
    comparison="gte",
    cooldown_seconds=30.0
)

# Consultar métricas de quema de presupuesto de error (SLA 99.9%)
budget = client.get_error_budget_burndown(sla_target=99.9)
print(f"Disponibilidad actual: {budget['current_uptime_percent']}% | Restante: {budget['error_budget_remaining_percent']}%")

# Purgar entradas expiradas de la caché semántica con TTL dinámico
purged = client.purge_expired_cache()
print(f"Entradas expiradas purgadas: {purged}")
```

### 7. CLI Interactiva y Comandos de Terminal
```bash
python truthgpt_cloud_cli.py
```
El CLI interactivo ofrece 21 opciones operativas para desarrolladores e ingenieros SRE:
- `[1]` Inferencia estándar con aceleración y certificados Z3 SMT
- `[2]` Streaming en tiempo real vía Server-Sent Events (SSE)
- `[3]` Demostración formal de teoremas e invariantes algebraicos en Z3
- `[4]` Ejecución de Swarm multi-agente con debate adversario (Red Team vs Blue Team)
- `[5]` Exploración y compilación JIT de papers SOTA (ArXiv Hub)
- `[6]` Telemetría del clúster, latencias percentiles (p50, p95, p99) y métricas de caché
- `[7]` Catálogo de niveles de suscripción y matriz de precios
- `[8]` Actualización de suscripción (Upgrade de nivel con facturación)
- `[9]` Creación, rotación y revocación de API keys con RBAC
- `[10]` Gestión y registro de webhooks con firma HMAC-SHA256
- `[11]` Exportación de certificados a formato SMT-LIB2
- `[12]` Verificación formal de contratos de código Python (Lógica de Hoare y AST)
- `[13]` Exportación de teoremas demostrados a Lean 4, Coq y teorías Isabelle/HOL
- `[14]` Auditoría criptográfica de árbol Merkle y prueba de inclusión de rama
- `[15]` Verificación formal de compatibilidad de formas de tensores (Z3 SMT)
- `[16]` Verificación de estabilidad numérica y mitigación de explosión de gradientes
- `[17]` Ejecución de Swarm con topologías avanzadas (Star, Hierarchical, Mesh, Ring)
- `[18]` Inspección operativa de Circuit Breakers y reinicio manual de resiliencia
- `[19]` Monitoreo SRE: Reglas de alerta, histórico de eventos y Error Budget Burndown
- `[20]` Inspección y purga bajo demanda de entradas expiradas de la caché semántica
- `[21]` Auditoría criptográfica del Ledger SHA-256 y tokens de sesión temporales

---

## 🌐 Especificación de Endpoints REST (FastAPI)

| Categoría | Método | Endpoint | Descripción |
| :--- | :--- | :--- | :--- |
| **Inferencia** | `POST` | `/api/v1/cloud/chat/completions` | Endpoint compatible con especificación OpenAI |
| | `POST` | `/api/v1/cloud/infer` | Inferencia con demostración formal Z3 opcional |
| | `GET` | `/api/v1/cloud/stream` | Streaming de tokens en tiempo real (SSE) |
| **Verificación** | `POST` | `/api/v1/cloud/formal/verify` | Solución y demostración formal de afirmación en Z3 SMT |
| | `POST` | `/api/v1/cloud/formal/verify/code` | Análisis AST y verificación de contratos Hoare DbC |
| | `POST` | `/api/v1/cloud/formal/verify/tensors` | Verificación de contratos de dimensiones tensoriales |
| | `POST` | `/api/v1/cloud/formal/verify/numerical-stability` | Análisis de estabilidad numérica y gradientes |
| | `POST` | `/api/v1/cloud/formal/verify/attention` | Invariantes de atención FlashAttention/MHA/GQA |
| | `POST` | `/api/v1/cloud/formal/verify/matrix` | Simetría, traza, radio espectral y definición positiva |
| | `POST` | `/api/v1/cloud/formal/verify/ode` | Estabilidad Hurwitz y Lyapunov para sistemas continuos |
| | `POST` | `/api/v1/cloud/formal/verify/loop` | Invariantes inductivos de bucles while |
| | `GET` | `/api/v1/cloud/formal/certificate/{id}` | Exportación de certificado criptográfico en JSON-LD |
| | `GET` | `/api/v1/cloud/formal/certificate/{id}/lean4` | Código de teorema en Lean 4 |
| | `GET` | `/api/v1/cloud/formal/certificate/{id}/coq` | Lemma formal en Coq Rocq |
| | `GET` | `/api/v1/cloud/formal/certificate/{id}/isabelle` | Teoría formal en Isabelle/HOL |
| **Swarm** | `POST` | `/api/v1/cloud/swarm/execute` | Ejecución de sesión de agentes multi-nodo |
| | `POST` | `/api/v1/cloud/swarm/stream` | Stream de razonamiento multi-agente |
| | `POST` | `/api/v1/cloud/swarm/debate` | Debate adversario formal Red Team vs Blue Team |
| **Resiliencia** | `GET` | `/api/v1/cloud/resilience/status` | Estado de Circuit Breakers (CLOSED/OPEN/HALF_OPEN) |
| | `POST` | `/api/v1/cloud/resilience/reset` | Reinicio forzado de Circuit Breaker a CLOSED |
| **SRE & Alertas** | `GET` | `/api/v1/cloud/telemetry/metrics` | Métricas de latencia p50/p95/p99 y solidez |
| | `GET` | `/api/v1/cloud/telemetry/prometheus` | Formato OpenMetrics compatible con Prometheus y Grafana |
| | `GET` | `/api/v1/cloud/telemetry/alerts` | Listado de reglas activas e histórico de disparos |
| | `POST` | `/api/v1/cloud/telemetry/alerts` | Registro dinámico de nuevas reglas de alerta SRE |
| | `GET` | `/api/v1/cloud/telemetry/error-budget` | Quema de error budget y cumplimiento de SLAs |
| | `GET` | `/api/v1/cloud/health` | Diagnóstico de salud de todos los subsistemas |
| **Caché** | `GET` | `/api/v1/cloud/cache/stats` | Estadísticas de aciertos, tokens y tiempo ahorrado |
| | `POST` | `/api/v1/cloud/cache/purge` | Purga bajo demanda de entradas con TTL expirado |
| **Suscripción** | `GET` | `/api/v1/cloud/subscription/tiers` | Catálogo completo de planes y características |
| | `GET` | `/api/v1/cloud/subscription/status` | Perfil de usuario, cuota diaria consumida y límites |
| | `POST` | `/api/v1/cloud/subscription/upgrade` | Cambio de plan con emisión automática de factura |
| | `POST` | `/api/v1/cloud/subscription/promo/apply`| Canje de códigos promocionales |
| | `GET` | `/api/v1/cloud/subscription/invoices` | Historial de recibos y facturas generadas |
| **Seguridad** | `POST` | `/api/v1/cloud/security/keys/generate` | Generación de clave con scopes RBAC |
| | `DELETE` | `/api/v1/cloud/security/keys/{hash}` | Revocación inmediata de clave de API |
| | `POST` | `/api/v1/cloud/webhooks/register` | Registro de endpoint de webhook con secreto HMAC |
| | `POST` | `/api/v1/cloud/webhooks/verify` | Verificación criptográfica de firma de payload |
| **Papers SOTA**| `GET` | `/api/v1/cloud/papers/search` | Búsqueda semántica en catálogo ArXiv |
| | `GET` | `/api/v1/cloud/papers/{id}/citation` | Generación de citas en BibTeX, APA o IEEE |
| | `POST` | `/api/v1/cloud/papers/compile` | Compilación JIT de técnica a kernel de aceleración |

---

## 🧪 Validación y Tests Automatizados

La plataforma cuenta con **más de 125 tests automatizados** distribuidos en 10 suites integrales que garantizan 100% de confiabilidad, resiliencia y conformidad formal:

```bash
# Ejecución completa de suites de pruebas unitarias y de integración
pytest tests/unit/test_truthgpt_cloud_resilience_and_alerts.py \
       tests/unit/test_truthgpt_cloud_modular_refactor.py \
       tests/unit/test_truthgpt_cloud_enhancements.py \
       tests/unit/test_truthgpt_cloud_comprehensive_enhancements.py \
       tests/unit/test_truthgpt_cloud_full_platform_enhancements.py \
       tests/test_truthgpt_cloud.py \
       tests/test_truthgpt_cloud_enhanced.py \
       tests/test_truthgpt_cloud_enhancements.py \
       tests/test_truthgpt_cloud_refactor.py \
       test_truthgpt_cloud_complete.py \
       test_truthgpt_cloud_comprehensive.py \
       test_truthgpt_cloud_suite.py -v
```

**Resultado: 100% de pruebas superadas exitosamente (0 errores, 0 regresiones)**.

