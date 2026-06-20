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
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.templating import Jinja2Templates
from fastapi import Request
import bcrypt
from jose import JWTError, jwt
from pydantic import BaseModel, Field, field_validator, EmailStr
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
import io

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
                        hashed_password TEXT NOT NULL
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
                        UNIQUE(fecha, user_id)
                    )
                """)
                conn.commit()
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
            hashed_password TEXT NOT NULL
        )
    """)

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
                UNIQUE(fecha, user_id)
            )
        """)
        # Revisar si la tabla vieja        # Copiar datos antiguos si existen
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='registros_diarios'")
        if cursor.fetchone():
            cursor.execute("INSERT OR IGNORE INTO registros_diarios_v2 (id, fecha, dia_del_ciclo, flujo, animo, sintomas) SELECT id, fecha, dia_del_ciclo, flujo, animo, sintomas FROM registros_diarios")
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

# Ejecutar la creación de tablas al iniciar la aplicación
@app.on_event("startup")
def startup_event():
    init_db()

@app.get("/")
def raiz():
    return {
        "mensaje": "¡Te damos la bienvenida a Lunita API! 🌙",
        "descripcion": "API enfocada en bienestar, nutrición y salud mental para el ciclo menstrual.",
        "documentacion": "/docs",
        "endpoints": {
            "registros": "/api/registros",
            "consejos": "/api/consejos/{dia_del_ciclo}"
        }
    }

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
        ejecutar_query(cursor, "INSERT INTO usuarios (username, email, hashed_password) VALUES (?, ?, ?)", 
                       (user.username, user.email, hashed_password))
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

class ConfigUsuario(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None

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
        ejecutar_query(cursor, 
            """
            INSERT INTO registros_diarios (fecha, dia_del_ciclo, flujo, animo, sintomas, user_id)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                registro.fecha.isoformat(),
                registro.dia_del_ciclo,
                registro.flujo,
                registro.animo,
                registro.sintomas,
                current_user["id"]
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

# --- Endpoint Especial: Consejos por día del ciclo ---

@app.get("/api/consejos/{dia_del_ciclo}")
def obtener_consejos(dia_del_ciclo: int):
    # Validar que el día del ciclo sea un valor válido
    if dia_del_ciclo < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El día del ciclo debe ser un número entero mayor o igual a 1."
        )
        
    # Clasificación de fases y recomendaciones orientadas a bienestar, nutrición y salud mental
    if 1 <= dia_del_ciclo <= 5:
        fase = "Menstrual"
        consejos = {
            "alimentacion": "Prioriza alimentos calientes y de fácil digestión. Consume vegetales de hoja verde oscura, lentejas y semillas de calabaza ricos en hierro para compensar la pérdida de sangre. Añade jengibre o cúrcuma en infusiones para reducir la inflamación.",
            "ejercicio": "Tu cuerpo está usando mucha energía hacia el interior. Opta por actividades de muy baja intensidad como yoga restaurativo, estiramientos suaves o caminatas lentas. Evita esfuerzos intensos si te sientes cansada.",
            "salud_mental": "Es una fase ideal para la introspección y el descanso. Practica la autocompasión, disminuye tu lista de pendientes si es posible, medita y prioriza el sueño de calidad."
        }
    elif 6 <= dia_del_ciclo <= 13:
        fase = "Folicular"
        consejos = {
            "alimentacion": "A medida que sube el estrógeno, tu energía aumenta. Incorpora carbohidratos complejos (avena, quinoa), grasas saludables (aguacate, nueces) y alimentos fermentados (yogur, kéfir) para apoyar la metabolización del estrógeno.",
            "ejercicio": "Aprovecha la energía ascendente. Es un buen momento para entrenamientos de fuerza moderada, ejercicios aeróbicos (correr, andar en bicicleta) y clases dinámicas. Te recuperarás más rápido.",
            "salud_mental": "Tu cerebro está predispuesto a la creatividad, el aprendizaje y la planificación. Es un gran momento para iniciar proyectos, resolver problemas complejos y programar reuniones importantes."
        }
    elif 14 <= dia_del_ciclo <= 16:
        fase = "Ovulación"
        consejos = {
            "alimentacion": "Consume alimentos ricos en antioxidantes como bayas, verduras crucíferas (brócoli, coles de Bruselas) y pescado azul rico en omega-3 para apoyar la salud celular y el equilibrio hormonal. Mantente muy bien hidratada.",
            "ejercicio": "Momento de máxima energía física. Ideal para entrenamientos de alta intensidad (HIIT), fuerza pesada, o deportes competitivos y demandantes.",
            "salud_mental": "Los niveles altos de estrógeno y testosterona favorecen la sociabilidad, la comunicación y la confianza. Aprovecha para socializar, realizar presentaciones públicas o tener conversaciones importantes."
        }
    else:  # dia_del_ciclo >= 17
        fase = "Lútea"
        # Recomendaciones adaptadas a la fase lútea, subdividiendo mentalmente si se aproxima el síndrome premenstrual
        consejos = {
            "alimentacion": "Para mitigar los antojos y la retención de líquidos, prioriza grasas saludables y alimentos ricos en magnesio (cacao puro, plátanos, espinacas) y vitamina B6. Reduce el consumo de cafeína, sal y azúcares refinados.",
            "ejercicio": "La energía irá disminuyendo progresivamente. Haz una transición hacia actividades de intensidad moderada a baja como pilates, caminatas al aire libre o natación suave. Escucha a tu cuerpo y baja el ritmo si lo pide.",
            "salud_mental": "Es normal experimentar fluctuaciones de ánimo o mayor sensibilidad. Practica el establecimiento de límites saludables, realiza actividades que te calmen (lectura, baños templados, escritura reflexiva) y reduce el estrés."
        }

    return {
        "dia_del_ciclo": dia_del_ciclo,
        "fase": fase,
        "consejos": consejos
    }

@app.get("/api/consejera")
def consejera_predictiva(db: sqlite3.Connection = Depends(get_db), current_user: dict = Depends(get_current_user)):
    # 1. Obtener los últimos 5 registros para dar contexto a la IA
    cursor = db.cursor()
    ejecutar_query(cursor, """
        SELECT fecha, dia_del_ciclo, animo, sintomas 
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
        "Eres una consejera de bienestar menstrual muy empática, dulce y enfocada en nutrición, autocuidado y salud mental. "
        "NO eres un médico y NUNCA debes hablar sobre temas de fertilidad o embarazo. "
        "Tu objetivo es dar una respuesta corta (máximo 3-4 líneas), en tono de amiga cercana, usando emojis kawaii. "
        "Analiza el contexto de la usuaria y ofrécele un consejo muy puntual y amoroso."
    )
    
    user_prompt = (
        f"Datos recientes de la usuaria: Está en el día {dia_actual} de su ciclo menstrual. "
        f"Su estado de ánimo predominante en estos días ha sido '{animo_predominante}'. "
        f"Sus síntomas más frecuentes son: '{sintoma_predominante}'. "
        "Por favor, dale un consejo de autocuidado o nutrición adecuado para esta fase de su ciclo."
    )

    try:
        # 4. Generar respuesta con Gemini
        if not client:
            raise Exception("No se pudo instanciar el cliente de Gemini. ¿Configuraste la API Key?")
            
        prompt = system_instruction + "\n\n" + user_prompt
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        mensaje_ia = response.text.strip()
        
        return {"mensaje": mensaje_ia}
    except Exception as e:
        # Fallback en caso de que haya un error
        print(f"Error generando respuesta con Gemini: {e}")
        return {
            "mensaje": f"Hola hermosa 🌸. Vi que estás en el día {dia_actual} y te has sentido {animo_predominante.lower()}. "
                       f"Recuerda escuchar a tu cuerpo y descansar. ¡Pronto tendré más consejitos mágicos para ti! ✨"
        }

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


