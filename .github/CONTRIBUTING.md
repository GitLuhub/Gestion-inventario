# Guía de Contribución

## Estrategia de Branching (H7)

Este proyecto usa **Trunk-Based Development** con ramas de corta duración.

### Ramas

| Rama | Propósito | Protección |
|------|-----------|-----------|
| `main` | Producción — siempre desplegable | ✅ Protegida: PR obligatorio + CI verde |
| `feat/<nombre>` | Nueva funcionalidad | — |
| `fix/<descripcion>` | Corrección de bug | — |
| `chore/<nombre>` | Mantenimiento, docs, deps | — |

### Flujo de trabajo

```
1. Crear rama desde main:
   git checkout -b feat/mi-funcionalidad

2. Trabajar en commits pequeños y atómicos:
   git commit -m "feat(inventory_custom): descripción concisa"

3. Abrir Pull Request hacia main
   - Título: < 70 caracteres
   - Descripción: qué, por qué, cómo probar

4. CI debe estar en verde (lint + tests + coverage ≥ 80%)

5. Merge (squash si hay muchos commits de WIP)
```

### Configurar protección de `main` en GitHub

1. Ir a Settings → Branches → Add branch protection rule
2. Branch name pattern: `main`
3. Activar:
   - ✅ Require a pull request before merging
   - ✅ Require status checks to pass before merging
     - Seleccionar: `Lint and Test`
   - ✅ Require branches to be up to date before merging
   - ✅ Do not allow bypassing the above settings

### Convención de commits

```
<tipo>(<scope>): <descripción imperativa corta>

[cuerpo opcional — qué y por qué, no cómo]
```

| Tipo | Cuándo usarlo |
|------|--------------|
| `feat` | Nueva funcionalidad |
| `fix` | Corrección de bug |
| `test` | Tests nuevos o modificados |
| `docs` | Solo documentación |
| `chore` | Build, deps, CI |
| `refactor` | Cambio sin nueva funcionalidad ni bug fix |
| `perf` | Mejora de rendimiento |

Ejemplos:
```
feat(inventory_custom): agregar campo barcode en formulario de producto
fix(api_gateway): corregir refresh token en ambiente Safari
test(etl): añadir tests de integración para loader Odoo
chore(deps): actualizar fastapi a 0.104
```

## Antes de abrir un PR

- [ ] `pytest tests/ --cov=src --cov-fail-under=80` pasa localmente
- [ ] `python tests/validate_views.py` sin errores (módulo Odoo)
- [ ] `npm run lint && npm run type-check` sin errores (frontend)
- [ ] Sin archivos `.env` con valores reales en el commit
- [ ] Actualizado `CLAUDE.md` si se modificaron modelos, vistas o flujos

## Entornos

| Entorno | Rama | URL |
|---------|------|-----|
| Development | local | http://localhost:8069 |
| Staging | `main` (auto-deploy) | https://staging.example.com |
| Production | `main` (aprobación manual) | https://prod.example.com |
