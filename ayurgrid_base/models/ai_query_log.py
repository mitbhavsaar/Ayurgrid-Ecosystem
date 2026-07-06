import time
import re
from odoo import models, fields, api

def convert_markdown_to_html(text):
    if not text:
        return ""
    
    # 1. Normalize spacing and inline elements into separate lines
    # Put newlines before bold titles (like **Title:** or **Title**)
    text = re.sub(r'\s*(\*\*[^*]+?\*\*:?)', r'\n\1', text)
    
    # Handle direct transition from bold to bullet (e.g. *** -> **\n* )
    text = re.sub(r'\*\*\*(?!\*)', r'**\n* ', text)
    
    # Put newlines before bullet items (like * Item)
    text = re.sub(r'\s*(?<!\*)\*(?!\*)\s+', r'\n* ', text)
    
    # Put newlines before numbered list items (like 1. Item)
    text = re.sub(r'\s+(\d+)\.\s+', r'\n\1. ', text)
    
    # Split text into lines
    lines = text.strip().split('\n')
    html_lines = []
    
    in_list = False
    list_type = None  # 'ul' or 'ol'
    
    for line in lines:
        line_stripped = line.strip()
        if not line_stripped:
            continue
            
        # Parse bold and italic first
        # Replace **bold** with <strong>bold</strong>
        line_processed = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', line_stripped)
        # Replace *italic* with <em>italic</em>
        line_processed = re.sub(r'\*(.*?)\*', r'<em>\1</em>', line_processed)
        
        # Check for bullet points starting with * or -
        bullet_match = re.match(r'^[\*\-]\s+(.*)', line_processed)
        # Check for numbered points starting with digit.
        numbered_match = re.match(r'^(\d+)\.\s+(.*)', line_processed)
        
        if bullet_match:
            content = bullet_match.group(1)
            if not in_list or list_type != 'ul':
                if in_list:
                    html_lines.append(f"</{list_type}>")
                html_lines.append("<ul style='margin-bottom: 8px; padding-left: 20px; list-style-type: disc;'>")
                in_list = True
                list_type = 'ul'
            html_lines.append(f"<li style='margin-bottom: 4px;'>{content}</li>")
        elif numbered_match:
            content = numbered_match.group(2)
            if not in_list or list_type != 'ol':
                if in_list:
                    html_lines.append(f"</{list_type}>")
                html_lines.append("<ol style='margin-bottom: 8px; padding-left: 20px;'>")
                in_list = True
                list_type = 'ol'
            html_lines.append(f"<li style='margin-bottom: 4px;'>{content}</li>")
        else:
            # If we were in a list, close it
            if in_list:
                html_lines.append(f"</{list_type}>")
                in_list = False
                list_type = None
                
            # Check if this line is a heading
            if line_processed.startswith('<strong>') and line_processed.endswith('</strong>'):
                html_lines.append(f"<h4 style='color: #2c3e50; margin-top: 16px; margin-bottom: 8px; border-bottom: 1px solid #eee; padding-bottom: 4px;'>{line_processed}</h4>")
            elif line_processed.startswith('<strong>') and line_processed.endswith('</strong>:'):
                content = line_processed[:-1]
                html_lines.append(f"<h4 style='color: #2c3e50; margin-top: 16px; margin-bottom: 8px; border-bottom: 1px solid #eee; padding-bottom: 4px;'>{content}</h4>")
            else:
                # Normal paragraph
                html_lines.append(f"<p style='margin-bottom: 8px; line-height: 1.5;'>{line_processed}</p>")
                
    if in_list:
        html_lines.append(f"</{list_type}>")
        
    return "\n".join(html_lines)

class AIQueryLog(models.Model):
    _name = 'ag.ai.query.log'
    _description = 'AyurGrid AI Query Log'
    _rec_name = 'query'
    _order = 'create_date desc'

    patient_id = fields.Many2one('ag.patient', string='Patient')
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user, readonly=True)
    query = fields.Text(string='Symptoms / Query', required=True)
    retrieved_chunks = fields.Text(string='Retrieved Context', readonly=True)
    response = fields.Html(string='AI Response', readonly=True)
    response_time = fields.Float(string='Response Time (seconds)', readonly=True)
    status = fields.Selection([
        ('success', 'Success'),
        ('failed', 'Failed')
    ], string='Status', readonly=True, default='success')

    def action_run_query(self):
        self.ensure_one()
        from ..services.rag_service import get_rag_service
        service = get_rag_service(self.env)
        
        start_time = time.time()
        try:
            res_dict = service.generate_response(self.query)
            end_time = time.time()
            
            chunks_text = ""
            for i, chunk in enumerate(res_dict.get('chunks', [])):
                chunks_text += f"[{i+1}] Source: {chunk.get('doc_name')} ({chunk.get('source_file')})\n"
                chunks_text += f"Content: {chunk.get('text')}\n\n"
                
            formatted_response = convert_markdown_to_html(res_dict.get('response', 'No response generated.'))
            self.write({
                'retrieved_chunks': chunks_text or "No matching context found.",
                'response': formatted_response,
                'response_time': round(end_time - start_time, 2),
                'status': 'success'
            })
        except Exception as e:
            end_time = time.time()
            self.write({
                'response': f"<p style='color:red;'>Error generating response: {str(e)}</p>",
                'response_time': round(end_time - start_time, 2),
                'status': 'failed'
            })
        return True
