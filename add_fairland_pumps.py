#!/usr/bin/env python3
"""
Script para adicionar as bombas Fairland InverX20 à base de dados SQLite
"""

import sqlite3
import os

def add_fairland_pumps():
    """Adiciona as bombas Fairland à base de dados"""
    
    # Bombas Fairland InverX20 para adicionar
    fairland_pumps = [
        {
            'id': 109,
            'category_id': 27,
            'code': 'FAIR-X20-14',
            'name': 'Fairland InverX20 X20-14 (14kW, 30-50m³)',
            'description': 'Bomba de calor Fairland InverX20 14kW para piscinas de 30-50m³',
            'brand': 'Fairland',
            'model': 'X20-14',
            'unit': 'UN',
            'base_price': 2900.00,
            'cost_price': 2320.00,
            'is_active': 1
        },
        {
            'id': 110,
            'category_id': 27,
            'code': 'FAIR-X20-18',
            'name': 'Fairland InverX20 X20-18 (18kW, 40-65m³)',
            'description': 'Bomba de calor Fairland InverX20 18kW para piscinas de 40-65m³',
            'brand': 'Fairland',
            'model': 'X20-18',
            'unit': 'UN',
            'base_price': 3400.00,
            'cost_price': 2720.00,
            'is_active': 1
        },
        {
            'id': 111,
            'category_id': 27,
            'code': 'FAIR-X20-22',
            'name': 'Fairland InverX20 X20-22 (22kW, 45-75m³)',
            'description': 'Bomba de calor Fairland InverX20 22kW para piscinas de 45-75m³',
            'brand': 'Fairland',
            'model': 'X20-22',
            'unit': 'UN',
            'base_price': 3900.00,
            'cost_price': 3120.00,
            'is_active': 1
        },
        {
            'id': 112,
            'category_id': 27,
            'code': 'FAIR-X20-26',
            'name': 'Fairland InverX20 X20-26 (26kW, 55-90m³)',
            'description': 'Bomba de calor Fairland InverX20 26kW para piscinas de 55-90m³',
            'brand': 'Fairland',
            'model': 'X20-26',
            'unit': 'UN',
            'base_price': 4900.00,
            'cost_price': 3920.00,
            'is_active': 1
        }
    ]
    
    # Conectar à base de dados
    db_path = 'database/pool_budgets.db'
    if not os.path.exists(db_path):
        print(f"Erro: Base de dados {db_path} não encontrada!")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("Adicionando bombas Fairland à base de dados...")
        
        for pump in fairland_pumps:
            # Verificar se já existe
            cursor.execute('SELECT id FROM products WHERE id = ?', (pump['id'],))
            if cursor.fetchone():
                print(f"Bomba ID {pump['id']} já existe, a atualizar...")
                cursor.execute('''
                    UPDATE products 
                    SET category_id=?, code=?, name=?, description=?, brand=?, model=?, 
                        unit=?, base_price=?, cost_price=?, is_active=?, updated_at=CURRENT_TIMESTAMP
                    WHERE id=?
                ''', (
                    pump['category_id'], pump['code'], pump['name'], pump['description'],
                    pump['brand'], pump['model'], pump['unit'], pump['base_price'],
                    pump['cost_price'], pump['is_active'], pump['id']
                ))
            else:
                print(f"Inserindo bomba {pump['name']}...")
                cursor.execute('''
                    INSERT INTO products 
                    (id, category_id, code, name, description, brand, model, unit, base_price, cost_price, is_active, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ''', (
                    pump['id'], pump['category_id'], pump['code'], pump['name'], pump['description'],
                    pump['brand'], pump['model'], pump['unit'], pump['base_price'],
                    pump['cost_price'], pump['is_active']
                ))
        
        conn.commit()
        print("✓ Bombas Fairland adicionadas com sucesso!")
        
        # Verificar se foram inseridas
        cursor.execute('SELECT id, name, brand, base_price FROM products WHERE brand = "Fairland"')
        results = cursor.fetchall()
        print(f"\nBombas Fairland na base de dados ({len(results)} encontradas):")
        for r in results:
            print(f"  ID: {r[0]}, Nome: {r[1]}, Marca: {r[2]}, Preço: €{r[3]}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"Erro ao adicionar bombas: {e}")
        return False

if __name__ == "__main__":
    success = add_fairland_pumps()
    if success:
        print("\n✓ Script concluído com sucesso!")
    else:
        print("\n✗ Script falhou!")
