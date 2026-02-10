"""
Script de semilla (seed) para crear usuarios de prueba.

Se ejecuta al iniciar la aplicación. Solo crea usuarios si no existen.
"""

import logging

from sqlalchemy.orm import Session

from app.models.database_models import User, UserRole
from app.auth.security import hash_password

logger = logging.getLogger(__name__)

SEED_USERS = [
    {
        "username": "admin",
        "email": "admin@adsib.gob.bo",
        "password": "Admin2024!",
        "role": UserRole.SUPERADMIN,
        "full_name": "Administrador ADSIB",
    },
    {
        "username": "secre",
        "email": "secretaria@adsib.gob.bo",
        "password": "Secre2024!",
        "role": UserRole.SECRETARY,
        "full_name": "Secretaría ADSIB",
    },
    {
        "username": "tech",
        "email": "evaluador@adsib.gob.bo",
        "password": "Tech2024!",
        "role": UserRole.EVALUATOR,
        "full_name": "Evaluador Técnico",
    },
]


def seed_users(db: Session) -> None:
    """
    Crea usuarios de prueba si no existen en la base de datos.

    Todos se crean sin institution_id (personal interno de AGETIC).
    """
    created = 0

    for user_data in SEED_USERS:
        existing = db.query(User).filter(
            User.username == user_data["username"]
        ).first()

        if existing:
            logger.debug(f"Seed: usuario '{user_data['username']}' ya existe, omitiendo")
            continue

        user = User(
            username=user_data["username"],
            email=user_data["email"],
            hashed_password=hash_password(user_data["password"]),
            full_name=user_data["full_name"],
            role=user_data["role"],
        )
        db.add(user)
        created += 1
        logger.info(
            f"  Seed: creado {user_data['username']} "
            f"({user_data['role'].value}) / {user_data['password']}"
        )

    if created > 0:
        db.commit()
        logger.info(f"[OK] {created} usuario(s) seed creados")
    else:
        logger.info("[OK] Usuarios seed ya existen, sin cambios")
