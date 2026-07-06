from odoo import models, fields, api

class RagDocument(models.Model):
    _name = 'ag.rag.document'
    _description = 'AyurGrid RAG Document'

    name = fields.Char(string='Name', required=True)
    source_type = fields.Selection([
        ('json', 'JSON'),
        ('txt', 'TXT'),
        ('md', 'Markdown'),
        ('ts', 'TypeScript')
    ], string='Source Type')
    source_file = fields.Char(string='Source File')
    content = fields.Text(string='Content')
    metadata = fields.Text(string='Metadata')
    active = fields.Boolean(string='Active', default=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('processed', 'Processed'),
        ('failed', 'Failed')
    ], string='State', default='draft')
    error_message = fields.Text(string='Error Message')

    chunk_ids = fields.One2many('ag.rag.chunk', 'document_id', string='Chunks')
    chunk_count = fields.Integer(string='Chunk Count', compute='_compute_chunk_count')

    @api.depends('chunk_ids')
    def _compute_chunk_count(self):
        for rec in self:
            rec.chunk_count = len(rec.chunk_ids)

    def action_import_knowledge_base(self):
        from ..services.rag_service import get_rag_service
        service = get_rag_service(self.env)
        service.load_knowledge_base()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Knowledge Base',
                'message': 'Knowledge base files scanned and imported successfully.',
                'type': 'success',
                'sticky': False,
            }
        }

    def action_rebuild_embeddings(self):
        from ..services.rag_service import get_rag_service
        service = get_rag_service(self.env)
        # Pass empty list to rebuild all documents
        service.rebuild_embeddings(self.ids)
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'RAG Embeddings',
                'message': 'RAG chunks and embeddings rebuild triggered.',
                'type': 'success',
                'sticky': False,
            }
        }

    def action_refresh_vector_index(self):
        from ..services.rag_service import get_rag_service
        service = get_rag_service(self.env)
        service.refresh_vector_index()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Vector Index',
                'message': 'Vector search index refreshed and optimized.',
                'type': 'success',
                'sticky': False,
            }
        }
