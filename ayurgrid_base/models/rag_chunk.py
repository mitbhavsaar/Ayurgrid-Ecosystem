from odoo import models, fields, api

class RagChunk(models.Model):
    _name = 'ag.rag.chunk'
    _description = 'AyurGrid RAG Document Chunk'
    _order = 'sequence, id'

    document_id = fields.Many2one('ag.rag.document', string='Document', ondelete='cascade', required=True)
    chunk_text = fields.Text(string='Chunk Text', required=True)
    embedding_vector = fields.Text(string='Embedding Vector')
    token_count = fields.Integer(string='Token Count')
    sequence = fields.Integer(string='Sequence', default=0)
    state = fields.Selection([
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed')
    ], string='Status', default='pending')
    error_message = fields.Text(string='Error Message')

    def init(self):
        super(RagChunk, self).init()
        # Check if the column is already vector type
        self.env.cr.execute("""
            SELECT format_type(atttypid, atttypmod) 
            FROM pg_attribute 
            WHERE attrelid = 'ag_rag_chunk'::regclass AND attname = 'embedding_vector';
        """)
        res = self.env.cr.fetchone()
        if res and 'vector' not in res[0]:
            try:
                # Install pgvector extension
                self.env.cr.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                # Alter column to vector
                self.env.cr.execute("""
                    ALTER TABLE ag_rag_chunk 
                    ALTER COLUMN embedding_vector TYPE vector USING embedding_vector::vector;
                """)
                self.env.cr.commit()
            except Exception:
                self.env.cr.rollback()
        # Build HNSW index if it is a vector column and index doesn't exist
        # Wait, the index build is done dynamically with dimension since pgvector needs dimension for indexes.
        # We will handle HNSW index optimization in refresh_vector_index.
