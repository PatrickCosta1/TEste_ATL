import json
from app import app

def test_add_alternative_flow():
    client = app.test_client()

    # Simular um budget simples na sessão
    with client.session_transaction() as sess:
        sess['current_budget'] = {
            'families': {
                'filtracao': {
                    'filter_1': {
                        'id': 1,
                        'name': 'Filtro X',
                        'price': 100,
                        'quantity': 1,
                        'item_type': 'incluido'
                    }
                }
            }
        }

    # Adicionar manualmente um alternativo referenciando '1'
    payload = {
        'product_id': '200',
        'item_type': 'alternativo',
        'alternative_to': '1'
    }

    resp = client.post('/add_product', data=json.dumps(payload), content_type='application/json')
    data = resp.get_json()
    assert resp.status_code == 200
    assert data['success'] is True
