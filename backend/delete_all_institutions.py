"""
Script para eliminar todas las instituciones de la base de datos.
ADVERTENCIA: Este script elimina TODOS los datos de instituciones y sus usuarios asociados.
"""
import sys
import os

# Agregar el directorio backend al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.database_models import Institution, User, UserRole

def delete_all_institutions():
    """Elimina todas las instituciones y sus usuarios responsables."""
    db: Session = SessionLocal()
    try:
        # Contar instituciones
        count = db.query(Institution).count()
        
        if count == 0:
            print("[INFO] No hay instituciones para eliminar")
            return
        
        # Eliminar todos los usuarios EVALUATOR (responsables de instituciones)
        evaluators_deleted = db.query(User).filter(User.role == UserRole.EVALUATOR).delete()
        
        # Eliminar todas las instituciones
        institutions_deleted = db.query(Institution).delete()
        
        db.commit()
        print(f"[OK] Eliminadas {institutions_deleted} instituciones y {evaluators_deleted} usuarios responsables")
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Error al eliminar instituciones: {e}")
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    print("[ADVERTENCIA] Este script eliminará TODAS las instituciones y sus usuarios responsables")
    response = input("¿Está seguro de continuar? (escriba 'SI' para confirmar): ")
    
    if response == "SI":
        delete_all_institutions()
    else:
        print("[INFO] Operación cancelada")
