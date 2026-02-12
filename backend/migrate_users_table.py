"""
Script para agregar columnas faltantes a tabla users.
Ejecutar: python migrate_users_table.py
"""
from app.database import engine
from sqlalchemy import text


def migrate_users():
    print("Migrando tabla users...")

    with engine.connect() as conn:
        # 1. Agregar columnas 2FA si no existen
        print("  - Agregando columnas 2FA...")

        try:
            conn.execute(text("""
                ALTER TABLE users 
                ADD COLUMN IF NOT EXISTS two_factor_enabled BOOLEAN DEFAULT FALSE,
                ADD COLUMN IF NOT EXISTS two_factor_secret VARCHAR(255),
                ADD COLUMN IF NOT EXISTS two_factor_backup_codes TEXT[]
            """))
            conn.commit()
            print("    v Columnas 2FA agregadas")
        except Exception as e:
            print(f"    ! Error agregando 2FA: {e}")

        # 2. Verificar columnas
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users'
            ORDER BY ordinal_position
        """))

        columns = [row[0] for row in result]
        print(f"\n  Columnas en tabla users: {', '.join(columns)}")

        # 3. Verificar roles existentes
        result = conn.execute(text("SELECT DISTINCT role FROM users"))
        roles = [row[0] for row in result]
        print(f"\n  Roles existentes: {', '.join(roles)}")

        print("\nv Migracion completada!")


if __name__ == "__main__":
    migrate_users()
