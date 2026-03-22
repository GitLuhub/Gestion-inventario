{
    "name": "inventory_custom",
    "version": "1.0.0",
    "category": "Inventory",
    "summary": "Módulo personalizado de gestión de inventario avanzado",
    "description": """
        Módulo de Gestión de Inventario Avanzado para Odoo 16.0
        
        Funcionalidades:
        - Gestión de productos y variantes
        - Gestión de ubicaciones de almacén
        - Recepciones de mercancía
        - Entregas de mercancía
        - Ajustes de inventario
        - Traslados internos
        - Informes de inventario
        
        Requisitos cubiertos:
        - RF1: Gestión de Productos
        - RF2: Gestión de Ubicaciones
        - RF3: Recepción de Mercancía
        - RF4: Entregas de Mercancía
        - RF5: Ajustes de Inventario
        - RF6: Traslados Internos
        - RF7: Informes de Inventario
    """,
    "author": "Inventory Team",
    "website": "https://inventory.local",
    "license": "LGPL-3",
    "depends": [
        "base",
        "product",
        "stock",
    ],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "data/stock_data.xml",
        "views/product_views.xml",
        "views/stock_views.xml",
        "views/menu_views.xml",
    ],
    "demo": [
    ],
    "installable": True,
    "application": True,
    "auto_install": False,
}
