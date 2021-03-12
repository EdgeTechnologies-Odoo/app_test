# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class InvoiceDetails(models.Model):
    _name = 'invoice.details'
    _description = 'Invoice Details'

    invoice_id = fields.Many2one('account.move', string="Invoice Status")
    date = fields.Datetime("Invoice Date")
    recurring_id = fields.Many2one('recurring.invoices')
    total_amount = fields.Float("Invoice Amount")


class RecurringInvoice(models.Model):
    _name = 'recurring.invoices'
    _description = "Recurring Invoice"

    name = fields.Char('Name')
    partner_id = fields.Many2one('res.partner',string='Partner')
    first_date = fields.Datetime('Start Date')
    recurring_interval = fields.Integer('Recurring Interval',default=1)
    interval_type = fields.Selection([('days', 'Days'),
                                     ('weeks', 'Weeks'),
                                     ('months', 'Months')], default='days')
    recurring_number = fields.Integer('Recurring Number of Calls',default=1)
    state = fields.Selection([
        ('new', 'New'),
        ('running', 'In Progress'),
        ('done','Done'),
        ('Cancelled', 'Cancelled'),
    ], string='State',copy=False ,default="new")
    active = fields.Boolean(string='Active',default="True")
    reviewer_ids = fields.Many2one('res.users', "Observer", default=lambda self: self.env.user, required=True,
                                   readonly=True)
    scheduled_idss = fields.One2many('scheduled.invoices','recurring_invoice_id')
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user)
    total = fields.Float('Amount Total')
    due_date = fields.Date('Due Date')
    cron_id = fields.Many2one('ir.cron', 'Cron Ref', help="Scheduler which runs on recurring invoice")
    inv_details_ids = fields.One2many('invoice.details','recurring_id', string="Invoice Details", help="show auto generated invoice details.")
    invoice_id = fields.Many2one('account.move','Account Invoice')


    def cancel_button(self):
        self.state = 'Cancelled'
                
class ScheduleInvoice(models.Model):
    _name = 'scheduled.invoices'
    _description = "Schedule Invoice"

    recurring_invoice_id = fields.Many2one('recurring.invoices')
    schedule_date = fields.Date('Schedule Date')
    invoice = fields.Char('Invoice')
