from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from datetime import date
import requests
import json

class Patient(models.Model):
    _name = 'ag.patient'
    _description = 'Patient Master'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # Core Fields
    patient_id = fields.Char(string='Patient ID', required=True, copy=False, readonly=True, default=lambda self: _('New'), tracking=True)
    uhid = fields.Char(string='UHID', tracking=True)
    first_name = fields.Char(string='First Name', required=True, tracking=True)
    middle_name = fields.Char(string='Middle Name', tracking=True)
    last_name = fields.Char(string='Last Name', required=True, tracking=True)
    
    name = fields.Char(string='Name', compute='_compute_name', store=True, tracking=True)

    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other')
    ], string='Gender', tracking=True)
    dob = fields.Date(string='Date of Birth', tracking=True)
    age = fields.Integer(string='Age', compute='_compute_age', store=True)
    marital_status = fields.Selection([
        ('single', 'Single'),
        ('married', 'Married'),
        ('widowed', 'Widowed'),
        ('divorced', 'Divorced'),
        ('separated', 'Separated')
    ], string='Marital Status')
    occupation = fields.Char(string='Occupation')
    education = fields.Char(string='Education')
    photo = fields.Binary(string='Photo')
    mobile = fields.Char(string='Mobile', required=True, tracking=True)
    alternate_mobile = fields.Char(string='Alternate Mobile')
    email = fields.Char(string='Email')

    # Address Details
    current_address = fields.Text(string='Current Address')
    permanent_address = fields.Text(string='Permanent Address')
    country_id = fields.Many2one('res.country', string='Country')
    state_id = fields.Many2one('res.country.state', string='State', domain="[('country_id', '=?', country_id)]")
    district = fields.Char(string='District')
    taluka = fields.Char(string='Taluka')
    village = fields.Char(string='Village/City')
    pincode = fields.Char(string='Pincode')
    geo_coordinates = fields.Char(string='Geo Coordinates')

    # Government Identity
    aadhaar = fields.Char(string='Aadhaar')
    pan = fields.Char(string='PAN')
    abha_id = fields.Char(string='ABHA ID')
    passport = fields.Char(string='Passport')
    driving_license = fields.Char(string='Driving License')
    voter_id = fields.Char(string='Voter ID')
    upload_documents = fields.Binary(string='Upload Documents') # A single binary field or One2many for multiple documents

    # Emergency Contact
    emergency_name = fields.Char(string='Emergency Contact Name')
    emergency_relation = fields.Char(string='Relation')
    emergency_mobile = fields.Char(string='Emergency Mobile')
    emergency_alt_mobile = fields.Char(string='Emergency Alternate Mobile')
    emergency_address = fields.Text(string='Emergency Address')

    # Medicolegal Information
    consent_status = fields.Boolean(string='Consent Status')
    mlc_status = fields.Boolean(string='MLC Status')
    police_information = fields.Text(string='Police Information')
    guardian_information = fields.Text(string='Guardian Information')

    # Ayurveda Registration Section - Prakriti Assessment
    prakriti_vata = fields.Float(string='Vata %')
    prakriti_pitta = fields.Float(string='Pitta %')
    prakriti_kapha = fields.Float(string='Kapha %')
    assessment_method = fields.Char(string='Assessment Method')
    assessor_id = fields.Many2one('res.users', string='Assessor')
    assessment_date = fields.Date(string='Assessment Date')

    # Vikriti Assessment
    vikriti_vata = fields.Float(string='Vikriti Vata %')
    vikriti_pitta = fields.Float(string='Vikriti Pitta %')
    vikriti_kapha = fields.Float(string='Vikriti Kapha %')
    current_imbalance = fields.Text(string='Current Imbalance')

    # Dashavidha Pariksha
    d_prakriti = fields.Char(string='Prakriti (D)')
    d_vikriti = fields.Char(string='Vikriti (D)')
    d_sara = fields.Char(string='Sara')
    d_samhanana = fields.Char(string='Samhanana')
    d_pramana = fields.Char(string='Pramana')
    d_satmya = fields.Char(string='Satmya')
    d_satva = fields.Char(string='Satva')
    d_aharashakti = fields.Char(string='Aharashakti')
    d_vyayamashakti = fields.Char(string='Vyayamashakti')
    d_vaya = fields.Char(string='Vaya')

    # Ashtavidha Pariksha
    a_nadi = fields.Char(string='Nadi')
    a_mala = fields.Char(string='Mala')
    a_mutra = fields.Char(string='Mutra')
    a_jihva = fields.Char(string='Jihva')
    a_shabda = fields.Char(string='Shabda')
    a_sparsha = fields.Char(string='Sparsha')
    a_drik = fields.Char(string='Drik')
    a_akruti = fields.Char(string='Akruti')

    # Lifestyle Intake
    wake_up_time = fields.Float(string='Wake Up Time')
    sleep_time = fields.Float(string='Sleep Time')
    diet_pattern = fields.Selection([
        ('veg', 'Vegetarian'),
        ('nonveg', 'Non-Vegetarian'),
        ('vegan', 'Vegan'),
        ('mixed', 'Mixed')
    ], string='Diet Pattern')
    addictions = fields.Text(string='Addictions')
    exercise = fields.Text(string='Exercise')
    occupation_type = fields.Char(string='Occupation Type')
    stress_level = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High')
    ], string='Stress Level')

    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)

    @api.depends('first_name', 'middle_name', 'last_name')
    def _compute_name(self):
        for rec in self:
            names = [name for name in [rec.first_name, rec.middle_name, rec.last_name] if name]
            rec.name = ' '.join(names)

    @api.depends('dob')
    def _compute_age(self):
        for rec in self:
            if rec.dob:
                today = date.today()
                rec.age = today.year - rec.dob.year - ((today.month, today.day) < (rec.dob.month, rec.dob.day))
            else:
                rec.age = 0

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('patient_id', _('New')) == _('New'):
                vals['patient_id'] = self.env['ir.sequence'].next_by_code('ag.patient') or _('New')
        return super(Patient, self).create(vals_list)

    def action_ai_predict_prakriti(self):
        self.ensure_one()
        
        # 1. Get active AI Config
        ai_config = self.env['ag.ai.configuration'].search([('ai_enabled', '=', True), ('provider', '=', 'nvidia')], limit=1)
        if not ai_config:
            raise UserError('No active NVIDIA AI Configuration found. Please set one up in Admin Setup.')
        if not ai_config.api_key:
            raise UserError('API Key is missing in the active AI Configuration.')

        # 2. Gather patient lifestyle data
        lifestyle_data = {
            "Wake Up Time": self.wake_up_time or "Not specified",
            "Sleep Time": self.sleep_time or "Not specified",
            "Diet Pattern": dict(self._fields['diet_pattern'].selection).get(self.diet_pattern, "Not specified"),
            "Addictions": self.addictions or "None",
            "Exercise": self.exercise or "None",
            "Occupation Type": self.occupation_type or "Not specified",
            "Stress Level": dict(self._fields['stress_level'].selection).get(self.stress_level, "Not specified"),
        }
        
        prompt = (
            "You are an expert Ayurvedic doctor. Based on the following patient lifestyle data, "
            "predict their Prakriti (Vata, Pitta, Kapha) as percentages summing to 100.\n\n"
            f"Patient Lifestyle Data: {json.dumps(lifestyle_data)}\n\n"
            "Return ONLY a raw JSON object with the keys 'vata', 'pitta', and 'kapha' and numeric values. Do not wrap it in markdown or add any other text."
        )

        api_key_clean = ai_config.api_key.strip()
        url = "https://integrate.api.nvidia.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key_clean}",
            "Content-Type": "application/json"
        }
        model = ai_config.model_name.strip() if ai_config.model_name else "meta/llama-3.1-8b-instruct"
        
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 50,
            "temperature": ai_config.temperature or 0.7
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=15)
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content'].strip()
                
                # Clean up possible markdown code blocks
                if content.startswith('```json'):
                    content = content[7:-3]
                elif content.startswith('```'):
                    content = content[3:-3]
                    
                try:
                    parsed_result = json.loads(content)
                    
                    self.prakriti_vata = parsed_result.get('vata', 0)
                    self.prakriti_pitta = parsed_result.get('pitta', 0)
                    self.prakriti_kapha = parsed_result.get('kapha', 0)
                    self.assessment_method = 'AI Predicted'
                    self.assessment_date = fields.Date.today()
                    
                    self.message_post(body=f"AI successfully predicted Prakriti based on lifestyle data.<br/>Vata: {self.prakriti_vata}%<br/>Pitta: {self.prakriti_pitta}%<br/>Kapha: {self.prakriti_kapha}%")
                    
                except json.JSONDecodeError:
                    raise UserError(f'Failed to parse AI response as JSON. AI Response was: {content}')
            else:
                raise UserError(f'API Connection failed! Status: {response.status_code}\nResponse: {response.text}')
        except requests.exceptions.RequestException as e:
            raise UserError(f'Network error: {str(e)}')
