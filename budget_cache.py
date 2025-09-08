import os
import json
import uuid
from datetime import datetime, timedelta

class BudgetCache:
    """Cache server-side para orçamentos grandes"""
    
    def __init__(self, cache_dir="cache"):
        self.cache_dir = cache_dir
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
    
    def store_budget(self, budget_data):
        """Armazena um orçamento e retorna um ID único"""
        cache_id = str(uuid.uuid4())
        cache_file = os.path.join(self.cache_dir, f"budget_{cache_id}.json")
        
        # Adicionar timestamp para limpeza automática
        cache_data = {
            'timestamp': datetime.now().isoformat(),
            'budget': budget_data
        }
        
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
        
        return cache_id
    
    def get_budget(self, cache_id):
        """Recupera um orçamento pelo ID"""
        cache_file = os.path.join(self.cache_dir, f"budget_{cache_id}.json")
        
        if not os.path.exists(cache_file):
            return None
        
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            # Verificar se não expirou (ex: 24 horas)
            timestamp = datetime.fromisoformat(cache_data['timestamp'])
            if datetime.now() - timestamp > timedelta(hours=24):
                os.remove(cache_file)
                return None
            
            return cache_data['budget']
        except Exception:
            return None
    
    def update_budget(self, cache_id, budget_data):
        """Atualiza um orçamento existente"""
        cache_file = os.path.join(self.cache_dir, f"budget_{cache_id}.json")
        
        cache_data = {
            'timestamp': datetime.now().isoformat(),
            'budget': budget_data
        }
        
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
    
    def cleanup_expired(self):
        """Remove arquivos de cache expirados"""
        for filename in os.listdir(self.cache_dir):
            if filename.startswith('budget_') and filename.endswith('.json'):
                filepath = os.path.join(self.cache_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        cache_data = json.load(f)
                    
                    timestamp = datetime.fromisoformat(cache_data['timestamp'])
                    if datetime.now() - timestamp > timedelta(hours=24):
                        os.remove(filepath)
                except Exception:
                    # Arquivo corrompido, remover
                    os.remove(filepath)

# Instância global
budget_cache = BudgetCache()
