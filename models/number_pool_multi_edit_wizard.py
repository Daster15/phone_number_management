# -*- coding: utf-8 -*-
from odoo import models, fields, api


class NumberPoolMultiEditWizard(models.TransientModel):
    _name = 'number.pool.multi.edit.wizard'
    _description = 'Number Pool Multi Edit Wizard'

    number_ids = fields.Many2many(
        'number.pool',
        string='Numery',
        default=lambda self: self._default_number_ids(),
        readonly=True
    )

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

    def _default_number_ids(self):
        return self.env.context.get('active_ids', [])

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        active_ids = self.env.context.get('active_ids', [])
        if not active_ids:
            return res

        records = self.env['number.pool'].browse(active_ids)
        res['number_ids'] = [(6, 0, active_ids)]

        if len(active_ids) == 1:
            record = records[0]
            for field in self._fields:
                if field in ['id', 'number_ids', 'create_uid', 'create_date', 'write_uid', 'write_date']:
                    continue
                value = record[field]
                if self._fields[field].type == 'many2many':
                    res[field] = [(6, 0, value.ids)]
                elif self._fields[field].type in ['many2one']:
                    res[field] = value.id if value else False
                else:
                    res[field] = value
            return res

        def get_common_value(field_name):
            field_type = self._fields[field_name].type

            if field_type == 'many2many':
                ids_sets = [set(v.ids) for v in records.mapped(field_name)]
                if not ids_sets or any(len(s) != len(ids_sets[0]) for s in ids_sets):
                    return []
                first = ids_sets[0]
                return list(first) if all(s == first for s in ids_sets) else []

            if field_type == 'many2one':
                first = records[0][field_name]
                if not first:
                    return False
                if all(rec[field_name] and rec[field_name].id == first.id for rec in records):
                    return first.id
                return False

            values = [rec[field_name] for rec in records]
            if any(v in (False, '', None) for v in values):
                return False
            return values[0] if all(v == values[0] for v in values) else False

        for field_name in self._fields:
            if field_name in ['id', 'number_ids', 'create_uid', 'create_date', 'write_uid', 'write_date']:
                continue
            common_value = get_common_value(field_name)
            if self._fields[field_name].type == 'many2many':
                res[field_name] = [(6, 0, common_value)] if common_value else []
            else:
                res[field_name] = common_value

        return res

    def action_apply_changes(self):
        self.ensure_one()
        values = {}

        for field_name, field in self._fields.items():
            if field_name in ['id', 'number_ids', 'create_uid', 'create_date', 'write_uid', 'write_date']:
                continue

            # Jeżeli użytkownik coś wpisał
            if self[field_name] not in (False, '', [], 0):
                if field.type == 'many2many':
                    values[field_name] = [(6, 0, self[field_name].ids)]
                else:
                    values[field_name] = self[field_name]

        if values:
            self.number_ids.write(values)
        return {'type': 'ir.actions.act_window_close'}
