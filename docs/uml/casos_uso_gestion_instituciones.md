# Casos de Uso Expandidos: Módulo de Gestión de Instituciones

**Versión:** 1.0  
**Fecha:** Febrero 2026  
**Módulo:** Sprint 2 - Gestión de Instituciones Gubernamentales

---

## 1. Diagrama de Casos de Uso

### 1.1 Actores del Sistema

| Actor | Descripción | Tipo |
|-------|-------------|------|
| **Superadmin** | Administrador con acceso total al sistema | Principal |
| **Secretaría** | Personal administrativo que gestiona instituciones | Principal |
| **Evaluador** | Personal técnico que consulta instituciones | Principal |
| **Sistema de Email** | Servicio SMTP para envío de credenciales | Secundario |
| **Sistema de Contraseñas** | Generador criptográfico de contraseñas seguras | Secundario |

### 1.2 Diagrama Visual de Casos de Uso

```
┌────────────────────────────────────────────────────────────────────────────────┐
│                    MÓDULO DE GESTIÓN DE INSTITUCIONES                           │
│                                                                                │
│    ┌─────────────────────┐                                                     │
│    │ CU-08: Registrar    │──── <<include>> ──▶ Crear Usuario Responsable       │
│    │   Institución       │──── <<include>> ──▶ Enviar Credenciales por Email   │
│    └─────────────────────┘                                                     │
│                                                                                │
│    ┌─────────────────────┐                                                     │
│    │ CU-09: Listar y     │                                                     │
│    │ Buscar Instituciones│                                                     │
│    └────────┬────────────┘                                                     │
│             │ <<extend>>                                                       │
│             ▼                                                                  │
│    ┌─────────────────────┐                                                     │
│    │ CU-10: Ver Detalle  │──── <<include>> ──▶ Ver Responsable                 │
│    │   de Institución    │──── <<include>> ──▶ Ver Historial de Evaluaciones   │
│    └─────────────────────┘                                                     │
│                                                                                │
│    ┌─────────────────────┐                                                     │
│    │ CU-11: Editar       │──── <<extend>> ──▶ Actualizar Datos Responsable     │
│    │   Institución       │                                                     │
│    └─────────────────────┘                                                     │
│                                                                                │
│    ┌─────────────────────┐                                                     │
│    │ CU-12: Eliminar     │──── <<include>> ──▶ Eliminar Usuarios Asociados     │
│    │   Institución       │                    (CASCADE)                         │
│    └─────────────────────┘                                                     │
│                                                                                │
└────────────────────────────────────────────────────────────────────────────────┘

 ACCESO POR ROL:
 ═══════════════════════════════════════════════════════════════════
 Superadmin ──────▶ CU-08, CU-09, CU-10, CU-11, CU-12
 Secretaría ─────▶ CU-08, CU-09, CU-10, CU-11
 Evaluador ──────▶ CU-09, CU-10
```

---

## 2. Casos de Uso Expandidos

---

### CU-08: Registrar Institución

| Campo | Detalle |
|-------|---------|
| **ID** | CU-08 |
| **Nombre** | Registrar Institución Gubernamental |
| **Actor Principal** | Superadmin, Secretaría |
| **Actor Secundario** | Sistema de Email, Sistema de Contraseñas |
| **Descripción** | Permite registrar una nueva institución gubernamental en el sistema. Al registrarla, se crea automáticamente un usuario responsable (`entity_user`) vinculado a la institución y se le envían las credenciales de acceso por correo electrónico. |
| **Prioridad** | Alta |
| **Precondiciones** | 1. El actor debe tener rol `superadmin` o `secretary`. <br> 2. El actor debe estar autenticado con token JWT válido. <br> 3. El dominio de la institución no debe existir ya en el sistema. <br> 4. El email del responsable no debe estar registrado en otro usuario. |
| **Postcondiciones** | 1. Se crea un nuevo registro en la tabla `institutions`. <br> 2. Se crea un usuario con rol `entity_user` vinculado a la institución. <br> 3. Se genera una contraseña aleatoria de 12 caracteres. <br> 4. Se envía email de bienvenida con credenciales al responsable. <br> 5. El responsable puede iniciar sesión inmediatamente. |

**Flujo Principal:**

| Paso | Actor | Sistema |
|------|-------|---------|
| 1 | El actor accede al panel de Gestión de Instituciones. | Muestra la lista de instituciones registradas con botón "Registrar Institución". |
| 2 | Presiona "Registrar Institución". | Muestra modal con formulario de registro. |
| 3 | Completa los datos de la institución: <br> - Nombre de la institución <br> - Dominio web (ej: `miinstitución.gob.bo`) | |
| 4 | Completa los datos del responsable: <br> - Nombre del contacto <br> - Email del contacto <br> - Cargo del contacto | |
| 5 | Presiona "Guardar". | |
| 6 | | Verifica que el `dominio` no exista en la tabla `institutions`. |
| 7 | | Verifica que el `email de contacto` no exista en la tabla `users`. |
| 8 | | Crea el registro de la institución con `is_active = true`. |
| 9 | | Genera un `username` a partir del email (parte antes del @, reemplazando puntos por guiones bajos). |
| 10 | | Verifica que el `username` generado sea único; si no, le agrega el ID de la institución como sufijo. |
| 11 | | Genera una contraseña aleatoria segura de 12 caracteres (letras, dígitos, símbolos). |
| 12 | | Encripta la contraseña con bcrypt. |
| 13 | | Crea el usuario responsable con rol `entity_user`, vinculado a la institución (`institution_id`). |
| 14 | | Envía email de bienvenida con las credenciales (email, contraseña, nombre de institución). |
| 15 | | Retorna los datos de la institución, el usuario creado y la contraseña generada. |
| 16 | | Muestra modal de credenciales con la contraseña generada y opción de copiar. |
| 17 | El actor puede copiar la contraseña y/o cerrar el modal. | Actualiza la lista de instituciones con el nuevo registro. |

**Flujos Alternativos:**

| ID | Condición | Acción |
|----|-----------|--------|
| FA-01 | Dominio ya registrado | Retorna error 400: "Ya existe una institución con el dominio [dominio]". No se crea nada. |
| FA-02 | Email del contacto ya existe | Retorna error 400: "Ya existe un usuario con el correo [email]". No se crea nada. |
| FA-03 | Username generado duplicado | Se agrega el ID de la institución al username (ej: `juan_perez_15`). El proceso continúa normalmente. |
| FA-04 | Fallo en envío de email | La institución y el usuario se crean exitosamente, pero las credenciales no llegan al responsable. La contraseña se muestra en el modal de credenciales. |
| FA-05 | Actor sin permisos | Retorna error 403: "No tiene permisos para realizar esta acción". |

---

### CU-09: Listar y Buscar Instituciones

| Campo | Detalle |
|-------|---------|
| **ID** | CU-09 |
| **Nombre** | Listar y Buscar Instituciones |
| **Actor Principal** | Superadmin, Secretaría, Evaluador |
| **Descripción** | Permite visualizar la lista de instituciones registradas con opciones de filtrado por búsqueda textual, letra inicial del nombre, y dominio exacto. La lista es paginada y muestra tarjetas con información básica de cada institución. |
| **Prioridad** | Media |
| **Precondiciones** | 1. El actor debe tener rol `superadmin`, `secretary` o `evaluator`. <br> 2. El actor debe estar autenticado con token JWT válido. |
| **Postcondiciones** | 1. Se muestra la lista paginada de instituciones con sus datos principales. |

**Flujo Principal:**

| Paso | Actor | Sistema |
|------|-------|---------|
| 1 | El actor accede al menú "Instituciones". | |
| 2 | | Realiza consulta paginada a `institutions` (offset=0, limit=50). |
| 3 | | Retorna la lista de instituciones con: nombre, dominio, estado, fecha de creación. |
| 4 | | Muestra las instituciones como tarjetas (`InstitutionCard`) con un alfabeto navegable (A-Z). |
| 5 | (Opcional) El actor ingresa un término en el buscador. | Filtra instituciones por coincidencia parcial en el nombre (ILIKE). |
| 6 | (Opcional) El actor hace clic en una letra del alfabeto (A-Z). | Filtra instituciones cuyo nombre inicia con esa letra. |
| 7 | (Opcional) El actor filtra por dominio exacto. | Filtra por dominio normalizado (con/sin `www.`). |
| 8 | El actor hace clic en una tarjeta de institución. | Navega al detalle de la institución (CU-10). |

**Flujos Alternativos:**

| ID | Condición | Acción |
|----|-----------|--------|
| FA-01 | No hay instituciones registradas | Muestra mensaje "No hay instituciones registradas" con sugerencia de crear una. |
| FA-02 | Búsqueda sin resultados | Muestra mensaje "No se encontraron instituciones" con el término buscado. |
| FA-03 | Letra sin coincidencias | Muestra lista vacía con la letra seleccionada resaltada. |

---

### CU-10: Ver Detalle de Institución

| Campo | Detalle |
|-------|---------|
| **ID** | CU-10 |
| **Nombre** | Ver Detalle Completo de Institución |
| **Actor Principal** | Superadmin, Secretaría, Evaluador |
| **Descripción** | Permite ver el detalle completo de una institución, incluyendo sus datos generales, la información del usuario responsable, y el historial de evaluaciones realizadas a su sitio web (con puntajes por dimensión). |
| **Prioridad** | Media |
| **Precondiciones** | 1. El actor debe tener rol `superadmin`, `secretary` o `evaluator`. <br> 2. La institución debe existir en el sistema. <br> 3. El actor debe estar autenticado con token JWT válido. |
| **Postcondiciones** | 1. Se muestran los datos de la institución, el responsable y las evaluaciones. |

**Flujo Principal:**

| Paso | Actor | Sistema |
|------|-------|---------|
| 1 | El actor hace clic en una tarjeta de institución (CU-09) o navega directamente a `/admin/institutions/{id}`. | |
| 2 | | Busca la institución por ID en la tabla `institutions`. |
| 3 | | Busca al usuario responsable (`entity_user`) vinculado a la institución mediante `institution_id`. |
| 4 | | Busca evaluaciones relacionadas: consulta la tabla `evaluations` a través de `websites`, filtrando por el dominio de la institución. Ordena por fecha descendente. |
| 5 | | Retorna un objeto con: datos de institución, datos del responsable, lista de evaluaciones. |
| 6 | | Muestra la vista de detalle con tres secciones: |
| 7 | | **Sección 1 — Datos Generales:** nombre, dominio (con enlace externo), estado, fechas de creación y actualización. |
| 8 | | **Sección 2 — Responsable:** nombre completo, email, cargo del responsable. Si no hay responsable, muestra mensaje de aviso. |
| 9 | | **Sección 3 — Historial de Evaluaciones:** tabla con fecha, estado, puntaje total, puntajes por dimensión (Accesibilidad, Usabilidad, Web Semántica, Soberanía), y enlace para ver el detalle de cada evaluación. |
| 10 | (Opcional) El actor hace clic en una evaluación. | Navega al detalle de la evaluación (`/admin/evaluations/{eval_id}`). |

**Flujos Alternativos:**

| ID | Condición | Acción |
|----|-----------|--------|
| FA-01 | Institución no encontrada | Retorna error 404: "Institución no encontrada". Muestra página de error. |
| FA-02 | Sin responsable asignado | Muestra tarjeta vacía con mensaje: "No se encontró un responsable para esta institución". |
| FA-03 | Sin evaluaciones | Muestra sección vacía con mensaje: "Esta institución aún no tiene evaluaciones" y botón para iniciar una. |

---

### CU-11: Editar Institución

| Campo | Detalle |
|-------|---------|
| **ID** | CU-11 |
| **Nombre** | Editar Datos de Institución |
| **Actor Principal** | Superadmin, Secretaría |
| **Descripción** | Permite modificar los datos de una institución existente y/o los datos de su usuario responsable. Los campos editables de la institución incluyen nombre, dominio y estado. Los campos editables del responsable incluyen nombre, email y cargo. |
| **Prioridad** | Alta |
| **Precondiciones** | 1. El actor debe tener rol `superadmin` o `secretary`. <br> 2. La institución debe existir en el sistema. <br> 3. El actor debe estar autenticado con token JWT válido. |
| **Postcondiciones** | 1. Los datos de la institución se actualizan en la base de datos. <br> 2. Si se modificaron datos del responsable, estos se actualizan en la tabla `users`. <br> 3. Los cambios son efectivos inmediatamente. |

**Flujo Principal:**

| Paso | Actor | Sistema |
|------|-------|---------|
| 1 | El actor se encuentra en la vista de detalle de la institución (CU-10). | |
| 2 | Presiona el botón "Editar". | Muestra modal de edición con dos secciones: Datos de Institución y Datos del Responsable, precargados con los valores actuales. |
| 3 | Modifica los campos deseados de la **institución**: <br> - Nombre <br> - Dominio <br> - Estado (activo/inactivo) | |
| 4 | Opcionalmente modifica los campos del **responsable**: <br> - Nombre del contacto <br> - Email del contacto <br> - Cargo del contacto | |
| 5 | Presiona "Guardar Cambios". | |
| 6 | | Busca la institución por ID en la BD. |
| 7 | | Separa los campos de institución (`name`, `domain`, `is_active`) de los campos del responsable (`contact_name`, `contact_email`, `contact_position`). |
| 8 | | Actualiza solo los campos de la institución que fueron modificados. |
| 9 | | Si hay campos del responsable modificados: busca al usuario `entity_user` vinculado y actualiza `full_name`, `email`, `position` según corresponda. |
| 10 | | Guarda los cambios y retorna los datos actualizados. |
| 11 | | Cierra el modal, muestra toast de confirmación y recarga los datos. |

**Flujos Alternativos:**

| ID | Condición | Acción |
|----|-----------|--------|
| FA-01 | Institución no encontrada | Retorna error 404: "Institución no encontrada". |
| FA-02 | Sin responsable asignado | Solo se actualizan los campos de la institución. Los campos del responsable se ignoran. |
| FA-03 | Actor sin permisos | Retorna error 403: "No tiene permisos para realizar esta acción". |
| FA-04 | El actor cancela | Cierra el modal sin guardar cambios. |

---

### CU-12: Eliminar Institución

| Campo | Detalle |
|-------|---------|
| **ID** | CU-12 |
| **Nombre** | Eliminar Institución |
| **Actor Principal** | Superadmin |
| **Descripción** | Permite eliminar permanentemente una institución del sistema. Esta acción es irreversible y elimina en cascada todos los usuarios asociados a la institución. Solo el Superadmin puede realizar esta operación. |
| **Prioridad** | Alta |
| **Precondiciones** | 1. El actor debe tener rol `superadmin`. <br> 2. La institución debe existir en el sistema. <br> 3. El actor debe estar autenticado con token JWT válido. |
| **Postcondiciones** | 1. La institución se elimina permanentemente de la tabla `institutions`. <br> 2. Todos los usuarios con `institution_id` = id de la institución se eliminan en cascada. <br> 3. Las notificaciones de los usuarios eliminados se eliminan en cascada. |

**Flujo Principal:**

| Paso | Actor | Sistema |
|------|-------|---------|
| 1 | El actor se encuentra en la vista de detalle (CU-10) o en la lista de instituciones (CU-09). | |
| 2 | Presiona el botón "Eliminar" de la institución. | |
| 3 | | Muestra modal de confirmación: "¿Está seguro de eliminar la institución [nombre]? Esta acción es irreversible y eliminará todos los usuarios asociados." |
| 4 | El actor confirma la eliminación. | |
| 5 | | Busca la institución por ID en la BD. |
| 6 | | Ejecuta `DELETE FROM institutions WHERE id = ?`. |
| 7 | | La base de datos ejecuta CASCADE: elimina todos los registros de `users` con `institution_id` = id, y sus notificaciones asociadas. |
| 8 | | Retorna status 204 No Content. |
| 9 | | Muestra toast: "Institución eliminada exitosamente". |
| 10 | | Redirige a la lista de instituciones. |

**Flujos Alternativos:**

| ID | Condición | Acción |
|----|-----------|--------|
| FA-01 | Institución no encontrada | Retorna error 404: "Institución no encontrada". |
| FA-02 | Actor no es Superadmin | Retorna error 403: "No tiene permisos para realizar esta acción". |
| FA-03 | El actor cancela la confirmación | Cierra el modal sin realizar ninguna acción. |

---

## 3. Matriz de Permisos (RBAC)

| Caso de Uso | Superadmin | Secretaría | Evaluador | Usuario Entidad |
|-------------|:----------:|:----------:|:---------:|:---------------:|
| CU-08: Registrar Institución | ✅ | ✅ | ❌ | ❌ |
| CU-09: Listar Instituciones | ✅ | ✅ | ✅ | ❌ |
| CU-10: Ver Detalle | ✅ | ✅ | ✅ | ❌ |
| CU-11: Editar Institución | ✅ | ✅ | ❌ | ❌ |
| CU-12: Eliminar Institución | ✅ | ❌ | ❌ | ❌ |

**Leyenda:** ✅ = Permitido | ❌ = Denegado

---

## 4. Reglas de Negocio

| ID | Regla | Descripción |
|----|-------|-------------|
| RN-11 | Dominio único | No pueden existir dos instituciones con el mismo dominio en el sistema. |
| RN-12 | Creación automática de responsable | Al registrar una institución, se crea automáticamente un usuario `entity_user` vinculado. |
| RN-13 | Username derivado del email | El username del responsable se genera a partir de la parte anterior al `@` del email, reemplazando puntos por guiones bajos. |
| RN-14 | Unicidad de username | Si el username generado ya existe, se le agrega el ID de la institución como sufijo. |
| RN-15 | Eliminación en cascada | Eliminar una institución elimina todos sus usuarios asociados y sus notificaciones. |
| RN-16 | Solo Superadmin elimina | La eliminación de instituciones está restringida exclusivamente al rol `superadmin`. |
| RN-17 | Normalización de dominio | La búsqueda por dominio normaliza eliminando el prefijo `www.` para comparación. |
| RN-18 | Edición parcial (PATCH) | Solo se actualizan los campos que fueron explícitamente modificados; los demás se mantienen. |
| RN-19 | Evaluaciones por dominio | El historial de evaluaciones se obtiene buscando websites cuyo dominio coincida con el de la institución. |
| RN-20 | Credenciales visibles una vez | La contraseña generada se muestra en el modal de credenciales y se envía por email. No se puede recuperar después. |

---

## 5. Requisitos No Funcionales

| ID | Requisito | Descripción |
|----|-----------|-------------|
| RNF-07 | Rendimiento | La lista de instituciones debe soportar paginación y cargarse en menos de 2 segundos. |
| RNF-08 | Filtrado alfabético | El filtro A-Z debe funcionar como navegación instantánea sin recarga total. |
| RNF-09 | Integridad referencial | La relación `Institution → Users` debe mantener CASCADE para eliminar en cadena. |
| RNF-10 | Seguridad de credenciales | La contraseña generada debe tener mínimo 12 caracteres con letras, números y símbolos. |
| RNF-11 | Auditoría | Todas las operaciones CRUD de instituciones se registran en logs con actor, acción y timestamp. |

---

## 6. Trazabilidad

### 6.1 Endpoints REST Asociados

| Caso de Uso | Método | Endpoint | Guard |
|-------------|--------|----------|-------|
| CU-08 | POST | `/api/v1/admin/institutions` | `allow_admin_secretary` |
| CU-09 | GET | `/api/v1/admin/institutions` | `allow_all_staff` |
| CU-10 | GET | `/api/v1/admin/institutions/{id}` | `allow_all_staff` |
| CU-11 | PATCH/PUT | `/api/v1/admin/institutions/{id}` | `allow_admin_secretary` |
| CU-12 | DELETE | `/api/v1/admin/institutions/{id}` | `allow_superadmin` |

### 6.2 Modelos de Datos Involucrados

| Caso de Uso | Tablas | Operación |
|-------------|--------|-----------|
| CU-08 | institutions, users | INSERT, INSERT |
| CU-09 | institutions | SELECT |
| CU-10 | institutions, users, evaluations, websites | SELECT (JOIN) |
| CU-11 | institutions, users | UPDATE |
| CU-12 | institutions, users, notifications | DELETE (CASCADE) |

### 6.3 Componentes Frontend Asociados

| Caso de Uso | Componente | Ruta |
|-------------|------------|------|
| CU-08 | `Institutions.jsx` → `CreateInstitutionModal` + `CredentialsModal` | `/admin/institutions` |
| CU-09 | `Institutions.jsx` → `InstitutionCard` + Alfabeto A-Z | `/admin/institutions` |
| CU-10 | `InstitutionDetail.jsx` → `ResponsibleCard` + `EvaluationsList` | `/admin/institutions/{id}` |
| CU-11 | `InstitutionDetail.jsx` → `EditModal` | `/admin/institutions/{id}` |
| CU-12 | `InstitutionDetail.jsx` / `Institutions.jsx` → `ConfirmDeleteModal` | `/admin/institutions/{id}` |

---

**Fin del Documento**
