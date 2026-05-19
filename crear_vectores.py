# ===================================================================
# SCRIPT PARA CREAR EL VECTOR STORE
# Ejecutar UNA SOLA VEZ antes de iniciar el chatbot
# ===================================================================

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
import os

# Lista de archivos PDF a procesar
archivos_pdf = [
    "U1T1.pdf",
    "U1T2.pdf", 
    "U2T1.pdf", 
    "U2T2.pdf", 
    "U3T1.pdf",
    "U3T2.pdf", 
    "U4T1.pdf"
]

documentos = []

# ===================================================================
# PASO 1: Cargar todos los PDFs
# ===================================================================

print("📄 Cargando archivos PDF...\n")

for archivo in archivos_pdf:
    if os.path.exists(archivo):
        try:
            # Cargar el PDF
            cargador = PyPDFLoader(archivo)
            docs = cargador.load()
            documentos.extend(docs)
            print(f"  ✅ {archivo} - {len(docs)} páginas")
        except Exception as e:
            print(f"  ❌ {archivo} - Error: {str(e)}")
    else:
        print(f"  ⚠️ {archivo} - No encontrado")

# Verificar que se hayan cargado documentos
if not documentos:
    print("\n❌ No se cargaron documentos. Verifica que los PDFs estén en el directorio.")
    exit(1)

print(f"\n✅ Total: {len(documentos)} documentos cargados\n")

# ===================================================================
# PASO 2: Crear embeddings (representación vectorial del texto)
# ===================================================================

print("🔧 Creando embeddings (puede tardar 2-3 minutos)...\n")

# Usar modelo gratuito de HuggingFace que soporta español
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)

# ===================================================================
# PASO 3: Dividir documentos en fragmentos más pequeños
# ===================================================================

print("✂️ Dividiendo documentos en fragmentos...\n")

divisor_texto = RecursiveCharacterTextSplitter(
    chunk_size=1000,      # Tamaño de cada fragmento
    chunk_overlap=200     # Superposición entre fragmentos
)

fragmentos = divisor_texto.split_documents(documentos)
print(f"✅ {len(fragmentos)} fragmentos creados\n")

# ===================================================================
# PASO 4: Crear y guardar el vector store
# ===================================================================

print("💾 Creando vector store...\n")

almacen_vectores = Chroma.from_documents(
    documents=fragmentos,
    embedding=embeddings,
    persist_directory="./chroma_db",
    collection_name="life_skills"
)

# ===================================================================
# COMPLETADO
# ===================================================================

print("="*60)
print("🎉 ¡Vector store creado exitosamente!")
print("="*60)
print("📁 Ubicación: ./chroma_db")
print("✅ Ahora puedes ejecutar el chatbot: python chatbot.py")
print("="*60 + "\n")
