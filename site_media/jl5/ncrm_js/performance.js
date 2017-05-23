PT.namespace('Performance');
PT.Performance = function() {

    var init_table=function (){
        $('#xfgroup_table').dataTable({
            "bRetrieve": true, //允许重新初始化表格
            "bPaginate": true,
            "bFilter": false,
            "bInfo": true,
            "bSort": true,
            "aaSorting": [[2,'asc'],[4,'asc']],
            "iDisplayLength": 30,
            "bAutoWidth": false,//禁止自动计算宽度
            'sDom': "<'row-fluid't>",
            "aoColumns": [{"bSortable": true},
                          {"bSortable": true},
                          {"bSortable": true},
                          {"bSortable": true},
                          {"bSortable": true},
                          ],
            "oLanguage": {"sEmptyTable":"没有数据",
                          "sProcessing" : "正在获取数据，请稍候...",
                          "sInfo":"正在显示第_START_-_END_条信息，共_TOTAL_条信息 ",
                          "sZeroRecords" : "没有您要搜索的内容",
                          "sInfoEmpty": "显示0条记录",
                          "sInfoFiltered" : "(全部记录数 _MAX_ 条)",
                          "oPaginate": {"sFirst" : "第一页",
                                        "sPrevious": "上一页",
                                        "sNext": "下一页",
                                        "sLast" : "最后一页"
                                        }
                         }
        });

    };

    var init_dom = function() {

        // 日期时间选择器
        require(['dom', 'gallery/datetimepicker/1.1/index'], function(DOM, Datetimepicker) {
            new Datetimepicker({
                start: '#tj_month',
                timepicker: false,
                closeOnDateSelect: true,
                yearStart : 2016,
                yearEnd : 2026,
                formatDate :'YYYY-MM',
            });
        });

        $('#id_check_pay input').change(function(){
            var order_pay = parseInt($('#id_check_pay input[name=check_order_pay]').val()),
                refund_pay = parseInt($('#id_check_pay input[name=check_refund_pay]').val());
            if (isNaN(order_pay) || isNaN(refund_pay)) {
                PT.light_msg('', '请输入数字');
                return;
            }
            $('#id_check_pay input[name=check_order_pay]').val(order_pay);
            $('#id_check_pay input[name=check_refund_pay]').val(refund_pay);
            var team_royalty = parseFloat($('#id_check_pay input[name=team_royalty]').val()),
                team_pay = parseInt((order_pay - refund_pay) * team_royalty / 100),
                consult_pay_limit = parseInt($('#consult_pay_limit').val()),
                consult_royalty = parseFloat($('.consult_royalty').data('old-value')),
                consult_pay = parseInt(team_pay * consult_royalty);
            if (consult_pay > consult_pay_limit) {
                consult_pay = consult_pay_limit;
            }
            $('#consult_pay').html(consult_pay);
            $('#seller_pay').html(team_pay - consult_pay);

        });

        $('#tj_month_form a.submit').click(function(){
            PT.show_loading('正在获取数据，请稍候');
            $('#tj_month_form').submit();
        });

        $('#id_check_pay input[name=team_royalty]').val(parseFloat($('#team_royalty_table td.bg_theme').attr('data')) * 100);
        // $('input[type=text][name=royalty_factor]').change(function() {
        //     var val = Number($(this).val()),
        //         val_type = $(this).data('type');
        //     if (isNaN(val)) {
        //         PT.light_msg('', '请输入数字');
        //         return;
        //     }
        //     $('.' + val_type + '_royalty').each(function(){
        //         $(this).text(Number($(this).data('old-value')) * val );
        //     });
        //     var team_pay = Number($('#team_pay').attr('team_pay')),
        //         consult_royalty_factor = Number($('#consult_royalty_factor').html()),
        //         seller_royalty_factor = Number($('#seller_royalty_factor').html());
        //     $('#consult_pay').html((team_pay * consult_royalty_factor / (consult_royalty_factor + seller_royalty_factor)).toFixed(2));
        //     $('#seller_pay').html((team_pay * seller_royalty_factor / (consult_royalty_factor + seller_royalty_factor)).toFixed(2));
        // });

        $('.tooltips').tooltip({'html': true});

    };

    return {
        init: function() {
            init_dom();
            PT.show_loading('正在获取数据');
            PT.sendDajax({'function': 'ncrm_get_performance_income',
                          'date_month': $('#tj_month').val(),
                          'call_back': 'PT.Performance.get_income_back'
                          });
        },
        get_income_back: function(is_success, xfgroup_list, person_list){
            if (!is_success) {
                PT.alert('获取数据失败');
            } else {
                var xfgroup_str = '', person_str = '', psuser_id = parseInt($('#psuser_id').val());
                var cur_person = {'order_pay': 0, 'order_pay_rank': 0, 'score_rank': 0, 'score': 0, 'refund_pay': 0, 'team_pay': 0};
                for(var i = 0 ; i < xfgroup_list.length ; i ++){
                    if (xfgroup_list[i].xfgroup_id == psuser_id){
                        cur_person = xfgroup_list[i];
                        xfgroup_list[i].is_current_user = true;
                    }
                    var score_detail_str_list = $.map(xfgroup_list[i].score_detail_list, function(obj){
                        return obj.indicator_name_cn + ': ' + obj.multiplier + '*' + obj.old_value + '=' +obj.score;
                    });
                    xfgroup_list[i].score_detail_str_list = score_detail_str_list;
                    xfgroup_str += template.render('xfgroup_table_tr',xfgroup_list[i]);
                }
                $('#xfgroup_table tbody').html(xfgroup_str);
                init_table();
                person_str = template.render('person_info', cur_person);
                $('#person').html(person_str);
                $('.tooltips').tooltip({'html': true});

                var td_index = $('input.sc_desc[value='+cur_person.score_level+']').parents('th').index(),
                    tr_index = $('input.pc_desc[value="'+cur_person.order_pay_level+'"]').parents('tr').index();
                if (td_index != -1 && tr_index != -1){
                    $('#cfg_table tbody').find('tr').eq(tr_index).find('td').eq(td_index).addClass('bg_theme');
                }
            }
        },
    };
}();
