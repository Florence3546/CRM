PT.namespace('OrderDunning');
PT.OrderDunning = function() {

    var orderTable = $('#order_table');

    var calc_time=function(){
        var day_seconds=24 * 3600 * 1000;
        var hour_seconds=3600 * 1000;
        var min_seconds=60 * 1000;
        var sec_seconds=1000;

        $('#order_table tbody tr').each(function(e){
            var time_str=$(this).find('td:eq(3)').attr("create_time");
            var time_delta=new Date().getTime()-new Date(time_str).getTime();
            if(time_delta > day_seconds){
                msg= Math.floor(time_delta/day_seconds) + "天前";
            }else if(time_delta> hour_seconds){
                msg= Math.floor(time_delta/hour_seconds) + "小时前";
            }else if(time_delta> min_seconds){
                msg= Math.floor(time_delta/min_seconds) + "分钟前";
            }else{
                msg="刚刚";
            }
            msg +="创建";
            $(this).find('td:eq(3)').text(msg);
        });
    };

    var init_note_dom = function(){
        $(document).on('click', '.edit_note', function(){
            var order_id=$(this).parent().parent().attr('id');
            var old_note=$('#id-'+ order_id+ '-note').text();
            $('#id_order_id').val(order_id);
            $('#id_order_note').val(old_note);
            $('#id_edit_note_layout').modal();
        });

        $(document).on('click', '#submit_note', function(){
            var order_id=$('#id_order_id').val();
            var note=$('#id_order_note').val();
            PT.sendDajax({'function': 'ncrm_submit_order_note', 'order_id': order_id, 'note': note});
        });

        $('#id-clear-order').click(function(){
            PT.sendDajax({'function': 'ncrm_clean_unpaid_order'});
        });
    }


    var init_dom = function() {

        init_note_dom();
        setInterval(calc_time, 5000);

        var startWebSocket = function() {
            var url,
                ws;

            url = 'ws://'+window.location.host+':30001/ncrm/echo_msg/';
            ws = new WebSocket(url);
            ws.onmessage = function(msg) {
                console.log(msg);
                if (msg != '' && msg != undefined) {
                    if(msg.data == 'ready'){
                        return false;
                    }
                    var content = $.evalJSON(msg.data);
                    showMsg(content, ws);
                } else {
                    console.log("error");
                }
            };
        }

        var showMsg = function(msg, ws) {
            var order = msg.content;

            var opt_type = msg.opt_type;
            order.opt_type = opt_type;
            if(opt_type == 'save'){
                appendNewOrder(order);
            }else if(opt_type == "close"){
                if($('#'+order.order_id )){
                    $('#'+order.order_id).addClass('order_close');
                    $('#'+order.order_id+' td:eq(-1)').append('<a href="javascript:void(0);" class="btn btn-small delete_subscribe">不再显示</a>');
                }
            }else if(opt_type == "paid"){
                if($('#'+order.order_id )){
                    $('#'+order.order_id).addClass('order_paid')
                    $('#'+order.order_id+' td:eq(-1)').append('<a href="javascript:void(0);" class="btn btn-small delete_subscribe">不再显示</a>');
                }
            }else{
                console.log("error...")
            }
        }

        startWebSocket();

        orderTable.on('click', '.delete_subscribe', function () {
            $(this).closest('tr').remove();
            if(!orderTable.find('tbody tr').length){
                var tr = '<tr class="no_data"><td class="tc" colspan="10">暂无未付款订单</td></tr>';
                orderTable.find('tbody').html(tr);
            }
            var old_count = parseInt($('#id_unpaid_count').text());
            if(old_count>0){
                $('#id_unpaid_count').text(old_count - 1);
            }
        });

        orderTable.on('click', '.close_fuwuorder', function () {
            PT.show_loading('正在提交');
            PT.sendDajax({
                'function': 'ncrm_close_fuwuorder',
                'order_id': $(this).closest('tr').attr('id'),
                'callback': 'PT.OrderDunning.close_fuwuorder_callback'
            });
        });

        $('#modal_add_activity_code').on('show', function () {
            $('#modal_add_activity_code').find('input[name=activity_code], input[name=psuser_name_cn]').val('');
        });

        $('#submit_activity_code').click(function () {
            var activity_code = $.trim($('#modal_add_activity_code input[name=activity_code]').val()),
                psuser_name_cn = $.trim($('#modal_add_activity_code input[name=psuser_name_cn]').val());
            if (!activity_code || !psuser_name_cn) {
                PT.alert('必须填写 活动代码 和 所属人！');
                return;
            }
            PT.show_loading('正在提交');
            PT.sendDajax({
                'function': 'ncrm_add_activity_code',
                'activity_code': activity_code,
                'psuser_name_cn': psuser_name_cn,
                'callback': 'PT.OrderDunning.add_activity_code_callback'
            });
        });

        $('#modal_activity_code_list .del_activity_code').click(function () {
            PT.sendDajax({
                'function': 'ncrm_del_activity_code',
                'activity_code': $(this).attr('activity_code'),
                'callback': 'PT.OrderDunning.del_activity_code_callback'
            });
        })

    };


    var get_biz_type = function(value){
        //((1, '新订'), (2, '续订'), (3, '升级'), (4, '后台赠送'), (5, '后台自动续订'), (6, '未知'))
        desc = '未知'
        switch(value){
            case 1:
                desc = '新订';
                break;
            case 2:
                desc = '续订';
                break;
            case 3:
                desc = '升级';
                break;
            case 4:
                desc = '后台赠送';
                break;
            case 5:
                desc = '后续自动续订';
                break;
            default:
                desc = '未知';
                break;
        }
        return desc;
    }

    /**
     * 来了新的订单，追加到table最顶部
     * @param data
     */
    var appendNewOrder = function(order){
        order.fee = parseFloat(order.fee/100).toFixed(2);
        order.total_pay_fee = parseFloat(order.total_pay_fee/100).toFixed(2);
        order.order_cycle_end = order.order_cycle_end.slice(0, 10);
        order.order_cycle_start = order.order_cycle_start.slice(0, 10);
        order.biz_type = get_biz_type(order.biz_type);
        var tr_html = template.render("order_dunning_template",{'order':order});
        if($('.no_data').length){
            orderTable.find("tbody").html(tr_html);
        }else{
            var firstTR = orderTable.find("tbody tr:first-child");
            firstTR.before(tr_html);
        }
        var old_count = parseInt($('#id_unpaid_count').text());
        $('#id_unpaid_count').text(old_count+1);
    };


    return {
        init: function() {
            init_dom();
        },
        note_save_callback: function(order_id, note){
            $('#id-'+ order_id+ '-note').text(note);
            $('#id_edit_note_layout').modal('hide');
        },
        close_fuwuorder_callback: function (error, order_id) {
            if (error) {
                PT.alert(error);
            } else {
                $('#'+order_id).remove();
                PT.light_msg('', '操作成功');
            }
        },
        add_activity_code_callback: function (error) {
            if (error) {
                PT.alert(error);
            } else {
                PT.show_loading('正在刷新');
                window.location.reload();
            }
        },
        del_activity_code_callback: function (error, activity_code) {
            if (error) {
                PT.alert(error);
            } else {
                $('#modal_activity_code_list a[activity_code='+activity_code+']').closest('tr').remove();
                PT.light_msg('', '删除成功');
            }
        }
    }
}();