PT.namespace('NcrmBulkOptimize');
PT.NcrmBulkOptimize = function() {
    var shop_id_list = [],
        test_shop_id = 0;

    var check_price = function(price) {
        var error_msg = '',
            new_price = parseFloat(price);
        if (isNaN(new_price) || new_price < 0.05 || new_price > 99.99) {
            error_msg = '出价必须在 0.05 ~ 99.99 之间';
        }
        return error_msg;
    };

    var check_parcent = function(parcent) {
        var error_msg = '',
            new_parcent = parseInt(parcent);
        if (isNaN(new_parcent) || new_parcent < 0 || new_parcent > 300) {
            error_msg = '百分比必须在 0% ~ 300% 之间';
        }
        return error_msg;
    };

    var get_del_kw_detail = function(cur_lable) {
        var error_msg = '',
            kw_cmd = {'cond': '', 'operate': '', 'desc': ''},
            del_rpt = cur_lable.find('#del_rpt').val(),
            del_rpt_desc = cur_lable.find('#del_rpt>option:selected').text(),
            pc_qscore = cur_lable.find('#pc_qscore').val(),
            yd_qscore = cur_lable.find('#yd_qscore').val(),
            desc = '删除：7天'+ del_rpt_desc +'，且PC质量得分<='+ pc_qscore +'，且移动质量得分<=' + yd_qscore,
            // 质量得分的命令 一定 要加上 >0. 质量得分==0 意味着 同步质量得分失败
            cond = "kw.rpt7."+ del_rpt +"==0 and 0 < kw.qscore_dict['qscore'] <= " + pc_qscore + " and (0 < kw.qscore_dict['wireless_qscore'] <= " + yd_qscore + " or kw.qscore_dict['wireless_qscore'] == -1 )";
            kw_cmd = {'cond': cond, 'operate': 'del_kw()', 'desc': desc};
        return {'error_msg': error_msg, 'kw_cmd': kw_cmd};
    };

    var get_change_yuan_detail = function(cur_lable){
        var error_msg = '',
            kw_cmd = {'cond': '', 'operate': '', 'desc': ''},
            change_type = cur_lable.find('select').val(),
            price = cur_lable.find('input[type=text]').val();
        error_msg = check_price(price);
        if (error_msg === '') {
            price = parseFloat(price, 2);
            var desc = '所有关键词出价'+ (change_type=='up'? '提高': '降低') + price +'元',
                operate = 'upd_price(kw.max_price'+ (change_type=='up'? '+': '-') + String(parseInt(price*100)) +')';
            kw_cmd = {'cond': 'True', 'operate': operate, 'desc': desc};
        }
        return {'error_msg': error_msg, 'kw_cmd': kw_cmd};
    };

    var get_change_parcent_detail = function(cur_lable){
        var error_msg = '',
            kw_cmd = {'cond': '', 'operate': '', 'desc': ''},
            change_type = cur_lable.find('select').val(),
            parcent = cur_lable.find('input[type=text]').val();
        error_msg = check_parcent(parcent);
        if (error_msg === ''){
            new_parcent = parseFloat(parcent, 2) / 100.0;
            var desc = '所有关键词出价'+ (change_type=='up'? '提高': '降低') + parcent +'%',
                operate = 'upd_price(kw.max_price * ( 1'+(change_type=='up'? '+': '-')  + String(new_parcent) +'))';
            kw_cmd = {'cond': 'True', 'operate': operate, 'desc': desc};
        }
        return {'error_msg': error_msg, 'kw_cmd': kw_cmd};
    };

    var get_change_gprice_detail = function(cur_lable){
        var kw_cmd = {'cond': '', 'operate': '', 'desc': ''},
            parcent = cur_lable.find('input[type=text]').val(),
            error_msg = check_parcent(parcent);
        if (error_msg === ''){
            new_parcent = parseFloat(parcent, 2) / 100.0;
            var desc = '所有关键词使用市场平均出价的'+ parcent +'%',
                operate = 'upd_price(kw.g_cpc * '+ String(new_parcent) +')';
            kw_cmd = {'cond': 'True', 'operate': operate, 'desc': desc};
        }
        return {'error_msg': error_msg, 'kw_cmd': kw_cmd};
    };

    var get_custom_strategy = function(){
        var cur_input = $('#custom_optimize input[type=radio][name=custom_cmd]:checked'),
            custom_opt_type = cur_input.val(),
            cur_lable = cur_input.parent(),
            result = {};
        switch(custom_opt_type){
            case 'del_kw':
                result = get_del_kw_detail(cur_lable);
                break;
            case 'change_yuan':
                result = get_change_yuan_detail(cur_lable);
                break;
            case 'change_parcent':
                result = get_change_parcent_detail(cur_lable);
                break;
            case 'change_gprice':
                result = get_change_gprice_detail(cur_lable);
                break;
            default:
                result = {'error_msg': '不存在', 'kw_cmd': {'cond': '', 'operate': '', 'desc': ''}};
                break;
        }
        return result;
    };

    var init_dom = function() {

        $(document).on('click', '#li_common_optimize', function() {
            $('#custom_optimize input[type=radio][name=custom_cmd]').attr('checked', false);
        });

        $(document).on('click', '#li_custom_optimize', function() {
            $('#common_optimize input[type=radio][name=common_stg]').attr('checked', false);
        });

        $('#custom_optimize').on('click', 'input[type=text],select', function(){
            $(this).parents('label').find('input[type=radio]').attr('checked', true);
        });

        $(document).on('click', '#common_opt_submit', function() {
            var cur_input = $('#common_optimize input[type=radio][name=common_stg]:checked');
            if (shop_id_list.length === 0){
                PT.light_msg('', '没有店铺可供操作');
                return false;
            }
            if (cur_input.length === 0) {
                PT.light_msg('', '请先选择一个操作');
                return false;
            }
            var desc = cur_input.attr('desc'),
                strategy_name = cur_input.val();
            PT.confirm('确定要对当前店铺【'+ desc +'】吗？', function () {
                PT.show_loading('正在提交操作');
                PT.sendDajax({
                    'function': 'ncrm_common_opt_submit',
                    'strategy_name': strategy_name,
                    'shop_id_list': shop_id_list,
                });
            });
        }),

        $(document).on('click', '#custom_opt_submit', function() {
            var cur_input = $('#custom_optimize input[type=radio][name=custom_cmd]:checked');
            if (shop_id_list.length === 0){
                PT.light_msg('', '没有店铺可供操作');
                return false;
            }
            if (cur_input.length === 0) {
                PT.light_msg('', '请先选择一个操作');
                return false;
            }

            var result = get_custom_strategy();
            if (result.error_msg !== ''){
                PT.alert(result.error_msg);
                return false;
            }else{
                console.log(result.kw_cmd);
                PT.confirm('确定要对当前店铺【'+ result.kw_cmd.desc +'】吗？', function () {
                    PT.show_loading('正在提交操作');
                    PT.sendDajax({
                        'function': 'ncrm_custom_opt_submit',
                        'kw_cmd': $.toJSON(result.kw_cmd),
                        'shop_id_list': shop_id_list,
                    });
                });
            }
        }),

        $(document).on('click', '.js_select_shop', function(){
            test_shop_id = $(this).parent().attr('id');
            $('#select_shop_name').html($(this).prev()[0].outerHTML);
            // PT.show_loading('正在查询数据');
            $('#select_camp').html('');
            $('#select_adg').html('');
            $('#show_deatail').show();
            PT.sendDajax({
                'function': 'ncrm_get_opt_camps',
                'shop_id': test_shop_id,
            });
        }),

        $('#kw_table').on('click', '.chart', function(){
            var jq_tr = $(this).parents('tr:first'),
                keyword_id = jq_tr.attr('id'),
                word = jq_tr.attr('word'),
                campaign_id = $('input[name="select_camp"]:checked').val(),
                adgroup_id = $('input[name="select_adg"]:checked').val();
            PT.sendDajax({
                'function': 'ncrm_get_kw_chart',
                'shop_id': test_shop_id,
                'campaign_id': campaign_id,
                'adgroup_id': adgroup_id,
                'keyword_id': keyword_id
            });
            $('#kw_word').text(word);
        }),

        $('#select_camp').on('click', 'input[name="select_camp"]', function(){
            $('#select_adg').html('');
            var campaign_id = $(this).val();
            // PT.show_loading('正在查询数据');
            PT.sendDajax({
                'function': 'ncrm_get_opt_adgs',
                'shop_id': test_shop_id,
                'campaign_id': campaign_id
            });
        }),

        $('#select_adg').on('click', 'input[type="radio"][name="select_adg"]', function(){
            var campaign_id = $('input[name="select_camp"]:checked').val(),
                adgroup_id = $(this).val(),
                common_strategy = $('#common_optimize input[type=radio][name=common_stg]:checked'),
                custom_strategy = $('#custom_optimize input[type=radio][name=custom_cmd]:checked'),
                kw_cmd = {},
                strategy_name = '';
            if (common_strategy.length > 0 ){
                strategy_name = common_strategy.val();
            }else if(custom_strategy.length > 0){
                var result = get_custom_strategy();
                if (result.error_msg !== ''){
                    PT.alert(result.error_msg);
                    return false;
                }else{
                    kw_cmd = result.kw_cmd;
                }
            }else{
                PT.alert('请先选择一个操作');
                return false;
            }
            PT.sendDajax({
                'function': 'ncrm_dryrun_adg',
                'shop_id': test_shop_id,
                'campaign_id': campaign_id,
                'adgroup_id': adgroup_id,
                'strategy_name': strategy_name,
                'kw_cmd': $.toJSON(kw_cmd)
            });
            PT.show_loading('正在查询数据');
        }),

        $('#div_kw_detail').on('click', 'input[name=kw_selector]', function(){
            var kw_type = $(this).val(),
                old_kw_table = $('#kw_table'),
                new_kw_table = $('#add_kw_table');
            if (kw_type=='add'){
                old_kw_table.hide();
                new_kw_table.show();
                return;
            }
            new_kw_table.hide();
            old_kw_table.show();
            if (kw_type!=='all'){
                old_kw_table.find('tbody>tr').each(function(){
                    if($(this).attr('optm_type') == kw_type) {
                        $(this).show();
                    }else{
                        $(this).hide();
                    }
                });
            }else{
                old_kw_table.find('tbody>tr').each(function(){
                    $(this).show();
                });
            }
        }),

        $('.tooltips').tooltip({'html': true});

    };

    return {
        init: function(unopt_shopid_list) {
            shop_id_list = unopt_shopid_list;
            init_dom();
        },

        opt_submit_back: function(shop_count, camp_count){
            PT.light_msg('提交成功', '系统正在后台执行：将优化'+ shop_count +'个店铺，'+ camp_count +'个托管计划');
            var html_str = '';
            for(var i=0; i<shop_id_list.length; i++){
                var temp_html = $('#' + shop_id_list[i]).find('a:first')[0].outerHTML;
                html_str += '<p>' + temp_html + '<span class="ml10 red">刚刚手动优化过</span></p>';
                $('#' + shop_id_list[i]).remove();
            }
            $('#opted_shop>div').prepend(html_str);
            var current_unopt_count = parseInt($('#unopt_shop_count').text()),
                current_opted_count = parseInt($('#opted_shop_count').text());
            $('#unopt_shop_count').text(current_unopt_count-shop_id_list.length);
            $('#opted_shop_count').text(current_opted_count+shop_id_list.length);
            shop_id_list = [];
        },

        opt_camps_back: function(camp_list){
            var html_str='';
            if (camp_list.length === 0){
                html_str = '<span class="red ml20">该店铺没有正在推广的托管计划</span>';
            }else{
                for(var i=0;i<camp_list.length;i++) {
                    html_str += ' <label class="dib ml20"> <input type="radio" name="select_camp" class="mr5" value="'+ camp_list[i].campaign_id +'">'+ camp_list[i].title +' </label>';
                }
            }
            $('#select_camp').html('').append(html_str);
            if(camp_list.length){
                $('input[type="radio"][name="select_camp"]').eq(0).click();
            }
        },

        opt_adgs_back: function(adg_list){
            var html_str = '';
            if (adg_list.length === 0){
                html_str = '<span class="red ml20">该计划下没有正在推广的托管宝贝</span>';
            }else{
                for(var i=0;i<adg_list.length;i++) {
                    html_str += ' <label class="dib ml20"> <input type="radio" name="select_adg" class="mr5" value="'+ adg_list[i].adgroup_id +
                                '">'+ '<img class="h80 w80" src="' + adg_list[i].pic_url + '_80x80.jpg">' +' </label>';
                }
            }
            $('#select_adg').html('').append(html_str);
            $('#div_kw_detail').hide();
        },

        kw_chart_back: function(category_list, series_cfg_list){
            PT.draw_trend_chart('kw_chart', category_list, series_cfg_list);
            $('#modal_kw_chart').modal();
        },

        dryrun_adg_back: function(kw_list, add_kw_list, user_limit_price){
            var temp_str = '',
                add_kw_temp_str = '',
                delete_count = 0,
                plus_price_count = 0,
                reduce_price_count = 0,
                match_count = 0,
                keep_count = 0;

            if (kw_list.length === 0){
                temp_str = '<td colspan="21" class="tc b f14">没有关键词</td>';
            }else{
                for (var i=0; i<kw_list.length; i++){
                    temp_str += template.render('kw_table_tr', kw_list[i]);
                    if (kw_list[i].optm_type==1){
                        delete_count += 1;
                    }else if (kw_list[i].optm_type==2){
                        reduce_price_count += 1;
                    }else if (kw_list[i].optm_type==3){
                        plus_price_count += 1;
                    }else if (kw_list[i].optm_type==4){
                        match_count += 1;
                    }else{
                        keep_count += 1;
                    }
                }
            }
            if (add_kw_list.length === 0){
                add_kw_temp_str = '<td colspan="9" class="tc b f14">没有关键词</td>';
            }else{
                for (var j=0; j<add_kw_list.length; j++){
                    add_kw_temp_str += template.render('add_kw_table_tr', add_kw_list[j]);
                }
            }
            $('#total_kw_count').text(kw_list.length);
            $('#plus_price_count').text(plus_price_count);
            $('#reduce_price_count').text(reduce_price_count);
            $('#delete_count').text(delete_count);
            $('#add_count').text(add_kw_list.length);
            $('#match_count').text(match_count);
            $('#keep_count').text(keep_count);
            $('#kw_limit_price').text(parseFloat(user_limit_price/100.0, 2).toFixed(2));

            $('#kw_table tbody').html(temp_str);
            $('#add_kw_table tbody').html(add_kw_temp_str);
            $('#kw_table').show();
            $('#add_kw_table').hide();
            $('#div_kw_detail').show();
            $('input[name=kw_selector][value=all]').attr('checked', true);
            $('.tooltips').tooltip();
        }

    };
}();
