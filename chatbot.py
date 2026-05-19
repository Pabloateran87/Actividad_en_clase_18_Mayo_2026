# ===================================================================
# CHATBOT DE HABILIDADES PARA LA VIDA
# Sistema de asistencia psicológica-académica con RAG
# ===================================================================

from flask import Flask, render_template, request, jsonify, send_file, session
from flask_cors import CORS
from openai import OpenAI
from dotenv import load_dotenv
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import inch
import os
from io import BytesIO
from datetime import datetime
import uuid
 
# Importaciones para RAG (Recuperación de contexto desde PDFs)
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

# ===================================================================
# CONFIGURACIÓN INICIAL
# ===================================================================

load_dotenv()

app = Flask(__name__)
CORS(app, supports_credentials=True)
app.secret_key = os.getenv("SECRET_KEY")

# Cliente de OpenAI
cliente_openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Almacenamiento de conversaciones en memoria
sesiones = {}

# ===================================================================
# CONFIGURACIÓN DEL ASISTENTE
# ===================================================================

PRINCIPIOS = """
1. Escucha activa: valida emociones antes de orientar.
2. Empatía: lenguaje respetuoso y humano.
3. No juicio: no impone decisiones ni valores.
4. Autonomía: fomenta reflexión personal.
5. Límites éticos: no diagnósticos ni tratamientos.
6. Derivación responsable: sugiere ayuda profesional cuando corresponde.
"""

PROMPT_SISTEMA = f"""
Eres un asistente psicológico-académico orientado al desarrollo de habilidades para la vida en estudiantes universitarios.

PRINCIPIOS:
{PRINCIPIOS}

INSTRUCCIONES CRÍTICAS:
- Basa tus respuestas EXCLUSIVAMENTE en el material académico proporcionado
- SIEMPRE proporciona una estrategia o consejo práctico concreto
- Responde en 2-3 oraciones máximo (50-70 palabras)
- Usa lenguaje empático, claro y calmado
- Solo si no encuentras información en el material, usa tus conocimientos pero que esté relacionado con el material
- NUNCA des diagnósticos médicos o psiquiátricos
- Si detectas crisis, deriva inmediatamente a profesionales
"""

# ===================================================================
# MAPA DE CONOCIMIENTO
# ===================================================================

# Unidades temáticas y sus PDFs correspondientes
MAPA_UNIDADES = {
    "U1": {
        "nombre": "Inteligencia Emocional",
        "archivos": ["U1T1.pdf", "U1T2.pdf"]
    },
    "U2": {
        "nombre": "Resiliencia y Manejo del Estrés",
        "archivos": ["U2T1.pdf", "U2T2.pdf"]
    },
    "U3": {
        "nombre": "Liderazgo",
        "archivos": ["U3T1.pdf", "U3T2.pdf"]
    },
    "U4": {
        "nombre": "Pensamiento Creativo",
        "archivos": ["U4T1.pdf"]
    }
}

# Palabras clave para detectar situaciones de crisis
PALABRAS_CRISIS = [
    "suicidar", "morir", "suicidio", "no quiero vivir",
    "hacerme daño", "quitarme la vida", "autolesión", "cortarme"
]

# Mapeo de palabras clave a temas específicos
MAPA_INTENCIONES = [
    {
        "palabras_clave": ["ansioso", "ansiedad", "nervioso", "nerviosa"],
        "unidad": "U2",
        "tipo": "estrés"
    },
    {
        "palabras_clave": ["estrés", "estresado", "estresada", "agobiado", "sobrecargado"],
        "unidad": "U2",
        "tipo": "estrés"
    },
    {
        "palabras_clave": ["fracasé", "fallé", "fracaso", "error"],
        "unidad": "U1",
        "tipo": "reflexivo"
    },
    {
        "palabras_clave": ["comunicar", "comunicación", "expresar", "hablar"],
        "unidad": "U3",
        "tipo": "reflexivo"
    },
    {
        "palabras_clave": ["creativo", "creatividad", "ideas", "innovar"],
        "unidad": "U4",
        "tipo": "creativo"
    },
    {
        "palabras_clave": ["conocerme", "autoconocimiento", "quién soy"],
        "unidad": "U1",
        "tipo": "reflexivo"
    },
    {
        "palabras_clave": ["conflicto", "pelea", "discusión", "desacuerdo"],
        "unidad": "U3",
        "tipo": "reflexivo"
    },
    {
        "palabras_clave": ["líder", "liderazgo", "equipo", "grupo"],
        "unidad": "U3",
        "tipo": "reflexivo"
    },
    {
        "palabras_clave": ["emociones", "sentimientos", "sentir"],
        "unidad": "U1",
        "tipo": "reflexivo"
    },
    {
        "palabras_clave": ["resiliencia", "recuperar", "superar"],
        "unidad": "U2",
        "tipo": "reflexivo"
    },
    {
        "palabras_clave": ["hasta luego", "adios", "chao", "nos vemos"],
        "unidad": "U2",
        "tipo": "despedida"
    }
]

# Estilos de respuesta según el tipo de situación
ESTILOS_RESPUESTA = {
    "estrés": """
Responde con empatía y contención en 2-3 oraciones.
Ofrece UNA estrategia práctica clara basada en el material académico.
No hagas preguntas. Sé directo y de apoyo.
""",
    "reflexivo": """
Responde en 2-3 oraciones.
Da un consejo práctico basado en el material académico.
Termina con UNA pregunta reflexiva breve.
""",
    "creativo": """
Responde en 2-3 oraciones.
Da UN consejo concreto para estimular creatividad.
Usa un ejemplo simple del material académico.
""",
"despedida":"""
Identificar cuando el usuario intenta cerrar la conversación. Responde en 2 - 3 oraciones.
Responde con empatía y da ánimos. Cierra la conversación. No hagas preguntas ya."""
}

# ===================================================================
# FUNCIONES AUXILIARES
# ===================================================================

def detectar_crisis(texto):
    """
    Detecta si el mensaje contiene indicadores de crisis emocional.
    
    Args:
        texto (str): Mensaje del usuario
        
    Returns:
        bool: True si detecta crisis, False en caso contrario
    """
    texto_minuscula = texto.lower()
    return any(palabra in texto_minuscula for palabra in PALABRAS_CRISIS)


def detectar_intencion(texto):
    """
    Identifica el tema y tipo de respuesta adecuado según el mensaje.
    
    Args:
        texto (str): Mensaje del usuario
        
    Returns:
        dict: Información de la intención detectada o None
    """
    texto_minuscula = texto.lower()
    for intencion in MAPA_INTENCIONES:
        if any(palabra in texto_minuscula for palabra in intencion["palabras_clave"]):
            return intencion
    return None


def limitar_oraciones(texto, maximo=3):
    """
    Limita el texto a un número máximo de oraciones.
    
    Args:
        texto (str): Texto a limitar
        maximo (int): Número máximo de oraciones
        
    Returns:
        str: Texto limitado
    """
    import re
    oraciones = re.split(r'(?<=[.!?])\s+', texto.strip())
    
    if len(oraciones) > maximo:
        return ' '.join(oraciones[:maximo])
    
    return texto

# ===================================================================
# INICIALIZACIÓN DEL VECTOR STORE
# ===================================================================

# Cargar embeddings gratuitos de HuggingFace
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)

directorio_vectores = "./chroma_db"
almacen_vectores = None

# Intentar cargar el vector store desde disco
if os.path.exists(directorio_vectores) and os.path.exists(os.path.join(directorio_vectores, "chroma.sqlite3")):
    try:
        almacen_vectores = Chroma(
            persist_directory=directorio_vectores, 
            embedding_function=embeddings, 
            collection_name="life_skills"
        )
    except Exception as e:
        print(f"⚠️ Error al cargar vector store: {str(e)}")
        almacen_vectores = None

# ===================================================================
# RUTAS DE LA APLICACIÓN
# ===================================================================

@app.route("/")
def inicio():
    """Página principal del chatbot"""
    return render_template("chatbot_habilidades.html")


@app.route("/chat", methods=["POST"])
def chat():
    """
    Endpoint principal para procesar mensajes del usuario.
    
    Flujo:
    1. Detectar crisis
    2. Detectar intención del mensaje
    3. Recuperar contexto relevante de los PDFs
    4. Generar respuesta con OpenAI
    5. Guardar en historial
    """
    datos = request.json
    mensaje_usuario = datos.get("message", "").strip()
    
    if not mensaje_usuario:
        return jsonify({"error": "Mensaje vacío"}), 400

    # PASO 1: Detectar situaciones de crisis (prioridad máxima)
    if detectar_crisis(mensaje_usuario):
        return jsonify({
            "reply": (
                "Comprendo que estás pasando por un momento muy difícil. "
                "Es muy importante que hables con alguien que pueda ayudarte de inmediato. "
                "Te sugiero contactar con un profesional de salud mental, el servicio de bienestar universitario, "
                "o una línea de emergencia emocional disponible 24/7."
            )
        })

    try:
        # Gestión de sesiones
        if 'user_id' not in session:
            session['user_id'] = str(uuid.uuid4())
        
        id_sesion = session['user_id']
        
        if id_sesion not in sesiones:
            sesiones[id_sesion] = {
                "mensajes": [],
                "fecha_creacion": datetime.now()
            }

        sesion_usuario = sesiones[id_sesion]

        # PASO 2: Detectar intención (qué tema está consultando)
        intencion = detectar_intencion(mensaje_usuario)

        # PASO 3: Recuperar contexto relevante del material académico
        contexto = ""
        if almacen_vectores and intencion:
            # Buscar solo en los PDFs de la unidad correspondiente
            unidad = intencion["unidad"]
            archivos_unidad = MAPA_UNIDADES[unidad]["archivos"]
            
            recuperador = almacen_vectores.as_retriever(search_kwargs={"k": 2})
            documentos_relevantes = recuperador.invoke(mensaje_usuario)
            
            # Filtrar solo documentos de la unidad
            documentos_filtrados = [
                doc for doc in documentos_relevantes 
                if any(archivo in doc.metadata.get('source', '') for archivo in archivos_unidad)
            ]
            
            if documentos_filtrados:
                contexto = "\n\n".join([doc.page_content for doc in documentos_filtrados])
            else:
                contexto = "\n\n".join([doc.page_content for doc in documentos_relevantes[:2]])
                
        elif almacen_vectores:
            # Si no hay intención clara, buscar en todo el material
            recuperador = almacen_vectores.as_retriever(search_kwargs={"k": 2})
            documentos_relevantes = recuperador.invoke(mensaje_usuario)
            contexto = "\n\n".join([doc.page_content for doc in documentos_relevantes])

        # PASO 4: Construir el prompt para OpenAI
        mensajes_conversacion = [
            {"role": "system", "content": PROMPT_SISTEMA}
        ]

        # Agregar estilo de respuesta según la situación
        if intencion:
            tipo_respuesta = intencion["tipo"]
            mensajes_conversacion.append({
                "role": "system", 
                "content": ESTILOS_RESPUESTA[tipo_respuesta]
            })
        else:
            mensajes_conversacion.append({
                "role": "system", 
                "content": ESTILOS_RESPUESTA["reflexivo"]
            })
        
        # Agregar el material académico como contexto
        if contexto:
            mensajes_conversacion.append({
                "role": "system", 
                "content": f"MATERIAL ACADÉMICO (usa solo esta información):\n{contexto}"
            })
        
        # Agregar historial reciente (últimos 6 mensajes)
        historial_reciente = sesion_usuario["mensajes"][-6:]
        for msg in historial_reciente:
            mensajes_conversacion.append({
                "role": msg["rol"],
                "content": msg["contenido"]
            })
        
        # Agregar mensaje actual
        mensajes_conversacion.append({"role": "user", "content": mensaje_usuario})

        # PASO 5: Llamar a OpenAI
        respuesta = cliente_openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=mensajes_conversacion,
            temperature=0.6,  # Balance entre precisión y naturalidad
            max_tokens=150    # Respuestas concisas
        )

        respuesta_texto = respuesta.choices[0].message.content.strip()
        
        if not respuesta_texto:
            raise ValueError("No se obtuvo respuesta del modelo")

        # Limitar a máximo 3 oraciones
        respuesta_texto = limitar_oraciones(respuesta_texto, maximo=3)

        # PASO 6: Guardar en historial
        sesion_usuario["mensajes"].append({
            "rol": "user",
            "contenido": mensaje_usuario,
            "fecha": datetime.now().isoformat()
        })
        sesion_usuario["mensajes"].append({
            "rol": "assistant",
            "contenido": respuesta_texto,
            "fecha": datetime.now().isoformat()
        })

        return jsonify({"reply": respuesta_texto, "session_id": id_sesion})

    except Exception as e:
        mensaje_error = str(e)
        
        # Detectar error de cuota específicamente
        if "insufficient_quota" in mensaje_error or "429" in mensaje_error:
            return jsonify({
                "error": "⚠️ No hay créditos disponibles en OpenAI. Agrega créditos en: https://platform.openai.com/account/billing"
            }), 402
        
        return jsonify({"error": mensaje_error}), 500


@app.route("/exportar", methods=["GET"])
def exportar_sesion():
    """
    Exporta la conversación actual a un archivo PDF.
    """
    if 'user_id' not in session:
        return jsonify({"error": "No hay sesión activa"}), 400
    
    id_sesion = session['user_id']
    
    if id_sesion not in sesiones:
        return jsonify({"error": "Sesión no encontrada"}), 404

    sesion_usuario = sesiones[id_sesion]
    mensajes = sesion_usuario["mensajes"]

    # Crear PDF en memoria
    buffer_pdf = BytesIO()
    documento = SimpleDocTemplate(buffer_pdf, pagesize=letter, topMargin=0.5*inch)
    contenido = []
    estilos = getSampleStyleSheet()

    # Estilo del título
    estilo_titulo = ParagraphStyle(
        'TituloPersonalizado',
        parent=estilos['Heading1'],
        fontSize=16,
        textColor='#2c3e50',
        spaceAfter=12,
        alignment=1
    )

    # Estilo para mensajes del usuario
    estilo_usuario = ParagraphStyle(
        'MensajeUsuario',
        parent=estilos['Normal'],
        fontSize=11,
        textColor='#1e88e5',
        spaceAfter=6,
        leftIndent=20
    )

    # Estilo para mensajes del asistente
    estilo_asistente = ParagraphStyle(
        'MensajeAsistente',
        parent=estilos['Normal'],
        fontSize=11,
        textColor='#43a047',
        spaceAfter=6,
        leftIndent=20
    )

    # Agregar título y metadatos
    contenido.append(Paragraph("Reporte de Sesión - Asistente de Habilidades para la Vida", estilo_titulo))
    contenido.append(Spacer(1, 0.2*inch))

    fecha_sesion = sesion_usuario["fecha_creacion"].strftime("%d/%m/%Y %H:%M:%S")
    contenido.append(Paragraph(f"<b>Fecha:</b> {fecha_sesion}", estilos['Normal']))
    contenido.append(Paragraph(f"<b>ID:</b> {id_sesion}", estilos['Normal']))
    contenido.append(Spacer(1, 0.3*inch))

    contenido.append(Paragraph("<b>Conversación:</b>", estilos['Heading2']))
    contenido.append(Spacer(1, 0.1*inch))

    # Agregar mensajes
    for msg in mensajes:
        if msg["rol"] == "user":
            contenido.append(Paragraph(f"<b>Tú:</b> {msg['contenido']}", estilo_usuario))
        else:
            contenido.append(Paragraph(f"<b>Asistente:</b> {msg['contenido']}", estilo_asistente))
        contenido.append(Spacer(1, 0.15*inch))

    documento.build(contenido)
    buffer_pdf.seek(0)

    return send_file(
        buffer_pdf,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"sesion_{id_sesion}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    )


@app.route("/sesion", methods=["GET"])
def obtener_sesion():
    """
    Retorna los datos de la sesión actual.
    """
    if 'user_id' not in session:
        return jsonify({"error": "No hay sesión activa"}), 400
    
    id_sesion = session['user_id']
    
    if id_sesion not in sesiones:
        return jsonify({"error": "Sesión no encontrada"}), 404
    
    sesion_usuario = sesiones[id_sesion]
    
    return jsonify({
        "id": id_sesion,
        "fecha_creacion": sesion_usuario["fecha_creacion"].isoformat(),
        "cantidad_mensajes": len(sesion_usuario["mensajes"])
    })


# ===================================================================
# EJECUCIÓN DE LA APLICACIÓN
# ===================================================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🎓 CHATBOT DE HABILIDADES PARA LA VIDA")
    print("="*60)
    print(f"🔗 Accede en: http://localhost:5000")
    print(f"💾 Vector Store: {'✅ Cargado' if almacen_vectores else '⚠️ No encontrado'}")
    print("="*60 + "\n")
    
    app.run(debug=True, use_reloader=False)
