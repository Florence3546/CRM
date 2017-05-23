PT.namespace('PerformanceIncome');
PT.PerformanceIncome = function() {
    var xfgroup_table = null,
        person_table = null;

    var get_cfg_dict = function() {
        var cfg_dict = {},
            score_cfg_list = [],
            pay_cfg_list = [],
            cfg_table = $('#cfg_table'),
            date_month = $('#tj_month').val();
        cfg_table.find('tr>th').each(function(){
            if ($(this).find('.sc_desc').length) {
                var score_cfg = {};
                score_cfg.desc = $.trim($(this).find('.sc_desc').val());
                score_cfg.count = parseInt($(this).find('input.sc_count').val());
                score_cfg_list.push(score_cfg);
            }
        });
        cfg_table.find('tr.consult_pay_limit>td').each(function(){
            var i = $(this).index();
            if (i > 0) {
                score_cfg_list[i-1].consult_pay_limit = parseInt($(this).find('input').val());
            }
        });
        cfg_table.find('tr.consult_royalty_equation>td').each(function(){
            var i = $(this).index();
            if (i > 0) {
                score_cfg_list[i-1].consult_royalty_equation = {
                    'x0': parseFloat($(this).find('input.cre_x0').val()),
                    'x1': parseFloat($(this).find('input.cre_x1').val()),
                    'x2': parseFloat($(this).find('input.cre_x2').val()),
                };
            }
        });
        cfg_table.find('tr.pay_cfg').each(function(){
            var pay_cfg = {};
            pay_cfg.team_royalty = {};
            $(this).find('td').each(function () {
                var i = $(this).index();
                if (i === 0) {
                    pay_cfg.desc = $.trim($(this).find('.pc_desc').val());
                    pay_cfg.pay_min = parseInt($(this).find('input.pc_pay_min').val());
                } else {
                    pay_cfg.team_royalty[score_cfg_list[i-1].desc] = parseInt($(this).find('input.team_royalty').val()) / 100.0;
                }
                 // body...
            });
            pay_cfg_list.push(pay_cfg);
        });

        var score_calc_list = $.map($('#score_calc_div').find('input[name=indicator_name]:checked'), function(obj){
            return {
                'indicator_name': $.trim($(obj).val()),
                'indicator_name_cn': $.trim($(obj).siblings('.jq_indicator_name_cn').text()),
                'multiplier': parseFloat($(obj).siblings('.jq_multiplier').val()),
            };
        });

        return {'date': date_month, 'score_cfg_list': score_cfg_list, 'pay_cfg_list': pay_cfg_list, 'score_calc_cfg_list': score_calc_list};
    };

    var save_cfg = function(){
        PT.show_loading('正在检查配置');
        var cfg_dict = get_cfg_dict();
        PT.sendDajax({'function': 'ncrm_save_performance_conf', 'cfg_dict': $.toJSON(cfg_dict)});
    };

    var save_xfgroup = function(){
        PT.show_loading('正在保存销服组绩效单');
        var cfg_dict = get_cfg_dict(),
            score_level_dict = {};
        $('#xfgroup_table tbody>tr').each(function(){
            var xfgroup_id = parseInt($(this).attr('id')),
                score_level = $.trim($(this).find('td.person_score_level select').val());
            score_level_dict[xfgroup_id] = score_level;
        });
        PT.sendDajax({'function': 'ncrm_save_xfgroup_perf', 'date_month': $('#tj_month').val(),
                      'cfg_dict': $.toJSON(cfg_dict), 'score_level_dict': $.toJSON(score_level_dict)});
    };

    var get_data = function(is_force){
        PT.show_loading('正在获取数据');
        var cfg_dict = get_cfg_dict();
        PT.sendDajax({'function': 'ncrm_get_performance_income',
                      'date_month': $('#tj_month').val(),
                      'cfg_dict': $.toJSON(cfg_dict),
                      'is_force': is_force,
                      'call_back': 'PT.PerformanceIncome.get_income_back'
                      });
    };

    var init_table=function (){
        xfgroup_table = $('#xfgroup_table').dataTable({
            "bRetrieve": true, //允许重新初始化表格
            "bPaginate": false,
            "bFilter": false,
            "bInfo": true,
            "bSort": true,
            "aaSorting": [[5,'desc'],[3,'asc']],
            "iDisplayLength": 100,
            "bAutoWidth": true,
            'sDom': "<'lh36 b f14 ml10'i>t",
            "aoColumns": [{"bSortable": true},
                          {"bSortable": true},
                          {"bSortable": true},
                          {"bSortable": true},
                          {"bSortable": true},
                          {"bSortable": true},
                          {"bSortable": true},
                          {"bSortable": true},
                          {"bSortable": true},
                          {"bSortable": true},
                          {"bSortable": true},
                          {"bSortable": true},
                          {"bSortable": true},
                          {"bSortable": true},
                          {"bSortable": true},
                          {"bSortable": true},
                          ],
            "oLanguage": {"sEmptyTable":"没有数据",
                          "sProcessing" : "正在获取数据，请稍候...",
                          "sInfo":"共_TOTAL_个销服组 ",
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

        // TableTools.DEFAULTS.aButtons = ["csv"];
        person_table = $('#person_table').dataTable({
            "bRetrieve": true, //允许重新初始化表格
            "bPaginate": false,
            "bFilter": false,
            "bInfo": true,
            "bSort": true,
            "aaSorting": [[2,'desc']],
            "iDisplayLength": 100,
            "bAutoWidth": true,
            'sDom': "lfrtip",
            "aoColumns": [{"bSortable": true},
                          {"bSortable": true},
                          {"bSortable": true},
                          {"bSortable": true},
                          ],
            // "oTableTools": {
            //     "sSwfPath":  "/site_media/assets/swf/copy_csv_xls.swf",
            //     "aButtons": [{
            //         "sExtends": "xls",
            //         "sTitle": "222",
            //         "fnClick": function(nButton, oConfig, flash) {
            //             this.fnSetText(flash, "1");
            //         }
            //     }],
            //     custom_btn_id: "save_as_csv"
            // },
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
                yearEnd : 2016,
                formatDate :'YYYY-MM',
            });
        });

        $('#tj_month_form a.submit').click(function(){
            $('#tj_month_form').submit();
            // PT.sendDajax({'function': 'ncrm_get_performance_income', 'date_month': $('#tj_month').val()});
        });

        $('.dryrun').click(function(){
            get_data(is_force = 1);
            $(this).siblings('.save_cfg').fadeIn();
        });

        $('.save_cfg').click(function(){
            PT.confirm('确定要保存该配置？(将会覆盖旧的记录！)', save_cfg);
        });

        $('.save_xfgroup').click(function(){
            PT.confirm('确定要保存该配置？(将会覆盖旧的记录！)', save_xfgroup);
        });

        $('.modify_score_level').click(function(){
            $('#xfgroup_table tr .person_score_level select').attr('disabled', false);
            $(this).fadeOut();
        });

        $('#export_csv').click(function(){
            var data_str = '';
            $('#person_table tr').each(function(){
                var temp_str = '';
                $(this).find('th').each(function(){
                    temp_str += $(this).find('div').text() + ',';
                });
                $(this).find('td').each(function(){
                    temp_str += $(this).text() + ',';
                });
                data_str += temp_str.slice(0, -1) + '\n';
            });
            var download_link = document.createElement('a');
            download_link.href = 'data:text/csv;charset=utf-8,\ufeff' + encodeURIComponent(data_str);
            download_link.download = '个人绩效单-' + $('#tj_month').val() + '.csv';
            document.body.appendChild(download_link);
            download_link.click();
            document.body.removeChild(download_link);
        });

        $('.jq_check_num').change(function(){
            if (isNaN((Number($(this).val())))) {
                $(this).val(1);
                PT.light_msg('', '只能填入数字');
            }
        });

        $('.sc_count').change(function(){
            var total_count = 0, i = 0,
                jq_span = $('#score_total_count>span');
            $('.sc_count').each(function(){
                var count = $(this).val();
                jq_span.eq(i+2).text(count);
                total_count += parseInt(count);
                i += 1;
            });
            jq_span.eq(1).text(total_count);
        });

        $('.tooltips').tooltip({'html': true});
        $('.sc_count').change();

    };

    return {
        init: function() {
            init_dom();
            $('.div_perf_cfg').slideToggle();
            get_data(is_force = 0);
        },
        get_income_back: function(is_success, xfgroup_list, person_list, group_sum_list){
            if (!is_success) {
                PT.alert('获取数据失败');
            } else {
                if(xfgroup_table){
                    xfgroup_table.fnDestroy();
                }else{
                    $('.div_perf_cfg').slideToggle();
                }
                if(person_table){
                    person_table.fnDestroy();
                }
                var xfgroup_str = '', person_str = '', group_sum_str = '';
                for(var k = 0 ; k < group_sum_list.length ; k++){
                    group_sum_str += template.render('group_sum_div',group_sum_list[k]);
                }
                $('#group_sum_info').html(group_sum_str);

                for(var i = 0 ; i < xfgroup_list.length ; i ++){
                    xfgroup_str += template.render('xfgroup_table_tr',xfgroup_list[i]);
                }
                $('#xfgroup_table tbody').html(xfgroup_str);
                for(var j = 0 ; j < person_list.length ; j ++){
                    person_str += template.render('person_table_tr',person_list[j]);
                }
                $('#person_table tbody').html(person_str);
                init_table();
            }
        },
        save_cfg_back: function(is_success){
            if (is_success){
                PT.light_msg('', '保存配置成功');
                $('.save_cfg').fadeOut();
            }else{
                PT.alert('保存配置失败！');
            }
        },
        save_xfgroup_perf: function(is_success){
            if (is_success){
                PT.alert('保存销服组绩效单成功', null, function(){window.location.reload();});

            }else{
                PT.alert('保存销服组绩效单失败！');
            }
        }

    };
}();
