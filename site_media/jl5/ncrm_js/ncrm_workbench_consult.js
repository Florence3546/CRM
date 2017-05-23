PT.namespace('NcrmWorkbench_sh');
PT.NcrmWorkbench_sh = function() {

    var init_dom = function() {

        //日期时间选择器
        require(['dom', 'gallery/datetimepicker/1.1/index'], function(DOM, Datetimepicker) {
            new Datetimepicker({
                start: '#order_end_starttime',
                timepicker: false,
                closeOnDateSelect : true
            });
            new Datetimepicker({
                start: '#order_end_endtime',
                timepicker: false,
                closeOnDateSelect : true
            });
            new Datetimepicker({
                start: '#order_create_endtime',
                timepicker: false,
                closeOnDateSelect : true
            });
            new Datetimepicker({
                start: '#order_create_starttime',
                timepicker: false,
                closeOnDateSelect : true
            });

        });

        $('.show_more_content').click(function(){
            var pos = parseInt($(this).attr('position'));
            if(pos>0){
                $(this).siblings().removeClass('hide');
                $(this).text('收起');
                $(this).attr('position', -1);
            }else{
                $(this).siblings().addClass('hide');
                $(this).text('展开');
                $(this).attr('position', 1);
            }
        });
        
        $('a.login_record').click(function () {
            if ($(this).attr('loaded')=='0') {
                PT.show_loading("正在查询");
                PT.sendDajax({
                    'function': 'ncrm_get_login_records',
                    'shop_id': $(this).closest('td[shop_id]').attr('shop_id'),
                    'callback': 'PT.NcrmWorkbench_sh.get_login_records_callback'
                });
            }
        });
    }

    var submit_stop_camp = function (camp_id) {
        $.fancybox.close();
        PT.sendDajax({'function':'ncrm_stop_mnt_campaign', 'campaign_id':camp_id});
    };
    
    var get_account_report_dict = function () {
	    var shop_id_list = $.map($('table.user_table tbody tr'), function (tr_obj) {return Number($(tr_obj).attr('shop_id'));});
	    PT.sendDajax({
	        'function':'ncrm_get_account_report_dict',
	        'shop_id_list':$.toJSON(shop_id_list),
	        'callback':'PT.NcrmWorkbench_sh.get_account_report_dict_callback'
	    });
    }
    
    return {
        init: function() {
            init_dom();
        },
        stop_mnt_campaign:function (camp_id){
            PT.confirm("确认终止当前全自动计划吗？", submit_stop_camp, [camp_id]);
        },
        update_max_num:function (camp_id){
            var max_num = $('#id_max_num_'+camp_id).val();
            if(max_num==''||isNaN(max_num)){
                alert('所填的不是数字！');
                return false;
            }else if(parseInt(max_num)<0||parseInt(max_num)>1000){
                alert("托管宝贝数量范围为0~1000！");
                return false;
            }else{
                if(max_num!=parseInt($('#max_num_bak_'+camp_id).val())){
                    PT.sendDajax({'function':'ncrm_update_mnt_max_num',"camp_id":camp_id, "max_num":max_num});
                    $.fancybox.close();
                }
            }
        },
        run_task:function (obj_id){
            PT.sendDajax({'function':'ncrm_run_mnt_task',"object_id":obj_id});
            $.fancybox.close();
            PT.show_loading('正在执行');
        },
        get_login_records_callback: function (shop_id, login_records) {
            if (login_records.length>0) {
	            var ul_login_records = $('#login_record_'+shop_id).next('ul');
	            ul_login_records.css('width', 87*login_records.length).empty();
	            $.each(login_records, function (i, record) {
	                var Ymd = record[0], HMS_list = record[1];
	                var li_login_records = $('<li class="dib p10 vt"><div>'+Ymd+'</div><hr class="mt5 mb5 btd"></li>');
	                ul_login_records.append(li_login_records);
	                $.each(HMS_list, function (j, HMS) {
	                    li_login_records.append('<div>'+HMS+'</div>');
	                });
	            });
	            ul_login_records.children().css('height', ul_login_records.innerHeight());
            }
            $('#login_record_'+shop_id).attr('loaded', '1');
        }
    }
}();
