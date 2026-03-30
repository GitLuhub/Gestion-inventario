# CLAUDE.md — Módulo `inventory_custom`

> Este archivo es la **fuente única de verdad** para asistentes de IA (Claude Code) y
> desarrolladores humanos que trabajen en este módulo.
> Léelo completamente antes de realizar cualquier cambio.

---

## Tabla de Contenidos

1. [Visión General del Proyecto](#1-visión-general-del-proyecto)
2. [Arquitectura del Sistema](#2-arquitectura-del-sistema)
3. [Mapa de Archivos del Módulo](#3-mapa-de-archivos-del-módulo)
4. [Referencia de Modelos](#4-referencia-de-modelos)
5. [Catálogo de Issues Identificados](#5-catálogo-de-issues-identificados)
6. [Plan de Acción Ejecutado](#6-plan-de-acción-ejecutado)
7. [Mejores Prácticas Odoo 16](#7-mejores-prácticas-odoo-16)
8. [Estrategia de Testing](#8-estrategia-de-testing)
9. [Flujo de Desarrollo](#9-flujo-de-desarrollo)
10. [Limitaciones Conocidas](#10-limitaciones-conocidas)
11. [Análisis de Cumplimiento PRD/Arquitectura](#11-análisis-de-cumplimiento-prdarquitectura)
12. [Plan de Acción PRD — Brechas Pendientes](#12-plan-de-acción-prd--brechas-pendientes)

---

## 1. Visión General del Proyecto

| Atributo | Valor |
|----------|-------|
| **Nombre técnico** | `inventory_custom` |
| **Versión** | `16.0.1.0.0` |
| **Versión Odoo** | 16.0 LTS |
| **Licencia** | LGPL-3 |
| **Autor** | Luis Brito |
| **Idioma UI** | Español (es) |
| **Código fuente** | Inglés |

### Propósito

`inventory_custom` extiende el módulo `stock` de Odoo 16 con gestión avanzada de inventario:

- **Marcas de Productos** — modelo `product.brand` con conteo automático de productos
- **Ubicaciones Avanzadas** — clasificación por tipo, capacidad máxima, clase de almacenamiento
- **Categorías Extendidas** — código, descripción traducible, utilidades de jerarquía
- **Ajustes de Inventario** — flujo completo (borrador → en progreso → validado) con trazabilidad
- **Wizard de Ajuste Rápido** — corrección de un solo producto en pocos pasos
- **Wizard de Conteo Rápido** — conteo completo de una ubicación en un formulario

### Contexto en el Sistema Mayor

Este módulo corre dentro de un stack contenedorizado completo:

```
Nginx ──▶ Frontend (Next.js)
              │
              ▼
       API Gateway (FastAPI) ──▶ Odoo 16 + inventory_custom ──▶ PostgreSQL 15
                                           │
                                     ETL Service (Python)

Observabilidad: Prometheus + Grafana
```

Ver `README.md` y `docker-compose.yml` para detalles de infraestructura.

---

## 2. Arquitectura del Sistema

### Grafo de Dependencias del Módulo

```
base
 └── product
      └── stock
           └── mail
                └── inventory_custom  ◄── este módulo
```

**IMPORTANTE:** `mail` es una dependencia obligatoria. `StockInventoryAdjustment` hereda
`mail.thread` y `mail.activity.mixin`. Sin `mail` en `depends`, el módulo no instala.

### Mapa de Herencia de Modelos

```
product.template  (extend)  ──▶ +brand_id, +manufacturer_ref, +min/max_stock_level
product.category  (extend)  ──▶ +code, +description, +image, +active
stock.location    (extend)  ──▶ +location_type, +max_capacity, +responsible_id,
                                +barcode, +usage_class, +temperature_range
stock.quant       (extend)  ──▶ +lot_name (related computed, store=False)

product.brand                        (modelo nuevo)
stock.inventory.adjustment           (modelo nuevo, hereda mail.thread)
stock.inventory.adjustment.line      (modelo nuevo)
stock.inventory.adjustment.reason    (modelo nuevo, catálogo)
stock.inventory.wizard               (transient)
stock.inventory.quick.count          (transient)
stock.inventory.quick.count.line     (transient)
```

### Máquina de Estados — Ajuste de Inventario

```
                   action_generate_lines()
                         │
draft ──[action_start]──▶ in_progress ──[action_validate]──▶ done
  ▲                           │
  └──────[action_draft]───────┘

(cualquier estado no done) ──[action_cancel]──▶ cancel
```

### Estructura de Seguridad

```
Grupos personalizados (security/security.xml):
  group_inventory_manager  ──▶ implica stock.group_stock_manager
  group_inventory_operator ──▶ implica stock.group_stock_user
  group_inventory_viewer   ──▶ implica stock.group_stock_user

Permisos (ir.model.access.csv):
  Manager:  CRUD completo en todos los modelos
  Operator: Leer/escribir/crear (sin eliminar) en modelos operacionales
  Viewer:   Solo lectura en product.brand
```

---

## 3. Mapa de Archivos del Módulo

```
odoo_custom_module/
├── __init__.py                          # from . import models
├── __manifest__.py                      # Metadata, depends, orden de carga DATA
│
├── data/
│   └── stock_data.xml                   # Datos maestros: ubicaciones, categorías, marcas
│                                        # noupdate="1" — no se resetean al actualizar
│
├── docs/
│   └── models_documentation.md          # Documentación de campos por modelo
│
├── models/
│   ├── __init__.py                      # Importa todas las clases de modelo
│   ├── inventory_adjustment.py          # StockInventoryAdjustment, Line, Reason
│   ├── inventory_wizard.py              # StockInventoryWizard, QuickCount, QuickCountLine
│   ├── product_category_extended.py     # ProductCategory (_inherit)
│   ├── product_extended.py              # ProductTemplate, ProductBrand
│   └── stock_extended.py               # StockLocation, StockQuant (_inherit)
│
├── security/
│   ├── ir.model.access.csv              # Reglas ACL — DEBE cargarse ANTES de las vistas
│   └── security.xml                     # Grupos: Manager, Operator, Viewer
│
├── tests/
│   ├── __init__.py
│   ├── test_models.py                   # Tests unitarios de modelos
│   ├── test_security.py                 # Tests de grupos de seguridad
│   ├── test_views.py                    # Tests de existencia de vistas/acciones/menús
│   └── validate_views.py               # Script de linting XML (sin Odoo)
│
└── views/
    ├── inventory_adjustment_views.xml   # Vistas form/tree/search + wizards + secuencia ADJ/
    ├── menu_views.xml                   # Menú raíz "Inventario Avanzado" y submenús
    ├── product_views.xml                # Vistas de product.template y product.brand
    └── stock_views.xml                  # Extensión de vista de stock.location
```

### Orden Crítico de Carga en `__manifest__.py`

```python
"data": [
    "security/security.xml",          # 1. Grupos deben existir antes que las ACL
    "security/ir.model.access.csv",   # 2. ACL ANTES de cualquier vista
    "data/stock_data.xml",            # 3. Datos maestros
    "views/product_views.xml",        # 4. Vistas (en cualquier orden entre sí)
    "views/stock_views.xml",
    "views/menu_views.xml",
    "views/inventory_adjustment_views.xml",
]
```

**Cargar las ACL después de las vistas puede causar errores de acceso durante la carga del módulo.**

---

## 4. Referencia de Modelos

### 4.1 `product.brand` (modelo nuevo)

| Campo | Tipo | Notas |
|-------|------|-------|
| `name` | Char | requerido, translate, index |
| `description` | Text | translate |
| `logo` | Binary | attachment=True |
| `product_count` | Integer | compute via `read_group`, store=False |
| `product_ids` | One2many → product.template | via brand_id |
| `active` | Boolean | default True |

**Método clave:** `_compute_product_count` — usa `read_group` (SQL COUNT), NO `len()`.

### 4.2 `product.template` (extendido)

| Campo | Tipo | Notas |
|-------|------|-------|
| `brand_id` | Many2one → product.brand | tracking=True, index |
| `manufacturer_ref` | Char | tracking=True, index |
| `min_stock_level` | Float | digits='Product Unit of Measure' |
| `max_stock_level` | Float | digits='Product Unit of Measure' |

**Constraint:** `_check_stock_levels` — min no puede superar max.

### 4.3 `product.category` (extendido)

| Campo | Tipo | Notas |
|-------|------|-------|
| `code` | Char | index |
| `description` | Text | translate |
| `image` | Binary | attachment=True |
| `active` | Boolean | default True |

**REGLA CRÍTICA:** NO redefinir `parent_path`. Es gestionado automáticamente por Odoo
cuando `_parent_store = True` en `product.category` de Odoo core.

**Métodos:**
- `get_full_path()` — retorna `"Padre / Hijo / Nieto"` recorriendo `parent_id`
- `get_subcategories(include_self=False)` — árbol recursivo; usa `child_ids` (plural con s)
- `_check_hierarchy()` — previene referencias circulares via `_check_recursion()`

**Constraint:** `@api.constrains('parent_id')` → `_check_hierarchy()` → `ValidationError` de `odoo.exceptions`.

### 4.4 `stock.location` (extendido)

| Campo | Tipo | Notas |
|-------|------|-------|
| `location_type` | Selection | warehouse/zone/aisle/rack/shelf/bin/transit/quality/returns/scrap |
| `max_capacity` | Float | input manual |
| `current_capacity` | Float | compute desde quant_ids.quantity |
| `capacity_usage_percent` | Float | compute, store=False |
| `responsible_id` | Many2one → res.users | index |
| `barcode` | Char | index, copy=False |
| `usage_class` | Selection | dry/cold/frozen/hazardous/standard |
| `temperature_range` | Char | ej. "2-8°C" |

**Constraint:** `_check_location_type_compatibility` — tipo `warehouse` solo puede tener usage `internal` o `view`.

### 4.5 `stock.quant` (extendido)

| Campo | Tipo | Notas |
|-------|------|-------|
| `lot_name` | Char | related='lot_id.name', store=False |

**REGLA CRÍTICA:** NO redefinir `lot_id`. Ya existe en `stock.quant` de Odoo 16 core.

### 4.6 `stock.inventory.adjustment` (modelo nuevo)

Hereda: `mail.thread`, `mail.activity.mixin` (requiere `mail` en depends).

| Campo | Tipo | Notas |
|-------|------|-------|
| `name` | Char | secuencia ADJ/XXXXX, readonly |
| `state` | Selection | draft/in_progress/done/cancel, tracking |
| `adjustment_type` | Selection | full/partial/cyclic/correction |
| `reason_id` | Many2one → adjustment.reason | |
| `location_ids` | Many2many → stock.location | domain internal only |
| `responsible_id` | Many2one → res.users | default current user |
| `line_ids` | One2many → adjustment.line | |
| `total_discrepancy` | Float | sum(abs(difference_qty)) — valores absolutos |
| `move_ids` | Many2many → stock.move | readonly |
| `company_id` | Many2one → res.company | required |

**Método clave:** `_get_inventory_location()` — usa `company.property_stock_inventory_loc_id`
(NO `env.ref('stock.location_inventory')` que puede no existir).

**`action_generate_lines()`:** Limpia líneas previas con `self.line_ids.unlink()` antes de regenerar.

### 4.7 `stock.inventory.adjustment.line` (modelo nuevo)

```python
_sql_constraints = [
    ('unique_product_location_adjustment',
     'UNIQUE(adjustment_id, product_id, location_id)',
     'Ya existe una línea para este producto y ubicación en el mismo ajuste.'),
]
```

| Campo | Tipo | Notas |
|-------|------|-------|
| `adjustment_id` | Many2one → adjustment | cascade, index |
| `product_id` | Many2one → product.product | domain storable |
| `location_id` | Many2one → stock.location | domain internal |
| `current_qty` | Float | stock real |
| `expected_qty` | Float | cantidad contada |
| `difference_qty` | Float | compute: expected - current, store=True |
| `adjustment_reason` | Selection | count/damage/loss/theft/expiration/return/correction/other |
| `move_id` | Many2one → stock.move | se asigna al validar |
| `state` | Selection | related de adjustment_id.state |

### 4.8 Modelos Transient (Wizards)

| Modelo | Descripción |
|--------|-------------|
| `stock.inventory.wizard` | Ajuste rápido de un producto |
| `stock.inventory.quick.count` | Conteo rápido de toda una ubicación |
| `stock.inventory.quick.count.line` | Una línea por producto en el conteo |

**IMPORTANTE:** Los tres necesitan entradas ACL en `ir.model.access.csv`. Sin ellas,
usuarios no administradores reciben `AccessError` al abrir el wizard.

---

## 5. Catálogo de Issues Identificados

### Bugs Críticos — Resueltos ✅

| ID | Archivo | Línea | Problema | Solución Aplicada |
|----|---------|-------|---------|-------------------|
| BUG-001 | `product_category_extended.py` | 53-54 | `self.child_id` → AttributeError | Cambiado a `self.child_ids` |
| BUG-002 | `inventory_adjustment.py` | 198, 201 | `env.ref('stock.location_inventory')` hardcoded | Reemplazado por `_get_inventory_location()` |
| BUG-003 | `product_views.xml`:81 + `menu_views.xml`:45 | XML ID `menu_product_brand` duplicado | Eliminado de `product_views.xml` |
| BUG-004 | `stock_extended.py` | 108-114 | Redefine `lot_id` que ya existe en Odoo 16 | Bloque eliminado |
| BUG-005 | `product_category_extended.py` | 15-19 | `parent_path` definido manualmente | Campo eliminado |
| BUG-006 | `inventory_wizard.py` | 134, 137 | Mismo `env.ref` hardcoded que BUG-002 | Reemplazado por `_get_inventory_location()` |
| BUG-007 | `product_category_extended.py` | 66 | `models.ValidationError` incorrecto | Corregido a `ValidationError` de `odoo.exceptions` + import |

### Issues Altos — Resueltos ✅

| ID | Archivo | Problema | Solución Aplicada |
|----|---------|---------|-------------------|
| ISSUE-001 | `__manifest__.py` | Falta `mail` en `depends` | Agregado |
| ISSUE-002 | `__manifest__.py` | `ir.model.access.csv` cargaba después de vistas | Movido a posición 2 (antes de vistas) |
| ISSUE-003 | `ir.model.access.csv` | Falta ACL para `stock.inventory.quick.count.line` | Línea agregada |
| ISSUE-004 | `__manifest__.py` | Versión `"1.0.0"` | Cambiado a `"16.0.1.0.0"` |

### Issues Medios — Resueltos ✅

| ID | Archivo | Problema | Solución Aplicada |
|----|---------|---------|-------------------|
| ISSUE-005 | `stock_extended.py` | `lot_name` con `store=True` | Cambiado a `store=False` |
| ISSUE-006 | `product_extended.py` | `len(product_ids)` para contar | Reemplazado por `read_group` |
| ISSUE-007 | `product_extended.py` | `product_count` con `store=True` | Cambiado a `store=False` |
| ISSUE-008 | `inventory_adjustment.py` | `action_generate_lines` creaba duplicados | Agregado `self.line_ids.unlink()` al inicio |
| ISSUE-009 | `inventory_adjustment.py` | `total_discrepancy` suma con signo | Reemplazado por `sum(abs(...))` |
| ISSUE-010 | `inventory_adjustment.py` | Sin constraint UNIQUE en líneas | Agregado `_sql_constraints` |
| ISSUE-011 | `stock_extended.py` | Condición redundante en constraint | Simplificado a una sola condición |

### Issues Bajos — Resueltos ✅

| ID | Archivo | Problema | Solución Aplicada |
|----|---------|---------|-------------------|
| ISSUE-012 | `tests/validate_views.py` | Variable `base_path` con nombre erróneo | Renombrado a `module_path` |
| ISSUE-013 | `tests/test_models.py` | Sin tests para adjustment y wizards | Agregadas clases `TestStockInventoryAdjustment` y `TestStockInventoryAdjustmentLine` |
| ISSUE-014 | `inventory_adjustment.py` | `StockInventoryAdjustmentReason` sin `_rec_name` | Agregado `_rec_name = 'name'` |

---

## 6. Plan de Acción Ejecutado

### Fase 1 — Infraestructura (ejecutada primero)
1. `__manifest__.py` — versión, `mail` en depends, reordenar data
2. `security/ir.model.access.csv` — agregar ACL para `quick.count.line`

### Fase 2 — Bugs Críticos en Modelos
3. `models/product_category_extended.py` — eliminar `parent_path`, `child_ids`, `ValidationError`
4. `models/stock_extended.py` — eliminar `lot_id`, `store=False`, condición limpia
5. `models/inventory_adjustment.py` — `_get_inventory_location`, limpiar líneas, `abs()`, SQL constraint
6. `models/inventory_wizard.py` — `_get_inventory_location`

### Fase 3 — Conflicto XML
7. `views/product_views.xml` — eliminar `menu_product_brand` duplicado

### Fase 4 — Calidad de Código
8. `models/product_extended.py` — `read_group`, `store=False`
9. `tests/validate_views.py` — renombrar variable
10. `tests/test_models.py` — agregar tests de ajuste

### Fase 5 — Documentación
11. `CLAUDE.md` — este documento

---

## 7. Mejores Prácticas Odoo 16

### Convención de Versión del Módulo

```python
"version": "16.0.X.Y.Z"
# 16.0 = versión de Odoo
# X    = cambio incompatible (breaking change)
# Y    = nueva funcionalidad
# Z    = corrección de bug
```

### Orden de Carga en `__manifest__.py` (Obligatorio)

```
1. security/security.xml          # Grupos primero
2. security/ir.model.access.csv   # ACL antes que cualquier vista
3. data/*.xml                     # Datos maestros
4. views/*.xml                    # Vistas al final
```

### Reglas de Herencia de Campos

```python
# CORRECTO — verificar primero que el campo no exista en Odoo core:
class StockQuant(models.Model):
    _inherit = 'stock.quant'
    lot_name = fields.Char(related='lot_id.name', store=False)  # lot_id ya existe

# INCORRECTO — redefinir un campo que ya existe:
class StockQuant(models.Model):
    _inherit = 'stock.quant'
    lot_id = fields.Many2one('stock.lot', ...)  # ← lot_id ya está en Odoo 16, CONFLICTO

# INCORRECTO — definir parent_path manualmente:
parent_path = fields.Char(...)  # Odoo lo gestiona con _parent_store=True
```

### Patrón de Ubicación de Inventario

```python
# CORRECTO — funciona en cualquier instalación de Odoo 16:
def _get_inventory_location(self):
    inventory_location = (
        self.env.company.property_stock_inventory_loc_id
        or self.env['stock.location'].search(
            [('usage', '=', 'inventory'), ('company_id', '=', self.env.company.id)],
            limit=1,
        )
    )
    if not inventory_location:
        raise UserError(_('No se encontró una ubicación de inventario para la compañía.'))
    return inventory_location

# INCORRECTO — puede no existir:
self.env.ref('stock.location_inventory')
```

### Campos Computed

```python
# CORRECTO — read_group para conteos:
@api.depends('product_ids')
def _compute_product_count(self):
    count_data = self.env['product.template'].read_group(
        domain=[('brand_id', 'in', self.ids)],
        fields=['brand_id'],
        groupby=['brand_id'],
    )
    count_map = {row['brand_id'][0]: row['brand_id_count'] for row in count_data}
    for brand in self:
        brand.product_count = count_map.get(brand.id, 0)

# INCORRECTO — len() carga todos los registros en memoria:
for brand in self:
    brand.product_count = len(brand.product_ids)

# Usar store=False en campos related (a menos que sean necesarios para búsqueda):
lot_name = fields.Char(related='lot_id.name', store=False)
```

### Excepciones

```python
# SIEMPRE importar desde odoo.exceptions:
from odoo.exceptions import UserError, ValidationError

# CORRECTO:
raise ValidationError(_('Mensaje de error'))
raise UserError(_('Error de usuario'))

# INCORRECTO — models.ValidationError no existe:
raise models.ValidationError(_('Error'))
```

### Security Groups en `ir.model.access.csv`

```csv
# Formato: id, name, model_id:id, group_id:id, perm_read, perm_write, perm_create, perm_unlink
access_my_model_operator,my.model.operator,model_my_model,group_inventory_operator,1,1,1,0
```

Los XML IDs de grupos definidos en el mismo módulo pueden usarse sin prefijo en el CSV cuando
son cargados en el mismo contexto de módulo. El prefijo completo `inventory_custom.group_xxx`
también es válido y más explícito.

### Transient Models (Wizards) + ACL

Todo `TransientModel` necesita entrada en `ir.model.access.csv`. Sin ella, usuarios no admin
reciben `AccessError` al abrir el wizard.

### Mail Mixin

```python
# Si el modelo hereda mail.thread o mail.activity.mixin:
_inherit = ['mail.thread', 'mail.activity.mixin']

# El módulo DEBE declarar 'mail' en depends:
"depends": ["base", "product", "stock", "mail"]
```

### SQL Constraints

```python
# Para unicidad que debe ser garantizada a nivel de base de datos:
_sql_constraints = [
    ('unique_product_location_adjustment',
     'UNIQUE(adjustment_id, product_id, location_id)',
     'Ya existe una línea para este producto y ubicación en el mismo ajuste.'),
]
```

---

## 8. Estrategia de Testing

### Tipos de Tests

| Tipo | Archivo | Cómo Ejecutar |
|------|---------|---------------|
| Tests unitarios Odoo | `tests/test_models.py` | `odoo-bin ... --test-enable` |
| Tests de seguridad | `tests/test_security.py` | `odoo-bin ... --test-enable` |
| Tests de vistas/menús | `tests/test_views.py` | `odoo-bin ... --test-enable` |
| Linting XML (standalone) | `tests/validate_views.py` | `python tests/validate_views.py` |

### Ejecutar Tests

```bash
# Suite completa del módulo
docker exec inventory_odoo_app odoo-bin \
  -d odoo_db \
  -u inventory_custom \
  --test-enable \
  --stop-after-init \
  --log-level=test

# Clase específica
docker exec inventory_odoo_app odoo-bin \
  -d odoo_db \
  --test-tags /inventory_custom:TestStockInventoryAdjustment \
  --stop-after-init

# Linting XML (no requiere Odoo ni base de datos)
cd odoo_custom_module
python tests/validate_views.py
```

### Tabla de Cobertura Requerida

| Modelo | Tests Requeridos |
|--------|-----------------|
| `product.brand` | crear, product_count, toggle activo |
| `product.template` | constraint stock levels, asignación de marca |
| `stock.location` | tipo, capacidad, uso, barcode |
| `product.category` | código, get_subcategories (child_ids), check_hierarchy, get_full_path |
| `stock.inventory.adjustment` | secuencia, flujo de estados, cancelar, discrepancia absoluta, generate_lines idempotente |
| `stock.inventory.adjustment.line` | difference_qty positivo, negativo, cero |
| `stock.inventory.wizard` | action_apply, UserError sin diferencia |
| `stock.inventory.quick.count` | action_validate crea adjustment |

### Patrón de Fixtures

```python
from odoo.tests import TransactionCase

class TestMiModelo(TransactionCase):
    """Tests para mi.modelo"""

    def setUp(self):
        super().setUp()
        # Crear datos mínimos necesarios
        self.location = self.env['stock.location'].create({
            'name': 'Test Location',
            'usage': 'internal',
        })
        self.product = self.env['product.product'].create({
            'name': 'Test Product',
            'type': 'product',
        })
    # No usar datos demo — noupdate=1 no se carga en modo test
```

---

## 9. Flujo de Desarrollo

### Antes de Empezar Cualquier Cambio

1. Leer este `CLAUDE.md` completamente.
2. Ejecutar `python tests/validate_views.py` para establecer baseline.
3. Verificar que la suite de tests existente pasa.

### Al Cambiar Modelos

1. Editar el archivo del modelo.
2. Si se agrega un modelo nuevo:
   - Agregar import en `models/__init__.py`
   - Agregar entradas ACL en `security/ir.model.access.csv`
3. Si se agrega un campo nuevo en un modelo existente: verificar que NO existe en Odoo core.
4. Actualizar `docs/models_documentation.md`.
5. Agregar/actualizar tests en `tests/test_models.py`.

### Al Cambiar Vistas

1. Editar el archivo XML.
2. Ejecutar `python tests/validate_views.py`.
3. Verificar que no hay XML IDs duplicados:
   ```bash
   grep -r 'id="menu_product_brand"' odoo_custom_module/views/
   # Solo debe aparecer en menu_views.xml
   ```

### Reinstalar el Módulo

```bash
# Actualizar módulo tras cambios
docker exec inventory_odoo_app odoo-bin \
  -d odoo_db \
  -u inventory_custom \
  --stop-after-init

# Verificar logs
docker compose logs odoo_app | grep -E "(ERROR|WARNING)" | grep inventory_custom
```

### Convención de Commits

```
feat(inventory_custom): <descripción de nueva funcionalidad>
fix(inventory_custom): <descripción del bug corregido>
test(inventory_custom): <descripción de tests agregados>
docs(inventory_custom): <descripción de documentación actualizada>
refactor(inventory_custom): <descripción de refactorización>
```

Ejemplos:
```
fix(inventory_custom): reemplazar env.ref hardcoded por company.property_stock_inventory_loc_id
feat(inventory_custom): agregar constraint UNIQUE en líneas de ajuste
test(inventory_custom): agregar tests de flujo de estados en StockInventoryAdjustment
```

---

## 10. Limitaciones Conocidas

### 1. Regeneración de Líneas Borra Cambios Manuales

`action_generate_lines()` elimina todas las líneas existentes antes de regenerar.
Si el usuario modificó manualmente `expected_qty` en alguna línea, esos valores se pierden.

**Mitigación:** Mostrar advertencia en la UI antes de permitir regeneración cuando existen
líneas modificadas (verificar si alguna `expected_qty != current_qty`).

### 2. Sin Soporte de Trazabilidad por Lote en Líneas de Ajuste

`StockInventoryAdjustmentLine` no tiene campo `lot_id`. Los ajustes afectan cantidad total
del producto en la ubicación pero no discriminan por lote.

**Mitigación futura:** Extender el modelo con `lot_id` y filtrar quants por lote.

### 3. Multi-Compañía — Dominio de Ubicaciones Sin Filtro de Compañía

`location_ids` en ajustes usa `domain=[('usage', '=', 'internal')]` sin filtrar por compañía.
En entornos multi-compañía, un usuario podría seleccionar ubicaciones de otra compañía.

**Mitigación futura:** Agregar `('company_id', 'in', [False, self.env.company.id])` al dominio.

### 4. `total_discrepancy` No Diferencia Exceso de Faltante

El campo muestra la suma de valores absolutos de todas las diferencias. No permite distinguir
cuánto corresponde a exceso (qty esperada > actual) vs faltante (qty esperada < actual).

**Mitigación futura:** Agregar campos `total_surplus` y `total_shortage` computados
separadamente.

### 5. `action_generate_lines` Solo Para Estado Borrador

Por diseño, `action_generate_lines()` lanza `UserError` si el ajuste no está en estado
`draft`. Esto previene sobrescribir un ajuste en progreso, pero impide actualizar las
cantidades base si el stock cambió después de iniciarlo.

### 6. Tests de Integración No Cubren `action_validate`

La ruta de `_create_stock_move` en `action_validate` requiere configurar una ubicación de
inventario en la compañía de test. Los tests actuales solo validan la lógica de modelos
sin crear movimientos reales.

**Mitigación futura:** Crear `tests/test_integration.py` con configuración completa de
ubicación de inventario usando `setUpClass`.

---

## 11. Análisis de Cumplimiento PRD/Arquitectura

> Auditoría realizada el 2026-03-30 contra `00_prd.md` y `01_arquitectura.md`.

### Estado General del Stack

| Componente | PRD/Arq. | Estado | Notas |
|-----------|----------|--------|-------|
| Odoo 16 + módulo custom | ✅ Requerido | ✅ Implementado | Módulo instalado y funcionando |
| PostgreSQL 15 | ✅ Requerido | ✅ Implementado | |
| ETL Service (Python) | ✅ Requerido | ✅ Implementado | Extract CSV/API/DB, Transform, Load con retry |
| Docker Compose | ✅ Requerido | ✅ Implementado | 9 servicios orquestados |
| Nginx (Reverse Proxy) | ✅ Requerido | ✅ Implementado | Perfil `production` |
| Prometheus + Grafana | Recomendado | ✅ Implementado | Perfil `monitoring` |
| API Gateway (FastAPI) | No en PRD original | ✅ Implementado | Mejora — JWT auth, CRUD, métricas |
| Frontend (Next.js) | No en PRD original | ✅ Implementado | Mejora — dashboard, productos, inventario |
| Log Centralizado | ✅ Requerido (RNF6) | ❌ Faltante | No hay Loki/ELK/Fluentd |
| Backup automático BD | ✅ Requerido (RNF7) | ❌ Faltante | No hay estrategia de backup |

### Requisitos Funcionales del Módulo Odoo

| ID | Requisito | Estado | Detalle |
|----|-----------|--------|---------|
| RF1 | Gestión de Productos (CRUD completo + categorías) | ⚠️ Parcial | Extiende product.template ✓; sin menú de listado de productos ni categorías |
| RF2 | Gestión de Ubicaciones jerárquicas | ⚠️ Parcial | Extiende stock.location ✓; solo vista "Por Tipo", sin CRUD completo ni almacenes |
| RF3 | Operaciones de Entrada (Recepciones) | ❌ Faltante | No hay vistas/menús de recepciones en el módulo custom |
| RF4 | Operaciones de Salida (Entregas) | ❌ Faltante | No hay vistas/menús de entregas en el módulo custom |
| RF5 | Ajustes de Inventario | ✅ Cumplido | Modelo completo con flujo de estados + wizards |
| RF6 | Traslados Internos | ❌ Faltante | No hay vistas/menús de traslados internos |
| RF7 | Informes de Inventario | ❌ Faltante | Menú "Informes" existe pero está vacío |

### Requisitos No Funcionales

| ID | Requisito | Estado | Detalle |
|----|-----------|--------|---------|
| RNF1 | Rendimiento (<2s CRUD, <5s informes) | ⚠️ Sin medir | `read_group` ✓, índices definidos ✓; sin benchmarks |
| RNF2 | Escalabilidad horizontal | ⚠️ Parcial | `ODOO_WORKERS: 2` configurado; sin Kubernetes |
| RNF3 | Disponibilidad 99.5% | ⚠️ Parcial | `restart: unless-stopped` ✓; sin HA real |
| RNF4 | Seguridad (roles, cifrado, auditoría) | ⚠️ Parcial | Grupos custom ✓, `mail.thread` ✓; sin SSL en dev, sin secretos cifrados |
| RNF5 | Mantenibilidad | ✅ Cumplido | CLAUDE.md ✓, código documentado ✓ |
| RNF6 | Monitorización | ⚠️ Parcial | Prometheus/Grafana ✓; sin logs centralizados |
| RNF7 | Backup y Recuperación | ❌ Faltante | Sin estrategia de backup automatizado |

---

## 12. Plan de Acción PRD — Brechas Pendientes

> Las tareas están ordenadas por prioridad de impacto. Las de Fase A son las que
> hacen que el módulo Odoo cumpla con el MVP del PRD.

---

### FASE A — Módulo Odoo: Completar RF faltantes (Alta prioridad)

#### A1 — RF7: Informes de Inventario ⭐ CRÍTICO

**Archivo a crear:** `odoo_custom_module/views/report_views.xml`
**Acción en manifest:** Agregar `"views/report_views.xml"` al array `data`.
**Acción en menu_views.xml:** Agregar actions a `menu_inventory_custom_reports`.

Vistas a implementar:

```xml
<!-- 1. Informe: Stock actual por producto y ubicación -->
<record id="action_report_stock_by_location" model="ir.actions.act_window">
    <field name="name">Stock por Ubicación</field>
    <field name="res_model">stock.quant</field>
    <field name="view_mode">tree,pivot,graph</field>
    <field name="domain">[('location_id.usage', '=', 'internal'), ('quantity', '>', 0)]</field>
    <field name="context">{'group_by': ['location_id', 'product_id']}</field>
</record>

<!-- 2. Informe: Movimientos de inventario -->
<record id="action_report_stock_moves" model="ir.actions.act_window">
    <field name="name">Historial de Movimientos</field>
    <field name="res_model">stock.move.line</field>
    <field name="view_mode">tree,pivot,graph</field>
    <field name="domain">[('state', '=', 'done')]</field>
</record>

<!-- 3. Informe: Productos con stock bajo mínimo -->
<record id="action_report_low_stock" model="ir.actions.act_window">
    <field name="name">Alertas de Stock Mínimo</field>
    <field name="res_model">product.template</field>
    <field name="view_mode">tree,form</field>
    <!-- domain filtra donde qty_available < min_stock_level -->
</record>

<!-- 4. Informe: Ajustes de inventario (histórico) -->
<record id="action_report_adjustments_history" model="ir.actions.act_window">
    <field name="name">Histórico de Ajustes</field>
    <field name="res_model">stock.inventory.adjustment</field>
    <field name="view_mode">tree,pivot,graph</field>
    <field name="domain">[('state', '=', 'done')]</field>
</record>
```

Menús a agregar en `menu_views.xml`:
```xml
<menuitem id="menu_report_stock_location" name="Stock por Ubicación"
          parent="menu_inventory_custom_reports"
          action="action_report_stock_by_location" sequence="1"/>
<menuitem id="menu_report_stock_moves" name="Historial de Movimientos"
          parent="menu_inventory_custom_reports"
          action="action_report_stock_moves" sequence="2"/>
<menuitem id="menu_report_low_stock" name="Alertas de Stock Mínimo"
          parent="menu_inventory_custom_reports"
          action="action_report_low_stock" sequence="3"/>
<menuitem id="menu_report_adjustments_history" name="Histórico de Ajustes"
          parent="menu_inventory_custom_reports"
          action="action_report_adjustments_history" sequence="4"/>
```

---

#### A2 — RF1: Menú Productos completo

**Archivo:** `odoo_custom_module/views/menu_views.xml`

Agregar los siguientes menús bajo `menu_inventory_custom_products`:

```xml
<!-- Listado de productos (reutiliza acción nativa de Odoo) -->
<menuitem id="menu_custom_product_list"
          name="Todos los Productos"
          parent="menu_inventory_custom_products"
          action="product.product_template_action_all"
          sequence="1"/>

<!-- Categorías de producto -->
<menuitem id="menu_custom_product_categories"
          name="Categorías"
          parent="menu_inventory_custom_products"
          action="product.product_category_action_form"
          sequence="2"/>

<!-- Marcas (ya existe, mover a sequence=3) -->
```

**Nota:** `action_product_brand` ya existe — solo ajustar `sequence` a 3.

---

#### A3 — RF2: Menú Ubicaciones completo

**Archivo:** `odoo_custom_module/views/menu_views.xml`

```xml
<!-- Vista full de todas las ubicaciones internas -->
<menuitem id="menu_custom_locations_all"
          name="Todas las Ubicaciones"
          parent="menu_inventory_custom_locations"
          action="stock.action_location_form"
          sequence="1"/>

<!-- Almacenes -->
<menuitem id="menu_custom_warehouses"
          name="Almacenes"
          parent="menu_inventory_custom_locations"
          action="stock.action_warehouse_form"
          sequence="2"/>

<!-- Por Tipo (ya existe — mover a sequence=3) -->
```

---

#### A4 — RF3/RF4/RF6: Operaciones de Almacén

**Archivo:** `odoo_custom_module/views/menu_views.xml`

Agregar bajo `menu_inventory_custom_operations` (después de los menús de ajuste existentes):

```xml
<!-- Recepciones -->
<menuitem id="menu_custom_receipts"
          name="Recepciones"
          parent="menu_inventory_custom_operations"
          action="stock.action_picking_tree_all"
          sequence="10"/>

<!-- Entregas -->
<menuitem id="menu_custom_deliveries"
          name="Entregas"
          parent="menu_inventory_custom_operations"
          action="stock.action_picking_tree_all"
          sequence="11"/>

<!-- Traslados Internos -->
<menuitem id="menu_custom_internal_transfers"
          name="Traslados Internos"
          parent="menu_inventory_custom_operations"
          action="stock.action_picking_tree_all"
          sequence="12"/>
```

**NOTA IMPORTANTE:** Las acciones de recepciones, entregas y traslados son el mismo
`stock.picking` filtrado por `picking_type_code`. Para tener vistas diferenciadas, crear
acciones con dominio en `product_views.xml`:

```xml
<record id="action_custom_receipts" model="ir.actions.act_window">
    <field name="name">Recepciones</field>
    <field name="res_model">stock.picking</field>
    <field name="view_mode">tree,form</field>
    <field name="domain">[('picking_type_code', '=', 'incoming')]</field>
    <field name="context">{'default_picking_type_code': 'incoming'}</field>
</record>

<record id="action_custom_deliveries" model="ir.actions.act_window">
    <field name="name">Entregas</field>
    <field name="res_model">stock.picking</field>
    <field name="view_mode">tree,form</field>
    <field name="domain">[('picking_type_code', '=', 'outgoing')]</field>
    <field name="context">{'default_picking_type_code': 'outgoing'}</field>
</record>

<record id="action_custom_internal_transfers" model="ir.actions.act_window">
    <field name="name">Traslados Internos</field>
    <field name="res_model">stock.picking</field>
    <field name="view_mode">tree,form</field>
    <field name="domain">[('picking_type_code', '=', 'internal')]</field>
    <field name="context">{'default_picking_type_code': 'internal'}</field>
</record>
```

Mover estas acciones a un nuevo archivo o a `stock_views.xml`.

---

### FASE B — Infraestructura: Gaps de arquitectura (Prioridad media)

#### B1 — RNF7: Estrategia de Backup Automatizado

**Archivo a crear:** `docker/backup/backup.sh`
**Acción en docker-compose.yml:** Agregar servicio `pg_backup`.

```yaml
pg_backup:
  image: postgres:15-alpine
  container_name: inventory_pg_backup
  environment:
    POSTGRES_USER: ${POSTGRES_USER:-odoo}
    POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-odoo_dev_pass}
    PGPASSWORD: ${POSTGRES_PASSWORD:-odoo_dev_pass}
    BACKUP_SCHEDULE: "0 2 * * *"   # 2am diario
    BACKUP_RETENTION_DAYS: 7
  volumes:
    - ./docker/backup/backup.sh:/backup.sh:ro
    - ./backups:/backups
  command: /bin/sh -c "crond -f"
  depends_on:
    pg_db:
      condition: service_healthy
  profiles:
    - production
  networks:
    - backend-network
```

Script `backup.sh`:
```bash
#!/bin/sh
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump -h pg_db -U $POSTGRES_USER odoo_db | gzip > /backups/odoo_db_$DATE.sql.gz
find /backups -name "*.sql.gz" -mtime +${BACKUP_RETENTION_DAYS:-7} -delete
```

---

#### B2 — RNF6: Log Centralizado (Loki + Grafana)

**Acción en docker-compose.yml:** Agregar servicio `loki` al perfil `monitoring`.

```yaml
loki:
  image: grafana/loki:2.9.0
  container_name: inventory_loki
  command: -config.file=/etc/loki/local-config.yaml
  volumes:
    - ./docker/loki/loki-config.yaml:/etc/loki/local-config.yaml:ro
  networks:
    - backend-network
  profiles:
    - monitoring

promtail:
  image: grafana/promtail:2.9.0
  container_name: inventory_promtail
  volumes:
    - /var/log:/var/log:ro
    - /var/lib/docker/containers:/var/lib/docker/containers:ro
    - ./docker/promtail/promtail-config.yaml:/etc/promtail/config.yaml:ro
  command: -config.file=/etc/promtail/config.yaml
  networks:
    - backend-network
  profiles:
    - monitoring
```

**Archivo a crear:** `docker/loki/loki-config.yaml` y `docker/promtail/promtail-config.yaml`.
**Acción en Grafana:** Agregar Loki como datasource en `docker/grafana/provisioning/datasources.yaml`.

---

#### B3 — RNF4: Prometheus Alert Rules

**Archivo a completar:** `docker/prometheus/rules/alerts.yml`

Reglas mínimas a implementar:
```yaml
groups:
  - name: inventory_alerts
    rules:
      - alert: OdooDown
        expr: up{job="odoo"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Odoo está caído"

      - alert: PostgreSQLDown
        expr: up{job="postgres"} == 0
        for: 1m
        labels:
          severity: critical

      - alert: HighMemoryUsage
        expr: (container_memory_usage_bytes / container_spec_memory_limit_bytes) > 0.85
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Contenedor usando >85% de memoria"

      - alert: ETLJobFailed
        expr: increase(etl_errors_total[1h]) > 5
        for: 0m
        labels:
          severity: warning
        annotations:
          summary: "ETL acumuló más de 5 errores en la última hora"
```

---

#### B4 — Grafana: Dashboards faltantes

**Archivos a crear** en `docker/grafana/dashboards/`:
- `odoo-metrics.json` — dashboard de Odoo (requests/s, errores, workers activos)
- `etl-pipeline.json` — dashboard del ETL (registros procesados, errores, tiempo de ejecución)
- `database-metrics.json` — dashboard de PostgreSQL (conexiones, cache hit ratio, tamaño BD)

---

### FASE C — Módulo Odoo: Mejoras de calidad (Baja prioridad)

#### C1 — RF1: Campo `barcode` visible en formulario de producto

El `barcode` ya existe en `product.template` de Odoo. Verificar que esté accesible
en la vista del módulo o que no sea necesario sobreescribirlo.

#### C2 — Alertas de stock mínimo en tiempo real

Agregar un servidor de acciones (`ir.actions.server`) o cron que notifique vía
`mail.thread` cuando `qty_available < min_stock_level`.

#### C3 — Tests de integración para RF3/RF4

Extender `tests/test_models.py` con tests que verifiquen:
- Que las acciones de recepciones, entregas y traslados retornan los pickings correctos
- Que los reportes de stock devuelven datos coherentes

---

### Resumen de Esfuerzo Estimado

| Fase | Tarea | Archivos afectados | Complejidad |
|------|-------|-------------------|-------------|
| A1 | Informes de inventario | `report_views.xml` (nuevo), `menu_views.xml` | Media |
| A2 | Menú Productos completo | `menu_views.xml` | Baja |
| A3 | Menú Ubicaciones completo | `menu_views.xml` | Baja |
| A4 | Operaciones de almacén | `menu_views.xml`, `stock_views.xml` | Media |
| B1 | Backup automatizado | `docker-compose.yml`, `docker/backup/` | Media |
| B2 | Log centralizado Loki | `docker-compose.yml`, `docker/loki/` | Alta |
| B3 | Alert rules Prometheus | `docker/prometheus/rules/alerts.yml` | Baja |
| B4 | Dashboards Grafana | `docker/grafana/dashboards/*.json` | Alta |
| C1 | Barcode en formulario | `product_views.xml` | Baja |
| C2 | Alertas stock mínimo | `models/`, `data/` | Media |
| C3 | Tests integración | `tests/test_models.py` | Media |

**Orden de ejecución recomendado:** A2 → A3 → A4 → A1 → B3 → B1 → C1 → C2 → B2 → B4 → C3

---

*Última actualización: 2026-03-30*
*Versión del módulo: 16.0.1.0.0*
*Versión de Odoo: 16.0*
*Autor del documento: Claude Code (auditoría PRD/Arquitectura)*
