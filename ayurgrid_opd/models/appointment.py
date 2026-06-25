from odoo import api, fields, models

class OPDAppointment(models.Model):
    _name = 'ag.opd.appointment'
    _description = 'OPD Appointment'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Appointment Reference', required=True, copy=False, readonly=True, default='New')
    patient_id = fields.Many2one('ag.patient', string='Patient', required=True)
    doctor_id = fields.Many2one('res.users', string='Doctor', required=True)
    appointment_date = fields.Datetime(string='Date', required=True, default=fields.Datetime.now)
    
    appointment_type = fields.Selection([
        ('new', 'New Consultation'),
        ('follow_up', 'Follow-Up Consultation'),
        ('emergency', 'Emergency Walk-In'),
        ('teleconsult', 'Teleconsultation'),
        ('corporate', 'Corporate Consultation'),
        ('camp', 'Camp Consultation')
    ], string='Type', required=True, default='new')

    state = fields.Selection([
        ('booked', 'Booked'),
        ('checked_in', 'Checked In'),
        ('in_queue', 'In Queue'),
        ('started', 'Consultation Started'),
        ('completed', 'Consultation Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
        ('rescheduled', 'Rescheduled')
    ], string='Status', required=True, default='booked', tracking=True)

    notes = fields.Text(string='Notes')
    
    consultation_ids = fields.One2many('ag.opd.consultation', 'appointment_id', string='Consultations')
    consultation_count = fields.Integer(compute='_compute_consultation_count', string='Consultation Count')

    @api.depends('consultation_ids')
    def _compute_consultation_count(self):
        for rec in self:
            rec.consultation_count = len(rec.consultation_ids)

    def action_view_consultations(self):
        self.ensure_one()
        return {
            'name': 'Consultations',
            'type': 'ir.actions.act_window',
            'res_model': 'ag.opd.consultation',
            'view_mode': 'list,form',
            'domain': [('appointment_id', '=', self.id)],
            'context': {'default_appointment_id': self.id, 'default_patient_id': self.patient_id.id, 'default_doctor_id': self.doctor_id.id},
        }

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('ag.opd.appointment') or 'New'
        return super(OPDAppointment, self).create(vals_list)

    def action_check_in(self):
        for rec in self:
            rec.state = 'checked_in'

    def action_in_queue(self):
        for rec in self:
            rec.state = 'in_queue'

    def action_start_consultation(self):
        for rec in self:
            rec.state = 'started'
            # Auto-create the consultation record
            consultation = self.env['ag.opd.consultation'].create({
                'appointment_id': rec.id,
                'patient_id': rec.patient_id.id,
                'doctor_id': rec.doctor_id.id,
                'consultation_type': rec.appointment_type if rec.appointment_type in ['new', 'follow_up', 'teleconsult', 'emergency'] else 'new',
            })
            return {
                'name': 'Consultation',
                'view_mode': 'form',
                'res_model': 'ag.opd.consultation',
                'res_id': consultation.id,
                'type': 'ir.actions.act_window',
            }

    def action_complete(self):
        for rec in self:
            rec.state = 'completed'

    def action_cancel(self):
        for rec in self:
            rec.state = 'cancelled'
