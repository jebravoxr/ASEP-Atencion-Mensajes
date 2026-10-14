"""Asistente local de demostración para consultas de ASEP.

Clasifica mensajes y prepara borradores para revisión. No se conecta a WhatsApp,
guarda solo ejemplos anonimizados revisados y no envía respuestas.
"""

import json
import re
import unicodedata
from datetime import datetime
from pathlib import Path

LINKTREE = "https://linktr.ee/asep_peru"
ENLACE_MEMBRESIA = "https://asep.pe/membresia/#quieroserasociado"
ENLACE_AFILIACION = "https://asep.pe/registro/"
CARPETA_DATOS = Path(__file__).with_name("datos_locales")
ARCHIVO_ESPERA = CARPETA_DATOS / "sala_espera.json"
ARCHIVO_APRENDIZAJE = CARPETA_DATOS / "ejemplos_validados.json"

# Las respuestas se muestran como borradores. ASEP debe aprobar el texto antes
# de reutilizarlo con clientes o automatizar su envío.
RESPUESTAS = {
    "afiliacion": {
        "nombre": "Afiliación a ASEP",
        "estado": "PENDIENTE DE APROBACIÓN DE ASEP",
        "enlace": ENLACE_MEMBRESIA,
        "enlace_registro": ENLACE_AFILIACION,
        "texto": (
            "¡Hola! Gracias por escribir a ASEP. Si deseas ser miembro, "
            "puedes conocer más aquí: " + ENLACE_MEMBRESIA + "\n\n"
            "Si ya deseas iniciar tu registro, utiliza este enlace: " + ENLACE_AFILIACION + "\n\n"
            "Si tienes alguna consulta adicional, indícanosla "
            "para que el equipo de ASEP pueda orientarte."
        ),
    },
    "anuncios_difusion": {
        "nombre": "Anuncios y difusión en redes sociales",
        "estado": "PENDIENTE DE APROBACIÓN DE ASEP",
        "enlace": None,
        "texto": (
            "\u00a1Hola! Gracias por escribirnos. Compartimos nuestros anuncios, "
            "actividades y novedades en nuestras redes sociales. Puedes seguirnos en:\n"
            "Instagram: @asepperu\n"
            "TikTok: @asep_peru\n\n"
            "Si buscas una publicaci\u00f3n o informaci\u00f3n espec\u00edfica, "
            "cu\u00e9ntanos un poco m\u00e1s y te orientamos."
        ),
    },
    "consulta_general": {
        "nombre": "Información y enlaces generales",
        "estado": "PENDIENTE DE APROBACIÓN DE ASEP",
        "enlace": LINKTREE,
        "texto": (
            "¡Hola! Gracias por escribir a ASEP. Puedes encontrar nuestros "
            "enlaces e información general aquí: " + LINKTREE + "\n\n"
            "Si buscas información sobre un tema específico, cuéntanos cuál "
            "para orientarte mejor."
        ),
    },
}

REGLAS = {
    "afiliacion": ("afiliar", "afiliarme", "afiliacion", "asociarme", "ser socio", "hacerme socio", "ser miembro", "membresia", "ser asociado", "ser asociada", "registro", "formar parte de asep", "unirme a asep", "incorporarme a asep", "quiero ser parte", "requisitos para afiliarme"),
    "capacitaciones": ("capacitacion", "capacitaciones", "curso", "taller", "charla", "formacion", "webinar", "seminario", "masterclass", "programa formativo", "aprender sobre emprendimiento"),
    "anuncios_difusion": ("anuncio", "anuncios", "publicar", "publicacion", "publicaciones", "difundir", "difusion", "redes sociales", "instagram", "tiktok", "novedades", "convocatorias", "comunicados", "donde anuncian", "donde publican", "donde comparten"),
    "registro_marca": ("registro de marca", "registrar mi marca", "registrar una marca", "proteger mi marca", "marca", "nombre comercial", "logo", "logotipo", "indecopi"),
    "alianzas_convenios": ("alianza", "alianza estrategica", "convenio", "colaboracion", "colaborar", "trabajar juntos", "trabajar en conjunto", "coorganizar", "difusion cruzada", "intercambio de experiencias"),
    "auspicios_eventos": ("sponsor", "sponsors", "ser sponsor", "auspicio", "auspicios", "auspiciar", "patrocinio", "patrocinar", "auspiciador"),
    "propuestas_comerciales": ("reunion comercial", "herramienta", "servicio", "propuesta comercial", "ofrecemos", "demo", "solucion tecnologica", "presentar una propuesta", "reunion de presentacion", "agendar una reunion"),
}
CLAVES_GENERAL = ("cositas", "enlaces", "links", "informacion general", "info general")
CLAVES_OFRECIMIENTO = ("ofrecer", "ofrecemos", "oferta de", "brindar", "poner a disposicion")
CLAVES_GRATUIDAD = ("gratuita", "gratuito", "gratis", "voluntariado", "sin costo", "cero costos")
CLAVES_FORMACION = ("capacitacion", "capacitaciones", "taller", "curso", "formacion")
NOMBRES = {
    "afiliacion": "Afiliación a ASEP",
    "capacitaciones": "Capacitaciones",
    "oferta_capacitacion": "Oferta de capacitación gratuita o voluntaria",
    "anuncios_difusion": "Anuncios y difusión",
    "registro_marca": "Registro de marcas",
    "alianzas_convenios": "Alianzas y convenios",
    "auspicios_eventos": "Auspicios y eventos",
    "propuestas_comerciales": "Propuestas comerciales",
    "consulta_general": "Información general",
    "desconocido": "Consulta no identificada",
}


def normalizar(texto: str) -> str:
    """Normaliza tildes y signos sin cambiar el mensaje original."""
    texto = unicodedata.normalize("NFD", texto.lower())
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", " ", texto).strip()


def contiene_frase(texto: str, frase: str) -> bool:
    """Busca una palabra o frase completa, evitando coincidencias parciales."""
    texto_normalizado = " " + normalizar(texto) + " "
    frase_normalizada = " " + normalizar(frase) + " "
    return frase_normalizada in texto_normalizado


def clasificar(mensaje: str) -> dict:
    ofrece_formacion = any(contiene_frase(mensaje, clave) for clave in CLAVES_OFRECIMIENTO)
    menciona_formacion = any(contiene_frase(mensaje, clave) for clave in CLAVES_FORMACION)
    indica_gratuidad = any(contiene_frase(mensaje, clave) for clave in CLAVES_GRATUIDAD)

    # Distingue a quien ofrece una capacitación gratuita de quien busca una.
    if ofrece_formacion and menciona_formacion and indica_gratuidad:
        return {"categoria": "oferta_capacitacion", "motivo": "Se ofrece capacitación gratuita o voluntaria; requiere revisión humana."}
    coincidencias = [
        categoria
        for categoria, claves in REGLAS.items()
        if any(contiene_frase(mensaje, clave) for clave in claves)
    ]

    # En un mensaje sobre una herramienta ofrecida, la colaboración suele ser el canal comercial.
    if "propuestas_comerciales" in coincidencias and "alianzas_convenios" in coincidencias and any(contiene_frase(mensaje, clave) for clave in ("herramienta", "servicio", "demo")):
        return {"categoria": "propuestas_comerciales", "motivo": "Se presenta una herramienta o servicio y se propone colaboración; requiere revisión humana."}

    # Una invitación explícita a ser sponsor de un evento se clasifica como auspicio.
    if "auspicios_eventos" in coincidencias and "alianzas_convenios" in coincidencias and contiene_frase(mensaje, "evento") and any(contiene_frase(mensaje, clave) for clave in ("sponsor", "sponsors", "auspicio", "auspicios", "patrocinio")):
        return {"categoria": "auspicios_eventos", "motivo": "La propuesta principal es auspiciar un evento; requiere revisión humana."}
    # Los talleres/webinars pueden describir las actividades de la organización
    # que propone una alianza, no una segunda consulta de capacitación.
    if "alianzas_convenios" in coincidencias and set(coincidencias).issubset({"alianzas_convenios", "capacitaciones", "anuncios_difusion"}):
        return {"categoria": "alianzas_convenios", "motivo": "La propuesta principal es una alianza; las actividades mencionadas son contexto y el caso requiere revisión humana."}
    if len(coincidencias) > 1:
        return {"categoria": "desconocido", "motivo": "El mensaje parece incluir varios temas; debe revisarlo una persona."}
    if coincidencias:
        categoria = coincidencias[0]
        return {"categoria": categoria, "motivo": "Se detectaron palabras relacionadas con esta categoría."}
    if any(contiene_frase(mensaje, clave) for clave in CLAVES_GENERAL):
        return {"categoria": "consulta_general", "motivo": "El mensaje pide enlaces o información general."}
    return {"categoria": "desconocido", "motivo": "No se encontró una regla clara; debe revisarlo una persona."}


def mostrar_resultado(mensaje: str) -> dict:
    resultado = clasificar(mensaje)
    categoria = resultado["categoria"]
    print("\n--- Resultado ---")
    print("Categoría:", NOMBRES[categoria])
    print("Motivo:", resultado["motivo"])

    respuesta = RESPUESTAS.get(categoria)
    if respuesta:
        print("Estado:", respuesta["estado"])
        if respuesta.get("enlace"):
            print("Enlace candidato:", respuesta["enlace"])
        print("\nBorrador de respuesta (no enviado):")
        print(respuesta["texto"])
    else:
        print("Acción: derivar a revisión humana; no hay una respuesta específica aprobada.")
        print("Borrador interno: una persona de ASEP debe revisar este mensaje y responder por este canal.")
    print("\nEl programa solo muestra un borrador: no envía WhatsApps.\n")
    return resultado


def anonimizar_para_guardar(mensaje: str) -> str:
    """Quita datos de contacto comunes antes de guardar un ejemplo local."""
    texto = re.sub(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b", "[CORREO]", mensaje)
    texto = re.sub(r"https?://\S+|www\.\S+", "[ENLACE]", texto, flags=re.IGNORECASE)
    texto = re.sub(r"(?i)\b(?:mi nombre es|me llamo|te saluda)\s+[\wÁÉÍÓÚÜÑáéíóúüñ'-]+(?:\s+[\wÁÉÍÓÚÜÑáéíóúüñ'-]+){0,2}", "[NOMBRE]", texto)
    texto = re.sub(r"(?<!\d)(?:\+?\d[\d\s().-]{6,}\d)(?!\d)", "[TELÉFONO]", texto)
    return re.sub(r"\s+", " ", texto).strip()


def leer_lista(ruta: Path) -> list:
    if not ruta.exists():
        return []
    try:
        datos = json.loads(ruta.read_text(encoding="utf-8"))
        return datos if isinstance(datos, list) else []
    except (OSError, json.JSONDecodeError):
        print(f"No se pudo leer {ruta.name}; el archivo se conserva sin modificar.")
        return []


def guardar_lista(ruta: Path, datos: list) -> None:
    CARPETA_DATOS.mkdir(exist_ok=True)
    temporal = ruta.with_suffix(".tmp")
    temporal.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")
    temporal.replace(ruta)


def buscar_ejemplos_parecidos(mensaje: str, limite: int = 3) -> list:
    """Sugiere categorías de ejemplos revisados; nunca clasifica por sí solo."""
    palabras_vacias = {"para", "como", "hola", "buenas", "gracias", "asep", "quiero", "puedo", "por", "una", "que", "los", "las", "del", "con", "sobre"}
    palabras_nuevas = set(normalizar(mensaje).split()) - palabras_vacias
    if not palabras_nuevas:
        return []

    candidatos = []
    for ejemplo in leer_lista(ARCHIVO_APRENDIZAJE):
        palabras_ejemplo = set(normalizar(ejemplo.get("mensaje", "")).split()) - palabras_vacias
        if not palabras_ejemplo:
            continue
        similitud = len(palabras_nuevas & palabras_ejemplo) / len(palabras_nuevas | palabras_ejemplo)
        candidatos.append((similitud, ejemplo))
    candidatos.sort(key=lambda item: item[0], reverse=True)
    return [(similitud, ejemplo) for similitud, ejemplo in candidatos[:limite] if similitud >= 0.12]


def elegir_categoria() -> str | None:
    categorias = [categoria for categoria in NOMBRES if categoria != "desconocido"]
    print("\nElige la categoría correcta:")
    for indice, categoria in enumerate(categorias, start=1):
        print(f"{indice}. {NOMBRES[categoria]}")
    opcion = input("Número de categoría (0 para cancelar): ").strip()
    if not opcion.isdigit() or opcion == "0":
        return None
    indice = int(opcion) - 1
    return categorias[indice] if 0 <= indice < len(categorias) else None


def mostrar_borrador_categoria(categoria: str) -> None:
    respuesta = RESPUESTAS.get(categoria)
    if respuesta:
        print(f"\nBorrador disponible ({respuesta['estado']}):")
        print(respuesta["texto"])
        print("Este borrador no se envía desde el programa.")
    else:
        print("Esta categoría no tiene una respuesta aprobada; requiere atención humana.")


def guardar_ejemplo_validado(mensaje: str, categoria: str) -> None:
    texto_seguro = anonimizar_para_guardar(mensaje)
    ejemplos = leer_lista(ARCHIVO_APRENDIZAJE)
    if any(e.get("mensaje") == texto_seguro and e.get("categoria") == categoria for e in ejemplos):
        print("Ese ejemplo ya está guardado como revisado.")
        return
    ejemplos.append({
        "mensaje": texto_seguro,
        "categoria": categoria,
        "revisado_en": datetime.now().astimezone().isoformat(timespec="seconds"),
    })
    guardar_lista(ARCHIVO_APRENDIZAJE, ejemplos)
    print("Ejemplo anonimizado guardado. Se usará para sugerir casos parecidos; no cambia reglas automáticamente.")


def guardar_en_espera(mensaje: str, motivo: str) -> None:
    pendientes = leer_lista(ARCHIVO_ESPERA)
    pendientes.append({
        "mensaje": anonimizar_para_guardar(mensaje),
        "motivo": motivo,
        "estado": "pendiente",
        "recibido_en": datetime.now().astimezone().isoformat(timespec="seconds"),
    })
    guardar_lista(ARCHIVO_ESPERA, pendientes)
    print("Mensaje anonimizado agregado a la sala de espera local.")


def registrar_revision(mensaje: str, resultado: dict) -> None:
    categoria = resultado["categoria"]
    similares = buscar_ejemplos_parecidos(mensaje)
    if similares:
        print("Casos revisados que podrían parecerse (solo sugerencias):")
        for similitud, ejemplo in similares:
            print(f"- {NOMBRES.get(ejemplo['categoria'], ejemplo['categoria'])} ({similitud:.0%} de palabras compartidas)")

    if categoria == "desconocido":
        print("\n¿Qué hacemos con este mensaje?")
        print("1. Corregir la categoría y guardar como ejemplo revisado")
        print("2. Dejarlo en sala de espera para una persona")
        print("0. No guardar")
        opcion = input("Elige una opción: ").strip()
        if opcion == "1":
            nueva_categoria = elegir_categoria()
            if nueva_categoria:
                guardar_ejemplo_validado(mensaje, nueva_categoria)
                mostrar_borrador_categoria(nueva_categoria)
            else:
                print("No se guardó ningún cambio.")
        elif opcion == "2":
            guardar_en_espera(mensaje, resultado["motivo"])
        return

    print("\n¿La categoría detectada es correcta?")
    print("1. Sí; guardar ejemplo revisado")
    print("2. Corregir categoría y guardar")
    print("3. Dejar en sala de espera")
    print("0. No guardar")
    opcion = input("Elige una opción: ").strip()
    if opcion == "1":
        guardar_ejemplo_validado(mensaje, categoria)
    elif opcion == "2":
        nueva_categoria = elegir_categoria()
        if nueva_categoria:
            guardar_ejemplo_validado(mensaje, nueva_categoria)
            mostrar_borrador_categoria(nueva_categoria)
    elif opcion == "3":
        guardar_en_espera(mensaje, "Revisión humana solicitada por el operador.")


def revisar_sala_espera() -> None:
    pendientes = leer_lista(ARCHIVO_ESPERA)
    indices = [i for i, item in enumerate(pendientes) if item.get("estado") == "pendiente"]
    if not indices:
        print("La sala de espera está vacía.")
        return
    print("\nMensajes pendientes (texto anonimizado):")
    for numero, indice in enumerate(indices, start=1):
        print(f"{numero}. {pendientes[indice]['mensaje'][:180]}")
    opcion = input("Número para revisar (0 para volver): ").strip()
    if not opcion.isdigit() or opcion == "0":
        return
    posicion = int(opcion) - 1
    if not 0 <= posicion < len(indices):
        print("Número no válido.")
        return
    indice = indices[posicion]
    categoria = elegir_categoria()
    if not categoria:
        return
    item = pendientes[indice]
    item["estado"] = "revisado"
    item["categoria"] = categoria
    item["revisado_en"] = datetime.now().astimezone().isoformat(timespec="seconds")
    guardar_lista(ARCHIVO_ESPERA, pendientes)
    guardar_ejemplo_validado(item["mensaje"], categoria)
    mostrar_borrador_categoria(categoria)


def mostrar_opciones() -> None:
    print("\nCategorías reconocidas:")
    for categoria in NOMBRES:
        respuesta = RESPUESTAS.get(categoria)
        if respuesta:
            detalle = "borrador disponible; pendiente de aprobación"
        elif categoria == "desconocido":
            detalle = "revisión humana"
        else:
            detalle = "revisión humana; falta respuesta/enlace aprobado"
        print(f"- {NOMBRES[categoria]}: {detalle}")


def main() -> None:
    print("=== Asistente local de ASEP ===")
    print("1. Analizar un mensaje y preparar una respuesta")
    print("2. Ver categorías y disponibilidad")
    print("3. Revisar sala de espera")
    print("0. Salir")
    while True:
        opcion = input("\nElige una opción: ").strip()
        if opcion == "0":
            print("Hasta luego.")
            break
        if opcion == "1":
            mensaje = input("Pega aquí el mensaje recibido: ").strip()
            if mensaje:
                resultado = mostrar_resultado(mensaje)
                registrar_revision(mensaje, resultado)
            else:
                print("No ingresaste un mensaje.")
        elif opcion == "2":
            mostrar_opciones()
        elif opcion == "3":
            revisar_sala_espera()
        else:
            print("Opción no válida. Escribe 1, 2, 3 o 0.")


if __name__ == "__main__":
    main()
