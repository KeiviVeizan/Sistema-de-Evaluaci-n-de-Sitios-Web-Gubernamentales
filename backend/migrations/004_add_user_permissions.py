"""
Migración: Agregar tabla user_permissions para permisos granulares.
Ejecutar: python migrations/004_add_user_permissions.py
"""
import sys
from pathlib import Path

# Agregar el directorio backend al path para importar app
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.database import engine
from sqlalchemy import text


def run_migration():
    print("Ejecutando migración: user_permissions...")

    with engine.connect() as conn:
        try:
            # 1. Crear tipo enum para permisos
            print("  - Creando tipo enum Permission...")
            conn.execute(text("""
                DO $$ BEGIN
                    CREATE TYPE permission AS ENUM (
                        'evaluations_manage',
                        'followups_manage',
                        'users_manage',
                        'institutions_manage',
                        'reports_view',
                        'followups_view',
                        'followups_respond'
                    );
                EXCEPTION
                    WHEN duplicate_object THEN null;
                END $$;
            """))
            conn.commit()
            print("    OK Tipo Permission creado/verificado")

            # 2. Crear tabla user_permissions
            print("  - Creando tabla user_permissions...")
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS user_permissions (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    permission permission NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW()
                )
            """))
            conn.commit()
            print("    OK Tabla user_permissions creada")

            # 3. Crear índices
            print("  - Creando índices...")
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_user_permissions_user ON user_permissions(user_id)
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_user_permissions_permission ON user_permissions(permission)
            """))
            conn.commit()
            print("    OK Índices creados")

            # 4. Asignar permisos por defecto a usuarios existentes
            print("  - Asignando permisos por defecto a usuarios existentes...")

            # Verificar si hay usuarios antes de insertar permisos
            result = conn.execute(text("SELECT COUNT(*) FROM users"))
            user_count = result.scalar()

            if user_count > 0:
                # Evaluadores: evaluations_manage y followups_manage
                conn.execute(text("""
                    INSERT INTO user_permissions (user_id, permission)
                    SELECT id, CAST('evaluations_manage' AS permission)
                    FROM users
                    WHERE role = 'evaluator'
                """))
                conn.execute(text("""
                    INSERT INTO user_permissions (user_id, permission)
                    SELECT id, CAST('followups_manage' AS permission)
                    FROM users
                    WHERE role = 'evaluator'
                """))

                # Secretarios: todos los permisos (insertar uno por uno)
                secretary_permissions = [
                    'users_manage',
                    'institutions_manage',
                    'reports_view',
                    'evaluations_manage',
                    'followups_manage'
                ]
                for perm in secretary_permissions:
                    conn.execute(text(f"""
                        INSERT INTO user_permissions (user_id, permission)
                        SELECT id, CAST('{perm}' AS permission)
                        FROM users
                        WHERE role = 'secretary'
                    """))

                # Usuarios de entidad: followups_view y followups_respond
                conn.execute(text("""
                    INSERT INTO user_permissions (user_id, permission)
                    SELECT id, CAST('followups_view' AS permission)
                    FROM users
                    WHERE role = 'entity_user'
                """))
                conn.execute(text("""
                    INSERT INTO user_permissions (user_id, permission)
                    SELECT id, CAST('followups_respond' AS permission)
                    FROM users
                    WHERE role = 'entity_user'
                """))

                conn.commit()
                print(f"    OK Permisos por defecto asignados a {user_count} usuarios")
            else:
                conn.commit()
                print("    OK No hay usuarios existentes, saltando asignación de permisos")

            print("\nMigración completada exitosamente!")
            print("\nNOTA: Los superadmins no requieren permisos granulares,")
            print("      tienen acceso completo al sistema por defecto.")

        except Exception as e:
            print(f"Error: {e}")
            conn.rollback()
            raise


if __name__ == "__main__":
    run_migration()
