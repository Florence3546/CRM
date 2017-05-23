PT.namespace('Area');
PT.Area = function () {
    var camp_id = $('#campaign_id').val();

    var init_dom = function(){

        $(document).on('click', '.edit_area', function() {
            if ($(this).data('is_lock')) {
                init_area_modal($(this).data('area_ids'));
            } else {
                PT.show_loading('正在获取投放地域');
                PT.sendDajax({'function':'web_get_camp_area', 'camp_id':camp_id});
            }
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
            var is_check = parseInt($(this).val())? false: true;
            $('#region_selector').find('input[name="area"]').each(function () {
                $(this).attr('checked', is_check);
                $(this).trigger('click');
            });
            return false;
        });

        $('#region_selector').on('click', 'input[name="area"]', function () {
            var now_check=this.checked,
                kids=$(this).parents('th').nextAll().find('input');
            kids.each(function(){
                if (this.checked!=now_check) {
                    $(this).trigger('click');
                }
            });
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
            $(this).trigger('change');
        });

        $('#region_selector').on('change', 'input[name="province"]', function () {
            var jq_tr = $(this).parents('tr'),
                jq_area = jq_tr.find('input[name="area"]'),
                jq_provinces = jq_tr.find('input[name="province"]'),
                jq_checked_input = jq_tr.find('input[name="province"]:checked');
            if (jq_checked_input.length == jq_provinces.length) {
                jq_area.attr('checked', true);
            }else{
                jq_area.attr('checked', false);
            }
        });

        $('#region_selector').on('change', 'input[name="city"]', function () {
            var jq_td = $(this).parents('td'),
                jq_province = jq_td.find('input[name="province"]'),
                jq_cities = jq_td.find('input[name="city"]'),
                jq_checked_input = jq_td.find('input[name="city"]:checked');
            if (jq_checked_input.length == jq_cities.length) {
                jq_province.attr('checked', true);
            }else{
                jq_province.attr('checked', false);
            }
            jq_province.trigger('change');
            var count_str = '';
            if (jq_checked_input.length) {
                count_str = '('+ jq_checked_input.length +')';
            }
            jq_td.find('.selected-count').text(count_str);
        });

        $('#region_selector').on('click', '.submit', function () {
            var jq_province_input = $('#region_selector').find('input[name="province"]'),
                area_ids = '';
            jq_province_input.each(function () {
                if ($(this).attr('checked') == 'checked') {
                    area_ids += $(this).val() + ',';
                } else {
                    var jq_city_input = $(this).parents('.clearfix:first').find('.cities input:checked');
                    jq_city_input.each(function () {
                        area_ids += $(this).val() + ',';
                    });
                }
            });

            if (area_ids === '') {
                PT.alert('请先选择投放地域');
                return;
            }
            area_ids = area_ids.slice(0, -1);
            if($('.edit_area').data().area_ids==area_ids){
                $('#modal_camp_area').modal('hide');
                return;
            }
            $('#camp_area_title').data('area_ids', area_ids);
            PT.sendDajax({'function':'web_update_camp_area', 'camp_id': camp_id, 'area_ids': area_ids});
            PT.show_loading('正在修改计划投放地域');
            // $('.modal-backdrop.fade.in').css('z-index', 1060);
            return false;
        });
    };

    var init_area_modal = function (area_ids) {
        var jq_modal = $('#modal_camp_area');
        jq_modal.find('input').attr('checked', false);
        jq_modal.find('.cities').hide();
        jq_modal.modal();
        if (area_ids == 'all') {
            jq_modal.find('.bulk_check').eq(0).click();
        } else {
            var area_list = area_ids.split(',');
            for (var i in area_list) {
                jq_modal.find('#region-'+area_list[i]).trigger('click');
            }
        }
    };

    return {
        init:function(){
            init_dom();
        },

        get_area_back:function(camp_id, area_ids){
            if (area_ids) {
                $('.edit_area').data({'is_lock': 1, 'area_ids': area_ids});
                init_area_modal(area_ids);
            } else {
                PT.alert('淘宝接口不稳定，请稍后再试');
            }
        },

        update_area_back:function(camp_id, is_success, msg_list) {
            // $('.modal-backdrop.fade.in').css('z-index', 1040);
            if (is_success) {
                var area_ids = $('#camp_area_title').data('area_ids');
                $('.edit_area').data('area_ids', area_ids);
                $('#modal_camp_area').modal('hide');
                PT.light_msg('修改计划投放地域','修改成功');
            } else {
                PT.alert('淘宝接口不稳定，请稍后再试');
            }
        }


    };

}();
