#!/usr/bin/env python3
"""
Teste rápido para verificar se a família da laje aparece corretamente no frontend
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app

def test_family_filter():
    """Testa o filtro family_display_name"""
    
    print("=== TESTE: FILTRO FAMILY_DISPLAY_NAME ===\n")
    
    # Testar todas as famílias
    families_to_test = [
        'filtracao',
        'recirculacao_iluminacao', 
        'tratamento_agua',
        'revestimento',
        'aquecimento',
        'construcao',
        'construcao_laje'  # Nossa nova família
    ]
    
    with app.app_context():
        for family in families_to_test:
            # Usar o filtro diretamente
            display_name = app.jinja_env.filters['family_display_name'](family)
            print(f"{family} → {display_name}")
    
    print("\n✅ Teste concluído")

if __name__ == "__main__":
    test_family_filter()
