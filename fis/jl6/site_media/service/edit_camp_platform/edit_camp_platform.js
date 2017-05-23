define(["template","jslider"], function(template) {
    "use strict";

    var tpl;

    tpl = __inline('edit_camp_platform.html');

    var show=function(options){
        var html,
            obj;

        html = template.compile(tpl)(options);

        obj=$(html);

        $('body').append(obj);

        obj.modal();

        obj.find('.slider_input[name=outside_discount]').slider({"from":1,
            "to":200,
            'step':1,
            "range":'min',
            "skin":"platform",
            "limits":false,
            'scale': [1, 100, 200],
            onstatechange: function(value){
                var parent_div = $('.slider_input[name=outside_discount]').closest('div');
                parent_div.find('.show_discount').html(value);
                parent_div.find('.update_discount').val( value);
                parent_div.find('.jslider-bg .v').css('width',parseFloat(value*100)/200+"%");
            }
        });

        obj.find('.slider_input[name=mobile_discount]').slider({"from":1,
            "to":400,
            'step':1,
            "range":'min',
            "skin":"platform",
            "limits":false,
            'scale': [1, 100, 200, 300, 400],
            onstatechange: function(value){
                var parent_div = $('.slider_input[name=mobile_discount]').closest('div');
                parent_div.find('.show_discount').html(value);
                parent_div.find('.update_discount').val( value);
                parent_div.find('.jslider-bg .v').css('width',parseFloat(value*100)/400+"%");
            }
        });

        obj.find('.btn-primary').on('click',function(){

            if(!check_value($('.update_discount').eq(0))||!check_value($('.update_discount').eq(1))){
                return false;
            }

            var data={};

            data['pc_outsite_nonsearch'] = obj.find('[name=pc_outsite_nonsearch]:checked').val();
            data['pc_insite_nonsearch'] = obj.find('[name=pc_insite_nonsearch]:checked').val();
            data['outside_discount'] = obj.find('[name=outside_discount]').val();
            data['yd_outsite'] = obj.find('[name=yd_outsite]:checked').val();
            data['pc_outsite_search'] = obj.find('[name=pc_outsite_search]:checked').val();
            data['mobile_discount'] = obj.find('[name=mobile_discount]').val();
            data['yd_insite'] = obj.find('[name=yd_insite]:checked').val();
            data['pc_insite_search'] = 1;

            obj.modal('hide');

            var no_update = true;
            for(var key in options){
                //当任意一个值被修改，则需要提交
                if(key!='onChange'&&parseInt(data[key])!=options[key]){
                    no_update = false;
                    break;
                }
            }
            if(no_update){
                return false;
            }
            options.onChange(data);
        });

        obj.on('hidden.bs.modal',function(){
            obj.remove();
        });

        obj.on('shown.bs.modal', function(){
            $('[data-toggle="tooltip"]').tooltip({html: true});
            $("input[name='pc_insite_nonsearch']").off('change');
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
            $("input[name='pc_insite_nonsearch']:checked").trigger('change');

            var can_set_nonsearch = $(this).attr('can_set_nonsearch');
            if (can_set_nonsearch != '1') {
                $(".can_set").hide();
                $('.not_set').show();
            }
        })

        //修改折扣
        obj.find('.edit_discount').click(function(){
            var par_obj = $(this).parent();
            var cur_value = par_obj.find('.show_discount').html();
            par_obj.find('.show_discount').addClass('hide');
            par_obj.find('.update_discount').removeClass('hide').focus().val(cur_value);
            $(this).addClass('hide');
        });

        obj.find('.update_discount').blur(function(){
            if(!check_value($(this))){
                return false;
            }
            var par_obj = $(this).parent();
            par_obj.find('.show_discount').html(parseInt($(this).val()));
            par_obj.find('.show_discount').removeClass('hide');
            par_obj.find('.update_discount').tooltip('hide').addClass('hide');
            par_obj.find('.edit_discount').removeClass('hide');
            update_discount($(this));
        });

        obj.find('.update_discount').on('keyup',function(){
            update_discount($(this));
        });

        obj.find('.update_discount').focus(function(){
            $(this).tooltip('hide');
        });

        //修改折扣，变动滑杆
        var update_discount = function(obj){
            if(!check_value(obj)){
                var range = $(obj).attr('range');
                $(obj).tooltip({title:'请输入'+range+'的数字',placement:'top',trigger:'manual'});
                $(obj).tooltip('show');
                return false;
            }
            var cur_value = $(obj).val();
            if(cur_value==""){
                return false;
            }
            var slider = $(obj).parents('td').find('.slider_input');
            slider.slider('value',cur_value);
        };

        //验证输入数据的合法性
        var check_value = function(obj){
            var cur_value = $(obj).val();
            var range = $(obj).attr('range');
            var max = range.substr(2,range.length);
            if(!Number(cur_value)||parseInt(cur_value)>parseInt(max)||parseInt(cur_value)<=0){
                return false;
            }
            return true;
        }
    }

    return {
        show: show
    }
});
