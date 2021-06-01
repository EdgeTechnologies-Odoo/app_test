odoo.define('pos_exta_credit_card_charges_app.PosCreditPopup', function (require) {
	'use strict';

	var core = require('web.core');
	const { useState, useRef } = owl.hooks;
	const { useListener } = require('web.custom_hooks');
	const PosComponent = require('point_of_sale.PosComponent');
	const Registries = require('point_of_sale.Registries');
	const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
	var QWeb = core.qweb;
	const utils = require('web.utils');
    const round_pr = utils.round_precision;
	var _t = core._t;

	class PosCreditPopup extends AbstractAwaitablePopup {
		constructor() {
			super(...arguments);
			let currentOrder = this.env.pos.get_order();
			let a = 0;
            let plines = currentOrder.get_paymentlines();

            for(var i = 0; i < this.env.pos.payment_methods.length; i++) {
                if(this.env.pos.config.enable_credit_charges === true){
                    this.props.order_total = currentOrder.get_total_with_tax();
                    if (this.env.pos.config.charges_type == "per"){
                        a =(currentOrder.get_total_with_tax()*this.env.pos.config.credit_charge)/100    
                    }
                    if (this.env.pos.config.charges_type ==  "fix"){
                        a =(this.env.pos.config.credit_charge)
                    }
                    this.props.credit_charge = (a).toFixed(2)
                    this.props.with_charge = (currentOrder.get_total_with_tax()+a).toFixed(2)
                }
            }
		}

		click_confirm(){
			this.trigger('close-popup');
		}
	}

	PosCreditPopup.template = 'PosCreditPopup';
	PosCreditPopup.defaultProps = {
        confirmText: 'Ok',
        cancelText: 'Cancel',
        title: '',
        body: '',
        list: [],
        startingValue: '',
    };

	Registries.Component.add(PosCreditPopup);

	return PosCreditPopup;
});
