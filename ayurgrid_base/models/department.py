from odoo import api, fields, models

class Department(models.Model):
    _name = 'ag.department'
    _description = 'Department Master'

    name = fields.Char(string='Department Name', required=True)
    description = fields.Text(string='Description')
    branch_id = fields.Many2one('ag.branch', string='Branch')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
