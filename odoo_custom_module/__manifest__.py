{
    "name": "inventory_custom",
    "version": "16.0.1.0.0",
    "category": "Inventory",
    "summary": "Módulo personalizado de gestión de inventario avanzado",
    "description": """
Advanced Inventory Management Module for Odoo 16.

Features:
- Product brands with product count
- Extended stock locations with capacity tracking and usage classification
- Extended product categories with hierarchy utilities
- Custom inventory adjustment workflow (draft → in_progress → done)
- Quick adjustment wizard for single-product corrections
- Quick count wizard for full location inventory
- Custom security groups (Manager, Operator, Viewer)
    """,
    "author": "Luis Brito",
    "website": "https://inventory.local",
    "license": "LGPL-3",
    "depends": [
        "base",
        "product",
        "stock",
        "mail",
    ],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "data/stock_data.xml",
        "data/cron_data.xml",
        "views/product_views.xml",
        "views/stock_views.xml",
        "views/menu_views.xml",
        "views/inventory_adjustment_views.xml",
        "views/report_views.xml",
    ],
    "demo": [],
    "installable": True,
    "application": True,
    "auto_install": False,
}
