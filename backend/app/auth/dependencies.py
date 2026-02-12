"""
Dependencias de autenticación y autorización (RBAC) para FastAPI.

Provee:
- get_current_user: Decodifica JWT y retorna el usuario autenticado
- get_current_active_user: Verifica que el usuario esté activo
- RoleChecker: Clase invocable que verifica roles permitidos
- Instancias pre-construidas para combinaciones comunes de roles
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.database_models import User

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

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user


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


# Instancias pre-construidas para uso directo en endpoints
allow_superadmin = RoleChecker(["superadmin"])
allow_admin_secretary = RoleChecker(["superadmin", "secretary"])
allow_admin_evaluator = RoleChecker(["superadmin", "evaluator"])
allow_all_staff = RoleChecker(["superadmin", "secretary", "evaluator"])
# Permitir admin, secretary Y evaluator para gestión de seguimientos
allow_staff_followups = RoleChecker(["superadmin", "secretary", "evaluator"])
