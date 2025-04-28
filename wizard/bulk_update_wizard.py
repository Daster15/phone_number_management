# -*- coding: utf-8 -*-
from odoo import models, fields, api


class BulkUpdateWizard(models.TransientModel):
    _name = 'bulk.update.wizard'
    _description = 'Bulk Number Update Wizard'

    number_ids = fields.Many2many(
        'number.pool',
        string='Numbers',
        default=lambda self: self.env.context.get('active_ids')
    )

    action_type = fields.Selection([
        ('reserve', 'Reserve'),
        ('activate', 'Activate'),
        ('release', 'Release'),
        ('change_status', 'Change Status')
    ], string='Action', required=True)

    new_status = fields.Selection([
        ('free', 'Free'),
        ('occupied', 'Occupied'),
        ('reserved', 'Reserved'),
        ('grace', 'Grace Period')
    ], string='New Status')

    subscriber_name = fields.Char(string='Subscriber Name')
    customer_id = fields.Many2one('res.partner', string='Customer')

    def action_apply(self):
        for record in self:
            vals = {}
            if record.action_type == 'reserve':
                vals.update({
                    'status': 'reserved',
                    'reservation_date': fields.Date.today(),
                    'subscriber_name': record.subscriber_name,
                    'customer_id': record.customer_id.id
                })
            elif record.action_type == 'activate':
                vals.update({
                    'status': 'occupied',
                    'activation_date': fields.Date.today()
                })
            elif record.action_type == 'release':
                vals.update({
                    'status': 'free',
                    'release_date': fields.Date.today(),
                    'subscriber_name': False,
                    'customer_id': False,
                    'reservation_date': False,
                    'activation_date': False
                })
            elif record.action_type == 'change_status':
                vals.update({'status': record.new_status})

            record.number_ids.write(vals)

        return {'type': 'ir.actions.act_window_close'}