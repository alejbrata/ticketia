Toma la siguiente petición del usuario y transfórmala en una spec SDD bien formada. Si no hay petición, muestra el template vacío para que el usuario lo rellene.

Petición del usuario: $ARGUMENTS

---

## Reglas para generar la spec

1. **Contexto** — describe el módulo/archivo afectado, su estado actual, y cualquier restricción relevante (permisos, dependencias, estado de la BD).

2. **Objetivo** — una frase concreta que describa el resultado esperado. Debe ser falsificable: o se cumple o no.

3. **Criterios de aceptación** — lista de checks verificables. Siempre incluir:
   - El comportamiento funcional pedido
   - `[ ] Todos los tests existentes pasan sin regresiones (pytest)`
   - `[ ] Los tests nuevos necesarios están escritos y pasan`
   - Si el cambio toca rutas (`api.py`, `web.py`) o modelos (`db_models.py`): `[ ] Revisión OWASP completada (input validation, auth checks, no SQL injection, no XSS)`

4. **Restricciones** — qué NO hacer: no añadir features extra, no refactorizar fuera de scope, no romper endpoints existentes.

5. **Salida esperada** — archivos modificados, comportamiento observable, comando de verificación.

---

## Template de salida

```
**Contexto:** [módulo, estado actual, restricciones]
**Objetivo:** [resultado concreto y verificable]
**Criterios de aceptación:**
- [ ] [comportamiento funcional 1]
- [ ] [comportamiento funcional 2]
- [ ] Todos los tests existentes pasan (pytest)
- [ ] Tests nuevos escritos y pasando (si aplica)
- [ ] Revisión OWASP completada (si toca rutas o modelos)
**Restricciones:** [qué NO hacer, límites de scope]
**Salida esperada:** [archivos, comportamiento, comando de verificación]
```

Si la petición original ya estaba bien formada como SDD, indícalo y señala qué estaba bien.
