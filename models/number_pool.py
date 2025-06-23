# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
from dateutil.relativedelta import relativedelta
import logging

_logger = logging.getLogger(__name__)


class NumberPool(models.Model):
    _name = 'number.pool'
    _description = 'Phone Number Pool'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'number'
    _sql_constraints = [
        ('number_uniq', 'unique(number)', 'Number must be unique!'),
    ]


    number = fields.Char(string='Number', required=True, tracking=True, index=True, copy=False)
    source = fields.Selection([
        ('uke', 'UKE'),
        ('plk', 'PLK'),
        ('p4', 'P4'),
        ('mmp', 'MMP'),
        ('vectra', 'Vectra'),
        ('obca', 'OBCA Reseller')
    ], string='Source', required=True, tracking=True)

    number_type = fields.Selection([
        ('fix', 'Fixed'),
        ('mob', 'Mobile'),
        ('mobsms', 'Mobile SMS')
    ], string='Type', required=True, tracking=True)

    status = fields.Selection([
        ('free', 'Free'),
        ('occupied', 'Occupied'),
        ('reserved', 'Reserved'),
        ('grace', 'Grace Period')
    ], string='Status', default='free', tracking=True, group_expand='_read_group_status', index=True)

    reservation_date = fields.Date(string='Reservation Date', tracking=True, index=True)
    activation_date = fields.Date(string='Activation Date', tracking=True)
    release_date = fields.Date(string='Release Date', tracking=True)

    reseller_id = fields.Many2one('res.partner', string='Reseller', tracking=True)
    customer_id = fields.Many2one('res.partner', string='Customer', tracking=True)
    subscriber_id = fields.Many2one('res.partner', string='Subscriber', tracking=True)

    history_line_ids = fields.One2many('number.history', 'number_id', string='History Lines', readonly=True)

    adescom_status = fields.Selection([
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('terminated', 'Terminated')
    ], string='Adescom Status', tracking=True)

    nip = fields.Char(string='NIP', tracking=True)
    contract_number = fields.Char(string='Contract Number', tracking=True)
    order_number = fields.Char(string='Order Number', tracking=True)
    notes = fields.Text(string='Notes', tracking=True, size=200)
    tags = fields.Many2many('number.pool.tags', string='Tags')

    @api.model_create_multi
    def create(self, vals_list):
        incoming_numbers = [vals.get('number') for vals in vals_list if vals.get('number')]
        existing = self.search([('number', 'in', incoming_numbers)])
        existing_map = {rec.number: rec for rec in existing}

        to_create = []
        result = self.env['number.pool']

        for vals in vals_list:
            num = vals.get('number')
            rec = existing_map.get(num)
            if rec:
                rec.write(vals)
                result |= rec
            else:
                to_create.append(vals)

        if to_create:
            new_recs = super(NumberPool, self).create(to_create)
            result |= new_recs

        return result

    def _read_group_status(self, statuses, domain, order):
        return [key for key, _ in type(self).status.selection]

    def _clear_fields_when_free(self):
        self.write({
            'customer_id': False,
            'subscriber_id': False,
            'reseller_id': False,
            'reservation_date': False,
            'activation_date': False,
            'release_date': fields.Date.today(),
            'nip': False,
            'contract_number': False,
            'order_number': False,
            'adescom_status': False,
            'notes': False,
            'tags': [(5, 0, 0)],
        })

    @api.constrains('number')
    def _check_number_format(self):
        for rec in self:
            if not rec.number or not rec.number.isdigit():
                raise ValidationError("Numer musi składać się wyłącznie z cyfr (0-9)")
            if not 9 <= len(rec.number) <= 16:
                raise ValidationError("Numer musi mieć od 9 do 16 cyfr")

    @api.constrains('reservation_date', 'activation_date', 'release_date')
    def _check_dates_consistency(self):
        for r in self:
            if r.reservation_date and r.activation_date and r.activation_date < r.reservation_date:
                raise ValidationError("Data aktywacji nie może być wcześniejsza niż data rezerwacji")
           # if r.activation_date and r.release_date and r.release_date < r.activation_date:
           #     raise ValidationError("Data zwolnienia nie może być wcześniejsza niż data aktywacji")

    def _validate_status_requirements(self):
        today = fields.Date.today()
        one_month_ago = today - relativedelta(months=1)
        for r in self:
            #if r.status == 'free' and (r.reseller_id or r.subscriber_id):
            #   raise ValidationError("Wolne numery nie mogą mieć przypisanego klienta lub abonenta")
            if r.status == 'reserved':
                if  not r.subscriber_id or not r.reseller_id or not r.reservation_date:
                    raise ValidationError("Brak wymaganych pól dla statusu 'reserved'")
                if r.reservation_date < one_month_ago:
                    raise ValidationError("Data rezerwacji nie może być starsza niż 1 miesiąc")
            if r.status == 'occupied':
                for f in ['subscriber_id', 'reseller_id', 'reservation_date', 'activation_date', 'contract_number']:
                    if not getattr(r, f):
                        raise ValidationError(f"Pole '{f}' jest wymagane dla statusu 'occupied'")
            if r.status == 'grace' and not r.release_date:
                raise ValidationError("Pole 'Data zwolnienia' jest wymagane dla statusu 'grace'")

    def action_open_multi_edit(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Mass Edit Numbers',
            'res_model': 'number.pool.multi.edit.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_number_ids': [(6, 0, self.ids)],
            }
        }

    def write(self, vals):
        for rec in self:
            old_status = rec.status
            new_status = vals.get('status', old_status)

            if old_status != new_status and new_status == 'free':
                vals.update({
                    'customer_id': False,
                    'subscriber_id': False,
                    'reseller_id' :False,
                    'reservation_date': False,
                    'activation_date': False,
                    'release_date': False,
                    'nip': False,
                    'contract_number': False,
                    'order_number': False,
                    'adescom_status': False,
                    'notes': False,
                    'tags': [(5, 0, 0)],
                })

            res = super(NumberPool, rec).write(vals)
            rec._validate_status_requirements()
            rec._create_history_record(old_status, rec.status)

        return True

    def _create_history_record(self, old_status, new_status):
        _logger.info("Tworzenie historii: %s -> %s dla ID %s", old_status, new_status, self.id)
        self.env['number.history'].create({
            'number_id': self.id,
            'subscriber_id': self.subscriber_id.id if self.subscriber_id else False,
            'customer_id': self.customer_id.id if self.customer_id else False,
            'reseller_id': self.customer_id.id if self.customer_id else False,
            'old_status': old_status,
            'new_status': new_status,
            'change_date': fields.Datetime.now(),
            'reservation_date': self.reservation_date,
            'activation_date': self.activation_date,
            'release_date': self.release_date,
            'adescom_status': self.adescom_status,
            'contract_number': self.contract_number,
        })

    def unlink(self):
        for rec in self:
            if rec.status != 'free':
                raise UserError("Można usunąć tylko numery o statusie 'free'.")
        return super().unlink()


class NumberHistory(models.Model):
    _name = 'number.history'
    _description = 'Number History'
    _order = 'change_date desc'

    number_id = fields.Many2one('number.pool', string='Number', required=True, ondelete='cascade')
    subscriber_id = fields.Many2one('res.partner', string='Subscriber')
    customer_id = fields.Many2one('res.partner', string='Customer')
    reseller_id = fields.Many2one('res.partner', string='Reseller')

    old_status = fields.Selection([
        ('free', 'Free'),
        ('occupied', 'Occupied'),
        ('reserved', 'Reserved'),
        ('grace', 'Grace Period')
    ], string='Previous Status')

    new_status = fields.Selection([
        ('free', 'Free'),
        ('occupied', 'Occupied'),
        ('reserved', 'Reserved'),
        ('grace', 'Grace Period')
    ], string='New Status')

    change_date = fields.Datetime(string='Change Date')
    reservation_date = fields.Date(string='Reservation Date')
    activation_date = fields.Date(string='Activation Date')
    release_date = fields.Date(string='Release Date')

    adescom_status = fields.Selection([
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('terminated', 'Terminated')
    ], string='Adescom Status')

    contract_number = fields.Char(string='Contract Number')


class NumberPoolTags(models.Model):
    _name = 'number.pool.tags'
    _description = 'Number Pool Tags'

    name = fields.Char(string='Tag Name', required=True, translate=True)
    color = fields.Integer(string='Color Index')

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Tag name already exists!"),
    ]
