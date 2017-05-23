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
        var limit_price_min = Number($('#modal_limit_price .limit_price_min').html()) || 0.8;
        var limit_price_max = Number($('#modal_limit_price .limit_price_max').html()) || 20;
        if($.trim(limit_price)==''){
            error='值不能为空！';
        }else if(isNaN(limit_price)){
            error='值必须是数字！';
        }else if (Number(limit_price)<limit_price_min || Number(limit_price)>limit_price_max){
            error='值必须介于'+limit_price_min.toFixed(2)+'~'+limit_price_max.toFixed(2)+'元之间！';
        }
        return error;
    }
    
    // 检查并获取宝贝图片
    var get_item_imgs = function (tr_objs) {
	    PT.show_loading('正在处理');
	    var all_item_list = [], to_handle_item_list = [];
	    $.map(tr_objs, function (tr_obj) {
		    all_item_list.push($(tr_obj).attr('item_id'));
            if ($(tr_obj).find('[name="item_imgs"]').length==0) {
                to_handle_item_list.push(Number($(tr_obj).attr('item_id')));
            }
	    });
	    PT.sendDajax({'function':'web_get_item_imgs',
		    'item_id_list':$.toJSON(to_handle_item_list),
		    'context':$.toJSON({'all_item_list':all_item_list}),
		    'namespace':'MntAdgBox'
	    });
    }
    
    // 更新托管宝贝列表
    var update_mnt_adgroup_table = function (data) {
        var table_data = template.render('mnt_adgroup_tr', {'data':data, 'mnt_type':mnt_type});
        $('#mnt_adgroup_table tbody').prepend(table_data);
        var tr_objs = $();
//        var adg_id_list = [];
        $.map(data, function (obj) {
            tr_objs = tr_objs.add($('#adgroup_table tr[item_id="'+obj['item_id']+'"]'));
//            adg_id_list.push(Number(obj['adgroup_id']));
        });
        tr_objs.removeClass('hovering');
        $('#adgroup_recycle_bin').append(tr_objs);
        update_statistic_data();
        getorcreate_adg_title_list(data);
    }
    
    // 加入托管
    var set_mnt_adg = function (tr_objs) {
        if (mnt_type=='2') {
	        var limit_price = tr_objs.attr('limit_price');
	        var adgroup_id = tr_objs.attr('adgroup_id');
            var cat_id = tr_objs.attr('cat_id');
            set_limit_price([cat_id], limit_price, adgroup_id);
        } else {
//            update_mnt_adgroup_table(tr_objs);
            get_item_imgs(tr_objs);
        }
    }

    // 确认删除未托管宝贝
    var confirm_2del_unmnt_adg = function () {
        $.fancybox.close();
	    $('#modal_del_unmnt_adg').modal('show');
    }
    
    // 处理图片链接
    var handle_img_url = function (img_url) {
        var suffix_list = ['.jpg', '.png', '.gif'];
        for (var i in suffix_list) {
            var suffix = suffix_list[i];
            if (img_url.indexOf(suffix+'_')!=-1) {
                img_url = img_url.split(suffix+'_', 1)[0] + suffix;
                return img_url;
            }
        }
        var suffix_list2 = ['_100x100.jpg', '_160x160.jpg', '_sum.jpg'];
        $.map(suffix_list2, function (suffix) {
            img_url = img_url.replace(new RegExp(suffix), '');
        })
        return img_url;
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
        var mnt_adg_dict = {}, update_creative_dict = {}, new_creative_list = [];
        $.map($('#mnt_adgroup_table tbody tr'), function (tr_obj) {
	        var adg_id = Number($(tr_obj).attr('adgroup_id'));
	        if (adg_id) {
		        mnt_adg_dict[adg_id] = {};
		        if (mnt_type=='2') {
			        mnt_adg_dict[adg_id]['limit_price'] = Number($(tr_obj).find('[name="limit_price"]').text())*100;
		        }
		        for (var i=0;i<2;i++) {
			        var input_obj = $(tr_obj).find('[name="adg_title"]:eq('+i+')');
			        var img_url = handle_img_url($(tr_obj).find('[name="creative_img"]:eq('+i+')').attr('src'));
                    if (input_obj.parent().hasClass('modified')) {
                        update_creative_dict[Number(input_obj.attr('creative_id'))] = [adg_id, $.trim(input_obj.val()), img_url];
                    } else if (input_obj.parent().hasClass('new')) {
	                    new_creative_list.push([adg_id, $.trim(input_obj.val()), img_url]);
                    }
		        }
	        }
        });
        PT.sendDajax({'function':'mnt_update_mnt_adg',
                                 'mnt_adg_dict':$.toJSON(mnt_adg_dict),
                                 'update_creative_dict':$.toJSON(update_creative_dict),
                                 'new_creative_list':$.toJSON(new_creative_list),
                                 'camp_id':campaign_id,
                                 'mnt_type':mnt_type,
                                 'flag':2,
                                 'namespace':'MntAdgBox',
                                 'callback_list':$.toJSON(callback_list),
                                 'context':$.toJSON(context)
                                 });
    }
        
    // 加载双创意标题，不够则生成标题
    var getorcreate_adg_title_list = function (data) {
	    for (var i in data) {
		    PT.sendDajax({
			    'function':'web_getorcreate_adg_title_list',
				'adgroup_id':data[i]['adgroup_id'],
				'item_id':data[i]['item_id'],
				'namespace':'MntAdgBox'
			});
	    }
    }
    
    //计算字符串的字节长度
    var bytes_len = function(str){
        var bytes_length = 0;
        for(var i=0;i<str.length;i++){
            if(str.charCodeAt(i)>255){
                bytes_length+=2;
            }else{
                bytes_length+=1;
            }
        }
        return bytes_length;
    }
    
    // 检查创意标题长度
    var check_adg_title_length = function (adg_title, parent_obj) {
        var char_delta = Math.floor(20-bytes_len($.trim(adg_title))/2);
        if (char_delta>=0) {
            parent_obj.find('[name="title_length_prompt"]').removeClass('overflow').addClass('margin');
            if (char_delta==20) {
                parent_obj.find('[name="title_length_prompt"]').addClass('blank');
            } else {
                parent_obj.find('[name="title_length_prompt"]').removeClass('blank');
            }
        } else {
            parent_obj.find('[name="title_length_prompt"]').removeClass('margin blank').addClass('overflow');
        }
        parent_obj.find('[name="char_delta"]').html(Math.abs(char_delta));
    }
    
    // 检查创意标题或图片是否被改动
    var check_creative_ismodified = function (item_id, no) {
	    var tr_obj = $('#mnt_adgroup_table tr[item_id="'+item_id+'"]');
	    var input_obj = tr_obj.find('[name="adg_title"]:eq('+no+')');
	    if (input_obj.parent().hasClass('current')) {
		    var creative_img = handle_img_url(tr_obj.find('[name="creative_img"]:eq('+no+')').attr('src')).split('.taobaocdn.com/', 2)[1];
		    var org_img = input_obj.attr('org_img').split('.taobaocdn.com/', 2)[1];
		    if (input_obj.val()!=input_obj.attr('org_value') || creative_img!=org_img) {
			    input_obj.parent().addClass('modified');
		    } else {
			    input_obj.parent().removeClass('modified');
		    }
	    }
    }
    
    var init_dom = function () {
        $('#modal_limit_price').off('keyup', '.keyup_restore');
        $('#modal_limit_price').on('keyup', '.keyup_restore', function(){
            $(this).closest('.input_error').removeClass('input_error');
        });
        
        // 设置重点宝贝限价
        $('#submit_impt_adg').unbind('click');
        $('#submit_impt_adg').click(function () {
	        if ($('#modal_limit_price .loading_tag:visible').length) {
		        PT.alert('正在加载数据，请等待加载完后再操作');
		        return;
	        }
            var limit_price = Number($('#adg_limit_price').val());
            var check_error = check_limit_price(limit_price);
            if (!check_error) {
                $('#adg_limit_price').closest('div').removeClass('input_error');
                $('#modal_limit_price').modal('hide');
                var adgroup_id = $('#modal_limit_price').attr('adgroup_id');
                var tr_objs = $('#adgroup_table tr[adgroup_id="'+adgroup_id+'"]');
//                setTimeout(function(){update_mnt_adgroup_table(tr_objs)}, 300);
                setTimeout(function(){get_item_imgs(tr_objs)}, 300);
            } else {
                $('#adg_limit_price').closest('div').addClass('input_error');
                $('#adg_limit_price').next().find('.icon-exclamation-sign').attr('data-original-title', check_error);
            }
        });
            
        // 批量设置托管 【注：用 .batch_set_mnt 而不用 #batch_set_mnt 是为了避免固定表头出现bug】
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
        $('#fancybox_mnt_adgroup').on('mouseenter', 'tbody tr', function () {
	        $(this).addClass('hovering');
        });
        $('#fancybox_mnt_adgroup').on('mouseleave', 'tbody tr', function () {
            $(this).removeClass('hovering');
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
        
        // 点击打开选择创意图片框【注：选择创意图片部分的主要JS和HTML在add_item_box2功能的对应文件上】
        $('#mnt_adgroup_table').off('click', '[name="creative_img"]');
        $('#mnt_adgroup_table').on('click', '[name="creative_img"]', function () {
            var item_id = $(this).closest('tr').attr('item_id');
            var no = $(this).parent().index();
            $('#modal_select_creative_img').attr({'item_id':item_id, 'no':no});
            $('#creative_img_no').html(no+1);
            var item_imgs = $.map($(this).closest('td').find('[name="item_imgs"] li'), function (li_obj) {
                return $(li_obj).html();
            });
            var html_item_imgs = template.render('item_imgs', {'item_imgs':item_imgs});
            $('#modal_select_creative_img .modal-body').html(html_item_imgs);
            $('#modal_select_creative_img').modal('show');
        });
        
        // 点击宝贝取消托管
        $('#mnt_adgroup_table').off('click', '.set_unmnt');
        $('#mnt_adgroup_table').on('click', '.set_unmnt', function () {
//            $(this).closest('tr').find('[name="mnt_adgroup"]').click();
            var adgroup_id = $(this).closest('tr').attr('adgroup_id');
            var tr_obj = $('#adgroup_recycle_bin tr[adgroup_id="'+adgroup_id+'"]');
            $('#adgroup_table').prepend(tr_obj);
            $(this).closest('tr').remove();
            update_statistic_data();
        });
        
        // 动态检测添加宝贝的创意标题长度和是否与原标题相同
        $('#mnt_adgroup_table').off('keyup', 'input[name="adg_title"]');
        $('#mnt_adgroup_table').on('keyup', 'input[name="adg_title"]', function () {
            check_adg_title_length($(this).val(), $(this).parent());
            check_creative_ismodified($(this).closest('tr').attr('item_id'), $(this).attr('no'));
        });
        
        // 确定已托管宝贝，检查将删除的宝贝
        $('#fancybox_mnt_adgroup .btn_OK').unbind('click');
        $('#fancybox_mnt_adgroup .btn_OK').click(function () {
            if ($('#mnt_adgroup_table .none_crt_img').length) {
                PT.alert('有宝贝未选择创意图片，请先选择图片');
                return;
            } else if ($('#mnt_adgroup_table .loading_tag:visible').length) {
                PT.alert('正在加载数据，请等待加载完后再操作');
                return;
            } else if ($('#mnt_adgroup_table [name="title_length_prompt"].overflow').length>0) {
                PT.alert('有些创意标题的长度超过20个汉字');
                return;
            } else if ($('#mnt_adgroup_table [name="title_length_prompt"].blank').length>0) {
                PT.alert('有些创意标题为空');
                return;
            }
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
//            var limit_price_min = Math.max(avg_cpc*0.8, 0.8);
            var limit_price_min = avg_cpc*0.8;
            limit_price_min = Math.min(limit_price_min, 20);
            modal_obj.find('.limit_price_min').html(limit_price_min.toFixed(2));
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
        submit_mnt_adg: submit_mnt_adg,
        get_item_imgs_callback: function (item_dict, context) {
	        var data = $.map(context['all_item_list'], function (item_id) {
		        var tr_obj = $('#adgroup_table tr[item_id="'+item_id+'"]');
		        var item_imgs = item_dict[item_id];
		        if (item_imgs) {
			        var html_item_imgs = template.render('ul_item_imgs', {'item_imgs':item_imgs});
			        tr_obj.find('td:first').append(html_item_imgs);
		        } else {
			        item_imgs = $.map(tr_obj.find('[name="item_imgs"] li'), function (li_obj) {return $(li_obj).html();});
		        }
		        return {'adgroup_id':tr_obj.attr('adgroup_id'),
			        'item_id':item_id,
			        'item_imgs':item_imgs,
			        'title':tr_obj.find('[name="item_title"]').html(),
			        'limit_price':Number($('#adg_limit_price').val()).toFixed(2)
		        };
	        });
	        update_mnt_adgroup_table(data);
        },
        getorcreate_adg_title_list_callback: function (adg_title_list, item_id) {
	        var tr_obj = $('#mnt_adgroup_table tr[item_id="'+item_id+'"]');
	        var creative_obj = adg_title_list[0], new_adg_title = adg_title_list[1];
	        var adg_title_obj = tr_obj.find('.adg_title');
	        adg_title_obj.children('.loading_tag').remove();
            if ($.isPlainObject(creative_obj) && !$.isEmptyObject(creative_obj)) {
	            var i = 0;
	            for (var creative_id in creative_obj) {
		            var creative_title = creative_obj[creative_id][0], creative_img = creative_obj[creative_id][1];
		            adg_title_obj.eq(i).addClass('current').children('[name="adg_title"]').attr({'creative_id':creative_id, 'org_value':creative_title, 'org_img':creative_img, 'no':i}).val(creative_title).show();
		            tr_obj.find('[name="creative_img"]:eq('+i+')').replaceWith('<img name="creative_img" src="'+creative_img+'_100x100.jpg" width="100" height="100" title="点击换图" />');
		            check_adg_title_length(creative_title, adg_title_obj.eq(i));
		            i++;
	            }
	            if (i==1) {
		            adg_title_obj.eq(1).addClass('new').children('[name="adg_title"]').val(new_adg_title).show();
		            adg_title_obj.eq(1).children().first().html('新增创意2');
		            check_adg_title_length(new_adg_title, adg_title_obj.eq(1));
	            }
	            adg_title_obj.children('[name="title_length_prompt"]').show();
            } else {
	            adg_title_obj.hide();
	            tr_obj.find('.error_list').html('<i class="icon-warning-sign large marr_3"></i>获取创意失败，请先尝试同步直通车结构数据').show();
            }
        },
        check_creative_ismodified:check_creative_ismodified
	}	
}();