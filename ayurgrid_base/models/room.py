from odoo import api, fields, models

class Room(models.Model):
    _name = 'ag.room'
    _description = 'Room Master'

    name = fields.Char(string='Room Number/Name', required=True)
    room_type = fields.Selection([
        ('consultation', 'Consultation'),
        ('therapy', 'Therapy'),
        ('procedure', 'Procedure'),
        ('ward', 'Ward'),
        ('private', 'Private Room'),
        ('deluxe', 'Deluxe Room'),
        ('suite', 'Suite'),
        ('icu', 'ICU')
    ], string='Room Type', required=True)
    floor = fields.Char(string='Floor')
    capacity = fields.Integer(string='Capacity (Beds)', default=1)
    branch_id = fields.Many2one('ag.branch', string='Branch', required=True)
    status = fields.Selection([
        ('available', 'Available'),
        ('occupied', 'Occupied'),
        ('maintenance', 'Maintenance')
    ], string='Status', default='available')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
