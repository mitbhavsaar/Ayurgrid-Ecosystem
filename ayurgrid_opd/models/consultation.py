from odoo import api, fields, models
from odoo.tools import html2plaintext

class OPDConsultation(models.Model):
    _name = 'ag.opd.consultation'
    _description = 'OPD Consultation'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Consultation ID', required=True, copy=False, readonly=True, default='New')
    appointment_id = fields.Many2one('ag.opd.appointment', string='Appointment')
    patient_id = fields.Many2one('ag.patient', string='Patient', required=True)
    doctor_id = fields.Many2one('res.users', string='Doctor', required=True)
    consultation_date = fields.Datetime(string='Date', required=True, default=fields.Datetime.now)
    
    consultation_type = fields.Selection([
        ('new', 'New'),
        ('follow_up', 'Follow-Up'),
        ('review', 'Review'),
        ('emergency', 'Emergency'),
        ('teleconsult', 'Teleconsult')
    ], string='Consultation Type', required=True, default='new')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled')
    ], string='Status', required=True, default='draft', tracking=True)

    # Vitals
    bp = fields.Char(string='BP')
    pulse = fields.Integer(string='Pulse')
    respiratory_rate = fields.Integer(string='Respiratory Rate')
    spo2 = fields.Integer(string='SpO2 (%)')
    temperature = fields.Float(string='Temperature (F)')
    weight = fields.Float(string='Weight (kg)')
    height = fields.Float(string='Height (cm)')
    bmi = fields.Float(string='BMI', compute='_compute_bmi', store=True)
    waist_circumference = fields.Float(string='Waist Circumference (cm)')

    # Ashtavidha Pariksha
    nadi = fields.Char(string='Nadi')
    mala = fields.Char(string='Mala')
    mutra = fields.Char(string='Mutra')
    jihwa = fields.Char(string='Jihwa')
    shabda = fields.Char(string='Shabda')
    sparsha = fields.Char(string='Sparsha')
    drika = fields.Char(string='Drika')
    akruti = fields.Char(string='Akruti')

    # Dashavidha Pariksha
    prakriti = fields.Char(string='Prakriti')
    vikriti = fields.Char(string='Vikriti')
    sara = fields.Char(string='Sara')
    samhanana = fields.Char(string='Samhanana')
    pramana = fields.Char(string='Pramana')
    satmya = fields.Char(string='Satmya')
    satva = fields.Char(string='Satva')
    ahara_shakti = fields.Char(string='Ahara Shakti')
    vyayama_shakti = fields.Char(string='Vyayama Shakti')
    vaya = fields.Char(string='Vaya')

    # One2many lines
    complaint_ids = fields.One2many('ag.opd.complaint', 'consultation_id', string='Chief Complaints')
    prescription_ids = fields.One2many('ag.opd.prescription.line', 'consultation_id', string='Medicines')
    procedure_advice_ids = fields.One2many('ag.opd.therapy.prescription', 'consultation_id', string='Procedure Advice')

    # Diagnosis
    ayurveda_diagnosis = fields.Text(string='Ayurveda Diagnosis')
    modern_diagnosis = fields.Text(string='Modern Diagnosis')
    samprapti = fields.Text(string='Samprapti')

    @api.depends('weight', 'height')
    def _compute_bmi(self):
        for rec in self:
            if rec.weight and rec.height:
                height_m = rec.height / 100.0
                rec.bmi = rec.weight / (height_m * height_m)
            else:
                rec.bmi = 0.0

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('ag.opd.consultation') or 'New'
        return super(OPDConsultation, self).create(vals_list)

    def action_start(self):
        for rec in self:
            rec.state = 'in_progress'

    def action_done(self):
        for rec in self:
            rec.state = 'done'
            if rec.appointment_id:
                rec.appointment_id.state = 'completed'

    def action_cancel(self):
        for rec in self:
            rec.state = 'cancelled'

    def message_post(self, *, body='', **kwargs):
        msg = super(OPDConsultation, self).message_post(body=body, **kwargs)
        
        # 1. Parse plaintext from HTML body
        plain_text = html2plaintext(body or '').strip()
        if not plain_text:
            return msg
            
        # 2. Check if this message was sent by a user (exclude system logs and bot actions)
        subtype_id = kwargs.get('subtype_id') or msg.subtype_id.id
        comment_subtype = self.env.ref('mail.mt_comment', raise_if_not_found=False)
        note_subtype = self.env.ref('mail.mt_note', raise_if_not_found=False)
        
        allowed_subtypes = []
        if comment_subtype:
            allowed_subtypes.append(comment_subtype.id)
        if note_subtype:
            allowed_subtypes.append(note_subtype.id)
            
        if allowed_subtypes and subtype_id not in allowed_subtypes:
            return msg
            
        # Also avoid infinite loops if the AI posts a message itself
        author_id = kwargs.get('author_id') or msg.author_id.id
        root_partner = self.env.ref('base.partner_root', raise_if_not_found=False)
        if root_partner and author_id == root_partner.id:
            return msg
            
        # Prevent processing system notification messages about record changes
        if plain_text.startswith("AI Auto-Fill"):
            return msg
            
        # 3. Call AI Auto-fill processing
        try:
            self._action_ai_autofill(plain_text)
        except Exception as e:
            # Post a warning back to the chatter instead of breaking message submission
            self.message_post(body=f"<p style='color:red;'>AI Auto-Fill Error: {str(e)}</p>")
            
        return msg

    def _action_ai_autofill(self, message_text):
        self.ensure_one()
        from odoo.addons.ayurgrid_base.services.rag_service import get_rag_service
        service = get_rag_service(self.env)
        
        # 1. Retrieve RAG context matching key terms in message
        rag_context = ""
        try:
            chunks = service.similarity_search(message_text, limit=3, threshold=0.6)
            for idx, chunk in enumerate(chunks):
                rag_context += f"Source: {chunk['doc_name']}\nContent: {chunk['text']}\n\n"
        except Exception:
            pass
            
        # 2. Format current Consultation record fields
        current_state = (
            f"Vitals: bp={self.bp or 'None'}, pulse={self.pulse or 0}, temp={self.temperature or 0.0}, weight={self.weight or 0.0}, height={self.height or 0.0}, respiratory_rate={self.respiratory_rate or 0}, spo2={self.spo2 or 0}, waist_circumference={self.waist_circumference or 0.0}\n"
            f"Ashtavidha Pariksha: nadi={self.nadi or 'None'}, mala={self.mala or 'None'}, mutra={self.mutra or 'None'}, jihwa={self.jihwa or 'None'}, shabda={self.shabda or 'None'}, sparsha={self.sparsha or 'None'}, drika={self.drika or 'None'}, akruti={self.akruti or 'None'}\n"
            f"Dashavidha Pariksha: prakriti={self.prakriti or 'None'}, vikriti={self.vikriti or 'None'}, sara={self.sara or 'None'}, samhanana={self.samhanana or 'None'}, pramana={self.pramana or 'None'}, satmya={self.satmya or 'None'}, satva={self.satva or 'None'}, ahara_shakti={self.ahara_shakti or 'None'}, vyayama_shakti={self.vyayama_shakti or 'None'}, vaya={self.vaya or 'None'}\n"
            f"Chief Complaints: {', '.join([c.sanskrit_term + ' (' + (c.english_term or '') + ')' for c in self.complaint_ids]) or 'None'}\n"
            f"Diagnosis: ayurveda_diagnosis={self.ayurveda_diagnosis or 'None'}, modern_diagnosis={self.modern_diagnosis or 'None'}, samprapti={self.samprapti or 'None'}\n"
            f"Prescription: {', '.join([p.medicine_id.name for p in self.prescription_ids]) or 'None'}\n"
            f"Procedures: {', '.join([pr.procedure_name for pr in self.procedure_advice_ids]) or 'None'}"
        )
        
        # 3. Compile prompt requesting structured JSON
        system_prompt = (
            "You are AyurGrid Clinical Auto-Fill Agent. Your job is to extract clinical metrics, diagnoses, "
            "complaints, prescriptions, and procedures from a doctor's chat message to update a consultation record.\n\n"
            "Here is some trusted Ayurvedic Knowledge Base Context retrieved for search terms in the message:\n"
            f"{rag_context}\n"
            "Below is the current state of the consultation record:\n"
            f"{current_state}\n\n"
            "Parse the new chat message and determine if there are updates. Merge these updates into the current record state.\n"
            "You MUST output ONLY a valid JSON object matching the schema below. No other text, no markdown wrapper.\n\n"
            "JSON Schema:\n"
            "{\n"
            "  \"bp\": string,\n"
            "  \"pulse\": integer,\n"
            "  \"respiratory_rate\": integer,\n"
            "  \"spo2\": integer,\n"
            "  \"temperature\": float,\n"
            "  \"weight\": float,\n"
            "  \"height\": float,\n"
            "  \"waist_circumference\": float,\n"
            "  \"nadi\": string,\n"
            "  \"mala\": string,\n"
            "  \"mutra\": string,\n"
            "  \"jihwa\": string,\n"
            "  \"shabda\": string,\n"
            "  \"sparsha\": string,\n"
            "  \"drika\": string,\n"
            "  \"akruti\": string,\n"
            "  \"prakriti\": string,\n"
            "  \"vikriti\": string,\n"
            "  \"sara\": string,\n"
            "  \"samhanana\": string,\n"
            "  \"pramana\": string,\n"
            "  \"satmya\": string,\n"
            "  \"satva\": string,\n"
            "  \"ahara_shakti\": string,\n"
            "  \"vyayama_shakti\": string,\n"
            "  \"vaya\": string,\n"
            "  \"ayurveda_diagnosis\": string,\n"
            "  \"modern_diagnosis\": string,\n"
            "  \"samprapti\": string,\n"
            "  \"complaints\": [\n"
            "    {\n"
            "      \"sanskrit_term\": string (Sanskrit name of complaint/symptom, e.g. Jvara, Kasa - use knowledge base to map),\n"
            "      \"english_term\": string (English name, e.g. Fever, Cough),\n"
            "      \"duration\": string (e.g. \"5 days\"),\n"
            "      \"severity\": string (must be 'mild', 'moderate', or 'severe'),\n"
            "      \"remarks\": string\n"
            "    }\n"
            "  ],\n"
            "  \"prescription\": [\n"
            "    {\n"
            "      \"medicine_name\": string (e.g. \"Haridra Khanda\"),\n"
            "      \"dose\": string (e.g. \"1 tablet\" or \"15ml\"),\n"
            "      \"frequency\": string (e.g. \"twice daily\"),\n"
            "      \"anupana\": string (e.g. \"warm water\"),\n"
            "      \"duration\": string (e.g. \"7 days\"),\n"
            "      \"remarks\": string\n"
            "    }\n"
            "  ],\n"
            "  \"procedures\": [\n"
            "    {\n"
            "      \"procedure_name\": string (e.g. \"Matra Basti\"),\n"
            "      \"material\": string (e.g. \"Sahacharadi tailam\"),\n"
            "      \"total_sessions\": integer,\n"
            "      \"frequency\": string (must be 'daily', 'alternate', or 'weekly'),\n"
            "      \"start_date\": string (YYYY-MM-DD or null)\n"
            "    }\n"
            "  ]\n"
            "}\n\n"
            "Rules:\n"
            "1. Only include keys if they are updated or mentioned in the message. Do not overwrite current values with empty/null strings unless explicitly instructed in the message.\n"
            "2. If no new complaints/prescriptions/procedures are mentioned, do not return them in the JSON list (return empty or omit).\n"
            "3. If complaints/prescriptions/procedures are mentioned, return the ones that need to be added or modified.\n"
            "4. Return ONLY valid JSON. No markdown ticks like ```json.\n"
            "5. Intelligently map unstructured key-value formats (e.g. 'bp 120/80', 'pulse 72', 'wt 66.5', 'temp 98.4', 'height 172'):\n"
            "   - 'bp' or 'BP' maps to 'bp'\n"
            "   - 'pulse', 'p', or 'hr' maps to 'pulse'\n"
            "   - 'wt' or 'weight' maps to 'weight'\n"
            "   - 'ht' or 'height' maps to 'height'\n"
            "   - 'temp', 't', or 'temperature' maps to 'temperature'\n"
            "   - 'rr' maps to 'respiratory_rate'\n"
            "   - 'spo2' maps to 'spo2'\n"
            "6. STRICT PROTECTION: If the message consists ONLY of a raw number (e.g., '75' or '66.50') without any label/prefix (like 'pulse' or 'wt'), DO NOT guess or merge it into unrelated fields (such as 'bp'). Leave all fields unchanged if there is zero label context."
        )
        
        # 4. Query LLM
        res_data = service.query_llm_json(system_prompt, f"New Chatter Message:\n{message_text}")
        if not res_data or not isinstance(res_data, dict):
            return
            
        # 5. Apply extracted updates
        self._apply_ai_autofill_data(res_data)

        # 6. Post chatbot status back to chatter
        updated_parts = []
        vitals_fields = ['bp', 'pulse', 'respiratory_rate', 'spo2', 'temperature', 'weight', 'height', 'waist_circumference']
        if any(f in res_data and res_data[f] not in [None, '', 'None'] for f in vitals_fields):
            updated_parts.append("vitals")
        pariksha_fields = ['nadi', 'mala', 'mutra', 'jihwa', 'shabda', 'sparsha', 'drika', 'akruti',
                           'prakriti', 'vikriti', 'sara', 'samhanana', 'pramana', 'satmya', 'satva', 'ahara_shakti', 'vyayama_shakti', 'vaya']
        if any(f in res_data and res_data[f] not in [None, '', 'None'] for f in pariksha_fields):
            updated_parts.append("pariksha metrics")
        diag_fields = ['ayurveda_diagnosis', 'modern_diagnosis', 'samprapti']
        if any(f in res_data and res_data[f] not in [None, '', 'None'] for f in diag_fields):
            updated_parts.append("diagnosis")
        if 'complaints' in res_data and res_data['complaints']:
            updated_parts.append("chief complaints")
        if 'prescription' in res_data and res_data['prescription']:
            updated_parts.append("prescription lines")
        if 'procedures' in res_data and res_data['procedures']:
            updated_parts.append("procedure advice")

        if updated_parts:
            summary = ", ".join(updated_parts)
            self.message_post(
                body=f"AI Auto-Fill: Successfully parsed and updated {summary}.",
                author_id=self.env.ref('base.partner_root').id,
                subtype_xmlid='mail.mt_comment'
            )
        else:
            self.message_post(
                body="AI Auto-Fill: No clinical updates found in note.",
                author_id=self.env.ref('base.partner_root').id,
                subtype_xmlid='mail.mt_comment'
            )

    def _apply_ai_autofill_data(self, data):
        self.ensure_one()
        vals = {}
        
        # Map simple fields
        simple_fields = [
            'bp', 'pulse', 'respiratory_rate', 'spo2', 'temperature', 'weight', 'height', 'waist_circumference',
            'nadi', 'mala', 'mutra', 'jihwa', 'shabda', 'sparsha', 'drika', 'akruti',
            'prakriti', 'vikriti', 'sara', 'samhanana', 'pramana', 'satmya', 'satva', 'ahara_shakti', 'vyayama_shakti', 'vaya',
            'ayurveda_diagnosis', 'modern_diagnosis', 'samprapti'
        ]
        
        for field in simple_fields:
            if field in data and data[field] not in [None, '', 'None']:
                field_type = self._fields[field].type
                val = data[field]
                if field_type == 'integer':
                    try:
                        vals[field] = int(val)
                    except ValueError:
                        pass
                elif field_type == 'float':
                    try:
                        vals[field] = float(val)
                    except ValueError:
                        pass
                else:
                    vals[field] = str(val)
                    
        if vals:
            self.write(vals)
            
        # Map One2many Complaints
        if 'complaints' in data and isinstance(data['complaints'], list):
            for c in data['complaints']:
                sanskrit_term = c.get('sanskrit_term')
                if sanskrit_term:
                    existing = self.complaint_ids.filtered(lambda comp: comp.sanskrit_term.strip().lower() == sanskrit_term.strip().lower())
                    comp_vals = {
                        'english_term': c.get('english_term'),
                        'duration': c.get('duration'),
                        'severity': c.get('severity') if c.get('severity') in ['mild', 'moderate', 'severe'] else False,
                        'remarks': c.get('remarks')
                    }
                    if existing:
                        existing.write(comp_vals)
                    else:
                        comp_vals['sanskrit_term'] = sanskrit_term
                        self.write({'complaint_ids': [(0, 0, comp_vals)]})
                        
        # Map One2many Prescription Lines
        if 'prescription' in data and isinstance(data['prescription'], list):
            for p in data['prescription']:
                med_name = p.get('medicine_name')
                if med_name:
                    medicine = self.env['product.product'].search([('name', '=ilike', med_name)], limit=1)
                    if not medicine:
                        medicine = self.env['product.product'].create({
                            'name': med_name
                        })
                        
                    existing = self.prescription_ids.filtered(lambda line: line.medicine_id.id == medicine.id)
                    presc_vals = {
                        'dose': p.get('dose'),
                        'frequency': p.get('frequency'),
                        'anupana': p.get('anupana'),
                        'duration': p.get('duration'),
                        'remarks': p.get('remarks')
                    }
                    if existing:
                        existing.write(presc_vals)
                    else:
                        presc_vals['medicine_id'] = medicine.id
                        self.write({'prescription_ids': [(0, 0, presc_vals)]})
                        
        # Map One2many Procedures
        if 'procedures' in data and isinstance(data['procedures'], list):
            for pr in data['procedures']:
                proc_name = pr.get('procedure_name')
                if proc_name:
                    existing = self.procedure_advice_ids.filtered(lambda line: line.procedure_name.strip().lower() == proc_name.strip().lower())
                    proc_vals = {
                        'material': pr.get('material'),
                        'total_sessions': pr.get('total_sessions') or 1,
                        'frequency': pr.get('frequency') if pr.get('frequency') in ['daily', 'alternate', 'weekly'] else 'daily',
                    }
                    if pr.get('start_date'):
                        try:
                            fields.Date.from_string(pr['start_date'])
                            proc_vals['start_date'] = pr['start_date']
                        except Exception:
                            pass
                            
                    if existing:
                        existing.write(proc_vals)
                    else:
                        proc_vals['procedure_name'] = proc_name
                        self.write({'procedure_advice_ids': [(0, 0, proc_vals)]})

    def get_chat_history(self):
        self.ensure_one()
        comment_subtype = self.env.ref('mail.mt_comment', raise_if_not_found=False)
        allowed_subtypes = [comment_subtype.id] if comment_subtype else []

        messages = self.env['mail.message'].search([
            ('model', '=', self._name),
            ('res_id', '=', self.id),
            ('subtype_id', 'in', allowed_subtypes)
        ], order='id asc')

        history = []
        root_partner = self.env.ref('base.partner_root', raise_if_not_found=False)

        for msg in messages:
            plain = html2plaintext(msg.body or '').strip()
            if not plain:
                continue

            sender = 'user'
            if (root_partner and msg.author_id.id == root_partner.id) or plain.startswith("AI Auto-Fill") or plain.startswith("AI successfully"):
                sender = 'bot'

            # Format time
            local_time = fields.Datetime.context_timestamp(self, msg.date)
            time_str = local_time.strftime('%I:%M %p')

            history.append({
                'id': msg.id,
                'sender': sender,
                'text': plain,
                'time': time_str
            })

        if not history:
            history = [
                {
                    'id': 0,
                    'sender': 'bot',
                    'text': "Namaste! I am AyurGrid AI Assistant. Type your patient notes here, and I will extract metrics & populate the form tabs in real time.",
                    'time': ''
                }
            ]
        return history

    def action_post_chat_message(self, message_text):
        self.ensure_one()
        self.message_post(
            body=message_text,
            message_type='comment',
            subtype_xmlid='mail.mt_comment'
        )

class OPDComplaint(models.Model):
    _name = 'ag.opd.complaint'
    _description = 'Chief Complaint'

    consultation_id = fields.Many2one('ag.opd.consultation', string='Consultation', ondelete='cascade')
    sanskrit_term = fields.Char(string='Sanskrit Term', required=True)
    english_term = fields.Char(string='English Term')
    duration = fields.Char(string='Duration')
    severity = fields.Selection([
        ('mild', 'Mild'),
        ('moderate', 'Moderate'),
        ('severe', 'Severe')
    ], string='Severity')
    remarks = fields.Text(string='Remarks')

class OPDPrescriptionLine(models.Model):
    _name = 'ag.opd.prescription.line'
    _description = 'Prescription Line'

    consultation_id = fields.Many2one('ag.opd.consultation', string='Consultation', ondelete='cascade')
    medicine_id = fields.Many2one('product.product', string='Medicine', required=True)
    dose = fields.Char(string='Dose')
    frequency = fields.Char(string='Frequency')
    anupana = fields.Char(string='Anupana')
    duration = fields.Char(string='Duration')
    remarks = fields.Text(string='Remarks')
