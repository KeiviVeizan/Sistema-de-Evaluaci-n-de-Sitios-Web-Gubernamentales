"""
Script para cambiar rol de usuario.
Ejecutar: python change_user_role.py
"""
from app.database import SessionLocal
from app.models.database_models import User


def change_role():
    db = SessionLocal()

    try:
        email = input("Email del usuario: ")

        user = db.query(User).filter(User.email == email).first()

        if not user:
            print(f"x Usuario '{email}' no encontrado")
            return

        print(f"\nUsuario: {user.email}")
        print(f"Rol actual: {user.role}")

        print("\nRoles disponibles:")
        print("  1. superadmin")
        print("  2. secretary")
        print("  3. evaluator")
        print("  4. entity_user")

        new_role = input("\nNuevo rol: ")

        user.role = new_role
        db.commit()

        print(f"\nv Rol actualizado a: {new_role}")

    except Exception as e:
        print(f"x Error: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    change_role()
