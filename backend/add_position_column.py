"""
Script para agregar la columna 'position' a la tabla users.
"""
import sys
import os

# Agregar el directorio backend al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from app.database import engine

def add_position_column():
    """Agrega la columna position a la tabla users."""
    try:
        with engine.connect() as conn:
            # Verificar si la columna ya existe (PostgreSQL)
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='users' AND column_name='position'
            """))
            
            if result.fetchone():
                print("[INFO] La columna 'position' ya existe en la tabla users")
                return
            
            # Agregar la columna
            conn.execute(text("ALTER TABLE users ADD COLUMN position VARCHAR(100)"))
            conn.commit()
            print("[OK] Columna 'position' agregada exitosamente a la tabla users")
    except Exception as e:
        print(f"[ERROR] Error al agregar la columna: {e}")
        sys.exit(1)

if __name__ == "__main__":
    add_position_column()
