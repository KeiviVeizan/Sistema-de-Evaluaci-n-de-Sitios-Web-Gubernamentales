"""
Migración: Agregar tabla notifications y columna evaluator_id en evaluations.
Ejecutar: python migrations/003_add_notifications.py
"""
from app.database import engine
from sqlalchemy import text


def run_migration():
    print("Ejecutando migración: notifications + evaluator_id...")

    with engine.connect() as conn:
        try:
            # 1. Agregar columna evaluator_id a evaluations
            print("  - Agregando evaluator_id a evaluations...")
            conn.execute(text("""
                ALTER TABLE evaluations
                ADD COLUMN IF NOT EXISTS evaluator_id INTEGER REFERENCES users(id) ON DELETE SET NULL
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_evaluations_evaluator ON evaluations(evaluator_id)
            """))
            conn.commit()
            print("    OK Columna evaluator_id agregada")

            # 2. Crear tabla notifications
            print("  - Creando tabla notifications...")
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS notifications (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    type VARCHAR(50) NOT NULL,
                    title VARCHAR(255) NOT NULL,
                    message TEXT NOT NULL,
                    link VARCHAR(500),
                    read BOOLEAN NOT NULL DEFAULT FALSE,
                    email_sent BOOLEAN NOT NULL DEFAULT FALSE,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW()
                )
            """))
            conn.commit()
            print("    OK Tabla notifications creada")

            # 3. Crear índices
            print("  - Creando índices...")
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id)
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_notifications_created_at ON notifications(created_at)
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_notifications_read ON notifications(read) WHERE read = FALSE
            """))
            conn.commit()
            print("    OK Índices creados")

            print("\nMigración completada exitosamente!")

        except Exception as e:
            print(f"Error: {e}")
            conn.rollback()
            raise


if __name__ == "__main__":
    run_migration()
