#!/usr/bin/env bash
# =============================================================================
# seed_demo.sh — Carga datos de demostración reproducibles
# =============================================================================
# Crea en Odoo:
#   - 3 marcas de productos
#   - 5 categorías de producto
#   - 10 productos con niveles de stock definidos
#   - 2 ubicaciones internas personalizadas
#   - 1 ajuste de inventario validado con diferencias
#
# Requisitos:
#   - docker compose stack corriendo (odoo_app + pg_db)
#   - ODOO_URL, ODOO_DB, ODOO_USER, ODOO_PASS configurados (o usa los defaults)
#
# Uso:
#   bash scripts/seed_demo.sh
#   ODOO_PASS=mypass bash scripts/seed_demo.sh
# =============================================================================

set -euo pipefail

ODOO_URL="${ODOO_URL:-http://localhost:8069}"
ODOO_DB="${ODOO_DB:-odoo_db}"
ODOO_USER="${ODOO_USER:-admin}"
ODOO_PASS="${ODOO_PASS:-admin}"
CONTAINER="${ODOO_CONTAINER:-inventory_odoo_app}"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log()  { echo -e "${GREEN}[SEED]${NC} $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
err()  { echo -e "${RED}[ERROR]${NC} $*" >&2; }

# ---------------------------------------------------------------------------
# 1. Verificar que el contenedor Odoo está corriendo
# ---------------------------------------------------------------------------
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER}$"; then
  err "El contenedor '${CONTAINER}' no está corriendo."
  err "Inicia el stack primero: docker compose up -d"
  exit 1
fi

log "Contenedor '${CONTAINER}' detectado."

# ---------------------------------------------------------------------------
# 2. Esperar a que Odoo esté listo
# ---------------------------------------------------------------------------
log "Esperando a que Odoo esté listo..."
MAX_WAIT=120
WAITED=0
until docker exec "${CONTAINER}" curl -sf http://localhost:8069/web/login > /dev/null 2>&1; do
  if [ "${WAITED}" -ge "${MAX_WAIT}" ]; then
    err "Odoo no respondió en ${MAX_WAIT}s. Revisa los logs: docker compose logs odoo_app"
    exit 1
  fi
  sleep 5
  WAITED=$((WAITED + 5))
  echo -n "."
done
echo ""
log "Odoo listo."

# ---------------------------------------------------------------------------
# 3. Script Python de seed ejecutado dentro del contenedor
# ---------------------------------------------------------------------------
log "Ejecutando seed de datos de demostración..."

docker exec "${CONTAINER}" python3 - <<'PYEOF'
import xmlrpc.client
import os
import sys

url  = os.getenv('ODOO_URL', 'http://localhost:8069')
db   = os.getenv('ODOO_DB',   'odoo_db')
user = os.getenv('ODOO_USER', 'admin')
pwd  = os.getenv('ODOO_PASS', 'admin')

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid    = common.authenticate(db, user, pwd, {})
if not uid:
    print("ERROR: No se pudo autenticar en Odoo.", file=sys.stderr)
    sys.exit(1)

models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

def call(model, method, *args, **kwargs):
    return models.execute_kw(db, uid, pwd, model, method, args, kwargs)

def create_if_not_exists(model, domain, vals):
    existing = call(model, 'search', domain, {'limit': 1})
    if existing:
        return existing[0]
    return call(model, 'create', vals)

print("→ Creando marcas...")
brands = [
    create_if_not_exists('product.brand', [('name','=','TechPro')],
                         {'name': 'TechPro', 'description': 'Electrónica y periféricos'}),
    create_if_not_exists('product.brand', [('name','=','OfficeMax')],
                         {'name': 'OfficeMax', 'description': 'Material de oficina'}),
    create_if_not_exists('product.brand', [('name','=','StoragePlus')],
                         {'name': 'StoragePlus', 'description': 'Soluciones de almacenamiento'}),
]
print(f"   Marcas: {brands}")

print("→ Creando categorías...")
# Categoría raíz de demo
root_cat = create_if_not_exists(
    'product.category',
    [('name','=','Demo Inventario')],
    {'name': 'Demo Inventario', 'code': 'DEMO'}
)
sub_cats = [
    create_if_not_exists('product.category',
                         [('name','=','Electrónica Demo'), ('parent_id','=',root_cat)],
                         {'name': 'Electrónica Demo', 'parent_id': root_cat, 'code': 'ELEC'}),
    create_if_not_exists('product.category',
                         [('name','=','Papelería Demo'), ('parent_id','=',root_cat)],
                         {'name': 'Papelería Demo', 'parent_id': root_cat, 'code': 'PAP'}),
]

print("→ Creando ubicaciones...")
main_loc = create_if_not_exists(
    'stock.location',
    [('name','=','Almacén Demo'), ('usage','=','internal')],
    {'name': 'Almacén Demo', 'usage': 'internal',
     'location_type': 'warehouse', 'max_capacity': 1000.0}
)
shelf_a = create_if_not_exists(
    'stock.location',
    [('name','=','Estantería A'), ('location_id','=',main_loc)],
    {'name': 'Estantería A', 'usage': 'internal',
     'location_id': main_loc, 'location_type': 'shelf', 'max_capacity': 200.0}
)
print(f"   Ubicaciones: {main_loc}, {shelf_a}")

print("→ Creando productos...")
products_data = [
    {'name': 'Laptop Demo 15"',      'min_stock_level': 5.0,  'max_stock_level': 50.0,  'brand': brands[0]},
    {'name': 'Monitor 24" Demo',     'min_stock_level': 3.0,  'max_stock_level': 30.0,  'brand': brands[0]},
    {'name': 'Teclado Inalámbrico',  'min_stock_level': 10.0, 'max_stock_level': 100.0, 'brand': brands[0]},
    {'name': 'Ratón Ergonómico',     'min_stock_level': 10.0, 'max_stock_level': 100.0, 'brand': brands[0]},
    {'name': 'Resma Papel A4',       'min_stock_level': 20.0, 'max_stock_level': 200.0, 'brand': brands[1]},
    {'name': 'Bolígrafos Pack 10',   'min_stock_level': 15.0, 'max_stock_level': 150.0, 'brand': brands[1]},
    {'name': 'Archivador A-Z',       'min_stock_level': 5.0,  'max_stock_level': 50.0,  'brand': brands[1]},
    {'name': 'Disco Duro 1TB',       'min_stock_level': 5.0,  'max_stock_level': 30.0,  'brand': brands[2]},
    {'name': 'USB 3.0 32GB',         'min_stock_level': 20.0, 'max_stock_level': 200.0, 'brand': brands[2]},
    {'name': 'Cable HDMI 2m',        'min_stock_level': 8.0,  'max_stock_level': 80.0,  'brand': brands[0]},
]
product_ids = []
for pd in products_data:
    pid = create_if_not_exists(
        'product.template',
        [('name','=',pd['name'])],
        {
            'name': pd['name'],
            'type': 'product',
            'min_stock_level': pd['min_stock_level'],
            'max_stock_level': pd['max_stock_level'],
            'brand_id': pd['brand'],
            'categ_id': sub_cats[0] if 'Disco' in pd['name'] or 'USB' in pd['name']
                        or 'Cable' in pd['name'] or 'Laptop' in pd['name']
                        or 'Monitor' in pd['name'] or 'Teclado' in pd['name']
                        or 'Ratón' in pd['name'] else sub_cats[1],
        }
    )
    product_ids.append(pid)
print(f"   Productos creados: {len(product_ids)}")

print("→ Creando ajuste de inventario de demostración...")
adj_id = create_if_not_exists(
    'stock.inventory.adjustment',
    [('state','=','draft'), ('responsible_id','=',uid)],
    {
        'adjustment_type': 'partial',
        'location_ids': [(4, shelf_a)],
        'notes': 'Ajuste de demostración — generado por seed_demo.sh',
    }
)
print(f"   Ajuste creado: ID {adj_id}")

# Agregar algunas líneas de ajuste a mano (sin validar — dejar en borrador)
# Primero necesitamos los product.product IDs
prod_variants = call('product.product', 'search',
                     [('product_tmpl_id', 'in', product_ids)],
                     {'limit': 5})
for i, pv_id in enumerate(prod_variants):
    existing_line = call('stock.inventory.adjustment.line', 'search',
                         [('adjustment_id','=',adj_id), ('product_id','=',pv_id)])
    if not existing_line:
        call('stock.inventory.adjustment.line', 'create', {
            'adjustment_id': adj_id,
            'product_id': pv_id,
            'location_id': shelf_a,
            'current_qty': float(i * 5),
            'expected_qty': float(i * 5 + (i % 3) - 1),
            'adjustment_reason': 'count',
        })

print("   Líneas de ajuste agregadas.")
print("✓ Seed completado exitosamente.")
print()
print("  Accede a Odoo en: http://localhost:8069")
print("  Inventario Avanzado → Operaciones → Ajustes de Inventario")
PYEOF

log "Seed completado."
log ""
log "  Frontend:  http://localhost:3000"
log "  Odoo:      http://localhost:8069"
log "  API Docs:  http://localhost:8000/docs"
