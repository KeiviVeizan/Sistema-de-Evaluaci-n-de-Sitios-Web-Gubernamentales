"""
Migración: Agregar tabla user_permissions para permisos granulares (versión 2).
Ejecutar: python migrations/004_add_user_permissions_v2.py
"""
import sys
from pathlib import Path

# Agregar el directorio backend al path para importar app
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.database import engine
from sqlalchemy import text


def run_migration():
    print("Ejecutando migración: user_permissions (v2 - limpia y recrea)...")

    with engine.connect() as conn:
        try:
            # 1. Eliminar tabla si existe (para poder recrear el enum)
            print("  - Eliminando tabla user_permissions si existe...")
            conn.execute(text("DROP TABLE IF EXISTS user_permissions CASCADE"))
            conn.commit()
            print("    OK Tabla eliminada")

            # 2. Eliminar tipo enum si existe
            print("  - Eliminando tipo permission si existe...")
            conn.execute(text("DROP TYPE IF EXISTS permission CASCADE"))
            conn.commit()
            print("    OK Tipo eliminado")

            # 3. Crear tipo enum
            print("  - Creando tipo enum permission...")
            conn.execute(text("""
                CREATE TYPE permission AS ENUM (
                    'evaluations_manage',
                    'followups_manage',
                    'users_manage',
                    'institutions_manage',
                    'reports_view',
                    'followups_view',
                    'followups_respond'
                )
            """))
            conn.commit()
            print("    OK Tipo permission creado")

            # 4. Crear tabla user_permissions
            print("  - Creando tabla user_permissions...")
            conn.execute(text("""
                CREATE TABLE user_permissions (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    permission permission NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW()
                )
            """))
            conn.commit()
            print("    OK Tabla user_permissions creada")

            # 5. Crear índices
            print("  - Creando índices...")
            conn.execute(text("""
                CREATE INDEX idx_user_permissions_user ON user_permissions(user_id)
            """))
            conn.execute(text("""
                CREATE INDEX idx_user_permissions_permission ON user_permissions(permission)
            """))
            conn.commit()
            print("    OK Índices creados")

            print("\n✅ Migración completada exitosamente!")
            print("\n📝 NOTA IMPORTANTE:")
            print("   - La tabla user_permissions fue creada vacía.")
            print("   - Los permisos se asignarán automáticamente al crear nuevos usuarios.")
            print("   - Para usuarios existentes, ejecuta el script de asignación manual:")
            print("     python migrations/004_assign_permissions_to_existing_users.py")

        except Exception as e:
            print(f"\n❌ Error: {e}")
            conn.rollback()
            raise


if __name__ == "__main__":
    run_migration()
