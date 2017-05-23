PT.namespace('AddItemBox2');
PT.AddItemBox2 = function () {
    var page_no = 1;
    var page_size = 50;
    var search_keyword = '';
    var campaign_id = 0;
    var mnt_type = $('#mnt_type').val();
    var mnt_max_num = 0;
    var mnt_num = 0; // 计划下已托管宝贝数
    var camp_dict = {}; //计划名称字典

    // 初始化表格数据
    var init_tables = function () {
        page_no = 1;
        search_keyword = '';
        mnt_max_num = Number($('#mnt_max_num').val()) || 0;
        $('#search_item_input').val('');
        $('#item_table tbody, #item_cart tbody, #item_recycle_bin').empty();
    }

    // 获取宝贝列表
    var get_item_list = function () {
        PT.show_loading('正在获取数据');
        PT.sendDajax({
            'function':'mnt_get_item_list',
            'campaign_id':campaign_id,
            'page_no':page_no,
            'page_size':page_size,
            'sSearch':search_keyword,
            'exclude_existed':1,  // 是否排除现有adgroup的标志
            'namespace':'AddItemBox2'
        });
    }

    // 更新宝贝个数统计
    var update_statistic_data = function () {
        var total_item_count = Number($('#fancybox_add_item .total_item_count').attr('init_value'));
        var mnt_adg_count = Number($('.mnt_adg_count').html()) || 0;
        var new_item_count = $('#item_cart tbody tr').length;
        var mnt_count0 = mnt_adg_count + new_item_count;
        mnt_num = Number($('.mnt_num').html()) || 0;
        if (mnt_type=='0') {
	        mnt_max_num = total_item_count;
        }
        var mnt_count = mnt_max_num - mnt_count0 - mnt_num;
        var batch_item_num = Math.min($('#item_table tbody tr').length, mnt_count);
        var danger_item_count = $('#item_cart tr.danger_cat').length;
        $('.total_item_count').html(total_item_count - new_item_count);
        $('.new_item_count').html(new_item_count);
        $('.mnt_count0').html(mnt_count0);
        $('.mnt_count').html(mnt_count);
        $('.batch_item_num').html(batch_item_num);
        $('.danger_item_count').html(danger_item_count);
        if (danger_item_count>0) {
            $('.danger_cats_info, #add_item_warning').show();
        } else {
            $('.danger_cats_info, #add_item_warning').hide();
        }
    }

    // 打开设置限价对话框
    var set_limit_price = function (cat_id_list, item_id) {
        $('#modal_init_limit_price').attr('item_id', item_id);
        $('#init_limit_price').val('');
        $('#modal_init_limit_price [name="cat_path"]').empty();
        $('#modal_init_limit_price .cat_path').removeClass('danger_cat');
        $('#modal_init_limit_price [name="cat_avg_cpc"]').empty();
        $('#modal_init_limit_price .loading_tag').show();
        $('#modal_init_limit_price .input_error').removeClass('input_error');
        $('#modal_init_limit_price').modal('show');
        PT.sendDajax({'function':'mnt_get_cat_avg_cpc', 'cat_id_list':cat_id_list, 'namespace':'AddItemBox2'});
    }

    // 校验关键词限价
//    var check_limit_price = function (limit_price){
//        var error='';
//        var limit_price_min = Number($('#modal_init_limit_price .limit_price_min').html()) || 0.8;
//        var limit_price_max = Number($('#modal_init_limit_price .limit_price_max').html()) || 20;
//        if($.trim(limit_price)==''){
//            error='值不能为空！';
//        }else if(isNaN(limit_price)){
//            error='值必须是数字！';
//        }else if (Number(limit_price)<limit_price_min || Number(limit_price)>limit_price_max){
//            error='值必须介于'+limit_price_min.toFixed(2)+'~'+limit_price_max.toFixed(2)+'元之间！';
//        }
//        return error;
//    }

    // 生成推广标题
    var generate_adg_title = function (data) {
        for (var i in data) {
            PT.sendDajax({
                'function':'web_getorcreate_adg_title_list',
                'item_id':data[i].item_id,
                'title':data[i].title,
                'namespace':'AddItemBox2'
            });
        }
    }

    // ajax加载动画
    var ajax_loading_animate = function (obj, number) {
        var obj_list = $('.ajax_loading').html() || '';
        if (obj_list.length<number) {
            $('.ajax_loading').append(obj);
        } else {
            $('.ajax_loading').empty();
        }
    }

    // ajax加载普通文本数据回调函数
    var remove_loading_tag = function (obj, key, value, hide) {
        if (hide) {
	        obj.find('.'+key+'>.loading_tag').hide();
        } else {
	        obj.find('.'+key+'>.loading_tag').remove();
        }
        obj.find('[name="'+key+'"]').html(value);
    }

    // 加载宝贝类目名
    var get_cat_path = function (data) {
        if (!data.length) return;
        if (mnt_type=='2') {
            var item_id = data[0].item_id;
            var cat_path = $('#modal_init_limit_price [name="cat_path"]').html();
            var tr_obj = $('#item_cart tr[item_id="'+item_id+'"]');
            remove_loading_tag(tr_obj, 'cat_path', cat_path);
            if (cat_path.indexOf('icon-warning-sign')!=-1) {
                tr_obj.addClass('danger_cat');
                tr_obj.find('i.tooltips').tooltip();
            }
            update_statistic_data();
        } else {
            for (var i in data) {
	            PT.sendDajax({
	                'function':'web_get_cat_path',
//	                'item_id':data[i].item_id,
//	                'cat_id':data[i].cat_id,
	                'cat_id_list':$.toJSON($.map(data, function (obj) {return Number(obj.cat_id)})),
	                'namespace':'AddItemBox2'
	            });
            }
        }
    }

    // 更新宝贝购物车
    var update_item_cart = function (tr_objs) {
        var data = $.map(tr_objs, function (obj) {
            var temp_obj = {
                'item_id':$(obj).attr('item_id'),
                'cat_id':$(obj).attr('cat_id'),
                'pic_url':$(obj).find('img').attr('src'),
                'title':$(obj).find('[name="item_title"]').html(),
                'limit_price':Number($('#init_limit_price').val()).toFixed(2),
                'danger_cat':$(obj).hasClass('danger_cat')
            };
            return temp_obj;
        });
        var table_data = template.render('item_cart_tr', {'data':data, 'mnt_type':mnt_type});
        $('#item_cart tbody').prepend(table_data);
        tr_objs.removeClass('hovering');
        $('#item_recycle_bin').append(tr_objs);
        update_statistic_data();
        generate_adg_title(data);
        get_cat_path(data);
    }

    // 加入宝贝购物车
    var add_new_item = function (tr_objs) {
        var no_pic_count = tr_objs.find('img[src="/site_media/jl/img/no_photo_100x100.jpg"]').length;
        if (no_pic_count>0) {
            if (tr_objs.length==1) {
	            PT.alert('宝贝未设置主图');
            } else {
	            PT.alert('有' + no_pic_count + '个宝贝未设置主图');
            }
            return;
        }
        if (mnt_type=='2') {
            var item_id = tr_objs.attr('item_id');
            var cat_id = tr_objs.attr('cat_id');
            set_limit_price([cat_id], item_id);
        } else {
            update_item_cart(tr_objs);
        }
    }

    // 检查宝贝类目
//    var check_danger_cats = function () {
//        if ($('#item_cart .loading_tag:visible').length) {
//            PT.alert('正在加载数据，请等待加载完后再操作');
//            return;
//        }
//        var cat_id_list = $.map($('#item_cart tbody tr'), function (obj) {
//            return $(obj).attr('cat_id');
//        });
//	    PT.show_loading('正在检查宝贝类目是否安全');
//	    PT.sendDajax({
//		    'function':'web_check_danger_cats',
//		    'cat_id_list':cat_id_list
//	    });
//    }

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

    // 检查推广标题长度
    var check_adg_title_length = function (adg_title, tr_obj) {
	    var char_delta = Math.floor(20-bytes_len(adg_title)/2);
	    if (char_delta>=0) {
		    tr_obj.find('[name="title_length_prompt"]').removeClass('overflow').addClass('margin');
	    } else {
		    tr_obj.find('[name="title_length_prompt"]').removeClass('margin').addClass('overflow');
	    }
	    tr_obj.find('[name="char_delta"]').html(Math.abs(char_delta));
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

    // 提交新增宝贝
    var submit_new_item = function (callback_list, context) {
        PT.hide_loading();
        PT.show_loading('正在添加新宝贝');
        if (!$.isArray(callback_list)) {
            callback_list = [];
        }
        if (!$.isPlainObject(context)) {
            context = {};
        }
        var new_item_dict = {};
        $.map($('#item_cart tbody tr'), function (tr_obj) {
	        var item_id = $(tr_obj).attr('item_id');
	        if (item_id) {
		        new_item_dict[item_id] = [{}];
		        new_item_dict[item_id][0]['title'] = $.trim($(tr_obj).find('[name="adg_title"]').val());
			    new_item_dict[item_id][0]['img_url'] = handle_img_url($(tr_obj).find('[name="new_item"] img:eq(0)').attr('src'));
		        if (mnt_type=='2') {
			        new_item_dict[item_id][0]['limit_price'] = Number($(tr_obj).find('[name="limit_price"]').text())*100;
		        }
	        }
        });
        mnt_type = $('#mnt_type').val();
        PT.sendDajax({'function':'web_add_items2',
                                 'new_item_dict':$.toJSON(new_item_dict),
                                 'camp_id':campaign_id,
                                 'mnt_type':mnt_type,
                                 'namespace':'AddItemBox2',
                                 'callback_list':$.toJSON(callback_list),
                                 'context':$.toJSON(context)
                                 });
    }

    var init_dom = function () {
	    // 构造计划名称字典
	    $('[name="camp_title"]').each(function () {
		    var camp_id = $(this).attr('camp_id');
		    var title = $(this).val();
		    var text = PT.truncate_str_8true_length(title, 20);
		    camp_dict[camp_id] = {'title':title, 'text':text};
	    });

        switch (mnt_type) {
	        case '1':
		        $('[name="mnt_name"]').html('长尾托管');
		        break;
	        case '2':
	            $('[name="mnt_name"]').html('重点托管');
	            break;
        }
        $('#modal_init_limit_price').off('keyup', '.keyup_restore');
        $('#modal_init_limit_price').on('keyup', '.keyup_restore', function(){
            $(this).closest('.input_error').removeClass('input_error');
        });

        // 设置重点宝贝限价
        $('#submit_impt_item').unbind('click');
        $('#submit_impt_item').click(function () {
          $("#check_limit_price").submit()
//            if ($('#modal_init_limit_price .loading_tag:visible').length) {
//                PT.alert('正在加载数据，请等待加载完后再操作');
//                return;
//            }
//            var limit_price = Number($('#init_limit_price').val());
//            var check_error = check_limit_price(limit_price);
//            if (!check_error) {
//                $('#init_limit_price').closest('div').removeClass('input_error');
//                $('#modal_init_limit_price').modal('hide');
//                var item_id = $('#modal_init_limit_price').attr('item_id');
//                var tr_objs = $('#item_table tr[item_id="'+item_id+'"]');
//                setTimeout(function(){update_item_cart(tr_objs)}, 300);
//            } else {
//                $('#init_limit_price').closest('div').addClass('input_error');
//                $('#init_limit_price').next().find('.icon-exclamation-sign').attr('data-original-title', check_error);
//            }
        });

         $("#check_limit_price").validate({
            rules: {
              limit_price: {
                required: true,
                number:true,
                custom:true
              }
            },
            success: function() {
              $('#modal_init_limit_price').modal('hide');
              var item_id = $('#modal_init_limit_price').attr('item_id');
              var tr_objs = $('#item_table tr[item_id="'+item_id+'"]');
              setTimeout(function(){update_item_cart(tr_objs)}, 300);
              return false;
            }
          })

        // 批量添加宝贝 (用 .batch_add_item 而不用 #batch_add_item 是为了避免固定表头出现bug)
        $('#item_table .batch_add_item').unbind('mouseenter mouseleave');
        $('#item_table .batch_add_item').bind('mouseenter mouseleave', function () {
            var batch_item_num = Number($('.batch_item_num').html());
            $('#item_table tbody tr:lt('+batch_item_num+')').toggleClass('hovering');
        });
        $('#item_table .batch_add_item').unbind('click');
        $('#item_table .batch_add_item').click(function () {
            if (Number($('.mnt_count').html())>0) {
                var batch_item_num = Number($('.batch_item_num').html());
                if (batch_item_num) {
	                add_new_item($('#item_table tbody tr:lt('+batch_item_num+')'));
                } else if ($('#load_more_item').is(':visible')) {
	                PT.alert('请点击加载更多宝贝！');
                } else {
	                PT.alert('没有宝贝可以添加！');
                }
            } else {
                PT.alert('已达到托管数量上限，不能再添加宝贝了！');
            }
        });

        // 生成固定表头
        $.map($('#fancybox_add_item .table_4fixedhead'), function (obj) {
            var table_id = $(obj).attr('source');
            $(obj).html($('#'+table_id).find('thead').clone(true));
        });

        // 搜索功能
        $('#search_item_btn').unbind('click');
        $('#search_item_btn').click(function(){
	        if ($('#item_cart .loading_tag:visible').length) {
	            PT.alert('正在加载数据，请等待加载完后再操作');
	            return;
	        }
            var search_keyword_old = search_keyword;
            search_keyword = $('#search_item_input').val();
            if (search_keyword != search_keyword_old) {
	            $('#item_table tbody').empty();
	            page_no = 1;
            } else if ($('#load_more_item').is(':hidden')) {
                PT.alert('已搜索完毕');
                return;
            }
            get_item_list();
        });

        // 加载更多宝贝
        $('#load_more_item').unbind('click');
        $('#load_more_item').click(get_item_list);

        // 表格行悬浮/离开事件
        $('#fancybox_add_item').off('mouseenter mouseleave', 'tbody tr');
        $('#fancybox_add_item').on('mouseenter mouseleave', 'tbody tr', function () {
            $(this).toggleClass('hovering');
        });

        // 点击添加宝贝
        $('#item_table').off('click', '[name="item"]');
        $('#item_table').on('click', '[name="item"]', function () {
            if (Number($('.mnt_count').html())>0) {
                add_new_item($(this).closest('tr'));
            } else {
                PT.alert('已达到托管数量上限，不能再添加宝贝了！');
            }
        });
        $('#item_table').off('click', '.add_item');
        $('#item_table').on('click', '.add_item', function () {
            $(this).closest('tr').find('[name="item"]').click();
        });

        // 取消添加宝贝
        $('#item_cart').off('click', '[name="new_item"]');
        $('#item_cart').on('click', '[name="new_item"]', function () {
            var item_id = $(this).closest('tr').attr('item_id');
            var tr_obj = $('#item_recycle_bin tr[item_id="'+item_id+'"]');
            $('#item_table').prepend(tr_obj);
            $(this).closest('tr').remove();
            update_statistic_data();
        });
        $('#item_cart').off('click', '.del_item');
        $('#item_cart').on('click', '.del_item', function () {
            $(this).closest('tr').find('[name="new_item"]').click();
        });

        // 动态检测添加宝贝的推广标题长度
        $('#item_cart').off('keyup', 'input[name="adg_title"]');
        $('#item_cart').on('keyup', 'input[name="adg_title"]', function () {
	        check_adg_title_length($(this).val(), $(this).closest('tr'));
        });

        // 确定要添加的宝贝，检查宝贝推广标题长度和宝贝类目
        $('#fancybox_add_item .btn_OK').unbind('click');
        $('#fancybox_add_item .btn_OK').click(function () {
            var title_is_empty=false;
	        $('#modal_new_item_info .btn_OK2').show();
	        $('#modal_new_item_info .into_next_step').hide();
		    if ($('#item_cart .loading_tag:visible').length) {
		        PT.alert('正在加载数据，请等待加载完后再操作');
		        return;
		    }

            if ($('#item_cart [name="title_length_prompt"].overflow').length>0) {
		        PT.alert('有些推广标题的长度超过20个汉字');
		        return;
	        }

            if(!$('#item_cart tbody tr').length){
                PT.alert('请选择宝贝');
                return;
            }

            $('input[name=adg_title]').each(function(){
                if($.trim(this.value)==""){
                    title_is_empty=true;
                }
                return;
            });

            if(title_is_empty){
                PT.alert('有些推广标题为空');
                return;
            }
//            check_danger_cats();
    //        $('#modal_new_item_info').modal('show');
            $.confirm({
              title:"注意",
              body:$('#modal_new_item_info').html(),
              okHide:function(e){
                if ($('#mnt_wizard').length) {
                    $(this).attr('confirmed', '1');
                } else {
                    submit_new_item([], {});
                }
              }

            });
            $.fancybox.close();
        });
//        $('#modal_new_item_info .btn_OK2').unbind('click');
//        $('#modal_new_item_info .btn_OK2').click(function () {
//		    $(this).closest('.modal').modal('hide');
//	        if ($('#mnt_wizard').length) {
//		        $(this).attr('confirmed', '1');
//	        } else {
//		        submit_new_item([], {});
//	        }
//        });

        // 打开添加宝贝面板
        $('#add_item').unbind('click');
        $('#add_item').click(function(){
            campaign_id = $('#campaign_id').val();
            mnt_type = $('#mnt_type').val();
            mnt_max_num = Number($('#mnt_max_num').val()) || 0;

            if (mnt_type=='2') {
                $('#fancybox_add_item .batch_add_item').hide().next().show();
            } else {
                $('#fancybox_add_item .batch_add_item').show().next().hide();
            }
            if ($.inArray(mnt_type, ['1', '2']) != -1) {
                $('.to_mnt').show();
            } else {
                $('.to_mnt').hide();
            }

            $.fancybox.open([{href:'#fancybox_add_item'}], {helpers:{
                title : {type : 'outside'},
                overlay : {closeClick: false}
            }});

            if (!isNaN($('.total_item_count').html())) return;

            // 初始化表格数据
            init_tables();
	        get_item_list();
	    });

        // 返回添加宝贝面板，以便排除属于限制类目的宝贝
//        $('#return_2add_item').unbind('click');
//        $('#return_2add_item').click(function () {
//            $('#modal_new_item_info').modal('hide');
//            $('#add_item').click();
//        });
    }

	return {
		init: function () {
			init_dom();
		},
		ajax_loading_animate: function (obj, number, millisec) {
		    var ajax_loading_animate_id = Number($('#ajax_loading_animate_id').val());
		    if (ajax_loading_animate_id) {
			    window.clearInterval(ajax_loading_animate_id);
		    }
		    ajax_loading_animate_id = setInterval(function(){ajax_loading_animate(obj, number);}, millisec);
		    $('#ajax_loading_animate_id').val(ajax_loading_animate_id);
		},
		remove_loading_tag: remove_loading_tag,
        init_tables: init_tables,
//        check_danger_cats: check_danger_cats,
        get_cat_avg_cpc: function (cat_path, danger_descr, avg_cpc, avg_cpc_flag) {
            var modal_obj = $('#modal_init_limit_price, #modal_limit_price');
            if (danger_descr) {
                cat_path += '<i class="icon-warning-sign tooltips r_color large marl_6" data-original-title="'+danger_descr+'"></i>';
                modal_obj.find('.cat_path').addClass('danger_cat');
            }
            remove_loading_tag(modal_obj, 'cat_path', cat_path, 1);
            remove_loading_tag(modal_obj, 'cat_avg_cpc', avg_cpc.toFixed(2), 1);
            modal_obj.find('i.tooltips').tooltip();
            if (!avg_cpc_flag) {
	            modal_obj.find('[name="cat_avg_cpc"]').prepend('<span class="s_color">未获取到</span>，默认为 ');
            }
            var limit_price_min = Math.min(avg_cpc*0.4, 0.5);
            var prompt_price = avg_cpc * 1.2;
            // limit_price_min = Math.min(limit_price_min, 20);
            modal_obj.find('.prompt_price').html(prompt_price.toFixed(2));
            modal_obj.find('#init_limit_price, #adg_limit_price').each(function(){
                $(this).attr('min', limit_price_min.toFixed(2));
                $(this).next().find('div:first').html('['+ avg_cpc.toFixed(2) +'-20]');
                if($(this).val() === '') {
                    $(this).val(prompt_price.toFixed(2));
                }
            });

        },
        get_item_list_callback: function (data, has_more, total_item_count) {
            var table_data = template.render('item_tr', {'data':data, 'camp_dict':camp_dict});
            $('#item_table tbody').append(table_data);
            $('#fancybox_add_item .total_item_count').attr('init_value', total_item_count);
            $.map($('#item_cart tbody tr'), function (tr_obj) {
                var item_id = $(tr_obj).attr('item_id');
                $('#item_table tbody tr[item_id="'+item_id+'"]').remove();
            });
            update_statistic_data();
            if (has_more && Number($('.total_item_count').html())) {
                $('#load_more_item').show();
            } else {
                $('#load_more_item').hide();
            }
            PT.hide_loading();
            page_no++;
        },
//        check_danger_cats_callback: function (cat_id_dict) {
//            if ($.inArray(mnt_type, ['1', '2']) != -1) {
//                $('.to_mnt').show();
//            } else {
//                $('.to_mnt').hide();
//            }
//            $.map(cat_id_dict, function (danger_descr, cat_id) {
//                var tr_obj = $('#fancybox_add_item tr[cat_id="'+cat_id+'"]');
//                if (!tr_obj.hasClass('danger_cat')) {
//	                tr_obj.addClass('danger_cat');
//	                tr_obj.find('[name="cat_path"]').append('<i class="icon-warning-sign tooltips r_color large marl_6" data-original-title="'+danger_descr+'"></i>');
//	                tr_obj.find('i.tooltips').tooltip();
//                }
//            });
//            update_statistic_data();
//            $.fancybox.close();
//            $('#modal_new_item_info').modal('show');
//        },
        getorcreate_adg_title_list_callback: function (adg_title_list, item_id) {
	        var adg_title = adg_title_list[0];
            var tr_obj = $('#item_cart tr[item_id="'+item_id+'"]');
            tr_obj.find('.adg_title1>.loading_tag').remove();
            tr_obj.find('.adg_title1>input').val(adg_title).show();
            check_adg_title_length(adg_title, tr_obj);
            tr_obj.find('[name="title_length_prompt"]').show();
        },
//        get_cat_path_callback: function (item_cat_dict) {
//            for (var item_id in item_cat_dict) {
//	            var tr_obj = $('#item_cart tr[item_id="'+item_id+'"]');
//	            var cat_path = item_cat_dict[item_id][0];
//	            var danger_descr = item_cat_dict[item_id][1];
//	            if (danger_descr && !tr_obj.hasClass('danger_cat')) {
//	                cat_path += '<i class="icon-warning-sign tooltips r_color large marl_6" data-original-title="'+danger_descr+'"></i>';
//	                tr_obj.addClass('danger_cat');
//	            }
//	            remove_loading_tag(tr_obj, 'cat_path', cat_path);
//	            tr_obj.find('i.tooltips').tooltip();
//            }
//            update_statistic_data();
//        },
        get_cat_path_callback: function (cat_dict) {
            $.map($('#item_cart tbody tr'), function (tr_obj) {
                var cat_info = cat_dict[$(tr_obj).attr('cat_id')];
                var cat_path, danger_descr;
                if (cat_info) {
                    cat_path = cat_info[0];
                    danger_descr = cat_info[1];
                } else {
                    cat_path = '未获取到值';
                    danger_descr = '';
                }
                if (danger_descr && !$(tr_obj).hasClass('danger_cat')) {
                    cat_path += '<i class="icon-warning-sign tooltips r_color large marl_6" data-original-title="'+danger_descr+'"></i>';
                    $(tr_obj).addClass('danger_cat');
                }
                remove_loading_tag($(tr_obj), 'cat_path', cat_path);
                $(tr_obj).find('i.tooltips').tooltip();
            });
            update_statistic_data();
        },
        submit_new_item: submit_new_item,
        add_items_callback: function (result, fail_msg, msg) {
            PT.hide_loading();
            var init_adgroup_table = function (mnt_type) {
	            $('.total_item_count').html('---');
                var rpt_days = $('[name="last_day"]').val() || '1';
                if (mnt_type=='0') {
                    PT.Adgroup_list.select_call_back(rpt_days);
                } else if (mnt_type=='1' || mnt_type=='2') {
                    PT.MntAdg.select_call_back(rpt_days);
                }
            }
            if (result==0) {
                PT.alert('宝贝添加失败：'+fail_msg);
            } else {
                if($.isPlainObject(fail_msg) && !$.isEmptyObject(fail_msg)){
                    msg += '<br/>' + template.render('add_item_fail_msg', {'fail_msg':fail_msg});
                }
                PT.alert(msg, null, init_adgroup_table, [mnt_type], null, 0);
            }
        }
	}
}();
