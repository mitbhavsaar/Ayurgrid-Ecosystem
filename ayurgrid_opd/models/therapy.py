from odoo import api, fields, models

class OPDTherapyPrescription(models.Model):
    _name = 'ag.opd.therapy.prescription'
    _description = 'Therapy Prescription Advice'

    name = fields.Char(string='Reference', required=True, copy=False, readonly=True, default='New')
    consultation_id = fields.Many2one('ag.opd.consultation', string='Consultation', ondelete='cascade')
    patient_id = fields.Many2one(related='consultation_id.patient_id', store=True, string='Patient')
    procedure_name = fields.Char(string='Procedure', required=True)
    material = fields.Char(string='Material/Oil')
    total_sessions = fields.Integer(string='Total Sessions', required=True, default=1)
    start_date = fields.Date(string='Start Date', default=fields.Date.context_today)
    frequency = fields.Selection([
        ('daily', 'Daily'),
        ('alternate', 'Alternate Days'),
        ('weekly', 'Weekly')
    ], string='Frequency', default='daily')
    session_ids = fields.One2many('ag.opd.therapy.session', 'prescription_id', string='Sessions')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('ag.opd.therapy.prescription') or 'New'
        return super(OPDTherapyPrescription, self).create(vals_list)

    def action_generate_sessions(self):
        # Basic logic to generate session records
        for rec in self:
            if not rec.session_ids:
                for i in range(1, rec.total_sessions + 1):
                    self.env['ag.opd.therapy.session'].create({
                        'prescription_id': rec.id,
                        'session_number': i,
                        'session_date': rec.start_date, # Simple default, real logic handles frequency
                        'status': 'scheduled'
                    })

class OPDTherapySession(models.Model):
    _name = 'ag.opd.therapy.session'
    _description = 'Therapy Session Register'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Session ID', compute='_compute_name', store=True)
    prescription_id = fields.Many2one('ag.opd.therapy.prescription', string='Prescription', ondelete='cascade')
    patient_id = fields.Many2one(related='prescription_id.patient_id', store=True, string='Patient')
    procedure_name = fields.Char(related='prescription_id.procedure_name', store=True, string='Procedure')
    session_number = fields.Integer(string='Session #')
    session_date = fields.Datetime(string='Session Date', required=True)
    therapist_id = fields.Many2one('res.users', string='Therapist')
    
    status = fields.Selection([
        ('scheduled', 'Scheduled'),
        ('checked_in', 'Checked In'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('missed', 'Missed')
    ], string='Status', required=True, default='scheduled', tracking=True)

    attendance = fields.Selection([
        ('present', 'Present'),
        ('absent', 'Absent')
    ], string='Attendance')
    
    remarks = fields.Text(string='Remarks')

    @api.depends('prescription_id', 'session_number')
    def _compute_name(self):
        for rec in self:
            rec.name = f"{rec.prescription_id.name or ''} - S{rec.session_number}"

    def action_check_in(self):
        for rec in self:
            rec.status = 'checked_in'

    def action_start(self):
        for rec in self:
            rec.status = 'in_progress'

    def action_complete(self):
        for rec in self:
            rec.status = 'completed'

    def action_missed(self):
        for rec in self:
            rec.status = 'missed'

    def action_cancel(self):
        for rec in self:
            rec.status = 'cancelled'
