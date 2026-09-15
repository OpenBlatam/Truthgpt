"""
📊 TruthGPT Cloud - Executive Analytics & Monetization Web Dashboard
Serves a high-end, responsive dark-mode dashboard with real-time churn tracking,
active user analytics, live Stripe payment link generation, and on-demand charging.
"""

def get_dashboard_html() -> str:
    return """<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>TruthGPT Cloud — Centro de Control, Cobros y Analítica de Churn</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Outfit:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg-dark: #070a12;
      --bg-card: rgba(17, 24, 39, 0.75);
      --bg-card-hover: rgba(31, 41, 55, 0.85);
      --border-card: rgba(255, 255, 255, 0.08);
      --border-accent: rgba(99, 102, 241, 0.35);
      --text-main: #f3f4f6;
      --text-muted: #9ca3af;
      --accent-indigo: #6366f1;
      --accent-cyan: #06b6d4;
      --accent-emerald: #10b981;
      --accent-rose: #f43f5e;
      --accent-amber: #f59e0b;
      --accent-purple: #a855f7;
      --glow-indigo: rgba(99, 102, 241, 0.25);
    }

    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }

    body {
      background-color: var(--bg-dark);
      background-image: 
        radial-gradient(at 0% 0%, rgba(99, 102, 241, 0.12) 0px, transparent 50%),
        radial-gradient(at 100% 0%, rgba(6, 182, 212, 0.10) 0px, transparent 50%),
        radial-gradient(at 50% 100%, rgba(168, 85, 247, 0.08) 0px, transparent 50%);
      color: var(--text-main);
      font-family: 'Inter', -apple-system, sans-serif;
      min-height: 100vh;
      padding-bottom: 4rem;
    }

    h1, h2, h3, h4, .brand-text {
      font-family: 'Outfit', sans-serif;
    }

    /* Container */
    .container {
      max-width: 1400px;
      margin: 0 auto;
      padding: 1.5rem 2rem;
    }

    /* Header */
    header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-bottom: 1.5rem;
      border-bottom: 1px solid var(--border-card);
      margin-bottom: 2rem;
      flex-wrap: wrap;
      gap: 1rem;
    }

    .brand-section {
      display: flex;
      align-items: center;
      gap: 1rem;
    }

    .logo-badge {
      width: 46px;
      height: 46px;
      border-radius: 12px;
      background: linear-gradient(135deg, var(--accent-indigo), var(--accent-cyan));
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 1.5rem;
      box-shadow: 0 0 20px var(--glow-indigo);
    }

    .brand-title {
      font-size: 1.5rem;
      font-weight: 700;
      background: linear-gradient(to right, #ffffff, #c7d2fe, #67e8f9);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }

    .brand-subtitle {
      font-size: 0.85rem;
      color: var(--text-muted);
    }

    .header-actions {
      display: flex;
      align-items: center;
      gap: 0.75rem;
    }

    .status-pill {
      display: inline-flex;
      align-items: center;
      gap: 0.5rem;
      padding: 0.4rem 0.85rem;
      border-radius: 9999px;
      font-size: 0.8rem;
      font-weight: 500;
      background: rgba(16, 185, 129, 0.12);
      border: 1px solid rgba(16, 185, 129, 0.3);
      color: #34d399;
    }

    .pulse-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background-color: #10b981;
      box-shadow: 0 0 10px #10b981;
      animation: pulse 2s infinite;
    }

    @keyframes pulse {
      0% { transform: scale(0.95); opacity: 0.8; }
      50% { transform: scale(1.3); opacity: 1; }
      100% { transform: scale(0.95); opacity: 0.8; }
    }

    .btn {
      display: inline-flex;
      align-items: center;
      gap: 0.5rem;
      padding: 0.6rem 1.1rem;
      border-radius: 10px;
      font-size: 0.875rem;
      font-weight: 600;
      cursor: pointer;
      border: none;
      transition: all 0.2s ease;
      text-decoration: none;
    }

    .btn-primary {
      background: linear-gradient(135deg, var(--accent-indigo), #4f46e5);
      color: white;
      box-shadow: 0 4px 14px rgba(79, 70, 229, 0.4);
    }

    .btn-primary:hover {
      background: linear-gradient(135deg, #4f46e5, #4338ca);
      transform: translateY(-1px);
    }

    .btn-emerald {
      background: linear-gradient(135deg, var(--accent-emerald), #059669);
      color: white;
      box-shadow: 0 4px 14px rgba(16, 185, 129, 0.35);
    }

    .btn-emerald:hover {
      background: linear-gradient(135deg, #059669, #047857);
      transform: translateY(-1px);
    }

    .btn-outline {
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid var(--border-card);
      color: var(--text-main);
    }

    .btn-outline:hover {
      background: rgba(255, 255, 255, 0.1);
      border-color: rgba(255, 255, 255, 0.2);
    }

    .btn-sm {
      padding: 0.35rem 0.75rem;
      font-size: 0.775rem;
      border-radius: 8px;
    }

    /* KPI Grid */
    .kpi-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
      gap: 1.25rem;
      margin-bottom: 2rem;
    }

    .kpi-card {
      background: var(--bg-card);
      backdrop-filter: blur(12px);
      border: 1px solid var(--border-card);
      border-radius: 16px;
      padding: 1.35rem;
      position: relative;
      overflow: hidden;
      transition: transform 0.2s ease, border-color 0.2s ease;
    }

    .kpi-card:hover {
      transform: translateY(-2px);
      border-color: var(--border-accent);
    }

    .kpi-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 0.75rem;
    }

    .kpi-title {
      font-size: 0.825rem;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: var(--text-muted);
      font-weight: 600;
    }

    .kpi-icon {
      width: 36px;
      height: 36px;
      border-radius: 10px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 1.2rem;
    }

    .kpi-value {
      font-size: 1.9rem;
      font-weight: 700;
      letter-spacing: -0.02em;
      margin-bottom: 0.35rem;
    }

    .kpi-subtext {
      font-size: 0.8rem;
      color: var(--text-muted);
      display: flex;
      align-items: center;
      gap: 0.35rem;
    }

    /* Stripe status alert banner */
    .stripe-banner {
      background: linear-gradient(90deg, rgba(99, 102, 241, 0.15), rgba(168, 85, 247, 0.15));
      border: 1px solid rgba(99, 102, 241, 0.35);
      border-radius: 14px;
      padding: 1rem 1.5rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 2rem;
      flex-wrap: wrap;
      gap: 1rem;
    }

    .stripe-banner-content {
      display: flex;
      align-items: center;
      gap: 1rem;
    }

    .stripe-logo-icon {
      font-size: 1.8rem;
    }

    /* Tabs Navigation */
    .tabs-nav {
      display: flex;
      gap: 0.5rem;
      border-bottom: 1px solid var(--border-card);
      margin-bottom: 1.5rem;
      overflow-x: auto;
      padding-bottom: 0.25rem;
    }

    .tab-btn {
      background: transparent;
      border: none;
      color: var(--text-muted);
      padding: 0.75rem 1.25rem;
      font-size: 0.95rem;
      font-weight: 600;
      border-radius: 10px 10px 0 0;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 0.5rem;
      border-bottom: 2px solid transparent;
      transition: all 0.2s ease;
      white-space: nowrap;
    }

    .tab-btn:hover {
      color: var(--text-main);
      background: rgba(255, 255, 255, 0.03);
    }

    .tab-btn.active {
      color: #818cf8;
      border-bottom-color: #818cf8;
      background: rgba(99, 102, 241, 0.08);
    }

    .badge-count {
      padding: 0.15rem 0.5rem;
      border-radius: 9999px;
      font-size: 0.75rem;
      font-weight: 700;
    }

    /* Tab Content Views */
    .tab-content {
      display: none;
    }

    .tab-content.active {
      display: block;
      animation: fadeIn 0.25s ease;
    }

    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(6px); }
      to { opacity: 1; transform: translateY(0); }
    }

    /* Table styles */
    .table-container {
      background: var(--bg-card);
      backdrop-filter: blur(12px);
      border: 1px solid var(--border-card);
      border-radius: 16px;
      overflow: hidden;
      margin-bottom: 2rem;
    }

    .table-header-box {
      padding: 1.25rem 1.5rem;
      border-bottom: 1px solid var(--border-card);
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 1rem;
    }

    .table-title {
      font-size: 1.1rem;
      font-weight: 700;
    }

    table {
      width: 100%;
      border-collapse: collapse;
      text-align: left;
    }

    th {
      padding: 0.9rem 1.5rem;
      font-size: 0.775rem;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: var(--text-muted);
      border-bottom: 1px solid var(--border-card);
      background: rgba(0, 0, 0, 0.2);
    }

    td {
      padding: 1rem 1.5rem;
      font-size: 0.875rem;
      border-bottom: 1px solid rgba(255, 255, 255, 0.04);
      vertical-align: middle;
    }

    tr:hover td {
      background: rgba(255, 255, 255, 0.02);
    }

    /* Badges */
    .tier-tag {
      padding: 0.25rem 0.65rem;
      border-radius: 6px;
      font-size: 0.75rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.03em;
      display: inline-block;
    }

    .tier-pro { background: rgba(99, 102, 241, 0.18); color: #a5b4fc; border: 1px solid rgba(99, 102, 241, 0.4); }
    .tier-ultra { background: rgba(245, 158, 11, 0.18); color: #fcd34d; border: 1px solid rgba(245, 158, 11, 0.4); }
    .tier-enterprise { background: rgba(168, 85, 247, 0.18); color: #d8b4fe; border: 1px solid rgba(168, 85, 247, 0.4); }
    .tier-free { background: rgba(156, 163, 175, 0.15); color: #d1d5db; border: 1px solid rgba(156, 163, 175, 0.3); }

    .status-badge {
      display: inline-flex;
      align-items: center;
      gap: 0.35rem;
      padding: 0.25rem 0.65rem;
      border-radius: 9999px;
      font-size: 0.75rem;
      font-weight: 600;
    }

    .status-active { background: rgba(16, 185, 129, 0.15); color: #34d399; }
    .status-churned { background: rgba(244, 63, 94, 0.15); color: #fb7185; }
    .status-at_risk { background: rgba(245, 158, 11, 0.15); color: #fbbf24; }

    /* Progress bar */
    .progress-bar-bg {
      width: 120px;
      height: 6px;
      background: rgba(255, 255, 255, 0.1);
      border-radius: 9999px;
      overflow: hidden;
      margin-top: 0.3rem;
    }

    .progress-bar-fill {
      height: 100%;
      border-radius: 9999px;
      background: linear-gradient(90deg, var(--accent-indigo), var(--accent-cyan));
    }

    /* Modals & Forms */
    .grid-form {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 1.5rem;
      padding: 1.5rem;
    }

    .form-group {
      display: flex;
      flex-direction: column;
      gap: 0.4rem;
    }

    .form-label {
      font-size: 0.825rem;
      font-weight: 600;
      color: var(--text-muted);
    }

    .form-input, .form-select {
      background: rgba(0, 0, 0, 0.4);
      border: 1px solid var(--border-card);
      color: var(--text-main);
      padding: 0.65rem 0.85rem;
      border-radius: 8px;
      font-size: 0.9rem;
      outline: none;
      transition: border-color 0.2s;
    }

    .form-input:focus, .form-select:focus {
      border-color: var(--accent-indigo);
    }

    /* Event stream list */
    .event-item {
      padding: 0.9rem 1.25rem;
      border-bottom: 1px solid rgba(255, 255, 255, 0.04);
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 1rem;
    }

    .event-item:last-child {
      border-bottom: none;
    }

    .event-left {
      display: flex;
      align-items: center;
      gap: 0.75rem;
    }

    .event-icon {
      width: 32px;
      height: 32px;
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 1rem;
    }

    .toast-box {
      position: fixed;
      bottom: 2rem;
      right: 2rem;
      z-index: 1000;
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
    }

    .toast {
      background: #1e1b4b;
      border: 1px solid #6366f1;
      color: #e0e7ff;
      padding: 0.85rem 1.25rem;
      border-radius: 10px;
      box-shadow: 0 10px 25px rgba(0,0,0,0.5);
      font-size: 0.875rem;
      display: flex;
      align-items: center;
      gap: 0.75rem;
      animation: slideIn 0.3s ease;
    }

    @keyframes slideIn {
      from { transform: translateX(100%); opacity: 0; }
      to { transform: translateX(0); opacity: 1; }
    }
  </style>
</head>
<body>

  <div class="container">
    <!-- Header -->
    <header>
      <div class="brand-section">
        <div class="logo-badge">🌌</div>
        <div>
          <h1 class="brand-title">TruthGPT Cloud</h1>
          <p class="brand-subtitle">Panel Ejecutivo de Monetización, Retención & Detección de Churn</p>
        </div>
      </div>

      <div class="header-actions">
        <div class="status-pill">
          <span class="pulse-dot"></span>
          <span>Sistema en Vivo</span>
        </div>
        <button class="btn btn-outline btn-sm" onclick="fetchDashboardData()">
          🔄 Actualizar
        </button>
        <button class="btn btn-outline btn-sm" onclick="openStripeConfigModal()">
          ⚙️ Claves Stripe
        </button>
        <button class="btn btn-emerald" onclick="openTestPaymentModal()">
          ⚡ Probar Cobro / Pasarela
        </button>
        <button class="btn btn-primary" onclick="switchTab('tab-billing')">
          💳 Panel de Cobros
        </button>
      </div>
    </header>

    <!-- Stripe Status Banner -->
    <div class="stripe-banner" id="stripeBanner">
      <div class="stripe-banner-content">
        <div class="stripe-logo-icon">⚡</div>
        <div>
          <h4 style="font-weight: 700; color: #e0e7ff;" id="stripeStatusTitle">Pasarela de Pagos Stripe</h4>
          <p style="font-size: 0.85rem; color: #c7d2fe;" id="stripeStatusText">
            Cargando estado de la pasarela...
          </p>
        </div>
      </div>
      <div id="stripeBannerAction" style="display: flex; gap: 0.5rem; flex-wrap: wrap;">
        <button class="btn btn-outline btn-sm" onclick="openStripeConfigModal()">
          ⚙️ Configurar Stripe Live
        </button>
        <button class="btn btn-primary btn-sm" onclick="switchTab('tab-billing')">
          Panel de Cobros
        </button>
      </div>
    </div>

    <!-- KPI Metric Cards -->
    <div class="kpi-grid">
      <!-- MRR -->
      <div class="kpi-card" style="border-top: 3px solid var(--accent-emerald);">
        <div class="kpi-header">
          <span class="kpi-title">Ingresos Recurrentes (MRR)</span>
          <div class="kpi-icon" style="background: rgba(16, 185, 129, 0.15); color: #34d399;">💰</div>
        </div>
        <div class="kpi-value" id="kpiMrr" style="color: #34d399;">$0.00</div>
        <div class="kpi-subtext">
          <span>ARR proyectado: </span>
          <strong id="kpiArr" style="color: #f3f4f6;">$0.00</strong>
        </div>
      </div>

      <!-- Total Revenue -->
      <div class="kpi-card" style="border-top: 3px solid var(--accent-indigo);">
        <div class="kpi-header">
          <span class="kpi-title">Ingresos Totales Cobrados</span>
          <div class="kpi-icon" style="background: rgba(99, 102, 241, 0.15); color: #818cf8;">💳</div>
        </div>
        <div class="kpi-value" id="kpiTotalRevenue" style="color: #818cf8;">$0.00</div>
        <div class="kpi-subtext">
          <span id="kpiInvoicesCount">0</span> facturas liquidadas
        </div>
      </div>

      <!-- Active Users (Quién lo usa) -->
      <div class="kpi-card" style="border-top: 3px solid var(--accent-cyan);">
        <div class="kpi-header">
          <span class="kpi-title">Quién lo Usa (Activos)</span>
          <div class="kpi-icon" style="background: rgba(6, 182, 212, 0.15); color: #22d3ee;">🟢</div>
        </div>
        <div class="kpi-value" id="kpiActiveUsers" style="color: #22d3ee;">0</div>
        <div class="kpi-subtext">
          <span>DAU: <strong id="kpiDau">0</strong></span> • 
          <span>WAU: <strong id="kpiWau">0</strong></span> • 
          <span>MAU: <strong id="kpiMau">0</strong></span>
        </div>
      </div>

      <!-- Churned Users (Quién lo deja de usar) -->
      <div class="kpi-card" style="border-top: 3px solid var(--accent-rose);">
        <div class="kpi-header">
          <span class="kpi-title">Quién lo Dejó de Usar (Churn)</span>
          <div class="kpi-icon" style="background: rgba(244, 63, 94, 0.15); color: #fb7185;">🔴</div>
        </div>
        <div class="kpi-value" id="kpiChurnUsers" style="color: #fb7185;">0</div>
        <div class="kpi-subtext">
          <span>Tasa de Churn: <strong id="kpiChurnRate" style="color: #fb7185;">0%</strong></span> • 
          <span>Retención: <strong id="kpiRetentionRate" style="color: #34d399;">100%</strong></span>
        </div>
      </div>

      <!-- At Risk Users (Inactivos) -->
      <div class="kpi-card" style="border-top: 3px solid var(--accent-amber);">
        <div class="kpi-header">
          <span class="kpi-title">En Riesgo (Inactivos > 7d)</span>
          <div class="kpi-icon" style="background: rgba(245, 158, 11, 0.15); color: #fbbf24;">⚠️</div>
        </div>
        <div class="kpi-value" id="kpiAtRiskUsers" style="color: #fbbf24;">0</div>
        <div class="kpi-subtext">
          <span>Clientes sin actividad reciente</span>
        </div>
      </div>
    </div>

    <!-- Tabs Navigation -->
    <div class="tabs-nav">
      <button class="tab-btn active" onclick="switchTab('tab-active')">
        🟢 Quién lo Usa (Activos)
        <span class="badge-count" id="badgeActiveCount" style="background: rgba(6, 182, 212, 0.2); color: #22d3ee;">0</span>
      </button>
      <button class="tab-btn" onclick="switchTab('tab-churn')">
        🔴 Quién lo Deja de Usar (Bajas / Churn)
        <span class="badge-count" id="badgeChurnCount" style="background: rgba(244, 63, 94, 0.2); color: #fb7185;">0</span>
      </button>
      <button class="tab-btn" onclick="switchTab('tab-at-risk')">
        ⚠️ Usuarios en Riesgo
        <span class="badge-count" id="badgeAtRiskCount" style="background: rgba(245, 158, 11, 0.2); color: #fbbf24;">0</span>
      </button>
      <button class="tab-btn" onclick="switchTab('tab-billing')">
        ⚡ Cobrar en Vivo (Stripe & Enlaces)
      </button>
      <button class="tab-btn" onclick="switchTab('tab-invoices')">
        🧾 Facturas & Recibos
      </button>
      <button class="tab-btn" onclick="switchTab('tab-activity')">
        📡 Feed de Actividad en Vivo
      </button>
    </div>

    <!-- TAB 1: Quién lo Usa (Activos) -->
    <div id="tab-active" class="tab-content active">
      <div class="table-container">
        <div class="table-header-box">
          <div>
            <h3 class="table-title">Clientes Activos en TruthGPT Cloud</h3>
            <p style="font-size: 0.85rem; color: var(--text-muted);">Monitoreo de consumo de tokens, peticiones y última actividad en tiempo real.</p>
          </div>
          <button class="btn btn-emerald btn-sm" onclick="switchTab('tab-billing')">
            + Cobrar a un Cliente
          </button>
        </div>
        <table>
          <thead>
            <tr>
              <th>Cliente</th>
              <th>Plan / Tier</th>
              <th>Última Actividad</th>
              <th>Tokens Hoy</th>
              <th>Peticiones Hoy</th>
              <th>Total Facturado</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody id="activeUsersTableBody">
            <tr><td colspan="7" style="text-align: center; color: var(--text-muted);">Cargando usuarios activos...</td></tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- TAB 2: Quién lo Deja de Usar (Churn) -->
    <div id="tab-churn" class="tab-content">
      <div class="table-container">
        <div class="table-header-box">
          <div>
            <h3 class="table-title" style="color: #fb7185;">Bajas y Cancelaciones de Suscripción (Churn)</h3>
            <p style="font-size: 0.85rem; color: var(--text-muted);">Clientes que cancelaron su servicio, motivo de salida y fecha de baja.</p>
          </div>
        </div>
        <table>
          <thead>
            <tr>
              <th>Cliente</th>
              <th>Plan Previo</th>
              <th>Fecha de Baja</th>
              <th>Motivo de Salida</th>
              <th>Histórico Gastado</th>
              <th>Acciones de Retención</th>
            </tr>
          </thead>
          <tbody id="churnUsersTableBody">
            <tr><td colspan="6" style="text-align: center; color: var(--text-muted);">No hay bajas registradas.</td></tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- TAB 3: Usuarios en Riesgo -->
    <div id="tab-at-risk" class="tab-content">
      <div class="table-container">
        <div class="table-header-box">
          <div>
            <h3 class="table-title" style="color: #fbbf24;">Usuarios en Riesgo de Deserción</h3>
            <p style="font-size: 0.85rem; color: var(--text-muted);">Clientes con suscripción de pago activa pero sin peticiones en los últimos 7 días.</p>
          </div>
        </div>
        <table>
          <thead>
            <tr>
              <th>Cliente</th>
              <th>Plan</th>
              <th>Días Inactivo</th>
              <th>Total Invertido</th>
              <th>Estado</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody id="atRiskUsersTableBody">
            <tr><td colspan="6" style="text-align: center; color: var(--text-muted);">No hay usuarios en riesgo actualmente.</td></tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- TAB 4: Cobrar en Vivo (Stripe & Enlaces) -->
    <div id="tab-billing" class="tab-content">
      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(380px, 1fr)); gap: 1.5rem;">
        
        <!-- Generador de Enlace de Pago / Stripe Checkout -->
        <div class="table-container">
          <div class="table-header-box" style="border-bottom: 1px solid var(--border-card);">
            <h3 class="table-title">⚡ Generador de Enlaces de Cobro</h3>
          </div>
          <div class="grid-form">
            <div class="form-group">
              <label class="form-label">Seleccionar Usuario a Cobrar</label>
              <select id="chargeUserSelect" class="form-select">
                <option value="usr_default_demo">TruthGPT Explorer (demo@truthgpt.ai)</option>
              </select>
            </div>

            <div class="form-group">
              <label class="form-label">Concepto / Plan</label>
              <select id="chargeTierSelect" class="form-select" onchange="onChargeTierChange()">
                <option value="pro" data-price="19.99">TruthGPT Pro — $19.99 USD / mes</option>
                <option value="ultra" data-price="99.99">TruthGPT Ultra — $99.99 USD / mes</option>
                <option value="enterprise" data-price="499.00">TruthGPT Enterprise — $499.00 USD / mes</option>
                <option value="topup_pack_starter" data-price="5.00">Top-Up 500k Tokens — $5.00 USD</option>
                <option value="topup_pack_pro" data-price="19.00">Top-Up 2.5M Tokens — $19.00 USD</option>
                <option value="custom" data-price="">Monto Personalizado (USD)</option>
              </select>
            </div>

            <div class="form-group" id="customAmountGroup" style="display: none;">
              <label class="form-label">Monto Personalizado (USD)</label>
              <input type="number" id="customAmountInput" class="form-input" placeholder="Ej: 50.00" min="1" step="0.5">
            </div>

            <div class="form-group">
              <label class="form-label">Ciclo de Facturación</label>
              <select id="chargeCycleSelect" class="form-select">
                <option value="monthly">Mensual</option>
                <option value="yearly">Anual (Descuento)</option>
                <option value="one_time">Pago Único</option>
              </select>
            </div>

            <div style="grid-column: 1 / -1; display: flex; gap: 1rem; flex-wrap: wrap;">
              <button class="btn btn-emerald" onclick="createCheckoutSessionAction()">
                💳 Generar Checkout Stripe
              </button>
              <button class="btn btn-primary" onclick="createPaymentLinkAction()">
                🔗 Crear Enlace Directo
              </button>
              <button class="btn btn-outline" onclick="chargeUserDirectAction()">
                ⚡ Cobrar de Inmediato
              </button>
            </div>
          </div>

          <!-- Resultado del Enlace -->
          <div id="paymentLinkResult" style="display: none; padding: 1.5rem; background: rgba(0,0,0,0.3); border-top: 1px solid var(--border-card);">
            <p style="font-size: 0.85rem; font-weight: 600; color: #a7f3d0; margin-bottom: 0.5rem;">
              ✅ Enlace de pago generado con éxito:
            </p>
            <div style="display: flex; gap: 0.5rem; align-items: center;">
              <input type="text" id="generatedLinkInput" readonly class="form-input" style="flex: 1; font-family: monospace; font-size: 0.85rem;">
              <button class="btn btn-sm btn-primary" onclick="copyPaymentLink()">
                📋 Copiar
              </button>
              <button class="btn btn-sm btn-outline" style="color: #34d399; border-color: rgba(16,185,129,0.4);" onclick="testGeneratedPaymentLink()">
                ⚡ Probar Cobro
              </button>
              <a id="openCheckoutBtn" href="#" target="_blank" class="btn btn-sm btn-emerald">
                Abrir ↗
              </a>
            </div>
          </div>
        </div>

        <!-- Panel de Configuración Stripe -->
        <div class="table-container">
          <div class="table-header-box">
            <h3 class="table-title">⚙️ Configuración de Stripe</h3>
          </div>
          <div style="padding: 1.5rem; display: flex; flex-direction: column; gap: 1rem;">
            <div style="background: rgba(0,0,0,0.3); padding: 1rem; border-radius: 10px; border: 1px solid var(--border-card);">
              <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                <span style="font-size: 0.85rem; color: var(--text-muted);">Estado de Conexión:</span>
                <span id="stripeConfigModeBadge" class="status-badge status-active">Cargando...</span>
              </div>
              <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                <span style="font-size: 0.85rem; color: var(--text-muted);">Clave Secreta (sk_...):</span>
                <span id="stripeHasSecret" style="font-size: 0.85rem; font-weight: 600;">No</span>
              </div>
              <div style="display: flex; justify-content: space-between;">
                <span style="font-size: 0.85rem; color: var(--text-muted);">Webhook Secreto (whsec_...):</span>
                <span id="stripeHasWebhook" style="font-size: 0.85rem; font-weight: 600;">No</span>
              </div>
            </div>

            <div style="font-size: 0.85rem; color: var(--text-muted); line-height: 1.5;">
              <strong style="color: var(--text-main);">Instrucciones para Cobros Reales:</strong><br>
              Para recibir dinero directamente en tu cuenta bancaria de Stripe, asigna la variable en tu entorno o en PowerShell:
              <pre style="background: #000; padding: 0.75rem; border-radius: 8px; margin-top: 0.5rem; font-size: 0.775rem; color: #a5b4fc; overflow-x: auto;">$env:STRIPE_SECRET_KEY="sk_live_tu_clave_aqui"
$env:STRIPE_WEBHOOK_SECRET="whsec_tu_webhook_aqui"</pre>
            </div>

            <div style="display: flex; gap: 0.5rem;">
              <button class="btn btn-outline btn-sm" onclick="openCustomerPortalAction()">
                🏛️ Abrir Portal de Clientes
              </button>
            </div>
          </div>
        </div>

      </div>
    </div>

    <!-- TAB 5: Facturas -->
    <div id="tab-invoices" class="tab-content">
      <div class="table-container">
        <div class="table-header-box">
          <h3 class="table-title">Historial de Facturación y Recibos</h3>
        </div>
        <table>
          <thead>
            <tr>
              <th>ID Factura</th>
              <th>Cliente</th>
              <th>Monto (USD)</th>
              <th>Plan / Concepto</th>
              <th>Método</th>
              <th>Fecha</th>
              <th>Estado</th>
            </tr>
          </thead>
          <tbody id="invoicesTableBody">
            <tr><td colspan="7" style="text-align: center; color: var(--text-muted);">Cargando facturas...</td></tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- TAB 6: Feed de Actividad en Vivo -->
    <div id="tab-activity" class="tab-content">
      <div class="table-container">
        <div class="table-header-box">
          <h3 class="table-title">📡 Registro de Eventos en Tiempo Real</h3>
        </div>
        <div id="eventStreamContainer">
          <div style="padding: 1.5rem; text-align: center; color: var(--text-muted);">Cargando flujo de eventos...</div>
        </div>
      </div>
    </div>

  <!-- Modal de Checkout / Pago Sandbox -->
  <div id="paymentModal" style="display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.82); z-index: 9999; align-items: center; justify-content: center; backdrop-filter: blur(8px);">
    <div style="background: #111827; border: 1px solid rgba(99, 102, 241, 0.45); border-radius: 16px; padding: 2rem; max-width: 480px; width: 90%; box-shadow: 0 25px 50px -12px rgba(0,0,0,0.8); color: #f3f4f6;">
      <div style="display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1.25rem;">
        <div style="width: 46px; height: 46px; border-radius: 12px; background: linear-gradient(135deg, #6366f1, #06b6d4); display: flex; align-items: center; justify-content: center; font-size: 1.5rem; box-shadow: 0 0 15px rgba(99,102,241,0.4);">💳</div>
        <div>
          <h3 style="font-weight: 700; font-size: 1.25rem;">Confirmación de Pago</h3>
          <p style="font-size: 0.8rem; color: #9ca3af;">TruthGPT Cloud Payment Gateway</p>
        </div>
      </div>
      <div style="background: rgba(0,0,0,0.4); border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 1.25rem; margin-bottom: 1.25rem; display: flex; flex-direction: column; gap: 0.75rem;">
        <div style="display: flex; justify-content: space-between;">
          <span style="color: #9ca3af; font-size: 0.85rem;">Concepto:</span>
          <span id="modalConcept" style="font-weight: 600; font-size: 0.85rem;">Suscripción TruthGPT</span>
        </div>
        <div style="display: flex; justify-content: space-between;">
          <span style="color: #9ca3af; font-size: 0.85rem;">Cliente / ID:</span>
          <span id="modalUserId" style="font-family: monospace; font-size: 0.85rem; color: #a5b4fc;">usr_default_demo</span>
        </div>
        <div style="display: flex; justify-content: space-between;">
          <span style="color: #9ca3af; font-size: 0.85rem;">Pasarela:</span>
          <span id="modalGateway" class="status-badge status-active" style="font-size: 0.75rem;">⚡ Instant Sandbox / Stripe</span>
        </div>
        <div style="height: 1px; background: rgba(255,255,255,0.08); margin: 0.25rem 0;"></div>
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <span style="font-weight: 700;">Total a Cobrar:</span>
          <span id="modalAmount" style="font-size: 1.5rem; font-weight: 800; color: #34d399;">$19.99 USD</span>
        </div>
      </div>

      <!-- Selector de Método de Pago -->
      <div style="margin-bottom: 1.25rem;">
        <label style="font-size: 0.75rem; color: #9ca3af; margin-bottom: 0.35rem; display: block; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;">Método de Cobro</label>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem;">
          <div id="modalPayMethodStripe" onclick="selectModalPaymentMethod('stripe_card')" style="border: 1px solid #6366f1; background: rgba(99,102,241,0.18); border-radius: 8px; padding: 0.55rem 0.75rem; cursor: pointer; text-align: center; font-size: 0.825rem; font-weight: 600; color: #e0e7ff; transition: all 0.2s;">
            💳 Tarjeta (Stripe)
          </div>
          <div id="modalPayMethodCrypto" onclick="selectModalPaymentMethod('crypto_usdc')" style="border: 1px solid rgba(255,255,255,0.1); background: rgba(255,255,255,0.02); border-radius: 8px; padding: 0.55rem 0.75rem; cursor: pointer; text-align: center; font-size: 0.825rem; font-weight: 500; color: #9ca3af; transition: all 0.2s;">
            🪙 Crypto USDC
          </div>
        </div>
      </div>

      <!-- Tarjeta / Instrumento -->
      <div id="modalCardFields" style="background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.06); border-radius: 10px; padding: 0.85rem; margin-bottom: 1.5rem;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.35rem;">
          <span style="font-size: 0.75rem; color: #9ca3af;">Instrumento de Pago:</span>
          <span style="color: #34d399; font-size: 0.75rem; font-weight: 600;">● Conexión Segura</span>
        </div>
        <div style="font-family: monospace; font-size: 0.95rem; font-weight: 600; color: #e0e7ff; letter-spacing: 0.05em; margin-bottom: 0.35rem;">
          4242 •••• •••• 4242
        </div>
        <div style="display: flex; justify-content: space-between; font-size: 0.75rem; color: #9ca3af;">
          <span>Exp: 12/28</span>
          <span>CVC: 789</span>
          <span>Stripe Live / Sandbox</span>
        </div>
      </div>

      <div style="display: flex; gap: 0.75rem;">
        <button class="btn btn-outline" style="flex: 1;" onclick="closePaymentModal()">Cancelar</button>
        <button id="modalConfirmPayBtn" class="btn btn-emerald" style="flex: 2;" onclick="executeModalPayment()">
          💰 Confirmar Pago
        </button>
      </div>
    </div>
  </div>

  <div class="toast-box" id="toastContainer"></div>

  <script>
    let dashboardState = null;

    async function fetchDashboardData() {
      try {
        const res = await fetch('/api/v1/cloud/dashboard/overview');
        if (!res.ok) throw new Error('Error de conexión con el servidor');
        const data = await res.json();
        dashboardState = data;
        renderDashboard(data);
      } catch (err) {
        showToast('⚠️ No se pudo actualizar el dashboard: ' + err.message);
      }
    }

    function renderDashboard(data) {
      if (!data || !data.kpis) return;
      const k = data.kpis;

      // KPIs
      document.getElementById('kpiMrr').textContent = '$' + k.mrr_usd.toFixed(2);
      document.getElementById('kpiArr').textContent = '$' + k.arr_usd.toFixed(2);
      document.getElementById('kpiTotalRevenue').textContent = '$' + k.total_revenue_usd.toFixed(2);
      document.getElementById('kpiInvoicesCount').textContent = k.total_invoices_count;
      document.getElementById('kpiActiveUsers').textContent = k.active_users_count;
      document.getElementById('kpiDau').textContent = k.dau;
      document.getElementById('kpiWau').textContent = k.wau;
      document.getElementById('kpiMau').textContent = k.mau;
      document.getElementById('kpiChurnUsers').textContent = k.churned_users_count;
      document.getElementById('kpiChurnRate').textContent = k.churn_rate_pct + '%';
      document.getElementById('kpiRetentionRate').textContent = k.retention_rate_pct + '%';
      document.getElementById('kpiAtRiskUsers').textContent = k.at_risk_users_count;

      // Badges
      document.getElementById('badgeActiveCount').textContent = data.active_users.length;
      document.getElementById('badgeChurnCount').textContent = data.churned_users.length;
      document.getElementById('badgeAtRiskCount').textContent = data.at_risk_users.length;

      // Stripe banner
      const g = data.gateway_status && data.gateway_status.stripe ? data.gateway_status.stripe : {};
      const stripeTitle = document.getElementById('stripeStatusTitle');
      const stripeText = document.getElementById('stripeStatusText');
      const stripeBadge = document.getElementById('stripeConfigModeBadge');
      const stripeHasSec = document.getElementById('stripeHasSecret');
      const stripeHasWh = document.getElementById('stripeHasWebhook');

      if (g.mode === 'live') {
        stripeTitle.textContent = '✅ Pasarela Stripe Live Activa';
        stripeText.textContent = 'Cobros reales en vivo conectados a tu cuenta bancaria.';
        stripeBadge.textContent = 'LIVE PROD';
        stripeBadge.className = 'status-badge status-active';
      } else if (g.mode === 'test') {
        stripeTitle.textContent = '🧪 Stripe Modo Test Conectado';
        stripeText.textContent = 'Listo para procesar tarjetas de prueba de Stripe.';
        stripeBadge.textContent = 'TEST MODE';
        stripeBadge.className = 'status-badge status-at_risk';
      } else {
        stripeTitle.textContent = '⚡ Modo Sandbox Activo (Listo para Cobrar)';
        stripeText.textContent = 'Simulación instantánea activa. Añade STRIPE_SECRET_KEY para cobros con tarjeta real.';
        stripeBadge.textContent = 'SANDBOX';
        stripeBadge.className = 'status-badge status-at_risk';
      }

      stripeHasSec.textContent = g.has_secret_key ? 'Sí (Configurada)' : 'No (Modo Sandbox)';
      stripeHasWh.textContent = g.has_webhook_secret ? 'Sí (Configurado)' : 'No';

      // Render Active Users Table
      renderActiveUsersTable(data.active_users);

      // Render Churn Users Table
      renderChurnUsersTable(data.churned_users);

      // Render At Risk Users Table
      renderAtRiskUsersTable(data.at_risk_users);

      // Render Invoices Table
      renderInvoicesTable(data.recent_invoices);

      // Render Event Stream
      renderEventStream(data.recent_events);

      // Update User Select options
      populateUserSelect(data.active_users);
    }

    function renderActiveUsersTable(users) {
      const tbody = document.getElementById('activeUsersTableBody');
      if (!users || users.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; color: var(--text-muted);">No hay usuarios activos.</td></tr>';
        return;
      }

      tbody.innerHTML = users.map(u => {
        const timeAgo = formatTimeAgo(u.last_active_at);
        return `
          <tr>
            <td>
              <div style="display: flex; align-items: center; gap: 0.75rem;">
                <div style="width: 32px; height: 32px; border-radius: 8px; background: rgba(99,102,241,0.2); display: flex; align-items: center; justify-content: center; font-weight: 700; color: #a5b4fc;">
                  ${u.name.charAt(0)}
                </div>
                <div>
                  <div style="font-weight: 600;">${escapeHtml(u.name)}</div>
                  <div style="font-size: 0.75rem; color: var(--text-muted);">${escapeHtml(u.email)}</div>
                </div>
              </div>
            </td>
            <td>
              <span class="tier-tag tier-${u.tier}">${u.tier_name}</span>
            </td>
            <td>
              <span style="display: inline-flex; align-items: center; gap: 0.35rem;">
                <span class="pulse-dot" style="width: 6px; height: 6px;"></span>
                <span>${timeAgo}</span>
              </span>
            </td>
            <td>
              <div>${u.tokens_consumed_today.toLocaleString()} / ${u.daily_token_limit.toLocaleString()}</div>
              <div class="progress-bar-bg">
                <div class="progress-bar-fill" style="width: ${u.percent_quota_used}%"></div>
              </div>
            </td>
            <td><strong>${u.requests_today}</strong> peticiones</td>
            <td><strong style="color: #34d399;">$${u.total_billed_usd.toFixed(2)}</strong></td>
            <td>
              <div style="display: flex; gap: 0.35rem;">
                <button class="btn btn-emerald btn-sm" onclick="quickChargeUser('${u.user_id}', '${escapeHtml(u.name)}')">
                  Cobrar
                </button>
                <button class="btn btn-outline btn-sm" style="color: #fb7185;" onclick="cancelUserPrompt('${u.user_id}', '${escapeHtml(u.name)}')">
                  Dar de Baja
                </button>
              </div>
            </td>
          </tr>
        `;
      }).join('');
    }

    function renderChurnUsersTable(users) {
      const tbody = document.getElementById('churnUsersTableBody');
      if (!users || users.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: var(--text-muted); padding: 2rem;">🎉 ¡Excelente! No hay clientes dados de baja en el registro.</td></tr>';
        return;
      }

      tbody.innerHTML = users.map(u => {
        const churnDateStr = u.churn_date ? new Date(u.churn_date).toLocaleDateString() : 'Reciente';
        return `
          <tr>
            <td>
              <div style="font-weight: 600;">${escapeHtml(u.name)}</div>
              <div style="font-size: 0.75rem; color: var(--text-muted);">${escapeHtml(u.email)}</div>
            </td>
            <td>
              <span class="tier-tag tier-${u.tier}">${u.tier_name}</span>
            </td>
            <td><span class="status-badge status-churned">${churnDateStr}</span></td>
            <td><span style="color: #fca5a5;">${escapeHtml(u.churn_reason || 'Sin motivo reportado')}</span></td>
            <td>$${u.total_billed_usd.toFixed(2)}</td>
            <td>
              <button class="btn btn-emerald btn-sm" onclick="reactivateUserAction('${u.user_id}')">
                🔄 Reactivar Cliente
              </button>
            </td>
          </tr>
        `;
      }).join('');
    }

    function renderAtRiskUsersTable(users) {
      const tbody = document.getElementById('atRiskUsersTableBody');
      if (!users || users.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: var(--text-muted); padding: 2rem;">✅ Ningún cliente en riesgo de abandono.</td></tr>';
        return;
      }

      tbody.innerHTML = users.map(u => {
        return `
          <tr>
            <td>
              <div style="font-weight: 600;">${escapeHtml(u.name)}</div>
              <div style="font-size: 0.75rem; color: var(--text-muted);">${escapeHtml(u.email)}</div>
            </td>
            <td><span class="tier-tag tier-${u.tier}">${u.tier_name}</span></td>
            <td><strong style="color: #fbbf24;">${u.days_inactive} días sin uso</strong></td>
            <td>$${u.total_billed_usd.toFixed(2)}</td>
            <td><span class="status-badge status-at_risk">En Riesgo</span></td>
            <td>
              <button class="btn btn-primary btn-sm" onclick="quickChargeUser('${u.user_id}', '${escapeHtml(u.name)}')">
                Enviar Oferta / Cobro
              </button>
            </td>
          </tr>
        `;
      }).join('');
    }

    function renderInvoicesTable(invoices) {
      const tbody = document.getElementById('invoicesTableBody');
      if (!invoices || invoices.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; color: var(--text-muted);">No hay facturas registradas.</td></tr>';
        return;
      }

      tbody.innerHTML = invoices.map(inv => {
        const dateStr = inv.created_at ? new Date(inv.created_at).toLocaleDateString() : 'N/A';
        return `
          <tr>
            <td><code>${inv.invoice_id}</code></td>
            <td>${inv.user_id}</td>
            <td><strong style="color: #34d399;">$${(inv.amount_usd || 0).toFixed(2)} USD</strong></td>
            <td>${(inv.tier_id || 'Servicio').toUpperCase()} (${inv.billing_cycle || 'mensual'})</td>
            <td>${inv.payment_method || 'stripe'}</td>
            <td>${dateStr}</td>
            <td><span class="status-badge status-active">${(inv.status || 'PAID').toUpperCase()}</span></td>
          </tr>
        `;
      }).join('');
    }

    function renderEventStream(events) {
      const container = document.getElementById('eventStreamContainer');
      if (!events || events.length === 0) {
        container.innerHTML = '<div style="padding: 1.5rem; text-align: center; color: var(--text-muted);">Sin eventos recientes.</div>';
        return;
      }

      container.innerHTML = events.map(e => {
        let icon = '⚡';
        let bg = 'rgba(99, 102, 241, 0.15)';
        if (e.type === 'invoice_paid') { icon = '💰'; bg = 'rgba(16, 185, 129, 0.15)'; }
        if (e.type === 'churn') { icon = '🔴'; bg = 'rgba(244, 63, 94, 0.15)'; }

        return `
          <div class="event-item">
            <div class="event-left">
              <div class="event-icon" style="background: ${bg};">${icon}</div>
              <div>
                <div style="font-weight: 600; font-size: 0.9rem;">${escapeHtml(e.title)}</div>
                <div style="font-size: 0.775rem; color: var(--text-muted);">${escapeHtml(e.details || '')}</div>
              </div>
            </div>
            <div style="font-size: 0.75rem; color: var(--text-muted);">${formatTimeAgo(e.timestamp)}</div>
          </div>
        `;
      }).join('');
    }

    function populateUserSelect(users) {
      const sel = document.getElementById('chargeUserSelect');
      if (!users || users.length === 0) return;
      sel.innerHTML = users.map(u => `<option value="${u.user_id}">${escapeHtml(u.name)} (${escapeHtml(u.email)}) - Plan ${u.tier.toUpperCase()}</option>`).join('');
    }

    function switchTab(tabId) {
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

      const target = document.getElementById(tabId);
      if (target) target.classList.add('active');

      const btn = Array.from(document.querySelectorAll('.tab-btn')).find(b => b.getAttribute('onclick').includes(tabId));
      if (btn) btn.classList.add('active');
    }

    function onChargeTierChange() {
      const sel = document.getElementById('chargeTierSelect');
      const customGrp = document.getElementById('customAmountGroup');
      if (sel.value === 'custom') {
        customGrp.style.display = 'block';
      } else {
        customGrp.style.display = 'none';
      }
    }

    async function createCheckoutSessionAction() {
      const uid = document.getElementById('chargeUserSelect').value;
      const tier = document.getElementById('chargeTierSelect').value;
      const cycle = document.getElementById('chargeCycleSelect').value;
      let amount = parseFloat(document.getElementById('chargeTierSelect').selectedOptions[0].dataset.price || 0);

      if (tier === 'custom') {
        amount = parseFloat(document.getElementById('customAmountInput').value);
        if (!amount || amount <= 0) {
          alert('Por favor introduce un monto válido.');
          return;
        }
      }

      try {
        const res = await fetch('/api/v1/cloud/billing/checkout-session', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            user_id: uid,
            tier_id: tier,
            amount_usd: amount,
            billing_cycle: cycle
          })
        });
        const data = await res.json();
        if (data.success) {
          showPaymentLinkResult(data.checkout_url);
          showToast('✅ Sesión de Checkout creada con éxito.');
        } else {
          showToast('❌ Error: ' + (data.detail || data.error));
        }
      } catch (e) {
        showToast('❌ Error al contactar el servidor: ' + e.message);
      }
    }

    async function createPaymentLinkAction() {
      const uid = document.getElementById('chargeUserSelect').value;
      const tier = document.getElementById('chargeTierSelect').value;
      let amount = parseFloat(document.getElementById('chargeTierSelect').selectedOptions[0].dataset.price || 19.99);

      if (tier === 'custom') {
        amount = parseFloat(document.getElementById('customAmountInput').value) || 19.99;
      }

      try {
        const res = await fetch('/api/v1/cloud/billing/payment-link', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            user_id: uid,
            amount_usd: amount,
            description: `TruthGPT Cloud — Plan ${tier.toUpperCase()}`
          })
        });
        const data = await res.json();
        if (data.success) {
          showPaymentLinkResult(data.payment_url);
          showToast('🔗 Enlace directo generado. ¡Listo para compartir!');
        }
      } catch (e) {
        showToast('❌ Error: ' + e.message);
      }
    }

    async function chargeUserDirectAction() {
      const uid = document.getElementById('chargeUserSelect').value;
      const tier = document.getElementById('chargeTierSelect').value;
      let amount = parseFloat(document.getElementById('chargeTierSelect').selectedOptions[0].dataset.price || 19.99);

      if (tier === 'custom') {
        amount = parseFloat(document.getElementById('customAmountInput').value) || 19.99;
      }

      if (!confirm(`¿Confirmas procesar el cobro inmediato de $${amount.toFixed(2)} USD a ${uid}?`)) return;

      try {
        const res = await fetch('/api/v1/cloud/billing/charge-direct', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            user_id: uid,
            amount_usd: amount,
            description: `Cobro puntual TruthGPT Cloud — ${tier.toUpperCase()}`
          })
        });
        const data = await res.json();
        if (data.success) {
          showToast(`💰 ¡Cobro de $${amount.toFixed(2)} USD procesado y factura emitida!`);
          fetchDashboardData();
        } else {
          showToast('❌ Error: ' + (data.detail || data.error));
        }
      } catch (e) {
        showToast('❌ Error al procesar cobro: ' + e.message);
      }
    }

    function quickChargeUser(userId, userName) {
      switchTab('tab-billing');
      const sel = document.getElementById('chargeUserSelect');
      if (sel) sel.value = userId;
      openModalForUser(userId, userName, 19.99, 'TruthGPT Cloud Plan Pro');
    }

    async function cancelUserPrompt(userId, userName) {
      const reason = prompt(`¿Motivo de la baja / cancelación para el usuario ${userName}?`, "Precio / Reducción de presupuesto");
      if (!reason) return;

      try {
        const res = await fetch('/api/v1/cloud/subscription/cancel', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ user_id: userId, reason: reason })
        });
        const data = await res.json();
        if (data.success) {
          showToast(`🔴 Cliente ${userName} dado de baja (registrado en métricas de churn).`);
          fetchDashboardData();
        }
      } catch (e) {
        showToast('❌ Error al registrar baja: ' + e.message);
      }
    }

    async function reactivateUserAction(userId) {
      try {
        const res = await fetch('/api/v1/cloud/subscription/reactivate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ user_id: userId })
        });
        const data = await res.json();
        if (data.success) {
          showToast('🟢 ¡Suscripción reactivada con éxito!');
          fetchDashboardData();
        }
      } catch (e) {
        showToast('❌ Error al reactivar: ' + e.message);
      }
    }

    async function openCustomerPortalAction() {
      const uid = document.getElementById('chargeUserSelect').value;
      try {
        const res = await fetch('/api/v1/cloud/billing/portal-session', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ user_id: uid })
        });
        const data = await res.json();
        if (data.portal_url) {
          window.open(data.portal_url, '_blank');
        }
      } catch (e) {
        showToast('❌ Error: ' + e.message);
      }
    }

    function showPaymentLinkResult(url) {
      const box = document.getElementById('paymentLinkResult');
      const input = document.getElementById('generatedLinkInput');
      const btn = document.getElementById('openCheckoutBtn');
      const fullUrl = url.startsWith('http') ? url : window.location.origin + url;
      input.value = fullUrl;
      btn.href = fullUrl;
      box.style.display = 'block';
    }

    function copyPaymentLink() {
      const input = document.getElementById('generatedLinkInput');
      input.select();
      navigator.clipboard.writeText(input.value);
      showToast('📋 ¡Enlace copiado al portapapeles!');
    }

    function showToast(msg) {
      const cont = document.getElementById('toastContainer');
      const t = document.createElement('div');
      t.className = 'toast';
      t.innerHTML = `<span>${msg}</span>`;
      cont.appendChild(t);
      setTimeout(() => {
        t.style.opacity = '0';
        t.style.transform = 'translateY(10px)';
        setTimeout(() => t.remove(), 300);
      }, 3500);
    }

    function formatTimeAgo(ts) {
      if (!ts) return 'Inactivo';
      let sec = typeof ts === 'number' ? Math.floor(Date.now() / 1000 - ts) : Math.floor((Date.now() - new Date(ts).getTime()) / 1000);
      if (sec < 0) sec = 0;
      if (sec < 60) return 'Hace instantes';
      if (sec < 3600) return `Hace ${Math.floor(sec / 60)}m`;
      if (sec < 86400) return `Hace ${Math.floor(sec / 3600)}h`;
      return `Hace ${Math.floor(sec / 86400)}d`;
    }

    function escapeHtml(str) {
      if (!str) return '';
      return String(str).replace(/[&<>"']/g, m => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[m]));
    }

    // Auto-fetch data on load & every 30s
    fetchDashboardData();
    setInterval(fetchDashboardData, 30000);

    // Check URL parameters for instant actions or payment feedback
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('payment') === 'success') {
      showToast('🎉 ¡Pago procesado con éxito! Factura emitida.');
    } else if (urlParams.get('payment') === 'canceled') {
      showToast('ℹ️ El pago fue cancelado por el usuario.');
    }

    function selectModalPaymentMethod(method) {
      if (!window._pendingPayment) {
        window._pendingPayment = {
          user_id: 'usr_default_demo',
          amount_usd: 19.99,
          description: 'TruthGPT Cloud Pro',
          payment_method: 'stripe_card'
        };
      }
      window._pendingPayment.payment_method = method;
      const bStripe = document.getElementById('modalPayMethodStripe');
      const bCrypto = document.getElementById('modalPayMethodCrypto');
      if (method === 'stripe_card') {
        if (bStripe) {
          bStripe.style.border = '1px solid #6366f1';
          bStripe.style.background = 'rgba(99,102,241,0.18)';
          bStripe.style.color = '#e0e7ff';
        }
        if (bCrypto) {
          bCrypto.style.border = '1px solid rgba(255,255,255,0.1)';
          bCrypto.style.background = 'rgba(255,255,255,0.02)';
          bCrypto.style.color = '#9ca3af';
        }
      } else {
        if (bCrypto) {
          bCrypto.style.border = '1px solid #10b981';
          bCrypto.style.background = 'rgba(16,185,129,0.18)';
          bCrypto.style.color = '#a7f3d0';
        }
        if (bStripe) {
          bStripe.style.border = '1px solid rgba(255,255,255,0.1)';
          bStripe.style.background = 'rgba(255,255,255,0.02)';
          bStripe.style.color = '#9ca3af';
        }
      }
    }

    function openModalForUser(userId, userName, amount, concept) {
      const amt = parseFloat(amount) || 19.99;
      const desc = concept || 'TruthGPT Cloud Plan Pro';
      window._pendingPayment = {
        user_id: userId,
        amount_usd: amt,
        description: desc,
        payment_method: 'stripe_card'
      };

      const elConcept = document.getElementById('modalConcept');
      const elUser = document.getElementById('modalUserId');
      const elAmt = document.getElementById('modalAmount');
      const modal = document.getElementById('paymentModal');
      if (elConcept) elConcept.textContent = desc;
      if (elUser) elUser.textContent = `${userName || userId} (${userId})`;
      if (elAmt) elAmt.textContent = `$${amt.toFixed(2)} USD`;
      if (modal) modal.style.display = 'flex';
    }

    function openTestPaymentModal() {
      const sel = document.getElementById('chargeUserSelect');
      const uid = sel && sel.value ? sel.value : 'usr_default_demo';
      openModalForUser(uid, 'Cliente Demo', 19.99, 'TruthGPT Cloud Pro — Prueba de Cobro');
    }

    function testGeneratedPaymentLink() {
      const input = document.getElementById('generatedLinkInput');
      if (!input || !input.value) {
        openTestPaymentModal();
        return;
      }
      try {
        const url = new URL(input.value, window.location.origin);
        const amt = parseFloat(url.searchParams.get('amount') || 19.99);
        const desc = decodeURIComponent(url.searchParams.get('desc') || 'TruthGPT Cloud Service');
        const uid = url.searchParams.get('user_id') || 'usr_default_demo';
        openModalForUser(uid, uid, amt, desc);
      } catch (e) {
        openTestPaymentModal();
      }
    }

    function closePaymentModal() {
      const m = document.getElementById('paymentModal');
      if (m) m.style.display = 'none';
      window._pendingPayment = null;
    }

    async function executeModalPayment() {
      if (!window._pendingPayment) return;
      const btn = document.getElementById('modalConfirmPayBtn');
      if (btn) {
        btn.textContent = 'Procesando...';
        btn.disabled = true;
      }

      try {
        const res = await fetch('/api/v1/cloud/billing/charge-direct', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(window._pendingPayment)
        });
        const data = await res.json();
        if (data.success) {
          closePaymentModal();
          showToast(`✅ ¡Cobro de $${window._pendingPayment.amount_usd.toFixed(2)} USD procesado! Factura emitida.`);
          switchTab('tab-invoices');
          fetchDashboardData();
        } else {
          showToast('❌ Error: ' + (data.detail || data.error));
        }
      } catch (e) {
        showToast('❌ Error de conexión: ' + e.message);
      } finally {
        if (btn) {
          btn.textContent = '💰 Confirmar Pago';
          btn.disabled = false;
        }
      }
    }

    // URL parameters listeners
    if (urlParams.get('action') === 'pay') {
      switchTab('tab-billing');
      const amt = parseFloat(urlParams.get('amount') || 19.99);
      const uid = urlParams.get('user_id') || 'usr_default_demo';
      const desc = decodeURIComponent(urlParams.get('desc') || 'TruthGPT Cloud Service');

      setTimeout(() => {
        openModalForUser(uid, uid, amt, desc);
      }, 400);
      showToast('💳 Enlace de cobro detectado. Pasarela abierta.');
    }

    if (urlParams.get('checkout_session')) {
      const sessId = urlParams.get('checkout_session');
      const uid = urlParams.get('user_id') || 'usr_default_demo';
      const tierId = urlParams.get('tier_id') || 'pro';
      const amt = parseFloat(urlParams.get('amount') || 19.99);
      const desc = `Suscripción Checkout ${tierId.toUpperCase()}`;

      setTimeout(() => {
        openModalForUser(uid, uid, amt, desc);
      }, 400);
    }
  </script>
</body>
</html>
"""
