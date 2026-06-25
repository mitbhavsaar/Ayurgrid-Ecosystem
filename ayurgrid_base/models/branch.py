from odoo import api, fields, models, _

class Branch(models.Model):
    _name = 'ag.branch'
    _description = 'Branch Master'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Branch Name', required=True, tracking=True)
    code = fields.Char(string='Branch Code', required=True, tracking=True)
    hospital_id = fields.Many2one('ag.hospital', string='Hospital', required=True, tracking=True)
    branch_type = fields.Selection([
        ('hospital', 'Hospital'),
        ('clinic', 'Clinic'),
        ('panchakarma', 'Panchakarma Center'),
        ('opd', 'OPD Center'),
        ('wellness', 'Wellness Center')
    ], string='Branch Type', default='clinic', tracking=True)

    # Address
    address = fields.Text(string='Address')
    city = fields.Char(string='City')
    state_id = fields.Many2one('res.country.state', string='State')
    district = fields.Char(string='District')
    latitude = fields.Float(string='Latitude', digits=(10, 7))
    longitude = fields.Float(string='Longitude', digits=(10, 7))
    phone = fields.Char(string='Phone')
    email = fields.Char(string='Email')
    opening_date = fields.Date(string='Opening Date')
    active = fields.Boolean(string='Active', default=True)

    # Infrastructure
    total_area = fields.Float(string='Total Area (sq ft)')
    consultation_rooms = fields.Integer(string='Consultation Rooms')
    therapy_rooms = fields.Integer(string='Therapy Rooms')
    procedure_rooms = fields.Integer(string='Procedure Rooms')
    minor_ot = fields.Integer(string='Minor OT')
    major_ot = fields.Integer(string='Major OT')
    icu = fields.Integer(string='ICU Beds')
    ward_beds = fields.Integer(string='Ward Beds')
    private_rooms = fields.Integer(string='Private Rooms')
    deluxe_rooms = fields.Integer(string='Deluxe Rooms')
    suites = fields.Integer(string='Suites')

    # Ayurveda Services (Boolean fields)
    has_opd = fields.Boolean(string='OPD')
    has_ipd = fields.Boolean(string='IPD')
    has_panchakarma = fields.Boolean(string='Panchakarma')
    has_agnikarma = fields.Boolean(string='Agnikarma')
    has_ksharasutra = fields.Boolean(string='Ksharasutra')
    has_jalaukavcharana = fields.Boolean(string='Jalaukavcharana')
    has_raktamokshana = fields.Boolean(string='Raktamokshana')
    has_yoga = fields.Boolean(string='Yoga')
    has_physiotherapy = fields.Boolean(string='Physiotherapy')
    has_dietetics = fields.Boolean(string='Dietetics')

    # Human Resource Intake
    doctors_count = fields.Integer(string='Doctors')
    therapists_count = fields.Integer(string='Therapists')
    nurses_count = fields.Integer(string='Nurses')
    receptionists_count = fields.Integer(string='Receptionists')
    billing_staff_count = fields.Integer(string='Billing Staff')
    pharmacists_count = fields.Integer(string='Pharmacists')
    attendants_count = fields.Integer(string='Attendants')
    housekeeping_count = fields.Integer(string='Housekeeping')

    # Regulatory Intake
    clinical_registration = fields.Char(string='Clinical Registration')
    clinical_reg_expiry = fields.Date(string='Clinical Reg Expiry')
    rohini = fields.Char(string='ROHINI')
    rohini_expiry = fields.Date(string='ROHINI Expiry')
    nabh = fields.Char(string='NABH')
    nabh_expiry = fields.Date(string='NABH Expiry')
    biomedical_waste = fields.Char(string='Biomedical Waste')
    biomedical_expiry = fields.Date(string='Biomedical Expiry')
    fire_noc = fields.Char(string='Fire NOC')
    fire_noc_expiry = fields.Date(string='Fire NOC Expiry')
    lift_license = fields.Char(string='Lift License')
    lift_license_expiry = fields.Date(string='Lift License Expiry')
    pollution_noc = fields.Char(string='Pollution NOC')
    pollution_noc_expiry = fields.Date(string='Pollution NOC Expiry')
    local_authority_noc = fields.Char(string='Local Authority NOC')
    local_auth_noc_expiry = fields.Date(string='Local Auth NOC Expiry')

    # Financial Intake
    bank_accounts = fields.Text(string='Bank Accounts')
    upi = fields.Char(string='UPI')
    payment_gateway = fields.Char(string='Payment Gateway')
    gst = fields.Char(string='GST')
    tds = fields.Char(string='TDS')
    accounting_start_date = fields.Date(string='Accounting Start Date')

    # Digital Intake
    domain = fields.Char(string='Domain')
    subdomain = fields.Char(string='Subdomain')
    whatsapp_number = fields.Char(string='WhatsApp Number')
    sms_gateway = fields.Char(string='SMS Gateway')
    email_smtp = fields.Char(string='Email SMTP')
    google_business_profile = fields.Char(string='Google Business Profile')
    social_media_links = fields.Text(string='Social Media Links')

    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
