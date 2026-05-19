# Actividad_en_clase_18_Mayo_2026
GitHub

# Nombre del proyecto: Chatbot de Habilidades para la Vida

Asistente de IA para apoyo emocional y desarrollo de habilidades personales usando OpenAI API y Flask.

---

## Objetivo

Crear un chatbot de apoyo emocional para los estudiantes universitarios. 

---

## Problema que resuelve

Brinda un apoyo extra a los estudiantes para que puedan manejar su vida estudiantil de una mejor forma.

---

## Público objetivo

Los estudiantes de la Universidad Nacional de Chimborazo. 

---

## Integrantes y roles

- Líder de Proyecto: Andy Nevarez

- Diseñador Digital: Juan Ruiz

- Documentador(es): Klever Castillo & William Macias

- Administrador GitHub: Pablo Teran

---

## Requisitos previos

- Python 3.8 o superior
- Cuenta en OpenAI (para obtener la API Key)
- Conexión a internet 

---

## Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/tu-usuario/chatbot-habilidades.git
cd chatbot-habilidades
```

### 2. Crear y activar entorno virtual

```bash
#  Windows:
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

Crea un archivo `.env` en la raíz del proyecto:

```
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxx
SECRET_KEY=tu-clave-secreta-aqui
```

**¿Cómo obtener OPENAI_API_KEY?**
1. Ve a [openai.com/api](https://openai.com/api)
2. Inicia sesión o registrate
3. Ve a "API keys" → “Create new key”
4. Copia la clave y pégala en .env 
**¿Cómo generar SECRET_KEY?**
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```
Copia el resultado y pégalo en .env junto a SECRET_KEY=


## Uso

### Iniciar el servidor

```bash
python chatbot_habilidades_backend.py
```

Abrirá automáticamente en: `http://localhost:5000`

### Funcionalidades

- **Chat en vivo**: Habla con el asistente
- **Descargar sesión**: Exporta la conversación a PDF
- **Info de sesión**: Ver detalles de la sesión actual
- **Nueva sesión**: Limpiar el chat

---

## Estructura del Proyecto

```
chatbot-habilidades/
├── chatbot.py    # Backend principal
├── crear_vectores.py                # Cargar vectores a la base de datos
├── templates/                         # Frontend
├── chroma_db/                        # Base de datos vectorial
├── documentacion/                    # Documentacion tecnica
├── imagenes/                         # Elementos visuales del proyecto
├── resources/                        # Material de entrenamiento el chatbot
├── .env                              # Variables secretas (NO SUBIR)
├── .gitignore                        # Archivos excluidos de Git
├── requirements.txt                  # Dependencias
└── README.md                         # Este archivo
```

---

## Seguridad

**IMPORTANTE:**
- NUNCA subas `.env` a GitHub 
- NUNCA compartas tu OPENAI_API_KEY
-  El `.gitignore` ya excluye `.env`

---

## Tecnologías

- **Backend**: Flask
- **IA**: OpenAI GPT-4o-mini
- **Frontend**: HTML5 + CSS3 + JavaScript
- **PDF**: ReportLab
- **Sesiones**: Flask Sessions (con cookies cifradas)

---

## Funciones principales

### `/chat` (POST)
- **Entrada**: `{"message": "tu mensaje"}`
- **Salida**: `{"reply": "respuesta del asistente", "session_id": "..."}`
- **Autenticación**: Automática por cookie

### `/export` (GET)
- **Función**: Descargar conversación en PDF
- **Autenticación**: Automática por cookie
- **Retorna**: Archivo PDF

### `/sessions` (GET)
- **Función**: Información de la sesión actual
- **Retorna**: `{"id": "...", "created_at": "...", "messages_count": N}`

### `/session` (GET)
- **Función**: Todos los mensajes de la sesión
- **Retorna**: Array de mensajes

---

## Troubleshooting

### Error: "ModuleNotFoundError: No module named 'flask'"
```bash
pip install -r requirements.txt
```

### Error: "OPENAI_API_KEY not found"
- Verifica que `.env` existe en la carpeta correcta
- Verifica que el archivo tiene: `OPENAI_API_KEY=sk-proj-...`


### La sesión se pierde al cerrar navegador
- Esto es normal, es un cache local del navegador
- El servidor guarda el historial en memoria

---

## Contribuir

¿Cambios que hacer?

1. Crea una rama: `git checkout -b mi-feature`
2. Haz cambios
3. Commit: `git commit -am "Descripción del cambio"`
4. Push: `git push origin mi-feature`
5. Crea un Pull Request en GitHub

---








