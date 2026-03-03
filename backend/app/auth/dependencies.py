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
from sqlalchemy.orm import Session, joinedload

from app.config import settings
from app.database import get_db
from app.models.database_models import User, Permission

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

    user = (
        db.query(User)
        .options(joinedload(User.permissions))
        .filter(User.username == username)
        .first()
    )
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


class PermissionChecker:
    """
    Dependencia invocable para control de acceso basado en permisos granulares.

    Verifica que el usuario tenga al menos uno de los permisos requeridos.
    Los superadmins siempre tienen acceso (bypass).

    Uso:
        @router.post("/evaluations", dependencies=[Depends(PermissionChecker([Permission.EVALUATIONS_MANAGE]))])
        def create_evaluation(): ...

        O como parámetro:
        def endpoint(user: User = Depends(PermissionChecker([Permission.EVALUATIONS_MANAGE]))):
            ...
    """

    def __init__(self, required_permissions: list[Permission]):
        self.required_permissions = required_permissions

    def __call__(
        self, current_user: User = Depends(get_current_active_user)
    ) -> User:
        # Superadmin siempre tiene acceso
        if current_user.role.value == "superadmin":
            return current_user

        # Verificar si el usuario tiene al menos uno de los permisos requeridos
        user_permissions = {p.permission for p in current_user.permissions}

        has_permission = any(
            perm in user_permissions for perm in self.required_permissions
        )

        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos suficientes para realizar esta acción",
            )

        return current_user


# Instancias pre-construidas para uso directo en endpoints (basadas en roles)
allow_superadmin = RoleChecker(["superadmin"])
allow_admin_secretary = RoleChecker(["superadmin", "secretary"])
allow_admin_evaluator = RoleChecker(["superadmin", "evaluator"])
allow_all_staff = RoleChecker(["superadmin", "secretary", "evaluator"])
# Permitir admin, secretary Y evaluator para gestión de seguimientos
allow_staff_followups = RoleChecker(["superadmin", "secretary", "evaluator"])

# Instancias pre-construidas para uso directo en endpoints (basadas en permisos)
require_evaluations_manage = PermissionChecker([Permission.EVALUATIONS_MANAGE])
require_followups_manage = PermissionChecker([Permission.FOLLOWUPS_MANAGE])
require_users_manage = PermissionChecker([Permission.USERS_MANAGE])
require_institutions_manage = PermissionChecker([Permission.INSTITUTIONS_MANAGE])
require_reports_view = PermissionChecker([Permission.REPORTS_VIEW])
require_followups_view = PermissionChecker([Permission.FOLLOWUPS_VIEW])
require_followups_respond = PermissionChecker([Permission.FOLLOWUPS_RESPOND])
