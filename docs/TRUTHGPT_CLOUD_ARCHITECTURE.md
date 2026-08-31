# 🌌 TruthGPT Cloud - Architectural Specification & SaaS Platform Manual

TruthGPT Cloud es la plataforma SaaS nativa y ecosistema de pago de **TruthGPT**, diseñada para ofrecer razonamiento matemático axiomático, verificación formal mediante Solucionadores **Z3 SMT**, orquestación Swarm multi-agente distribuida, y aceleración de inferencia GPU con **TensorRT-LLM**.

---

## 🏛️ 1. Arquitectura General del Sistema

TruthGPT Cloud implementa un modelo desacoplado de microservicios y SDKs para inferencia de ultra-baja latencia y validación formal estricta:

```
                  ┌────────────────────────────────────────┐
                  │          TruthGPT Web App / UI         │
                  │        (Next.js Dashboard & Chat)      │
                  └───────────────────┬────────────────────┘
                                      │ REST / WebSocket
                  ┌───────────────────▼────────────────────┐
                  │       TruthGPT Cloud FastAPI Hub       │
                  │      (truthgpt_cloud_server.py)        │
                  └───────┬──────────────────────┬─────────┘
                          │                      │
       ┌──────────────────▼──────┐      ┌────────▼─────────────────┐
       │   Subscription Manager  │      │  Multi-Tier Engine Router│
       │   & Token Accounting    │      │    (CloudRouter Engine)  │
       │  (Free, Pro, Ultra, Ent)│      └────────┬─────────────────┘
       └─────────────────────────┘               │
                          ┌──────────────────────┼─────────────────────┐
                          │                      │                     │
               ┌──────────▼─────────┐ ┌──────────▼─────────┐ ┌─────────▼──────────┐
               │ Formal Verifier SMT│ │ Multi-Agent Swarm  │ │ GPU Priority Queue │
               │  (Z3 / SymPy / CoVe│ │   (Consensus Arbiter│ │ (TensorRT H100)    │
               └────────────────────┘ └────────────────────┘ └────────────────────┘
```

---

## 💎 2. Matriz Comparativa de Niveles de Suscripción (Tiers)

A semejanza de **Gemini** (Nano / Flash / Pro / Advanced) y **OpenAI ChatGPT Plus / Pro**, TruthGPT Cloud segmenta el cómputo y el rigor matemático en cuatro niveles optimizados:

| Característica | 🌿 TruthGPT Lite (Free) | ⚡ TruthGPT Pro ($19.99/mes) | 🌌 TruthGPT Ultra ($99.99/mes) | 🏢 TruthGPT Enterprise ($499/mes) |
| :--- | :--- | :--- | :--- | :--- |
| **Público Objetivo** | Comunidad / Estudiantes | Desarrolladores / Ingenieros IA | Laboratorios Frontier / Científicos | Corporaciones / Clúster Soberano |
| **Modelos Frontier Disponibles** | `truthgpt-lite`, `deepseek-chat` | `deepseek-v3`, `claude-3-7-sonnet`, `gpt-4o`, `truthgpt-pro-smt` | `truthgpt-quantum-singularity`, `deepseek-r1-reasoner`, `ensemble-supreme` | `truthgpt-sovereign-cluster`, modelos propietarios fine-tuned |
| **Verificación Formal SMT** | Nivel 1 (SymPy Básico) | Nivel 2 (Solucionador Z3 SMT Completo) | Nivel 3 (Teoremas Cuánticos e Invariantes) | Nivel 3 + Auditoría Formal Personalizada |
| **Certificados de Verdad Criptográficos** | ❌ No | ✅ Sí (Hash SHA-256 de Invariantes) | ✅ Sí (Árbol de Prueba SAT Completo) | ✅ Sí (Auditoría Formal & Certificados Legales) |
| **Cadena de Verificación (CoVe)** | ❌ No | ✅ Auto-Backtracking Activo | ✅ Auto-Backtracking Cuántico Activo | ✅ Validación de Código y Teoremas |
| **Orquestación Swarm** | 1 Agente | 5 Agentes Especializados | 20 Agentes con Consenso Arbitrado | 100 Agentes en Malla Distribuida |
| **Límite Diario de Tokens** | 50,000 tokens | 2,000,000 tokens | 20,000,000 tokens | 100,000,000+ tokens |
| **Ventana de Contexto** | 32,768 tokens (32k) | 200,000 tokens (200k) | 2,000,000 tokens (2M) | 4,000,000 tokens (4M) |
| **Throughput (RPM)** | 15 peticiones / min | 120 peticiones / min | 600 peticiones / min | 2,000+ peticiones / min |
| **Nivel de Latencia GPU** | Estándar (Cola compartida) | Cola Prioritaria TensorRT-LLM | Zero-Queue Dedicada H100/H200 | Hardware Dedicado On-Premise / Cloud |
| **Claves de API Dedicadas** | 1 Clave | 5 Claves | 20 Claves | Claves Ilimitadas con Roles RBAC |
| **Alojamiento LoRA Privado** | ❌ No | ❌ No | ✅ Sí (Adaptadores LoRA & EMA) | ✅ Sí (Weights Privados Aislados) |
| **Garantía SLA de Uptime** | 99.0% | 99.9% | 99.99% | 99.999% con soporte 24/7 de ingenieros |

---

## 🛡️ 3. Motor de Verificación Formal Z3 SMT

A diferencia de los modelos LLM convencionales que sufren de alucinaciones, **TruthGPT Cloud** acopla directamente la inferencia con el demostrador automático de teoremas **Z3 SMT Solver**:

1. **Extracción de Invariantes:** La consulta y la respuesta son traducidas a fórmulas de lógica de primer orden y restricciones algebraicas.
2. **Chequeo de Satisfacibilidad (SAT/UNSAT):** Z3 valida si existe alguna contradicción lógica o matemática.
3. **Emisión de Certificado:** Se genera un `ProofCertificate` con identificador único, estampa de tiempo, tiempo de resolución en milisegundos y hash criptográfico (`0x...`).

---

## 💻 4. Guía de Uso del SDK en Python

### 4.1 Uso Rápido mediante `truthgpt`
```python
import truthgpt as tg

# 1. Consultar estado y nivel de suscripción
status = tg.get_subscription_info("usr_pro_sample")
print(f"Tier: {status['tier_name']} | Tokens restantes: {status['metrics']['remaining_tokens']}")

# 2. Inferencia Cloud con Verificación Formal Z3
async def main():
    res = await tg.cloud_ask(
        "Demuestra que para todo x real, (x+1)^2 = x^2 + 2x + 1",
        user_id="usr_pro_sample"
    )
    print("Contenido:", res.content)
    print("Certificado de Verdad:", res.proof_certificate["proof_tree_hash"])

# 3. Verificación Formal Directa en Z3
cert = tg.verify_formal("∀x, y ∈ ℝ: (x+y)^2 ≥ 4xy", depth=2)
print("Estado Z3:", cert.status)
```

### 4.2 Cliente Avanzado `TruthGPTCloudClient`
```python
from truthgpt_cloud import TruthGPTCloudClient, CloudTier

client = TruthGPTCloudClient(api_key="tgpt_cloud_live_your_key_here")

# Actualizar nivel de suscripción
upgrade_result = client.upgrade_tier(
    new_tier=CloudTier.ULTRA,
    billing_cycle="yearly",
    payment_method="stripe_card"
)
print("Nuevo plan activo:", upgrade_result["tier_name"])

# Ejecutar Swarm de Investigación
swarm_trace = client.run_swarm("Diseñar kernel CUDA con invariantes de convergencia")
print("Consenso alcanzado:", swarm_trace.consensus_summary)
```

---

## 🌐 5. Endpoints de la API REST (FastAPI)

El servidor expone los siguientes endpoints estandarizados:

- `GET /api/v1/cloud/tiers`: Lista completa de niveles y características.
- `POST /api/v1/cloud/auth/signup`: Registro de nuevo desarrollador / usuario.
- `GET /api/v1/cloud/subscription/me`: Consulta de métricas, consumo diario e historial de facturas.
- `POST /api/v1/cloud/subscription/upgrade`: Cambio o subida de plan (Free -> Pro / Ultra / Enterprise).
- `POST /api/v1/cloud/subscription/generate-key`: Emisión de nueva clave de API.
- `POST /api/v1/cloud/chat/completions`: Inferencia con enrutamiento GPU y certificados de prueba.
- `POST /api/v1/cloud/formal/verify`: Ejecución directa del Solucionador Z3 SMT.
- `POST /api/v1/cloud/swarm/execute`: Despliegue de Swarm de agentes con consenso.
- `GET /api/v1/cloud/papers/hub`: Catálogo de papers de investigación SOTA listos para aplicar.
- `POST /api/v1/cloud/papers/apply`: Compilación de técnicas de papers en tiempo de ejecución.

---

## 🚀 6. Despliegue y Ejecución

### 6.1 Iniciar el Servidor de Producción FastAPI
```bash
python truthgpt_cloud_server.py
```

### 6.2 Iniciar la CLI Interactiva
```bash
python truthgpt_cloud_cli.py
```

### 6.3 Iniciar el Panel Web SaaS (Next.js)
```bash
cd web_app
npm run dev
```
Acceder a `http://localhost:3000` para disfrutar de la experiencia visual completa de TruthGPT Cloud.
