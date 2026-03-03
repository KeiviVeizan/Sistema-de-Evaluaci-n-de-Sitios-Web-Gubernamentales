"""
Script opcional: Asignar permisos por defecto a usuarios existentes.
Ejecutar: python migrations/004_assign_permissions_to_existing_users.py

Este script asigna permisos por defecto a todos los usuarios que no tienen permisos asignados.
"""
import sys
from pathlib import Path

# Agregar el directorio backend al path para importar app
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.database import engine
from sqlalchemy import text


def assign_permissions_to_existing_users():
    """Asigna permisos por defecto a usuarios existentes sin permisos."""
    print("Asignando permisos a usuarios existentes...\n")

    with engine.connect() as conn:
        try:
            # Verificar si hay usuarios
            result = conn.execute(text("SELECT COUNT(*) FROM users"))
            user_count = result.scalar()

            if user_count == 0:
                print("[INFO] No hay usuarios en la base de datos.")
                return

            print(f"[INFO] Total de usuarios: {user_count}\n")

            # Evaluadores: evaluations_manage y followups_manage
            print("Asignando permisos a Evaluadores...")
            result = conn.execute(text("""
                INSERT INTO user_permissions (user_id, permission)
                SELECT id, CAST('evaluations_manage' AS permission)
                FROM users
                WHERE role = 'EVALUATOR'
                  AND NOT EXISTS (
                      SELECT 1 FROM user_permissions
                      WHERE user_permissions.user_id = users.id
                  )
            """))
            evaluators_updated = result.rowcount

            conn.execute(text("""
                INSERT INTO user_permissions (user_id, permission)
                SELECT id, CAST('followups_manage' AS permission)
                FROM users
                WHERE role = 'EVALUATOR'
                  AND EXISTS (
                      SELECT 1 FROM user_permissions
                      WHERE user_permissions.user_id = users.id
                        AND permission = 'evaluations_manage'
                  )
            """))
            conn.commit()
            if evaluators_updated > 0:
                print(f"   [OK] {evaluators_updated} evaluadores actualizados")
            else:
                print(f"   [SKIP] Evaluadores ya tienen permisos")

            # Secretarios: todos los permisos
            print("Asignando permisos a Secretarios...")
            secretary_permissions = [
                'users_manage',
                'institutions_manage',
                'reports_view',
                'evaluations_manage',
                'followups_manage'
            ]

            secretaries_updated = 0
            for perm in secretary_permissions:
                result = conn.execute(text(f"""
                    INSERT INTO user_permissions (user_id, permission)
                    SELECT id, CAST('{perm}' AS permission)
                    FROM users
                    WHERE role = 'SECRETARY'
                      AND NOT EXISTS (
                          SELECT 1 FROM user_permissions
                          WHERE user_permissions.user_id = users.id
                            AND permission = '{perm}'
                      )
                """))
                if perm == 'users_manage':
                    secretaries_updated = result.rowcount

            conn.commit()
            if secretaries_updated > 0:
                print(f"   [OK] {secretaries_updated} secretarios actualizados")
            else:
                print(f"   [SKIP] Secretarios ya tienen permisos")

            # Usuarios de entidad: followups_view y followups_respond
            print("Asignando permisos a Usuarios de Entidad...")
            result = conn.execute(text("""
                INSERT INTO user_permissions (user_id, permission)
                SELECT id, CAST('followups_view' AS permission)
                FROM users
                WHERE role = 'ENTITY_USER'
                  AND NOT EXISTS (
                      SELECT 1 FROM user_permissions
                      WHERE user_permissions.user_id = users.id
                  )
            """))
            entities_updated = result.rowcount

            conn.execute(text("""
                INSERT INTO user_permissions (user_id, permission)
                SELECT id, CAST('followups_respond' AS permission)
                FROM users
                WHERE role = 'ENTITY_USER'
                  AND EXISTS (
                      SELECT 1 FROM user_permissions
                      WHERE user_permissions.user_id = users.id
                        AND permission = 'followups_view'
                  )
            """))
            conn.commit()
            if entities_updated > 0:
                print(f"   [OK] {entities_updated} usuarios de entidad actualizados")
            else:
                print(f"   [SKIP] Usuarios de entidad ya tienen permisos")

            # Superadmins
            result = conn.execute(text("SELECT COUNT(*) FROM users WHERE role = 'SUPERADMIN'"))
            superadmin_count = result.scalar()
            if superadmin_count > 0:
                print(f"{superadmin_count} Superadmins - No requieren permisos granulares")

            print("\n[OK] Proceso completado!")

        except Exception as e:
            print(f"\n[ERROR] Error: {e}")
            conn.rollback()
            raise


if __name__ == "__main__":
    assign_permissions_to_existing_users()
