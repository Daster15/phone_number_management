from odoo import models, fields, api


class RemovedNumbers(models.Model):
    _name = 'removed.numbers'
    _description = 'Removed Phone Numbers'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    number = fields.Char(string='Number', required=True, size=9, tracking=True)
    is_home_operator = fields.Boolean(string='Home Operator', tracking=True)
    rn_number = fields.Char(string='RN Number', tracking=True)
    subscriber_name = fields.Char(string='Subscriber Name', tracking=True)
    completion_date = fields.Date(string='Completion Date', tracking=True)
    completion_type = fields.Selection([
        ('removal', 'Removal'),
        ('return', 'Return')
    ], string='Completion Type', tracking=True)

    customer_id = fields.Many2one('res.partner', string='Customer', tracking=True)

    @api.constrains('number')
    def _check_number_format(self):
        for record in self:
            if not record.number.isdigit() or len(record.number) != 9:
                raise ValidationError("Number must be 9 digits")