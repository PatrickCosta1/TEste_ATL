#!/usr/bin/env python3

from advanced_product_selector import AdvancedProductSelector
from database_manager import DatabaseManager

# Criar instância
selector = AdvancedProductSelector()
selector.db = DatabaseManager()

# Teste com dados simples
conditions = {'aquecimento': 'sim'}
dimensions = {'volume': 45}  # 45m³ volume
metrics = {'volume': 45}

print('=== TESTE DE SELEÇÃO DE AQUECIMENTO ===')
result = selector._select_heating_products(conditions, dimensions, metrics)
print('=== RESULTADO ===')
for key, value in result.items():
    print(f'{key}: {value}')
