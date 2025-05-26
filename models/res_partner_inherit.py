from odoo import models, fields

class ResPartner(models.Model):
    _inherit = 'res.partner'

    subscribed_number_ids = fields.One2many(
        'number.pool',
        'subscriber_id',
        string='Subscribed Numbers'
    )