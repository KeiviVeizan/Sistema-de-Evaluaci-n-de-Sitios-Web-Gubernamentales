# Casos de Uso Expandidos: Módulo de Gestión de Usuarios

**Versión:** 1.0  
**Fecha:** Febrero 2026  
**Módulo:** Sprint 1 - Gestión de Usuarios y Autenticación

---

## 1. Diagrama de Casos de Uso

### 1.1 Actores del Sistema

| Actor | Descripción | Tipo |
|-------|-------------|------|
| **Superadmin** | Administrador del sistema con acceso total | Principal |
| **Secretaría** | Personal administrativo con permisos de gestión | Principal |
| **Evaluador** | Personal técnico que realiza evaluaciones | Principal |
| **Usuario Entidad** | Responsable de institución gubernamental | Principal |
| **Sistema de Email** | Servicio SMTP para envío de notificaciones | Secundario |
| **Sistema JWT** | Servicio de generación de tokens de acceso | Secundario |

### 1.2 Diagrama Visual de Casos de Uso

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                    SISTEMA DE GESTIÓN DE USUARIOS                            │
│                                                                              │
│                                                                              │
│    ┌─────────────────┐         ┌─────────────────┐                          │
│    │  CU-01: Iniciar │         │  CU-02: Verificar│                         │
│    │    Sesión        │────────▶│   Código 2FA     │                         │
│    └────────┬────────┘         └────────┬────────┘                          │
│             │ <<include>>               │ <<include>>                       │
│             ▼                           ▼                                   │
│    ┌─────────────────┐         ┌─────────────────┐      ┌──────────┐       │
│    │  Validar         │         │  Generar Token   │      │ Sistema  │       │
│    │  Credenciales    │         │  JWT             │─────▶│  JWT     │       │
│    └─────────────────┘         └─────────────────┘      └──────────┘       │
│                                                                              │
│                                         ┌──────────┐                        │
│    ┌─────────────────┐                  │ Sistema  │                        │
│    │  CU-03: Crear   │─── <<include>> ─▶│  Email   │                        │
│    │    Usuario       │                  └──────────┘                        │
│    └─────────────────┘                                                      │
│                                                                              │
│    ┌─────────────────┐                                                      │
│    │  CU-04: Listar  │                                                      │
│    │   Usuarios       │                                                      │
│    └─────────────────┘                                                      │
│                                                                              │
│    ┌─────────────────┐                                                      │
│    │  CU-05: Editar  │                                                      │
│    │    Usuario       │                                                      │
│    └─────────────────┘                                                      │
│                                                                              │
│    ┌─────────────────┐                                                      │
│    │  CU-06: Eliminar│                                                      │
│    │    Usuario       │                                                      │
│    └─────────────────┘                                                      │
│                                                                              │
│    ┌─────────────────┐                                                      │
│    │  CU-07: Ver     │                                                      │
│    │  Perfil Propio   │                                                      │
│    └─────────────────┘                                                      │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

 ACCESO POR ROL:
 ══════════════════════════════════════════════════════════════════
 Superadmin ──────▶ CU-01, CU-02, CU-03, CU-04, CU-05, CU-06, CU-07
 Secretaría ─────▶ CU-01, CU-02, CU-04, CU-06 (solo entity_user), CU-07
 Evaluador ──────▶ CU-01, CU-02, CU-07
 Usuario Entidad ▶ CU-01, CU-02, CU-07
```

---

## 2. Casos de Uso Expandidos

---

### CU-01: Iniciar Sesión

| Campo | Detalle |
|-------|---------|
| **ID** | CU-01 |
| **Nombre** | Iniciar Sesión |
| **Actor Principal** | Superadmin, Secretaría, Evaluador, Usuario Entidad |
| **Actor Secundario** | Sistema de Email |
| **Descripción** | Permite a los usuarios autenticarse en el sistema ingresando sus credenciales. El sistema valida las credenciales y envía un código de verificación 2FA al correo electrónico del usuario. |
| **Prioridad** | Alta |
| **Precondiciones** | 1. El usuario debe estar registrado en el sistema. <br> 2. La cuenta del usuario debe estar activa (`is_active = true`). <br> 3. El usuario debe tener acceso a su correo electrónico. |
| **Postcondiciones** | 1. Se genera y envía un código 2FA de 6 dígitos al email del usuario. <br> 2. El sistema almacena el código temporalmente para verificación posterior (CU-02). |

**Flujo Principal:**

| Paso | Actor | Sistema |
|------|-------|---------|
| 1 | El usuario accede a la pantalla de login. | Muestra el formulario de inicio de sesión con campos: usuario/email y contraseña. |
| 2 | Ingresa su nombre de usuario (o email) y contraseña. | |
| 3 | Presiona el botón "Iniciar Sesión". | |
| 4 | | Busca al usuario por `username` o `email` en la base de datos. |
| 5 | | Verifica que la contraseña coincida con el hash almacenado (bcrypt). |
| 6 | | Verifica que la cuenta esté activa (`is_active = true`). |
| 7 | | Genera un código aleatorio de 6 dígitos. |
| 8 | | Almacena el código temporalmente en memoria. |
| 9 | | Envía el código al correo electrónico del usuario en segundo plano. |
| 10 | | Retorna mensaje: "Código de verificación enviado a tu correo electrónico." |
| 11 | El usuario revisa su correo electrónico. | |

**Flujos Alternativos:**

| ID | Condición | Acción |
|----|-----------|--------|
| FA-01 | Usuario no encontrado en BD | Retorna error 401: "Credenciales incorrectas". No se revela si el usuario existe o no (seguridad). |
| FA-02 | Contraseña incorrecta | Retorna error 401: "Credenciales incorrectas". Mismo mensaje que FA-01 para evitar enumeración de usuarios. |
| FA-03 | Cuenta desactivada (`is_active = false`) | Retorna error 403: "Usuario desactivado". El login se rechaza antes de generar el código 2FA. |
| FA-04 | Fallo en envío de email | El código se genera y almacena, pero puede no llegar al usuario. Se registra el error en logs. |

---

### CU-02: Verificar Código 2FA

| Campo | Detalle |
|-------|---------|
| **ID** | CU-02 |
| **Nombre** | Verificar Código de Autenticación en Dos Factores |
| **Actor Principal** | Superadmin, Secretaría, Evaluador, Usuario Entidad |
| **Actor Secundario** | Sistema JWT |
| **Descripción** | El usuario ingresa el código de verificación de 6 dígitos recibido por correo electrónico. El sistema valida el código y genera un token JWT para la sesión. |
| **Prioridad** | Alta |
| **Precondiciones** | 1. El usuario completó exitosamente el CU-01. <br> 2. Existe un código 2FA pendiente para el usuario. <br> 3. El código no ha sido utilizado previamente. |
| **Postcondiciones** | 1. Se genera un token JWT con los datos del usuario (username, role). <br> 2. El código 2FA se invalida (uso único). <br> 3. El usuario accede al sistema según su rol. |

**Flujo Principal:**

| Paso | Actor | Sistema |
|------|-------|---------|
| 1 | | Muestra el formulario de verificación 2FA con campo para código de 6 dígitos. |
| 2 | El usuario ingresa el código recibido por email. | |
| 3 | Presiona "Verificar". | |
| 4 | | Verifica que exista un código pendiente para el usuario. |
| 5 | | Compara el código ingresado con el almacenado. |
| 6 | | Busca al usuario en la base de datos para obtener sus datos. |
| 7 | | Elimina el código usado (un solo uso). |
| 8 | | Genera un token JWT con `sub: username` y `role: user.role`. |
| 9 | | Retorna el token JWT y los datos del usuario. |
| 10 | El navegador almacena el token JWT. | Redirige al dashboard correspondiente al rol del usuario. |

**Flujos Alternativos:**

| ID | Condición | Acción |
|----|-----------|--------|
| FA-01 | No existe código pendiente para el usuario | Retorna error 401: "No hay código pendiente para este usuario". El usuario debe reiniciar el login (CU-01). |
| FA-02 | Código incorrecto | Retorna error 401: "Código de verificación inválido". El código NO se invalida; el usuario puede reintentar. |
| FA-03 | Usuario no encontrado después de verificar código | Retorna error 404: "Usuario no encontrado". Caso raro (usuario eliminado entre CU-01 y CU-02). |

---

### CU-03: Crear Usuario

| Campo | Detalle |
|-------|---------|
| **ID** | CU-03 |
| **Nombre** | Crear Usuario Interno |
| **Actor Principal** | Superadmin |
| **Actor Secundario** | Sistema de Email |
| **Descripción** | Permite al Superadmin crear un nuevo usuario interno del sistema (superadmin, secretaría o evaluador). Se genera una contraseña segura automáticamente y se envían las credenciales al correo del nuevo usuario. |
| **Prioridad** | Alta |
| **Precondiciones** | 1. El actor debe tener rol `superadmin`. <br> 2. El actor debe estar autenticado con token JWT válido. <br> 3. El username y email del nuevo usuario no deben existir en el sistema. |
| **Postcondiciones** | 1. Se crea un nuevo registro en la tabla `users`. <br> 2. La contraseña se almacena encriptada con bcrypt. <br> 3. Se envía email de bienvenida con las credenciales al nuevo usuario. <br> 4. El nuevo usuario puede iniciar sesión inmediatamente. |

**Flujo Principal:**

| Paso | Actor | Sistema |
|------|-------|---------|
| 1 | El Superadmin accede al panel de Gestión de Usuarios. | Muestra la lista de usuarios existentes con botón "Crear Usuario". |
| 2 | Presiona "Crear Usuario". | Muestra formulario con campos: nombre de usuario, email, nombre completo, rol (selector), contraseña (opcional). |
| 3 | Completa los campos obligatorios: <br> - Username <br> - Email <br> - Rol (superadmin/secretary/evaluator) | |
| 4 | Opcionalmente ingresa un nombre completo y/o contraseña personalizada. | |
| 5 | Presiona "Guardar" o "Crear". | |
| 6 | | Verifica que el `username` no exista en la BD. |
| 7 | | Verifica que el `email` no exista en la BD. |
| 8 | | Si no se proporcionó contraseña, genera una aleatoria de 12 caracteres (letras, números, símbolos). |
| 9 | | Encripta la contraseña con bcrypt. |
| 10 | | Crea el registro en la tabla `users` con `is_active = true`. |
| 11 | | Envía email de bienvenida con username, contraseña y rol al correo del nuevo usuario. |
| 12 | | Retorna los datos del usuario creado (sin contraseña). |
| 13 | | Actualiza la lista de usuarios mostrando el nuevo registro. |

**Flujos Alternativos:**

| ID | Condición | Acción |
|----|-----------|--------|
| FA-01 | Username ya existe | Retorna error 400: "Ya existe un usuario con ese username". No se crea el usuario. |
| FA-02 | Email ya existe | Retorna error 400: "Ya existe un usuario con ese email". No se crea el usuario. |
| FA-03 | Actor no es Superadmin | Retorna error 403: "No tiene permisos". Endpoint protegido por `allow_superadmin`. |
| FA-04 | Fallo en envío de email | El usuario se crea exitosamente, pero las credenciales no llegan por correo. Se registra error en logs. |

---

### CU-04: Listar y Buscar Usuarios

| Campo | Detalle |
|-------|---------|
| **ID** | CU-04 |
| **Nombre** | Listar y Buscar Usuarios |
| **Actor Principal** | Superadmin, Secretaría |
| **Descripción** | Permite visualizar la lista completa de usuarios del sistema con opciones de búsqueda por nombre, email o username. La lista es paginada. |
| **Prioridad** | Media |
| **Precondiciones** | 1. El actor debe tener rol `superadmin` o `secretary`. <br> 2. El actor debe estar autenticado con token JWT válido. |
| **Postcondiciones** | 1. Se muestra la lista de usuarios con sus datos principales. |

**Flujo Principal:**

| Paso | Actor | Sistema |
|------|-------|---------|
| 1 | El actor accede al menú "Gestión de Usuarios". | |
| 2 | | Realiza consulta paginada a la tabla `users` (offset=0, limit=50). |
| 3 | | Retorna la lista de usuarios con: username, email, nombre completo, rol, estado, fecha de creación. |
| 4 | | Muestra la tabla de usuarios con total de registros. |
| 5 | (Opcional) El actor ingresa un término de búsqueda. | |
| 6 | | Filtra usuarios por coincidencia parcial (ILIKE) en username, email o full_name. |
| 7 | | Muestra los resultados filtrados con el conteo actualizado. |
| 8 | (Opcional) El actor navega entre páginas. | Carga la siguiente página ajustando el offset. |

**Flujos Alternativos:**

| ID | Condición | Acción |
|----|-----------|--------|
| FA-01 | No hay usuarios registrados | Muestra mensaje "No hay usuarios registrados" con lista vacía. |
| FA-02 | La búsqueda no encuentra resultados | Muestra mensaje "No se encontraron usuarios" con el término buscado. |
| FA-03 | Actor no tiene permisos | Retorna error 403: "No tiene permisos". |

---

### CU-05: Editar Usuario

| Campo | Detalle |
|-------|---------|
| **ID** | CU-05 |
| **Nombre** | Editar Datos de Usuario |
| **Actor Principal** | Superadmin |
| **Descripción** | Permite al Superadmin modificar los datos de un usuario existente, incluyendo su rol, estado (activo/inactivo), email y nombre completo. |
| **Prioridad** | Alta |
| **Precondiciones** | 1. El actor debe tener rol `superadmin`. <br> 2. El usuario a editar debe existir en el sistema. <br> 3. El actor debe estar autenticado con token JWT válido. |
| **Postcondiciones** | 1. Los datos del usuario se actualizan en la base de datos. <br> 2. Los cambios son efectivos inmediatamente. |

**Flujo Principal:**

| Paso | Actor | Sistema |
|------|-------|---------|
| 1 | El Superadmin identifica al usuario a editar en la lista (CU-04). | |
| 2 | Presiona el botón "Editar" del usuario seleccionado. | Muestra formulario precargado con los datos actuales del usuario. |
| 3 | Modifica los campos deseados: <br> - Email <br> - Nombre completo <br> - Rol <br> - Estado (activo/inactivo) | |
| 4 | Presiona "Guardar Cambios". | |
| 5 | | Valida que el nuevo email (si cambió) no esté en uso por otro usuario. |
| 6 | | Actualiza solo los campos que fueron modificados (PATCH parcial). |
| 7 | | Guarda los cambios en la base de datos. |
| 8 | | Retorna los datos actualizados del usuario. |
| 9 | | Actualiza la información mostrada en la interfaz. |

**Flujos Alternativos:**

| ID | Condición | Acción |
|----|-----------|--------|
| FA-01 | El nuevo email ya existe en otro usuario | Retorna error 400: "Ya existe un usuario con ese email". Los cambios no se aplican. |
| FA-02 | El usuario no existe (eliminado por otro admin) | Retorna error 404: "Usuario no encontrado". |
| FA-03 | Actor no es Superadmin | Retorna error 403: "No tiene permisos". |

---

### CU-06: Eliminar Usuario

| Campo | Detalle |
|-------|---------|
| **ID** | CU-06 |
| **Nombre** | Eliminar Usuario |
| **Actor Principal** | Superadmin, Secretaría |
| **Descripción** | Permite eliminar un usuario del sistema. El Superadmin puede eliminar cualquier usuario, mientras que la Secretaría solo puede eliminar usuarios con rol `entity_user`. No se permite la auto-eliminación. |
| **Prioridad** | Alta |
| **Precondiciones** | 1. El actor debe tener rol `superadmin` o `secretary`. <br> 2. El usuario a eliminar debe existir en el sistema. <br> 3. El actor no puede ser el mismo usuario a eliminar. <br> 4. Si el actor es `secretary`, el usuario a eliminar debe tener rol `entity_user`. |
| **Postcondiciones** | 1. El usuario se elimina permanentemente de la base de datos. <br> 2. Las notificaciones del usuario se eliminan en cascada. <br> 3. Las evaluaciones realizadas por el usuario conservan `evaluator_id = NULL`. |

**Flujo Principal:**

| Paso | Actor | Sistema |
|------|-------|---------|
| 1 | El actor identifica al usuario a eliminar en la lista (CU-04). | |
| 2 | Presiona el botón "Eliminar" del usuario seleccionado. | Muestra diálogo de confirmación: "¿Está seguro de eliminar al usuario [nombre]? Esta acción es irreversible." |
| 3 | Confirma la eliminación. | |
| 4 | | Verifica que el usuario a eliminar exista en la BD. |
| 5 | | Verifica que el actor tenga permisos sobre el rol del usuario a eliminar. |
| 6 | | Verifica que el actor no se esté eliminando a sí mismo. |
| 7 | | Elimina el registro del usuario (CASCADE elimina notificaciones). |
| 8 | | Retorna mensaje: "Usuario [nombre] eliminado exitosamente". |
| 9 | | Actualiza la lista de usuarios sin el registro eliminado. |

**Flujos Alternativos:**

| ID | Condición | Acción |
|----|-----------|--------|
| FA-01 | El usuario no existe | Retorna error 404: "Usuario no encontrado". |
| FA-02 | Secretaría intenta eliminar usuario no `entity_user` | Retorna error 403: "Solo puedes eliminar usuarios de tipo Entidad". |
| FA-03 | Auto-eliminación | Retorna error 400: "No puedes eliminarte a ti mismo". |
| FA-04 | El actor cancela la confirmación | Se cierra el diálogo y no se realiza ninguna acción. |

---

### CU-07: Ver Perfil Propio

| Campo | Detalle |
|-------|---------|
| **ID** | CU-07 |
| **Nombre** | Ver Perfil del Usuario Actual |
| **Actor Principal** | Superadmin, Secretaría, Evaluador, Usuario Entidad |
| **Descripción** | Permite a cualquier usuario autenticado consultar sus propios datos de perfil (nombre, email, rol, institución asociada, fecha de creación). |
| **Prioridad** | Baja |
| **Precondiciones** | 1. El actor debe estar autenticado con token JWT válido. <br> 2. La cuenta del actor debe estar activa. |
| **Postcondiciones** | 1. Se muestran los datos del perfil del usuario autenticado. |

**Flujo Principal:**

| Paso | Actor | Sistema |
|------|-------|---------|
| 1 | El usuario accede a la opción "Mi Perfil" en el menú o navbar. | |
| 2 | | Extrae el `username` del token JWT del header `Authorization`. |
| 3 | | Busca al usuario en la BD y verifica que esté activo. |
| 4 | | Retorna los datos del perfil: id, username, email, full_name, position, role, institution_id, is_active, created_at. |
| 5 | | Muestra la información del perfil en la interfaz. |

**Flujos Alternativos:**

| ID | Condición | Acción |
|----|-----------|--------|
| FA-01 | Token JWT expirado o inválido | Retorna error 401: "Token inválido". Redirige a la pantalla de login. |
| FA-02 | Cuenta desactivada | Retorna error 403: "Usuario desactivado". Se cierra la sesión. |

---

## 3. Matriz de Permisos (RBAC)

| Caso de Uso | Superadmin | Secretaría | Evaluador | Usuario Entidad |
|-------------|:----------:|:----------:|:---------:|:---------------:|
| CU-01: Iniciar Sesión | ✅ | ✅ | ✅ | ✅ |
| CU-02: Verificar 2FA | ✅ | ✅ | ✅ | ✅ |
| CU-03: Crear Usuario | ✅ | ❌ | ❌ | ❌ |
| CU-04: Listar Usuarios | ✅ | ✅ | ❌ | ❌ |
| CU-05: Editar Usuario | ✅ | ❌ | ❌ | ❌ |
| CU-06: Eliminar Usuario | ✅ | ⚠️ Solo entity_user | ❌ | ❌ |
| CU-07: Ver Perfil Propio | ✅ | ✅ | ✅ | ✅ |

**Leyenda:** ✅ = Permitido | ❌ = Denegado | ⚠️ = Permitido con restricciones

---

## 4. Reglas de Negocio

| ID | Regla | Descripción |
|----|-------|-------------|
| RN-01 | Autenticación en dos pasos | Todo inicio de sesión requiere validación de credenciales + código 2FA por email. |
| RN-02 | Contraseña segura | Las contraseñas generadas automáticamente tienen 12 caracteres con letras, números y símbolos. |
| RN-03 | Unicidad de credenciales | No pueden existir dos usuarios con el mismo `username` o `email`. |
| RN-04 | Encriptación de contraseñas | Todas las contraseñas se almacenan encriptadas con bcrypt. |
| RN-05 | Código 2FA de uso único | Cada código de verificación solo puede ser utilizado una vez. |
| RN-06 | Protección contra auto-eliminación | Un usuario no puede eliminar su propia cuenta. |
| RN-07 | Restricción de eliminación para Secretaría | La Secretaría solo puede eliminar usuarios de tipo `entity_user`. |
| RN-08 | Token JWT | El token contiene `sub` (username) y `role` para autorización RBAC. |
| RN-09 | Seguridad en mensajes de error | Los errores de login no revelan si el username existe (mismos mensajes para usuario no encontrado y contraseña incorrecta). |
| RN-10 | Notificación por email | Al crear un usuario, se envían las credenciales por correo electrónico. |

---

## 5. Requisitos No Funcionales

| ID | Requisito | Descripción |
|----|-----------|-------------|
| RNF-01 | Rendimiento | El login debe responder en menos de 2 segundos. |
| RNF-02 | Seguridad | Las contraseñas deben estar encriptadas con bcrypt (mínimo 12 rounds). |
| RNF-03 | Disponibilidad | El sistema de autenticación debe estar disponible 99.5% del tiempo. |
| RNF-04 | Escalabilidad | La lista de usuarios debe soportar paginación para más de 1000 registros. |
| RNF-05 | Auditoría | Todas las operaciones CRUD se registran en logs con (quién, qué, cuándo). |
| RNF-06 | Compatibilidad | El token JWT debe ser compatible con cualquier cliente HTTP (web, mobile). |

---

## 6. Trazabilidad

### 6.1 Endpoints REST asociados

| Caso de Uso | Método | Endpoint | Guard |
|-------------|--------|----------|-------|
| CU-01 | POST | `/api/auth/login` | Público |
| CU-02 | POST | `/api/auth/verify-2fa` | Público |
| CU-03 | POST | `/api/admin/users` | `allow_superadmin` |
| CU-04 | GET | `/api/admin/users` | `allow_admin_secretary` |
| CU-05 | PATCH | `/api/admin/users/{user_id}` | `allow_superadmin` |
| CU-06 | DELETE | `/api/admin/users/{user_id}` | `allow_admin_secretary` |
| CU-07 | GET | `/api/auth/me` | `get_current_active_user` |

### 6.2 Modelos de datos involucrados

| Caso de Uso | Tablas | Operación |
|-------------|--------|-----------|
| CU-01 | users | SELECT |
| CU-02 | users | SELECT |
| CU-03 | users | INSERT |
| CU-04 | users | SELECT |
| CU-05 | users | UPDATE |
| CU-06 | users, notifications | DELETE (CASCADE) |
| CU-07 | users | SELECT |

### 6.3 Componentes Frontend asociados

| Caso de Uso | Componente | Ruta |
|-------------|------------|------|
| CU-01 | `Login.jsx` | `/login` |
| CU-02 | `Login.jsx` (paso 2) | `/login` |
| CU-03 | `Users.jsx` (modal) | `/admin/users` |
| CU-04 | `Users.jsx` | `/admin/users` |
| CU-05 | `Users.jsx` (modal edición) | `/admin/users` |
| CU-06 | `Users.jsx` (botón eliminar) | `/admin/users` |
| CU-07 | `Navbar` / componente de perfil | Global |

---

**Fin del Documento**
