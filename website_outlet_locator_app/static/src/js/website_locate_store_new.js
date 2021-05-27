odoo.define('website_outlet_locator_app.website_locate_store_new',function(require){
"use strict";
    $(document).ready(function() {
    
    var ajax=require('web.ajax');
    var core=require('web.core');
    var _t=core._t;

    var markers=[];
    var mapinfo=[];
    
    var checkstatus=null;
    var vals={};

    var mapProp;
    var map;
    var show_locator;
    var location_data;
    var bounds;

    var load_count=0;
    var shop_count=0; 
    var search_radius=0;

    $('.loader').show();

    // store_json();
    var store = {
        store_json: function(){
            $('.loader').show();
            ajax.jsonRpc('/store/vals','call', {}).then(function(data){
                if(data){
                    location_data = data;
                    search_radius = data.map_search_radius;
                    initialize_stores(location_data);
                }else{
                    alert(_t("No Store Found."));
                }
                $('.loader').hide();
            });
        },

        reset_store_location: function(){
            var self = this;
            $('.store-not-found').hide();
            $('#search-input').val('');

            location_data = JSON.parse(location_data);
            map.setZoom(location_data.map_init.map_zoom);
            map.setCenter(new google.maps.LatLng(location_data.map_init.latitude,location_data.map_init.longitude));
            if(checkstatus!=null){
                mapinfo[checkstatus].close(map,markers[checkstatus]);
                $('#'+(checkstatus+1)+'').find('.all-stores').removeClass('selected');
                checkstatus=null;
            }
            $('.store-ul').show();
            self.markers_on_map();
            self.show_all_shop_list();
        },


        search_by_address_init: function(){
            var addr_dict={};
            var search_string = document.getElementById("search-input");
            if(search_string){
                search_string= search_string.value
                
                search_string = search_string.toLowerCase()
                
                $('.store-not-found').hide();
                
                hide_info_window();
                get_shop_nearest_address(search_string);
            }
        },
        
        get_shop_nearest_address: function(search_string){
            ajax.jsonRpc('/search/vals','call', {'search_string' : search_string}).then(function(data){
                if(data){
                    var old_data = JSON.parse(data);
                    var latitude=0;
                    var longitude=0;
                    var geocoder = new google.maps.Geocoder();
                    
                    var count =0;
                    $('.loader').show();
                    bounds = new google.maps.LatLngBounds();
                    
                    geocoder.geocode(
                        {'address':search_string},
                        function(results,status){
                            // var count =0;
                            $('.loader').hide();
                            
                            if(results) {
                                if(status == google.maps.GeocoderStatus.OK)
                                {
                                    latitude=results[0].geometry.location.lat();
                                    longitude=results[0].geometry.location.lng();
                                    if (old_data.map_stores_data) {
                                        $.each(old_data.map_stores_data,function(key,value){
                                            if(value.found == true){
                                                show_store_data(parseInt(key));
                                                count++;
                                            }else{
                                                hide_store_data(parseInt(key));
                                            }
                                        });
                                        if(count==0)
                                        {
                                            $('.store-not-found').show();
                                            $('.store-ul').hide();
                                        }
                                        $(".store-head").text(""+count+"");
                                    }
                                }
                                else
                                {
                                    $('.store-not-found').show();
                                    $('.store-ul').hide();
                                }
                            }
                            else
                            {
                                $('.store-not-found').show();
                                $('.store-ul').hide();
                            }
                        }
                    );
                } 

            });
        },
        

        show_store_data: function(key){
            key = key - 1;
            if (markers.hasOwnProperty(key)) {
                if(!markers[key].getVisible()){
                    markers[key].setVisible(true);
                }
                bounds.extend(markers[key].getPosition());
                key = key + 1;
                $('#'+(key)+'').removeClass('hide-shop');
            }
        },
        
        hide_store_data: function(key){
            key = key -1;
            if(markers[key].getVisible()){
                markers[key].setVisible(false);
            }
            key = key + 1;
            $('#'+(key)+'').addClass('hide-shop');
        },

        hide_info_window: function(){
            if(checkstatus!=null){
                mapinfo[checkstatus].close(map,markers[checkstatus]);
                $('#'+(checkstatus+1)+'').find('.all-stores').removeClass('selected');
                checkstatus=null;
            }
        },

        initialize_stores: function(data){
            var final_data = JSON.parse(data)
            var mapProp={
                center : new google.maps.LatLng(final_data.map_init.latitude,final_data.map_init.longitude),zoom:final_data.map_init.map_zoom,mapTypeId:final_data.map_init.map_type
            };
            map = new google.maps.Map(document.getElementById("googleMap"),mapProp);
            
            main_map_view(map,final_data.map_stores_data);
            
            $('.store-lists').append("<ul class='store-not-found' style='display:none;'>No Result Found.</ul>");
        },
        
        main_map_view: function(map,map_stores_data){
            $(".store-head").text(""+ Object.keys(map_stores_data).length + "");
            shop_count=((Object.keys(map_stores_data).length)-1);
            Object.keys(map_stores_data).forEach(function(key) {
            }); 

            $.each(map_stores_data,function(key,values){
                var icon = {
                    url: '/website_outlet_locator_app/static/src/img/marker.png',
                    scaledSize: new google.maps.Size(28,36)
                }
                markers.push(new google.maps.Marker({position:new google.maps.LatLng(values.latitude,values.longitude),title:values.name,map:map,icon:icon,animation:google.maps.Animation.DROP}));
                key=parseInt(key);
                key= key - 1;
                var info=store_data(values);
                
                mapinfo.push(new google.maps.InfoWindow({content:info}));
                shop_list_details(key,values,info);
                if (markers.hasOwnProperty(key)) {
                    
                    markers[key].addListener('click', function() {
                        if(checkstatus!=null)
                        {
                            mapinfo [checkstatus].close(map,markers[checkstatus]);
                            $('#'+(checkstatus+1)+'').find('.all-stores').removeClass('selected');
                            checkstatus=null;
                        }
                        mapinfo[key].open(map,markers[key]);
                        if(!markers[key].getVisible()){
                            markers[key].setVisible(true);
                        }
                        $('#'+(key+1)+'').find('.all-stores').addClass('selected');
                        checkstatus=key;
                        var temp=$(".store-lists").offset().top;
                        $(".store-lists").animate({
                            scrollTop:0},1,function(){$(".store-lists").animate({
                                scrollTop:$('#'+(key+1)+'').offset().top-temp
                            },1);
                        });
                    });
                }
            });
        },


        store_data: function(store){
            var addr='';
            if(store.image){
                addr+='<div class="store-image"><img style="max-height:70px;" src="'+store.image+'"/></div>';
            }
            if(store.name){
                addr+='<div class="store-name">'+store.name+'</div>';
            }
            if(store.address) {
                addr+='<div class="store-address">'+store.address+'</div>';
            }
            if(store.contact){
                addr+='<div class="store-details"> <b>Contact: </b>'+store.contact+'</div>';
            }
            if(store.email){
                addr+='<div class="store-details"> <b>Email: </b> <a href="Email:'+store.email+'">'+store.email+'</a></div>';
            }
            addr+='</div>'
            return addr;
        },

        shop_list_details: function(key,store,info){
            if (markers.hasOwnProperty(key)) {
                $('.store-lists ul').append("<li id="+(key+1)+" class=''>\
                    <div class='all-stores'>\
                      <input type='hidden' name='store-id' value="+store.store_id+"></input>\
                      <div class='row'>\
                        <div class='list-image col-md-2 col-sm-4 col-xs-4'>\
                            <img style='height: 38px' src='/website_outlet_locator_app/static/src/img/marker.png'/>\
                        </div>\
                        <div class='store-info col-md-10'>"+info+"</div>\
                       </div>\
                    </div></li>"
                );

                $('li#'+key+'').find('.store-info img').remove();

                $('#'+(key+1)+'').on('click',function(){
                    if(checkstatus!=null){
                        mapinfo[checkstatus].close(map,markers[checkstatus]);
                        $('#'+(checkstatus+1)+'').find('.all-stores').removeClass('selected');checkstatus=null;
                    }
                    $('#'+(key+1)+'').find('.all-stores').addClass('selected');
                    map.setZoom(18);
                    markers[key].setVisible(true);
                    map.setCenter(markers[key].getPosition());
                    mapinfo[key].open(map,markers[key]);
                    checkstatus=key;   
                });
            }
        },
        
        

        markers_on_map: function(){
            $.each(markers,function(index,value)
                {if(!value.getVisible()){
                    value.setVisible(true);
                }
            });
        },
        
        show_all_shop_list: function(){
            $('.store-lists ul li').removeClass('hide-shop');
            $(".store-head").text(""+Object.keys(location_data.map_stores_data).length+"");
            shop_count=((Object.keys(location_data.map_stores_data).length)-1);
        }
    }

        $('.reset-loc').on('click',function(){
            var self = this;
            reset_store_location();
        });


        $('.search-store').on('click',function(){
            search_by_address_init();
        });

        $('#search-input').keypress(function(e)
            {
            if(e.which==13){
                search_by_address_init();
            }
        });

    });

});