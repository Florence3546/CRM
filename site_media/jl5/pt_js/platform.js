PT.namespace('Platform');
PT.Platform = function () {

    var camp_id = $('#campaign_id').val(),
        jq_modal = $('#modal_camp_platform');

    var init_dom = function() {
        $(document).on('click', '.edit_platform', function() {
            if ($(this).data('is_lock')){
                init_modal($(this).data('platform'));
            } else {
                PT.show_loading('正在获取计划投放平台');
                PT.sendDajax({'function':'web_get_camp_platform', 'camp_id':camp_id});
            }
        });

        $("input[name='pc_insite_nonsearch']").on('change', function(){
            var jq_inputs = $("input[name='pc_outsite_nonsearch']");
            if (parseInt($(this).val()) == 1) {
                jq_inputs.attr('disabled', false).removeClass('non_cursor');
                jq_inputs.parent().removeClass('non_cursor');
            } else {
                jq_inputs.eq(0).attr('checked', 'checked');
                jq_inputs.attr('disabled', 'disabled').addClass('non_cursor');
                jq_inputs.parent().addClass('non_cursor');
            }
        });

        $('#modal_camp_platform').on('click', '.submit', function(){
            var outside_discount = jq_modal.find('#outside_discount').val(),
                mobile_discount = jq_modal.find('#mobile_discount').val(),
                jq_inputs = jq_modal.find('input[type="radio"]:checked'),
                result_data = {};
            jq_inputs.each(function () {
                result_data[$(this).attr('name')] = parseInt($(this).val());
            });
            result_data.outside_discount = parseInt(outside_discount);
            result_data.mobile_discount = parseInt(mobile_discount);

            var no_update = true;
            var old_obj = $('.edit_platform').data().platform;
            delete old_obj["pc_insite_search"];
            for(var key in old_obj){
                //当任意一个值被修改，则需要提交
                if(result_data[key]!=old_obj[key]){
                    no_update = false;
                    break;
                }
            }

            //如果没有被修改，直接返回，无需提交
            if(no_update){
                $('#modal_camp_platform').modal('hide');
                return false;
            }
            $(this).data('modify_data', result_data);
            PT.show_loading('正在设置计划投放平台');
            PT.sendDajax({
                'function':'web_update_camp_platform',
                'camp_id':camp_id,
                'platform_dict':$.toJSON(result_data)
                });
            return true;
        });
    };

    var init_modal = function(pform){
        for (var prop in pform) {
            jq_modal.find('[name="'+prop+'"]').eq(pform[prop]).attr('checked', true);
        }
        jq_modal.find('#outside_discount').val(pform.outside_discount);
        jq_modal.find('#mobile_discount').val(pform.mobile_discount);
        var is_set_nonsearch = jq_modal.attr('is_set_nonsearch');
        if (is_set_nonsearch != '1') {
            $(".can_set").remove();
            $('.not_set').show();
        }
        $('#outside_discount').slider({"from":1,
            "to":200,
            'step':1,
            "range":'min',
            "skin":"plastic",
            "limits":false,
            "dimension":"&nbsp;%",
            'scale': [1, '|', 51, '|', 101, '|', 150, '|', 200]
        });
        $('#mobile_discount').slider({"from":1,
            "to":400,
            'step':1,
            "range":'min',
            "skin":"plastic",
            "limits":false,
            "dimension":"&nbsp;%",
            'scale': [1, '|', 101, '|', 201, '|', 301, '|', 400]
        });

        if (pform.pc_insite_nonsearch === 0){
            $("input[name='pc_insite_nonsearch']").eq(0).trigger('change');
        }
        jq_modal.modal();

    };

    return {

        init: function (){
            init_dom();
        },

        get_platform_back:function(camp_id, platform) {
            if (platform) {
                $('.edit_platform').data({'is_lock': 1, 'platform': platform});
                init_modal(platform);
            } else {
                PT.alert('淘宝接口不稳定，请稍后再试');
            }

        },

        update_platform_back:function(camp_id, is_success, msg_list) {
            PT.hide_loading();
            if (is_success) {
                // var camp_id = $('#camp_platform_title').data('camp_id'),
                var platform = jq_modal.find('.submit').data('modify_data');
                $('.edit_platform').data('platform', platform);
                $('#modal_camp_platform').modal('hide');
                PT.light_msg('修改计划投放平台', '修改成功');
            } else {
                PT.alert('修改计划投放平台失败');
            }
        }
    };
}();
