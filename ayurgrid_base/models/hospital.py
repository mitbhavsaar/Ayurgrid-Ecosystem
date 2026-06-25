from odoo import api, fields, models, _

class Hospital(models.Model):
    _name = 'ag.hospital'
    _description = 'Hospital Master'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Hospital Name', required=True, tracking=True)
    organization_id = fields.Many2one('ag.organization', string='Organization', required=True, tracking=True)
    registration_number = fields.Char(string='Registration Number', tracking=True)
    clinical_establishment_no = fields.Char(string='Clinical Establishment No', tracking=True)
    rohini_id = fields.Char(string='ROHINI ID', tracking=True)
    nabh_status = fields.Selection([
        ('not_applied', 'Not Applied'),
        ('applied', 'Applied'),
        ('accredited', 'Accredited')
    ], string='NABH Status', default='not_applied', tracking=True)
    ayush_registration = fields.Char(string='AYUSH Registration', tracking=True)
    gstin = fields.Char(string='GSTIN')
    pan = fields.Char(string='PAN')
    email = fields.Char(string='Email')
    mobile = fields.Char(string='Mobile')
    website = fields.Char(string='Website')
    logo = fields.Binary(string='Logo')
    stamp = fields.Binary(string='Stamp')
    signature = fields.Binary(string='Signature')

    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
