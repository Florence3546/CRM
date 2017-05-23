PT.namespace('OperatingRpt');
PT.OperatingRpt1 = function() {
    var pay_rpt_table = null,
        refund_rpt_table = null;

    var init_table=function (){

        refund_rpt_table = $('#refund_rpt_table').dataTable({
            "bRetrieve": true, //允许重新初始化表格
            "bPaginate": false,
            "bFilter": false,
            "bInfo": true,
            "bSort": false,
            "bAutoWidth": true,
            'sDom': "t",
            "aoColumns": [{"bSortable": false},
                          {"bSortable": false},
                          {"bSortable": false},
                          {"bSortable": false},
                          {"bSortable": false},
                          {"bSortable": false},
                          {"bSortable": false},
                          {"bSortable": false},
                          {"bSortable": false},
                          ],
            "oLanguage": {"sEmptyTable":"没有数据",
                          "sInfoEmpty": "显示0条记录",
                         }
        });

    };

    var change_selected_status = function(){
        if ( $(".category_selecter").length > $(".category_selecter:checked").length ){
            $("#category_selecter_all").removeAttr("checked");
        } else {
            $("#category_selecter_all").attr("checked","checked");
        }
        if ( $(".refund_style_selecter").length > $(".refund_style_selecter:checked").length ){
            $("#refund_style_selecter_all").removeAttr("checked");
        } else {
            $("#refund_style_selecter_all").attr("checked","checked");
        }
    };

    var init_dom = function() {
        // 日期时间选择器
        require(['dom', 'gallery/datetimepicker/1.1/index'], function(DOM, Datetimepicker) {
            new Datetimepicker({
                start: '#start_date',
                timepicker: false,
                closeOnDateSelect: true,
                yearStart : 2015,
                yearEnd : 2026,
                formatDate :'YYYY-MM-DD',
            });
            new Datetimepicker({
                start: '#end_date',
                timepicker: false,
                closeOnDateSelect: true,
                yearStart : 2015,
                yearEnd : 2026,
                formatDate :'YYYY-MM-DD',
            });
        });

        $("#category_selecter_all").click(function(){
            if ( $(this).attr("checked") == undefined){
                 $(".category_selecter").removeAttr("checked");
            } else {
                 $(".category_selecter").attr("checked","checked");
            }
            $("#submit_form").click();
        });

        $("#refund_style_selecter_all").click(function(){
            if ( $(this).attr("checked") == undefined){
                 $(".refund_style_selecter").removeAttr("checked");
            } else {
                 $(".refund_style_selecter").attr("checked","checked");
            }
            $("#submit_form").click();
        });

        $(".category_selecter, .refund_style_selecter").click(function(){
            change_selected_status();
            $("#submit_form").click();
        });

        $('#submit_form').click(function(){
            var start_date = $('#start_date').val(),
                end_date = $('#end_date').val();

            var category_obj_list = $(".category_selecter:checked");
            var category_list = [];
            for (var i = 0 ; i < category_obj_list.length ; i ++){
               var key = $(category_obj_list[i]).val();
               category_list.push(key);
            }
            var refund_style_list = $('.refund_style_selecter:checked').map(function () {
                return parseInt($(this).val());
            }).get();

            console.log(category_list);
            if ((!start_date) || (!end_date) || (start_date>end_date)){
                PT.light_msg('请输入正确的统计时间', '不能为空，且结束时间必须大于或等于开始时间');
            } else {
                PT.sendDajax({
                    'function': 'ncrm_get_operating_rpt1',
                    'category_list':$.toJSON(category_list),
                    'refund_style_list':$.toJSON(refund_style_list),
                    'start_date': start_date,
                    'end_date': end_date
                });
                PT.show_loading('正在加载中');
                if (refund_rpt_table) {
                    refund_rpt_table.fnDestroy();
                }
            }
        });

        $(document).on('mouseover', '.icon_hover_show tr', function(){
            $(this).find('.hover').show();
        });
        $(document).on('mouseout', '.icon_hover_show tr', function(){
            $(this).find('.hover').hide();
        });

        $('.tooltips').tooltip({'html': true});

        $('#pay_rpt_table').on('click', '.show_psuser', function() {
            var dpt_id = $(this).closest('tr[dpt_id]').attr('dpt_id');
            var is_showing = $(this).data('is_showing');
            if (is_showing) {
                $('#pay_rpt_table tr[dpt_id='+dpt_id+'][psuser_id]').addClass('hidden');
                $(this).removeData('is_showing');
            } else {
                $('#pay_rpt_table tr[dpt_id='+dpt_id+'][psuser_id]').removeClass('hidden');
                $(this).data('is_showing', 1);
            }
        });

        $('.check_all_dpt').click(function () {
            if (this.checked) {
                $('.check_dpt:not(:checked)').click();
            } else {
                $('.check_dpt:checked').click();
            }
        });

        $('.check_dpt').click(function () {
            if (this.checked) {
                if ($('.check_dpt:not(:checked)').length==0) {
                    $('.check_all_dpt').attr('checked', true);
                }
                $('#pay_rpt_table tr[dpt_id='+this.value+']:lt(3)').removeClass('hidden');
            } else {
                $('.check_all_dpt').attr('checked', false);
                $('#pay_rpt_table tr[dpt_id='+this.value+']').addClass('hidden');
            }
            $('#pay_rpt_table tr[dpt_id='+this.value+'] .show_psuser').removeData('is_showing');
        });

    };


    // var adjust_th_width = function () {
    //     $('#refund_rpt_table tr.fixed_tr>th').each(function (i) {
    //         $(this).width($('#refund_rpt_table tr.inner_tr>th:eq('+i+')').width());
    //     });
    // };

    var init_subdivide_event = function() {

        $('.show_rpt_subdivide_all').off('click');
        $('.show_rpt_subdivide_all').on('click',function(){
            var is_showing = $(this).data('is_showing');
            if(is_showing){
                $(this).parents('table:first').find('.show_subdivide.in').trigger('click');
                delete($(this).data().is_showing);
            }else{
                $(this).parents('table:first').find('.show_subdivide:not(.in)').trigger('click');
                $(this).data('is_showing', 1);
            }
            // adjust_th_width();
        });

        //切换每日细分数据
        $('table').off('click', '.show_subdivide');
        $('table').on('click', '.show_subdivide', function () {
            if ($(this).hasClass('in')) {
                $(this).closest('tr').nextUntil('tr:not(.hover_non_color)').addClass('hidden');
                $(this).removeClass('in');
            } else {
                $(this).closest('tr').nextUntil('tr:not(.hover_non_color)').removeClass('hidden');
                $(this).addClass('in');
            }
        });

    };

    return {
        init: function() {
            init_dom();
            $('#submit_form').click();
        },

        get_rpt_back: function(pay_list, refund_list){
            var pay_str = '';
            for (var i = 0; i < pay_list.length; i ++ ){
                pay_str += template.render('pay_rpt_table_tr', pay_list[i]);
            }
            $('#pay_rpt_table tbody').html(pay_str);
            $('#pay_rpt_table').parent().slideDown();

            //var xiaofu_pay_str = '';
            //for (var i = 0; i < xiaofu_pay_list.length; i ++ ){
            //    xiaofu_pay_str += template.render('xiaofu_pay_table_tr', xiaofu_pay_list[i]);
            //    for (var j = 0; j < xiaofu_pay_list[i].user_list.length; j ++){
            //        xiaofu_pay_str += template.render('xiaofu_pay_table_subtr', xiaofu_pay_list[i].user_list[j]);
            //    }
            //}
            //$('#xiaofu_pay_table tbody').html(xiaofu_pay_str);
            //$('#xiaofu_pay_table').parent().slideDown();

            var refund_str = '';
            for (var i = 0; i < refund_list.length; i ++ ){
                refund_str += template.render('refund_rpt_table_tr', refund_list[i]);
                for (var j = 0; j < refund_list[i].user_list.length; j ++){
                    refund_str += template.render('refund_rpt_table_subtr', refund_list[i].user_list[j]);
                }
            }
            $('#refund_rpt_table tbody').html(refund_str);
            $('#refund_rpt_table').parent().slideDown();

            init_table();
            init_subdivide_event();
        }
    };
}();
