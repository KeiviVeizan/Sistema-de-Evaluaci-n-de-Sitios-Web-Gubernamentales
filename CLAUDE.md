# Instrucciones de proyecto

## Reglas de comportamiento
- Analiza SOLO los archivos que menciono explícitamente. No escanees el proyecto completo.
- No explores carpetas ni archivos que no te indique.
- Responde de forma concisa y técnica. Sin explicaciones extensas.
- Da la solución directa: código final o diff unificado. No razonamiento paso a paso.
- No sugieras mejoras, refactorizaciones ni optimizaciones que no haya pedido.
- No repitas análisis de archivos ya revisados en la conversación.
- No recapitules lo que ya se discutió.

## Formato de respuesta
- Código listo para aplicar o diff unificado
- Solo comentarios breves si son estrictamente necesarios
- Sin ejemplos adicionales no solicitados
```

## Paso 3: Hábitos que ahorran tokens

Esto es igual de importante que las instrucciones:

**Usa `/compact` frecuentemente** — esto comprime el historial de la conversación y reduce drásticamente los tokens en mensajes siguientes.

**Usa `/clear` cuando cambies de tarea** — no acumules contexto innecesario de tareas anteriores.

**Sé específico en tus prompts** — en lugar de "arregla el login", di "en `src/auth/login.js`, la función `handleSubmit` línea 45 no valida el email, agrega validación con regex".

**Usa Sonnet en vez de Opus para tareas simples** — si tu plan lo permite, Sonnet consume menos y para tareas rutinarias es suficiente. Puedes cambiar con:
```
/model sonnet