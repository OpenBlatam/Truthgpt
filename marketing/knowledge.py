"""
Marketing Knowledge Base: Personas, Channels, Funnel Stages & Cialdini Principles
"""

from typing import Dict, Any, List

# ═══════════════════════════════════════════════════════════════════════════
# [PAPER 3.1] CIALDINI 6 PRINCIPLES OF PERSUASION
# Source: "LLM-Generated Ads: From Personalization Parity to Persuasion
#          Superiority" (2025) — 59.1% preference rate with principles
# ═══════════════════════════════════════════════════════════════════════════
CIALDINI_PRINCIPLES: Dict[str, Dict[str, Any]] = {
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
        ]
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
        ]
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
        ]
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
        ]
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
        ]
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
        ]
    },
}

PERSONAS: Dict[str, Dict[str, Any]] = {
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
    }
}

CHANNEL_SPECS: Dict[str, Dict[str, Any]] = {
    "meta_ad":      {"max_chars": 125, "has_headline": True, "headline_max": 40, "cta_options": ["Más información", "Comprar ahora", "Registrarse", "Descargar"]},
    "google_ad":    {"max_chars": 90, "has_headline": True, "headline_max": 30, "cta_options": ["Visitar sitio", "Obtener oferta", "Empezar gratis"]},
    "linkedin_ad":  {"max_chars": 150, "has_headline": True, "headline_max": 50, "cta_options": ["Saber más", "Solicitar demo", "Descargar reporte"]},
    "twitter_ad":   {"max_chars": 280, "has_headline": False, "cta_options": ["Descubrir", "Probar gratis"]},
    "email":        {"max_chars": 500, "has_subject": True, "subject_max": 60},
    "landing_page": {"max_chars": 800, "has_headline": True, "headline_max": 70},
    "retargeting":  {"max_chars": 90, "has_headline": True, "headline_max": 30, "cta_options": ["Volver", "Terminar compra", "Ver oferta"]},
}

FUNNEL_STAGES: Dict[str, Dict[str, Any]] = {
    "tofu": {"name": "TOFU (Atracción)", "goal": "Generar awareness y captar atención masiva", "kpi": "Impresiones, CTR, Costo por clic"},
    "mofu": {"name": "MOFU (Consideración)", "goal": "Nutrir leads con contenido de valor y prueba social", "kpi": "Tasa de apertura email, Descargas, Engagement"},
    "bofu": {"name": "BOFU (Conversión)", "goal": "Cerrar la venta con urgencia y oferta irresistible", "kpi": "Tasa de conversión, CPA, Revenue"},
    "retention": {"name": "Retención / Upsell", "goal": "Aumentar LTV con recompra y referidos", "kpi": "Churn rate, NPS, LTV/CAC ratio"},
}
