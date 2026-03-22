# Documentación de Modelos - inventory_custom

**Versión:** 1.0.0  
**Odoo:** 16.0  
**Última actualización:** 2026-03-22

---

## Modelos Personalizados

### 1. product.brand (Marca de Producto)

**Tabla en BD:** `product_brand`

| Campo | Tipo | Descripción | Requerido |
|-------|------|-------------|-----------|
| id | integer | ID único | Auto |
| name | char | Nombre de la marca | Sí |
| description | text | Descripción de la marca | No |
| logo | binary | Logo de la marca (adjunto) | No |
| product_count | integer | Contador de productos (calculado) | Auto |
| product_ids | one2many | Productos asociados | Auto |
| active | boolean | Marca activa/inactiva | Default: True |
| create_date | datetime | Fecha de creación | Auto |
| write_date | datetime | Fecha de modificación | Auto |

**Métodos disponibles:**
- `name_get()` - Retorna tuplas (id, name)

---

## Modelos Extendidos

### 2. product.template (Plantilla de Producto)

**Herencia:** `product.template` → Se agregan campos personalizados

| Campo | Tipo | Descripción | Requerido |
|-------|------|-------------|-----------|
| brand_id | many2one | Marca del producto (product.brand) | No |
| min_stock_level | float | Nivel mínimo de stock para alertas | No |
| max_stock_level | float | Nivel máximo de stock | No |

**Validaciones:**
- `_check_stock_levels()`: El nivel mínimo no puede ser mayor que el máximo

**Campos existentes en Odoo 16 útiles:**
- `property_stock_inventory` (many2one) - Ubicación de inventario
- `property_stock_production` (many2one) - Ubicación de producción
- `reordering_min_qty` (float) - Cantidad mínima de reorden
- `reordering_max_qty` (float) - Cantidad máxima de reorden

---

### 3. stock.location (Ubicación de Almacén)

**Herencia:** `stock.location` → Se agregan campos personalizados

| Campo | Tipo | Descripción | Requerido |
|-------|------|-------------|-----------|
| location_type | selection | Tipo de ubicación (warehouse, zone, aisle, rack, shelf, bin, transit, quality, returns, scrap) | Default: bin |
| max_capacity | float | Capacidad máxima de almacenamiento | No |
| current_capacity | float | Capacidad actual (calculado) | Auto |
| capacity_usage_percent | float | Porcentaje de uso (calculado) | Auto |
| responsible_id | many2one | Usuario responsable (res.users) | No |
| barcode | char | Código de barras | No |
| usage_class | selection | Clase de almacenamiento (dry, cold, frozen, hazardous, standard) | Default: standard |
| temperature_range | char | Rango de temperatura (ej: 2-8°C) | No |

**Constrainst:**
- `_check_location_type_compatibility()`: Una ubicación tipo "Almacén" solo puede tener uso "Interno" o "Vista"

**Métodos disponibles:**
- `get_child_locations_tree()` - Retorna estructura de árbol de ubicaciones
- `get_locations_by_type(location_type)` - Retorna ubicaciones filtradas por tipo

---

### 4. product.category (Categoría de Producto)

**Herencia:** `product.category` → Se agregan campos personalizados

| Campo | Tipo | Descripción | Requerido |
|-------|------|-------------|-----------|
| code | char | Código de categoría | No |
| description | text | Descripción de la categoría | No |
| image | binary | Imagen de la categoría | No |
| active | boolean | Categoría activa/inactiva | Default: True |

**Constrainst:**
- `_check_hierarchy()` - Evita categorías recursivas

**Métodos disponibles:**
- `name_create(name)` - Crea categoría desde el nombre
- `get_full_path()` - Retorna ruta completa de categorías
- `get_subcategories(include_self=False)` - Retorna todas las subcategorías

---

## Modelos de Odoo 16 Compatibles

### 5. stock.lot (Lote/Serial)

**Nota:** En Odoo 16 el modelo se llama `stock.lot` (antes era `stock.production.lot`)

| Campo | Tipo | Descripción |
|-------|------|-------------|
| name | char | Nombre del lote |
| product_id | many2one | Producto asociado |
| product_qty | float | Cantidad del producto |
| company_id | many2one | Compañía |

---

### 6. stock.quant (Cantidades en Stock)

| Campo | Tipo | Descripción |
|-------|------|-------------|
| product_id | many2one | Producto |
| location_id | many2one | Ubicación |
| quantity | float | Cantidad |
| lot_id | many2one | Lote asociado (stock.lot) |
| lot_name | char | Nombre del lote (relacionado) |

---

### 7. stock.warehouse.orderpoint (Reglas de Reorden)

**Nota:** Este modelo reemplaza la funcionalidad de mínimos/máximos de stock en Odoo 16

| Campo | Tipo | Descripción |
|-------|------|-------------|
| product_id | many2one | Producto |
| location_id | many2one | Ubicación |
| product_min_qty | float | Cantidad mínima |
| product_max_qty | float | Cantidad máxima |
| qty_to_order | float | Cantidad a ordenar (calculado) |
| warehouse_id | many2one | Almacén |
| trigger | selection | Disparador (manual, auto) |

---

## Estructura de Menús

```
Inventario Avanzado (stock.group_stock_manager)
├── Productos (stock.group_stock_user)
│   └── Marcas (product.brand)
│   └── Stock Bajo (product.product filtrado)
├── Ubicaciones (stock.group_stock_user)
│   └── Por Tipo (stock.location agrupado)
├── Operaciones (stock.group_stock_user)
└── Informes (stock.group_stock_manager)
    └── Stock por Ubicación (stock.quant)
    └── Historial de Ajustes (stock.inventory)
    └── Valoración (product.product)
```

---

## Notas Importantes de Compatibilidad Odoo 16

### Modelos NO disponibles en Odoo 16 base:
- `stock.inventory` - No existe como modelo separado
- `stock.inventory.line` - No existe como modelo separado
- `stock.production.lot` - Renombrado a `stock.lot`

### Campos NO disponibles en Odoo 16 base:
- `lot_id.expiration_date` - No existe en `stock.lot`
- `lot_id.use_date` - No existe en `stock.lot`
- `product_id.product_ids` - No existe en `product.category`

### Equivalencias Odoo 16:
| Odoo 14/15 | Odoo 16 |
|------------|---------|
| stock.production.lot | stock.lot |
| stock.inventory | Funcionalidad en stock.picking |
| stock.inventory.line | stock.move.line |

---

## Checklist de Validación Pre-Instalación

```bash
# Verificar modelos
docker exec odoo psql -U odoo -d odoo_db -c \
  "SELECT model FROM ir_model WHERE model IN ('product.brand', 'stock.location');"

# Verificar campos agregados
docker exec odoo psql -U odoo -d odoo_db -c \
  "SELECT name FROM ir_model_fields WHERE model='product.template' AND name IN ('brand_id', 'min_stock_level');"

# Verificar estado del módulo
docker exec odoo psql -U odoo -d odoo_db -c \
  "SELECT name, state FROM ir_module_module WHERE name='inventory_custom';"
```

---

*Documento generado automáticamente - 2026-03-22*
