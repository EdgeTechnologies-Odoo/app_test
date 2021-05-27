odoo.define('website_outlet_locator_advance_app.website_locate_store',function(require){
"use strict";

	var ajax=require('web.ajax');
	var core=require('web.core');
	var _t=core._t;

	var markers=[];
	var mapinfo=[];
	var ids = []
	
	var checkstatus=null;

	var mapProp;
	var map;
	var show_locator;
	var location_data;
	var bounds;

	var load_count=0;
	var shop_count=0; 
	var search_radius=0;

	var c_lat = '';
	var c_lng = '';
	
	var vals={};

	var selected_category = false;
	var browse_string = '';
	var clnt = {};
	var categ_value = new Set();
	var categ_ids = [];
	var removed_categs = [];
	var outputArray = [];

	var sAnimation = require('website.content.snippets.animation');

	sAnimation.registry.affixMenu = sAnimation.Class.extend({
		selector: '.store-locations',
		custom_events: {
			'field_changed': '_onFieldChanged',
		},
		events: {
			'click .select_categ' : '_onInputClick',
			'click .o_delete' : '_onDeleteTag',
			'change .select_categ' : '_onChangeField',
		},

		init: function(parent, editableMode) {
			this._super.apply(this, arguments);
			var self = this;
			this.lastSetValue = undefined;
			this.value;
			this._autocompleteSources = [];
			this.isDirty = false;
			this._addAutocompleteSource(this._search, {placeholder: _t('Loading...'), order: 1});
		},

		_addAutocompleteSource: function (method, params) {
			this._autocompleteSources.push({
				method: method,
				placeholder: (params.placeholder ? _t(params.placeholder) : _t('Loading...')) + '<i class="fa fa-spinner fa-spin pull-right"></i>' ,
				validation: params.validation,
				loading: false,
				order: params.order || 999
			});
			this._autocompleteSources = _.sortBy(this._autocompleteSources, 'order');
		},

		_isSameValue: function (value) {
			return this.value === value;
		},

		_setValue: function (value, options) {
			var self = this;
			// we try to avoid doing useless work, if the value given has not
			// changed.  Note that we compare the unparsed values.
			if (this.lastSetValue === value || (this.value === false && value === '')) {
				return Promise.resolve();
			}
			this.lastSetValue = value;
			// ids.push(value.id)
			categ_ids.push(value.display_name)

			$('.o_field_many2one').before("<div class='badge badge-pill badge-secondary category_badge' t-att-data-id="+value.id+">\
				<span class='o_badge_text' t-att-id="+value['id']+" t-att-title="+value['display_name']+">\
				<span role='img'/><span>"+value['display_name']+"</span></span>\
				<a href='#' class='fa fa-times o_delete' title='Delete' aria-label='Delete'/>\
				</div>"
			)

			if(value){
				$('.store-not-found').hide();
				self.hide_info_window();
				self.get_shop_nearest_address(browse_string,categ_ids,clnt);
			}	
			else{
				self.reset_store_location();
			}

			
			return new Promise(function (resolve, reject) {
				var changes = {};
				changes[self.name] = value;
				self.trigger_up('field_changed', {
					dataPointID: self.dataPointID,
					changes: changes,
					viewType: self.viewType,
					doNotSetDirty: options && options.doNotSetDirty,
					notifyChange: !options || options.notifyChange !== false,
					allowWarning: options && options.allowWarning,
					onSuccess: resolve,
					onFailure: reject,
				});
			});
		},

		_onDeleteTag: function (event) {
			event.preventDefault();
			event.stopPropagation();
			this._removeTag($(event.target).parent().attr('t-att-data-id'));
		},

		_removeTag: function (id) {
			var remove_tg = $('.o_badge_text')
			var self = this;
			for(var i = 0; i < ids.length; i++){
				if (ids[i] == parseInt(id))
				{
					ids.splice(i, 1);
				}
			}
			
			for (var i = 0; i <= remove_tg.length; i++){
				if (parseInt($(remove_tg[i]).attr('t-att-id')) == parseInt(id)){
					categ_ids.splice(categ_ids.indexOf($.trim($(remove_tg[i]).text())), 1);
					$(remove_tg[i]).parent().remove();
				}
			}

			$('.store-not-found').hide();
			self.hide_info_window();
			self.get_shop_nearest_address(browse_string,categ_ids,clnt);
		},
		_onFieldChanged: function (ev) {
			if (ev.target === this) {
				ev.initialEvent = this.lastInitialEvent;
				return;
			}
			ev.stopPropagation();
			// changes occured in an editable list
			var changes = ev.data.changes;
			// save the initial event triggering the field_changed, as it will be
			// necessary when the field triggering this event will be reset (to
			// prevent it from re-rendering itself, formatting its value, loosing
			// the focus... while still being edited)
			this.lastInitialEvent = undefined;
			if (Object.keys(changes).length) {
				this.lastInitialEvent = ev;
				this._setValue({
					operation: 'UPDATE',
					id: ev.data.dataPointID,
					data: changes,
				}).then(function () {
					if (ev.data.onSuccess) {
						ev.data.onSuccess();
					}
				}).guardedCatch(function () {
					if (ev.data.onFailure) {
						ev.data.onFailure();
					}l
				});
			}
		},
		_bindAutoComplete: function () {
			var self = this;
			// avoid ignoring autocomplete="off" by obfuscating placeholder, see #30439
			if ($.browser.chrome && this.$input.attr('placeholder')) {
				this.$input.attr('placeholder', function (index, val) {
					return val.split('').join('\ufeff');
				});
			}
			this.$input.autocomplete({
				source: function (req, resp) {
					_.each(self._autocompleteSources, function (source) {
						// Resets the results for this source
						source.results = [];

						// Check if this source should be used for the searched term
						if (!source.validation || source.validation.call(self, req.term)) {
							source.loading = true;
							
							// Wrap the returned value of the source.method with a promise
							// So event if the returned value is not async, it will work
							Promise.resolve(source.method.call(self, req.term)).then(function (results) {
								source.results = results;
								source.loading = false;
								resp(self._concatenateAutocompleteResults());
							});
						}
					});
				},
				select: function (event, ui) {
					// we do not want the select event to trigger any additional
					// effect, such as navigating to another field.

					event.stopImmediatePropagation();
					event.preventDefault();

					var item = ui.item;
					ids.push(item.id)
					self.floating = false;
					if (item.id) {
						self.reinitialize({id: item.id, display_name: item.name});
					} else if (item.action) {
						item.action();
					}
					return false;
				},
				focus: function (event) {
					event.preventDefault(); // don't automatically select values on focus
				},
				open: function (event) {
					self._onScroll = function (ev) {
						if (ev.target !== self.$input.get(0) && self.$input.hasClass('ui-autocomplete-input')) {
							self.$input.autocomplete('close');
						}
					};
					window.addEventListener('scroll', self._onScroll, true);
				},
				close: function (event) {
					// it is necessary to prevent ESC key from propagating to field
					// root, to prevent unwanted discard operations.
					if (event.which === $.ui.keyCode.ESCAPE) {
						event.stopPropagation();
					}
					if (self._onScroll) {
						window.removeEventListener('scroll', self._onScroll, true);
					}
				},
				autoFocus: true,
				html: true,
				minLength: 0,
				delay: this.AUTOCOMPLETE_DELAY,
			});
			this.$input.autocomplete("option", "position", { my : "left top", at: "left bottom" });
			this.autocomplete_bound = true;
		},

		reinitialize: function (value) {
			this.isDirty = false;
			this.floating = false;
			return this._setValue(value);
		},
		_concatenateAutocompleteResults: function () {
			var results = [];
			_.each(this._autocompleteSources, function (source) {
				if (source.results && source.results.length) {
					results = results.concat(source.results);
				} else if (source.loading) {
					results.push({
						label: source.placeholder
					});
				}
			});
			return results;
		},

		start: function () {
			var self = this;
			this.$input = $('.select_categ');
			var def = this._super.apply(this, arguments);
			window.gMapsCallback = function(){
				self.store_json();
			}
			this.floating = false;
			this.store_json();

			$('.loader').show();
			$('.shop_loc').hide();

			$('.reset-loc').on('click',function(){
				self.reset_store_location();
			});
			$(this.$input).on('change', function() {
				let value = $(this).val();
				if(value){
					value = value.toLowerCase()
					$('.store-not-found').hide();
					self.hide_info_window();
					selected_category = value;
					self.get_shop_nearest_address(browse_string,selected_category,clnt);
				}
				else{
					self.reset_store_location();
				}
			});

			$('.search-store').on('click',function(){
				self.search_by_address_init();
			});

			$('#search-input').keyup(function(e){
				if(e.which==13){
					self.search_by_address_init();
				}
				else{
					if(e.which == 8)
					{
						let ss = $('#search-input').val();
						if(ss.length == 0){
							location.reload();
						}
					}
				}
			});
			if (!this.autocomplete_bound) {
				this._bindAutoComplete();
			}
			return def;
		},

		_getSearchBlacklist: function () {
			var self = this;
			return ids;
		},

		_search: function (search_val) {
			var self = this;
			var def = new Promise(function (resolve, reject) {
				var domain = [];
				var blacklisted_ids = self._getSearchBlacklist();
				if (blacklisted_ids.length > 0) {
					domain.push(['id', 'not in', blacklisted_ids]);
				}
				self._rpc({
					route: "/category/data",
		            params: {
		                domain: domain,
		            },}).then(function (result) {
					var new_value;
					var categ_values = _.map(result, function (x) {
						new_value = x;
					});
					// possible selections for the m2o
					var values = _.map(new_value, function (x) {
						return {
							label: _.str.escapeHTML(x[1].trim()) || data.noDisplayContent,
							value: x[1],
							name: x[1],
							id: x[0],
						};
					});

					resolve(values);
				});
			});
			return def;
		},

		init_map: function(data) {
			var final_data = JSON.parse(data);
			var mapProp={
				center : new google.maps.LatLng(final_data.map_init.latitude,final_data.map_init.longitude),zoom:final_data.map_init.map_zoom,mapTypeId:final_data.map_init.map_type
			};
			map = new window.google.maps.Map(document.getElementById("googleMap"),mapProp);
		},

		_onInputClick: function () {
			if (this.$input.autocomplete("widget").is(":visible")) {
				this.$input.autocomplete("close");
			} else if (this.floating) {
				this.$input.autocomplete("search"); // search with the input's content
			} else {
				this.$input.autocomplete("search", ''); // search with the empty string
			}
		},

		store_json: function () {
			$('.loader').show();
			var self = this;
			let c_data = self.get_client_location();
			var $def = ajax.jsonRpc('/store/vals','call', {}).then(function(data){
				if(data){
					location_data = data;
					search_radius = data.map_search_radius;
					location_data =  JSON.parse(data);
					let loc_data = self.locations_add_distance(location_data.map_stores_data);
					var locationInfo = loc_data.sort(function(a, b){
						if (parseFloat(a.distance) < parseFloat(b.distance)) {
							return -1;
						}

						if (parseFloat(a.distance) > parseFloat(b.distance)) {
							return 1;
						}
						return 0;
					});
					self.add_ids(locationInfo)
					self.init_map(data);
					let dictionary = Object.assign({}, ...locationInfo.map((x) => ({[x.id]: x})));
					location_data.map_stores_data = dictionary;
					self.initialize_stores(location_data);
				}else{
					alert(_t("No Store Found."));
				}
				
				$('.loader').hide();
			});
		},

		add_ids : function(locationInfo) {
			let cnt = 1;
			$.each(locationInfo,function(key,values){
				values['id'] = cnt;
				cnt += 1;
			});
		},

		locations_add_distance: function(location_data) {
			let loc_data = []
			$.each(location_data,function(key,values){
				let p1 = new window.google.maps.LatLng(parseFloat(values.latitude), parseFloat(values.longitude));
				let p2 = new window.google.maps.LatLng(parseFloat(c_lat),parseFloat(c_lng));
				let dis = (window.google.maps.geometry.spherical.computeDistanceBetween(p1, p2) / 1000).toFixed(2);
				values['distance'] = dis;
				values['found'] = true;
				loc_data.push(values);
			});
			return loc_data;
		},

		locations_search_distance : function(location_data,latlng) {
			let loc_data = []
			$.each(location_data,function(key,values){
				let p1 = new window.google.maps.LatLng(parseFloat(values.latitude), parseFloat(values.longitude));
				let p2 = new window.google.maps.LatLng(parseFloat(latlng.lat),parseFloat(latlng.lng));
				let dis = (window.google.maps.geometry.spherical.computeDistanceBetween(p1, p2) / 1000).toFixed(2);
				values['distance'] = dis;
				if (values.loc_category && selected_category && values.loc_category == selected_category){
					values['found'] = true;
				}
				else{
					if (!selected_category){
						values['found'] = true;
					} 
				}
				loc_data.push(values);
			});
			return loc_data;
		},

		reset_store_location : function(){
			// $('.store-not-found').hide();
			location.reload();
			$('#search-input').val('');

			this.markers_on_map();
			// $('.store-not-found').hide();
			// $('#search-input').val('');
			// $('.li-item').show();
			// $('.select_categ').val('');
			// browse_string = '';
			// selected_category = false;
			// clnt = {};
			
			// $('.store-ul').show();
			// this.show_all_shop_list();
		},

		search_by_address_init : function(){
			var self = this;
			var addr_dict={};
			var search_string = document.getElementById("search-input");
			if(search_string){
				search_string= search_string.value
				
				search_string = search_string.toLowerCase()
				
				$('.store-not-found').hide();
				
				self.hide_info_window();
				browse_string = search_string;
				self.get_shop_nearest_address(browse_string,selected_category,clnt);
			}
		},

		get_shop_nearest_address : function(search_string,categs,latlng){
			var self = this;
			this._rpc({
				route: '/search/vals',
				params: {'search_string' : search_string,'categs' : categs},
			}).then(function(data){
				if(data){
					var old_data = JSON.parse(data);
					$('.loader').show();
					if(latlng && latlng.lat){
						let loc_data = self.locations_search_distance(old_data.map_stores_data,latlng);
						// let locationInfo = loc_data.sort(compare);
						let locationInfo = loc_data.sort(function(a, b){
							if (parseFloat(a.distance) < parseFloat(b.distance)) {
								return -1;
							}

							if (parseFloat(a.distance) > parseFloat(b.distance)) {
								return 1;
							}
							return 0;
						});

						self.add_ids(locationInfo)
						let dictionary = Object.assign({}, ...locationInfo.map((x) => ({[x.id]: x})));
						old_data.map_stores_data = dictionary;
						$( ".li-item" ).remove();
						self.main_map_view(map,dictionary);
					}
					if (old_data.map_stores_data) {
						self.hide_show_store(old_data.map_stores_data);
					}
					else
					{
						$('.store-not-found').show();
						$('.store-ul').hide();
						$('.loader').hide();
					}
				} 
			});
		},

		hide_show_store : function(records) {
			var count =0;
			$.each(records,function(key,value){
				if(value.found == true){
					count++;
					$('#'+(value.store_id)+'').show();
				}
				if(value.found == false){
					$('#'+(value.store_id)+'').hide();
				}
			});
			$(".store-head").text(""+count+"");
			$('.loader').hide();
			if(count == 0)
			{
				$('.store-not-found').show();
				$('.store-ul').hide();
				$('.li-item').hide();
			}
			else{
				$('.store-ul').show();
			}
		},

		hide_info_window : function(){
			if(checkstatus!=null){
				if (mapinfo[checkstatus-1]){ 
					mapinfo[checkstatus-1].close(map,markers[checkstatus]);
					$('#'+(checkstatus)+'').find('.all-stores').removeClass('selected');
					checkstatus=null;
				}
			}
		},

		compare : function(a, b) {
			if (parseFloat(a.distance) < parseFloat(b.distance)) {
				return -1;
			}

			if (parseFloat(a.distance) > parseFloat(b.distance)) {
				return 1;
			}
			return 0;
		},

		get_client_location : function() {
			let client_lat = '';
			let client_lng = '';
			let client_address = '';
			let loc = {} ;
			if (navigator.geolocation) {
				navigator.geolocation.getCurrentPosition(function(position) {
					client_lat = position.coords.latitude;
					client_lng = position.coords.longitude;
					c_lat = client_lat;
					c_lng = client_lng;
					var pos = {
					  lat: position.coords.latitude,
					  lng: position.coords.longitude
					};
					return pos
				});
			} 
			else{
				alert("Geolocation is not supported by this browser")
			}
			
		},

		initialize_stores : function(data){
			var final_data = data;
			var self = this;
			self.main_map_view(map,final_data.map_stores_data);

			var input = document.getElementById('search-input');
			var autocomplete = new window.google.maps.places.Autocomplete(input,{types: ['geocode']});
			autocomplete.addListener('place_changed', function() {
				var place = autocomplete.getPlace();
				if (!place.geometry) {
					return;
				}
		  
				var address = '';
				if (place.address_components) {
					address = [
					  (place.address_components[0] && place.address_components[0].short_name || ''),
					  (place.address_components[1] && place.address_components[1].short_name || ''),
					  (place.address_components[2] && place.address_components[2].short_name || '')
					].join(' ');
				}
				let country = '';
				let zip_code = '';
				// Location details
				for (var i = 0; i < place.address_components.length; i++) {
					if(place.address_components[i].types[0] == 'postal_code'){
						zip_code = place.address_components[i].long_name;
					}
					if(place.address_components[i].types[0] == 'country'){
						country = place.address_components[i].long_name;
					}
				}
				let formatted_address = place.formatted_address;
				let lat = place.geometry.location.lat();
				let lng = place.geometry.location.lng();
				clnt = {
					'lat' : lat ,
					'lng' : lng ,
					'formatted_address' : formatted_address ,
				}
				self.get_shop_nearest_address(browse_string,selected_category,clnt);
			});

			$('.store-lists-card').append("<ul class='store-not-found' style='display:none;'>No Result Found.</ul>");
		},
		
		main_map_view : function(map,map_stores_data){
			var self = this;
			$(".store-head").text(""+ Object.keys(map_stores_data).length + "");
			shop_count=((Object.keys(map_stores_data).length)-1);

			$.each(map_stores_data,function(key,values){
				var icon = {
					url: '/website_outlet_locator_advance_app/static/src/img/marker.png',
					scaledSize: new window.google.maps.Size(28,36)
				}
				markers.push(new window.google.maps.Marker({position:new window.google.maps.LatLng(values.latitude,values.longitude),title:values.name,map:map,id:values.id,icon:icon,animation:google.maps.Animation.DROP}));
				var info=self.store_data(values);
				// const infowindow = new window.google.maps.InfoWindow({content:info})
				mapinfo.push(new window.google.maps.InfoWindow({content:info}));
				
				self.shop_list_details(key,values,info);
				if (markers.hasOwnProperty(key)) {
					markers[key].addListener('click', function() {

						if(checkstatus!=null)
						{
							mapinfo [checkstatus].close(map,markers[checkstatus]);
							$('#'+(checkstatus+1)+'').find('.all-stores').removeClass('selected');
							checkstatus=null;
						}
						infowindow.open(map, markers);
						mapinfo[key].open(map,markers[key]);
						if(!markers[key].getVisible()){
							markers[key].setVisible(true);
						}
						$('#'+(key+1)+'').find('.all-stores').addClass('selected');
						checkstatus=key;
						var temp=$(".store-lists-card").offset().top;
						$(".store-lists-card").animate({
							scrollTop:0},1,function(){$(".store-lists-card").animate({
								scrollTop:$('#'+(key+1)+'').offset().top-temp
							},1);
						});
					});
				}
			});
		},


		store_data : function(store){
			var self = this;
			var addr='';
			if(store.name){
				addr+='<div class="store-name">'+store.name+'</div>';
			}
			if(store.address) {
				addr+='<div class="store-address">'+store.address+'</div>';
			}
			if(store.contact){
				addr+='<div class="store-details"> <b>Contact: </b>'+store.contact+'</div>';
			}
			if(store.web_address){
				addr+='<div class="store-details"> <b>Website: </b>'+store.web_address+'</div>';
			}
			if(store.email){
				addr+='<div class="store-details"> <b>Email: </b> <a href="Email:'+store.email+'">'+store.email+'</a></div>';
			}
			if(store.distance != 'NaN'){
				addr+='<div class="store-details" style="padding-bottom: 2%;"> <b>Distance: </b>'+store.distance+'km </div>';
			}
			addr+='</div>'
			return addr;
		},

		shop_list_details : function(key,store,info){
			var self = this;
			let web_address = '#';
			if(store.web_address){
				web_address = store.web_address;
			}
			if(store.image){
				$('.store-lists-card ul').append("<li id="+(store.store_id)+" class='li-item col-md-12'>\
					<div class='all-stores'><span value="+(web_address)+">\
						<input type='hidden' name='store-id' value="+store.store_id+"></input>\
						<span class='store-website'>"+web_address+"</span>\
						<div class='row col-sm-12' style='margin: 0px !important;'>\
							<div class='list-image col-md-2 col-sm-4 col-xs-4'>\
								<img style='height: 38px;' src='"+store.image+"'/>\
							</div>\
						<div class='store-info col-md-10'>"+info+"</div>\
					   </div>\
					</span></div></li>"
				);
			}else{
				$('.store-lists-card ul').append("<li id="+(store.store_id)+" class='li-item col-md-12'>\
					<div class='all-stores'><span value="+(web_address)+">\
						<span class='store-website'>"+web_address+"</span>\
						<input type='hidden' name='store-id' value="+store.store_id+"></input>\
						<div class='row'>\
							<div class='list-image col-md-2 col-sm-4 col-xs-4'>\
								<img style='height: 38px;' src='/website_outlet_locator_advance_app/static/src/img/marker.png'/>\
							</div>\
							<div class='store-info col-md-10'>"+info+"</div>\
						</div>\
					</span></div></li>"
				);
			}
			$('#'+(store.store_id)+'').on('click',function(){
				for (var marker in markers){
					var info = "";
					if(checkstatus!=null){
						mapinfo[marker].close(map,store[checkstatus]);
						$('#'+(checkstatus)+'').find('.all-stores').removeClass('selected');checkstatus=null;
					}
					$('#'+(store.store_id)+'').find('.all-stores').addClass('selected');
					map.setZoom(18);
					markers[marker].setVisible(true);
					info=self.store_data(store);
					if (markers[marker]['title'] == store.name){
						
						map.setCenter(markers[marker].getPosition());
						mapinfo[marker].open(map,markers[marker]);
						checkstatus=store.store_id;
					}
					var infowindow = new google.maps.InfoWindow({
						id: store.store_id,
						content: info,
					});

					(function (marker) {
						marker.addListener("click", () => {
							if (marker['title'] == store['name']){
								infowindow.open(map, marker);
							}
						});
					})(markers[marker]);
				}
			});
		},

		markers_on_map: function(){
			$.each(markers,function(index,value)
				{if(!value.getVisible()){
					value.setVisible(true);
				}
			});
		},
		
		show_all_shop_list : function(){
			var self = this;
			$('.store-lists-card ul li').removeClass('hide-shop');
			$(".store-head").text(""+Object.keys(location_data.map_stores_data).length+"");
			shop_count=((Object.keys(location_data.map_stores_data).length)-1);
		},
	});
});