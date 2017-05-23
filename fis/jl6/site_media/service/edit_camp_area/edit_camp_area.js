define(["template", 'widget/alert/alert',], function(template, alert) {
    "use strict";

    var tpl,
    tpl = __inline('edit_camp_area.html');


    var show = function(options){
        var html,
            obj;

        html = template.compile(tpl)(options);

        obj=$(html);

        $('body').append(obj);

        bind_event(obj,options);

        obj.find('input').attr('checked', false);
        obj.find('.cities').hide();
        if (options.area_ids == 'all') {
            obj.find('.bulk_check').eq(0).click();
        } else {
            var area_list = options.area_ids.split(',');
            for (var i in area_list) {
                obj.find('#region-'+area_list[i]).trigger('click');
            }
        }
        obj.modal();
    }

    var refresh_city_checked_count = function () {
        $('#city_checked_count').html($('#region_selector input[name="city"]:checked').length);
    }

    var bind_event = function(obj,options){
        $('#region_selector').on('click', '.submit', function () {
            //var jq_province_input = $('#region_selector').find('input[name="province"]'),
            //    area_ids = '',
            //    area_names = '';
            //
            //jq_province_input.each(function () {
            //    if ($(this).prop('checked')) {
            //        area_ids += $(this).val() + ',';
            //        area_names+= $(this).parent().attr('title')+',';
            //    } else {
            //        var jq_city_input = $(this).parents('.clearfix:first').find('.cities input:checked');
            //        jq_city_input.each(function () {
            //            area_ids += $(this).val() + ',';
            //            area_names += $(this).parent().attr('title') + ',';
            //        });
            //    }
            //});

            var area_ids = [], area_names = [], provinces = {};
            $('#region_selector input[name="city"]:checked').each(function () {
                if ($(this).parent('.province').length == 0) {
                    var td_obj = $(this).closest('td');
                    if (td_obj.find('input[name="city"]:not(:checked)').length == 0) {
                        var province_obj = td_obj.find('[name="province"]');
                        provinces[province_obj.val()] = province_obj.parent().attr('title');
                        return true;
                    }
                }
                area_ids.push(this.value);
                area_names.push($(this).parent().attr('title'));
            });
            for (var area_id in provinces) {
                area_ids.push(area_id);
                area_names.push(provinces[area_id]);
            }
            area_ids = area_ids.join(',');
            area_names = area_names.join(',');

            if(area_ids == ''){
                alert.show('地域不能为空');
                return;
            }
            obj.modal('hide');
            if(area_ids==options.area_ids+","){
                return false;
            }

            options.onChange(area_ids,area_names);
        });

        $(document).on('click', function (e) {
            if($('.details').find(e.target).length){
                return;
            }
            $('.cities').hide();
        });

        $('#region_selector').on('click', '.summary', function () {
            var current_city = $(this).next();
            $('.cities').each(function () {
                if (this == current_city[0]) {
                    current_city.fadeToggle();
                }else{
                    $(this).hide();
                }
            });
        });

        $('#region_selector').on('click', '.bulk_check', function () {
            var is_check = parseInt($(this).val())? true: false;
            $('#region_selector').find('input[type="checkbox"]').each(function () {
                $(this).prop('checked', is_check);
            });
            refresh_city_checked_count();
            return false;
        });

        $('#region_selector').on('click', 'input[name="area"]', function () {
            var now_check=this.checked,
                kids=$(this).parents('th').nextAll().find('input');
            kids.each(function(){
                if (this.checked!=now_check) {
                    $(this).prop('checked',now_check);
                }
            });
            refresh_city_checked_count();
        });

        $('#region_selector').on('click', 'input[name="province"]', function () {
            var now_check=this.checked,
                selected_str='',
                kids=$(this).parent().next().find('input[name="city"]');
            kids.each(function(){
                if (this.checked!=now_check) {
                    this.checked=now_check;
                }
            });
            if (now_check) {
                selected_str = '('+ kids.length +')';
            } else {
                selected_str = '';
            }
            $(this).parents('td').find('.selected-count').text(selected_str);
            refresh_city_checked_count();
            //$(this).trigger('change');
        });

        //$('#region_selector').on('change', 'input[name="province"]', function () {
        //    var jq_tr = $(this).parents('tr'),
        //        jq_area = jq_tr.find('input[name="area"]'),
        //        //jq_provinces = jq_tr.find('input[name="province"]'),
        //        jq_checked_input = jq_tr.find('input[name="province"]:checked');
        //    //if (jq_checked_input.length == jq_provinces.length) {
        //    //    jq_area.prop('checked', true);
        //    //}else{
        //    //    jq_area.prop('checked', false);
        //    //}
        //    if (jq_checked_input.length > 0) {
        //        jq_area.prop('checked', true);
        //    } else {
        //        jq_area.prop('checked', false);
        //    }
        //});

        $('#region_selector').on('click', 'input[name="city"]', function () {
            var jq_td = $(this).parents('td'),
                jq_province = jq_td.find('input[name="province"]'),
                //jq_cities = jq_td.find('input[name="city"]'),
                jq_checked_input = jq_td.find('input[name="city"]:checked');
            //if (jq_checked_input.length == jq_cities.length) {
            //    jq_province.prop('checked', true);
            //}else{
            //    jq_province.prop('checked', false);
            //}
            if (jq_checked_input.length > 0) {
                jq_province.prop('checked', true);
            } else {
                jq_province.prop('checked', false);
            }
            jq_province.trigger('change');
            var count_str = '';
            if (jq_checked_input.length) {
                count_str = '('+ jq_checked_input.length +')';
            }
            jq_td.find('.selected-count').text(count_str);
            refresh_city_checked_count();
            var jq_tr = $(this).closest('tr'),
                jq_area = jq_tr.find('input[name="area"]'),
                jq_checked_input = jq_tr.find('input[name="city"]:checked');
            if (jq_checked_input.length > 0) {
                jq_area.prop('checked', true);
            } else {
                jq_area.prop('checked', false);
            }
        });

        obj.on('hidden.bs.modal',function(){
            obj.remove();
        });

        $('#region_selector').on('change', 'input[name="selector"]', function () {
            var selector_dict = {
                level_1: ["19", "461", "300", "311", "417", "260", "509", "519", "40", "50", "373", "380", "200", "214", "73", "85", "532", "441", "413"],
                level_2: ["137", "138", "402", "336", "339", "238", "166", "167", "256", "257", "261", "262", "269", "272", "275", "277", "512", "526", "46", "8", "379", "384", "386", "389", "150", "160", "288", "70", "71",
                    "75", "90", "91", "105", "497", "112", "414"],
                level_3: ["126", "129", "133", "135", "140", "141", "394", "395", "405", "586", "295", "303", "304", "308", "314", "239", "179", "259", "266", "273", "511", "514", "522", "523", "528", "41", "51", "2", "13",
                    "16", "369", "371", "374", "377", "381", "382", "392", "151", "152", "156", "205", "210", "215", "216", "224", "230", "233", "282", "286", "76", "77", "81", "89", "121", "122", "98", "104", "443", "451",
                    "416", "59", "366", "356", "485"],
                level_4: ["144", "396", "398", "401", "404", "337", "344", "346", "306", "241", "242", "246", "176", "265", "518", "529", "42", "44", "45", "48", "6", "7", "10", "11", "370", "390", "148", "159", "191",
                    "192", "207", "213", "218", "220", "223", "227", "285", "290", "79", "80", "84", "86", "88", "448", "450", "452", "453", "454", "457", "458", "460", "490", "502", "118", "466", "412", "415"],
                level_5: ["132", "134", "403", "597", "598", "321", "328", "587", "588", "589", "590", "297", "298", "305", "309", "310", "312", "235", "237", "244", "249", "169", "170", "173", "174", "178", "180", "181",
                    "183", "622", "3", "4", "5", "9", "12", "14", "15", "17", "18", "372", "376", "146", "147", "149", "153", "155", "157", "161", "162", "163", "164", "621", "185", "186", "188", "193", "196", "198", "203",
                    "623", "624", "199", "202", "228", "232", "585", "280", "283", "289", "291", "292", "293", "69", "74", "78", "83", "87", "609", "610", "611", "612", "613", "614", "615", "616", "617", "618", "619", "620",
                    "93", "94", "96", "99", "100", "102", "106", "107", "108", "581", "580", "440", "442", "444", "445", "447", "455", "456", "459", "600", "601", "489", "491", "492", "499", "500", "503", "504", "506", "507",
                    "605", "606", "607", "608", "110", "111", "113", "117", "582", "583", "584", "464", "465", "467", "468", "469", "470", "407", "408", "409", "410", "411", "53", "54", "55", "56", "57", "60", "61", "62", "63",
                    "65", "66", "67", "579", "361", "367", "592", "593", "594", "595", "596", "352", "353", "354", "591", "472", "473", "476", "477", "478", "479", "480", "483", "484", "486", "602", "603", "604", "625", "626"],
                extreme_cold: [],
                very_cold: [],
                cold: [],
                cool: ["468", "592", "594", "595"],
                comfort: ["137", "321", "586", "587", "588", "589", "590", "295", "297", "300", "303", "304", "306", "308", "310", "314", "234", "235", "237", "238", "239", "241", "242", "244", "246", "249", "165", "166",
                    "167", "169", "170", "173", "174", "176", "178", "179", "180", "181", "183", "622", "380", "381", "384", "389", "444", "454", "600", "601", "489", "490", "491", "492", "497", "499", "500", "502", "503",
                    "506", "507", "608", "110", "112", "113", "584", "464", "465", "466", "467", "469", "470", "53", "54", "55", "57", "60", "579", "361", "366", "367", "593", "596", "352", "473", "483", "485", "486", "603"],
                hot: ["19", "461", "132", "140", "144", "394", "395", "396", "401", "402", "403", "404", "598", "328", "336", "337", "339", "344", "346", "298", "305", "309", "311", "312", "417", "255", "256", "257", "259",
                    "260", "261", "262", "265", "266", "269", "272", "273", "275", "277", "509", "511", "512", "523", "528", "41", "45", "46", "50", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14",
                    "15", "16", "17", "18", "369", "371", "376", "379", "382", "386", "390", "392", "157", "162", "185", "186", "188", "191", "192", "193", "198", "200", "203", "207", "210", "623", "624", "199", "202", "213",
                    "215", "218", "223", "224", "228", "230", "232", "585", "285", "69", "70", "75", "76", "77", "78", "80", "81", "83", "84", "85", "86", "88", "89", "90", "91", "121", "122", "609", "612", "613", "614", "615",
                    "616", "617", "618", "619", "620", "94", "96", "98", "100", "102", "104", "105", "106", "107", "108", "581", "532", "440", "441", "442", "443", "445", "447", "448", "450", "451", "452", "453", "455", "456",
                    "457", "458", "459", "460", "504", "605", "606", "607", "111", "117", "118", "582", "583", "408", "409", "410", "411", "412", "413", "414", "415", "416", "56", "59", "61", "62", "63", "65", "66", "67", "353",
                    "354", "356", "591", "472", "476", "477", "478", "479", "480", "602", "604", "625", "626", "599", "576"],
                high: ["126", "129", "133", "134", "135", "138", "141", "398", "405", "597", "514", "518", "519", "522", "526", "529", "40", "42", "44", "48", "51", "370", "372", "373", "374", "377", "146", "147", "148", "149",
                    "150", "151", "152", "153", "155", "156", "159", "160", "161", "163", "164", "621", "196", "205", "214", "216", "220", "227", "233", "280", "282", "283", "286", "288", "289", "290", "291", "292", "293", "71",
                    "73", "74", "79", "87", "610", "611", "93", "99", "580", "407", "484"]
            };
            $('#region_selector table.area_table input:checkbox').prop('checked', false);
            $('#region_selector table.area_table .selected-count').empty();
            var city_level_ischecked = $('#region_selector input.city_level:checked').length > 0,
                temperature_ischecked = $('#region_selector input.temperature:checked').length > 0,
                select_citys1 = $('#region_selector input.city_level:checked').map(function () {return selector_dict[$(this).data('type')];}).get(),
                select_citys2 = $('#region_selector input.temperature:checked').map(function () {return selector_dict[$(this).data('type')];}).get(),
                result = [];
            if (city_level_ischecked && temperature_ischecked) {
                var temp_obj = {};
                $(select_citys1).each(function (i, city_id) {
                    temp_obj[city_id] = 1;
                });
                $(select_citys2).each(function (i, city_id) {
                    if (temp_obj[city_id]) {
                        result.push(city_id);
                    }
                });
            } else if (city_level_ischecked) {
                result = select_citys1;
            } else if (temperature_ischecked) {
                result = select_citys2;
            }
            $.each(result, function (i, city_id) {
                $('#region-'+city_id).trigger('click');
            });
            $('#city_checked_count').html(result.length);
        })
    }

    return {
        show: show
    }
});
