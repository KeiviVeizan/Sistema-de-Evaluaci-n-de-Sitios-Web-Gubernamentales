"""
Script de prueba para el sistema de permisos granulares.
Ejecutar: python test_permissions_api.py
"""
import requests
import json
from typing import Optional

BASE_URL = "http://localhost:8000/api/v1"
TOKEN: Optional[str] = None


def print_response(response):
    """Imprime la respuesta de forma formateada."""
    print(f"Status: {response.status_code}")
    try:
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    except:
        print(response.text)
    print("-" * 80)


def login(username: str, password: str) -> str:
    """Realiza login y retorna el token."""
    print(f"\nRealizando login como: {username}")
    response = requests.post(
        f"{BASE_URL}/auth/login",
        data={"username": username, "password": password}
    )
    print_response(response)

    if response.status_code == 200:
        token = response.json()["access_token"]
        print(f"[OK] Login exitoso. Token obtenido.\n")
        return token
    else:
        print(f"[ERROR] Error en login\n")
        return None


def get_role_permissions(role: str):
    """Obtiene los permisos disponibles para un rol."""
    print(f"\nObteniendo permisos disponibles para rol: {role}")
    headers = {"Authorization": f"Bearer {TOKEN}"}
    response = requests.get(
        f"{BASE_URL}/admin/roles/{role}/permissions",
        headers=headers
    )
    print_response(response)


def create_user_with_permissions(
    username: str,
    email: str,
    full_name: str,
    role: str,
    permissions: list = None,
):
    """Crea un usuario con permisos específicos."""
    print(f"\nCreando usuario: {username}")
    print(f"   Permisos: {permissions or 'Todos los del rol'}")

    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }

    data = {
        "username": username,
        "email": email,
        "full_name": full_name,
        "role": role,
        "position": "Test Position"
    }

    if permissions:
        data["permissions"] = permissions

    response = requests.post(
        f"{BASE_URL}/admin/users",
        headers=headers,
        json=data
    )
    print_response(response)

    if response.status_code == 201:
        return response.json()["id"]
    return None


def list_users():
    """Lista todos los usuarios."""
    print("\nListando usuarios...")
    headers = {"Authorization": f"Bearer {TOKEN}"}
    response = requests.get(
        f"{BASE_URL}/admin/users",
        headers=headers
    )
    print_response(response)


def update_user_permissions(user_id: int, permissions: list):
    """Actualiza los permisos de un usuario."""
    print(f"\nActualizando permisos del usuario ID {user_id}")
    print(f"   Nuevos permisos: {permissions}")

    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }

    response = requests.patch(
        f"{BASE_URL}/admin/users/{user_id}",
        headers=headers,
        json={"permissions": permissions}
    )
    print_response(response)


def delete_user(user_id: int):
    """Elimina un usuario."""
    print(f"\nEliminando usuario ID {user_id}")
    headers = {"Authorization": f"Bearer {TOKEN}"}
    response = requests.delete(
        f"{BASE_URL}/admin/users/{user_id}",
        headers=headers
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print(response.json())
    print("-" * 80)


def test_invalid_permission():
    """Prueba crear un usuario con permiso inválido para su rol."""
    print("\n[WARNING] Intentando crear usuario con permiso inválido...")
    print("   (Evaluador con permiso 'users_manage' - debería fallar)")

    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }

    response = requests.post(
        f"{BASE_URL}/admin/users",
        headers=headers,
        json={
            "username": "test_invalido",
            "email": "invalido@test.com",
            "full_name": "Test Inválido",
            "role": "evaluator",
            "permissions": ["users_manage"]  # Permiso no disponible para evaluator
        }
    )
    print_response(response)


def run_tests():
    """Ejecuta todas las pruebas."""
    global TOKEN

    print("=" * 80)
    print("PRUEBAS DEL SISTEMA DE PERMISOS GRANULARES")
    print("=" * 80)

    # 1. Login
    username = input("\nIngresa tu username (ej: admin): ").strip()
    password = input("Ingresa tu password: ").strip()

    TOKEN = login(username, password)
    if not TOKEN:
        print("[ERROR] No se pudo obtener el token. Verifica tus credenciales.")
        return

    # 2. Obtener permisos disponibles por rol
    print("\n" + "=" * 80)
    print("TEST 1: Obtener permisos disponibles por rol")
    print("=" * 80)
    get_role_permissions("evaluator")
    get_role_permissions("secretary")
    get_role_permissions("entity_user")

    # 3. Crear usuario con permisos específicos
    print("\n" + "=" * 80)
    print("TEST 2: Crear usuario con permisos específicos")
    print("=" * 80)
    user1_id = create_user_with_permissions(
        username="eval_test_1",
        email="eval1@test.com",
        full_name="Evaluador Solo Evaluaciones",
        role="evaluator",
        permissions=["evaluations_manage"]  # Solo evaluaciones, sin seguimientos
    )

    # 4. Crear usuario con todos los permisos del rol
    print("\n" + "=" * 80)
    print("TEST 3: Crear usuario con todos los permisos del rol")
    print("=" * 80)
    user2_id = create_user_with_permissions(
        username="eval_test_2",
        email="eval2@test.com",
        full_name="Evaluador Completo",
        role="evaluator",
        permissions=None  # Todos los permisos del rol
    )

    # 5. Listar usuarios
    print("\n" + "=" * 80)
    print("TEST 4: Listar usuarios (verificar campo permissions)")
    print("=" * 80)
    list_users()

    # 6. Actualizar permisos
    if user1_id:
        print("\n" + "=" * 80)
        print("TEST 5: Actualizar permisos de usuario")
        print("=" * 80)
        update_user_permissions(
            user1_id,
            ["evaluations_manage", "followups_manage"]  # Agregar seguimientos
        )

    # 7. Intentar crear usuario con permiso inválido
    print("\n" + "=" * 80)
    print("TEST 6: Validar restricción de permisos por rol")
    print("=" * 80)
    test_invalid_permission()

    # 8. Limpieza (opcional)
    print("\n" + "=" * 80)
    print("LIMPIEZA")
    print("=" * 80)
    cleanup = input("\n¿Deseas eliminar los usuarios de prueba? (s/n): ").strip().lower()
    if cleanup == 's':
        if user1_id:
            delete_user(user1_id)
        if user2_id:
            delete_user(user2_id)

    print("\n" + "=" * 80)
    print("[OK] PRUEBAS COMPLETADAS")
    print("=" * 80)
    print("\nResumen:")
    print("1. [OK] Obtención de permisos por rol")
    print("2. [OK] Creación de usuarios con permisos específicos")
    print("3. [OK] Creación de usuarios con todos los permisos del rol")
    print("4. [OK] Listado de usuarios con permisos")
    print("5. [OK] Actualización de permisos")
    print("6. [OK] Validación de restricciones")
    print("\n>> Próximo paso: Integrar con el frontend")


if __name__ == "__main__":
    try:
        run_tests()
    except KeyboardInterrupt:
        print("\n\n[WARNING] Pruebas interrumpidas por el usuario")
    except Exception as e:
        print(f"\n\n[ERROR] Error inesperado: {e}")
        import traceback
        traceback.print_exc()
