from odoo import api, fields, models, _

class Organization(models.Model):
    _name = 'ag.organization'
    _description = 'Organization Master'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Organization Name', required=True, tracking=True)
    legal_name = fields.Char(string='Legal Name', tracking=True)
    llp_cin = fields.Char(string='LLP/CIN', tracking=True)
    gstin = fields.Char(string='GSTIN', tracking=True)
    pan = fields.Char(string='PAN', tracking=True)
    email = fields.Char(string='Email', tracking=True)
    mobile = fields.Char(string='Mobile', tracking=True)
    website = fields.Char(string='Website')
    logo = fields.Binary(string='Logo')
    
    # Address fields
    address = fields.Text(string='Address')
    country_id = fields.Many2one('res.country', string='Country')
    state_id = fields.Many2one('res.country.state', string='State', domain="[('country_id', '=?', country_id)]")
    district = fields.Char(string='District')
    city = fields.Char(string='City')
    pincode = fields.Char(string='Pincode')
    
    timezone = fields.Selection([
        ('UTC', 'UTC'),
        ('Asia/Kolkata', 'Asia/Kolkata'),
    ], string='Timezone', default='Asia/Kolkata')
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id.id)

    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
