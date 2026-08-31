# 🌌 TruthGPT Cloud - Plataforma Nube de Frontier AI y Verificación Formal

**TruthGPT Cloud** es el ecosistema en la nube de nivel de producción para **TruthGPT**, diseñado para ofrecer inferencia acelerada por GPU, orquestación de swarms multi-agente autónomos y **garantías matemáticas de veracidad mediante Solucionadores Formales Z3 SMT y Lógica de Hoare**.

TruthGPT Cloud introduce un modelo comercial de **suscripciones por niveles escalonados** análogo a los modelos de suscripción de frontier AI como **Google Gemini (Free / Advanced / Ultra / Enterprise)** y **OpenAI ChatGPT (Free / Plus / Pro / Enterprise)**, pero con una ventaja diferencial única en la industria: **verificación formal de teoremas y código con emisión de certificados criptográficos de verdad**.

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
| **Certificados Criptográficos** | ❌ No | ✅ SHA-256 Proof Trees | ✅ SHA-256 + Merkle Audit | ✅ Criptográfico con Firma HSM |
| **Swarm de Agentes Autónomos** | 1 Agente | Swarm de hasta 5 Agentes | Swarm Masivo de 20 Agentes | Agentes Ilimitados en Paralelo |
| **Infraestructura & GPU** | Cola Estándar CPU/GPU | GPU Prioritaria (TensorRT-LLM) | Zero-Queue Dedicado (H100/H200) | Clúster Soberano Dedicado / On-Prem |
| **Claves de API Dedicadas** | 1 Clave | 5 Claves | 20 Claves | Ilimitadas |
| **Garantía SLA Uptime** | 99.0% | 99.9% | 99.99% | 99.999% |

---

## 🏛️ Componentes y Arquitectura de TruthGPT Cloud

El sistema está estructurado de forma modular y desacoplada:

1. **`truthgpt_cloud/tiers.py`**:
   - Define el catálogo `CloudTier` (`FREE`, `PRO`, `ULTRA`, `ENTERPRISE`) y el esquema `TierConfig` con todos los parámetros técnicos y cuotas.

2. **`truthgpt_cloud/billing.py`**:
   - Motor de suscripciones, registro de usuarios, cálculo de consumo de tokens en tiempo real, gestión y rotación de API keys, pasarela de cobro y generación de facturas compliant (`Invoice`).

3. **`truthgpt_cloud/verifier.py`**:
   - Solucionador SMT basado en **Z3** y **SymPy**. Genera objetos `ProofCertificate` con estado de satisfacción lógica (`PROVEN_SAT`, `PROVEN_UNSAT`, `VERIFIED_SYMBOLIC`), invariantes evaluados y hash criptográfico `0xSHA256`.

4. **`truthgpt_cloud/swarm_cloud.py`**:
   - Orquestador de agentes autónomos especializados:
     - 🧮 **Mathematician Agent**: Modelado riguroso y formulación de hipótesis.
     - 🔍 **Logic & Boundary Auditor**: Detección de casos de borde y contradicciones.
     - 🛡️ **Formal Theorem Prover**: Generación de cláusulas SMT para Z3.
     - ⚡ **Empirical Validator**: Pruebas de estrés y benchmarking de complejidad.
     - ⚖️ **Consensus Arbiter**: Síntesis y emisión del veredicto final.

5. **`truthgpt_cloud/engine_router.py`**:
   - Enrutador de inferencia con control de acceso por nivel, selección automática de modelos y control dinámico de cuotas.

6. **`truthgpt_cloud/client.py`**:
   - SDK cliente en Python (`TruthGPTCloudClient`) con métodos sincrónicos y asincrónicos para integración instantánea.

7. **`truthgpt_cloud_server.py`**:
   - Servidor **FastAPI** con endpoints REST documentados en OpenAPI/Swagger.

8. **`truthgpt_cloud_cli.py`**:
   - Terminal interactiva rica para usuarios y administradores.

9. **`web_app/`**:
   - Panel de control Next.js con interfaz visual moderna, checkout Stripe/Crypto, terminal de chat con Z3 y gestor de API keys.

---

## 🚀 Guía de Uso

### 1. Iniciar el Servidor de TruthGPT Cloud (FastAPI)
```bash
python truthgpt_cloud_server.py
```
*El servidor iniciará en `http://localhost:8000` con documentación interactiva en `http://localhost:8000/docs`.*

### 2. Uso mediante el SDK de Python
```python
import asyncio
from truthgpt_cloud import TruthGPTCloudClient, CloudTier

# Inicializar cliente con API Key o usuario
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
        print("Certificado Z3:", res.proof_certificate["proof_tree_hash"])
        print("Estado:", res.proof_certificate["status"])

asyncio.run(main())
```

### 3. Actualización de Plan (Upgrade Tier)
```python
# Actualizar de Free a Pro ($19.99/mes)
upgrade_result = client.upgrade_tier(target_tier="pro", billing_cycle="monthly", payment_method="stripe_card")
print("Nuevo plan:", upgrade_result["tier_name"])
print("Factura:", upgrade_result["invoice"]["invoice_id"])
```

### 4. CLI Interactiva
```bash
python truthgpt_cloud_cli.py
```

### 5. Iniciar la Interfaz Web (Next.js)
```bash
cd web_app
npm run dev
```
*Accede al dashboard en `http://localhost:3000` para disfrutar de la experiencia visual completa.*

---

## 🧪 Validación y Tests Automatizados

La plataforma cuenta con una suite completa de pruebas unitarias y de integración que verifica:
- Catálogo de tiers y coherencia de cuotas.
- Registro y persistencia de cuentas y claves API.
- Actualización de niveles y emisión de facturas.
- Solución de teoremas en Z3 SMT y generación de hashes criptográficos.
- Ejecución distribuida de Swarms multi-agente.
- Enrutamiento por cuotas y límites diarios de tokens.
- Endpoints HTTP del servidor FastAPI.

Para ejecutar los tests:
```bash
python test_truthgpt_cloud_suite.py
```
Resultado: **7/7 tests superados exitosamente (OK)**.
