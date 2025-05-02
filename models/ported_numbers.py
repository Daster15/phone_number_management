from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import date


class PortedNumbers(models.Model):
    _name = 'ported.numbers'
    _description = 'Ported Phone Numbers'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'porting_date desc, number'
    _sql_constraints = [
        ('number_owner_unique', 'unique(number, customer_id)', 'Numer musi mieć unikalnego właściciela!'),
        ('number_subscriber_unique', 'unique(number, subscriber_name)', 'Numer musi mieć unikalnego abonenta!'),
    ]

    number = fields.Char(
        string='Numer telefonu',
        required=True,
        size=9,
        tracking=True,
        help="9-cyfrowy numer telefonu bez kodu kraju"
    )

    # Pole właściciela (required, unique per number)
    customer_id = fields.Many2one(
        'res.partner',
        string='Właściciel',
        required=True,
        tracking=True,
        domain=[('is_company', '=', True)],
        ondelete='restrict'
    )

    # Pole abonenta (sprawdzenia w constraintach)
    subscriber_name = fields.Char(
        string='Abonent',
        tracking=True,
        help="Nazwa osoby/instytucji używającej numeru"
    )

    identification_type = fields.Selection(
        selection=[
            ('nip', 'NIP'),
            ('regon', 'REGON'),
            ('pesel', 'PESEL')
        ],
        string='Typ identyfikacji',
        tracking=True
    )

    identification_number = fields.Char(
        string='Numer identyfikacyjny',
        tracking=True
    )

    donor = fields.Char(
        string='Poprzedni operator',
        tracking=True,
        help="Operator przed przeniesieniem numeru"
    )

    porting_date = fields.Date(
        string='Data przeniesienia',
        tracking=True,
        default=fields.Date.today
    )

    return_date = fields.Date(
        string='Data zwrotu',
        tracking=True
    )

    is_active = fields.Boolean(
        string='Aktywny',
        default=True,
        tracking=True,
        help="Czy numer jest obecnie aktywny"
    )

    # Nowe pola
    status_adescom = fields.Selection(
        selection=[
            ('active', 'Aktywny'),
            ('suspended', 'Zawieszony'),
            ('terminated', 'Wypowiedziany')
        ],
        string='Status Adescom',
        tracking=True,
        default='active'
    )

    contract_number = fields.Char(
        string='Numer umowy',
        tracking=True
    )

    order_number = fields.Char(
        string='Numer zamówienia',
        tracking=True
    )

    notes = fields.Text(
        string='Uwagi',
        tracking=True,
        size=200,
        help="Dodatkowe uwagi (max 200 znaków)"
    )

    tags = fields.Many2many(
        'ported.numbers.tags',
        string='Tagi',
        help="Dodatkowe tagi do kategoryzacji"
    )

    # Constraints
    @api.constrains('number')
    def _check_number_format(self):
        for record in self:
            if not record.number.isdigit() or len(record.number) != 9:
                raise ValidationError("Numer telefonu musi składać się z dokładnie 9 cyfr!")

    @api.constrains('subscriber_name', 'is_active')
    def _check_subscriber_required(self):
        for record in self:
            if record.is_active and not record.subscriber_name:
                raise ValidationError("Dla aktywnych numerów pole Abonent jest wymagane!")

    @api.constrains('porting_date', 'return_date')
    def _check_date_consistency(self):
        for record in self:
            if record.return_date and record.porting_date:
                if record.return_date < record.porting_date:
                    raise ValidationError("Data zwrotu nie może być wcześniejsza niż data przeniesienia!")

    @api.constrains('notes')
    def _check_notes_length(self):
        for record in self:
            if record.notes and len(record.notes) > 200:
                raise ValidationError("Uwagi nie mogą przekraczać 200 znaków!")