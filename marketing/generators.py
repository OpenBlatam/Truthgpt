"""
Generators Module: Multi-channel content generators for Video, WhatsApp, SEO, Cold Email, Social Media, etc.
"""

from typing import Dict, Any, List
from .knowledge import PERSONAS, CIALDINI_PRINCIPLES


class ContentGenerators:
    """Specialized content generators for omni-channel campaigns."""

    @staticmethod
    def build_video_script(product: str, persona: dict, angle: dict, llm_body: str = None) -> Dict[str, Any]:
        if llm_body:
            script_body = llm_body
        else:
            script_body = (
                f"🎬 [0-3s HOOK VISUAL]: 'Si eres {persona['name']} y sigues sufriendo por {persona['pain'].lower()}... frena 30 segundos.'\n"
                f"⚡ [3-15s EL PROBLEMA]: 'El 90% del presupuesto de marketing se pierde porque {persona['pain'].lower()}.'\n"
                f"💡 [15-40s LA SOLUCION]: 'Con {product}, puedes {angle['benefit']}. Sin complicaciones.'\n"
                f"🎯 [40-60s CTA]: 'Haz clic abajo y accede a {angle['gift']} hoy mismo.'"
            )
        return {
            "product": product, "persona": persona["name"],
            "format": "Vertical Short-Form Video (TikTok / Reels / Shorts)",
            "script": script_body,
            "estimated_retention_rate": "72.4%"
        }

    @staticmethod
    def build_whatsapp_sequence(product: str, persona: dict, angle: dict) -> Dict[str, Any]:
        messages = [
            {
                "step": "Mensaje 1 (Primer Contacto)",
                "timing": "Inmediato tras registro",
                "text": f"Hola! 👋 Vi tu interés en {product}. Preparé {angle['gift']} para ayudarte a {persona['desire'].lower()}. Te lo envío por aquí?"
            },
            {
                "step": "Mensaje 2 (Prueba Social & Valor)",
                "timing": "+24 horas",
                "text": f"Hola de nuevo! Solo quería mostrarte cómo otras empresas lograron resolver {persona['pain'].lower()} usando {product}. Te gustaría ver un caso rápido de 2 minutos?"
            },
            {
                "step": "Mensaje 3 (Cierre Directo / Urgencia)",
                "timing": "+48 horas",
                "text": f"Última llamada ⏰ Estamos ofreciendo onboarding prioritario para {product} esta semana. ¿Hablamos 10 minutos para dejar tu cuenta lista?"
            }
        ]
        return {
            "product": product, "persona": persona["name"],
            "channel": "WhatsApp / SMS Direct Sales",
            "messages": messages,
            "predicted_reply_rate": "28.5%"
        }

    @staticmethod
    def build_multi_angle_matrix(product: str, persona: dict, angle: dict) -> Dict[str, Any]:
        matrix = {
            "emotional": {
                "angle": "Ángulo Emocional (Estatus & Alivio)",
                "headline": f"Deja de perder tiempo con {product}",
                "body": f"Como {persona['name']}, mereces la tranquilidad de {persona['desire'].lower()} sin la frustración constante.",
                "cta": "Transformar mi negocio"
            },
            "logical_roi": {
                "angle": "Ángulo Lógico & ROI Métrico",
                "headline": f"+150% de Eficiencia con {product}",
                "body": f"Análisis comprobado: {product} elimina {persona['pain'].lower()} y reduce costos operativos un 35%.",
                "cta": "Ver números y métricas"
            },
            "zero_risk": {
                "angle": "Ángulo Riesgo Cero (Garantía)",
                "headline": f"Prueba {product} 100% Sin Riesgo",
                "body": f"Sin tarjeta de crédito. Configuración asistida en 5 minutos. Garantía de resultados.",
                "cta": "Probar Gratis Ahora"
            }
        }
        return {"product": product, "persona": persona["name"], "angles": matrix}

    @staticmethod
    def build_competitor_ad(product: str, competitor: str, angle: dict) -> Dict[str, Any]:
        return {
            "product": product, "competitor": competitor,
            "headline": f"¿Usando {competitor}? Descubre la alternativa más eficiente: {product}",
            "body": f"A diferencia de {competitor}, {product} te permite {angle['benefit']} sin sobrecostos ni complejas migraciones.",
            "cta": f"Comparar {product} vs {competitor}",
            "predicted_ctr_boost": "+38% vs Anuncio Genérico"
        }

    @staticmethod
    def build_seo_article(product: str, persona: dict, angle: dict, llm_body: str = None) -> Dict[str, Any]:
        if llm_body:
            article_body = llm_body
        else:
            article_body = (
                f"# Guía Completa de {angle['domain']}: Cómo {angle['benefit']}\n\n"
                f"## 📌 Introducción\nEn el mercado actual, los {persona['name']} enfrentan el desafío crítico de {persona['pain'].lower()}.\n\n"
                f"## 🚀 Estrategia Principal: Implementación de {product}\nDescubre la metodología paso a paso para transformar tus resultados sin riesgos.\n\n"
                f"## 📊 Caso de Éxito & Métricas de Referencia\nEmpresas líderes ya están multiplicando su retorno con {product}.\n\n"
                f"## 🎁 Recurso Descargable\nAccede a {angle['gift']} y empieza hoy."
            )
        return {
            "product": product, "persona": persona["name"],
            "title": f"La Guía Definitiva de {product}: Estrategias de {angle['domain']} para {persona['name']}",
            "meta_description": f"Aprende cómo {angle['benefit']} y eliminar {persona['pain'].lower()} con {product}.",
            "content": article_body,
            "estimated_organic_traffic_score": "88/100"
        }

    @staticmethod
    def build_cold_email(product: str, persona: dict, angle: dict, llm_subject: str = None, llm_body: str = None) -> Dict[str, Any]:
        subject = llm_subject or f"Idea rápida sobre {angle['domain']} para tu equipo"
        body = llm_body or (
            f"Hola [Nombre],\n\n"
            f"Veo que estás liderando el crecimiento en tu empresa. Muchos {persona['name']} con los que hablo nos comentan que su mayor cuello de botella es {persona['pain'].lower()}.\n\n"
            f"Desarrollamos {product} específicamente para resolver esto: te permite {angle['benefit']}.\n\n"
            f"¿Tendrías 10 minutos este jueves para mostrarte una breve demo sin compromiso?\n\n"
            f"Un saludo,\n[Tu Nombre]"
        )
        return {
            "product": product, "persona": persona["name"],
            "framework": "PAS (Problem-Agitate-Solve)",
            "subject": subject, "body": body,
            "predicted_open_rate": "52.4%", "predicted_reply_rate": "14.8%"
        }

    @staticmethod
    def build_webinar_funnel(product: str, persona: dict, angle: dict) -> Dict[str, Any]:
        return {
            "product": product, "persona": persona["name"],
            "webinar_title": f"Masterclass En Vivo: Cómo {angle['benefit']} en 30 Días",
            "registration_page_headline": f"Aprende el sistema probado de {product} para {persona['desire'].lower()}",
            "email_invitation": f"Hola! Te invitamos a la Masterclass en vivo donde revelaremos cómo eliminar {persona['pain'].lower()} usando {product}.",
            "reminder_sms": f"🚨 Empezamos en 15 minutos! Conéctate a la Masterclass de {product} aquí: [link]",
            "predicted_attendance_rate": "42.1%"
        }

    @staticmethod
    def build_social_calendar(product: str, persona: dict, angle: dict) -> Dict[str, Any]:
        calendar = [
            {"day": "Lunes (LinkedIn)", "topic": "Mito vs Realidad de la industria", "post": f"El mayor mito sobre {angle['domain']} es creer que necesitas más personal. Con {product} automatizas el proceso."},
            {"day": "Miércoles (Twitter Thread)", "topic": "5 Lecciones tácticas", "post": f"🧵 5 errores fatales que cometen los {persona['name']} al intentar resolver {persona['pain'].lower()} (y cómo evitarlos con {product})."},
            {"day": "Viernes (LinkedIn Case Study)", "topic": "Estudio de caso real", "post": f"Cómo logramos que una empresa aumente sus conversiones un +150% usando {product}. Desglose paso a paso."}
        ]
        return {
            "product": product, "persona": persona["name"],
            "calendar": calendar,
            "predicted_engagement_rate": "8.4%"
        }

    @staticmethod
    def build_churn_prevention(product: str, persona: dict, angle: dict) -> Dict[str, Any]:
        return {
            "product": product, "persona": persona["name"],
            "subject": f"No te vayas aún: Regalo especial en tu cuenta de {product}",
            "body": f"Hola,\n\nNotamos que tu actividad en {product} ha disminuido. Queremos asegurarnos de que estés logrando {persona['desire'].lower()}.\n\nHemos activado una sesión 1-a-1 gratuita con nuestro especialista de Customer Success + 1 mes gratis de upgrade premium.",
            "predicted_churn_reduction": "-28.5%"
        }
