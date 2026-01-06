"""
Script para agregar la columna robots_txt a la tabla extracted_content.
"""

import sys
import io
from pathlib import Path

# Configurar encoding UTF-8 para Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Agregar el directorio app al path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import text
from app.database import engine

def add_robots_txt_column():
    """Agrega la columna robots_txt a la tabla extracted_content si no existe."""

    with engine.connect() as conn:
        try:
            # Verificar si la columna ya existe
            result = conn.execute(text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name='extracted_content'
                AND column_name='robots_txt';
            """))

            if result.fetchone():
                print("✓ La columna 'robots_txt' ya existe")
                return

            # Agregar la columna
            print("Agregando columna 'robots_txt' a la tabla 'extracted_content'...")
            conn.execute(text("""
                ALTER TABLE extracted_content
                ADD COLUMN robots_txt JSON;
            """))
            conn.commit()

            print("✓ Columna 'robots_txt' agregada exitosamente")

        except Exception as e:
            print(f"✗ Error: {e}")
            conn.rollback()

if __name__ == "__main__":
    add_robots_txt_column()
