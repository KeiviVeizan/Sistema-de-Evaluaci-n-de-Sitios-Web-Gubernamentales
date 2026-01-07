"""
Migración para actualizar la tabla criteria_results
Agrega las columnas necesarias para el nuevo esquema de evaluación
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


def migrate_criteria_result_table():
    """
    Migra la tabla criteria_results al nuevo esquema
    """
    engine = create_engine(settings.database_url)

    print("Conectando a la base de datos...")

    with engine.connect() as conn:
        print("Verificando estructura actual de criteria_results...")

        # Verificar si la tabla existe
        result = conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = 'criteria_results'
            );
        """))

        table_exists = result.scalar()

        if not table_exists:
            print("La tabla criteria_results no existe. Creando desde cero...")
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

                CREATE INDEX idx_criteria_results_evaluation_id ON criteria_results(evaluation_id);
                CREATE INDEX idx_criteria_results_criteria_id ON criteria_results(criteria_id);
            """))
            conn.commit()
            print("✓ Tabla criteria_results creada exitosamente")
            return

        print("La tabla existe. Verificando columnas...")

        # Verificar columnas existentes
        result = conn.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'criteria_results';
        """))

        existing_columns = {row[0] for row in result}
        print(f"Columnas existentes: {existing_columns}")

        # Primero, cambiar la columna status de ENUM a VARCHAR si existe
        print("Verificando tipo de columna status...")
        try:
            # Eliminar la columna status antigua si existe con tipo ENUM
            conn.execute(text("""
                DO $$
                BEGIN
                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name = 'criteria_results'
                        AND column_name = 'status'
                    ) THEN
                        ALTER TABLE criteria_results DROP COLUMN status;
                    END IF;
                END $$;
            """))
            conn.commit()
            print("✓ Columna status antigua eliminada")
        except Exception as e:
            print(f"⚠ Error al eliminar columna status: {e}")
            conn.rollback()

        # Columnas requeridas
        required_columns = {
            'criteria_id': 'VARCHAR(50) NOT NULL',
            'criteria_name': 'VARCHAR(255) NOT NULL',
            'dimension': 'VARCHAR(50) NOT NULL',
            'lineamiento': 'VARCHAR(255) NOT NULL',
            'status': 'VARCHAR(20) NOT NULL',
            'score': 'FLOAT NOT NULL DEFAULT 0',
            'max_score': 'FLOAT NOT NULL DEFAULT 0',
            'details': 'JSONB',
            'evidence': 'JSONB',
            'created_at': 'TIMESTAMP NOT NULL DEFAULT NOW()'
        }

        # Columnas a eliminar (del esquema antiguo)
        columns_to_drop = {'criteria_type', 'criteria_code'}

        # Eliminar columnas antiguas
        for col in columns_to_drop:
            if col in existing_columns:
                print(f"Eliminando columna antigua '{col}'...")
                try:
                    conn.execute(text(f"ALTER TABLE criteria_results DROP COLUMN IF EXISTS {col};"))
                    conn.commit()
                    print(f"✓ Columna '{col}' eliminada")
                except Exception as e:
                    print(f"⚠ Error al eliminar '{col}': {e}")
                    conn.rollback()

        # Agregar o modificar columnas requeridas
        for col_name, col_type in required_columns.items():
            if col_name not in existing_columns:
                print(f"Agregando columna '{col_name}'...")
                try:
                    conn.execute(text(f"ALTER TABLE criteria_results ADD COLUMN {col_name} {col_type};"))
                    conn.commit()
                    print(f"✓ Columna '{col_name}' agregada")
                except Exception as e:
                    print(f"⚠ Error al agregar '{col_name}': {e}")
                    conn.rollback()
            else:
                print(f"✓ Columna '{col_name}' ya existe")

        # Crear índices si no existen
        print("Creando índices...")
        try:
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_criteria_results_evaluation_id
                ON criteria_results(evaluation_id);

                CREATE INDEX IF NOT EXISTS idx_criteria_results_criteria_id
                ON criteria_results(criteria_id);

                CREATE INDEX IF NOT EXISTS idx_criteria_results_dimension
                ON criteria_results(dimension);
            """))
            conn.commit()
            print("✓ Índices creados")
        except Exception as e:
            print(f"⚠ Error al crear índices: {e}")
            conn.rollback()

        print("\n✓ Migración completada exitosamente")


if __name__ == "__main__":
    try:
        migrate_criteria_result_table()
    except Exception as e:
        print(f"\n✗ Error durante la migración: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
