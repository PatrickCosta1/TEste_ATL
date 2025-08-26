import requests
import json

def test_alternatives():
    base_url = "http://127.0.0.1:5000"
    
    # Testar alternativas para um produto da família recirculação
    print("=== TESTANDO ALTERNATIVAS PARA PRODUTOS DE RECIRCULAÇÃO ===")
    
    # Produtos de teste da família recirculação
    test_cases = [
        ("recirculacao", "skimmer_33"),  # Skimmer
        ("recirculacao", "boca_impulsao_43"),  # Boca de Impulsão
        ("recirculacao", "ralo_fundo_60"),  # Ralo de Fundo
        ("recirculacao", "iluminacao_65"),  # Iluminação
    ]
    
    for family, product_id in test_cases:
        print(f"\n--- Testando {family}/{product_id} ---")
        
        url = f"{base_url}/get_alternatives/{family}/{product_id}"
        
        try:
            response = requests.get(url, timeout=5)
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Success: {data.get('success', 'N/A')}")
                
                if data.get('success'):
                    current = data.get('current_product', {})
                    alternatives = data.get('alternatives', [])
                    
                    print(f"Produto atual: {current.get('name', 'N/A')} (ID: {current.get('id', 'N/A')})")
                    print(f"Alternativas encontradas: {len(alternatives)}")
                    
                    for i, alt in enumerate(alternatives[:3], 1):  # Mostrar apenas as primeiras 3
                        print(f"  {i}. {alt.get('name', 'N/A')} (ID: {alt.get('id', 'N/A')}) - €{alt.get('price', 0):.2f}")
                        
                    if len(alternatives) > 3:
                        print(f"  ... e mais {len(alternatives) - 3} alternativas")
                else:
                    print(f"Erro: {data.get('error', 'Erro desconhecido')}")
            else:
                print(f"Erro HTTP: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"Erro de conexão: {e}")
        except Exception as e:
            print(f"Erro: {e}")

if __name__ == "__main__":
    test_alternatives()
