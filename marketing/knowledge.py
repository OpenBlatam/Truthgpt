"""
Marketing Knowledge Base Module
===============================
Contains structured domain knowledge for marketing automation:
- Cialdini's 6 Principles of Persuasion (Reciprocidad, Compromiso, Prueba Social, Autoridad, Simpatía, Escasez)
- Target Marketing Personas (CEO B2B, E-commerce Manager, Startup Growth Lead)
- Channel Technical Specifications (Meta Ads, Google Ads, LinkedIn Ads, Twitter/X, Email, Landing Page, Retargeting)
- Funnel Stages (TOFU, MOFU, BOFU, Retention)
"""

from __future__ import annotations

import logging
from typing import Dict, Any, List, Optional, TypedDict

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# TYPEDDICT DEFINITIONS FOR DOMAIN KNOWLEDGE SCHEMAS
# ═══════════════════════════════════════════════════════════════════════════

class CialdiniPrinciple(TypedDict):
    """Schema for Cialdini Persuasion Principle metadata."""
    name: str
    description: str
    triggers: Dict[str, str]
    copy_patterns: List[str]


class PersonaData(TypedDict):
    """Schema for target audience persona metadata."""
    name: str
    pain: str
    desire: str
    tone: str
    channels: List[str]
    fatigue_sensitivity: float


class ChannelSpec(TypedDict, total=False):
    """Schema for marketing channel technical limits and options."""
    max_chars: int
    has_headline: bool
    headline_max: int
    cta_options: List[str]
    has_subject: bool
    subject_max: int


class FunnelStage(TypedDict):
    """Schema for marketing funnel stage definitions."""
    name: str
    goal: str
    kpi: str


# ═══════════════════════════════════════════════════════════════════════════
# CIALDINI 6 PRINCIPLES OF PERSUASION
# Source: "LLM-Generated Ads: From Personalization Parity to Persuasion
#          Superiority" (2025) — 59.1% preference rate with principles
# ═══════════════════════════════════════════════════════════════════════════

CIALDINI_PRINCIPLES: Dict[str, CialdiniPrinciple] = {
    "reciprocity": {
        "name": "Reciprocidad",
        "description": "Da valor primero para generar obligación de devolver",
        "triggers": {
            "tofu": "auditoría gratuita, template descargable, herramienta free",
            "mofu": "caso de estudio exclusivo, webinar privado, consultoría express",
            "bofu": "prueba gratis 14 días, setup incluido, onboarding personalizado",
            "retention": "upgrade gratuito, feature anticipada, créditos bonus",
        },
        "copy_patterns": [
            "Te regalamos {gift} sin pedir nada a cambio",
            "Descarga gratis: {gift}. Sin tarjeta, sin compromiso",
            "Accede a {gift} — es nuestro regalo por tu interés",
        ],
    },
    "commitment": {
        "name": "Compromiso y Consistencia",
        "description": "Pequeños 'sí' llevan a grandes decisiones",
        "triggers": {
            "tofu": "responde esta encuesta de 30 segundos",
            "mofu": "reserva tu lugar en el webinar",
            "bofu": "activa tu prueba gratuita (solo 2 minutos)",
            "retention": "renueva y desbloquea tu nivel premium",
        },
        "copy_patterns": [
            "Solo toma {time} — el primer paso que ya diste fue abrir este mensaje",
            "Ya demostraste interés. El siguiente paso lógico: {action}",
            "Tú ya sabes que {pain} es un problema. Solo falta actuar",
        ],
    },
    "social_proof": {
        "name": "Prueba Social",
        "description": "Las personas siguen las acciones de otros similares",
        "triggers": {
            "tofu": "+2,400 empresas ya usan {product}",
            "mofu": "mira los resultados de empresas como la tuya",
            "bofu": "147 empresas se unieron esta semana",
            "retention": "los clientes que renuevan crecen 3.2x más",
        },
        "copy_patterns": [
            "{count} empresas en tu industria ya lo están usando",
            "\"Redujimos nuestro CPA un 41%\" — {testimonial_name}, CMO",
            "9 de cada 10 usuarios lo recomiendan a colegas",
        ],
    },
    "authority": {
        "name": "Autoridad",
        "description": "Expertise y credenciales generan confianza",
        "triggers": {
            "tofu": "desarrollado por ingenieros de DeepSeek y Google Brain",
            "mofu": "metodología publicada en KDD 2025",
            "bofu": "certificado por partners de Meta y Google",
            "retention": "reconocido como líder por Gartner en IA para Marketing",
        },
        "copy_patterns": [
            "Basado en investigación publicada en {conference}",
            "Desarrollado por el equipo que creó {credencial}",
            "Tecnología validada por {authority_name}",
        ],
    },
    "liking": {
        "name": "Simpatía",
        "description": "Compramos a quien nos cae bien y se parece a nosotros",
        "triggers": {
            "tofu": "somos fundadores como tú, sabemos lo que se siente",
            "mofu": "creamos esto porque vivimos tu mismo problema",
            "bofu": "te acompañamos desde el día 1",
            "retention": "tu éxito es literalmente nuestro éxito",
        },
        "copy_patterns": [
            "Sabemos exactamente cómo se siente {pain} porque lo vivimos",
            "No somos una corporación sin rostro — somos un equipo que entiende tu reto",
            "Construimos {product} para resolver nuestro propio problema. Ahora es tuyo",
        ],
    },
    "scarcity": {
        "name": "Escasez",
        "description": "Lo limitado se percibe como más valioso",
        "triggers": {
            "tofu": "contenido disponible solo esta semana",
            "mofu": "quedan 12 lugares para el webinar del jueves",
            "bofu": "oferta de lanzamiento: solo las primeras 50 cuentas",
            "retention": "acceso anticipado exclusivo para clientes actuales",
        },
        "copy_patterns": [
            "Solo quedan {count} lugares — no habrá otra oportunidad este trimestre",
            "Esta oferta expira en {hours}h. Después vuelve al precio regular",
            "Limitado a {count} empresas. {taken} ya confirmaron su lugar",
        ],
    },
}

PERSONAS: Dict[str, PersonaData] = {
    "ceo_b2b": {
        "name": "CEO / Founder B2B",
        "pain": "No tiene tiempo para experimentar. Necesita ROI comprobado.",
        "desire": "Escalar ingresos sin escalar equipo de marketing.",
        "tone": "directo, datos, sin florituras",
        "channels": ["linkedin_ad", "email", "landing_page"],
        "fatigue_sensitivity": 0.15,
    },
    "ecommerce_manager": {
        "name": "E-commerce Manager",
        "pain": "ROAS en caída, CPA subiendo, presupuesto limitado.",
        "desire": "Campañas que se optimicen solas y vendan 24/7.",
        "tone": "urgente, orientado a resultados, números concretos",
        "channels": ["meta_ad", "google_ad", "email", "retargeting"],
        "fatigue_sensitivity": 0.10,
    },
    "startup_growth": {
        "name": "Growth Lead / Startup",
        "pain": "Necesita tracción rápida con presupuesto limitado.",
        "desire": "Hackear el crecimiento con IA antes que la competencia.",
        "tone": "innovador, audaz, velocidad",
        "channels": ["twitter_ad", "meta_ad", "landing_page", "email"],
        "fatigue_sensitivity": 0.08,
    },
}

CHANNEL_SPECS: Dict[str, ChannelSpec] = {
    "meta_ad":      {"max_chars": 125, "has_headline": True, "headline_max": 40, "cta_options": ["Más información", "Comprar ahora", "Registrarse", "Descargar"]},
    "google_ad":    {"max_chars": 90, "has_headline": True, "headline_max": 30, "cta_options": ["Visitar sitio", "Obtener oferta", "Empezar gratis"]},
    "linkedin_ad":  {"max_chars": 150, "has_headline": True, "headline_max": 50, "cta_options": ["Saber más", "Solicitar demo", "Descargar reporte"]},
    "twitter_ad":   {"max_chars": 280, "has_headline": False, "cta_options": ["Descubrir", "Probar gratis"]},
    "email":        {"max_chars": 500, "has_subject": True, "subject_max": 60},
    "landing_page": {"max_chars": 800, "has_headline": True, "headline_max": 70},
    "retargeting":  {"max_chars": 90, "has_headline": True, "headline_max": 30, "cta_options": ["Volver", "Terminar compra", "Ver oferta"]},
}

FUNNEL_STAGES: Dict[str, FunnelStage] = {
    "tofu": {"name": "TOFU (Atracción)", "goal": "Generar awareness y captar atención masiva", "kpi": "Impresiones, CTR, Costo por clic"},
    "mofu": {"name": "MOFU (Consideración)", "goal": "Nutrir leads con contenido de valor y prueba social", "kpi": "Tasa de apertura email, Descargas, Engagement"},
    "bofu": {"name": "BOFU (Conversión)", "goal": "Cerrar la venta con urgencia y oferta irresistible", "kpi": "Tasa de conversión, CPA, Revenue"},
    "retention": {"name": "Retención / Upsell", "goal": "Aumentar LTV con recompra y referidos", "kpi": "Churn rate, NPS, LTV/CAC ratio"},
}


# ═══════════════════════════════════════════════════════════════════════════
# HELPER LOOKUP FUNCTIONS WITH DEFENSIVE VALIDATION
# ═══════════════════════════════════════════════════════════════════════════

def get_persona(key: str, default: Optional[str] = "ceo_b2b") -> PersonaData:
    """Retrieves target persona dictionary by key with optional fallback.

    Args:
        key: Target persona identifier key (e.g. 'ceo_b2b', 'ecommerce_manager').
        default: Fallback persona key if target key is not found.

    Returns:
        PersonaData: Persona specification dictionary.
    """
    if not isinstance(key, str) or not key.strip():
        fallback_key = default if isinstance(default, str) and default in PERSONAS else "ceo_b2b"
        return PERSONAS[fallback_key]

    clean_key = key.strip().lower()
    if clean_key in PERSONAS:
        return PERSONAS[clean_key]

    fallback = default if isinstance(default, str) and default in PERSONAS else "ceo_b2b"
    return PERSONAS.get(fallback, PERSONAS["ceo_b2b"])


def get_channel_spec(channel: str) -> ChannelSpec:
    """Retrieves technical specification for a marketing channel.

    Args:
        channel: Channel key (e.g. 'meta_ad', 'email', 'linkedin_ad').

    Returns:
        ChannelSpec: Channel specification dictionary.
    """
    if not isinstance(channel, str) or not channel.strip():
        return {"max_chars": 250, "has_headline": True, "headline_max": 60}
    return CHANNEL_SPECS.get(channel.strip().lower(), {"max_chars": 250, "has_headline": True, "headline_max": 60})


def get_cialdini_principle(principle_key: str) -> Optional[CialdiniPrinciple]:
    """Retrieves Cialdini persuasion principle metadata by key.

    Args:
        principle_key: Principle key (e.g. 'reciprocity', 'social_proof').

    Returns:
        Optional[CialdiniPrinciple]: Principle dictionary if found, None otherwise.
    """
    if not isinstance(principle_key, str) or not principle_key.strip():
        return None
    return CIALDINI_PRINCIPLES.get(principle_key.strip().lower())


def get_funnel_stage(stage_key: str) -> FunnelStage:
    """Retrieves funnel stage metadata dictionary.

    Args:
        stage_key: Stage key ('tofu', 'mofu', 'bofu', 'retention').

    Returns:
        FunnelStage: Stage metadata dictionary.
    """
    if not isinstance(stage_key, str) or not stage_key.strip():
        return {"name": "GENERAL", "goal": "General Marketing", "kpi": "CTR / Conversions"}
    clean_key = stage_key.strip().lower()
    return FUNNEL_STAGES.get(clean_key, {"name": clean_key.upper(), "goal": "General Marketing", "kpi": "CTR / Conversions"})
