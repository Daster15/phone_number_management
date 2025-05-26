# -*- coding: utf-8 -*-
from odoo import models, fields, api


class NumberPoolMultiEditWizard(models.TransientModel):
    _name = 'number.pool.multi.edit.wizard'
    _description = 'Number Pool Multi Edit Wizard'

    number_ids = fields.Many2many('number.pool', string='Numery do edycji')

    # Dodaj pola do edycji
    status = fields.Selection([
        ('free', 'Free'),
        ('occupied', 'Occupied'),
        ('reserved', 'Reserved'),
        ('grace', 'Grace Period')
    ], string='Status')

    customer_id = fields.Many2one('res.partner', string='Właściciel')
    subscriber_id = fields.Many2one('res.partner', string='Abonent')
    nip = fields.Char(string='NIP')
    contract_number = fields.Char(string='Numer Umowy')
    order_number = fields.Char(string='Numer Zamówienia')
    reservation_date = fields.Date(string='Data rezerwacji')
    activation_date = fields.Date(string='Data aktywacji')
    release_date = fields.Date(string='Data zwolnienia')
    tags = fields.Many2many('number.pool.tags', string='Tagi')

    @api.model
    def default_get(self, fields):
        res = super(NumberPoolMultiEditWizard, self).default_get(fields)
        active_ids = self.env.context.get('active_ids')
        if active_ids:
            res['number_ids'] = [(6, 0, active_ids)]
            if len(active_ids) == 1:
                # Dla jednego rekordu wypełnij wartości domyślne
                record = self.env['number.pool'].browse(active_ids)
                res.update({
                    'status': record.status,
                    'customer_id': record.customer_id.id,
                    'subscriber_id': record.subscriber_id.id,
                    'nip': record.nip,
                    'contract_number': record.contract_number,
                    'order_number': record.order_number,
                    'reservation_date': record.reservation_date,
                    'activation_date': record.activation_date,
                    'release_date': record.release_date,
                    'tags': [(6, 0, record.tags.ids)],
                })
        return res

    def action_apply_changes(self):
        self.ensure_one()
        values = {}
        for field in self._fields:
            if field not in ['id', 'number_ids', 'create_uid', 'create_date', 'write_uid', 'write_date']:
                if self[field]:
                    values[field] = self[field]

        if values:
            self.number_ids.write(values)
        return {'type': 'ir.actions.act_window_close'}