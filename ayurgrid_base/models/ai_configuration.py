from odoo import api, fields, models
from odoo.exceptions import UserError
import requests

class AIConfiguration(models.Model):
    _name = 'ag.ai.configuration'
    _description = 'AI Configuration'

    name = fields.Char(string='Configuration Name', required=True, default='Main AI Config')
    ai_enabled = fields.Boolean(string='AI Enabled', default=True)
    provider = fields.Selection([
        ('nvidia', 'NVIDIA'),
        ('openai', 'OpenAI'),
        ('anthropic', 'Anthropic'),
        ('ollama', 'Ollama'),
        ('openrouter', 'OpenRouter'),
        ('azure', 'Azure')
    ], string='Provider', default='nvidia')
    api_key = fields.Char(string='API Key')
    model_name = fields.Char(string='Model Name', default='meta/llama-3.1-8b-instruct')
    temperature = fields.Float(string='Temperature', default=0.7)
    max_tokens = fields.Integer(string='Max Tokens', default=1000)
    embedding_provider = fields.Selection([
        ('nvidia', 'NVIDIA'),
        ('openai', 'OpenAI'),
        ('huggingface', 'HuggingFace')
    ], string='Embedding Provider', default='nvidia')
    embedding_model_name = fields.Char(string='Embedding Model Name', default='nvidia/llama-3.2-nv-embedqp-1b-v1')
    vector_db = fields.Selection([
        ('pinecone', 'Pinecone'),
        ('milvus', 'Milvus'),
        ('qdrant', 'Qdrant'),
        ('pgvector', 'pgvector')
    ], string='Vector DB', default='pgvector')
    rag_enabled = fields.Boolean(string='RAG Enabled', default=True)
    
    # RAG parameters
    chunk_size = fields.Integer(string='Chunk Size (tokens)', default=500, help='Maximum size of each chunk in tokens')
    chunk_overlap = fields.Integer(string='Chunk Overlap (tokens)', default=100, help='Overlap size between consecutive chunks')
    top_k_results = fields.Integer(string='Top K Results', default=5, help='Number of top matching chunks to retrieve')
    similarity_threshold = fields.Float(string='Similarity Threshold', default=0.7, help='Minimum similarity score (0.0 to 1.0) to retrieve a chunk')
    max_context_tokens = fields.Integer(string='Max Context Tokens', default=4000, help='Maximum allowed tokens for retrieved context in the prompt')

    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)

    def action_test_connection(self):
        self.ensure_one()
        if not self.api_key:
            raise UserError('Please enter an API Key first.')
        
        api_key_clean = self.api_key.strip()
        
        if self.provider == 'nvidia':
            url = "https://integrate.api.nvidia.com/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {api_key_clean}",
                "Content-Type": "application/json"
            }
            model = self.model_name.strip() if self.model_name else "meta/llama-3.1-8b-instruct"
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": "Ping!"}],
                "max_tokens": 10
            }
            
            try:
                response = requests.post(url, headers=headers, json=payload, timeout=10)
                if response.status_code == 200:
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': 'Connection Successful',
                            'message': f'Successfully connected to NVIDIA API using model: {model}',
                            'type': 'success',
                            'sticky': False,
                        }
                    }
                else:
                    raise UserError(f'Connection failed! Status: {response.status_code}\nResponse: {response.text}')
            except Exception as e:
                raise UserError(f'Connection error: {str(e)}')
        elif self.provider == 'openai':
            url = "https://api.openai.com/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {api_key_clean}",
                "Content-Type": "application/json"
            }
            model = self.model_name.strip() if self.model_name else "gpt-4o-mini"
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": "Ping!"}],
                "max_tokens": 10
            }
            
            try:
                response = requests.post(url, headers=headers, json=payload, timeout=10)
                if response.status_code == 200:
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': 'Connection Successful',
                            'message': f'Successfully connected to OpenAI API using model: {model}',
                            'type': 'success',
                            'sticky': False,
                        }
                    }
                else:
                    raise UserError(f'Connection failed! Status: {response.status_code}\nResponse: {response.text}')
            except Exception as e:
                raise UserError(f'Connection error: {str(e)}')
        else:
            raise UserError('Test connection is currently only implemented for the NVIDIA and OpenAI providers.')
