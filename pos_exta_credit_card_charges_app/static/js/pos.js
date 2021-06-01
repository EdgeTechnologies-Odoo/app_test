odoo.define('pos_exta_credit_card_charges_app.pos', function(require) {
	"use strict";

	const models = require('point_of_sale.models');
	const core = require('web.core');
	const field_utils = require('web.field_utils');
	const rpc = require('web.rpc');
	const session = require('web.session');
	const time = require('web.time');
	const utils = require('web.utils');
	var round_pr = utils.round_precision;
	const PaymentScreen = require('point_of_sale.PaymentScreen');
	const Registries = require('point_of_sale.Registries');
	const OrderWidget = require('point_of_sale.OrderWidget');
	const NumberBuffer = require('point_of_sale.NumberBuffer');
	
	var _t = core._t;

	var _super_posmodel = models.PosModel.prototype;
	models.PosModel = models.PosModel.extend({
		initialize: function (session, attributes) {            
			var journal_model = _.find(this.models, function(model){ return model.model === 'pos.payment.method'; });
			// journal_model.fields.push('credit_charge');
			journal_model.fields.push('is_credit');
			return _super_posmodel.initialize.call(this, session, attributes);
		},
	});
	
	var PaymentSuper = models.Paymentline;
	models.Paymentline = models.Paymentline.extend({
		init: function(parent,options){
			this._super(parent,options);
			this.staystr = 0;
		},

		init_from_JSON: function(json){
			this.amount = json.amount;
			this.staystr = json.get_to_stay;
			this.payment_method = this.pos.payment_methods_by_id[json.payment_method_id];
			this.name = this.pos.payment_methods.name;
		},
		set_staystr: function(entered_charge){
		
		  this.stayStr = entered_charge;
		  this.trigger('change',this);
		},
		
		get_to_stay: function(){
			return this.stayStr;
		},
		export_as_JSON: function() {
			var self = this;
			var loaded = PaymentSuper.prototype.export_as_JSON.apply(this,arguments);
			loaded.get_to_stay = self.get_to_stay();
			return loaded;
		},
	});


	var OrderSuper = models.Order;
	models.Order = models.Order.extend({

		init: function(parent, options) {
			var self = this;
			this._super(parent,options);
			this.set_charges();

		},
		set_charges: function(entered_charge){
		
		  this.charges = entered_charge;
		  this.trigger('change',this);
		},
		
		get_charges: function(){
			if(this.charges){
				return this.charges;
			}else{
				return this.charges = 0;
			}
			
		},
		get_total_with_tax: function() {
			if (this.selected_paymentline){
				if (this.selected_paymentline.payment_method.is_credit){
					if (this.screen_data.value){
						if (this.screen_data.value.name == "ProductScreen"){
							return this.get_total_without_tax() + this.get_total_tax();
						}else{
							return this.get_total_without_tax() + this.get_total_tax() + this.get_charges();		
						}
					}
				}
				else{
					return this.get_total_without_tax() + this.get_total_tax();
				}
			}else{
				return this.get_total_without_tax() + this.get_total_tax();
			}
		},
	   
		
		export_as_JSON: function() {
			var self = this;
			var loaded = OrderSuper.prototype.export_as_JSON.call(this);
			loaded.credit_charge = self.get_charges();
			return loaded;
		},
	});

	const PosCreditOrderWidget = (OrderWidget) =>
		class extends OrderWidget {
			constructor() {
				super(...arguments);
			}
			_updateSummary() {
				let currentOrder = this.env.pos.get_order();
				let a = 0;
				if(this.env.pos.config.enable_credit_charges === true){
                    this.props.order_total = currentOrder.get_total_with_tax();
                    if (this.env.pos.config.charges_type == "per"){
                        a =(currentOrder.get_total_with_tax()*this.env.pos.config.credit_charge)/100    
                    }
                    if (this.env.pos.config.charges_type ==  "fix"){
                        a =(this.env.pos.config.credit_charge)
                    }
                    this.state.credit_charge = a.toFixed(2)
                    // this.state.with_charge = (currentOrder.get_total_with_tax()+a).toFixed(2)
                }
	            const total = this.order ? this.order.get_total_with_tax() : 0;
	            const tax = this.order ? total - this.order.get_total_without_tax() : 0;
	            this.state.total = this.env.pos.format_currency(total);
	            this.state.tax = this.env.pos.format_currency(tax);
	            this.render();
	        }
		};
	Registries.Component.extend(OrderWidget, PosCreditOrderWidget);
	// };

	const PosCreditPaymentScreen = (PaymentScreen) =>
		class extends PaymentScreen {
			constructor() {
				super(...arguments);
				
			}
			addNewPaymentLine({ detail: paymentMethod }) {
				// original function: click_paymentmethods
				if (this.currentOrder.electronic_payment_in_progress()) {
					this.showPopup('ErrorPopup', {
						title: this.env._t('Error'),
						body: this.env._t('There is already an electronic payment in progress.'),
					});
					return false;
				}else{
					var payment_method = null;
					var credit_pay = null;
					for (var i = 0; i < this.env.pos.payment_methods.length; i++ ) {
						if (this.env.pos.payment_methods[i].id === paymentMethod.id ){
							if(this.env.pos.payment_methods[i]['is_credit'] === true){
								payment_method = this.env.pos.payment_methods[i];
								credit_pay = true;
								break;
							}else{
								payment_method = this.env.pos.payment_methods[i];
								break;
							}   
						}
					}
					var order_charges = this.env.pos.get_order().get_charges();
					if(credit_pay == true){
						var order = this.env.pos.get_order();
						var total_paid = order.get_total_paid();
						var due = order.get_due();
						var total = 0
						if(this.env.pos.config.enable_credit_charges){
							if (this.env.pos.config.charges_type == "per"){
								total = due * this.env.pos.config.credit_charge /100;  
							}		
							if (this.env.pos.config.charges_type == "fix"){
								total = (this.env.pos.config.credit_charge)
							}
						}
						this.env.pos.get_order().set_charges(total);
						this.currentOrder.add_paymentline(payment_method);
						NumberBuffer.reset();
						this.payment_interface = payment_method.payment_terminal;
						if (this.payment_interface) {
							this.currentOrder.selected_paymentline.set_payment_status('pending');
						}
					}else{
						this.currentOrder.add_paymentline(paymentMethod);
						NumberBuffer.reset();
						this.payment_interface = paymentMethod.payment_terminal;
						if (this.payment_interface) {
							this.currentOrder.selected_paymentline.set_payment_status('pending');
						}
					}
					return true;
				}
			}
			deletePaymentLine(event) {
				const { cid } = event.detail;
				const line = this.paymentLines.find((line) => line.cid === cid);

				// If a paymentline with a payment terminal linked to
				// it is removed, the terminal should get a cancel
				// request.
				if (['waiting', 'waitingCard', 'timeout'].includes(line.get_payment_status())) {
					line.payment_method.payment_terminal.send_payment_cancel(this.currentOrder, cid);
				}
				this.currentOrder.remove_paymentline(line);
				NumberBuffer.reset();
				this.render();
			}
		};
	Registries.Component.extend(PaymentScreen, PosCreditPaymentScreen);

	return {
		PosCreditOrderWidget,
		PosCreditPaymentScreen,
	};
});
