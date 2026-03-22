# -*- coding: utf-8 -*-
"""
Script de validación de XPath para vistas de Odoo

Este script valida que los XPath en las vistas XML sean correctos
antes de intentar instalar el módulo.

Uso:
    python validate_views.py
"""

import xml.etree.ElementTree as etree
import os


def validate_xml_file(xml_path):
    """
    Valida que el archivo XML sea válido.
    
    Args:
        xml_path: Ruta al archivo XML
    
    Returns:
        tuple: (es_valido, mensaje)
    """
    try:
        tree = etree.parse(xml_path)
        root = tree.getroot()
        
        if root.tag != 'odoo':
            return False, f"Raíz debe ser <odoo>, encontrado: {root.tag}"
        
        # Validar estructura de data
        data = root.find('data')
        if data is None:
            return False, "Falta elemento <data>"
        
        # Contar elementos válidos
        records = data.findall('record')
        menuitems = data.findall('menuitem')
        
        total = len(records) + len(menuitems)
        
        if total == 0:
            return False, "No hay registros ni menuitems"
        
        # Validar XPath en vistas heredadas
        for record in records:
            model = record.get('model')
            if model == 'ir.ui.view':
                arch_field = record.find("field[@name='arch']")
                if arch_field is not None:
                    # Buscar elementos xpath
                    for elem in arch_field.iter():
                        if elem.tag == 'xpath':
                            expr = elem.get('expr')
                            if expr and not (expr.startswith('//') or expr.startswith('/')):
                                return False, f"XPath inválido: {expr}"
        
        return True, f"Válido ({len(records)} registros, {len(menuitems)} menuitems)"
    
    except etree.ParseError as e:
        return False, f"Error de parseo XML: {e}"
    except Exception as e:
        return False, f"Error: {e}"


def main():
    """Función principal de validación"""
    
    views_to_validate = [
        'views/product_views.xml',
        'views/stock_views.xml',
        'views/menu_views.xml',
    ]
    
    module_path = os.path.dirname(os.path.abspath(__file__))
    base_path = os.path.dirname(module_path)
    
    print("=" * 60)
    print("VALIDACIÓN DE VISTAS - inventory_custom")
    print("=" * 60)
    
    all_valid = True
    
    for view_file in views_to_validate:
        view_path = os.path.join(base_path, view_file)
        
        if not os.path.exists(view_path):
            print(f"\n[FAIL] {view_file}: Archivo no encontrado")
            all_valid = False
            continue
        
        is_valid, message = validate_xml_file(view_path)
        
        status = "[OK]" if is_valid else "[FAIL]"
        print(f"\n{status} {view_file}")
        print(f"    {message}")
        
        if not is_valid:
            all_valid = False
    
    print("\n" + "=" * 60)
    if all_valid:
        print("RESULTADO: Todas las vistas son válidas")
    else:
        print("RESULTADO: Hay errores en las vistas")
    print("=" * 60)
    
    return 0 if all_valid else 1


if __name__ == '__main__':
    exit(main())
