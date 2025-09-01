#!/usr/bin/env python3

import sqlite3

conn = sqlite3.connect('database/pool_budgets.db')
cursor = conn.cursor()
cursor.execute('UPDATE selection_rules SET condition_value = "ceramica" WHERE condition_value = "ceramico"')
rows = cursor.rowcount
conn.commit()
conn.close()
print(f'Atualizadas {rows} regras de seleção')
