"""
Script para eliminar y recrear completamente la tabla criteria_results
"""
import sys
import os
from pathlib import Path

# Asegurar UTF-8 en Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Agregar el directorio raíz al path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine, text
from app.config import settings


def recreate_criteria_results_table():
    """
    Elimina y recrea la tabla criteria_results completamente
    """
    engine = create_engine(settings.database_url)

    print("Conectando a la base de datos...")

    with engine.connect() as conn:
        # 1. Eliminar la tabla completamente
        print("Eliminando tabla criteria_results...")
        try:
            conn.execute(text("DROP TABLE IF EXISTS criteria_results CASCADE;"))
            conn.commit()
            print("✓ Tabla eliminada")
        except Exception as e:
            print(f"⚠ Error al eliminar tabla: {e}")
            conn.rollback()
            return

        # 2. Crear la tabla desde cero
        print("Creando tabla criteria_results...")
        try:
            conn.execute(text("""
                CREATE TABLE criteria_results (
                    id SERIAL PRIMARY KEY,
                    evaluation_id INTEGER NOT NULL REFERENCES evaluations(id) ON DELETE CASCADE,
                    criteria_id VARCHAR(50) NOT NULL,
                    criteria_name VARCHAR(255) NOT NULL,
                    dimension VARCHAR(50) NOT NULL,
                    lineamiento VARCHAR(255) NOT NULL,
                    status VARCHAR(20) NOT NULL,
                    score FLOAT NOT NULL,
                    max_score FLOAT NOT NULL,
                    details JSONB,
                    evidence JSONB,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW()
                );
            """))
            conn.commit()
            print("✓ Tabla creada")
        except Exception as e:
            print(f"✗ Error al crear tabla: {e}")
            conn.rollback()
            return

        # 3. Crear índices
        print("Creando índices...")
        try:
            conn.execute(text("""
                CREATE INDEX idx_criteria_results_evaluation_id ON criteria_results(evaluation_id);
                CREATE INDEX idx_criteria_results_criteria_id ON criteria_results(criteria_id);
                CREATE INDEX idx_criteria_results_dimension ON criteria_results(dimension);
            """))
            conn.commit()
            print("✓ Índices creados")
        except Exception as e:
            print(f"⚠ Error al crear índices: {e}")
            conn.rollback()

        print("\n✓ Tabla criteria_results recreada exitosamente")


if __name__ == "__main__":
    try:
        recreate_criteria_results_table()
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
