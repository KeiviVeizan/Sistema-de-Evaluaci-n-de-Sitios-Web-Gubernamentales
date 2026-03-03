# Guía de Pruebas - Sistema de Permisos Granulares

## 1. Ejecutar Migración

Primero, ejecuta la migración para crear la tabla `user_permissions`:

```bash
cd e:/ADSIB/gob-bo-evaluator/backend
python migrations/004_add_user_permissions.py
```

Esta migración:
- ✅ Crea el tipo enum `Permission`
- ✅ Crea la tabla `user_permissions`
- ✅ Crea índices para optimizar consultas
- ✅ Asigna permisos por defecto a usuarios existentes

## 2. Iniciar el Servidor

```bash
# Asegúrate de estar en el directorio backend
cd e:/ADSIB/gob-bo-evaluator/backend

# Activa el entorno virtual si no lo está
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Inicia el servidor
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 3. Probar Endpoints

### 3.1 Login (Obtener Token)

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=tu_password"
```

Guarda el `access_token` que recibes en la respuesta.

### 3.2 Obtener Permisos Disponibles por Rol

Obtener permisos disponibles para el rol "evaluator":

```bash
curl -X GET "http://localhost:8000/api/v1/admin/roles/evaluator/permissions" \
  -H "Authorization: Bearer TU_TOKEN_AQUI"
```

Respuesta esperada:
```json
{
  "role": "evaluator",
  "available_permissions": [
    {
      "value": "evaluations_manage",
      "label": "Gestionar Evaluaciones",
      "description": "Crear y realizar evaluaciones de sitios web"
    },
    {
      "value": "followups_manage",
      "label": "Gestionar Seguimientos",
      "description": "Crear y validar seguimientos de criterios no cumplidos"
    }
  ]
}
```

### 3.3 Crear Usuario con Permisos Específicos

Crear un evaluador que solo puede gestionar evaluaciones (sin seguimientos):

```bash
curl -X POST "http://localhost:8000/api/v1/admin/users" \
  -H "Authorization: Bearer TU_TOKEN_AQUI" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "evaluador_test",
    "email": "evaluador@test.com",
    "full_name": "Evaluador de Prueba",
    "role": "evaluator",
    "position": "Evaluador Junior",
    "permissions": ["evaluations_manage"]
  }'
```

### 3.4 Crear Usuario con Todos los Permisos del Rol

Si no especificas `permissions`, se asignan todos los permisos del rol:

```bash
curl -X POST "http://localhost:8000/api/v1/admin/users" \
  -H "Authorization: Bearer TU_TOKEN_AQUI" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "evaluador_completo",
    "email": "evaluador2@test.com",
    "full_name": "Evaluador Completo",
    "role": "evaluator",
    "position": "Evaluador Senior"
  }'
```

Este usuario tendrá ambos permisos: `evaluations_manage` y `followups_manage`.

### 3.5 Listar Usuarios (Ver Permisos)

```bash
curl -X GET "http://localhost:8000/api/v1/admin/users" \
  -H "Authorization: Bearer TU_TOKEN_AQUI"
```

La respuesta incluirá el campo `permissions` para cada usuario:

```json
{
  "total": 5,
  "items": [
    {
      "id": 1,
      "username": "evaluador_test",
      "email": "evaluador@test.com",
      "full_name": "Evaluador de Prueba",
      "role": "evaluator",
      "permissions": ["evaluations_manage"],
      ...
    }
  ]
}
```

### 3.6 Actualizar Permisos de un Usuario

```bash
curl -X PATCH "http://localhost:8000/api/v1/admin/users/1" \
  -H "Authorization: Bearer TU_TOKEN_AQUI" \
  -H "Content-Type: application/json" \
  -d '{
    "permissions": ["evaluations_manage", "followups_manage"]
  }'
```

## 4. Validar Funcionamiento

### 4.1 Verificar Permisos en la Base de Datos

```sql
-- Ver todos los usuarios con sus permisos
SELECT
    u.id,
    u.username,
    u.role,
    array_agg(up.permission) as permissions
FROM users u
LEFT JOIN user_permissions up ON u.id = up.user_id
GROUP BY u.id, u.username, u.role
ORDER BY u.id;
```

### 4.2 Verificar Restricción de Permisos

Intenta crear un usuario con un permiso que no corresponde a su rol:

```bash
curl -X POST "http://localhost:8000/api/v1/admin/users" \
  -H "Authorization: Bearer TU_TOKEN_AQUI" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "test_invalido",
    "email": "test@test.com",
    "full_name": "Test Inválido",
    "role": "evaluator",
    "permissions": ["users_manage"]
  }'
```

Deberías recibir un error 400:
```json
{
  "detail": "El permiso 'users_manage' no está disponible para el rol 'evaluator'"
}
```

## 5. Permisos por Rol

### Evaluator (evaluator)
- ✅ `evaluations_manage` - Gestionar Evaluaciones
- ✅ `followups_manage` - Gestionar Seguimientos

### Secretary (secretary)
- ✅ `users_manage` - Gestionar Usuarios
- ✅ `institutions_manage` - Gestionar Instituciones
- ✅ `reports_view` - Ver Reportes
- ✅ `evaluations_manage` - Gestionar Evaluaciones
- ✅ `followups_manage` - Gestionar Seguimientos

### Entity User (entity_user)
- ✅ `followups_view` - Ver Seguimientos
- ✅ `followups_respond` - Responder Seguimientos

### Superadmin (superadmin)
- ✅ Acceso completo (no requiere permisos específicos)

## 6. Próximos Pasos

Una vez verificado que el backend funciona correctamente:

1. ✅ Todos los endpoints responden correctamente
2. ✅ Los permisos se guardan en la base de datos
3. ✅ Las validaciones funcionan
4. ⏭️ Integrar con el frontend (modal de usuarios)

## Notas Importantes

- Los **superadmins** no requieren permisos granulares, tienen acceso completo por defecto
- Si no se especifican permisos al crear un usuario, se asignan **todos los permisos del rol**
- Los permisos se pueden actualizar en cualquier momento usando PATCH `/admin/users/{id}`
- La migración asigna automáticamente permisos por defecto a usuarios existentes
