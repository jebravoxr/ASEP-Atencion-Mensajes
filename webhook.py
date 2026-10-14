"""Webhook local de pruebas para la integracion de ASEP con Meta.

No envia respuestas ni queda expuesto a internet: escucha solo en localhost.
"""

import hashlib
import hmac
import os
import secrets
from pathlib import Path

from flask import Flask, request

app = Flask(__name__)

# En desarrollo, los secretos se guardan en datos_locales, carpeta que ya esta
# excluida de Git por el .gitignore del proyecto.
CARPETA_DATOS = Path(__file__).with_name("datos_locales")
RUTA_TOKEN = CARPETA_DATOS / "meta_verify_token.txt"
RUTA_APP_SECRET = CARPETA_DATOS / "meta_app_secret.txt"


def cargar_o_crear_token() -> str:
    """Usa la variable de entorno o conserva un token local entre ejecuciones."""
    token_entorno = os.environ.get("META_VERIFY_TOKEN")
    if token_entorno:
        return token_entorno

    RUTA_TOKEN.parent.mkdir(parents=True, exist_ok=True)
    if RUTA_TOKEN.exists():
        token_guardado = RUTA_TOKEN.read_text(encoding="utf-8").strip()
        if token_guardado:
            return token_guardado

    token_nuevo = secrets.token_urlsafe(32)
    RUTA_TOKEN.write_text(token_nuevo, encoding="utf-8")
    return token_nuevo


VERIFY_TOKEN = cargar_o_crear_token()
APP_SECRET = os.environ.get("META_APP_SECRET")
if not APP_SECRET and RUTA_APP_SECRET.exists():
    APP_SECRET = RUTA_APP_SECRET.read_text(encoding="utf-8").strip() or None


def firma_valida(cuerpo: bytes, firma_recibida: str | None) -> bool:
    """Comprueba la firma SHA-256 enviada por Meta en cada evento POST."""
    if not APP_SECRET or not firma_recibida:
        return False

    firma_esperada = "sha256=" + hmac.new(
        APP_SECRET.encode("utf-8"), cuerpo, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(firma_esperada, firma_recibida)


@app.get("/health")
def estado_servidor():
    """Permite comprobar en el navegador que Flask esta funcionando."""
    return {"status": "ok", "modo": "prueba local"}, 200


@app.get("/webhook")
def verificar_webhook():
    """Responde al desafio de verificacion de Meta."""
    modo = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    desafio = request.args.get("hub.challenge")

    if modo == "subscribe" and token == VERIFY_TOKEN and desafio is not None:
        return desafio, 200

    return "Verificacion no autorizada", 403


@app.post("/webhook")
def recibir_evento():
    """Acepta solo eventos firmados por Meta y registra metadatos minimos."""
    cuerpo = request.get_data(cache=True)
    firma = request.headers.get("X-Hub-Signature-256", "")
    if not firma_valida(cuerpo, firma):
        return "Firma de Meta no valida o secreto no configurado", 401

    datos = request.get_json(silent=True)
    if not isinstance(datos, dict):
        return "JSON no valido", 400

    entradas = datos.get("entry", [])
    if not isinstance(entradas, list):
        return "Formato de evento no valido", 400

    print(
        "Evento recibido:",
        datos.get("object"),
        "| notificaciones:",
        len(entradas),
    )
    return "EVENT_RECEIVED", 200


if __name__ == "__main__":
    print("Token de verificacion local: datos_locales/meta_verify_token.txt")
    print("Secreto de la app de Meta: datos_locales/meta_app_secret.txt")
    print("No compartas esos archivos ni los subas a GitHub.")
    if not APP_SECRET:
        print("Falta meta_app_secret.txt: los eventos POST se rechazaran hasta configurarlo.")
    print("Comprobacion local: http://127.0.0.1:5000/health")
    print("Este servidor no envia respuestas y solo escucha en esta computadora.")
    app.run(host="127.0.0.1", port=5000, debug=False)
