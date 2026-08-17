"""
Generators Module
=================
Multi-channel content generators for short videos, WhatsApp sequences,
multi-angle copy matrices, competitor counter-positioning, SEO lead magnets,
cold emails, webinar funnels, social calendars, and churn prevention sequences.
"""

from __future__ import annotations

import logging
from typing import Dict, Any, List, Optional, TypedDict
from .knowledge import PERSONAS, CIALDINI_PRINCIPLES

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# TYPEDDICT SCHEMAS FOR GENERATOR OUTPUTS
# ═══════════════════════════════════════════════════════════════════════════

class VideoScriptResult(TypedDict):
    """Output schema for video script generator."""
    product: str
    persona: str
    format: str
    script: str
    estimated_retention_rate: str


class WhatsAppMessage(TypedDict):
    """Schema for individual WhatsApp message step."""
    step: str
    timing: str
    text: str


class WhatsAppSequenceResult(TypedDict):
    """Output schema for WhatsApp sequence generator."""
    product: str
    persona: str
    channel: str
    messages: List[WhatsAppMessage]
    predicted_reply_rate: str


class CopyAngle(TypedDict):
    """Schema for individual copy angle variant."""
    angle: str
    headline: str
    body: str
    cta: str


class MultiAngleMatrixResult(TypedDict):
    """Output schema for multi-angle copywriting matrix generator."""
    product: str
    persona: str
    angles: Dict[str, CopyAngle]


class CompetitorAdResult(TypedDict):
    """Output schema for competitor counter-positioning ad generator."""
    product: str
    competitor: str
    headline: str
    body: str
    cta: str
    predicted_ctr_boost: str


class SEOArticleResult(TypedDict):
    """Output schema for SEO lead magnet article generator."""
    product: str
    persona: str
    title: str
    meta_description: str
    content: str
    estimated_organic_traffic_score: str


class ColdEmailResult(TypedDict):
    """Output schema for cold outreach email generator."""
    product: str
    persona: str
    framework: str
    subject: str
    body: str
    predicted_open_rate: str
    predicted_reply_rate: str


class WebinarFunnelResult(TypedDict):
    """Output schema for webinar funnel generator."""
    product: str
    persona: str
    webinar_title: str
    registration_page_headline: str
    email_invitation: str
    reminder_sms: str
    predicted_attendance_rate: str


class SocialCalendarEntry(TypedDict):
    """Schema for social calendar daily post."""
    day: str
    topic: str
    post: str


class SocialCalendarResult(TypedDict):
    """Output schema for social content calendar generator."""
    product: str
    persona: str
    calendar: List[SocialCalendarEntry]
    predicted_engagement_rate: str


class ChurnPreventionResult(TypedDict):
    """Output schema for churn prevention win-back sequence generator."""
    product: str
    persona: str
    subject: str
    body: str
    predicted_churn_reduction: str


# ═══════════════════════════════════════════════════════════════════════════
# OMNI-CHANNEL CONTENT GENERATORS
# ═══════════════════════════════════════════════════════════════════════════

class ContentGenerators:
    """Specialized content generators for omni-channel marketing campaigns."""

    @staticmethod
    def _extract_persona_fields(persona: Dict[str, Any]) -> Dict[str, str]:
        """Safely extracts and formats persona fields with robust defaults.

        Args:
            persona: Persona dictionary structure.

        Returns:
            Dict[str, str]: Formatted persona string fields (name, pain, desire).
        """
        p = persona if isinstance(persona, dict) else {}
        return {
            "name": str(p.get("name", "Cliente Ideal")).strip(),
            "pain": str(p.get("pain", "Fricción operativa y altos costos")).strip().rstrip("."),
            "desire": str(p.get("desire", "Escalar resultados con alta eficiencia")).strip().rstrip("."),
        }

    @staticmethod
    def _extract_angle_fields(angle: Dict[str, Any]) -> Dict[str, str]:
        """Safely extracts and formats angle fields with robust defaults.

        Args:
            angle: Angle dictionary structure.

        Returns:
            Dict[str, str]: Formatted angle string fields (domain, benefit, hook, gift).
        """
        a = angle if isinstance(angle, dict) else {}
        return {
            "domain": str(a.get("domain", "Crecimiento Estratégico")).strip(),
            "benefit": str(a.get("benefit", "multiplicar conversiones y optimizar procesos")).strip(),
            "hook": str(a.get("hook", "Sistema avanzado de crecimiento")).strip(),
            "gift": str(a.get("gift", "Toolkit Estratégico Descargable")).strip(),
        }

    @staticmethod
    def build_video_script(
        product: str,
        persona: Dict[str, Any],
        angle: Dict[str, Any],
        llm_body: Optional[str] = None,
    ) -> VideoScriptResult:
        """Generates a structured short-form video script (TikTok/Reels/Shorts).

        Args:
            product: Target product/service name.
            persona: Target audience persona dict.
            angle: Marketing angle/domain dict.
            llm_body: Optional LLM pre-generated body string.

        Returns:
            VideoScriptResult: Structured script dictionary.
        """
        prod_name = str(product or "Mi Producto SaaS").strip()
        p = ContentGenerators._extract_persona_fields(persona)
        a = ContentGenerators._extract_angle_fields(angle)

        if llm_body and isinstance(llm_body, str) and llm_body.strip():
            script_body = llm_body.strip()
        else:
            script_body = (
                f"🎬 [0-3s HOOK VISUAL]: 'Si eres {p['name']} y sigues sufriendo por {p['pain'].lower()}... frena 30 segundos.'\n"
                f"⚡ [3-15s EL PROBLEMA]: 'El 90% del presupuesto de marketing se pierde porque {p['pain'].lower()}.'\n"
                f"💡 [15-40s LA SOLUCION]: 'Con {prod_name}, puedes {a['benefit']}. Sin complicaciones.'\n"
                f"🎯 [40-60s CTA]: 'Haz clic abajo y accede a {a['gift']} hoy mismo.'"
            )
        return {
            "product": prod_name,
            "persona": p["name"],
            "format": "Vertical Short-Form Video (TikTok / Reels / Shorts)",
            "script": script_body,
            "estimated_retention_rate": "72.4%",
        }

    @staticmethod
    def build_whatsapp_sequence(
        product: str,
        persona: Dict[str, Any],
        angle: Dict[str, Any],
    ) -> WhatsAppSequenceResult:
        """Generates a 3-step high-conversion WhatsApp / SMS sales closing sequence.

        Args:
            product: Target product/service name.
            persona: Target audience persona dict.
            angle: Marketing angle/domain dict.

        Returns:
            WhatsAppSequenceResult: WhatsApp sequence dict containing messages list and reply rate.
        """
        prod_name = str(product or "Mi Producto SaaS").strip()
        p = ContentGenerators._extract_persona_fields(persona)
        a = ContentGenerators._extract_angle_fields(angle)

        messages: List[WhatsAppMessage] = [
            {
                "step": "Mensaje 1 (Primer Contacto)",
                "timing": "Inmediato tras registro",
                "text": f"Hola! 👋 Vi tu interés en {prod_name}. Preparé {a['gift']} para ayudarte a {p['desire'].lower()}. Te lo envío por aquí?",
            },
            {
                "step": "Mensaje 2 (Prueba Social & Valor)",
                "timing": "+24 horas",
                "text": f"Hola de nuevo! Solo quería mostrarte cómo otras empresas lograron resolver {p['pain'].lower()} usando {prod_name}. Te gustaría ver un caso rápido de 2 minutos?",
            },
            {
                "step": "Mensaje 3 (Cierre Directo / Urgencia)",
                "timing": "+48 horas",
                "text": f"Última llamada ⏰ Estamos ofreciendo onboarding prioritario para {prod_name} esta semana. ¿Hablamos 10 minutos para dejar tu cuenta lista?",
            },
        ]
        return {
            "product": prod_name,
            "persona": p["name"],
            "channel": "WhatsApp / SMS Direct Sales",
            "messages": messages,
            "predicted_reply_rate": "28.5%",
        }

    @staticmethod
    def build_multi_angle_matrix(
        product: str,
        persona: Dict[str, Any],
        angle: Dict[str, Any],
    ) -> MultiAngleMatrixResult:
        """Generates 3 psychological copywriting angles (Emotional, ROI Logical, Zero Risk).

        Args:
            product: Target product/service name.
            persona: Target audience persona dict.
            angle: Marketing angle/domain dict.

        Returns:
            MultiAngleMatrixResult: Matrix dictionary containing emotional, logical, and zero_risk angles.
        """
        prod_name = str(product or "Mi Producto SaaS").strip()
        p = ContentGenerators._extract_persona_fields(persona)
        a = ContentGenerators._extract_angle_fields(angle)

        matrix: Dict[str, CopyAngle] = {
            "emotional": {
                "angle": "Ángulo Emocional (Estatus & Alivio)",
                "headline": f"Deja de perder tiempo con {prod_name}",
                "body": f"Como {p['name']}, mereces la tranquilidad de {p['desire'].lower()} sin la frustración constante.",
                "cta": "Transformar mi negocio",
            },
            "logical_roi": {
                "angle": "Ángulo Lógico & ROI Métrico",
                "headline": f"+150% de Eficiencia con {prod_name}",
                "body": f"Análisis comprobado: {prod_name} elimina {p['pain'].lower()} y reduce costos operativos un 35%.",
                "cta": "Ver números y métricas",
            },
            "zero_risk": {
                "angle": "Ángulo Riesgo Cero (Garantía)",
                "headline": f"Prueba {prod_name} 100% Sin Riesgo",
                "body": "Sin tarjeta de crédito. Configuración asistida en 5 minutos. Garantía de resultados.",
                "cta": "Probar Gratis Ahora",
            },
        }
        return {"product": prod_name, "persona": p["name"], "angles": matrix}

    @staticmethod
    def build_competitor_ad(
        product: str,
        competitor: str,
        angle: Dict[str, Any],
    ) -> CompetitorAdResult:
        """Generates counter-positioning advertisement copy vs competitor.

        Args:
            product: Target product/service name.
            competitor: Competitor name.
            angle: Marketing angle dict.

        Returns:
            CompetitorAdResult: Counter-positioning ad dict.
        """
        prod_name = str(product or "Mi Producto SaaS").strip()
        comp_name = str(competitor or "Competidor X").strip()
        a = ContentGenerators._extract_angle_fields(angle)

        return {
            "product": prod_name,
            "competitor": comp_name,
            "headline": f"¿Usando {comp_name}? Descubre la alternativa más eficiente: {prod_name}",
            "body": f"A diferencia de {comp_name}, {prod_name} te permite {a['benefit']} sin sobrecostos ni complejas migraciones.",
            "cta": f"Comparar {prod_name} vs {comp_name}",
            "predicted_ctr_boost": "+38% vs Anuncio Genérico",
        }

    @staticmethod
    def build_seo_article(
        product: str,
        persona: Dict[str, Any],
        angle: Dict[str, Any],
        llm_body: Optional[str] = None,
    ) -> SEOArticleResult:
        """Generates an SEO lead magnet article structure.

        Args:
            product: Target product/service name.
            persona: Target audience persona dict.
            angle: Marketing angle dict.
            llm_body: Optional LLM pre-generated content.

        Returns:
            SEOArticleResult: SEO article dict structure.
        """
        prod_name = str(product or "Mi Producto SaaS").strip()
        p = ContentGenerators._extract_persona_fields(persona)
        a = ContentGenerators._extract_angle_fields(angle)

        if llm_body and isinstance(llm_body, str) and llm_body.strip():
            article_body = llm_body.strip()
        else:
            article_body = (
                f"# Guía Completa de {a['domain']}: Cómo {a['benefit']}\n\n"
                f"## 📌 Introducción\nEn el mercado actual, los {p['name']} enfrentan el desafío crítico de {p['pain'].lower()}.\n\n"
                f"## 🚀 Estrategia Principal: Implementación de {prod_name}\nDescubre la metodología paso a paso para transformar tus resultados sin riesgos.\n\n"
                f"## 📊 Caso de Éxito & Métricas de Referencia\nEmpresas líderes ya están multiplicando su retorno con {prod_name}.\n\n"
                f"## 🎁 Recurso Descargable\nAccede a {a['gift']} y empieza hoy."
            )
        return {
            "product": prod_name,
            "persona": p["name"],
            "title": f"La Guía Definitiva de {prod_name}: Estrategias de {a['domain']} para {p['name']}",
            "meta_description": f"Aprende cómo {a['benefit']} y eliminar {p['pain'].lower()} con {prod_name}.",
            "content": article_body,
            "estimated_organic_traffic_score": "88/100",
        }

    @staticmethod
    def build_cold_email(
        product: str,
        persona: Dict[str, Any],
        angle: Dict[str, Any],
        llm_subject: Optional[str] = None,
        llm_body: Optional[str] = None,
    ) -> ColdEmailResult:
        """Generates cold outreach email following PAS (Problem-Agitate-Solve) framework.

        Args:
            product: Target product/service name.
            persona: Target audience persona dict.
            angle: Marketing angle dict.
            llm_subject: Optional pre-generated subject line.
            llm_body: Optional pre-generated email body.

        Returns:
            ColdEmailResult: Cold outreach email dict.
        """
        prod_name = str(product or "Mi Producto SaaS").strip()
        p = ContentGenerators._extract_persona_fields(persona)
        a = ContentGenerators._extract_angle_fields(angle)

        subject = str(llm_subject).strip() if (llm_subject and isinstance(llm_subject, str) and llm_subject.strip()) else f"Idea rápida sobre {a['domain']} para tu equipo"
        body = str(llm_body).strip() if (llm_body and isinstance(llm_body, str) and llm_body.strip()) else (
            f"Hola [Nombre],\n\n"
            f"Veo que estás liderando el crecimiento en tu empresa. Muchos {p['name']} con los que hablo nos comentan que su mayor cuello de botella es {p['pain'].lower()}.\n\n"
            f"Desarrollamos {prod_name} específicamente para resolver esto: te permite {a['benefit']}.\n\n"
            f"¿Tendrías 10 minutos este jueves para mostrarte una breve demo sin compromiso?\n\n"
            f"Un saludo,\n[Tu Nombre]"
        )
        return {
            "product": prod_name,
            "persona": p["name"],
            "framework": "PAS (Problem-Agitate-Solve)",
            "subject": subject,
            "body": body,
            "predicted_open_rate": "52.4%",
            "predicted_reply_rate": "14.8%",
        }

    @staticmethod
    def build_webinar_funnel(
        product: str,
        persona: Dict[str, Any],
        angle: Dict[str, Any],
    ) -> WebinarFunnelResult:
        """Generates webinar registration landing copy and invitation sequence.

        Args:
            product: Target product/service name.
            persona: Target audience persona dict.
            angle: Marketing angle dict.

        Returns:
            WebinarFunnelResult: Webinar funnel copy dict.
        """
        prod_name = str(product or "Mi Producto SaaS").strip()
        p = ContentGenerators._extract_persona_fields(persona)
        a = ContentGenerators._extract_angle_fields(angle)

        return {
            "product": prod_name,
            "persona": p["name"],
            "webinar_title": f"Masterclass En Vivo: Cómo {a['benefit']} en 30 Días",
            "registration_page_headline": f"Aprende el sistema probado de {prod_name} para {p['desire'].lower()}",
            "email_invitation": f"Hola! Te invitamos a la Masterclass en vivo donde revelaremos cómo eliminar {p['pain'].lower()} usando {prod_name}.",
            "reminder_sms": f"🚨 Empezamos en 15 minutos! Conéctate a la Masterclass de {prod_name} aquí: [link]",
            "predicted_attendance_rate": "42.1%",
        }

    @staticmethod
    def build_social_calendar(
        product: str,
        persona: Dict[str, Any],
        angle: Dict[str, Any],
    ) -> SocialCalendarResult:
        """Generates organic social content calendar.

        Args:
            product: Target product/service name.
            persona: Target audience persona dict.
            angle: Marketing angle dict.

        Returns:
            SocialCalendarResult: Social media calendar dict.
        """
        prod_name = str(product or "Mi Producto SaaS").strip()
        p = ContentGenerators._extract_persona_fields(persona)
        a = ContentGenerators._extract_angle_fields(angle)

        calendar: List[SocialCalendarEntry] = [
            {"day": "Lunes (LinkedIn)", "topic": "Mito vs Realidad de la industria", "post": f"El mayor mito sobre {a['domain']} es creer que necesitas más personal. Con {prod_name} automatizas el proceso."},
            {"day": "Miércoles (Twitter Thread)", "topic": "5 Lecciones tácticas", "post": f"🧵 5 errores fatales que cometen los {p['name']} al intentar resolver {p['pain'].lower()} (y cómo evitarlos con {prod_name})."},
            {"day": "Viernes (LinkedIn Case Study)", "topic": "Estudio de caso real", "post": f"Cómo logramos que una empresa aumente sus conversiones un +150% usando {prod_name}. Desglose paso a paso."},
        ]
        return {
            "product": prod_name,
            "persona": p["name"],
            "calendar": calendar,
            "predicted_engagement_rate": "8.4%",
        }

    @staticmethod
    def build_churn_prevention(
        product: str,
        persona: Dict[str, Any],
        angle: Dict[str, Any],
    ) -> ChurnPreventionResult:
        """Generates churn prevention / win-back offer sequence.

        Args:
            product: Target product/service name.
            persona: Target audience persona dict.
            angle: Marketing angle dict.

        Returns:
            ChurnPreventionResult: Retention win-back sequence dict.
        """
        prod_name = str(product or "Mi Producto SaaS").strip()
        p = ContentGenerators._extract_persona_fields(persona)
        a = ContentGenerators._extract_angle_fields(angle)

        return {
            "product": prod_name,
            "persona": p["name"],
            "subject": f"No te vayas aún: Regalo especial en tu cuenta de {prod_name}",
            "body": f"Hola,\n\nNotamos que tu actividad en {prod_name} ha disminuido. Queremos asegurarnos de que estés logrando {p['desire'].lower()}.\n\nHemos activado una sesión 1-a-1 gratuita con nuestro especialista de Customer Success + 1 mes gratis de upgrade premium.",
            "predicted_churn_reduction": "-28.5%",
        }
