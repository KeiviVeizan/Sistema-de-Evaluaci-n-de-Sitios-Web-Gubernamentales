"""
Script para debuggear usuario y resetear contrasena si es necesario.
Ejecutar: python debug_user.py
"""
from app.database import SessionLocal
from app.models.database_models import User
from app.auth.security import hash_password, verify_password


def debug_user():
    db = SessionLocal()

    try:
        email = input("Email del usuario a debuggear: ")

        user = db.query(User).filter(User.email == email).first()

        if not user:
            print(f"Usuario '{email}' no encontrado")
            return

        print("\n=== INFO DEL USUARIO ===")
        print(f"Email: {user.email}")
        print(f"Rol: {user.role}")
        print(f"Activo: {user.is_active}")
        print(f"2FA habilitado: {getattr(user, 'two_factor_enabled', 'N/A')}")
        print(f"Institucion ID: {user.institution_id}")
        print(f"Hash contrasena: {user.hashed_password[:50]}...")

        # Probar contrasena
        test_password = input("\nIngresa la contrasena para probar: ")

        if verify_password(test_password, user.hashed_password):
            print("Contrasena CORRECTA")
        else:
            print("Contrasena INCORRECTA")

            reset = input("\nResetear contrasena? (s/n): ")
            if reset.lower() == 's':
                new_pass = input("Nueva contrasena: ")
                user.hashed_password = hash_password(new_pass)

                # Asegurar que este activo
                user.is_active = True

                db.commit()
                print(f"Contrasena actualizada a: {new_pass}")
                print(f"Usuario activado: {user.is_active}")

    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        db.close()


if __name__ == "__main__":
    debug_user()
