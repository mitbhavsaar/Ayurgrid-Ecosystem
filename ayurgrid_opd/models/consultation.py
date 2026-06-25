from odoo import api, fields, models

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
