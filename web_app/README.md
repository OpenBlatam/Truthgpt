# 🧠 TruthGPT Web App — Frontend Open Source Boilerplate

[![Next.js](https://img.shields.io/badge/Next.js-16.2-black?style=flat-square&logo=next.js)](https://nextjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0-blue?style=flat-square&logo=typescript)](https://www.typescriptlang.org/)
[![TailwindCSS](https://img.shields.io/badge/TailwindCSS-4.0-38bdf8?style=flat-square&logo=tailwindcss)](https://tailwindcss.com/)
[![Z3 SMT Solver](https://img.shields.io/badge/Formal_Verification-Z3_SMT-10b981?style=flat-square)](https://github.com/Z3Prover/z3)
[![License: MIT](https://img.shields.io/badge/License-MIT-purple?style=flat-square)](LICENSE)

> **Plantilla oficial y modular de frontend para [OpenBlatam/Truthgpt](https://github.com/OpenBlatam/Truthgpt).** Diseñada para que cualquier desarrollador o equipo pueda desplegar su propia interfaz de usuario web conectada a la arquitectura de agentes, búsqueda vectorial RAG y verificación formal Z3 SMT de TruthGPT en menos de 2 minutos.

---

## 🚀 Despliegue en 1 Clic

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https%3A%2F%2Fgithub.com%2FOpenBlatam%2FTruthgpt&project-name=truthgpt-frontend&repo-name=truthgpt-frontend&env=NEXT_PUBLIC_TRUTHGPT_API_URL,TRUTHGPT_API_KEY)

---

## ✨ Características Principales

* 🐝 **Acordeón de Razonamiento del Agente (`AgentSteps.tsx`):** Visualizador interactivo de pasos intermedios (recuperación RAG en Redis Vector Search, consenso multi-agente y comprobación formal SMT).
* 🛡️ **Certificados Formales de Verificación Z3 SMT (`ProofModal.tsx`):** Inspección de árboles de prueba criptográficos (SHA-256), invariantes matemáticas demostradas y estado SAT/UNSAT.
* ⚡ **Plug & Play con Doble Modo (Live Backend o Simulador Local):** Si no tienes un clúster de TruthGPT levantado, la aplicación incluye un motor inteligente de demostración para explorar todas las capacidades sin configuración previa.
* ⚙️ **Modal de Configuración Dinámica (`SettingsModal.tsx`):** Permite cambiar en caliente la URL base del backend, la API Key, los modelos (TruthGPT v2, DeepSeek-V3, Claude 3.5, Gemini 1.5 Pro) y parámetros de temperatura sin necesidad de reconstruir la app.
* 🔬 **Laboratorio SMT Interactivo (`SmtLabView.tsx`):** Sandbox visual para escribir fórmulas lógicas de primer orden, invariantes de ciclo y generar código ejecutable en Python con Microsoft Z3.
* 📚 **Explorador de Papers RAG (`PapersView.tsx`):** Catálogo indexado de literatura científica sobre métodos formales y optimización de kernels Triton.
* 🎨 **Diseño Moderno & Glassmorphism:** Paleta oscura de alta precisión, animaciones sutiles, renderizado de código con botón de copiado inmediato y tipografía Geist.

---

## 📁 Estructura del Proyecto

```plaintext
web_app/
├── app/
│   ├── api/
│   │   └── chat/route.ts       # Endpoint proxy hacia backend TruthGPT o simulador formal
│   ├── globals.css             # Paleta HSL, clases glassmorphism y animaciones
│   ├── layout.tsx              # Shell HTML5, fuentes Geist y metadatos
│   └── page.tsx                # Página principal orquestadora
├── components/
│   ├── AgentSteps.tsx          # Acordeón colapsable de pasos y fuentes RAG
│   ├── ChatInterface.tsx       # Contenedor interactivo de chat y prompts rápidos
│   ├── MessageList.tsx         # Renderizado de mensajes, markdown y bloques de código
│   ├── Navbar.tsx              # Barra superior con estado de conexión y acceso a configuración
│   ├── PapersView.tsx          # Explorador de documentos y similitud vectorial
│   ├── ProofModal.tsx          # Modal de certificados formales Z3 SMT
│   ├── SettingsModal.tsx       # Configuración de endpoints y parámetros de inferencia
│   └── SmtLabView.tsx          # Sandbox del solver formal SMT
├── types/
│   └── chat.ts                 # Interfaces TypeScript de mensajes, certificados y ajustes
├── .env.example                # Variables de entorno modelo
├── Dockerfile                  # Empaquetado de producción multi-etapa
├── docker-compose.yml          # Despliegue en 1 comando con Docker
└── package.json
```

---

## 🛠️ Inicio Rápido Local

### 1. Clonar e Instalar Dependencias

```bash
cd web_app
npm install
# o con yarn
yarn install
```

### 2. Configurar Variables de Entorno (Opcional)

Copia el archivo `.env.example` a `.env.local`:

```bash
cp .env.example .env.local
```

Contenido de `.env.local`:
```env
# URL de tu backend TruthGPT (FastAPI, Onyx o proxy)
NEXT_PUBLIC_TRUTHGPT_API_URL=http://localhost:8000

# Clave de autenticación
TRUTHGPT_API_KEY=tu_api_key_aqui
```

> **Nota:** Si dejas `NEXT_PUBLIC_TRUTHGPT_API_URL` en blanco, el frontend funcionará automáticamente con el motor de simulación formal integrado.

### 3. Iniciar el Servidor de Desarrollo

```bash
npm run dev
# o
yarn dev
```

Abre [http://localhost:3000](http://localhost:3000) en tu navegador para ver la aplicación en vivo.

---

## 🐳 Despliegue con Docker

Para correr el frontend en cualquier servidor o VPS con Docker:

```bash
docker compose up -d --build
```

La aplicación estará disponible inmediatamente en `http://localhost:3000`.

---

## 🔌 Contrato de API para Conectar tu Propio Backend

Para conectar tu propio backend en Python / FastAPI a este frontend, asegúrate de implementar el siguiente endpoint:

### `POST /chat`

**Payload de Petición:**
```json
{
  "prompt": "Demuestra la invariante con Z3 SMT",
  "model": "truthgpt-v2-frontier",
  "enable_swarm": true,
  "enable_formal_verification": true
}
```

**Respuesta Esperada:**
```json
{
  "success": true,
  "response": {
    "response_id": "resp_98214a",
    "content": "Respuesta en formato Markdown...",
    "model_name": "truthgpt-v2-frontier",
    "execution_time_ms": 145,
    "tokens_consumed": 420,
    "agent_steps": [
      {
        "id": "step_1",
        "type": "vector_search",
        "title": "Redis Vector Search (RAG)",
        "description": "Búsqueda en índices HNSW",
        "status": "completed",
        "duration_ms": 110
      }
    ],
    "proof_certificate": {
      "certificate_id": "cert_tgpt_a5ebea35",
      "status": "PROVED_SAT",
      "solver_engine": "Z3 SMT v4.12",
      "confidence_score": 0.9998,
      "proof_tree_hash": "sha256_hash...",
      "mathematical_invariants": ["∀x: x >= 0 -> sqrt(x) >= 0"]
    }
  }
}
```

---

## 📄 Licencia

Este proyecto está bajo la licencia MIT. Eres libre de bifurcarlo (fork), modificarlo e integrarlo en tus aplicaciones comerciales o de investigación.
