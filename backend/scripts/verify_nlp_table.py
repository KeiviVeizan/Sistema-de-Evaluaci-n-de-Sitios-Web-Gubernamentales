#!/usr/bin/env python3
"""
Script de verificación de la tabla nlp_analysis.

Verifica que la migración se ejecutó correctamente:
- Tabla existe
- Columnas correctas
- Índices creados
- Constraints activos
- Relación con evaluations

Uso:
    python verify_nlp_table.py

Variables de entorno requeridas (o valores por defecto):
    DATABASE_URL: URL de conexión PostgreSQL
    POSTGRES_HOST: localhost
    POSTGRES_PORT: 5432
    POSTGRES_USER: postgres
    POSTGRES_PASSWORD: postgres
    POSTGRES_DB: gob_bo_evaluator
"""

import os
import sys
import logging
from typing import Dict, List, Any, Optional

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)

# Colores ANSI para terminal
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def get_database_url() -> str:
    """
    Obtiene URL de conexión a PostgreSQL.

    Returns:
        URL de conexión en formato SQLAlchemy
    """
    # Primero intentar DATABASE_URL completa
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        return database_url

    # Construir desde variables individuales
    host = os.getenv('POSTGRES_HOST', 'localhost')
    port = os.getenv('POSTGRES_PORT', '5432')
    user = os.getenv('POSTGRES_USER', 'postgres')
    password = os.getenv('POSTGRES_PASSWORD', 'postgres')
    db = os.getenv('POSTGRES_DB', 'gob_bo_evaluator')

    return f"postgresql://{user}:{password}@{host}:{port}/{db}"


def connect_database():
    """
    Conecta a la base de datos.

    Returns:
        Conexión SQLAlchemy

    Raises:
        SystemExit: Si no puede conectar
    """
    try:
        from sqlalchemy import create_engine, text
        from sqlalchemy.orm import sessionmaker

        url = get_database_url()
        logger.info(f"Conectando a: {url.replace(url.split(':')[2].split('@')[0], '****')}")

        engine = create_engine(url)
        Session = sessionmaker(bind=engine)
        session = Session()

        # Test conexión
        session.execute(text("SELECT 1"))
        logger.info(f"{Colors.GREEN}✓ Conexión exitosa{Colors.RESET}")

        return engine, session

    except ImportError:
        logger.error(f"{Colors.RED}Error: SQLAlchemy no instalado{Colors.RESET}")
        logger.error("Ejecutar: pip install sqlalchemy psycopg2-binary")
        sys.exit(1)
    except Exception as e:
        logger.error(f"{Colors.RED}Error de conexión: {e}{Colors.RESET}")
        sys.exit(1)


def verify_table_exists(session) -> bool:
    """
    Verifica que la tabla nlp_analysis existe.

    Args:
        session: Sesión SQLAlchemy

    Returns:
        True si existe
    """
    from sqlalchemy import text

    result = session.execute(text("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables
            WHERE table_name = 'nlp_analysis'
        );
    """)).scalar()

    return result


def get_table_columns(session) -> List[Dict[str, Any]]:
    """
    Obtiene información de columnas de la tabla.

    Args:
        session: Sesión SQLAlchemy

    Returns:
        Lista de diccionarios con info de columnas
    """
    from sqlalchemy import text

    result = session.execute(text("""
        SELECT
            column_name,
            data_type,
            is_nullable,
            column_default
        FROM information_schema.columns
        WHERE table_name = 'nlp_analysis'
        ORDER BY ordinal_position;
    """))

    return [dict(row._mapping) for row in result]


def get_table_indexes(session) -> List[Dict[str, Any]]:
    """
    Obtiene información de índices de la tabla.

    Args:
        session: Sesión SQLAlchemy

    Returns:
        Lista de diccionarios con info de índices
    """
    from sqlalchemy import text

    result = session.execute(text("""
        SELECT
            indexname,
            indexdef
        FROM pg_indexes
        WHERE tablename = 'nlp_analysis';
    """))

    return [dict(row._mapping) for row in result]


def get_table_constraints(session) -> List[Dict[str, Any]]:
    """
    Obtiene constraints de la tabla.

    Args:
        session: Sesión SQLAlchemy

    Returns:
        Lista de diccionarios con info de constraints
    """
    from sqlalchemy import text

    result = session.execute(text("""
        SELECT
            conname as constraint_name,
            contype as constraint_type,
            pg_get_constraintdef(oid) as definition
        FROM pg_constraint
        WHERE conrelid = 'nlp_analysis'::regclass;
    """))

    return [dict(row._mapping) for row in result]


def get_foreign_keys(session) -> List[Dict[str, Any]]:
    """
    Obtiene foreign keys de la tabla.

    Args:
        session: Sesión SQLAlchemy

    Returns:
        Lista de diccionarios con info de FKs
    """
    from sqlalchemy import text

    result = session.execute(text("""
        SELECT
            tc.constraint_name,
            kcu.column_name,
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name
        FROM information_schema.table_constraints AS tc
        JOIN information_schema.key_column_usage AS kcu
            ON tc.constraint_name = kcu.constraint_name
        JOIN information_schema.constraint_column_usage AS ccu
            ON ccu.constraint_name = tc.constraint_name
        WHERE tc.table_name = 'nlp_analysis'
            AND tc.constraint_type = 'FOREIGN KEY';
    """))

    return [dict(row._mapping) for row in result]


def print_verification_report(
    table_exists: bool,
    columns: List[Dict],
    indexes: List[Dict],
    constraints: List[Dict],
    foreign_keys: List[Dict]
) -> bool:
    """
    Imprime reporte de verificación.

    Args:
        table_exists: Si la tabla existe
        columns: Info de columnas
        indexes: Info de índices
        constraints: Info de constraints
        foreign_keys: Info de FKs

    Returns:
        True si todo está correcto
    """
    all_ok = True

    print(f"\n{Colors.BOLD}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}  REPORTE DE VERIFICACIÓN - nlp_analysis{Colors.RESET}")
    print(f"{Colors.BOLD}{'='*60}{Colors.RESET}")

    # 1. Tabla existe
    print(f"\n{Colors.BLUE}[1] EXISTENCIA DE TABLA{Colors.RESET}")
    if table_exists:
        print(f"    {Colors.GREEN}✓ Tabla nlp_analysis existe{Colors.RESET}")
    else:
        print(f"    {Colors.RED}✗ Tabla nlp_analysis NO existe{Colors.RESET}")
        all_ok = False
        return all_ok

    # 2. Columnas
    print(f"\n{Colors.BLUE}[2] COLUMNAS ({len(columns)} encontradas){Colors.RESET}")

    expected_columns = {
        'id': 'integer',
        'evaluation_id': 'integer',
        'nlp_global_score': 'double precision',
        'coherence_score': 'double precision',
        'ambiguity_score': 'double precision',
        'clarity_score': 'double precision',
        'coherence_details': 'jsonb',
        'ambiguity_details': 'jsonb',
        'clarity_details': 'jsonb',
        'recommendations': 'ARRAY',
        'wcag_compliance': 'jsonb',
        'analyzed_at': 'timestamp',
        'created_at': 'timestamp',
        'updated_at': 'timestamp'
    }

    found_columns = {col['column_name']: col['data_type'] for col in columns}

    for col_name, expected_type in expected_columns.items():
        if col_name in found_columns:
            actual_type = found_columns[col_name]
            if expected_type.lower() in actual_type.lower():
                print(f"    {Colors.GREEN}✓ {col_name}: {actual_type}{Colors.RESET}")
            else:
                print(f"    {Colors.YELLOW}⚠ {col_name}: {actual_type} (esperado: {expected_type}){Colors.RESET}")
        else:
            print(f"    {Colors.RED}✗ {col_name}: NO ENCONTRADA{Colors.RESET}")
            all_ok = False

    # 3. Índices
    print(f"\n{Colors.BLUE}[3] ÍNDICES ({len(indexes)} encontrados){Colors.RESET}")

    expected_indexes = [
        'idx_nlp_evaluation_id',
        'idx_nlp_global_score',
        'idx_nlp_analyzed_at'
    ]

    found_index_names = [idx['indexname'] for idx in indexes]

    for idx_name in expected_indexes:
        if idx_name in found_index_names:
            print(f"    {Colors.GREEN}✓ {idx_name}{Colors.RESET}")
        else:
            print(f"    {Colors.RED}✗ {idx_name}: NO ENCONTRADO{Colors.RESET}")
            all_ok = False

    # Mostrar índices adicionales
    for idx in indexes:
        if idx['indexname'] not in expected_indexes:
            print(f"    {Colors.YELLOW}+ {idx['indexname']}{Colors.RESET}")

    # 4. Constraints
    print(f"\n{Colors.BLUE}[4] CONSTRAINTS ({len(constraints)} encontrados){Colors.RESET}")

    constraint_types = {
        'p': 'PRIMARY KEY',
        'f': 'FOREIGN KEY',
        'u': 'UNIQUE',
        'c': 'CHECK'
    }

    for con in constraints:
        con_type = constraint_types.get(con['constraint_type'], con['constraint_type'])
        print(f"    {Colors.GREEN}✓ {con['constraint_name']} ({con_type}){Colors.RESET}")

    # 5. Foreign Keys
    print(f"\n{Colors.BLUE}[5] FOREIGN KEYS ({len(foreign_keys)} encontradas){Colors.RESET}")

    has_evaluation_fk = any(
        fk['foreign_table_name'] == 'evaluations'
        for fk in foreign_keys
    )

    if has_evaluation_fk:
        print(f"    {Colors.GREEN}✓ FK a evaluations.id{Colors.RESET}")
    else:
        print(f"    {Colors.RED}✗ FK a evaluations NO ENCONTRADA{Colors.RESET}")
        all_ok = False

    # Resumen
    print(f"\n{Colors.BOLD}{'='*60}{Colors.RESET}")
    if all_ok:
        print(f"{Colors.GREEN}{Colors.BOLD}  VERIFICACIÓN EXITOSA{Colors.RESET}")
        print(f"{Colors.GREEN}  Todos los componentes están correctos{Colors.RESET}")
    else:
        print(f"{Colors.RED}{Colors.BOLD}  VERIFICACIÓN FALLIDA{Colors.RESET}")
        print(f"{Colors.RED}  Revisar los errores anteriores{Colors.RESET}")
    print(f"{Colors.BOLD}{'='*60}{Colors.RESET}\n")

    return all_ok


def main():
    """Función principal."""
    print(f"\n{Colors.BOLD}{'#'*60}{Colors.RESET}")
    print(f"{Colors.BOLD}#  VERIFICACIÓN DE TABLA nlp_analysis{' '*19}#{Colors.RESET}")
    print(f"{Colors.BOLD}{'#'*60}{Colors.RESET}\n")

    # Conectar
    engine, session = connect_database()

    try:
        # Verificaciones
        table_exists = verify_table_exists(session)

        if table_exists:
            columns = get_table_columns(session)
            indexes = get_table_indexes(session)
            constraints = get_table_constraints(session)
            foreign_keys = get_foreign_keys(session)
        else:
            columns = []
            indexes = []
            constraints = []
            foreign_keys = []

        # Reporte
        success = print_verification_report(
            table_exists=table_exists,
            columns=columns,
            indexes=indexes,
            constraints=constraints,
            foreign_keys=foreign_keys
        )

        sys.exit(0 if success else 1)

    finally:
        session.close()


if __name__ == "__main__":
    main()
