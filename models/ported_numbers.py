from odoo import models, fields, api


class PortedNumbers(models.Model):
    _name = 'ported.numbers'
    _description = 'Ported Phone Numbers'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    number = fields.Char(string='Number', required=True, size=9, tracking=True)
    subscriber_name = fields.Char(string='Subscriber Name', tracking=True)
    identification_type = fields.Selection([
        ('nip', 'NIP'),
        ('regon', 'REGON'),
        ('pesel', 'PESEL')
    ], string='Identification Type', tracking=True)

    identification_number = fields.Char(string='Identification Number', tracking=True)
    donor = fields.Char(string='Donor', tracking=True)
    porting_date = fields.Date(string='Porting Date', tracking=True)
    return_date = fields.Date(string='Return Date', tracking=True)
    is_active = fields.Boolean(string='Active', default=True, tracking=True)

    customer_id = fields.Many2one('res.partner', string='Customer', tracking=True)

    @api.constrains('number')
    def _check_number_format(self):
        for record in self:
            if not record.number.isdigit() or len(record.number) != 9:
                raise ValidationError("Number must be 9 digits")