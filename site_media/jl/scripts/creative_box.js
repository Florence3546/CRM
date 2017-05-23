PT.namespace('CreativeBox');
PT.CreativeBox = function () {
	var app, shop_id, campaign_id, adgroup_id = $('#adgroup_id').val(), item_id = $('#item_id').val();
	// 获取宝贝创意
	var get_creative_by_id = function () {
	    var request_data=['id',
	                    'title',
	                    'img_url',
	                    'qr.impressions',
	                    'qr.click',
	                    'qr.ctr',
	                    'qr.cpc',
	                    'qr.paycount',
	                    'qr.favcount',
	                    'qr.conv',
	                    'qr.roi',
	                    'qr.favcount',
	                    'qr.cost',
	                    'qr.pay'
	                    ];
	    if (!app) {
		    app = 'web';
	    }
	    PT.sendDajax({'function':app+'_get_creative_by_id',
		    'app':app,
		    'shop_id':shop_id,
		    'adgroup_id':adgroup_id,
		    'data':$.toJSON(request_data),
		    'call_back':'PT.CreativeBox.creative_callback',
		    'last_day':$('#creative_last_day').val()
		    });
	}
    
    // 检查创意标题长度
    var check_crt_title = function (adg_title, title_length_prompt) {
        var char_delta = Math.floor(20-PT.true_length($.trim(adg_title))/2);
        if (char_delta>=0) {
            title_length_prompt.removeClass('overflow').addClass('margin');
            if (char_delta==20) {
                title_length_prompt.addClass('blank');
            } else {
                title_length_prompt.removeClass('blank');
            }
        } else {
            title_length_prompt.removeClass('margin blank').addClass('overflow');
        }
        title_length_prompt.find('[name="char_delta"]').html(Math.abs(char_delta));
    }
    
    // 检查是否已取得宝贝图片
    var check_item_imgs = function (creative_id) {
	    if ($('#modal_select_creative_img [name="item_img"]').length==0) {
	        if (!app) {
	            app = 'web';
	        }
		    PT.sendDajax({'function':app+'_get_item_imgs',
			    'app':app,
			    'shop_id':shop_id,
			    'item_id_list':$.toJSON([Number(item_id)]),
			    'context':$.toJSON(creative_id), // 必须转成JSON，参数可能为空字符串
			    'namespace':'CreativeBox'
		    });
	    } else {
		    if (creative_id) {
			    var creative_img = $('#creative_box .creative_img[creative_id="'+creative_id+'"] img').attr('src');
			    mark_creative_img(creative_img);
		    }
	    }
    }
    
    // 在宝贝图片选择框中标记出创意图片
    var mark_creative_img = function (creative_img) {
		$('#modal_select_creative_img .modal-body a').removeClass('creative_img selected').addClass('item_img');
		var item_imgs = $.map($('#modal_select_creative_img [name="item_img"]'), function (img_obj) {return img_obj.src.split('.jpg', 1)[0] + '.jpg';});
		creative_img = creative_img.split('.taobaocdn.com/', 2)[1].split('.jpg', 1)[0] + '.jpg';
		for (var i in item_imgs) {
		    var item_img = item_imgs[i].split('.taobaocdn.com/', 2)[1];
		    if (item_img==creative_img) {
		        $('#modal_select_creative_img .item_img:eq('+i+')').removeClass('item_img').addClass('creative_img');
		    }
		}
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
    
    // 提交创意更改
    var update_creative = function (creative_id, title, img_url, opt_type) {
	    PT.show_loading('正在提交修改');
        if (!app) {
            app = 'web';
        }
	    PT.sendDajax({'function':app+'_update_creative',
		    'app':app,
		    'shop_id':shop_id,
		    'adgroup_id':adgroup_id,
		    'creative_id':creative_id,
		    'title':title,
		    'img_url':handle_img_url(img_url),
		    'opt_type':opt_type,
		    'namespace':'CreativeBox'
	    });
    }
    
    // 提交添加新创意
    var add_creative = function (title, img_url) {
        PT.show_loading('正在提交添加');
        if (!app) {
            app = 'web';
        }
        PT.sendDajax({'function':app+'_add_creative',
            'app':app,
            'shop_id':shop_id,
            'campaign_id':campaign_id,
            'adgroup_id':adgroup_id,
            'title':title,
            'img_url':handle_img_url(img_url),
            'namespace':'CreativeBox'
        });
    }
    
	var init_dom = function () {
		// 打开创意管理对话框
		$('#show_creative_box').unbind('click');
		$('#show_creative_box').click(function () {
		    $('#creative_box').modal('show');
		    if ($(this).attr('switch')==undefined) {
		        get_creative_by_id();
		    }
		    $(this).attr('switch',1);
		});

		// 编辑现有创意标题
        $('#creative_box').off('click.PT.e', '.edit_title');
        $('#creative_box').on('click.PT.e', '.edit_title', function () {
	        var creative_input = $(this).next().find('.creative_input');
	        var crt_title = $.trim($(this).text());
	        creative_input.val(crt_title);
	        check_crt_title(crt_title, creative_input.siblings('[name="title_length_prompt"]'));
	        $('#spread_content .popover').hide();
	        $(this).next().show();
        });

        $('#creative_box').off('click.PT.e', '.close');
        $('#creative_box').on('click.PT.e', '.close', function () {
            $(this).parent().hide();
        });

		// 提交创意标题改动
        $('#creative_box').off('click.PT.e', '.submit_title');
        $('#creative_box').on('click.PT.e', '.submit_title', function () {
	        var creative_input = $(this).siblings('.creative_input');
	        var title_length_prompt = $(this).siblings('[name="title_length_prompt"]');
	        if (creative_input.is(':disabled')) {
		        PT.alert('正在自动生成标题，请稍候');
            } else if (title_length_prompt.hasClass('blank')) {
                PT.alert('标题不能为空');
            } else if (title_length_prompt.hasClass('overflow')) {
                PT.alert('标题长度不能超过20个汉字');
	        } else {
	            var creative_id = creative_input.attr('creative_id');
	            var new_title = $.trim(creative_input.val());
	            var old_title = $.trim($(this).parent().parent().prev().text());
	            if(new_title!=old_title){
		            var img_url = $('.creative_img[creative_id="'+creative_id+'"] img').attr('src');
		            update_creative(creative_id, new_title, img_url, 13);
	            }
	            $(this).closest('.popover').hide();
	        }
        });
        
		// 打开创意图片对话框
        $('#creative_box').off('click.PT.e', '.creative_img'); 
        $('#creative_box').on('click.PT.e', '.creative_img', function () {
	        var creative_id = $(this).attr('creative_id');
	        $('#modal_select_creative_img').modal({'width':'860px'});
	        $('#modal_select_creative_img').attr('creative_id', creative_id);
	        $('#creative_img_no').html($('#creative_box .creative_img').index($(this))+1);
	        check_item_imgs(creative_id);
        });
    
	    // 点击选择创意图片
	    $('#modal_select_creative_img').off('click', '.item_img');
	    $('#modal_select_creative_img').on('click', '.item_img', function () {
	        var creative_id = $('#modal_select_creative_img').attr('creative_id');
	        var title = $('#creative_title_'+creative_id).html();
	        var img_url = $(this).children().attr('src');
	        $(this).addClass('selected');
	        PT.confirm('确定要替换为这张图片吗？', update_creative, [creative_id, title, img_url, 14], this, function () {$(this).removeClass('selected');});
	    });
        
        // 打开新创意对话框
        $('#creative_box').off('click.PT.e', '.add_creative');
        $('#creative_box').on('click.PT.e', '.add_creative', function () {
            check_item_imgs('');
            check_crt_title($('#new_creative_title').val(), $('#new_creative_title').siblings('[name="title_length_prompt"]'));
            $('#modal_new_creative').modal({'width':'890px'});
        });
        
        // 选择新创意图片
        $('#modal_new_creative').off('click.PT.e', '.item_img');
        $('#modal_new_creative').on('click.PT.e', '.item_img', function () {
	        $(this).addClass('selected').siblings().removeClass('selected');
        });
        
        $('#spread_content').off('keyup', '.creative_input');
        $('#spread_content').on('keyup', '.creative_input', function () {
	        check_crt_title($(this).val(), $(this).siblings('[name="title_length_prompt"]'));
        });
        
        $('#modal_new_creative').off('keyup', '#new_creative_title');
        $('#modal_new_creative').on('keyup', '#new_creative_title', function () {
            check_crt_title($(this).val(), $(this).siblings('[name="title_length_prompt"]'));
        });
        
        // 系统自动生成创意标题
        $(document).off('click.PT.e', '.generate_crt_title');
        $(document).on('click.PT.e', '.generate_crt_title', function () {
            $(this).hide().siblings('.loading_tag').show();
            var crt_title_input = $(this).siblings('input');
            crt_title_input.attr('disabled', true);
	        var official_title = crt_title_input.attr('official_title');
	        if (official_title) {
		        setTimeout(function () {
			        crt_title_input.siblings().show();
			        crt_title_input.siblings('.loading_tag').hide();
			        crt_title_input.attr('disabled', false);
			        crt_title_input.val(official_title);
			        check_crt_title(official_title, crt_title_input.siblings('[name="title_length_prompt"]'));
		        }, 1000); // 手工的虚假加载样式，模拟响应
	        } else {
		        if (!app) {
		            app = 'web';
		        }
		        PT.sendDajax({
	                'function':app+'_generate_crt_title',
	                'app':app,
	                'shop_id':shop_id,
	                'item_id':item_id,
	                'creative_no':Math.abs($('#spread_content .generate_crt_title').index($(this))),
	                'namespace':'CreativeBox',
	                'context':$.toJSON(crt_title_input.attr('id'))
		        });
	        }
        });
        
        // 点击提交添加新创意
        $('#submit_new_creative').unbind('click');
        $('#submit_new_creative').click(function () {
	        var title = $.trim($('#new_creative_title').val());
	        var img_url = $('#new_creative_img .item_img.selected [name="item_img"]').attr('src');
	        if (!img_url) {
		        PT.alert('请先选择创意图片');
		    } else if ($('#new_creative_title').is(':disabled')) {
		        PT.alert('正在自动生成标题，请稍候');
	        } else if ($('#modal_new_creative [name="title_length_prompt"]').hasClass('blank')) {
		        PT.alert('标题不能为空');
            } else if ($('#modal_new_creative [name="title_length_prompt"]').hasClass('overflow')) {
                PT.alert('标题长度不能超过20个汉字');
	        } else {
		        PT.confirm('确定要提交添加这个创意吗？', add_creative, [title, img_url]);
	        }
        });
	};
	
	return {
		init: function () {
			PT.initDashboardDaterange();
			init_dom();
		},
        creative_callback: function (adgroup_id, data) {
            var dom='', i;
            for (i in data) {
	            data[i]['i'] = i;
                dom += template.render('template_creative',data[i]);
                PT.draw_trend_chart( 'creative_trend_chart'+(Number(i)+1) , data[i].category_list, data[i].series_cfg_list);
            }
            if (i==0) {
                dom+=template.render('template_add_creative');
            }
            $('#spread_content').html(dom);
            $('#creative_info_tip').hide();
            $('#creative_box').attr('adgroup_id', adgroup_id);
            $('#creative_box').modal('hide').modal('show'); // 处理样式问题
        },
        creative_select_call_back: function (day) {
            $('#creative_last_day').val(day);
            $('#creative_info_tip').show();
            get_creative_by_id();
        },
        get_item_imgs_callback: function (item_dict, creative_id) {
	        for (var item_id in item_dict) {
		        var item_imgs = item_dict[item_id];
	            var html_item_imgs = template.render('item_imgs', {'item_imgs':item_imgs});
	            $('#modal_select_creative_img .modal-body').html(html_item_imgs);
	            $('#new_creative_img').html(html_item_imgs);
	            if (creative_id) {
			        var creative_img = $('.creative_img[creative_id="'+creative_id+'"] img').attr('src');
		            mark_creative_img(creative_img);
	            }
	        }
        },
        update_creative_callback: function (creative_id, title, img_url, opt_type) {
	        $('#creative_title_'+creative_id).html(title);
	        $('.creative_img[creative_id="'+creative_id+'"] img').attr('src', img_url + '_160x160.jpg');
	        $('#modal_select_creative_img').modal('hide');
	        var opt_desc = "";
	        switch (opt_type) {
		        case 13: 
			        opt_desc = '修改创意标题';
			        break;
                case 14: 
                    opt_desc = '修改创意图片';
                    break;
	        }
	        PT.light_msg(opt_desc, "修改成功！");
	        $('body').addClass('modal-open'); // 处理样式问题
        },
        generate_crt_title_callback: function (crt_title, input_id) {
	        var crt_title_input = $('#'+input_id);
	        crt_title_input.siblings().show();
	        crt_title_input.siblings('.loading_tag').hide();
	        crt_title_input.attr('disabled', false);
	        crt_title_input.val(crt_title).attr('official_title', crt_title);
	        check_crt_title(crt_title, crt_title_input.siblings('[name="title_length_prompt"]'));
        },
        add_creative_callback: function () {
	        $('#modal_new_creative').modal('hide');
	        $('#creative_info_tip').show();
	        $('#add_creative_box').hide();
	        get_creative_by_id();
        },
        show_creative_box: function (_app, _shop_id, _camp_id, _adgroup_id, _item_id) {
	        $('#creative_box').modal('show');
	        app = _app;
	        shop_id = _shop_id;
	        campaign_id = _camp_id;
	        adgroup_id = _adgroup_id;
	        item_id = _item_id;
	        if (adgroup_id!=$('#creative_box').attr('adgroup_id')) {
		        $('#creative_info_tip').show();
		        $('#creative_last_day').val('7');
		        $('#spread_content, #creative_trend_chart1, #creative_trend_chart2').empty();
		        var loading_tip = '<img src="/site_media/jl/img/ajax-loader.gif">正在加载。。。';
		        $('#modal_select_creative_img .modal-body, #new_creative_img').html(loading_tip);
		        $('#creative_box .creative_input, #new_creative_title').val('').removeAttr('official_title');
		        get_creative_by_id();
	        }
        }
	}
}();