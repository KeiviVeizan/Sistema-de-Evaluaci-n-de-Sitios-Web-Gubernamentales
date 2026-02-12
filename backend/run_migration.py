"""
Script para ejecutar migración 2FA.
Ejecutar: python run_migration.py
"""

from app.database import engine
from sqlalchemy import text


def run_migration():
    print("Ejecutando migración 2FA...")

    with engine.connect() as conn:
        try:
            conn.execute(text("""
                ALTER TABLE users
                    ADD COLUMN IF NOT EXISTS two_factor_enabled BOOLEAN NOT NULL DEFAULT FALSE,
                    ADD COLUMN IF NOT EXISTS two_factor_secret VARCHAR(255),
                    ADD COLUMN IF NOT EXISTS two_factor_backup_codes TEXT[]
            """))
            conn.commit()
            print("[OK] Migracion completada exitosamente")

            # Verificar columnas creadas
            result = conn.execute(text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'users'
                AND column_name LIKE '%two_factor%'
                ORDER BY column_name
            """))

            columns = [row[0] for row in result]
            if columns:
                print(f"[OK] Columnas 2FA en BD: {', '.join(columns)}")
            else:
                print("[WARN] No se encontraron columnas two_factor (puede que ya existieran)")

        except Exception as e:
            print(f"[ERROR] {e}")
            conn.rollback()


if __name__ == "__main__":
    run_migration()
