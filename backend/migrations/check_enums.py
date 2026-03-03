"""
Script para verificar los valores de los enums en PostgreSQL.
"""
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    print("=" * 80)
    print("VALORES DE ENUMS EN POSTGRESQL")
    print("=" * 80)

    # Verificar enum userrole
    print("\nEnum: userrole")
    result = conn.execute(text("""
        SELECT enumlabel
        FROM pg_enum
        JOIN pg_type ON pg_enum.enumtypid = pg_type.oid
        WHERE pg_type.typname = 'userrole'
        ORDER BY enumsortorder
    """))

    roles = [row[0] for row in result]
    if roles:
        for role in roles:
            print(f"   - '{role}'")
    else:
        print("   [!] Enum no encontrado")

    # Verificar enum permission
    print("\nEnum: permission")
    result = conn.execute(text("""
        SELECT enumlabel
        FROM pg_enum
        JOIN pg_type ON pg_enum.enumtypid = pg_type.oid
        WHERE pg_type.typname = 'permission'
        ORDER BY enumsortorder
    """))

    perms = [row[0] for row in result]
    if perms:
        for perm in perms:
            print(f"   - '{perm}'")
    else:
        print("   [!] Enum no encontrado")

    print("\n" + "=" * 80)
