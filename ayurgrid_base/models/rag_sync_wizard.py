from odoo import models, fields, api
from odoo.exceptions import UserError

class RAGSyncWizard(models.TransientModel):
    _name = 'ag.rag.sync.wizard'
    _description = 'Knowledge Base Synchronizer'

    import_files = fields.Boolean(string='Scan & Import Files', default=True,
                                  help='Scan knowledge base folder and import markdown and JSON files.')
    rebuild_embeddings = fields.Boolean(string='Generate Chunks & Embeddings', default=True,
                                        help='Divide document content into chunks and generate vector embeddings.')
    limit_docs = fields.Integer(string='Limit Documents to Embed', default=20,
                               help='Number of draft/failed documents to process in this run to avoid rate limits or HTTP timeouts. Set to 0 to process all.')
    optimize_index = fields.Boolean(string='Optimize Vector Index', default=True,
                                    help='Rebuild/refresh pgvector index for fast search.')

    def action_sync(self):
        self.ensure_one()
        from ..services.rag_service import get_rag_service
        service = get_rag_service(self.env)

        # 1. Scan and Import Files
        if self.import_files:
            service.load_knowledge_base()

        # 2. Generate Embeddings
        if self.rebuild_embeddings:
            domain = [('active', '=', True)]
            if self.limit_docs > 0:
                domain.append(('state', 'in', ['draft', 'failed']))
                docs = self.env['ag.rag.document'].search(domain, limit=self.limit_docs)
            else:
                docs = self.env['ag.rag.document'].search(domain)

            if docs:
                service.rebuild_embeddings(docs.ids)

        # 3. Optimize Vector Index
        if self.optimize_index:
            try:
                service.refresh_vector_index()
            except UserError:
                # Silently ignore if no chunks are completed yet
                pass

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Sync Completed',
                'message': 'RAG Knowledge Base sync completed successfully.',
                'type': 'success',
                'sticky': False,
            }
        }
