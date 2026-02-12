"""
Script para migrar la tabla followups con las nuevas columnas.
Ejecutar: python migrate_followups.py
"""

from app.database import engine
from sqlalchemy import text

def migrate_followups():
    print("Migrando tabla followups...")
    
    with engine.connect() as conn:
        # 1. Eliminar tabla vieja
        print("  - Eliminando tabla vieja...")
        conn.execute(text("DROP TABLE IF EXISTS followups CASCADE"))
        conn.commit()
        
        # 2. Crear tabla nueva
        print("  - Creando tabla nueva...")
        conn.execute(text("""
            CREATE TABLE followups (
                id SERIAL PRIMARY KEY,
                evaluation_id INTEGER NOT NULL REFERENCES evaluations(id) ON DELETE CASCADE,
                criteria_result_id INTEGER NOT NULL REFERENCES criteria_results(id) ON DELETE CASCADE,
                due_date TIMESTAMP NOT NULL,
                status VARCHAR(20) NOT NULL DEFAULT 'pending',
                notes TEXT,
                created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                corrected_at TIMESTAMP,
                corrected_by_user_id INTEGER REFERENCES users(id),
                validated_at TIMESTAMP,
                validated_by_user_id INTEGER REFERENCES users(id),
                validation_notes TEXT
            )
        """))
        conn.commit()
        
        # 3. Crear índices
        print("  - Creando indices...")
        conn.execute(text("CREATE INDEX idx_followups_evaluation ON followups(evaluation_id)"))
        conn.execute(text("CREATE INDEX idx_followups_criteria_result ON followups(criteria_result_id)"))
        conn.execute(text("CREATE INDEX idx_followups_status ON followups(status)"))
        conn.commit()
        
        print("Migracion completada exitosamente!")

if __name__ == "__main__":
    migrate_followups()
