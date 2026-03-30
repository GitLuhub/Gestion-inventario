# Carta a Mi Yo del Futuro: Lecciones Aprendidas en Odoo 16

---

**Querido yo del futuro,**

Si estás leyendo esto, probablemente estás intentando instalar un módulo personalizado de Odoo y te estás frustrando. Respira. Aquí van las lecciones que aprendí:

---

## 1. Validación de API ≠ API Real

Antes de escribir código, **verifica en la base de datos** qué campos y modelos realmente existen. Odoo 16 renombró muchos modelos (`stock.production.lot` → `stock.lot`) y eliminó campos. No asumas que la documentación o el IDE son correctos.

**Comando útil:**
```sql
SELECT name FROM ir_model_fields WHERE model='stock.lot';
```

---

## 2. Los Errores de Python son Mentirosos

Los mensajes de error de Odoo a veces apuntan a la línea equivocada. El error "Element odoo has extra content" era en realidad por un XPath inválido en otra vista. **Lee los logs completos** y busca el error real, no el primero que ves.

---

## 3. La Caché es Tu Enemiga

Odoo cachea TODO: módulos, vistas, archivos Python, CSS. Cuando algo no funciona después de un cambio:

```bash
# Limpia cache
rm -rf /var/lib/odoo/filestore/*
rm -rf /mnt/extra-addons/*/__pycache__

# Reinicia contenedor
docker restart inventory_odoo_app
```

---

## 4. Copy-Paste es Peligroso

Este módulo fue escrito probablemente para Odoo 14 o 18. Los nombres de modelos cambian entre versiones. **Nunca copies código entre versiones de Odoo sin verificar**.

---

## 5. Dependencias en Cascada

Cuando eliminamos `ProductProduct` del `__init__.py` pero alguien más lo esperaba, todo falló silenciosamente. **Mantén un registro de las dependencias explícitamente**.

---

## 6. Los Datos Demo Son Opcionales

Si el módulo no instala, **primero elimina los datos de demostración** (`data/stock_data.xml`). Instálalo básico primero, luego agrega datos.

---

## 7. Los Permisos Importan en Docker

Los archivos copiados desde el host heredan permisos del usuario que los creó. Cuando `docker cp` no funciona como esperas:

```bash
chown -R odoo:odoo /mnt/extra-addons/inventory_custom
```

---

## La Regla de Oro

> **"Si el módulo no instala en 30 minutos, estás haciendo algo fundamentalmente mal. Detente, respira, y vuelve a verificar los modelos y campos en la base de datos."**

---

# Recomendaciones para Continuar el Desarrollo

## Fase 1: Estabilización del Módulo

- [ ] **Verificar todos los modelos heredados** contra la API de Odoo 16
- [ ] **Documentar los campos disponibles** en cada modelo personalizado
- [ ] **Agregar tests unitarios** para los modelos Python
- [ ] **Validar XPath de vistas** antes de instalar

## Fase 2: Funcionalidades Pendientes

- [ ] **Reimplementar StockInventoryLine y StockInventory** con campos compatibles de Odoo 16
- [ ] **Agregar tracking de lotes** usando la nueva estructura de `stock.lot`
- [ ] **Implementar alerts de stock bajo** (revisa cómo hacerlo con `stock.quant` y `stock.replenishment`)
- [ ] **Crear dashboard de inventario** con métricas clave

## Fase 3: Mejoras de UX

- [ ] **Validar el XPath de vistas** usando el editor de vistas de Odoo
- [ ] **Agregar iconos a los menús** (atributo `web_icon`)
- [ ] **Implementar colores condicionales** en listas de productos
- [ ] **Crear wizard de ajustes de inventario** más intuitivo

## Fase 4: Integración con Otros Servicios

- [ ] **Verificar conexión con API Gateway** (FastAPI)
- [ ] **Probar sincronización con ETL Service**
- [ ] **Validar endpoints del Frontend Next.js**
- [ ] **Configurar logs centralizados**

## Fase 5: Producción

- [ ] **Migrar datos de demo** a datos de prueba realistas
- [ ] **Configurar backups automáticos** de PostgreSQL
- [ ] **Implementar monitoreo** con Prometheus + Grafana
- [ ] **Documentar instalación** para otros desarrolladores

---

## Checklist de Verificación Pre-Instalación

Antes de instalar el módulo, ejecutar estos checks:

```bash
# 1. Verificar que los modelos existen
docker exec odoo psql -U odoo -d odoo_db -c \
  "SELECT model FROM ir_model WHERE model LIKE 'stock.%';"

# 2. Verificar campos de producto
docker exec odoo psql -U odoo -d odoo_db -c \
  "SELECT name FROM ir_model_fields WHERE model='product.product';"

# 3. Verificar grupo de stock
docker exec odoo psql -U odoo -d odoo_db -c \
  "SELECT name FROM res_groups WHERE name LIKE '%stock%';"

# 4. Limpiar cache antes de instalar
docker exec odoo bash -c "rm -rf /var/lib/odoo/filestore/*"
docker restart inventory_odoo_app
```

---

## Recursos Útiles

- [Odoo 16 API Reference](https://www.odoo.com/documentation/16.0/developer/reference.html)
- [Odoo Migration Guide](https://upgrade.odoo.com/)
- [Stock Module Source Code](https://github.com/odoo/odoo/tree/16.0/addons/stock/models)

---

*Con cariño,*
*Tu yo del pasado*
*Marzo 2026*

---

**Última actualización:** 2026-03-22
