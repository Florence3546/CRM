PT.namespace('MntAdgBox');
PT.MntAdgBox = function () {
    var page_no = 1;
    var page_size = 50;
    var search_keyword = '';
    var campaign_id = 0;
    var mnt_type = 0;
    var mnt_max_num = 0;

    // 初始化表格数据
    var init_tables = function () {
        page_no = 1;
        search_keyword = '';
        mnt_max_num = Number($('#mnt_max_num').val()) || 0;
        $('#search_adg_input').val('');
        $('#adgroup_table tbody, #mnt_adgroup_table tbody, #adgroup_recycle_bin').empty();
    }

    // 获取宝贝列表
    var get_adg_list = function () {
        PT.show_loading('正在获取数据');
        PT.sendDajax({
            'function':'mnt_get_adg_list',
            'campaign_id':campaign_id,
            'page_no':page_no,
            'page_size':page_size,
            'sSearch':search_keyword,
            'rpt_days':7
        });
    }

    // 更新宝贝个数统计
    var update_statistic_data = function () {
        var total_adg_count = Number($('#fancybox_mnt_adgroup .total_adg_count').attr('init_value'));
        var mnt_adg_count = $('#mnt_adgroup_table tbody tr').length;
        var new_item_count = Number($('.new_item_count').html()) || 0;
        var mnt_count0 = mnt_adg_count + new_item_count;
        var mnt_count = mnt_max_num - mnt_count0;
        var batch_adg_num = Math.min($('#adgroup_table tbody tr').length, mnt_count);
        total_adg_count -= mnt_adg_count;
        if (total_adg_count>0 && mnt_type=='1') {
	        $('.adg_2del_info').show();
        } else {
	        $('.adg_2del_info').hide();
        }
        $('.total_adg_count').html(total_adg_count);
        $('.mnt_adg_count').html(mnt_adg_count);
        $('.mnt_count0').html(mnt_count0);
        $('.mnt_count').html(mnt_count);
        $('.batch_adg_num').html(batch_adg_num);
    }

    // 打开设置限价对话框
    var set_limit_price = function (cat_id_list, limit_price, adgroup_id) {
        $('#modal_limit_price').attr('adgroup_id', adgroup_id);
        $('#adg_limit_price').val(limit_price);
        $('#modal_limit_price [name="cat_path"]').empty();
        $('#modal_limit_price .cat_path').removeClass('danger_cat');
        $('#modal_limit_price [name="cat_avg_cpc"]').empty();
        $('#modal_limit_price .loading_tag').show();
        $('#modal_limit_price .input_error').removeClass('input_error');
        $('#modal_limit_price').modal('show');
        PT.sendDajax({'function':'mnt_get_cat_avg_cpc', 'cat_id_list':cat_id_list, 'namespace':'MntAdgBox'});
    }

    // 校验关键词限价
    var check_limit_price = function (limit_price){
        var error='';
        var limit_price_min = Number($('#modal_limit_price .limit_price_min').html()) || 1;
        var limit_price_max = Number($('#modal_limit_price .limit_price_max').html()) || 20;
        var limit_price_min = limit_price_min * 0.8;
        if($.trim(limit_price) ===''){
            error='值不能为空！';
        }else if(isNaN(limit_price)){
            error='值必须是数字！';
        }else if (Number(limit_price)<limit_price_min || Number(limit_price)>limit_price_max){
            error='值必须介于'+limit_price_min.toFixed(2)+'~'+limit_price_max.toFixed(2)+'元之间！';
        }
        return error;
    }

    // 更新托管宝贝列表
    var update_mnt_adgroup_table = function (tr_objs) {
        var data = $.map(tr_objs, function (obj) {
            var temp_obj = {
                'adgroup_id':$(obj).attr('adgroup_id'),
                'pic_url':$(obj).find('img').attr('src'),
                'title':$(obj).find('[name="item_title"]').html(),
                'limit_price':Number($('#adg_limit_price').val()).toFixed(2)
            };
            return temp_obj;
        });
        var table_data = template.render('mnt_adgroup_tr', {'data':data, 'mnt_type':mnt_type});
        $('#mnt_adgroup_table tbody').prepend(table_data);
        tr_objs.removeClass('hovering');
        $('#adgroup_recycle_bin').append(tr_objs);
        update_statistic_data();
    }

    // 加入托管
    var set_mnt_adg = function (tr_objs) {
        if (mnt_type=='2') {
	        var limit_price = tr_objs.attr('limit_price');
	        var adgroup_id = tr_objs.attr('adgroup_id');
            var cat_id = tr_objs.attr('cat_id');
            set_limit_price([cat_id], limit_price, adgroup_id);
        } else {
            update_mnt_adgroup_table(tr_objs);
        }
    }

    // 确认删除未托管宝贝
    var confirm_2del_unmnt_adg = function () {
        $.fancybox.close();
	    //$('#modal_del_unmnt_adg').modal('show');
        $.confirm({
          title:"注意",
          okBtn:'返回重选',
          cancelBtn:'确定',
          body:$('#modal_del_unmnt_adg').html(),
          okHide:function(e){$('#set_mnt_adg').click();}

        });
    }

    // 提交托管宝贝
    var submit_mnt_adg = function (callback_list, context) {
        PT.hide_loading();
        PT.show_loading('正在设置托管宝贝');
        if (!$.isArray(callback_list)) {
            callback_list = [];
        }
        if (!$.isPlainObject(context)) {
            context = {};
        }
        var mnt_adg_dict = {};
        var use_camp_limit = mnt_type==2? 0:1;
        $.map($('#mnt_adgroup_table tbody tr'), function (tr_obj) {
	        var adg_id = $(tr_obj).attr('adgroup_id');
	        if (adg_id) {
		        mnt_adg_dict[adg_id] = {};
		        if (mnt_type=='2') {
			        mnt_adg_dict[adg_id]['limit_price'] = Number($(tr_obj).find('[name="limit_price"]').text())*100;
		        }
	        }
        });
        PT.sendDajax({'function':'mnt_update_mnt_adg',
                                 'mnt_adg_dict':$.toJSON(mnt_adg_dict),
                                 'camp_id':campaign_id,
                                 'mnt_type':mnt_type,
                                 'flag':2,
                                 'namespace':'MntAdgBox',
                                 'use_camp_limit': use_camp_limit,
                                 'callback_list':$.toJSON(callback_list),
                                 'context':$.toJSON(context)
                                 });
        }

    var init_dom = function () {
        $('#modal_limit_price').off('keyup', '.keyup_restore');
        $('#modal_limit_price').on('keyup', '.keyup_restore', function(){
            $(this).closest('.input_error').removeClass('input_error');
        });

        // 设置重点宝贝限价
        $('#submit_impt_adg').unbind('click');
        $('#submit_impt_adg').click(function () {
             $("#check_limit_price2").submit()
//	        if ($('#modal_limit_price .loading_tag:visible').length) {
//		        PT.alert('正在加载数据，请等待加载完后再操作');
//		        return;
//	        }
//            var limit_price = Number($('#adg_limit_price').val());
//            var check_error = check_limit_price(limit_price);
//            if (!check_error) {
//                $('#adg_limit_price').closest('div').removeClass('input_error');
//                $('#modal_limit_price').modal('hide');
//                var adgroup_id = $('#modal_limit_price').attr('adgroup_id');
//                var tr_objs = $('#adgroup_table tr[adgroup_id="'+adgroup_id+'"]');
//                setTimeout(function(){update_mnt_adgroup_table(tr_objs)}, 300);
//            } else {
//                $('#adg_limit_price').closest('div').addClass('input_error');
//                $('#adg_limit_price').next().find('.icon-exclamation-sign').attr('data-original-title', check_error);
//            }
        });

         $("#check_limit_price2").validate({
            rules: {
              limit_price: {
                required: true,
                number:true,
                custom:true
              }
            },
            success: function() {
              $('#modal_limit_price').modal('hide');
              var adgroup_id = $('#modal_limit_price').attr('adgroup_id');
              var tr_objs = $('#adgroup_table tr[adgroup_id="'+adgroup_id+'"]');
              setTimeout(function(){update_mnt_adgroup_table(tr_objs)}, 300);
              return false;
            }
          })

        // 批量设置托管 (用 .batch_set_mnt 而不用 #batch_set_mnt 是为了避免固定表头出现bug)
        $('#adgroup_table .batch_set_mnt').unbind('mouseenter mouseleave');
        $('#adgroup_table .batch_set_mnt').bind('mouseenter mouseleave', function () {
            var batch_adg_num = Number($('.batch_adg_num').html());
            $('#adgroup_table tbody tr:lt('+batch_adg_num+')').toggleClass('hovering');
        });
        $('#adgroup_table .batch_set_mnt').unbind('click');
        $('#adgroup_table .batch_set_mnt').click(function () {
            if (Number($('.mnt_count').html())>0) {
                var batch_adg_num = Number($('.batch_adg_num').html());
                if (batch_adg_num) {
	                set_mnt_adg($('#adgroup_table tbody tr:lt('+batch_adg_num+')'));
                } else if ($('#load_more_adg').is(':visible')) {
	                PT.alert('请点击加载更多宝贝！');
                } else {
	                PT.alert('没有宝贝可以托管！');
                }
            } else {
                PT.alert('已达到托管数量上限，不能再添加宝贝了！');
            }
        });

        // 生成固定表头
        $.map($('#fancybox_mnt_adgroup .table_4fixedhead'), function (obj) {
            var table_id = $(obj).attr('source');
            $(obj).html($('#'+table_id).find('thead').clone(true));
        });

        // 搜索功能
        $('#search_adg_btn').unbind('click');
        $('#search_adg_btn').click(function(){
            var search_keyword_old = search_keyword;
            search_keyword = $('#search_adg_input').val();
            if (search_keyword != search_keyword_old) {
	            $('#adgroup_table tbody').empty();
	            page_no = 1;
            } else if ($('#load_more_adg').is(':hidden')) {
                PT.alert('已搜索完毕');
                return;
            }
            get_adg_list();
        });

        // 加载更多宝贝
        $('#load_more_adg').unbind('click');
        $('#load_more_adg').click(get_adg_list);

        // 表格行悬浮/离开事件
        $('#fancybox_mnt_adgroup').off('mouseenter mouseleave', 'tbody tr');
        $('#fancybox_mnt_adgroup').on('mouseenter mouseleave', 'tbody tr', function () {
	        $(this).toggleClass('hovering');
        });

        // 点击宝贝加入托管
        $('#adgroup_table').off('click', '[name="adgroup"]');
        $('#adgroup_table').on('click', '[name="adgroup"]', function () {
            if (Number($('.mnt_count').html())>0) {
                set_mnt_adg($(this).closest('tr'));
            } else {
                PT.alert('已达到托管数量上限，不能再添加宝贝了！');
            }
        });
        $('#adgroup_table').off('click', '.set_mnt');
        $('#adgroup_table').on('click', '.set_mnt', function () {
	        $(this).closest('tr').find('[name="adgroup"]').click();
        });

        // 点击宝贝取消托管
        $('#mnt_adgroup_table').off('click', '[name="mnt_adgroup"]');
        $('#mnt_adgroup_table').on('click', '[name="mnt_adgroup"]', function () {
            var adgroup_id = $(this).closest('tr').attr('adgroup_id');
            var tr_obj = $('#adgroup_recycle_bin tr[adgroup_id="'+adgroup_id+'"]');
            $('#adgroup_table').prepend(tr_obj);
            $(this).closest('tr').remove();
            update_statistic_data();
        });
        $('#mnt_adgroup_table').off('click', '.set_unmnt');
        $('#mnt_adgroup_table').on('click', '.set_unmnt', function () {
            $(this).closest('tr').find('[name="mnt_adgroup"]').click();
        });

        // 确定已托管宝贝，检查将删除的宝贝
        $('#fancybox_mnt_adgroup .btn_OK').unbind('click');
        $('#fancybox_mnt_adgroup .btn_OK').click(function () {
            if (Number($('.total_adg_count').html())>0 && mnt_type=='1') {
	            $('#modal_del_unmnt_adg .btn_OK2').show();
	            $('#modal_del_unmnt_adg .into_next_step').hide();
                confirm_2del_unmnt_adg();
            } else {
                $.fancybox.close();
            }
        });
        $('#modal_del_unmnt_adg .btn_OK2').unbind('click');
        $('#modal_del_unmnt_adg .btn_OK2').click(function () {
            $(this).attr('confirmed', '1');
            $(this).closest('.modal').modal('hide');
        });

        // 打开托管面板
        $('#set_mnt_adg').unbind('click');
        $('#set_mnt_adg').click(function(){
            campaign_id = $('#campaign_id').val();
            mnt_type = $('#mnt_type').val();
            mnt_max_num = Number($('#mnt_max_num').val()) || 0;

            switch (mnt_type) {
                case '1':
                    $('#fancybox_mnt_adgroup .batch_set_mnt').show().next().hide();
                    break;
                case '2':
                    $('#fancybox_mnt_adgroup .batch_set_mnt').hide().next().show();
                    break;
            }

            $.fancybox.open([{href:'#fancybox_mnt_adgroup'}], {helpers:{
                title : {type : 'outside'},
                overlay : {closeClick: false}
            }});

            if (!isNaN($('.total_adg_count').html())) return;

            // 初始化表格数据
            init_tables();
	        get_adg_list();
	    });

        // 从删除对话框返回继续设置托管
        $('#return_2set_mnt_adg').unbind('click');
        $('#return_2set_mnt_adg').click(function () {
            $('#modal_del_unmnt_adg').modal('hide');
            $('#set_mnt_adg').click();
        });
    }

	return {
		init: function () {
			init_dom();
		},
        init_tables: init_tables,
        confirm_2del_unmnt_adg: confirm_2del_unmnt_adg,
        get_cat_avg_cpc: function (cat_path, danger_descr, avg_cpc, avg_cpc_flag) {
            var modal_obj = $('#modal_limit_price');
            if (danger_descr) {
                cat_path += '<i class="icon-warning-sign tooltips r_color large marl_6" data-original-title="'+danger_descr+'"></i>';
                modal_obj.find('.cat_path').addClass('danger_cat');
            }
            PT.AddItemBox2.remove_loading_tag(modal_obj, 'cat_path', cat_path, 1);
            PT.AddItemBox2.remove_loading_tag(modal_obj, 'cat_avg_cpc', avg_cpc.toFixed(2), 1);
            modal_obj.find('i.tooltips').tooltip();
            if (!avg_cpc_flag) {
	            modal_obj.find('[name="cat_avg_cpc"]').prepend('<span class="r_color">查询失败</span>，默认为 ');
            }
            var limit_price_min = Math.min(avg_cpc*0.4, 0.5);
            var prompt_price = avg_cpc * 1.2;
            modal_obj.find('.prompt_price').html(prompt_price.toFixed(2));
            modal_obj.find('#adg_limit_price').attr('min', limit_price_min.toFixed(2));
            modal_obj.find('#adg_limit_price').next().find('div:first').html('['+ avg_cpc.toFixed(2) +'-20]');
            $('#adg_limit_price').val(prompt_price.toFixed(2));
        },
        get_adg_list_callback: function (data, has_more, total_adg_count, into_next_step) {
            var table_data = template.render('adgroup_tr', {'data':data});
            $('#adgroup_table tbody').append(table_data);
            $('#fancybox_mnt_adgroup .total_adg_count').attr('init_value', total_adg_count);
            $.map($('#mnt_adgroup_table tbody tr'), function (tr_obj) {
                var adgroup_id = $(tr_obj).attr('adgroup_id');
                $('#adgroup_table tbody tr[adgroup_id="'+adgroup_id+'"]').remove();
            });
            update_statistic_data();
            if (has_more && Number($('.total_adg_count').html())) {
	            // 判断中加入 Number($('.total_adg_count').html()) 是为了应付将所有宝贝都托管后，再输入关键词搜索的情况。
                $('#load_more_adg').show();
            } else {
                $('#load_more_adg').hide();
            }
            PT.hide_loading();
	        page_no++;
            if (into_next_step) {
                if (total_adg_count>0) {
	                $('#modal_del_unmnt_adg .into_next_step').show();
	                $('#modal_del_unmnt_adg .btn_OK2').hide();
                    confirm_2del_unmnt_adg();
                } else {
	                $.fancybox.close();
	                PT.ChooseMntcampaign.into_next_step();
                }
            }
        },
        submit_mnt_adg: submit_mnt_adg
	}
}();
