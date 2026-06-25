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
    api_key = fields.Char(string='API Key', default='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')
    model_name = fields.Char(string='Model Name', default='meta/llama-3.1-8b-instruct')
    temperature = fields.Float(string='Temperature', default=0.7)
    max_tokens = fields.Integer(string='Max Tokens', default=1000)
    embedding_provider = fields.Selection([
        ('nvidia', 'NVIDIA'),
        ('openai', 'OpenAI'),
        ('huggingface', 'HuggingFace')
    ], string='Embedding Provider')
    vector_db = fields.Selection([
        ('pinecone', 'Pinecone'),
        ('milvus', 'Milvus'),
        ('qdrant', 'Qdrant'),
        ('pgvector', 'pgvector')
    ], string='Vector DB')
    rag_enabled = fields.Boolean(string='RAG Enabled')
    
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
            # Use a fallback model if none provided
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
        else:
            raise UserError('Test connection is currently only implemented for the NVIDIA provider.')
