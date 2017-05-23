PT.namespace('CreativeBox');
PT.CreativeBox = function () {
    var app,
        shop_id,
        item_image_list=[],
        adgroup_id = $('#adgroup_id').val(),
        item_id = $('#item_id').val();

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

        PT.show_loading('正在获取数据');

        PT.sendDajax({'function':app+'_get_creative_by_id',
            'app':app,
            'shop_id':shop_id,
            'adgroup_id':adgroup_id,
            'data':$.toJSON(request_data),
            'call_back':'PT.CreativeBox.creative_callback',
            'last_day':$('#creative_last_day>a').attr('data-value')
            });
    }

    // 检查创意标题长度
    var check_crt_title = function (adg_title, title_length_prompt) {
        var char_delta=Math.floor(PT.true_length($.trim(adg_title))/2);
        if (char_delta>20){
            title_length_prompt.addClass('red');
        }else{
             title_length_prompt.removeClass('red');
        }
        title_length_prompt.text(char_delta);
    }

    // 检查是否已取得宝贝图片
    var check_item_imgs = function (creative_id) {
        if (!item_image_list.length) {
            if (!app) {
                app = 'web';
            }

            PT.sendDajax({
                'function': app + '_get_item_imgs',
                'app': app,
                'shop_id': shop_id,
                'item_id_list': $.toJSON([Number(item_id)]),
                'context': $.toJSON(creative_id), // 必须转成JSON，参数可能为空字符串
                'namespace': 'CreativeBox'
            });
        } else {
            set_img_list();
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
        return img_url;
    }

    // 提交创意更改
    var update_creative = function (creative_id, title, img_url, opt_type) {
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
        if (!app) {
            app = 'web';
        } else if (app == 'crm') {
            PT.alert('暂停使用该功能');
            return;
        }
        $('#J_add_box').modal('hide').modal('shadeOut');
        PT.show_loading('正在提交添加');
        PT.sendDajax({'function':app+'_add_creative',
            'app':app,
            'shop_id':shop_id,
            'adgroup_id':adgroup_id,
            'campaign_id':$('#campaign_id').val(),
            'title':title,
            'img_url':handle_img_url(img_url),
            'namespace':'CreativeBox'
        });
        PT.show_loading('正在提交修改');
    }

    //将图片数据填充到页面上
    var set_img_list = function(){
        var dom='';
        for (var i = 0; i < item_image_list.length; i++) {
            dom+='<li class="bdd mr10 rel J_image" fix-ie="hover"><img src="'+item_image_list[i]+'_160x160.jpg" width="160" height="160"></li>'
        };

        $('#J_add_box .J_image_list,#J_change_box .J_image_list').html(dom);
    }

    var init_dom = function () {

        //切换天数
        $('#creative_last_day').on('change',function(e,v){
            get_creative_by_id();
        });

        // 编辑现有创意标题
        $('body').on('click.PT.e', '.J_edit_title', function () {
            var old_title=$(this).prev().text(),creative_id=$(this).attr('creative_id');

            $.confirm({
                title:'修改创意标题',
                body:pt_tpm['creative_edit_title.tpm.html'],
                backdrop:'static',
                shown:function(){
                    $('#J_edit_input').val(old_title);
                    check_crt_title($('#J_edit_input').val(), $('#J_edit_input').next().find('.J_last_title_num'));
                },
                width:715,
                okHide:function(e){
                    var input=$('#J_edit_input'),new_title=$.trim(input.val()),obj=this.$element;
                    obj.modal('shadeIn');
                    if (input.is(':disabled')){
                        PT.alert('正在自动生成标题，请稍候','',function(){obj.modal('shadeOut')});
                        return false;
                    }else if (new_title==''){
                        PT.alert('标题不能为空','',function(){obj.modal('shadeOut')});
                        return false;
                    }else if (Math.floor(PT.true_length(new_title)/2)>20){
                        PT.alert('标题长度不能超过20个汉字','',function(){obj.modal('shadeOut')});
                        return false;
                    }else{
                        if(new_title!=old_title){
                            var img_url = $('.J_info img[creative_id='+creative_id+']').attr('src');
                            update_creative(creative_id, new_title, img_url, 13);
                            obj.modal('shadeOut');
                            return true;
                            obj.modal('shadeOut');
                        }else{
                            PT.alert('和原有标题相同','',function(){obj.modal('shadeOut')});
                        }
                        return false;
                    }
                }
            });
        });

        // 打开创意图片对话框
        $('body').on('click.PT.e', '.J_edit_img', function () {
            var creative_id = $(this).next().attr('creative_id');
            $('#J_change_box').modal({'width':900}).data('creative_id',creative_id);
            check_item_imgs(creative_id);
        });

        //提交创意图片
        $('body').on('click.PT.e','#update_creative',function(){
            var creative_id=$('#J_change_box').data('creative_id'),img_url = $('#J_change_box .J_image_list li.active>img').attr('src'),new_title=$('#creative_title_'+creative_id).text();
            $('#J_change_box').modal('shadeIn');
            if(!img_url){
                PT.alert('请先选择创意图片','',function(){$('#J_change_box').modal('shadeOut')});
                return false;
            }
            $('#J_change_box').modal('shadeOut').modal('hide');
            PT.show_loading('正在提交修改');
            update_creative(creative_id, new_title, img_url, 14);
        });

        // 打开新创意对话框
        $('body').on('click.PT.e', '.J_add', function () {
            check_item_imgs('');
            $('#J_add_box').modal({width:900})
        });

        $('body').on('keyup.PT.e', '#J_add_title,#J_edit_input', function () {
            check_crt_title($(this).val(), $(this).next().find('.J_last_title_num'));
        });

        // 系统自动生成创意标题
        $(document).on('click.PT.e', '.J_generate_crt_title', function () {
            $(this).hide().siblings('.loading_tag').show();
            var crt_title_input =$(this).prev().find('input');
            crt_title_input.attr('disabled', true);
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
        });

        // 点击提交添加新创意
        $('#submit_new_creative').click(function () {
            var title = $.trim($('#J_add_title').val());
            var img_url = $('#J_add_box .J_image_list li.active>img').attr('src');

            $('#J_add_box').modal('shadeIn');
            if (!img_url) {
                PT.alert('请先选择创意图片','',function(){$('#J_add_box').modal('shadeOut');});
            } else if ($('#new_creative_title').is(':disabled')) {
                PT.alert('正在自动生成标题，请稍候','',function(){$('#J_add_box').modal('shadeOut');});
            } else if (title=='') {
                PT.alert('标题不能为空','',function(){$('#J_add_box').modal('shadeOut');});
            } else if (Math.floor(PT.true_length($('#J_add_title').val())/2)>20) {
                PT.alert('标题长度不能超过20个汉字','',function(){$('#J_add_box').modal('shadeOut');});
            } else {
                PT.confirm('确定要提交添加这个创意吗？', add_creative, [title, img_url]);
            }
        });

        //选择推广图片的样式
        $('body').on('click.PT.e','.J_image',function(e){
            $(this).parent().find('.J_image').not($(this)).removeClass('active');
            $(this).toggleClass('active');
        });
    };

    return {
        init: function () {
            init_dom();
        },
        creative_callback: function (adgroup_id, data) {
            var  i;
            for (i in data) {
                data[i]['i'] = i;
                $('#creative_'+i).find('.J_info').html(template.compile(pt_tpm['creative_optimization_into.tpm.html'])(data[i])).show();
                PT.draw_trend_chart( 'creative_trend_chart'+(Number(i)+1) , data[i].category_list, data[i].series_cfg_list);
            }
        },
        creative_select_call_back: function (day) {
            $('#creative_last_day').val(day);
            $('#creative_info_tip').show();
            get_creative_by_id();
        },
        get_item_imgs_callback: function (item_dict, creative_id) {
            for (var item_id in item_dict) {
                item_image_list = item_dict[item_id];
            }
            set_img_list();
        },
        update_creative_callback: function (creative_id, title, img_url, opt_type) {
            var opt_desc = "";
            PT.hide_loading();
            switch (opt_type) {
                case 13:
                    $('#creative_title_'+creative_id).html(title);
                    opt_desc = '修改创意标题';
                    break;
                case 14:
                    $('.J_info img[creative_id='+creative_id+']').attr('src', img_url + '_160x160.jpg');
                    opt_desc = '修改创意图片';
                    break;
            }
            PT.light_msg(opt_desc,'修改成功');
        },
        generate_crt_title_callback: function (crt_title, input_id) {
            var crt_title_input = $('#'+input_id);
            crt_title_input.parent().siblings().show();
            crt_title_input.parent().siblings('.loading_tag').hide();
            crt_title_input.attr('disabled', false);
            crt_title_input.val(crt_title).attr('official_title', crt_title);
            check_crt_title(crt_title, crt_title_input.next().find('.J_last_title_num'));
        },
        add_creative_callback: function () {
            $('#modal_new_creative').modal('hide');
            $('#creative_info_tip').show();
            $('#add_creative_box').hide();
            get_creative_by_id();
        },
        show_creative_box: function (_app, _shop_id, _adgroup_id, _item_id) {
            $('#creative_box').modal('show');
            app = _app;
            shop_id = _shop_id;
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
