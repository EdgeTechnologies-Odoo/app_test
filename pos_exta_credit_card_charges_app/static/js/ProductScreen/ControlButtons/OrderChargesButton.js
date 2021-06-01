odoo.define('pos_exta_credit_card_charges_app.OrderChargesButton', function(require) {
	'use strict';

	const PosComponent = require('point_of_sale.PosComponent');
	const ProductScreen = require('point_of_sale.ProductScreen');
	const { useListener } = require('web.custom_hooks');
	const Registries = require('point_of_sale.Registries');
	const utils = require('web.utils');
    const round_pr = utils.round_precision;

	class OrderChargesButton extends PosComponent {
		constructor() {
			super(...arguments);
			useListener('click', this.onClick);
		}
		async onClick() {
			this.showPopup('PosCreditPopup', {
				title: this.env._t('Select Discount Type'),
			});
		}
	}

	OrderChargesButton.template = 'OrderChargesButton';

	ProductScreen.addControlButton({
		component: OrderChargesButton,
		condition: function() {
			return this.env.pos.config.enable_credit_charges;
		},
	});

	Registries.Component.add(OrderChargesButton);

	return OrderChargesButton;
});