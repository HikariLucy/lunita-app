import os
import sqlite3
import psycopg2
from psycopg2.extras import DictCursor
from datetime import date, datetime, timedelta
from typing import List, Optional
from collections import Counter

from dotenv import load_dotenv
from google import genai
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.responses import HTMLResponse, StreamingResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi import Request
import bcrypt
from jose import JWTError, jwt
from pydantic import BaseModel, Field, field_validator, EmailStr
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
import io
import json
from pywebpush import webpush, WebPushException
from apscheduler.schedulers.background import BackgroundScheduler

# Cargar variables de entorno
load_dotenv()

# Configurar Gemini
client = None
if os.getenv("GEMINI_API_KEY"):
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Configuración Base de Datos
DATABASE_NAME = "lunita.db"
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

IS_POSTGRES = bool(DATABASE_URL)

def ejecutar_query(cursor, query, params=()):
    if IS_POSTGRES:
        query = query.replace("?", "%s")
    cursor.execute(query, params)
import os
import sqlite3
import psycopg2
from psycopg2.extras import DictCursor
from datetime import date, datetime, timedelta
from typing import List, Optional
from collections import Counter

from dotenv import load_dotenv
from google import genai
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.responses import HTMLResponse, StreamingResponse, FileResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi import Request
import bcrypt
from jose import JWTError, jwt
from pydantic import BaseModel, Field, field_validator, EmailStr
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
import io
import json
from pywebpush import webpush, WebPushException
from apscheduler.schedulers.background import BackgroundScheduler
import weasyprint
import secrets

# Cargar variables de entorno
load_dotenv()

# Configurar Gemini
client = None
if os.getenv("GEMINI_API_KEY"):
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Configuración Base de Datos
DATABASE_NAME = "lunita.db"
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

IS_POSTGRES = bool(DATABASE_URL)

def ejecutar_query(cursor, query, params=()):
    if IS_POSTGRES:
        query = query.replace("?", "%s")
    cursor.execute(query, params)

def init_db():
    if IS_POSTGRES:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS usuarios (
                        id SERIAL PRIMARY KEY,
                        username TEXT UNIQUE NOT NULL,
                        email TEXT UNIQUE NOT NULL,
                        hashed_password TEXT NOT NULL,
                        es_irregular BOOLEAN DEFAULT FALSE,
                        pin_seguridad TEXT,
                        push_subscription TEXT,
                        hora_recordatorio_pastilla TEXT
                    )
                """)
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS registros_diarios (
                        id SERIAL PRIMARY KEY,
                        fecha TEXT NOT NULL,
                        dia_del_ciclo INTEGER NOT NULL,
                        flujo TEXT NOT NULL,
                        animo TEXT NOT NULL,
                        sintomas TEXT NOT NULL,
                        user_id INTEGER NOT NULL DEFAULT 1,
                        relaciones BOOLEAN DEFAULT FALSE,
                        tomo_pastilla BOOLEAN DEFAULT FALSE,
                        tomo_vitaminas BOOLEAN DEFAULT FALSE,
                        durmio_bien BOOLEAN DEFAULT FALSE,
                        UNIQUE(fecha, user_id)
                    )
                """)
                conn.commit()
                
            try:
                with conn.cursor() as cursor:
                    cursor.execute("ALTER TABLE usuarios ADD COLUMN es_irregular BOOLEAN DEFAULT FALSE")
                conn.commit()
            except Exception:
                conn.rollback()

            try:
                with conn.cursor() as cursor:
                    cursor.execute("ALTER TABLE usuarios ADD COLUMN pin_seguridad TEXT")
                conn.commit()
            except Exception:
                conn.rollback()

            try:
                with conn.cursor() as cursor:
                    cursor.execute("ALTER TABLE usuarios ADD COLUMN push_subscription TEXT")
                conn.commit()
            except Exception:
                conn.rollback()

            try:
                with conn.cursor() as cursor:
                    cursor.execute("ALTER TABLE usuarios ADD COLUMN hora_recordatorio_pastilla TEXT")
                conn.commit()
            except Exception:
                conn.rollback()

            try:
                with conn.cursor() as cursor:
                    cursor.execute("ALTER TABLE usuarios ADD COLUMN token_pareja TEXT")
                conn.commit()
            except Exception:
                conn.rollback()

            try:
                with conn.cursor() as cursor:
                    cursor.execute("ALTER TABLE registros_diarios ADD COLUMN relaciones BOOLEAN DEFAULT FALSE")
                conn.commit()
            except Exception:
                pass

            try:
                with conn.cursor() as cursor:
                    cursor.execute("ALTER TABLE registros_diarios ADD COLUMN tomo_pastilla BOOLEAN DEFAULT FALSE")
                conn.commit()
            except Exception:
                pass

            try:
                with conn.cursor() as cursor:
                    cursor.execute("ALTER TABLE registros_diarios ADD COLUMN tomo_vitaminas BOOLEAN DEFAULT FALSE")
                conn.commit()
            except Exception:
                pass

            try:
                with conn.cursor() as cursor:
                    cursor.execute("ALTER TABLE registros_diarios ADD COLUMN durmio_bien BOOLEAN DEFAULT FALSE")
                conn.commit()
            except Exception:
                pass

            try:
                with conn.cursor() as cursor:
                    cursor.execute("ALTER TABLE registros_diarios ADD COLUMN temperatura_basal NUMERIC")
                conn.commit()
            except Exception:
                conn.rollback()
                
        return
    else:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
    
    # Crear tabla de usuarios
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            hashed_password TEXT NOT NULL,
            es_irregular BOOLEAN DEFAULT FALSE,
            pin_seguridad TEXT,
            push_subscription TEXT,
            hora_recordatorio_pastilla TEXT,
            token_pareja TEXT
        )
    """)
    
    try:
        cursor.execute("ALTER TABLE usuarios ADD COLUMN es_irregular BOOLEAN DEFAULT FALSE")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE usuarios ADD COLUMN pin_seguridad TEXT")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE usuarios ADD COLUMN push_subscription TEXT")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE usuarios ADD COLUMN hora_recordatorio_pastilla TEXT")
    except sqlite3.OperationalError:
        pass
        
    try:
        cursor.execute("ALTER TABLE usuarios ADD COLUMN token_pareja TEXT")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE registros_diarios ADD COLUMN relaciones BOOLEAN DEFAULT FALSE")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE registros_diarios ADD COLUMN tomo_pastilla BOOLEAN DEFAULT FALSE")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE registros_diarios ADD COLUMN tomo_vitaminas BOOLEAN DEFAULT FALSE")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE registros_diarios ADD COLUMN durmio_bien BOOLEAN DEFAULT FALSE")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE registros_diarios ADD COLUMN temperatura_basal NUMERIC")
    except sqlite3.OperationalError:
        pass

    # Migrar registros_diarios para soportar multi-usuario y evitar colisiones de fechas
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='registros_diarios_v2'")
    if not cursor.fetchone():
        cursor.execute("""
            CREATE TABLE registros_diarios_v2 (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha TEXT NOT NULL,
                dia_del_ciclo INTEGER NOT NULL,
                flujo TEXT NOT NULL,
                animo TEXT NOT NULL,
                sintomas TEXT NOT NULL,
                user_id INTEGER NOT NULL DEFAULT 1,
                relaciones BOOLEAN DEFAULT FALSE,
                tomo_pastilla BOOLEAN DEFAULT FALSE,
                tomo_vitaminas BOOLEAN DEFAULT FALSE,
                durmio_bien BOOLEAN DEFAULT FALSE,
                temperatura_basal NUMERIC,
                UNIQUE(fecha, user_id)
            )
        """)
        # Revisar si la tabla vieja
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='registros_diarios'")
        if cursor.fetchone():
            cursor.execute("INSERT OR IGNORE INTO registros_diarios_v2 (id, fecha, dia_del_ciclo, flujo, animo, sintomas, relaciones, tomo_pastilla, tomo_vitaminas, durmio_bien, temperatura_basal) SELECT id, fecha, dia_del_ciclo, flujo, animo, sintomas, relaciones, tomo_pastilla, tomo_vitaminas, durmio_bien, temperatura_basal FROM registros_diarios")
            cursor.execute("DROP TABLE registros_diarios")
            
        cursor.execute("ALTER TABLE registros_diarios_v2 RENAME TO registros_diarios")

    conn.commit()
    conn.close()

# Inicialización de FastAPI
app = FastAPI(
    title="Lunita API",
    description="API para el seguimiento del bienestar, nutrición y salud mental durante el ciclo menstrual.",
    version="1.0.0"
)

# Configuración de CORS para permitir la conexión desde un frontend en HTML/JS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite todos los orígenes para entornos de desarrollo
    allow_credentials=False,
    allow_methods=["*"],  # Permite todos los métodos (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],
)

templates = Jinja2Templates(directory=".")

import os
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

import asyncio
import random
from datetime import date, timedelta

def crear_datos_demo(db):
    cursor = db.cursor()
    ejecutar_query(cursor, "SELECT * FROM usuarios WHERE username = 'lunita'")
    user = cursor.fetchone()
    
    if not user:
        hashed_password = get_password_hash('lunita')
        ejecutar_query(cursor, "INSERT INTO usuarios (username, email, hashed_password) VALUES (?, ?, ?)", 
                       ('lunita', 'lunita@demo.com', hashed_password))
        db.commit()
        # Handle postgres id retrieval
        if IS_POSTGRES:
            ejecutar_query(cursor, "SELECT id FROM usuarios WHERE username = 'lunita'")
            user_id = cursor.fetchone()[0]
        else:
            user_id = cursor.lastrowid
    else:
        user_id = user["id"]
        
    ejecutar_query(cursor, "DELETE FROM registros_diarios WHERE user_id = ?", (user_id,))
    db.commit()
    
    hoy = date.today()
    inicio_ciclo_actual = hoy - timedelta(days=13)
    inicio_ciclo_anterior = inicio_ciclo_actual - timedelta(days=28)
    inicio_ciclo_muy_anterior = inicio_ciclo_anterior - timedelta(days=28)
    
    sintomas_pool = ["Ninguno", "Cólicos", "Sensibilidad en el pecho", "Dolor de cabeza", "Inflamación", "Antojos dulces"]
    
    for i in range(60, -1, -1):
        fecha_registro = hoy - timedelta(days=i)
        
        if fecha_registro >= inicio_ciclo_actual:
            dia_del_ciclo = (fecha_registro - inicio_ciclo_actual).days + 1
        elif fecha_registro >= inicio_ciclo_anterior:
            dia_del_ciclo = (fecha_registro - inicio_ciclo_anterior).days + 1
        else:
            dia_del_ciclo = (fecha_registro - inicio_ciclo_muy_anterior).days + 1
            
        flujo = "Ninguno"
        if 1 <= dia_del_ciclo <= 2:
            flujo = "Abundante"
        elif 3 <= dia_del_ciclo <= 4:
            flujo = "Moderado"
        elif dia_del_ciclo == 5:
            flujo = "Ligero"
            
        if 1 <= dia_del_ciclo <= 5:
            animo = random.choice(["Cansada", "Triste", "Sensible"])
        elif 6 <= dia_del_ciclo <= 11:
            animo = random.choice(["Feliz", "Enérgica", "Motivada"])
        elif 12 <= dia_del_ciclo <= 16:
            animo = random.choice(["Enérgica", "Feliz", "Radiante"])
        elif 17 <= dia_del_ciclo <= 23:
            animo = random.choice(["Normal", "Tranquila", "Cansada"])
        else:
            animo = random.choice(["Irritable", "Sensible", "Triste", "Cansada"])
            
        if flujo != "Ninguno" and random.random() < 0.7:
            sintomas = "Cólicos"
        elif dia_del_ciclo > 24 and random.random() < 0.6:
            sintomas = random.choice(["Inflamación", "Antojos dulces", "Sensibilidad en el pecho"])
        else:
            sintomas = "Ninguno" if random.random() < 0.8 else random.choice(sintomas_pool)
            
        ejecutar_query(cursor, 
            """
            INSERT INTO registros_diarios (fecha, dia_del_ciclo, flujo, animo, sintomas, user_id, relaciones)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                fecha_registro.isoformat(),
                dia_del_ciclo,
                flujo,
                animo,
                sintomas,
                user_id,
                False
            )
        )
    db.commit()
    print("Datos demo de 'lunita' regenerados exitosamente.")

async def reset_demo_user_loop():
    while True:
        try:
            if IS_POSTGRES:
                conn = psycopg2.connect(DATABASE_URL)
                conn.cursor_factory = DictCursor
            else:
                conn = sqlite3.connect(DATABASE_NAME)
                conn.row_factory = sqlite3.Row
                
            try:
                crear_datos_demo(conn)
            finally:
                conn.close()
        except Exception as e:
            print(f"Error resetting demo user: {e}")
            
        await asyncio.sleep(12 * 3600) # 12 horas

# --- TAREAS PROGRAMADAS (APScheduler) ---
scheduler = BackgroundScheduler()

def verificar_habitos_diarios():
    from datetime import datetime
    hora_actual = datetime.now().strftime("%H:%M")
    hoy = date.today().isoformat()
    # Abrimos una conexión nueva para el hilo del scheduler
    if IS_POSTGRES:
        conn = psycopg2.connect(DATABASE_URL)
        conn.cursor_factory = DictCursor
    else:
        conn = sqlite3.connect(DATABASE_NAME)
        conn.row_factory = sqlite3.Row
        
    try:
        cursor = conn.cursor()
        # Seleccionamos usuarias con hora exacta y cruzamos con registros de hoy
        query = """
            SELECT u.id, r.tomo_pastilla 
            FROM usuarios u
            LEFT JOIN registros_diarios r ON u.id = r.user_id AND r.fecha = %s
            WHERE u.hora_recordatorio_pastilla = %s
        """ if IS_POSTGRES else """
            SELECT u.id, r.tomo_pastilla 
            FROM usuarios u
            LEFT JOIN registros_diarios r ON u.id = r.user_id AND r.fecha = ?
            WHERE u.hora_recordatorio_pastilla = ?
        """
        cursor.execute(query, (hoy, hora_actual))
        filas = cursor.fetchall()
        
        for fila in filas:
            user_id = fila["id"]
            tomo_pastilla = fila["tomo_pastilla"]
            
            # Si no hay registro (tomo_pastilla is None) o si tomo_pastilla es False
            if tomo_pastilla is None or not tomo_pastilla:
                enviar_notificacion_push(
                    user_id, 
                    "¡Hora de tu pastilla mágica! 💊✨", 
                    "Lunita te recuerda tomar tu anticonceptivo. ¡Regístralo para mantener tu racha!", 
                    conn
                )
    except Exception as e:
        print(f"Error en verificar_habitos_diarios: {e}")
    finally:
        conn.close()

def generar_alerta_semanal():
    print("Ejecutando tarea programada: generar_alerta_semanal...")
    if IS_POSTGRES:
        conn = psycopg2.connect(DATABASE_URL)
        conn.cursor_factory = DictCursor
    else:
        conn = sqlite3.connect(DATABASE_NAME)
        conn.row_factory = sqlite3.Row
        
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, email FROM usuarios")
        usuarios = cursor.fetchall()
        
        hace_7_dias = (date.today() - timedelta(days=7)).isoformat()
        
        for u in usuarios:
            try:
                # 1. Obtener registros de la semana
                ejecutar_query(cursor, """
                    SELECT fecha, dia_del_ciclo, flujo, animo, sintomas, temperatura_basal 
                    FROM registros_diarios 
                    WHERE user_id = ? AND fecha >= ?
                    ORDER BY fecha ASC
                """, (u["id"], hace_7_dias))
                registros = cursor.fetchall()
                
                # 2. Si no hay registros, enviar push amable y saltar
                if not registros:
                    enviar_notificacion_push(
                        u["id"], 
                        "🌙 ¡Lunita te extraña!", 
                        "Esta semana no hemos sabido de ti. Vuelve a escribir en tu diario para no perder el hilo de tu magia.", 
                        conn
                    )
                    continue
                
                # 3. Formatear datos
                resumen = f"Registros de los últimos 7 días de {u['username']}:\n"
                for r in registros:
                    resumen += f"- Fecha {r['fecha']} (Día {r['dia_del_ciclo']}): Flujo {r['flujo']}, Ánimo {r['animo']}, Síntomas: {r['sintomas']}, Temp: {r['temperatura_basal']}°C\n"
                    
                # 4. System Instruction para Gemini
                system_instruction = (
                    "Eres Lunita. Recibirás el registro semanal de la usuaria. "
                    "Redacta un correo electrónico (en formato HTML básico y limpio, usando colores pastel en línea) "
                    "resumiendo cómo estuvo su semana hormonalmente, felicitándola por sus buenos hábitos y "
                    "dándole un consejo cálido y experto para la semana que comienza. Mantén el tono de amiga experta."
                )
                
                # 5. Llamada a Gemini
                if client:
                    response = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=resumen,
                        config=genai.types.GenerateContentConfig(
                            system_instruction=system_instruction,
                            temperature=0.7,
                        ),
                    )
                    html_content = response.text.replace("```html", "").replace("```", "").strip()
                else:
                    html_content = f"<h1>Hola {u['username']}</h1><p>Parece que la IA no está conectada.</p>"
                    
                # 6. Envío del correo usando FastAPI-Mail (asíncrono)
                async def enviar_correo_async(destinatario, html_body):
                    message = MessageSchema(
                        subject="🌙 Tu Magia Semanal: Análisis de Lunita ✨",
                        recipients=[destinatario],
                        body=html_body,
                        subtype=MessageType.html
                    )
                    fm = FastMail(conf)
                    await fm.send_message(message)
                
                # Ejecutar el corutina en el hilo actual de forma segura
                asyncio.run(enviar_correo_async(u["email"], html_content))
                print(f"Correo enviado exitosamente a {u['email']}")
                
                # Enviar push avisando que el correo llegó
                enviar_notificacion_push(
                    u["id"], 
                    "💌 Tu Análisis Semanal está listo", 
                    "Revisa tu correo electrónico para leer el resumen mágico de tu semana.", 
                    conn
                )
                
            except Exception as loop_e:
                print(f"Error procesando usuaria {u['id']}: {loop_e}")
                
    except Exception as e:
        print(f"Error general en generar_alerta_semanal: {e}")
    finally:
        conn.close()

# Ejecutar la creación de tablas al iniciar la aplicación
@app.on_event("startup")
async def startup_event():
    init_db()
    asyncio.create_task(reset_demo_user_loop())
    
    # Iniciar tareas programadas
    scheduler.add_job(verificar_habitos_diarios, 'cron', minute='*')
    scheduler.add_job(generar_alerta_semanal, 'cron', day_of_week='sun', hour=10, minute=0)
    scheduler.start()
    print("APScheduler iniciado.")

@app.on_event("shutdown")
def shutdown_event():
    scheduler.shutdown()
    print("APScheduler detenido.")

@app.get("/")
def raiz():
    return FileResponse('index.html')

@app.get("/app", response_class=HTMLResponse)
@app.get("/index.html", response_class=HTMLResponse)
def get_index():
    with open("index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read(), status_code=200)

@app.get("/manifest.json")
def get_manifest():
    from fastapi.responses import FileResponse
    import os
    if os.path.exists("manifest.json"):
        return FileResponse("manifest.json", media_type="application/manifest+json")
    return {"error": "Manifest not found"}

@app.get("/sw.js")
def get_sw():
    from fastapi.responses import FileResponse
    import os
    if os.path.exists("sw.js"):
        return FileResponse("sw.js", media_type="application/javascript")
    return {"error": "Service worker not found"}

@app.get("/icon-192x192.png")
def get_icon_192():
    import os
    if os.path.exists("icon-192x192.png"):
        return FileResponse("icon-192x192.png", media_type="image/png")
    return {"error": "Icon not found"}

@app.get("/icon-512x512.png")
def get_icon_512():
    import os
    if os.path.exists("icon-512x512.png"):
        return FileResponse("icon-512x512.png", media_type="image/png")
    return {"error": "Icon not found"}

# Dependencia para obtener la conexión de base de datos
def get_db():
    if IS_POSTGRES:
        conn = psycopg2.connect(DATABASE_URL)
        conn.cursor_factory = DictCursor
        try:
            yield conn
        finally:
            conn.close()
    else:
        conn = sqlite3.connect(DATABASE_NAME, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

# --- CONFIGURACIÓN DE CORREO (FastAPI-Mail) ---
EMAIL_USER = os.getenv("EMAIL_USER", "tu_correo@gmail.com")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "tu_contraseña_de_aplicación")

conf = ConnectionConfig(
    MAIL_USERNAME=EMAIL_USER,
    MAIL_PASSWORD=EMAIL_PASSWORD,
    MAIL_FROM=EMAIL_USER,
    MAIL_PORT=587,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)

# --- SISTEMA DE AUTENTICACIÓN ---
SECRET_KEY = os.getenv("SECRET_KEY", "secreto_super_kawaii_luna_12345")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7 # 7 días

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/token")

def verify_password(plain_password, hashed_password):
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def get_password_hash(password):
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(token: str = Depends(oauth2_scheme), db: sqlite3.Connection = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    cursor = db.cursor()
    ejecutar_query(cursor, "SELECT * FROM usuarios WHERE username = ?", (username,))
    user = cursor.fetchone()
    if user is None:
        raise credentials_exception
    return dict(user)

# Modelos Pydantic para Auth
class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    es_irregular: bool = False

class Token(BaseModel):
    access_token: str
    token_type: str

class RecuperarPassword(BaseModel):
    email: str

@app.post("/api/registro", status_code=status.HTTP_201_CREATED)
def crear_usuario(user: UserCreate, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    ejecutar_query(cursor, "SELECT * FROM usuarios WHERE username = ? OR email = ?", (user.username, user.email))
    if cursor.fetchone():
        raise HTTPException(status_code=400, detail="El nombre de usuario o email ya está registrado.")
    
    hashed_password = get_password_hash(user.password)
    try:
        ejecutar_query(cursor, "INSERT INTO usuarios (username, email, hashed_password, es_irregular) VALUES (?, ?, ?, ?)", 
                       (user.username, user.email, hashed_password, user.es_irregular))
        db.commit()
        return {"mensaje": "Usuario creado exitosamente 🌸"}
    except sqlite3.Error:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error interno al registrar usuario.")

@app.post("/api/token", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    ejecutar_query(cursor, "SELECT * FROM usuarios WHERE username = ?", (form_data.username,))
    user = cursor.fetchone()
    
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/api/recuperar-password")
async def recuperar_password(data: RecuperarPassword, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    ejecutar_query(cursor, "SELECT * FROM usuarios WHERE email = ?", (data.email,))
    user = cursor.fetchone()
    if not user:
        return {"mensaje": "Si el correo existe, enviaremos un enlace de recuperación. 💌"}
    
    # Generar contraseña temporal segura
    import secrets
    import string
    alphabet = string.ascii_letters + string.digits
    nueva_password = ''.join(secrets.choice(alphabet) for i in range(8))
    
    # Actualizar en la base de datos
    hashed_password = get_password_hash(nueva_password)
    ejecutar_query(cursor, "UPDATE usuarios SET hashed_password = ? WHERE id = ?", (hashed_password, user["id"]))
    db.commit()
    
    html_content = f"""
    <div style="background-color: #FFF8F0; padding: 40px; border-radius: 20px; font-family: sans-serif; text-align: center; color: #4A3E4D; border: 2px solid #FFC6FF; max-width: 500px; margin: auto;">
        <h2 style="color: #B28DFF;">¡Hola Mágica! 🌙</h2>
        <p>Recibimos una solicitud para restablecer tu contraseña en Lunita.</p>
        <p>Tu nueva contraseña temporal es:</p>
        <div style="background: white; padding: 15px; border-radius: 10px; font-size: 24px; letter-spacing: 2px; font-weight: bold; color: #B28DFF; margin: 20px auto; width: max-content; border: 1px dashed #FFC6FF;">{nueva_password}</div>
        <p>Por favor, ingresa con esta contraseña y cámbiala desde la sección de configuración (engranaje) una vez dentro.</p>
        <p style="margin-top: 30px; font-size: 0.8rem; color: #7A6F80;">Si no solicitaste esto, alguien más intentó acceder. Te recomendamos cambiar tu contraseña pronto. 🤫</p>
    </div>
    """

    message = MessageSchema(
        subject="Recupera tu Magia en Lunita ✨",
        recipients=[data.email],
        body=html_content,
        subtype=MessageType.html
    )

    try:
        fm = FastMail(conf)
        await fm.send_message(message)
        return {"mensaje": f"Se ha enviado un correo mágico a {data.email} con instrucciones. ✨"}
    except Exception as e:
        print(f"Error enviando correo SMTP: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Uy, hubo un problema enviando el correo. ¿Están bien tus credenciales SMTP en el .env?"
        )

class PinUpdate(BaseModel):
    pin: str = Field(..., min_length=4, max_length=10)

class PinVerify(BaseModel):
    pin: str

@app.post("/api/usuario/pin")
def configurar_pin(data: PinUpdate, db: sqlite3.Connection = Depends(get_db), current_user: dict = Depends(get_current_user)):
    cursor = db.cursor()
    hashed_pin = get_password_hash(data.pin)
    try:
        ejecutar_query(cursor, "UPDATE usuarios SET pin_seguridad = ? WHERE id = ?", (hashed_pin, current_user["id"]))
        db.commit()
        return {"mensaje": "PIN de seguridad configurado exitosamente 🔒✨"}
    except sqlite3.Error as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error interno al guardar el PIN.")

@app.get("/api/usuario/check-pin")
def check_pin(db: sqlite3.Connection = Depends(get_db), current_user: dict = Depends(get_current_user)):
    return {"has_pin": bool(current_user.get("pin_seguridad"))}

@app.post("/api/usuario/verificar-pin")
def verificar_pin(data: PinVerify, db: sqlite3.Connection = Depends(get_db), current_user: dict = Depends(get_current_user)):
    hashed_pin = current_user.get("pin_seguridad")
    if not hashed_pin or not verify_password(data.pin, hashed_pin):
        raise HTTPException(status_code=401, detail="PIN incorrecto")
    return {"mensaje": "PIN verificado correctamente"}

@app.post("/api/usuario/recuperar-pin")
async def recuperar_pin(db: sqlite3.Connection = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if not current_user.get("pin_seguridad"):
        raise HTTPException(status_code=400, detail="No tienes un PIN configurado.")
    
    import secrets
    import string
    nuevo_pin = ''.join(secrets.choice(string.digits) for i in range(4))
    
    cursor = db.cursor()
    hashed_pin = get_password_hash(nuevo_pin)
    ejecutar_query(cursor, "UPDATE usuarios SET pin_seguridad = ? WHERE id = ?", (hashed_pin, current_user["id"]))
    db.commit()
    
    html_content = f"""
    <div style="background-color: #FFF8F0; padding: 40px; border-radius: 20px; font-family: sans-serif; text-align: center; color: #4A3E4D; border: 2px solid #FFC6FF; max-width: 500px; margin: auto;">
        <h2 style="color: #B28DFF;">¡Tranquila, aquí está tu nuevo PIN! 🌙</h2>
        <p>Tu nuevo PIN temporal de seguridad es:</p>
        <div style="background: white; padding: 15px; border-radius: 10px; font-size: 32px; letter-spacing: 8px; font-weight: bold; color: #B28DFF; margin: 20px auto; width: max-content; border: 1px dashed #FFC6FF;">{nuevo_pin}</div>
        <p>Entra con este PIN y luego cámbialo en la sección de configuración si lo deseas.</p>
    </div>
    """

    message = MessageSchema(
        subject="Tu nuevo PIN mágico en Lunita ✨",
        recipients=[current_user["email"]],
        body=html_content,
        subtype=MessageType.html
    )

    try:
        fm = FastMail(conf)
        await fm.send_message(message)
        return {"mensaje": f"Se ha enviado un correo a {current_user['email']} con tu nuevo PIN temporal. 💌"}
    except Exception as e:
        print(f"Error enviando correo SMTP: {e}")
        # En caso de error de correo (ej. credenciales faltantes), igual devolvemos éxito para la prueba 
        # (Idealmente debería fallar, pero para entornos de desarrollo sin smtp configurado, lo mostramos)
        return {"mensaje": f"Modo Dev: No se pudo enviar el correo, pero tu nuevo PIN es {nuevo_pin} (Configura SMTP en .env)"}

@app.get("/api/usuario/perfil")
def get_perfil(current_user: dict = Depends(get_current_user)):
    return {
        "username": current_user.get("username"),
        "email": current_user.get("email"),
        "es_irregular": current_user.get("es_irregular"),
        "hora_recordatorio_pastilla": current_user.get("hora_recordatorio_pastilla")
    }

class ConfigUsuario(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    hora_recordatorio_pastilla: Optional[str] = None

@app.put("/api/usuario/configuracion")
async def actualizar_configuracion(data: ConfigUsuario, db: sqlite3.Connection = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        current_username: str = payload.get("sub")
        if current_username is None:
            raise HTTPException(status_code=401, detail="Token inválido")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")
        
    cursor = db.cursor()
    ejecutar_query(cursor, "SELECT * FROM usuarios WHERE username = ?", (current_username,))
    user = cursor.fetchone()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
    updates = []
    params = []
    
    if data.username:
        ejecutar_query(cursor, "SELECT id FROM usuarios WHERE username = ? AND id != ?", (data.username, user["id"]))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Este nombre de usuario ya está en uso.")
        updates.append("username = ?")
        params.append(data.username)
        
    if data.email:
        ejecutar_query(cursor, "SELECT id FROM usuarios WHERE email = ? AND id != ?", (data.email, user["id"]))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Este correo ya está registrado por otra cuenta.")
        updates.append("email = ?")
        params.append(data.email)
        
    if data.password:
        updates.append("hashed_password = ?")
        params.append(get_password_hash(data.password))
        
    if data.hora_recordatorio_pastilla is not None:
        updates.append("hora_recordatorio_pastilla = ?")
        params.append(data.hora_recordatorio_pastilla)
        
    if not updates:
        return {"mensaje": "No se realizaron cambios."}
        
    params.append(user["id"])
    query = f"UPDATE usuarios SET {', '.join(updates)} WHERE id = ?"
    
    try:
        ejecutar_query(cursor, query, tuple(params))
        db.commit()
        
        # Enviar correo de notificación
        email_destino = data.email if data.email else user["email"]
        html_content = f"""
        <div style="background-color: #FFF8F0; padding: 40px; border-radius: 20px; font-family: sans-serif; text-align: center; color: #4A3E4D; border: 2px solid #FFC6FF; max-width: 500px; margin: auto;">
            <h2 style="color: #B28DFF;">¡Configuración Actualizada! 🌸</h2>
            <p>Hola <strong>{data.username or user['username']}</strong>,</p>
            <p>Te escribimos para avisarte que los datos de tu cuenta en Lunita han sido actualizados exitosamente.</p>
            <p style="margin-top: 30px; font-size: 0.8rem; color: #7A6F80;">Si tú no realizaste este cambio, por favor contacta a soporte o recupera tu contraseña inmediatamente.</p>
        </div>
        """
        
        message = MessageSchema(
            subject="Actualización de Cuenta en Lunita 🌸",
            recipients=[email_destino],
            body=html_content,
            subtype=MessageType.html
        )
        fm = FastMail(conf)
        await fm.send_message(message)
        
        return {"mensaje": "¡Datos actualizados exitosamente! ✨"}
    except Exception as e:
        db.rollback()
        print(f"Error actualizando usuario: {e}")
        raise HTTPException(status_code=500, detail="Error interno al actualizar los datos.")

# Modelos de validación con Pydantic
class RegistroDiarioBase(BaseModel):
    fecha: date = Field(..., description="Fecha del registro en formato YYYY-MM-DD")
    dia_del_ciclo: int = Field(..., ge=1, le=40, description="Día del ciclo menstrual (usualmente de 1 a 35 o 40)")
    flujo: str = Field(..., min_length=1, description="Nivel de flujo: Ninguno, Ligero, Moderado, Abundante")
    animo: str = Field(..., min_length=1, description="Estado de ánimo predominante")
    sintomas: str = Field(..., min_length=1, description="Síntomas físicos o emocionales experimentados")
    relaciones: bool = False
    tomo_pastilla: bool = False
    tomo_vitaminas: bool = False
    durmio_bien: bool = False
    temperatura_basal: Optional[float] = Field(None, description="Temperatura basal en °C")

    @field_validator("fecha", mode="before")
    def parse_fecha(cls, value):
        if isinstance(value, str):
            try:
                return date.fromisoformat(value)
            except ValueError:
                raise ValueError("La fecha debe tener el formato YYYY-MM-DD")
        return value

class RegistroDiarioCreate(RegistroDiarioBase):
    pass

class RegistroDiarioUpdate(BaseModel):
    fecha: Optional[date] = None
    dia_del_ciclo: Optional[int] = Field(None, ge=1, le=40)
    flujo: Optional[str] = None
    animo: Optional[str] = None
    sintomas: Optional[str] = None
    relaciones: Optional[bool] = None
    tomo_pastilla: Optional[bool] = None
    tomo_vitaminas: Optional[bool] = None
    durmio_bien: Optional[bool] = None
    temperatura_basal: Optional[float] = None

    @field_validator("fecha", mode="before")
    def parse_fecha(cls, value):
        if value is None:
            return None
        if isinstance(value, str):
            try:
                return date.fromisoformat(value)
            except ValueError:
                raise ValueError("La fecha debe tener el formato YYYY-MM-DD")
        return value

class RegistroDiario(RegistroDiarioBase):
    id: int

    class Config:
        from_attributes = True

# --- ENDPOINTS PROTEGIDOS ---

@app.post("/api/registros", response_model=RegistroDiario, status_code=status.HTTP_201_CREATED)
def crear_registro(registro: RegistroDiarioBase, db: sqlite3.Connection = Depends(get_db), current_user: dict = Depends(get_current_user)):
    cursor = db.cursor()
    fecha_str = registro.fecha.isoformat()
    
    # Verificar si ya existe un registro para esa fecha y usuario
    ejecutar_query(cursor, "SELECT id FROM registros_diarios WHERE fecha = ? AND user_id = ?", (fecha_str, current_user["id"]))
    if cursor.fetchone():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe un registro para la fecha {fecha_str}."
        )
        
    try:
        ejecutar_query(cursor, """
            INSERT INTO registros_diarios (fecha, dia_del_ciclo, flujo, animo, sintomas, user_id, relaciones, tomo_pastilla, tomo_vitaminas, durmio_bien, temperatura_basal)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                registro.fecha.isoformat(),
                registro.dia_del_ciclo,
                registro.flujo,
                registro.animo,
                registro.sintomas,
                current_user["id"],
                registro.relaciones,
                registro.tomo_pastilla,
                registro.tomo_vitaminas,
                registro.durmio_bien,
                registro.temperatura_basal
            )
        )
        db.commit()
        nuevo_id = cursor.lastrowid
        
        # Obtener el registro recién insertado
        ejecutar_query(cursor, "SELECT * FROM registros_diarios WHERE id = ?", (nuevo_id,))
        row = cursor.fetchone()
        return dict(row)
    except sqlite3.Error as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al guardar el registro en la base de datos: {str(e)}"
        )

@app.get("/api/registros", response_model=List[RegistroDiario])
def listar_registros(db: sqlite3.Connection = Depends(get_db), current_user: dict = Depends(get_current_user)):
    cursor = db.cursor()
    ejecutar_query(cursor, "SELECT * FROM registros_diarios WHERE user_id = ? ORDER BY fecha DESC", (current_user["id"],))
    rows = cursor.fetchall()
    return [dict(row) for row in rows]

@app.get("/api/registros/{registro_id}", response_model=RegistroDiario)
def obtener_registro(registro_id: int, db: sqlite3.Connection = Depends(get_db), current_user: dict = Depends(get_current_user)):
    cursor = db.cursor()
    ejecutar_query(cursor, "SELECT * FROM registros_diarios WHERE id = ? AND user_id = ?", (registro_id, current_user["id"]))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Registro con ID {registro_id} no encontrado."
        )
    return dict(row)

@app.put("/api/registros/{registro_id}", response_model=RegistroDiario)
def actualizar_registro(registro_id: int, registro_update: RegistroDiarioUpdate, db: sqlite3.Connection = Depends(get_db), current_user: dict = Depends(get_current_user)):
    cursor = db.cursor()
    
    # Verificar si el registro existe y pertenece al usuario
    ejecutar_query(cursor, "SELECT * FROM registros_diarios WHERE id = ? AND user_id = ?", (registro_id, current_user["id"]))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Registro con ID {registro_id} no encontrado."
        )
    
    # Construir consulta dinámica basada en los campos provistos para actualizar
    update_data = registro_update.model_dump(exclude_unset=True)
    if not update_data:
        return dict(row)
    
    if "fecha" in update_data and update_data["fecha"] is not None:
        fecha_str = update_data["fecha"].isoformat()
        ejecutar_query(cursor, "SELECT id FROM registros_diarios WHERE fecha = ? AND id != ? AND user_id = ?", (fecha_str, registro_id, current_user["id"]))
        if cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya existe otro registro para la fecha {fecha_str}."
            )
        update_data["fecha"] = fecha_str

    fields = ", ".join([f"{key} = ?" for key in update_data.keys()])
    values = list(update_data.values())
    values.append(registro_id)
    values.append(current_user["id"])
    
    try:
        ejecutar_query(cursor, f"UPDATE registros_diarios SET {fields} WHERE id = ? AND user_id = ?", values)
        db.commit()
        
        ejecutar_query(cursor, "SELECT * FROM registros_diarios WHERE id = ?", (registro_id,))
        row_actualizada = cursor.fetchone()
        return dict(row_actualizada)
    except sqlite3.Error as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar el registro: {str(e)}"
        )

@app.delete("/api/registros/{registro_id}")
def eliminar_registro(registro_id: int, db: sqlite3.Connection = Depends(get_db), current_user: dict = Depends(get_current_user)):
    cursor = db.cursor()
    ejecutar_query(cursor, "SELECT id FROM registros_diarios WHERE id = ? AND user_id = ?", (registro_id, current_user["id"]))
    if not cursor.fetchone():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Registro con ID {registro_id} no encontrado."
        )
    
    try:
        ejecutar_query(cursor, "DELETE FROM registros_diarios WHERE id = ?", (registro_id,))
        db.commit()
        return {"mensaje": f"Registro con ID {registro_id} eliminado exitosamente."}
    except sqlite3.Error as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al eliminar el registro: {str(e)}"
        )

@app.delete("/api/registros")
def borrar_todos_los_registros(db: sqlite3.Connection = Depends(get_db), current_user: dict = Depends(get_current_user)):
    cursor = db.cursor()
    try:
        ejecutar_query(cursor, "DELETE FROM registros_diarios WHERE user_id = ?", (current_user["id"],))
        db.commit()
        return {"mensaje": "Todos los registros han sido borrados mágicamente."}
    except sqlite3.Error as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al borrar los registros."
        )

# --- Endpoint Especial: Consejos por día del ciclo ---

@app.get("/api/consejos/{dia_del_ciclo}")
def obtener_consejos(dia_del_ciclo: int):
    if dia_del_ciclo < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El día del ciclo debe ser un número entero mayor o igual a 1."
        )
        
    system_instruction = (
        "Eres Lunita, una experta en salud femenina y bienestar cíclico. Tu misión es educar a la usuaria sobre su cuerpo, pero hablando como una amiga cercana, cálida y moderna. Traduce la ciencia a un lenguaje cotidiano, empático y fácil de digerir.\n\n"
        "REGLAS DE TONO:\n"
        "- Menciona de forma sencilla qué hormonas están actuando (ej: 'Tus estrógenos están en su punto más alto, lo que te dará mucha energía natural...').\n"
        "- Haz recomendaciones de vitaminas y alimentos, pero redactadas como una charla amigable, no como una receta médica.\n"
        "- Escribe párrafos cortos y fluidos. No uses lenguaje excesivamente clínico ni parezcas un robot. Usa emojis con buen gusto.\n\n"
        "REGLA TÉCNICA OBLIGATORIA:\n"
        "Tu respuesta DEBE ser un JSON válido con las tres claves exactas: nutricion, ejercicio y salud_mental.\n"
        "¡ATENCIÓN! Los valores de estas claves DEBEN ser cadenas de texto simples (strings) con tu consejo redactado en lenguaje natural. PROHIBIDO incluir listas [], diccionarios anidados {}, o viñetas raras de markdown dentro de los valores. Solo texto limpio y directo. Devuelve ÚNICA Y EXCLUSIVAMENTE el objeto JSON. No agregues saludos, ni explicaciones antes o después de las llaves {}.\n\n"
        "REGLA SINTOTÉRMICA:\n"
        "Utiliza el método sintotérmico: un aumento sostenido de la temperatura basal junto con flujo tipo 'clara de huevo' confirma la ventana de máxima fertilidad y la ovulación."
    )
    
    user_prompt = f"Genera los consejos mágicos para el día {dia_del_ciclo} del ciclo menstrual."

    try:
        if not client:
            raise Exception("No se pudo instanciar el cliente de Gemini.")
            
        prompt = system_instruction + "\n\n" + user_prompt
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        
        texto_crudo = response.text.strip()
        
        import re
        import json
        
        # Buscar el bloque JSON dentro del texto crudo
        match = re.search(r'\{.*\}', texto_crudo, re.DOTALL)
        if match:
            texto_json = match.group(0)
        else:
            texto_json = texto_crudo
            
        consejos_raw = json.loads(texto_json)
        
        def a_texto(val):
            if isinstance(val, dict):
                return " ".join([str(v) for v in val.values()])
            elif isinstance(val, list):
                return ", ".join([str(v) for v in val])
            return str(val) if val else "Sin información."
            
        consejos_json = {
            "nutricion": a_texto(consejos_raw.get("nutricion")),
            "ejercicio": a_texto(consejos_raw.get("ejercicio", consejos_raw.get("movimiento"))),
            "salud_mental": a_texto(consejos_raw.get("salud_mental"))
        }
        
        if 1 <= dia_del_ciclo <= 5: fase = "Menstrual"
        elif 6 <= dia_del_ciclo <= 13: fase = "Folicular"
        elif 14 <= dia_del_ciclo <= 16: fase = "Ovulación"
        else: fase = "Lútea"

        return {
            "dia_del_ciclo": dia_del_ciclo,
            "fase": fase,
            "consejos": consejos_json
        }
    except Exception as e:
        print(f"Error al procesar Gemini: {e}")
        if 'texto_crudo' in locals():
            print(f"Texto crudo devuelto por la IA: {texto_crudo}")
        # Fallback de emergencia
        if 1 <= dia_del_ciclo <= 5: fase = "Menstrual"
        elif 6 <= dia_del_ciclo <= 13: fase = "Folicular"
        elif 14 <= dia_del_ciclo <= 16: fase = "Ovulación"
        else: fase = "Lútea"
        
        return {
            "dia_del_ciclo": dia_del_ciclo,
            "fase": fase,
            "consejos": {
                "nutricion": "Escucha a tu cuerpo y mantente muy hidratada. 🍵",
                "ejercicio": "Muévete a tu propio ritmo, honrando tu energía de hoy. 🧘‍♀️",
                "salud_mental": "Sé muy amable y compasiva contigo misma. ✨"
            }
        }

@app.get("/api/consejera")
def consejera_predictiva(db: sqlite3.Connection = Depends(get_db), current_user: dict = Depends(get_current_user)):
    # 1. Obtener los últimos 5 registros para dar contexto a la IA
    cursor = db.cursor()
    ejecutar_query(cursor, """
        SELECT fecha, dia_del_ciclo, animo, sintomas, temperatura_basal 
        FROM registros_diarios 
        WHERE user_id = ?
        ORDER BY fecha DESC 
        LIMIT 5
    """, (current_user["id"],))
    rows = cursor.fetchall()
    
    if not rows:
        return {"mensaje": "¡Aún necesito conocerte un poquito más! Registra un par de días para darte los mejores consejos. 💖"}
    
    # 2. Procesar los datos recientes
    dia_actual = rows[0]['dia_del_ciclo']
    
    animos_list = []
    sintomas_list = []
    for row in rows:
        animos_list.append(row['animo'])
        sintomas_list.extend([s.strip() for s in row['sintomas'].split(',') if s.strip().lower() != 'ninguno'])
        
    animo_predominante = Counter(animos_list).most_common(1)[0][0] if animos_list else "Normal"
    sintoma_predominante = Counter(sintomas_list).most_common(1)[0][0] if sintomas_list else "ninguno en particular"

    # 3. Construir el prompt para Gemini
    system_instruction = (
        "Eres una consejera de bienestar menstrual experta, empática y con rigor científico. "
        "Te comunicas en un tono de amiga comprensiva, no empalagosa, usando emojis con moderación. "
        "Recibirás el estado actual de la usuaria y debes proporcionar consejos claros y accionables divididos estrictamente en tres categorías: "
        "nutrición, ejercicio, y salud mental. "
        "Si la usuaria está en su fase ovulatoria (aprox. días 11 al 16), infórmale sutilmente que se encuentra en su ventana de alta fertilidad. "
        "Considera en tu análisis la temperatura basal reportada para identificar patrones de ovulación según el método sintotérmico. "
        "IMPORTANTE: Devuelve ÚNICA Y EXCLUSIVAMENTE un objeto JSON válido con las claves exactas: 'nutricion', 'ejercicio' y 'salud_mental'. No devuelvas ningún otro texto ni formato markdown."
    )
    
    user_prompt = (
        f"Datos recientes de la usuaria: Está en el día {dia_actual} de su ciclo menstrual. "
        f"Su estado de ánimo predominante en estos días ha sido '{animo_predominante}'. "
        f"Sus síntomas más frecuentes son: '{sintoma_predominante}'. "
        "Genera los 3 consejos (nutricion, ejercicio, salud_mental) en formato JSON puro."
    )

    try:
        # 4. Generar respuesta con Gemini
        if not client:
            raise Exception("No se pudo instanciar el cliente de Gemini. ¿Configuraste la API Key?")
            
        prompt = system_instruction + "\n\n" + user_prompt
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=genai.types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        
        # Como forzamos application/json, parseamos el texto
        data = json.loads(response.text.strip())
        return {
            "nutricion": data.get("nutricion", "No hay consejo disponible."),
            "ejercicio": data.get("ejercicio", "No hay consejo disponible."),
            "salud_mental": data.get("salud_mental", "No hay consejo disponible.")
        }
    except Exception as e:
        print(f"Error generando respuesta con Gemini en Consejera: {e}")
        return {
            "nutricion": f"Hola hermosa 🌸. Vi que estás en el día {dia_actual}. Mantente hidratada y come algo ligero.",
            "ejercicio": "Escucha a tu cuerpo y haz movimiento suave si te sientes cómoda.",
            "salud_mental": f"Te has sentido {animo_predominante.lower()}. Recuerda ser amable contigo misma hoy. ✨"
        }

@app.get("/api/pronostico_mensual")
def pronostico_mensual(db: sqlite3.Connection = Depends(get_db), current_user: dict = Depends(get_current_user)):
    cursor = db.cursor()
    ejecutar_query(cursor, """
        SELECT fecha, dia_del_ciclo, flujo, animo, sintomas, temperatura_basal 
        FROM registros_diarios 
        WHERE user_id = ? 
        ORDER BY fecha DESC LIMIT 60
    """, (current_user["id"],))
    rows = cursor.fetchall()
    
    if len(rows) < 3:
        raise HTTPException(status_code=400, detail="Necesito al menos 3 días de registros para poder analizar tus patrones y darte un buen pronóstico. ¡Sigue registrando tu magia! ✨")
        
    resumen_datos = "Historial de los últimos 60 días:\n"
    for r in reversed(rows):
        resumen_datos += f"- Día {r['dia_del_ciclo']} ({r['fecha']}): Flujo {r['flujo']}, Ánimo {r['animo']}, Síntomas: {r['sintomas']}, Temp: {r['temperatura_basal']}°C\n"
        
    system_instruction = (
        "Eres Lunita, una experta en endocrinología femenina y bienestar cíclico. La usuaria te enviará un resumen de sus últimos registros. "
        "Tu misión es analizar sus patrones (síntomas, flujo, temperatura, emociones) y darle un pronóstico para su próximo mes.\n"
        "REGLAS:\n"
        "Basa tu análisis estrictamente en procesos biológicos reales (fluctuaciones de estrógeno, progesterona, testosterona).\n"
        "Utiliza el método sintotérmico: un aumento sostenido de la temperatura basal junto con flujo tipo 'clara de huevo' confirma la ventana de máxima fertilidad y la ovulación.\n"
        "Explica qué puede esperar hormonalmente en las próximas semanas considerando cómo se ha sentido últimamente.\n"
        "Mantén el tono de 'amiga experta': empático, directo y fácil de entender, sin ser excesivamente clínica ni empalagosa.\n"
        "Tu respuesta DEBE ser un JSON válido con las claves: analisis_patrones (qué notaste de sus datos) y pronostico_hormonal (qué esperar este mes). "
        "Los valores deben ser texto limpio, sin diccionarios anidados ni corchetes."
    )
    
    try:
        if not client:
            raise Exception("Gemini API Client no configurado.")
            
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=system_instruction + "\n\n" + resumen_datos,
        )
        
        texto_crudo = response.text.strip()
        match = re.search(r'\{.*\}', texto_crudo, re.DOTALL)
        if match:
            texto_json = match.group(0)
        else:
            texto_json = texto_crudo
            
        pronostico_json = json.loads(texto_json)
        
        return {
            "analisis_patrones": pronostico_json.get("analisis_patrones", "No pude generar un análisis en este momento."),
            "pronostico_hormonal": pronostico_json.get("pronostico_hormonal", "Sigue registrando para darte un mejor pronóstico.")
        }
    except Exception as e:
        print(f"Error generando pronóstico con Gemini: {e}")
        if 'texto_crudo' in locals():
            print(f"Texto crudo: {texto_crudo}")
        raise HTTPException(status_code=500, detail="Ups, las estrellas se han cruzado y no pude generar tu pronóstico ahora mismo. Intenta más tarde. 🌟")

@app.get("/api/notificaciones")
def obtener_notificaciones(db: sqlite3.Connection = Depends(get_db), current_user: dict = Depends(get_current_user)):
    cursor = db.cursor()
    ejecutar_query(cursor, """
        SELECT dia_del_ciclo FROM registros_diarios 
        WHERE user_id = ? 
        ORDER BY fecha DESC LIMIT 1
    """, (current_user["id"],))
    row = cursor.fetchone()
    
    notificaciones = []
    if row:
        dia = row["dia_del_ciclo"]
        if dia >= 1 and dia <= 5:
            notificaciones.append({"mensaje": "¡Hola bonita! Estás en tus días menstruales. Recuerda mantenerte abrigadita y beber infusiones calientes. 🍵💖", "tipo": "info"})
        elif dia >= 24:
            notificaciones.append({"mensaje": "La fase premenstrual se acerca. Escucha a tu cuerpo y date los descansos que necesites. 🧘‍♀️✨", "tipo": "warning"})
        else:
            notificaciones.append({"mensaje": "¡Tu ciclo fluye hermosamente! Recuerda mantener tu diario actualizado. 🌸✍️", "tipo": "success"})
    else:
        notificaciones.append({"mensaje": f"¡Bienvenida {current_user['username']}! Empieza a registrar tus días para recibir notificaciones mágicas. ✨", "tipo": "info"})
        
    return notificaciones

@app.get("/api/estado_actual")
def obtener_estado_actual(db: sqlite3.Connection = Depends(get_db), current_user: dict = Depends(get_current_user)):
    cursor = db.cursor()
    ejecutar_query(cursor, """
        SELECT fecha, dia_del_ciclo FROM registros_diarios 
        WHERE user_id = ? 
        ORDER BY fecha DESC LIMIT 1
    """, (current_user["id"],))
    row = cursor.fetchone()
    
    if not row:
        return {
            "dia": 1, 
            "fase": "Menstrual 🩸", 
            "emoji": "🌑", 
            "mensaje": "Empieza a registrar tus días para conectar con tu ciclo. ✨", 
            "porcentaje": 0
        }
        
    from datetime import date
    fecha_ultimo_str = row["fecha"]
    dia_ultimo = int(row["dia_del_ciclo"])
    fecha_ultimo = date.fromisoformat(fecha_ultimo_str)
    
    diferencia_dias = (date.today() - fecha_ultimo).days
    dia_actual = dia_ultimo + diferencia_dias
    
    if dia_actual < 1:
        dia_actual = 1
        
    if 1 <= dia_actual <= 5:
        fase = "Menstrual"
        emoji = "🌑"
        mensaje = "Energía de introspección, ideal para descansar y conectar contigo."
    elif 6 <= dia_actual <= 11:
        fase = "Folicular"
        emoji = "🌙"
        mensaje = "Energía al alza y creatividad. ¡Aprovecha para iniciar proyectos!"
    elif 12 <= dia_actual <= 16:
        fase = "Ovulatoria"
        emoji = "🌕"
        mensaje = "Tu energía está al máximo, ¡es un gran día para brillar y socializar! ✨"
    else:
        fase = "Lútea"
        emoji = "🌘"
        mensaje = "Tiempo de autocuidado y calma. Escucha a tu cuerpo y baja el ritmo."
        
    porcentaje = min((dia_actual / 28) * 100, 100)
    
    return {
        "dia": dia_actual,
        "fase": fase,
        "emoji": emoji,
        "mensaje": mensaje,
        "porcentaje": porcentaje
    }

@app.get("/api/prediccion")
def obtener_prediccion(db: sqlite3.Connection = Depends(get_db), current_user: dict = Depends(get_current_user)):
    cursor = db.cursor()
    ejecutar_query(cursor, "SELECT fecha, dia_del_ciclo FROM registros_diarios WHERE user_id = ? ORDER BY fecha ASC", (current_user["id"],))
    rows = cursor.fetchall()
    
    if not rows:
        return {"fechas": []}
        
    fechas_inicio = []
    from datetime import date, timedelta
    
    for row in rows:
        try:
            fecha_str = row["fecha"]
            dia = int(row["dia_del_ciclo"])
            fecha_obj = date.fromisoformat(fecha_str)
            inicio_estimado = fecha_obj - timedelta(days=dia - 1)
            
            if not fechas_inicio:
                fechas_inicio.append(inicio_estimado)
            else:
                ultimo_inicio = fechas_inicio[-1]
                if abs((inicio_estimado - ultimo_inicio).days) > 10:
                    fechas_inicio.append(inicio_estimado)
        except Exception:
            continue
            
    dias_sombreados = 6 if current_user.get("es_irregular") else 4

    if len(fechas_inicio) < 2:
        promedio = 28
    else:
        diferencias = []
        for i in range(1, len(fechas_inicio)):
            diff = (fechas_inicio[i] - fechas_inicio[i-1]).days
            if 20 <= diff <= 45:
                diferencias.append(diff)
        
        if not diferencias:
            promedio = 28
        elif current_user.get("es_irregular") and len(diferencias) >= 2:
            avg_last_2 = sum(diferencias[-2:]) / 2
            if len(diferencias) > 2:
                avg_older = sum(diferencias[:-2]) / len(diferencias[:-2])
                promedio = int(0.8 * avg_last_2 + 0.2 * avg_older)
            else:
                promedio = int(avg_last_2)
        else:
            promedio = sum(diferencias) // len(diferencias)
        
    ultimo_ciclo = fechas_inicio[-1]
    proximo_periodo_inicio = ultimo_ciclo + timedelta(days=promedio)
    
    fechas_prediccion = [(proximo_periodo_inicio + timedelta(days=i)).isoformat() for i in range(dias_sombreados)]
    
    return {"fechas": fechas_prediccion}

# --- WEB PUSH NOTIFICATIONS ---

VAPID_PUBLIC_KEY = os.getenv("VAPID_PUBLIC_KEY")
VAPID_PRIVATE_KEY = os.getenv("VAPID_PRIVATE_KEY", "./private_key.pem")
VAPID_CLAIMS = {
    "sub": f"mailto:{os.getenv('EMAIL_USER', 'admin@example.com')}"
}

class PushSubscription(BaseModel):
    endpoint: str
    expirationTime: Optional[int] = None
    keys: dict

@app.get("/api/notificaciones/vapid-public-key")
def get_vapid_public_key():
    if not VAPID_PUBLIC_KEY:
        raise HTTPException(status_code=500, detail="VAPID_PUBLIC_KEY no configurado en servidor")
    return {"public_key": VAPID_PUBLIC_KEY}

@app.post("/api/notificaciones/suscribir")
def suscribir_push(sub: PushSubscription, db: sqlite3.Connection = Depends(get_db), current_user: dict = Depends(get_current_user)):
    cursor = db.cursor()
    try:
        ejecutar_query(cursor, "UPDATE usuarios SET push_subscription = ? WHERE id = ?", (json.dumps(sub.model_dump()), current_user["id"]))
        db.commit()
        return {"mensaje": "Suscripción push guardada con éxito 🔔✨"}
    except Exception as e:
        db.rollback()
        print(f"Error al guardar suscripción push: {e}")
        raise HTTPException(status_code=500, detail="No se pudo guardar la suscripción")

def enviar_notificacion_push(user_id: int, titulo: str, mensaje: str, db: sqlite3.Connection):
    cursor = db.cursor()
    ejecutar_query(cursor, "SELECT push_subscription FROM usuarios WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    
    if not row or not row["push_subscription"]:
        print(f"Usuario {user_id} no tiene suscripción push configurada.")
        return False
        
    try:
        sub_info = json.loads(row["push_subscription"])
        payload = json.dumps({
            "title": titulo,
            "body": mensaje,
            "icon": "/icon-192x192.png",
            "badge": "/icon-192x192.png"
        })
        
        webpush(
            subscription_info=sub_info,
            data=payload,
            vapid_private_key=VAPID_PRIVATE_KEY,
            vapid_claims=VAPID_CLAIMS
        )
        print(f"Notificación Push enviada exitosamente al usuario {user_id}")
        return True
    except WebPushException as ex:
        print(f"Excepción Web Push para el usuario {user_id}: {repr(ex)}")
        if ex.response and ex.response.json():
            print(f"Detalles: {ex.response.json()}")
        return False
    except Exception as e:
        print(f"Error desconocido al enviar Web Push a usuario {user_id}: {e}")
        return False

# --- REPORTE MEDICO Y MODO PAREJA ---

@app.get("/api/reporte/pdf")
def generar_reporte_pdf(db: sqlite3.Connection = Depends(get_db), current_user: dict = Depends(get_current_user)):
    cursor = db.cursor()
    # Últimos 90 días
    hace_90_dias = (date.today() - timedelta(days=90)).isoformat()
    ejecutar_query(cursor, """
        SELECT fecha, dia_del_ciclo, flujo, sintomas, animo 
        FROM registros_diarios 
        WHERE user_id = ? AND fecha >= ?
        ORDER BY fecha DESC
    """, (current_user["id"], hace_90_dias))
    rows = cursor.fetchall()
    
    html_content = f"""
    <html>
    <head>
        <style>
            body {{ font-family: sans-serif; color: #333; }}
            h1 {{ color: #B28DFF; text-align: center; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #F8F0FF; color: #5C4B62; }}
        </style>
    </head>
    <body>
        <h1>Reporte de Salud - Lunita 🌙</h1>
        <p><strong>Usuaria:</strong> {current_user['username']}</p>
        <p><strong>Fecha de Emisión:</strong> {date.today().isoformat()}</p>
        <p>A continuación se detallan los registros de los últimos 3 meses.</p>
        <table>
            <tr>
                <th>Fecha</th>
                <th>Día del Ciclo</th>
                <th>Flujo</th>
                <th>Ánimo</th>
                <th>Síntomas</th>
            </tr>
    """
    for r in rows:
        html_content += f"""
            <tr>
                <td>{r['fecha']}</td>
                <td>{r['dia_del_ciclo']}</td>
                <td>{r['flujo']}</td>
                <td>{r['animo']}</td>
                <td>{r['sintomas']}</td>
            </tr>
        """
    html_content += """
        </table>
    </body>
    </html>
    """
    
    try:
        pdf_bytes = weasyprint.HTML(string=html_content).write_pdf()
        return Response(content=pdf_bytes, media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=Reporte_Lunita.pdf"})
    except Exception as e:
        print(f"Error generando PDF: {e}")
        raise HTTPException(status_code=500, detail="No se pudo generar el PDF. Verifica que GTK esté instalado en tu sistema.")

@app.post("/api/pareja/generar")
def generar_token_pareja(db: sqlite3.Connection = Depends(get_db), current_user: dict = Depends(get_current_user)):
    cursor = db.cursor()
    token = secrets.token_urlsafe(16)
    ejecutar_query(cursor, "UPDATE usuarios SET token_pareja = ? WHERE id = ?", (token, current_user["id"]))
    db.commit()
    return {"token": token}

@app.get("/pareja/{token}", response_class=HTMLResponse)
def vista_pareja(token: str, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    ejecutar_query(cursor, "SELECT id, username FROM usuarios WHERE token_pareja = ?", (token,))
    user = cursor.fetchone()
    if not user:
        return HTMLResponse("<h1>Enlace mágico no encontrado o expirado ✨</h1>", status_code=404)
        
    ejecutar_query(cursor, """
        SELECT dia_del_ciclo, animo 
        FROM registros_diarios 
        WHERE user_id = ? 
        ORDER BY fecha DESC LIMIT 1
    """, (user["id"],))
    registro = cursor.fetchone()
    
    if not registro:
        return HTMLResponse(f"<h1>Hola. {user['username']} aún no ha registrado sus días en Lunita. 🌙</h1>")
        
    dia = registro["dia_del_ciclo"]
    animo = registro["animo"]
    
    # Lógica simple
    fase = "Fase desconocida"
    mensaje = "Dale mucho amor."
    if 1 <= dia <= 5:
        fase = "Menstrual 🩸"
        mensaje = "Está en sus días de descanso. Necesita mimitos, calorcito y mucha comprensión."
    elif 6 <= dia <= 13:
        fase = "Folicular 🌸"
        mensaje = "Su energía va en aumento. ¡Excelente momento para planes divertidos y activos!"
    elif 14 <= dia <= 16:
        fase = "Ovulatoria ✨"
        mensaje = "Está en su pico de energía y sociabilidad. Se siente radiante."
    else:
        fase = "Lútea 🍂"
        mensaje = "Su energía empieza a bajar. Puede estar más sensible, necesita paciencia y apoyo."

    html_content = f"""
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Lunita - Modo Pareja</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #F8F0FF 0%, #E8DFF5 100%); display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; color: #5C4B62; }}
            .card {{ background: white; padding: 40px; border-radius: 20px; box-shadow: 0 10px 30px rgba(178,141,255,0.2); text-align: center; max-width: 400px; width: 90%; }}
            h1 {{ color: #B28DFF; margin-bottom: 5px; }}
            .fase {{ font-size: 1.5rem; font-weight: bold; margin: 20px 0; color: #FFAAA6; }}
            .mensaje {{ font-size: 1.1rem; line-height: 1.5; margin-bottom: 20px; }}
        </style>
    </head>
    <body>
        <div class="card">
            <h1>Lunita 🌙</h1>
            <p>El estado actual de <strong>{user['username']}</strong> es:</p>
            <div class="fase">{fase}</div>
            <p><strong>Ánimo reciente:</strong> {animo}</p>
            <div class="mensaje">{mensaje}</div>
            <p style="font-size: 0.8rem; color: #999;">Esta es una vista segura. No se muestran datos clínicos.</p>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)
