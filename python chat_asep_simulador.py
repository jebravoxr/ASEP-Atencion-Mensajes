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



def crear_respuesta_chat(mensaje: str) -> tuple[str, dict, str]:
    """Genera una respuesta de demostración según las reglas locales de ASEP."""
    resultado = clasificar(mensaje)
    categoria = resultado["categoria"]
    respuesta = RESPUESTAS.get(categoria)

    if respuesta:
        return respuesta["texto"], resultado, respuesta["estado"]

    textos = {
        "capacitaciones": (
            "¡Hola! Gracias por escribir a ASEP. Para orientarte mejor sobre "
            "capacitaciones, indícanos qué curso, taller o tema te interesa. "
            "El equipo deberá confirmar la información."
        ),
        "oferta_capacitacion": (
            "¡Hola! Gracias por ofrecer una capacitación a la comunidad de ASEP. "
            "Compártenos el tema, la modalidad, la duración y las condiciones "
            "de tu propuesta. El equipo deberá evaluarla."
        ),
        "registro_marca": (
            "¡Hola! Gracias por escribir a ASEP. Para orientarte sobre el "
            "registro de marca, cuéntanos brevemente qué necesitas registrar. "
            "El equipo deberá revisar tu consulta antes de darte información específica."
        ),
        "alianzas_convenios": (
            "¡Hola! Gracias por tu interés en colaborar con ASEP. Cuéntanos "
            "brevemente qué tipo de alianza propones y cuáles serían sus objetivos. "
            "El equipo revisará la propuesta."
        ),
        "auspicios_eventos": (
            "¡Hola! Gracias por considerar a ASEP para tu iniciativa. "
            "Compártenos el nombre del evento, la fecha y el tipo de auspicio "
            "que propones. El equipo revisará la solicitud."
        ),
        "propuestas_comerciales": (
            "¡Hola! Gracias por contactar con ASEP y presentarnos tu propuesta. "
            "¿Podrías compartir un resumen del servicio o herramienta y cómo "
            "podría ayudar a nuestra comunidad? El equipo revisará el mensaje."
        ),
    }
    if categoria in textos:
        return textos[categoria], resultado, "PENDIENTE DE REVISIÓN HUMANA"

    return (
        "¡Hola! Gracias por escribir a ASEP. Para ayudarte correctamente, "
        "¿podrías contarnos un poco más sobre tu consulta? Tu mensaje queda "
        "pendiente de revisión por una persona del equipo.",
        resultado,
        "REQUIERE REVISIÓN HUMANA",
    )


def iniciar_chat() -> None:
    """Abre una ventana de chat independiente, inspirada en WhatsApp."""
    import tkinter as tk
    from tkinter import messagebox, scrolledtext, ttk

    BG = "#efeae2"
    GREEN = "#d9fdd3"
    WHITE = "#ffffff"
    DARK = "#111b21"
    MUTED = "#667781"
    TEAL = "#075e54"

    root = tk.Tk()
    root.title("ASEP Chat — Simulación local")
    root.geometry("1000x740")
    root.minsize(780, 580)
    root.configure(bg=BG)
    root.grid_columnconfigure(1, weight=1)
    root.grid_rowconfigure(0, weight=1)

    sidebar = tk.Frame(root, bg=WHITE, width=255)
    sidebar.grid(row=0, column=0, sticky="nsew")
    sidebar.grid_propagate(False)

    brand = tk.Frame(sidebar, bg=TEAL, height=88)
    brand.pack(fill="x")
    brand.pack_propagate(False)
    tk.Label(brand, text="ASEP", bg=TEAL, fg=WHITE,
             font=("Segoe UI", 19, "bold")).pack(anchor="w", padx=18, pady=(17, 0))
    tk.Label(brand, text="Asistente de prueba", bg=TEAL, fg="#d7f5ee",
             font=("Segoe UI", 9)).pack(anchor="w", padx=19)

    tk.Label(sidebar, text="CHATS", bg=WHITE, fg=MUTED,
             font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=18, pady=(20, 8))
    contact = tk.Frame(sidebar, bg="#f0f2f5", height=78)
    contact.pack(fill="x")
    contact.pack_propagate(False)
    tk.Label(contact, text="A", bg="#00a884", fg=WHITE,
             font=("Segoe UI", 17, "bold"), width=3).pack(side="left", padx=12, pady=15)
    names = tk.Frame(contact, bg="#f0f2f5")
    names.pack(side="left", fill="both", expand=True, pady=15)
    tk.Label(names, text="Asistente ASEP", bg="#f0f2f5", fg=DARK,
             font=("Segoe UI", 10, "bold")).pack(anchor="w")
    tk.Label(names, text="Simulación en este equipo", bg="#f0f2f5", fg=MUTED,
             font=("Segoe UI", 8)).pack(anchor="w", pady=(4, 0))

    tk.Label(
        sidebar,
        text="MODO DE DEMOSTRACIÓN\n\n"
             "• No envía WhatsApps reales\n"
             "• No utiliza una IA externa\n"
             "• Clasifica con reglas locales\n"
             "• Revisa antes de guardar ejemplos",
        justify="left", bg=WHITE, fg=MUTED,
        font=("Segoe UI", 9), wraplength=210
    ).pack(anchor="w", padx=18, pady=20)

    chat = tk.Frame(root, bg=BG)
    chat.grid(row=0, column=1, sticky="nsew")
    chat.grid_columnconfigure(0, weight=1)
    chat.grid_rowconfigure(1, weight=1)

    header = tk.Frame(chat, bg="#f0f2f5", height=72)
    header.grid(row=0, column=0, sticky="ew")
    header.grid_propagate(False)
    tk.Label(header, text="ASEP | Asistente virtual", bg="#f0f2f5", fg=DARK,
             font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=18, pady=(14, 0))
    tk.Label(header, text="En línea · entorno local de prueba", bg="#f0f2f5",
             fg=MUTED, font=("Segoe UI", 9)).pack(anchor="w", padx=18, pady=(3, 0))

    messages = scrolledtext.ScrolledText(
        chat, wrap="word", state="disabled", bg=BG, fg=DARK, relief="flat",
        borderwidth=0, padx=18, pady=16, font=("Segoe UI", 10),
        spacing1=3, spacing3=8
    )
    messages.grid(row=1, column=0, sticky="nsew")
    messages.tag_configure("system", foreground=MUTED, justify="center",
                           font=("Segoe UI", 9), spacing1=8, spacing3=12)
    messages.tag_configure("user", background=GREEN, lmargin1=220,
                           lmargin2=220, rmargin=12, spacing1=7, spacing3=7)
    messages.tag_configure("bot", background=WHITE, lmargin1=12,
                           lmargin2=12, rmargin=220, spacing1=7, spacing3=7)

    review_panel = tk.Frame(chat, bg="#fff8e1", padx=12, pady=8)
    review_panel.grid(row=2, column=0, sticky="ew")
    review_label = tk.Label(
        review_panel, text="La clasificación aparecerá aquí.",
        bg="#fff8e1", fg="#6d4c00", anchor="w",
        font=("Segoe UI", 9), wraplength=690, justify="left"
    )
    review_label.pack(fill="x")
    review_buttons = tk.Frame(review_panel, bg="#fff8e1")
    review_buttons.pack(anchor="w", pady=(6, 0))

    composer = tk.Frame(chat, bg="#f0f2f5", padx=12, pady=12)
    composer.grid(row=3, column=0, sticky="ew")
    composer.grid_columnconfigure(0, weight=1)
    entry = tk.Text(composer, height=3, wrap="word", font=("Segoe UI", 10),
                    relief="flat", padx=12, pady=10, undo=True)
    entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
    send_button = tk.Button(
        composer, text="Enviar", bg="#00a884", fg=WHITE,
        activebackground="#008f70", activeforeground=WHITE,
        relief="flat", font=("Segoe UI", 10, "bold"),
        padx=18, pady=10, cursor="hand2"
    )
    send_button.grid(row=0, column=1, sticky="s")

    last_message = {"text": "", "result": None}

    def append_message(text: str, role: str) -> None:
        messages.configure(state="normal")
        if role == "system":
            messages.insert("end", f"\n{text}\n", "system")
        else:
            messages.insert("end", text + "\n\n", "user" if role == "user" else "bot")
        messages.see("end")
        messages.configure(state="disabled")

    def update_review(resultado: dict, estado: str) -> None:
        categoria = resultado["categoria"]
        review_label.config(
            text=f"Categoría: {NOMBRES.get(categoria, categoria)}  |  Estado: {estado}\n"
                 f"Motivo: {resultado['motivo']}"
        )
        for widget in review_buttons.winfo_children():
            widget.destroy()

        def save_validated(category: str) -> None:
            original = last_message["text"]
            if not original:
                return
            guardar_ejemplo_validado(original, category)
            messagebox.showinfo(
                "Ejemplo guardado",
                "Se guardó una versión anonimizada como ejemplo revisado. "
                "Esto no modifica automáticamente las reglas del chatbot."
            )

        def send_to_waiting() -> None:
            original = last_message["text"]
            if original:
                guardar_en_espera(original, last_message["result"]["motivo"])
                messagebox.showinfo(
                    "Sala de espera",
                    "El mensaje anonimizado se guardó para revisión local."
                )

        tk.Button(review_buttons, text="Aprobar categoría",
                  command=lambda: save_validated(categoria),
                  bg="#d9fdd3", relief="flat", padx=8, pady=4).pack(side="left", padx=(0, 6))
        tk.Button(review_buttons, text="Enviar a revisión humana",
                  command=send_to_waiting, bg=WHITE, relief="flat",
                  padx=8, pady=4).pack(side="left", padx=(0, 6))

        categories = [c for c in NOMBRES if c != "desconocido"]
        selected = tk.StringVar(value=categoria if categoria in categories else categories[0])
        dropdown = ttk.Combobox(review_buttons, textvariable=selected, state="readonly",
                                width=27, values=categories)
        dropdown.pack(side="left", padx=(4, 6))

        def correct_category() -> None:
            save_validated(selected.get())
            review_label.config(
                text=f"Categoría corregida: {NOMBRES[selected.get()]} "
                     "(guardada como ejemplo revisado)."
            )

        tk.Button(review_buttons, text="Corregir", command=correct_category,
                  relief="flat", padx=8, pady=4).pack(side="left")

    def send_message(event=None):
        mensaje = entry.get("1.0", "end-1c").strip()
        if not mensaje:
            return "break"
        entry.delete("1.0", "end")
        append_message(mensaje, "user")
        texto, resultado, estado = crear_respuesta_chat(mensaje)
        last_message.update(text=mensaje, result=resultado)
        append_message(texto, "bot")
        update_review(resultado, estado)
        return "break"

    def clear_chat():
        messages.configure(state="normal")
        messages.delete("1.0", "end")
        messages.configure(state="disabled")
        review_label.config(text="La clasificación aparecerá aquí.")
        for widget in review_buttons.winfo_children():
            widget.destroy()
        last_message.update(text="", result=None)
        append_message("Chat reiniciado. Escribe un mensaje para probar el asistente.", "system")

    send_button.configure(command=send_message)
    entry.bind("<Control-Return>", send_message)
    entry.bind("<Return>", lambda event: "break")

    tk.Button(sidebar, text="Reiniciar conversación", command=clear_chat,
              bg="#f0f2f5", fg=DARK, relief="flat", pady=8).pack(
                  side="bottom", fill="x", padx=12, pady=14)

    append_message(
        "¡Hola! Soy el asistente de demostración de ASEP. Puedes escribirme "
        "como si fuera WhatsApp. Esta simulación usa reglas locales; revisa "
        "las respuestas antes de utilizarlas.",
        "bot"
    )
    append_message(
        "Prueba con: «Quiero afiliarme», «¿Dónde encuentro sus enlaces?» "
        "o «Quiero ofrecer una capacitación gratuita».",
        "system"
    )
    entry.focus_set()
    root.mainloop()


def main() -> None:
    iniciar_chat()


if __name__ == "__main__":
    main()
