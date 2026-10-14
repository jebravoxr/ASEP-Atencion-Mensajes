"""Webhook de pruebas de ASEP para Meta WhatsApp Cloud API.

Este servidor verifica los webhooks entrantes; no responde ni envía WhatsApps.
En Railway, configura META_VERIFY_TOKEN y META_APP_SECRET como variables privadas.
"""
import hashlib
import hmac
import logging
import os
import secrets
from pathlib import Path

from flask import Flask, jsonify, request

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 1024 * 1024  # Limita solicitudes a 1 MB.
logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO").upper())
logger = logging.getLogger("asep.webhook")

CARPETA_DATOS = Path(__file__).with_name("datos_locales")
RUTA_TOKEN = CARPETA_DATOS / "meta_verify_token.txt"
RUTA_APP_SECRET = CARPETA_DATOS / "meta_app_secret.txt"
EN_RAILWAY = bool(os.environ.get("RAILWAY_PROJECT_ID") or os.environ.get("RAILWAY_SERVICE_ID"))
PORT = int(os.environ.get("PORT", "5000"))


def cargar_token_verificacion() -> str | None:
    """En Railway usa solo variables privadas; localmente permite guardar un token."""
    token = os.environ.get("META_VERIFY_TOKEN", "").strip()
    if token:
        return token
    if EN_RAILWAY:
        return None

    CARPETA_DATOS.mkdir(parents=True, exist_ok=True)
    if RUTA_TOKEN.exists():
        guardado = RUTA_TOKEN.read_text(encoding="utf-8").strip()
        if guardado:
            return guardado
    nuevo = secrets.token_urlsafe(32)
    RUTA_TOKEN.write_text(nuevo, encoding="utf-8")
    return nuevo


def cargar_secreto_app() -> str | None:
    """Prioriza el entorno; el archivo local solo se usa fuera de Railway."""
    secreto = os.environ.get("META_APP_SECRET", "").strip()
    if secreto:
        return secreto
    if not EN_RAILWAY and RUTA_APP_SECRET.exists():
        return RUTA_APP_SECRET.read_text(encoding="utf-8").strip() or None
    return None


VERIFY_TOKEN = cargar_token_verificacion()
APP_SECRET = cargar_secreto_app()


def validar_firma(cuerpo: bytes, firma_recibida: str) -> bool:
    """Valida X-Hub-Signature-256 usando el cuerpo HTTP original."""
    if not APP_SECRET or not firma_recibida:
        return False
    esperada = "sha256=" + hmac.new(
        APP_SECRET.encode("utf-8"), cuerpo, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(esperada, firma_recibida)


@app.get("/")
def inicio():
    return "ASEP webhook activo. No se envian respuestas.", 200


@app.get("/health")
def health():
    """Informa disponibilidad sin revelar secretos ni datos de clientes."""
    configurado = bool(VERIFY_TOKEN and APP_SECRET)
    return jsonify(
        status="ok" if configurado else "configuracion_pendiente",
        modo="railway" if EN_RAILWAY else "local",
        webhook_configurado=configurado,
    ), 200


@app.get("/webhook")
def verificar_webhook():
    """Verificación del callback solicitada por Meta."""
    modo = request.args.get("hub.mode", "")
    token = request.args.get("hub.verify_token", "")
    desafio = request.args.get("hub.challenge", "")
    if not VERIFY_TOKEN:
        return "META_VERIFY_TOKEN no configurado", 503
    if (
        modo == "subscribe"
        and desafio
        and hmac.compare_digest(token, VERIFY_TOKEN)
    ):
        return desafio, 200
    return "Verificacion no autorizada", 403


@app.post("/webhook")
def recibir_evento():
    """Acepta eventos firmados y registra solo conteos, nunca mensajes o teléfonos."""
    if not APP_SECRET:
        return "META_APP_SECRET no configurado", 503

    cuerpo = request.get_data(cache=True)
    firma = request.headers.get("X-Hub-Signature-256", "")
    if not validar_firma(cuerpo, firma):
        return "Firma de Meta no valida", 401

    datos = request.get_json(silent=True)
    if not isinstance(datos, dict):
        return "JSON no valido", 400

    entradas = datos.get("entry")
    if not isinstance(entradas, list):
        return "Formato de evento no valido", 400

    cantidad_mensajes = 0
    for entrada in entradas:
        if not isinstance(entrada, dict):
            continue
        cambios = entrada.get("changes", [])
        if not isinstance(cambios, list):
            continue
        for cambio in cambios:
            if not isinstance(cambio, dict):
                continue
            valor = cambio.get("value", {})
            if isinstance(valor, dict):
                mensajes = valor.get("messages", [])
                if isinstance(mensajes, list):
                    cantidad_mensajes += len(mensajes)

    logger.info(
        "Webhook firmado recibido: tipo=%s entradas=%d mensajes=%d",
        datos.get("object", "desconocido"),
        len(entradas),
        cantidad_mensajes,
    )
    # Meta necesita una respuesta rápida; aquí todavía no se envía respuesta al usuario.
    return "EVENT_RECEIVED", 200


@app.errorhandler(413)
def solicitud_demasiado_grande(_error):
    return "Solicitud demasiado grande", 413


if __name__ == "__main__":
    if EN_RAILWAY:
        logger.info("Iniciando en Railway en 0.0.0.0:%d", PORT)
    else:
        logger.info("Token local: %s", RUTA_TOKEN)
        logger.info("El endpoint no envia respuestas de WhatsApp.")
        logger.info("Comprobacion local: http://127.0.0.1:%d/health", PORT)
        if not APP_SECRET:
            logger.warning("META_APP_SECRET no configurado; los POST se rechazaran.")
    # El Start Command python webhook.py sirve para la prueba inicial.
    # Para producción, usar un servidor WSGI como Gunicorn.
    app.run(host="0.0.0.0", port=PORT, debug=False)
