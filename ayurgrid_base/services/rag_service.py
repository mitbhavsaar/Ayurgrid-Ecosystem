import os
import json
import time
import subprocess
import requests
from odoo.exceptions import UserError

def get_rag_service(env):
    return RAGService(env)

class RAGService:
    def __init__(self, env):
        self.env = env

    def _get_active_config(self):
        config = self.env['ag.ai.configuration'].search([('ai_enabled', '=', True)], limit=1)
        if not config:
            raise UserError("No active AI configuration found. Please enable and configure AI under Admin Setup -> AI Configuration.")
        return config

    def load_knowledge_base(self):
        kb_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'knowledge-base')
        
        # 1. Run Node script to export TS files to JSON
        export_script = os.path.join(kb_path, 'export_ts_to_json.js')
        if os.path.exists(export_script):
            try:
                subprocess.run(
                    ["npx", "-y", "tsx", "export_ts_to_json.js"],
                    cwd=kb_path,
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=30
                )
            except Exception as e:
                # Log warning but continue with existing JSON files
                pass

        # 2. Recursively find JSON and MD files
        json_files = []
        md_files = []
        
        # Directories to exclude from raw scans
        exclude_dirs = {'cache', 'articles'}
        
        for root, dirs, files in os.walk(kb_path):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, kb_path)
                
                # Exclude raw WhatsApp chat txt files as they are parsed in json
                if file.endswith('.txt') and ('whatsapp-chat' in root or 'case-studies' in root):
                    continue
                    
                if file.endswith('.json'):
                    json_files.append(file_path)
                elif file.endswith('.md'):
                    md_files.append(file_path)

        # Process and upsert documents
        self._import_json_files(json_files, kb_path)
        self._import_md_files(md_files, kb_path)

    def _import_json_files(self, file_paths, kb_path):
        RagDocObj = self.env['ag.rag.document']
        
        # Load all existing documents to avoid N+1 queries
        existing_data = RagDocObj.search_read([('source_type', '=', 'json')], ['source_file', 'name', 'content'])
        existing_map = {(d['source_file'], d['name']): d for d in existing_data}
        
        to_create = []
        for file_path in file_paths:
            rel_file = os.path.relpath(file_path, kb_path)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                docs = []
                if isinstance(data, list):
                    for idx, item in enumerate(data):
                        if isinstance(item, dict):
                            name = item.get('name') or item.get('title') or item.get('id') or item.get('diseaseName') or item.get('scientificName') or item.get('medicineName')
                            if not name:
                                name = f"{os.path.basename(file_path)} #{idx+1}"
                            
                            content_lines = []
                            for k, v in item.items():
                                if v is not None:
                                    if isinstance(v, list):
                                        content_lines.append(f"{k.capitalize()}: {', '.join(map(str, v))}")
                                    elif isinstance(v, dict):
                                        content_lines.append(f"{k.capitalize()}: {json.dumps(v)}")
                                    else:
                                        content_lines.append(f"{k.capitalize()}: {v}")
                            
                            content = "\n".join(content_lines)
                            metadata = json.dumps({
                                'source_file': rel_file,
                                'index': idx,
                                'keys': list(item.keys())
                            })
                            docs.append({'name': name, 'content': content, 'metadata': metadata})
                elif isinstance(data, dict):
                    # Check if nested object
                    is_nested = any(isinstance(v, (dict, list)) for v in data.values())
                    if is_nested:
                        for key, val in data.items():
                            name = f"{os.path.basename(file_path)} -> {key}"
                            content = json.dumps(val, indent=2) if isinstance(val, (dict, list)) else str(val)
                            metadata = json.dumps({'source_file': rel_file, 'key': key})
                            docs.append({'name': name, 'content': content, 'metadata': metadata})
                    else:
                        name = os.path.basename(file_path)
                        content = "\n".join(f"{k}: {v}" for k, v in data.items())
                        metadata = json.dumps({'source_file': rel_file})
                        docs.append({'name': name, 'content': content, 'metadata': metadata})

                # Check and upsert
                for doc in docs:
                    key = (rel_file, doc['name'])
                    if key in existing_map:
                        existing = existing_map[key]
                        if existing['content'] != doc['content']:
                            RagDocObj.browse(existing['id']).write({
                                'content': doc['content'],
                                'metadata': doc['metadata'],
                                'state': 'draft'
                            })
                    else:
                        to_create.append({
                            'name': doc['name'],
                            'source_type': 'json',
                            'source_file': rel_file,
                            'content': doc['content'],
                            'metadata': doc['metadata'],
                            'state': 'draft'
                        })
            except Exception as e:
                # Log import failure
                to_create.append({
                    'name': f"FAILED: {os.path.basename(file_path)}",
                    'source_type': 'json',
                    'source_file': rel_file,
                    'content': '',
                    'metadata': '{}',
                    'state': 'failed',
                    'error_message': str(e)
                })
        
        # Batch create all new documents in chunks of 100
        if to_create:
            for idx in range(0, len(to_create), 100):
                RagDocObj.create(to_create[idx:idx+100])

    def _import_md_files(self, file_paths, kb_path):
        RagDocObj = self.env['ag.rag.document']
        
        # Load all existing documents to avoid N+1 queries
        existing_data = RagDocObj.search_read([('source_type', '=', 'md')], ['source_file', 'name', 'content'])
        existing_map = {(d['source_file'], d['name']): d for d in existing_data}
        
        to_create = []
        for file_path in file_paths:
            rel_file = os.path.relpath(file_path, kb_path)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                name = os.path.basename(file_path)
                key = (rel_file, name)
                if key in existing_map:
                    existing = existing_map[key]
                    if existing['content'] != content:
                        RagDocObj.browse(existing['id']).write({
                            'content': content,
                            'metadata': json.dumps({'source_file': rel_file}),
                            'state': 'draft'
                        })
                else:
                    to_create.append({
                        'name': name,
                        'source_type': 'md',
                        'source_file': rel_file,
                        'content': content,
                        'metadata': json.dumps({'source_file': rel_file}),
                        'state': 'draft'
                    })
            except Exception as e:
                to_create.append({
                    'name': f"FAILED: {name}",
                    'source_type': 'md',
                    'source_file': rel_file,
                    'content': '',
                    'metadata': '{}',
                    'state': 'failed',
                    'error_message': str(e)
                })
                
        # Batch create all new documents in chunks of 100
        if to_create:
            for idx in range(0, len(to_create), 100):
                RagDocObj.create(to_create[idx:idx+100])

    def rebuild_embeddings(self, doc_ids=None):
        config = self._get_active_config()
        RagDocObj = self.env['ag.rag.document']
        domain = [('active', '=', True)]
        if doc_ids:
            domain.append(('id', 'in', doc_ids))
        
        docs = RagDocObj.search(domain)
        for doc in docs:
            # Delete old chunks
            doc.chunk_ids.unlink()
            
            try:
                # 1. Chunk document content
                chunks_text = self._split_text(doc.content, config.chunk_size or 500, config.chunk_overlap or 100)
                
                # Create draft chunk records
                chunk_records = []
                for seq, text in enumerate(chunks_text):
                    # Simple token count estimation (1 word = 1.3 tokens)
                    token_est = int(len(text.split()) * 1.3)
                    chunk_rec = self.env['ag.rag.chunk'].create({
                        'document_id': doc.id,
                        'chunk_text': text,
                        'token_count': token_est,
                        'sequence': seq,
                        'state': 'pending'
                    })
                    chunk_records.append(chunk_rec)
                
                # 2. Generate embeddings in batches of 50
                batch_size = 50
                for idx in range(0, len(chunk_records), batch_size):
                    batch = chunk_records[idx:idx+batch_size]
                    texts = [c.chunk_text for c in batch]
                    try:
                        vectors = self._fetch_embeddings(texts, config)
                        for chunk, vector in zip(batch, vectors):
                            chunk.write({
                                'embedding_vector': str(vector),
                                'state': 'completed',
                                'error_message': False
                            })
                    except Exception as embed_err:
                        for chunk in batch:
                            chunk.write({
                                'state': 'failed',
                                'error_message': str(embed_err)
                            })
                doc.write({'state': 'processed', 'error_message': False})
            except Exception as doc_err:
                doc.write({'state': 'failed', 'error_message': str(doc_err)})

    def _split_text(self, text, chunk_size, chunk_overlap):
        if not text:
            return []
            
        try:
            import tiktoken
            encoding = tiktoken.get_encoding("cl100k_base")
            tokenize = lambda t: encoding.encode(t)
            detokenize = lambda tokens: encoding.decode(tokens)
        except ImportError:
            tokenize = lambda t: t.split()
            detokenize = lambda tokens: " ".join(tokens)
            # Scale word count based on 0.75 words per token
            chunk_size = int(chunk_size * 0.75)
            chunk_overlap = int(chunk_overlap * 0.75)
            
        tokens = tokenize(text)
        total_tokens = len(tokens)
        chunks = []
        
        if total_tokens <= chunk_size:
            return [text]
            
        start = 0
        while start < total_tokens:
            end = min(start + chunk_size, total_tokens)
            chunk_tokens = tokens[start:end]
            chunks.append(detokenize(chunk_tokens))
            start += (chunk_size - chunk_overlap)
            if start >= total_tokens or end == total_tokens:
                break
                
        return chunks

    def _fetch_embeddings(self, texts, config):
        if not config.api_key:
            raise UserError("API Key is missing in AI Configuration.")
            
        api_key_clean = config.api_key.strip()
        provider = config.embedding_provider or 'nvidia'
        model = config.embedding_model_name or 'nvidia/llama-3.2-nv-embedqp-1b-v1'
        
        if provider == 'openai':
            url = "https://api.openai.com/v1/embeddings"
            headers = {
                "Authorization": f"Bearer {api_key_clean}",
                "Content-Type": "application/json"
            }
            payload = {
                "input": texts,
                "model": model or "text-embedding-3-small"
            }
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            return [item['embedding'] for item in data['data']]
            
        elif provider == 'nvidia':
            url = "https://integrate.api.nvidia.com/v1/embeddings"
            headers = {
                "Authorization": f"Bearer {api_key_clean}",
                "Content-Type": "application/json"
            }
            payload = {
                "input": texts,
                "model": model,
                "input_type": "passage",
                "encoding_format": "float"
            }
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            return [item['embedding'] for item in data['data']]
            
        elif provider == 'huggingface':
            # Hugging Face Inference API
            url = f"https://api-inference.huggingface.co/pipeline/feature-extraction/{model}"
            headers = {
                "Authorization": f"Bearer {api_key_clean}",
                "Content-Type": "application/json"
            }
            payload = {
                "inputs": texts,
                "options": {"wait_for_model": True}
            }
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            return response.json()
            
        else:
            raise UserError(f"Unsupported embedding provider: {provider}")

    def refresh_vector_index(self):
        # Sample one completed chunk to get dimension
        self.env.cr.execute("SELECT embedding_vector FROM ag_rag_chunk WHERE state = 'completed' LIMIT 1;")
        res = self.env.cr.fetchone()
        if not res:
            raise UserError("No completed embeddings found. Please build embeddings first before refreshing the index.")
            
        # Parse vector string '[0.1, 0.2, ...]'
        vec_str = res[0]
        try:
            dim = len(json.loads(vec_str))
        except Exception:
            dim = len(vec_str.strip('[]').split(','))
            
        # Re-cast column to specify the fixed dimension and build HNSW index
        self.env.cr.execute("DROP INDEX IF EXISTS ag_rag_chunk_vector_idx;")
        self.env.cr.execute(f"ALTER TABLE ag_rag_chunk ALTER COLUMN embedding_vector TYPE vector({dim}) USING embedding_vector::vector({dim});")
        self.env.cr.execute("CREATE INDEX IF NOT EXISTS ag_rag_chunk_vector_idx ON ag_rag_chunk USING hnsw (embedding_vector vector_cosine_ops);")
        self.env.cr.commit()

    def similarity_search(self, query_text, limit=None, threshold=None):
        config = self._get_active_config()
        if not limit:
            limit = config.top_k_results or 5
        if not threshold:
            threshold = config.similarity_threshold or 0.7
            
        # 1. Fetch embedding vector for the query text
        query_vecs = self._fetch_embeddings([query_text], config)
        if not query_vecs:
            return []
        query_vec = query_vecs[0]
        query_vec_str = str(query_vec)
        
        # 2. Calculate postgres Cosine distance threshold: distance = 1 - similarity
        distance_threshold = 1.0 - threshold
        
        # 3. Query PostgreSQL using raw SQL (standard Odoo ORM doesn't support vector distance operations)
        self.env.cr.execute("""
            SELECT c.id, c.chunk_text, c.token_count, d.name as doc_name, d.source_file, (c.embedding_vector <=> %s) AS distance
            FROM ag_rag_chunk c
            JOIN ag_rag_document d ON c.document_id = d.id
            WHERE d.active = true 
              AND c.state = 'completed'
              AND (c.embedding_vector <=> %s) <= %s
            ORDER BY c.embedding_vector <=> %s
            LIMIT %s
        """, (query_vec_str, query_vec_str, distance_threshold, query_vec_str, limit))
        
        results = []
        for row in self.env.cr.fetchall():
            results.append({
                'id': row[0],
                'text': row[1],
                'token_count': row[2],
                'doc_name': row[3],
                'source_file': row[4],
                'similarity': round(1.0 - row[5], 4)
            })
        return results

    def generate_response(self, query_text):
        config = self._get_active_config()
        
        # 1. Similarity search
        chunks = []
        if config.rag_enabled:
            try:
                chunks = self.similarity_search(query_text)
            except Exception:
                # If similarity search fails (e.g. index/extension issue), fall back to direct query without RAG context
                pass
                
        # 2. Build system/user prompts
        context_str = ""
        for idx, chunk in enumerate(chunks):
            context_str += f"--- Source Document: {chunk['doc_name']} ---\n{chunk['text']}\n\n"
            
        system_prompt = (
            "You are AyurGrid, an expert Ayurvedic clinical assistant. "
            "Use the provided Ayurvedic internal knowledge base context to answer the clinical questions. "
            "Prioritize using the internal knowledge base details (herbs, formulations, diagnoses, treatments) over generic training information. "
            "If the context does not contain relevant information, clearly state that and provide a standard Ayurvedic answer based on classical texts, while keeping it accurate. "
            "Output your response formatted in professional HTML layout. Include sections for: Possible Diagnosis, Recommended Herbs, Classical Formulations, and Treatment & Lifestyle Guidance."
        )
        
        user_prompt = f"Patient Query / Symptoms:\n{query_text}\n\n"
        if context_str:
            user_prompt += f"Trusted Ayurvedic Knowledge Base Context:\n{context_str}\n"
            
        # 3. Query LLM Chat Completion
        api_key_clean = config.api_key.strip()
        provider = config.provider or 'nvidia'
        model = config.model_name or 'meta/llama-3.1-8b-instruct'
        temp = config.temperature or 0.7
        max_tokens = config.max_tokens or 1000
        
        if provider == 'openai':
            url = "https://api.openai.com/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {api_key_clean}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": temp,
                "max_tokens": max_tokens
            }
            response = requests.post(url, json=payload, headers=headers, timeout=45)
            response.raise_for_status()
            res_data = response.json()
            ans_text = res_data['choices'][0]['message']['content']
            
        elif provider == 'nvidia':
            url = "https://integrate.api.nvidia.com/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {api_key_clean}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": temp,
                "max_tokens": max_tokens
            }
            response = requests.post(url, json=payload, headers=headers, timeout=45)
            response.raise_for_status()
            res_data = response.json()
            ans_text = res_data['choices'][0]['message']['content']
            
        else:
            raise UserError(f"Unsupported chat provider for query completions: {provider}")
            
        return {
            'response': ans_text,
            'chunks': chunks
        }

    def query_llm_json(self, system_prompt, user_prompt):
        config = self._get_active_config()
        if not config.api_key:
            raise UserError("API Key is missing in AI Configuration.")
            
        api_key_clean = config.api_key.strip()
        provider = config.provider or 'nvidia'
        model = config.model_name or 'meta/llama-3.1-8b-instruct'
        temp = 0.2
        max_tokens = config.max_tokens or 1500
        
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": temp,
            "max_tokens": max_tokens
        }
        
        if provider == 'openai':
            url = "https://api.openai.com/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {api_key_clean}",
                "Content-Type": "application/json"
            }
            if 'gpt-4' in model or 'gpt-3.5' in model or 'gpt-4o' in model:
                payload["response_format"] = {"type": "json_object"}
        elif provider == 'nvidia':
            url = "https://integrate.api.nvidia.com/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {api_key_clean}",
                "Content-Type": "application/json"
            }
        else:
            raise UserError(f"Unsupported chat provider: {provider}")
            
        response = requests.post(url, json=payload, headers=headers, timeout=45)
        response.raise_for_status()
        res_data = response.json()
        ans_text = res_data['choices'][0]['message']['content'].strip()
        
        # Clean markdown code block wraps if present
        if ans_text.startswith('```json'):
            ans_text = ans_text[7:-3]
        elif ans_text.startswith('```'):
            ans_text = ans_text[3:-3]
        ans_text = ans_text.strip()
        
        try:
            return json.loads(ans_text)
        except Exception as e:
            raise UserError(f"Failed to parse JSON response from LLM. Raw output: {ans_text}. Error: {str(e)}")
