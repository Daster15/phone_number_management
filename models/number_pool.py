# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
from dateutil.relativedelta import relativedelta


class NumberPool(models.Model):
    _name = 'number.pool'
    _description = 'Phone Number Pool'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'number'

    # Fields
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

    status = fields.Selection([
        ('free', 'Free'),
        ('occupied', 'Occupied'),
        ('reserved', 'Reserved'),
        ('grace', 'Grace Period')
    ], string='Status', default='free', tracking=True)

    # Dates
    reservation_date = fields.Date(string='Reservation Date', tracking=True)
    activation_date = fields.Date(string='Activation Date', tracking=True)
    release_date = fields.Date(string='Release Date', tracking=True)

    # Relationships
    reseller_id = fields.Many2one('res.partner', string='Reseller', tracking=True)
    customer_id = fields.Many2one('res.partner', string='Customer', tracking=True)
    subscriber_name = fields.Char(string='Subscriber Name', tracking=True)

    # History
    history_line_ids = fields.One2many(
        'number.history',
        'number_id',
        string='History Lines',
        readonly=True
    )

    # Additional fields
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

    # Constraints
    @api.constrains('number')
    def _check_number_format(self):
        for record in self:
            if not record.number.isdigit() or len(record.number) != 9:
                raise ValidationError("Number must be 9 digits")

    @api.constrains('reservation_date', 'activation_date', 'release_date')
    def _check_dates_consistency(self):
        for record in self:
            if record.reservation_date and record.activation_date:
                if record.activation_date < record.reservation_date:
                    raise ValidationError("Activation date cannot be before reservation date")
            if record.activation_date and record.release_date:
                if record.release_date < record.activation_date:
                    raise ValidationError("Release date cannot be before activation date")

    # Actions
    def action_reserve(self):
        for record in self:
            if record.status != 'free':
                raise UserError("Only free numbers can be reserved!")

            record.write({
                'status': 'reserved',
                'reservation_date': fields.Date.today(),
                'customer_id': self.env.context.get('default_customer_id'),
                'subscriber_name': self.env.context.get('default_subscriber_name')
            })
            self._create_history_record(record, 'reserved')

    def action_activate(self):
        for record in self:
            if record.status not in ('free', 'reserved'):
                raise UserError("Only free or reserved numbers can be activated!")

            record.write({
                'status': 'occupied',
                'activation_date': fields.Date.today()
            })
            self._create_history_record(record, 'occupied')

    def action_release(self):
        for record in self:
            if record.status == 'free':
                raise UserError("Number is already free!")

            self._create_history_record(record, 'free')
            record.write({
                'status': 'free',
                'subscriber_name': False,
                'customer_id': False,
                'release_date': fields.Date.today(),
                'reservation_date': False,
                'activation_date': False
            })

    def _create_history_record(self, record, new_status):
        self.env['number.history'].create({
            'number_id': record.id,
            'subscriber_name': record.subscriber_name,
            'customer_id': record.customer_id.id,
            'old_status': record.status,
            'new_status': new_status,
            'change_date': fields.Datetime.now(),
            'reservation_date': record.reservation_date,
            'activation_date': record.activation_date,
            'release_date': record.release_date,
            'adescom_status': record.adescom_status,
            'contract_number': record.contract_number
        })

    # Automatic expiration of reservations
    def _cron_expire_reservations(self):
        expire_date = fields.Date.today() - relativedelta(months=3)
        expired = self.search([
            ('status', '=', 'reserved'),
            ('reservation_date', '<', expire_date)
        ])
        expired.action_release()


class NumberHistory(models.Model):
    _name = 'number.history'
    _description = 'Number History'
    _order = 'change_date desc'

    number_id = fields.Many2one('number.pool', string='Number', required=True, ondelete='cascade')
    subscriber_name = fields.Char(string='Subscriber Name')
    customer_id = fields.Many2one('res.partner', string='Customer')

    old_status = fields.Selection(related='number_id.status', string='Previous Status')
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