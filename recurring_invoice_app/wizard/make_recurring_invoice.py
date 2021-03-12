# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta

class RecurringInvoice(models.TransientModel):
	_name = 'recurring.invoice'
	_description = "Recurring Invoice" 

	name = fields.Char('Name',readonly=True, copy=False)
	partner_id = fields.Many2one('res.partner',string='Partner', default=lambda self: self.env.user.partner_id.id)
	first_date = fields.Datetime('Start Date', default=fields.Datetime.now)
	recurring_interval = fields.Integer('Recurring Interval',default=1)
	interval_type = fields.Selection([('days', 'Days'),
									 ('weeks', 'Weeks'),
									 ('months', 'Months')], default='days')
	recurring_number = fields.Integer('Number of Calls for Recurring',default=1)
	state = fields.Selection([
		('new', 'New'),
		('running', 'In Progress'),
	], string='State',copy=False ,default="new", index=True, track_visibility='onchange', track_sequence=5)
	active = fields.Boolean(string='Active',default="True")
	reviewer_ids = fields.Many2one('res.users', "Observer", default=lambda self: self.env.user, required=True,
								   readonly=True)
	scheduled_idss = fields.One2many('scheduled.invoice','recurring_invoice_id')

	user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user,options="{'no_create_edit': True}")
	total = fields.Float('Amount Total')
	due_date = fields.Date('Due Date')
	date_invoice = fields.Date('Invoice Date')
	
	@api.model
	def default_get(self,fields):
		res = super(RecurringInvoice, self).default_get(fields)
		active_ids = self._context.get('active_ids')
		account_invoice = self.env['account.move'].browse(self._context.get('active_id')) 
		
		if account_invoice.state == "draft":
			name = account_invoice.id
		else:
			name = account_invoice.name
		res['name'] = name
		res['partner_id'] = account_invoice.partner_id.id
		res['total'] = account_invoice.amount_total
		res['due_date'] = account_invoice.invoice_date_due
		res['date_invoice'] = account_invoice.invoice_date
		return res


	@api.onchange('recurring_number','recurring_interval')
	def check_recurring_number(self):
		if self.recurring_number <= 0 or self.recurring_interval <=0:
			raise ValidationError('Please enter valid Number of Recurring Invoice & Recurring Invoice Interval...!')


	def confirm_recurring(self):
		first_date = self.first_date
		account_invoice = self.env['account.move'].browse(self._context.get('active_id'))
		recurring_id = self.env['recurring.invoices']
		rec_state = self.update({'state': 'running'})
		if self.interval_type == 'days':
			firstdate = first_date.date()
			terms = []
			list_date = []
			list_date.append(firstdate)
			interval = self.recurring_interval
			for num in range(0,self.recurring_number):
				date = firstdate + timedelta(interval)
				interval += self.recurring_interval
				list_date.append(date)
				terms.append((0, 0, {
								'recurring_invoice_id': self.scheduled_idss.recurring_invoice_id.id,
								'schedule_date': list_date[num],
								'invoice' : self.name,
								}))
				
			new_record = self.env['recurring.invoices'].create({
				'name':self.name,
				'partner_id':self.partner_id.id,
				'interval_type':self.interval_type,
				'first_date': first_date,
				'recurring_interval':self.recurring_interval,
				'recurring_number':self.recurring_number,
				'state':rec_state,
				'scheduled_idss': terms,
				'invoice_id': account_invoice.id,
			})
			recurring_id = new_record

		if self.interval_type == 'weeks':
			firstdate = first_date.date()
			terms = []
			list_date = []
			list_date.append(firstdate)
			interval = self.recurring_interval 
			for num in range(0,self.recurring_number):
				date = firstdate + timedelta(interval*7)
				interval += self.recurring_interval
				list_date.append(date)
				terms.append((0, 0, {
								'recurring_invoice_id': self.scheduled_idss.recurring_invoice_id.id,
								'schedule_date': list_date[num],
								'invoice' : self.name,
								}))

			new_record = self.env['recurring.invoices'].create({
				'name':self.name,
				'partner_id':self.partner_id.id,
				'interval_type':self.interval_type,
				'first_date':first_date,
				'recurring_interval':self.recurring_interval,
				'recurring_number':self.recurring_number,
				'state':rec_state,
				'scheduled_idss': terms,
				'invoice_id': account_invoice.id,
			})
			recurring_id = new_record                      

		if self.interval_type == 'months':
			firstdate = first_date.date()
			terms = []
			list_date = []
			list_date.append(firstdate) 
			months = self.recurring_interval
			for num in range(0,self.recurring_number):
				date = firstdate + relativedelta(months=months)
				months += self.recurring_interval
				list_date.append(date)
				terms.append((0, 0, {
								'recurring_invoice_id': self.scheduled_idss.recurring_invoice_id.id,
								'schedule_date': list_date[num],
								'invoice' : self.name,
								}))

			new_record = self.env['recurring.invoices'].create({
				'name':self.name,
				'partner_id':self.partner_id.id,
				'interval_type':self.interval_type,
				'first_date': first_date,
				'recurring_interval':self.recurring_interval,
				'recurring_number':self.recurring_number,
				'state':rec_state,
				'scheduled_idss': terms,
				'invoice_id': account_invoice.id,
			})
			recurring_id = new_record


		Cron = self.env['ir.cron']
		order_model = self.env.ref('recurring_invoice_app.model_recurring_invoice').id
		vals = {
			'name': self.name,
			'model_id': order_model,
			'interval_number':self.recurring_interval,
			'interval_type': self.interval_type,
			'numbercall':self.recurring_number,
			'nextcall': first_date,
			'priority': 6,
			'user_id': self.reviewer_ids.id,
			'state': 'code',
			'code': 'model.valide_process('+str(recurring_id.id)+')'
		}
		ir_cron = Cron.create(vals)
		if ir_cron:
			recurring_id.update({'cron_id': ir_cron.id, 'state': 'running'})


	def valide_process(self, rec_id):
		recurring = self.env['recurring.invoices'].browse(rec_id)
		remaining = recurring.cron_id.numbercall
		
		default = {'state':'draft'}
		state = 'running'
		# the recurring is over and we mark it as being done
		if remaining == 1:
			state = 'done'

		account_invoice_id = recurring.invoice_id
		new_invoice = account_invoice_id.copy(default=default)
		self.env['invoice.details'].create({
			'invoice_id':new_invoice.id,
			'date': recurring.cron_id.nextcall,
			'recurring_id':recurring.id,
			'total_amount':new_invoice.amount_total
		})
		recurring.state = state

	def _cron_recurring_invoice_alerts(self):
		current_date = fields.Date.today().strftime('%Y-%m-%d')
		recurring_invoice_ids = self.env['recurring.invoices'].search([('state','=','running')])
		for invoice in recurring_invoice_ids:
			if invoice.scheduled_idss:
				schedule_date_lst = []
				for sched in invoice.scheduled_idss:
					schedule_date = sched.schedule_date - timedelta(days=1)
					schedule_date = schedule_date.strftime('%Y-%m-%d')
					schedule_date_lst.append(schedule_date)
				if current_date in schedule_date_lst:
					template_id =  self.env.ref('recurring_invoice_app.recurring_invoice_remainder_template')
					values = template_id.generate_email(self.id, fields=None)
					values['email_from'] = self.env.user.email_formatted
					values['email_to'] = invoice.partner_id.email
					values['author_id'] = self.env.user.partner_id.id
					values['subject'] = 'Reminder Mail for Recurring Invoice'
					main_body = """<p> Dear %s , <br/><br/>
									This is a Reminder Mail For Your Recurring Invoice Payment:<br/><br/>
									Your recurring Payment of amount '%s' on invoice '%s', will be due to at '%s' <br/><br/>
									Regards,<br/>
									%s </p>
										 """%(invoice.partner_id.name,invoice.invoice_id.amount_total,invoice.name, invoice.first_date, self.env.user.name)
					values['body_html'] = main_body
					mail_mail_obj = self.env['mail.mail']
					msg_id = mail_mail_obj.sudo().create(values)
					if msg_id:
						msg_id.sudo().send()

class ScheduleInvoice(models.TransientModel):
	_name = 'scheduled.invoice'
	_description = "Schedule Invoice" 

	recurring_invoice_id = fields.Many2one('recurring.invoice')
	schedule_date = fields.Date('Schedule Date')
	invoice = fields.Char('Name')
