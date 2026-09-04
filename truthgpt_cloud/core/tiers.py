"""
💎 TruthGPT Cloud - Subscription Tiers & Feature Matrix
Defines tier levels, resource limits, formal verification capabilities,
and compute allocations analogous to frontier AI tiers (Gemini / Claude / ChatGPT).
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Any, Union


class CloudTier(str, Enum):
    FREE = "free"
    PRO = "pro"
    ULTRA = "ultra"
    ENTERPRISE = "enterprise"


@dataclass
class TierConfig:
    tier_id: CloudTier
    name: str
    tagline: str
    price_monthly_usd: float
    price_yearly_usd: float
    badge: str

    # Context and Compute Limits
    context_window_tokens: int
    max_output_tokens: int
    daily_token_limit: int
    requests_per_minute: int
    concurrent_requests: int

    # Intelligence & Models
    available_models: List[str]
    default_model: str
    ensemble_enabled: bool
    swarm_multi_agent: bool
    max_swarm_agents: int

    # Formal Verification & Mathematical Rigor
    smt_z3_verification_depth: int  # 0: None, 1: Basic SymPy, 2: Full Z3 SMT, 3: Quantum/Singularity Hybrid
    hoare_dbc_contracts: bool
    proof_certificate_generation: bool
    auto_backtracking_cove: bool

    # Performance & Cloud Infrastructure
    latency_tier: str  # "standard", "priority_tensorrt", "zero_queue_dedicated"
    priority_gpu_routing: bool
    sla_uptime_percent: float
    private_lora_hosting: bool
    dedicated_api_keys: int
    features_list: List[str] = field(default_factory=list)

    @property
    def tokens_per_minute(self) -> int:
        """Estimated tokens per minute based on daily token limit."""
        return max(10_000, self.daily_token_limit // (24 * 60))

    @property
    def features(self) -> Dict[str, Any]:
        """Feature flags dictionary for easy tier comparison and telemetry."""
        return {
            "formal_verification": self.smt_z3_verification_depth >= 2,
            "multi_agent_swarm": self.swarm_multi_agent,
            "paper_compiler": self.tier_id in (CloudTier.ULTRA, CloudTier.ENTERPRISE),
            "cryptographic_audit": self.tier_id in (CloudTier.PRO, CloudTier.ULTRA, CloudTier.ENTERPRISE),
            "features_list": self.features_list,
        }


# ---------------------------------------------------------------------------
# 🌟 Tier Catalog Definitions
# ---------------------------------------------------------------------------

TIER_CONFIGURATIONS: Dict[CloudTier, TierConfig] = {
    CloudTier.FREE: TierConfig(
        tier_id=CloudTier.FREE,
        name="TruthGPT Lite (Free)",
        tagline="Explora la verdad matemática y razonamiento estructurado sin costo.",
        price_monthly_usd=0.0,
        price_yearly_usd=0.0,
        badge="Community",
        context_window_tokens=32_768,
        max_output_tokens=4_096,
        daily_token_limit=50_000,
        requests_per_minute=15,
        concurrent_requests=1,
        available_models=["deepseek-chat", "truthgpt-lite"],
        default_model="truthgpt-lite",
        ensemble_enabled=False,
        swarm_multi_agent=False,
        max_swarm_agents=1,
        smt_z3_verification_depth=1,  # Basic SymPy
        hoare_dbc_contracts=True,
        proof_certificate_generation=False,
        auto_backtracking_cove=False,
        latency_tier="standard",
        priority_gpu_routing=False,
        sla_uptime_percent=99.0,
        private_lora_hosting=False,
        dedicated_api_keys=1,
        features_list=[
            "Acceso al modelo base TruthGPT Lite",
            "Verificación algebraica básica con SymPy",
            "Ventana de contexto de 32k tokens",
            "Límite de 15 peticiones por minuto (RPM)",
            "1 clave de API para integraciones personales",
            "Soporte estándar de la comunidad"
        ]
    ),

    CloudTier.PRO: TierConfig(
        tier_id=CloudTier.PRO,
        name="TruthGPT Pro (Truth-Seeker)",
        tagline="Razonamiento avanzado con Solucionador Z3 SMT, Swarm y alta velocidad.",
        price_monthly_usd=19.99,
        price_yearly_usd=199.90,  # 2 months free
        badge="Popular ✨",
        context_window_tokens=200_000,
        max_output_tokens=16_384,
        daily_token_limit=2_000_000,
        requests_per_minute=120,
        concurrent_requests=5,
        available_models=[
            "deepseek-v3",
            "claude-3-7-sonnet",
            "gpt-4o",
            "gemini-2-5-pro",
            "truthgpt-pro-smt"
        ],
        default_model="truthgpt-pro-smt",
        ensemble_enabled=True,
        swarm_multi_agent=True,
        max_swarm_agents=5,
        smt_z3_verification_depth=2,  # Full Z3 SMT
        hoare_dbc_contracts=True,
        proof_certificate_generation=True,
        auto_backtracking_cove=True,
        latency_tier="priority_tensorrt",
        priority_gpu_routing=True,
        sla_uptime_percent=99.9,
        private_lora_hosting=False,
        dedicated_api_keys=5,
        features_list=[
            "Modelos Frontier: DeepSeek V3, Claude 3.7 Sonnet, GPT-4o",
            "Motor de Verificación Formal Z3 SMT & Hoare Logic",
            "Certificados de Prueba Criptográfica de Verdad",
            "Orquestación Swarm de hasta 5 Agentes de Investigación",
            "Ventana de contexto de 200k tokens",
            "Cola de GPU prioritaria acelerada con TensorRT-LLM",
            "Cadena de Verificación (CoVe) con Auto-Backtracking",
            "5 claves de API dedicadas"
        ]
    ),

    CloudTier.ULTRA: TierConfig(
        tier_id=CloudTier.ULTRA,
        name="TruthGPT Ultra (Singularity)",
        tagline="Consenso Multi-Modelo Cuántico y orquestación Swarm masiva ilimitada.",
        price_monthly_usd=99.99,
        price_yearly_usd=999.00,
        badge="Max Performance ⚡",
        context_window_tokens=2_000_000,
        max_output_tokens=65_536,
        daily_token_limit=20_000_000,
        requests_per_minute=600,
        concurrent_requests=25,
        available_models=[
            "truthgpt-quantum-singularity",
            "ensemble-supreme",
            "deepseek-r1-reasoner",
            "claude-3-7-sonnet-thinking",
            "gpt-4o-extended",
            "gemini-2-5-pro-deep"
        ],
        default_model="truthgpt-quantum-singularity",
        ensemble_enabled=True,
        swarm_multi_agent=True,
        max_swarm_agents=20,
        smt_z3_verification_depth=3,  # Hybrid Quantum / Singularity Theorem Prover
        hoare_dbc_contracts=True,
        proof_certificate_generation=True,
        auto_backtracking_cove=True,
        latency_tier="zero_queue_dedicated",
        priority_gpu_routing=True,
        sla_uptime_percent=99.99,
        private_lora_hosting=True,
        dedicated_api_keys=20,
        features_list=[
            "Ensemble Cuántico Multi-Modelo con Votación de Consenso",
            "Acceso sin límites a TruthGPT Quantum Singularity",
            "Swarm Autónomo de 20 agentes en paralelo",
            "Ventana masiva de 2,000,000 tokens de contexto",
            "Compilación de Papers SOTA con descarga de pesos e inferencia directa",
            "Alojamiento privado de adaptadores LoRA y checkpoints EMA",
            "Prioridad Zero-Queue absoluta en clúster H100/H200",
            "20 claves de API y webhook real-time streaming"
        ]
    ),

    CloudTier.ENTERPRISE: TierConfig(
        tier_id=CloudTier.ENTERPRISE,
        name="TruthGPT Enterprise (Sovereign)",
        tagline="Infraestructura dedicada, seguridad soberana y auditoría formal personalizada.",
        price_monthly_usd=499.00,
        price_yearly_usd=4990.00,
        badge="Custom / Enterprise 🏢",
        context_window_tokens=4_000_000,
        max_output_tokens=131_072,
        daily_token_limit=100_000_000,
        requests_per_minute=2000,
        concurrent_requests=100,
        available_models=[
            "truthgpt-sovereign-cluster",
            "custom-finetuned-truthgpt",
            "ensemble-supreme",
            "all-frontier-models"
        ],
        default_model="truthgpt-sovereign-cluster",
        ensemble_enabled=True,
        swarm_multi_agent=True,
        max_swarm_agents=100,
        smt_z3_verification_depth=3,
        hoare_dbc_contracts=True,
        proof_certificate_generation=True,
        auto_backtracking_cove=True,
        latency_tier="zero_queue_dedicated",
        priority_gpu_routing=True,
        sla_uptime_percent=99.999,
        private_lora_hosting=True,
        dedicated_api_keys=100,
        features_list=[
            "Clúster dedicado en nube privada / on-premise",
            "Entrenamiento y fine-tuning continuo de modelos propietarios",
            "Garantía SLA del 99.999% con soporte 24/7 de ingenieros IA",
            "Auditoría formal de seguridad y cumplimiento regulatorio",
            "Conexión directa con Web3 Sentinel e indexación de papers privados",
            "Claves de API ilimitadas con roles granulares y SSO SAML"
        ]
    )
}


def get_tier_config(tier: Union[str, CloudTier, Any]) -> TierConfig:
    """Retrieve the configuration object for a specific tier."""
    if isinstance(tier, str):
        try:
            tier = CloudTier(tier.lower())
        except ValueError:
            tier = CloudTier.FREE
    return TIER_CONFIGURATIONS.get(tier, TIER_CONFIGURATIONS[CloudTier.FREE])


def get_all_tiers() -> List[Dict[str, Any]]:
    """Return serialized tier definitions for API and UI rendering."""
    tiers_data = []
    for cfg in TIER_CONFIGURATIONS.values():
        tiers_data.append({
            "tier_id": cfg.tier_id.value,
            "name": cfg.name,
            "tagline": cfg.tagline,
            "price_monthly_usd": cfg.price_monthly_usd,
            "price_yearly_usd": cfg.price_yearly_usd,
            "badge": cfg.badge,
            "context_window_tokens": cfg.context_window_tokens,
            "max_output_tokens": cfg.max_output_tokens,
            "daily_token_limit": cfg.daily_token_limit,
            "requests_per_minute": cfg.requests_per_minute,
            "concurrent_requests": cfg.concurrent_requests,
            "max_swarm_agents": cfg.max_swarm_agents,
            "smt_verification_level": f"Nivel {cfg.smt_z3_verification_depth}",
            "smt_z3_verification_depth": cfg.smt_z3_verification_depth,
            "proof_certificates": cfg.proof_certificate_generation,
            "latency_tier": cfg.latency_tier,
            "available_models": cfg.available_models,
            "default_model": cfg.default_model,
            "features_list": cfg.features_list
        })
    return tiers_data


__all__ = [
    "CloudTier",
    "TierConfig",
    "TIER_CONFIGURATIONS",
    "get_tier_config",
    "get_all_tiers",
]
