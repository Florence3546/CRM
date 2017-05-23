PT.namespace('Base_adg');
PT.Base_adg = function () {
    var adgroup_id=$('#adgroup_id').val(), campaign_id=$('#campaign_id').val();

    var init_dom=function() {

        $('#contact_consult').hover(function(){
            $('#contact_telephone').stop().animate({'marginLeft':0},300);
        },function(){
            $('#contact_telephone').stop().animate({'marginLeft':-181},100);
        });

        $('#show_adgroup_box').click(function(){
            $('#adgroup_box').modal();

            if($(this).attr('switch')==undefined){
                get_adgroup_by_id();
                PT.sendDajax({'function':'web_get_adgroup_trend','adgroup_id':adgroup_id,'name_space':'Base_adg'});
            }

            $(this).attr('switch',1);
        });

        $('#sync_adg').click(function(){
            PT.show_loading("正在同步当前宝贝数据，可能用时较长");
            PT.sendDajax({'function':'web_sync_current_adg','adg_id':adgroup_id,'camp_id':campaign_id,rpt_days:15});
        });

        $('#item_picture').mouseenter(function(){
            $('#item_picture_big').stop().fadeTo(300,1);
        });

        $('#item_picture_big').mouseleave(function(){
            $('#item_picture_big').stop().fadeTo(300,0).queue(function(next){
                $(this).hide();
                $(this).dequeue();
            });
        });

        //当鼠标经过该元素时，加上hover这个class名称，修复ie中css的hover动作
        $(document).on('mouseover.PT.e','*[fix-ie="hover"]',function(){
            $(this).addClass('hover');
            $(this).mouseout(function(){
                $(this).removeClass('hover');
            });
        });

        //切换天数
        $(document).on('change.PT.e','#adg_select_days',function(e,v){
            $('#adgroup_last_day').val(v);
            $('#adgroup_info_tip').show();
            get_adgroup_by_id();
        });

        $('#adg_base_info .item_pic').on('mouseover',function(){
            $('#adg_base_info .big_item_pic').stop().fadeIn();
        });

        $('#adg_base_info .big_item_pic').on('mouseout',function(){
            $(this).stop().fadeOut();
        });

        $('#set_habit').on('click.modal',function(){
            var dom=template.compile(pt_tpm['habit.tpm.html'])({});
            if(!$('#set_habit_modal').length){
                $('body').append(dom);
            }

            if(PT.get_habit()&&PT.get_habit()['keyword_float_switch']==false){
                $('#keyword_float_switch').removeClass('on off').addClass('off');
            }else{
                $('#keyword_float_switch').removeClass('on off').addClass('on');
            }

            if(PT.get_habit()&&PT.get_habit()['bulk_float_switch']==false){
                $('#bulk_float_switch').removeClass('on off').addClass('off');
            }else{
                $('#bulk_float_switch').removeClass('on off').addClass('on');
            }

            $('#set_habit_modal').modal();
        });

        $(document).on('change.set_habit','#bulk_float_switch input',function(e,statue){
            PT.set_habit({'bulk_float_switch':statue});
            PT.light_msg('设置已生效','请刷新批量优化页面');
        });

        $(document).on('change.set_habit','#keyword_float_switch input',function(e,statue){
            PT.set_habit({'keyword_float_switch':statue});
            PT.light_msg('设置已生效','请刷新选词页面');
        });
    };

    var get_adgroup_by_id=function(){
        var request_data=['default_price',
                          'item.title',
                          'item.price',
                          'item.pic_url',
                          'item.item_id',
                          'campaign.title',
                          'rpt_sum.impressions',
                          'rpt_sum.click',
                          'rpt_sum.ctr',
                          'rpt_sum.cpc',
                          'rpt_sum.paycount',
                          'rpt_sum.favcount',
                          'rpt_sum.conv',
                          'rpt_sum.roi',
                          'rpt_sum.favcount',
                          'rpt_sum.cost',
                          'rpt_sum.pay',
                          'online_status'
                          ];
        request_data=$.toJSON(request_data)
        PT.sendDajax({'function':'web_get_adgroup_by_id','adgroup_id':adgroup_id,data:request_data,call_back:'PT.Base_adg.adgroup_callback','last_day':$('#adg_select_days .dropdown-value').text().match(/\d+/)[0],'auto_hide':0});
    }

    return {
        init: function (){
            init_dom();
        },
        show_adgroup_trend:function(category_list,series_cfg_list){
            PT.draw_trend_chart( 'adgroup_trend_chart', category_list, series_cfg_list);
        },
        adgroup_callback:function(data){
            var dom=template.compile(pt_tpm['adgroup_info_box.tpm.html'])(data);
            $('#adgroup_detail_box').html(dom);
            $('#adgroup_detail_box i.tooltips').tooltip();
            $('#adgroup_info_tip').hide();
        },
        // adgroup_select_call_back:function(day){
        //  $('#adgroup_last_day').val(day);
        //  $('#adgroup_info_tip').show();
        //  get_adgroup_by_id();
        // },
        sync_adg_back:function(msg){
            msg+='即将刷新页面';
            PT.confirm(msg,function(){window.location.reload();});
        }
    }
}();
