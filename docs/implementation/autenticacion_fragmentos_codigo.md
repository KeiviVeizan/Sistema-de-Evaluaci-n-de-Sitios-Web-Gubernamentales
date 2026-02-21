# Implementación del Sistema de Autenticación

**Módulo:** Gestión de Usuarios — Autenticación con 2FA  
**Tecnologías:** FastAPI, SQLAlchemy, JWT (python-jose), bcrypt (passlib), fastapi-mail  
**Fecha:** Febrero 2026

---

## Tabla de Contenidos

1. [Arquitectura General](#1-arquitectura-general)
2. [Modelo de Datos — Usuario](#2-modelo-de-datos--usuario)
3. [Módulo de Seguridad — Hashing y JWT](#3-módulo-de-seguridad--hashing-y-jwt)
4. [Flujo de Login — Paso 1: Validación de Credenciales](#4-flujo-de-login--paso-1-validación-de-credenciales)
5. [Flujo de Login — Paso 2: Verificación de Código 2FA](#5-flujo-de-login--paso-2-verificación-de-código-2fa)
6. [Middleware de Autorización — Decodificación JWT](#6-middleware-de-autorización--decodificación-jwt)
7. [Control de Acceso Basado en Roles (RBAC)](#7-control-de-acceso-basado-en-roles-rbac)
8. [Servicio de Email — Envío de Código 2FA](#8-servicio-de-email--envío-de-código-2fa)
9. [Generación Segura de Contraseñas](#9-generación-segura-de-contraseñas)
10. [Configuración Centralizada](#10-configuración-centralizada)

---

## 1. Arquitectura General

El sistema de autenticación implementa un flujo de **dos factores (2FA)** basado en código por correo electrónico:

```
┌──────────┐     ┌──────────┐     ┌──────────────┐     ┌─────────────┐     ┌──────────┐
│ Frontend │────▶│ FastAPI  │────▶│  security.py │────▶│email_service│────▶│PostgreSQL│
│ (React)  │◀────│ Endpoint │◀────│  (JWT/bcrypt)│     │  (SMTP)     │     │ (Users)  │
└──────────┘     └──────────┘     └──────────────┘     └─────────────┘     └──────────┘
```

**Flujo completo:**
1. Usuario envía credenciales → Se valida contra la BD (bcrypt)
2. Si son correctas → Se genera un código de 6 dígitos → Se envía por email
3. Usuario ingresa el código → Se valida → Se genera un token JWT
4. El token JWT se envía en cada solicitud posterior como `Authorization: Bearer <token>`

---

## 2. Modelo de Datos — Usuario

**Archivo:** `backend/app/models/database_models.py`

### 2.1 Enumeración de Roles

El sistema define 4 roles con diferentes niveles de acceso:

```python
class UserRole(str, enum.Enum):
    """Roles de usuario en el sistema."""
    SUPERADMIN = "superadmin"
    SECRETARY = "secretary"
    EVALUATOR = "evaluator"
    ENTITY_USER = "entity_user"
```

> **Nota:** Al heredar de `str` y `enum.Enum`, los valores se serializan automáticamente como strings en las respuestas JSON.

### 2.2 Modelo de Usuario (SQLAlchemy ORM)

```python
class User(Base):
    """
    Modelo para usuarios del sistema.
    Soporta roles: superadmin, secretary, evaluator, entity_user.
    Los usuarios pueden estar asociados a una institución.
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    position: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole),
        default=UserRole.EVALUATOR,
        nullable=False
    )
    institution_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("institutions.id", ondelete="SET NULL"),
        nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Campos 2FA
    two_factor_enabled: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, server_default="false"
    )
    two_factor_secret: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    two_factor_backup_codes: Mapped[Optional[list]] = mapped_column(
        ARRAY(String), nullable=True
    )

    # Relaciones
    institution: Mapped[Optional["Institution"]] = relationship(
        back_populates="users"
    )
    notifications: Mapped[List["Notification"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
```

**Aspectos clave:**
- La contraseña se almacena como `hashed_password` (nunca en texto plano).
- `username` y `email` tienen restricción `unique=True` para evitar duplicados.
- El campo `is_active` permite desactivar cuentas sin eliminarlas.
- `institution_id` vincula usuarios de tipo `entity_user` con su institución.

---

## 3. Módulo de Seguridad — Hashing y JWT

**Archivo:** `backend/app/auth/security.py`

Este módulo contiene las utilidades centrales de seguridad: el hashing de contraseñas con bcrypt y la generación/verificación de tokens JWT.

### 3.1 Configuración del Contexto Criptográfico

```python
from passlib.context import CryptContext
from jose import jwt

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
```

> **`CryptContext`** de la biblioteca `passlib` permite manejar múltiples esquemas de hashing. Se configura con `bcrypt` como esquema principal y `deprecated="auto"` para migrar automáticamente hashes antiguos.

### 3.2 Hashing de Contraseñas

```python
def hash_password(password: str) -> str:
    """Genera un hash bcrypt de la contraseña."""
    return pwd_context.hash(password)
```

**¿Cómo funciona?**
- `bcrypt` genera un **salt aleatorio** de 16 bytes en cada llamada.
- Aplica **12 rounds** de hashing (por defecto), haciendo el proceso computacionalmente costoso.
- El resultado incluye el salt, los rounds y el hash: `$2b$12$salt...hash...`
- Dos llamadas con la misma contraseña producen hashes **diferentes** (por el salt aleatorio).

### 3.3 Verificación de Contraseñas

```python
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica una contraseña contra su hash bcrypt."""
    return pwd_context.verify(plain_password, hashed_password)
```

**¿Cómo funciona?**
- Extrae el **salt** del hash almacenado.
- Aplica el mismo algoritmo bcrypt con el mismo salt a la contraseña ingresada.
- Compara el resultado con el hash almacenado.
- Retorna `True` si coinciden, `False` si no.

### 3.4 Generación de Token JWT

```python
def create_access_token(
    data: dict, expires_delta: Optional[timedelta] = None
) -> str:
    """
    Crea un token JWT firmado.

    Args:
        data: Payload del token (debe incluir "sub" con el username)
        expires_delta: Duración personalizada del token

    Returns:
        Token JWT codificado como string
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta
        if expires_delta
        else timedelta(minutes=settings.access_token_expire_minutes)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.jwt_algorithm,
    )
```

**¿Cómo funciona?**
- Recibe un diccionario con datos del usuario (ej: `{"sub": "admin", "role": "superadmin"}`).
- Agrega la fecha de expiración al payload (`exp`).
- Firma el payload con la clave secreta usando el algoritmo **HS256**.
- Retorna un string JWT con formato: `header.payload.signature`.
- Por defecto, el token expira en **480 minutos (8 horas)**.

---

## 4. Flujo de Login — Paso 1: Validación de Credenciales

**Archivo:** `backend/app/api/auth_routes.py`  
**Endpoint:** `POST /api/v1/auth/login`

```python
# Almacenamiento temporal de códigos 2FA (en producción, usar Redis con TTL)
_2fa_codes: Dict[str, str] = {}


@router.post(
    "/login",
    summary="Paso 1: Validar credenciales y generar código 2FA",
)
async def login(
    credentials: LoginRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Valida credenciales y genera código de verificación de 6 dígitos.
    El código se envía al correo electrónico del usuario.
    """
    # 1. Buscar usuario por username O email
    user = db.query(User).filter(
        (User.username == credentials.username) |
        (User.email == credentials.username)
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
        )

    # 2. Refrescar datos desde BD (evita cache de sesión SQLAlchemy)
    db.refresh(user)

    # 3. Verificar contraseña contra el hash bcrypt
    if not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
        )

    # 4. Verificar que la cuenta esté activa
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario desactivado",
        )

    # 5. Generar código 2FA de 6 dígitos
    user_key = user.username or user.email
    code = str(random.randint(100000, 999999))
    _2fa_codes[user_key] = code

    # 6. Enviar código por email en segundo plano (no bloquea la respuesta)
    background_tasks.add_task(
        email_service.send_2fa_code,
        email=user.email,
        code=code,
        username=user_key,
    )

    return {
        "message": "Código de verificación enviado a tu correo electrónico.",
        "username": user_key,
    }
```

**Aspectos de seguridad implementados:**
1. **Mismo mensaje de error** para "usuario no encontrado" y "contraseña incorrecta" → Previene enumeración de usuarios.
2. **`db.refresh(user)`** → Fuerza recarga desde BD, evitando datos en caché.
3. **`BackgroundTasks`** → El envío de email no bloquea la respuesta al cliente.
4. **Código aleatorio** de 6 dígitos (100000 a 999999) → 900,000 combinaciones posibles.

---

## 5. Flujo de Login — Paso 2: Verificación de Código 2FA

**Archivo:** `backend/app/api/auth_routes.py`  
**Endpoint:** `POST /api/v1/auth/verify-2fa`

```python
@router.post(
    "/verify-2fa",
    response_model=TokenResponse,
    summary="Paso 2: Verificar código 2FA y obtener token",
)
async def verify_2fa(
    verification: Verify2FARequest,
    db: Session = Depends(get_db),
):
    """
    Verifica el código 2FA y retorna el JWT si es válido.
    """
    # 1. Validar que existe un código pendiente para el usuario
    if verification.username not in _2fa_codes:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No hay código pendiente para este usuario",
        )

    # 2. Comparar el código ingresado con el almacenado
    if _2fa_codes[verification.username] != verification.code:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Código de verificación inválido",
        )

    # 3. Buscar usuario en BD para obtener datos completos
    user = db.query(User).filter(
        (User.username == verification.username) |
        (User.email == verification.username)
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado",
        )

    # 4. Invalidar código (un solo uso)
    del _2fa_codes[verification.username]

    # 5. Generar token JWT con datos del usuario
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role.value}
    )

    # 6. Retornar token + datos del usuario
    return TokenResponse(
        access_token=access_token,
        user=UserResponse.from_user(user),
    )
```

**Aspectos clave:**
1. **Uso único del código** → Se elimina inmediatamente después de verificar (`del _2fa_codes[...]`).
2. **El JWT contiene el rol** → Permite autorización sin consultar la BD en cada request.
3. **Separación en dos pasos** → El primer paso no genera token; solo el segundo lo hace tras verificar el 2FA.

---

## 6. Middleware de Autorización — Decodificación JWT

**Archivo:** `backend/app/auth/dependencies.py`

### 6.1 Extracción y Validación del Token

```python
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Decodifica el token JWT y retorna el usuario correspondiente.

    Raises:
        HTTPException 401: Token inválido, expirado o usuario no encontrado
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido o expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Decodificar y verificar firma del JWT
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # Buscar usuario en BD
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user
```

**¿Cómo funciona?**
1. `OAuth2PasswordBearer` extrae automáticamente el token del header `Authorization: Bearer <token>`.
2. `jwt.decode()` verifica la firma y la expiración del token.
3. Se extrae el `username` del claim `sub`.
4. Se busca al usuario en la BD para validar que aún existe.
5. Si cualquier paso falla → Error 401.

### 6.2 Verificación de Usuario Activo

```python
async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Verifica que el usuario autenticado esté activo.

    Raises:
        HTTPException 403: Usuario desactivado
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario desactivado",
        )
    return current_user
```

> **Cadena de dependencias:** `get_current_active_user` depende de `get_current_user`, que depende de `oauth2_scheme`. FastAPI resuelve esta cadena automáticamente.

---

## 7. Control de Acceso Basado en Roles (RBAC)

**Archivo:** `backend/app/auth/dependencies.py`

### 7.1 Clase RoleChecker

```python
class RoleChecker:
    """
    Dependencia invocable para control de acceso basado en roles.

    Uso:
        @router.get("/admin", dependencies=[Depends(RoleChecker(["superadmin"]))])
        def admin_endpoint(): ...

        O como parámetro:
        def endpoint(user: User = Depends(RoleChecker(["superadmin", "secretary"]))):
            ...
    """

    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = allowed_roles

    def __call__(
        self, current_user: User = Depends(get_current_active_user)
    ) -> User:
        if current_user.role.value not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos para realizar esta acción",
            )
        return current_user
```

### 7.2 Instancias Pre-construidas

```python
# Instancias pre-construidas para uso directo en endpoints
allow_superadmin = RoleChecker(["superadmin"])
allow_admin_secretary = RoleChecker(["superadmin", "secretary"])
allow_admin_evaluator = RoleChecker(["superadmin", "evaluator"])
allow_all_staff = RoleChecker(["superadmin", "secretary", "evaluator"])
allow_staff_followups = RoleChecker(["superadmin", "secretary", "evaluator"])
```

### 7.3 Ejemplo de Uso en un Endpoint

```python
@router.post("/users", response_model=UserResponse, status_code=201)
async def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(allow_superadmin),  # ← Solo superadmin
):
    """Solo accesible por superadmin."""
    # ... lógica de creación ...
```

**¿Cómo funciona la cadena de autorización?**
```
Request con JWT
    └── OAuth2PasswordBearer (extrae token del header)
        └── get_current_user (decodifica JWT, busca en BD)
            └── get_current_active_user (verifica is_active)
                └── RoleChecker (verifica rol permitido)
                    └── ✅ Endpoint se ejecuta
```

---

## 8. Servicio de Email — Envío de Código 2FA

**Archivo:** `backend/app/services/email_service.py`

### 8.1 Envío del Código 2FA

```python
async def send_2fa_code(self, email: str, code: str, username: str) -> bool:
    """
    Envía el código de verificación 2FA por correo electrónico.
    """
    # Inicialización lazy del servicio SMTP
    self._initialize()

    subject = f"Código de Verificación: {code} - Evaluador GOB.BO"
    html_content = self._get_2fa_html_template(code, username)

    # Modo desarrollo: si SMTP no está configurado, muestra en consola
    if not self._fastmail:
        if settings.environment == "development":
            logger.warning("[MODO DESARROLLO] Servicio de correo NO configurado.")
            logger.warning(f"  Para: {email}")
            logger.warning(f"  Código: {code}")
            return True  # Permite continuar en desarrollo
        else:
            logger.error("Servicio de correo no disponible en producción.")
            return False

    # Envío real vía SMTP
    try:
        message = MessageSchema(
            subject=subject,
            recipients=[email],
            body=html_content,
            subtype=MessageType.html,
        )
        await self._fastmail.send_message(message)
        return True

    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"Error de autenticación SMTP: {e}")
        logger.warning(f"[FALLBACK] Código 2FA para {username}: {code}")
        return False
```

**Aspectos clave:**
- **Inicialización lazy** → El servicio SMTP solo se configura cuando es necesario.
- **Modo desarrollo** → Si no hay SMTP configurado, el código se muestra en la consola del servidor.
- **Fallback** → Si el envío falla, el código se registra en logs como respaldo.

### 8.2 Configuración SMTP

```python
def _initialize(self):
    """Inicializa la configuración de correo de forma lazy."""
    if self._initialized:
        return

    # Verificar conectividad SMTP antes de configurar
    if not self._test_smtp_connection(settings.mail_server, settings.mail_port):
        logger.error("No se puede conectar al servidor SMTP.")
        self._initialized = True
        return

    self._config = ConnectionConfig(
        MAIL_USERNAME=settings.mail_username,
        MAIL_PASSWORD=settings.mail_password,
        MAIL_FROM=settings.mail_from,
        MAIL_FROM_NAME=settings.mail_from_name,
        MAIL_PORT=settings.mail_port,           # 587 (TLS)
        MAIL_SERVER=settings.mail_server,       # smtp.gmail.com
        MAIL_STARTTLS=settings.mail_tls,        # True
        MAIL_SSL_TLS=settings.mail_ssl,         # False
        USE_CREDENTIALS=True,
        VALIDATE_CERTS=True,
    )
    self._fastmail = FastMail(self._config)
```

---

## 9. Generación Segura de Contraseñas

**Archivo:** `backend/app/api/admin_routes.py`

```python
import secrets
import string


def _generate_password(length: int = 12) -> str:
    """Genera una contraseña aleatoria segura."""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return "".join(secrets.choice(alphabet) for _ in range(length))
```

**¿Por qué `secrets` y no `random`?**
- `secrets` usa un **generador criptográficamente seguro** (CSPRNG).
- `random` es predecible si se conoce la semilla — **no es seguro** para contraseñas.
- El alfabeto incluye: mayúsculas, minúsculas, dígitos y 8 caracteres especiales.
- Longitud por defecto: **12 caracteres** → ~71 bits de entropía.

### Uso en la Creación de Usuarios

```python
@router.post("/users", response_model=UserResponse, status_code=201)
async def create_user(user_data: UserCreate, ...):
    # Si no se proporcionó contraseña, generar una automáticamente
    plain_password = user_data.password if user_data.password else _generate_password()

    db_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hash_password(plain_password),  # ← bcrypt hash
        full_name=user_data.full_name,
        role=user_data.role,
        is_active=True,
    )
    db.add(db_user)
    db.commit()

    # Enviar credenciales por email (contraseña en texto plano, solo en este momento)
    await email_service.send_welcome_email(
        email=db_user.email,
        password=plain_password,  # ← Solo se envía una vez
        role=db_user.role.value,
    )
```

---

## 10. Configuración Centralizada

**Archivo:** `backend/app/config.py`

```python
class Settings(BaseSettings):
    """Configuración principal cargada desde variables de entorno (.env)."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Seguridad
    secret_key: str = Field(
        default="dev-secret-key-change-in-production-min-32-characters",
        description="Clave secreta para JWT y encriptación"
    )
    jwt_algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(
        default=480,  # 8 horas
        description="Duración del token en minutos"
    )

    # Email (2FA y notificaciones)
    mail_username: str = Field(default="")
    mail_password: str = Field(default="")
    mail_server: str = Field(default="smtp.gmail.com")
    mail_port: int = Field(default=587)
    mail_tls: bool = Field(default=True)
    mail_from: str = Field(default="noreply@evaluador.gob.bo")
    mail_from_name: str = Field(default="Evaluador GOB.BO")

    # Validaciones
    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, v):
        """La clave secreta debe tener mínimo 32 caracteres."""
        if len(v) < 32:
            raise ValueError(
                "La clave secreta debe tener al menos 32 caracteres"
            )
        return v

# Instancia global
settings = Settings()
```

**Variables de entorno requeridas (.env):**
```env
SECRET_KEY=mi-clave-secreta-de-al-menos-32-caracteres
DATABASE_URL=postgresql://user:pass@localhost:5432/gob_evaluator
MAIL_USERNAME=sistema@gmail.com
MAIL_PASSWORD=xxxx-xxxx-xxxx-xxxx    # Contraseña de aplicación de Google
```

---

## Resumen de Archivos del Sistema de Autenticación

| Archivo | Responsabilidad | Líneas |
|---------|----------------|--------|
| `auth/security.py` | Hashing bcrypt + Generación de JWT | 51 |
| `auth/dependencies.py` | Middleware JWT + RBAC (RoleChecker) | 107 |
| `api/auth_routes.py` | Endpoints de login y 2FA | 189 |
| `services/email_service.py` | Envío de correos (2FA, bienvenida) | 873 |
| `models/database_models.py` | Modelo User (SQLAlchemy ORM) | 114 |
| `config.py` | Configuración centralizada (.env) | 189 |

---

## Diagrama de Dependencias entre Módulos

```
                    ┌─────────────────────┐
                    │      config.py      │
                    │   (Settings/.env)   │
                    └──────────┬──────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
    ┌─────────────────┐ ┌───────────┐ ┌──────────────────┐
    │  security.py    │ │email_srv  │ │database_models.py│
    │ hash_password() │ │send_2fa() │ │   class User     │
    │ verify_password()│ │send_email()││   class UserRole │
    │ create_token()  │ └─────┬─────┘ └────────┬─────────┘
    └────────┬────────┘       │                │
             │                │                │
             ▼                ▼                ▼
    ┌──────────────────────────────────────────────────┐
    │              dependencies.py                      │
    │  get_current_user() → get_current_active_user()  │
    │         → RoleChecker (allow_superadmin, etc.)   │
    └──────────────────────┬───────────────────────────┘
                           │
                           ▼
    ┌──────────────────────────────────────────────────┐
    │              auth_routes.py                       │
    │  POST /login → POST /verify-2fa → GET /me        │
    └──────────────────────────────────────────────────┘
```

---

**Fin del Documento**
