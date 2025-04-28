from odoo import models, fields, api
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


class NumberPool(models.Model):
    _name = 'number.pool'
    _description = 'Phone Number Pool'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'number'

    number = fields.Char(string='Number', required=True, size=9, tracking=True)
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

    reseller_id = fields.Many2one('res.partner', string='Reseller', tracking=True)

    status = fields.Selection([
        ('free', 'Free'),
        ('occupied', 'Occupied'),
        ('reserved', 'Reserved'),
        ('grace', 'Grace Period')
    ], string='Status', default='free', tracking=True)

    subscriber_name = fields.Char(string='Subscriber Name', tracking=True)
    reservation_date = fields.Date(string='Reservation Date', tracking=True)
    activation_date = fields.Date(string='Activation Date', tracking=True)
    release_date = fields.Date(string='Release Date', tracking=True)

    history_line_ids = fields.One2many(
        'number.history', 'number_id', string='History Lines')

    customer_id = fields.Many2one('res.partner', string='Customer', tracking=True)

    @api.constrains('number')
    def _check_number_format(self):
        for record in self:
            if not record.number.isdigit() or len(record.number) != 9:
                raise ValidationError("Number must be 9 digits")

    def action_reserve(self):
        self.write({
            'status': 'reserved',
            'reservation_date': fields.Date.today()
        })

    def action_activate(self):
        self.write({
            'status': 'occupied',
            'activation_date': fields.Date.today()
        })

    def action_release(self):
        self.write({
            'status': 'free',
            'subscriber_name': False,
            'customer_id': False,
            'release_date': fields.Date.today(),
            'reservation_date': False,
            'activation_date': False
        })

    def action_show_history(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Number History',
            'view_mode': 'tree,form',
            'res_model': 'number.history',
            'domain': [('number_id', '=', self.id)],
            'context': {'default_number_id': self.id},
        }


class NumberHistory(models.Model):
    _name = 'number.history'
    _description = 'Number History'
    _order = 'activation_date desc'

    number_id = fields.Many2one('number.pool', string='Number', required=True)
    subscriber_name = fields.Char(string='Subscriber Name')
    customer_id = fields.Many2one('res.partner', string='Customer')
    activation_date = fields.Date(string='Activation Date')
    release_date = fields.Date(string='Release Date')
    status = fields.Selection(related='number_id.status', string='Status')

    reservation_date = fields.Date(string='Reservation Date', tracking=True)
    release_date = fields.Date(string='Release Date', tracking=True)

    @api.constrains('reservation_date', 'release_date')
    def _check_dates(self):
        for record in self:
            if record.reservation_date and record.release_date:
                if record.release_date <= record.reservation_date:
                    raise ValidationError("Release Date must be after Reservation Date")

    @api.onchange('reservation_date')
    def _onchange_reservation_date(self):
        """Automatycznie ustawia Release Date 3 miesiące po Reservation Date"""
        for record in self:
            if record.reservation_date:
                reservation_date = fields.Date.from_string(record.reservation_date)
                record.release_date = reservation_date + relativedelta(months=+3)
            else:
                record.release_date = False

    @api.model
    def create(self, vals):
        """Automatyczne ustawienie Release Date przy tworzeniu rekordu"""
        if vals.get('reservation_date') and not vals.get('release_date'):
            reservation_date = fields.Date.from_string(vals['reservation_date'])
            vals['release_date'] = reservation_date + relativedelta(months=+3)
        return super(NumberPool, self).create(vals)

    def write(self, vals):
        """Automatyczne ustawienie Release Date przy aktualizacji Reservation Date"""
        if 'reservation_date' in vals:
            if vals['reservation_date']:
                reservation_date = fields.Date.from_string(vals['reservation_date'])
                vals['release_date'] = reservation_date + relativedelta(months=+3)
            else:
                vals['release_date'] = False
        return super(NumberPool, self).write(vals)