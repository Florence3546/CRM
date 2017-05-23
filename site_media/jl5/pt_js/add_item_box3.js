PT.namespace('AddItemBox3');
PT.AddItemBox3 = function () {
    var item_page_no = 1;
    var adg_page_no = 1;
    var page_size = 50;
    var item_search_keyword = '';
    var adg_search_keyword = '';
    var campaign_id = 0;
    var mnt_type = $('#mnt_type').val();
//    var mnt_max_num = 0;
    var max_done_num = 0;
    var done_count = 0; // 计划下已托管宝贝数
    var camp_dict = {}; //计划名称字典
    var default_pane = null;
    var cat_list = {};

    // 初始化表格数据
    var init_tables = function (mnt_num) {
        item_page_no = adg_page_no = 1;
        item_search_keyword = adg_search_keyword = '';
        max_done_num = Number($('#mnt_max_num').val()) || 0;
        $('#add_item_box3 .search_keyword').val('');
        $('#add_item_box3 .tab-pane').attr('inited', '0');
        $('#add_item_box3 tbody, #recycle_bin').empty();
        $('#candidate .nav-tabs li').removeClass('active');
        if (mnt_num) {
            done_count = mnt_num;
            $('.mnt_num').html(done_count);
            $('.new_num').html(max_done_num-done_count);
        }
    }

    // 打开添加宝贝面板
    var open = function () {
        campaign_id = $('#campaign_id').val();
        mnt_type = $('#mnt_type').val();
        max_done_num = Number($('#mnt_max_num').val()) || 0;
        if (mnt_type=='2') {
            $('#add_item_box3 .batch_add').hide().next().show();
        } else {
            $('#add_item_box3 .batch_add').show().next().hide();
        }
        if ($.inArray(mnt_type, ['1', '2']) != -1) {
            $('.to_mnt, .doable_count_info').show();
        } else {
            $('.to_mnt, .doable_count_info').hide();
        }

        $('#add_item_box3 a[data-toggle="tab"]').off('show');
        $('#add_item_box3 a[data-toggle="tab"]').on('show', function () {
            switch ($(this).attr('href')) {
                case '#item_pane':
                    $('#modal_init_limit_price').attr('tb', '0');
                    if ($('#item_pane').attr('inited')=='0') {
                        item_page_no = 1;
                        get_item_list();
                    }
                    $('#item_pane .batch_num').html($('#item_pane tbody tr').length);
                    break;
                case '#adgroup_pane':
                    $('#modal_init_limit_price').attr('tb', '1');
                    if ($('#adgroup_pane').attr('inited')=='0') {
                        adg_page_no = 1;
                        get_adg_list();
                        // console.log('init')
                    }
                    $('#adgroup_pane .batch_num').html($('#adgroup_pane tbody tr').length);
                    break;
                }
        });

        if ($('#candidate .nav-tabs .active').length==0) {
//          init_tables();
            $('#candidate [href="#'+default_pane+'"]').tab('show');
        }
        $('#item_pane .batch_num').html($('#item_pane tbody tr').length);
    }

    // 获取宝贝列表
    var get_item_list = function () {
        PT.show_loading('正在获取数据');
        PT.sendDajax({
            'function':'mnt_get_item_list',
            'campaign_id':campaign_id,
            'page_no':item_page_no,
            'page_size':page_size,
            'sSearch':item_search_keyword,
            'exclude_existed':1,  // 是否排除现有adgroup的标志
            'namespace':'AddItemBox3',
            'auto_hide':0
        });
    }
    var get_adg_list = function () {
        PT.show_loading('正在获取数据');
        PT.sendDajax({
            'function':'mnt_get_adg_list',
            'campaign_id':campaign_id,
            'page_no':adg_page_no,
            'page_size':page_size,
            'sSearch':adg_search_keyword,
            'rpt_days':7,
            'namespace':'AddItemBox3',
            'auto_hide':0
        });
    }

    // 更新宝贝个数统计
    var update_statistic_data = function () {
        
        var item_total_count = Number($('#item_pane .total_count').attr('init_value'));
        var adgroup_total_count = Number($('#adgroup_pane .total_count').attr('init_value'));
        var item_doing_count = $('#item_cart tbody tr[tb="0"]').length;
        $('.item_doing_count').html(item_doing_count);
        var adgroup_doing_count = $('#item_cart tbody tr[tb="1"]').length;
        $('.adgroup_doing_count').html(adgroup_doing_count);
        var doing_count = item_doing_count + adgroup_doing_count;
        done_count = Number($('.mnt_num').html()) || 0;
        if (mnt_type=='0') {
            max_done_num = item_total_count;
        }
        var doable_count = max_done_num - doing_count - done_count;
        var danger_item_count = $('#item_cart tr.danger_cat').length;
        $('#item_pane .total_count').html(item_total_count - item_doing_count);
        $('#adgroup_pane .total_count').html(adgroup_total_count - adgroup_doing_count);
        $('.doing_count').html(doing_count);
        $('.doable_count').html(doable_count);
        $('#item_pane .batch_num').html(Math.min($('#item_table tbody tr:visible').length, doable_count));
        $('#adgroup_pane .batch_num').html(Math.min($('#adgroup_pane tbody tr:visible').length, doable_count));
        $('.danger_item_count').html(danger_item_count);
        if (danger_item_count>0) {
            $('.danger_cats_info, #add_item_warning').show();
        } else {
            $('.danger_cats_info, #add_item_warning').hide();
        }

        $('#item_pane .batch_num').html($('#item_table tbody tr').length);
        //设置拷贝的表头的宽度与数据列表宽度一致，解决列表表头错位的bug
        /*if ($('#item_pane').attr('inited')!='0') {
            $('#item_pane table').width($('#item_pane').width()-15);
        }
        if ($('#adgroup_pane').attr('inited')!='0') {
            $('#adgroup_pane table').width($('#adgroup_pane').width()-15);
        }*/
    }

    // 打开设置限价对话框
    var set_limit_price = function (cat_id_list, item_id, limit_price) {
        $('#init_limit_price').val(limit_price);
        $('#modal_init_limit_price').attr('item_id', item_id);
        $('#modal_init_limit_price [name="cat_path"]').empty();
        $('#modal_init_limit_price .cat_path').removeClass('danger_cat');
        $('#modal_init_limit_price [name="cat_avg_cpc"]').empty();
        $('#modal_init_limit_price .loading_tag').show();
        $('#modal_init_limit_price .input_error').removeClass('input_error');
        $('#modal_init_limit_price').modal('show');
        PT.sendDajax({'function':'mnt_get_cat_avg_cpc', 'cat_id_list':cat_id_list, 'namespace':'AddItemBox3'});
    }

    // 校验关键词限价
    var check_limit_price = function (limit_price){
        var error='';
        var limit_price_min = Number($('#modal_init_limit_price .limit_price_min').html());
        limit_price_min = isNaN(limit_price_min)?1:limit_price_min;
        limit_price_min = Math.min(limit_price_min * 0.4, 0.5);
        var limit_price_max = Number($('#modal_init_limit_price .limit_price_max').html()) || 20;
       // var limit_price_min = Number($('#modal_init_limit_price .limit_price_min').html());
        if($.trim(limit_price) ===''){
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
            'namespace':'AddItemBox3'
        });
    }

    // 生成创意标题
    var getorcreate_adg_title_list = function (data) {
        for (var i in data) {
            PT.sendDajax({
                'function':'web_getorcreate_adg_title_list',
                'item_id':data[i].item_id,
                'adgroup_id':data[i]['adgroup_id'] || 0,
                'title':data[i].title,
                'namespace':'AddItemBox3'
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
//            if (cat_path.indexOf('icon-warning-sign')!=-1) {
            if ($('#modal_init_limit_price .cat_path').hasClass('danger_cat')) {
                tr_obj.addClass('danger_cat');
                tr_obj.find('i.tooltips').tooltip();
            }
            update_statistic_data();
        } else {
            PT.sendDajax({
                'function':'web_get_cat_path',
                'cat_id_list':$.toJSON($.map(data, function (obj) {return Number(obj.cat_id)})),
                'namespace':'AddItemBox3'
            });
        }
    }

    // 更新宝贝购物车
    var update_item_cart = function (tr_objs) {
        var data = $.map(tr_objs, function (obj) {
            var temp_obj = {
                'item_id':$(obj).attr('item_id'),
                'cat_id':$(obj).attr('cat_id'),
                'pic_url':$(obj).find('img:eq(0)').attr('src'),
                'item_imgs':$.map($(obj).find('[name="item_imgs"] li'), function (li_obj) {return $(li_obj).html();}),
                'title':$(obj).find('[name="item_title"]').html(),
                'limit_price':Number($('#init_limit_price').val()).toFixed(2),
                'danger_cat':$(obj).hasClass('danger_cat')
            };
            return temp_obj;
        });
        var table_data = template.render('item_cart_tr', {'data':data, 'mnt_type':mnt_type});
        $('#item_cart tbody').prepend(table_data);
        tr_objs.removeClass('hover');
        $('#recycle_bin').append(tr_objs);
        update_statistic_data();
        getorcreate_adg_title_list(data);
        get_cat_path(data);
    }
    var update_mnt_adgroup_table = function (data) {
        var table_data = template.render('mnt_adgroup_tr', {'data':data, 'mnt_type':mnt_type});
        $('#item_cart tbody').prepend(table_data);
        var tr_objs = $();
        $.map(data, function (obj) {
            tr_objs = tr_objs.add($('#adgroup_table tr[item_id="'+obj['item_id']+'"]'));
        });
        tr_objs.removeClass('hover');
        $('#recycle_bin').append(tr_objs.clone());
        tr_objs.remove();
        update_statistic_data();
        getorcreate_adg_title_list(data);
    }

    // 加入宝贝购物车
    var add_item = function (tr_objs) {
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
            set_limit_price([cat_id], item_id, '');
        } else {
            update_item_cart(tr_objs);
        }
    }
    var add_adgroup = function (tr_objs) {
        if (mnt_type=='2') {
            var limit_price = tr_objs.attr('limit_price');
            var item_id = tr_objs.attr('item_id');
            var cat_id = tr_objs.attr('cat_id');
            set_limit_price([cat_id], item_id, limit_price);
        } else {
            get_item_imgs(tr_objs);
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
//      PT.show_loading('正在检查宝贝类目是否安全');
//      PT.sendDajax({
//          'function':'web_check_danger_cats',
//          'cat_id_list':cat_id_list
//      });
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

    // 检查创意标题长度
    var check_adg_title_length = function (adg_title, parent_obj) {
        var char_delta = Math.floor(20-bytes_len($.trim(adg_title))/2);
        if (char_delta>=0) {
            parent_obj.find('[name="length_prompt"]').removeClass('overflow').addClass('margin');
            if (char_delta==20) {
                parent_obj.find('[name="length_prompt"]').addClass('blank');
            } else {
                parent_obj.find('[name="length_prompt"]').removeClass('blank');
            }
        } else {
            parent_obj.find('[name="length_prompt"]').removeClass('margin blank').addClass('overflow');
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

    // 检查创意图片，标题长度
    var check_creative_isvalid = function () {
        if (Number($(".doing_count").html())==0) {
            PT.alert('请先选择宝贝');
            return false;
        } else if ($('#item_cart .none_crt_img').length) {
            PT.alert('有宝贝未选择创意图片，请先选择图片');
            return false;
        } else if ($('#item_cart .loading_tag:visible').length) {
            PT.alert('正在加载数据，请等待加载完后再操作');
            return false;
        } else if ($('#item_cart [name="length_prompt"].overflow').length>0) {
            PT.alert('有些创意标题的长度超过20个汉字');
            return false;
        } else if ($('#item_cart [name="length_prompt"].blank').length>0) {
            PT.alert('有些创意标题为空');
            return false;
        } else {
            return true;
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
        $.map($('#item_cart tbody tr[tb="0"]'), function (tr_obj) {
            var item_id = $(tr_obj).attr('item_id');
            if (item_id) {
                new_item_dict[item_id] = [{}, {}];
                for (var i=0;i<2;i++) {
                    new_item_dict[item_id][i]['title'] = $.trim($(tr_obj).find('[name="adg_title"]:eq('+i+')').val());
                    new_item_dict[item_id][i]['img_url'] = handle_img_url($(tr_obj).find('[name="creative_img"]:eq('+i+')').attr('src'));
                    if (mnt_type=='2' && i==0) {
                        new_item_dict[item_id][i]['limit_price'] = Number($(tr_obj).find('[name="limit_price"]').text())*100;
                    }
                }
            }
        });
        mnt_type = $('#mnt_type').val();
        PT.sendDajax({'function':'web_add_items2',
                                 'new_item_dict':$.toJSON(new_item_dict),
                                 'camp_id':campaign_id,
                                 'mnt_type':mnt_type,
                                 'namespace':'AddItemBox3',
                                 'callback_list':$.toJSON(callback_list),
                                 'context':$.toJSON(context)
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
        var mnt_adg_dict = {}, update_creative_dict = {}, new_creative_list = [];
        $.map($('#item_cart tbody tr[tb="1"]'), function (tr_obj) {
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
                                 'namespace':'AddItemBox3',
                                 'callback_list':$.toJSON(callback_list),
                                 'context':$.toJSON(context)
                                 });
    }

    //候选宝贝排序
    var sort_adgroup_table = function(){
        if($.fn.dataTable.fnIsDataTable($('#add_item_box3 #adgroup_table')[0])){
            redrow_adgroup_table();
        }

        if(!$('#add_item_box3 #adgroup_table tbody tr').length){
            return;
        }
        $('#add_item_box3 #adgroup_table').dataTable({
            "bPaginate": false,
            "bFilter": false,
            "bInfo": false,
            "bAutoWidth":false,//禁止自动计算宽度
            "sDom":'',
            "aoColumns": [
                {"bSortable": false},
                {"bSortable": false},
                {"bSortable": false,"sSortDataType": "dom-text", "sType": "numeric","sClass": "no_back_img"},
                {"bSortable": false,"sSortDataType": "dom-text", "sType": "numeric","sClass": "no_back_img"}
            ],
            "oLanguage": {
                "sZeroRecords": "没有符合要求的宝贝",
                "sInfoEmpty": "显示0条记录"
            }
        });
    }

    redrow_adgroup_table = function(){
        var old_dom=$('#adgroup_table tbody').html();
        $('#adgroup_table').dataTable().fnDestroy();
        $('#adgroup_table tbody').html(old_dom);
    }

    var init_dom = function (mode) {
        switch (mode) {
            case 0:
                default_pane = 'item_pane'; // 默认模式下只有一个添加新宝贝面板
                $('#add_item_box3 .modal_header .title').html('添加新宝贝');
                break;
            case 1:
                default_pane = 'adgroup_pane'; // 扩展模式1应用于全自动托管，首选面板为计划下已有宝贝面板
                $('#add_item_box3').removeClass('modal fade');
                break;
        }
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
        $('#modal_init_limit_price, #modal_limit_price').off('keyup', '.keyup_restore');
        $('#modal_init_limit_price, #modal_limit_price').on('keyup', '.keyup_restore', function(){
            $(this).closest('.input_error').removeClass('input_error');
        });
        
        // 设置重点宝贝限价
        $('#submit_limit_price').unbind('click');
        $('#submit_limit_price').click(function () {
            if ($('#modal_init_limit_price .loading_tag:visible').length) {
                PT.alert('正在加载数据，请等待加载完后再操作');
                return;
            }
            var limit_price = Number($('#init_limit_price').val());
            var check_error = check_limit_price(limit_price);
            if (!check_error) {
                $('#init_limit_price').closest('div').removeClass('input_error');
                $('#modal_init_limit_price').modal('hide');
                var item_id = $('#modal_init_limit_price').attr('item_id');
                switch ($('#modal_init_limit_price').attr('tb')) {
                    case '0':
                        var tr_objs = $('#item_table tr[item_id="'+item_id+'"]');
                        setTimeout(function(){update_item_cart(tr_objs)}, 300);
                        break;
                    case '1':
                        var tr_objs = $('#adgroup_table tr[item_id="'+item_id+'"]');
                        setTimeout(function(){get_item_imgs(tr_objs)}, 300);
                        break;
                }
            } else {
                $('#init_limit_price').closest('div').addClass('input_error');
                $('#init_limit_price').next().find('.tooltips').attr('data-original-title', check_error);
            }
        });

        // 批量添加宝贝 (用 .batch_add 而不用 #batch_add 是为了避免固定表头出现bug)
        $('#add_item_box3 .batch_add').unbind('mouseenter');
        $('#add_item_box3 .batch_add').bind('mouseenter', function () {
            var batch_num = Number($(this).find('.batch_num').html());
            $(this).closest('.tab-pane').find('tbody tr:visible:lt('+batch_num+')').addClass('hover');
        });
        $('#add_item_box3 .batch_add').unbind('mouseleave');
        $('#add_item_box3 .batch_add').bind('mouseleave', function () {
            var batch_num = Number($(this).find('.batch_num').html());
            $(this).closest('.tab-pane').find('tbody tr:visible:lt('+batch_num+')').removeClass('hover');
        });
        $('#add_item_box3 .batch_add').unbind('click');
        $('#add_item_box3 .batch_add').click(function () {
            if (Number($('.doable_count').html())>0) {
                var batch_num = Number($(this).find('.batch_num').html());
                var pane_obj = $(this).closest('.tab-pane');
                if (batch_num) {
                    var tr_objs = pane_obj.find('tbody tr:visible:lt('+batch_num+')');
                    switch (pane_obj.attr('id')) {
                        case 'item_pane':
                            add_item(tr_objs);
                            get_item_list();
                            // console.log('batch')
                            break;
                        case 'adgroup_pane':
                            add_adgroup(tr_objs);
                            get_adg_list();
                            // console.log('batch')
                            break;
                    }
                } else if (pane_obj.find('.load_more').is(':visible')) {
                    PT.alert('请点击加载更多宝贝！');
                } else {
                    PT.alert('没有宝贝可以添加！');
                }
            } else {
                //PT.alert('已达到托管数量上限，不能再添加宝贝了！');
                PT.alert('没有宝贝可以添加！');
            }
        });
        
        // 生成固定表头
       /* $.map($('#add_item_box3 .table_4fixedhead'), function (obj) {
            var table_id = $(obj).attr('source');
            $(obj).html($('#'+table_id).find('thead').clone());
        });*/
        
        $('table[source="adgroup_table"]').find('.dropdown-toggle').dropdown();

        // 搜索功能
        $('#add_item_box3 .search_btn').unbind('click');
        $('#add_item_box3 .search_btn').click(function(){
            if ($('#item_cart .loading_tag:visible').length) {
                PT.alert('正在加载数据，请等待加载完后再操作');
                return;
            }
            var pane_obj = $(this).closest('.tab-pane');
            var search_keyword_old = '';
            switch (pane_obj.attr('id')) {
                case 'item_pane':
                    search_keyword_old = item_search_keyword;
                    item_search_keyword = $(this).prev('.search_keyword').val();
                    if (item_search_keyword != search_keyword_old) {
                        $('#item_table tbody').empty();
                        item_page_no = 1;
                    } else if (pane_obj.find('.load_more').is(':hidden')) {
                        PT.alert('已搜索完毕');
                        return;
                    }
                    get_item_list();
                    // console.log('secrch')
                    break;
                case 'adgroup_pane':
                    search_keyword_old = adg_search_keyword;
                    adg_search_keyword = $(this).prev('.search_keyword').val();
                    if (adg_search_keyword != search_keyword_old) {
                        $('#adgroup_table tbody').empty();
                        adg_page_no = 1;
                    } else if (pane_obj.find('.load_more').is(':hidden')) {
                        PT.alert('已搜索完毕');
                        return;
                    }
                    get_adg_list();
                    // console.log('secrch')
                    break;
            }
        });

        // 加载更多宝贝
        // $('#add_item_box3 .load_more').unbind('click');
        // $('#item_pane .load_more').click(get_item_list);
        // $('#adgroup_pane .load_more').click(get_adg_list);

        //滚动加载
        $('.h520.ofys:eq(1)').off('scroll');
        $('.h520.ofys:eq(1)').on('scroll',function(e){
            var top=$(e.target).scrollTop(),
                obj_h=$('#item_table').height()-$(e.target).height();

                // console.log(e.isDefaultPrevented())

                if($('#item_table tr').length==2){  //防止点击批量时触发
                    return;
                }

            if(top>=obj_h&&$('#item_table .load_more:visible').length && $('#full_screen_tips').is(':hidden')){
                get_item_list();
                // console.log('scroll')
            }
        });

        //滚动加载
        // console.log('init scroll')
        $('.h520.ofys:eq(0)').off('scroll');
        $('.h520.ofys:eq(0)').on('scroll',function(e){
            var top=$(e.target).scrollTop(),
                obj_h=$('#adgroup_table').height()-$(e.target).height();

                if($('#adgroup_table tr').length==2){ //防止点击批量时触发
                    return;
                }

            if(top>=obj_h&&$('#adgroup_table .load_more:visible').length && $('#full_screen_tips').is(':hidden')){
                get_adg_list();
                // console.log('scroll')
            }
        });

        // 表格行悬浮/离开事件
        $('#add_item_box3').off('mouseenter', 'tbody tr');
        $('#add_item_box3').on('mouseenter', 'tbody tr', function () {
            $(this).addClass('hover');
        });

        $('#add_item_box3').off('mouseleave', 'tbody tr');
        $('#add_item_box3').on('mouseleave', 'tbody tr', function () {
            $(this).removeClass('hover');
        });

        // 点击添加宝贝
        $('#item_table').off('click', '[name="item"]');
        $('#item_table').on('click', '[name="item"]', function () {
            if (Number($('.doable_count').html())>0) {
                add_item($(this).closest('tr'));
            } else {
                PT.alert('已达到托管数量上限，不能再添加宝贝了！');
            }
        });
        $('#adgroup_table').off('click', '[name="adgroup"]');
        $('#adgroup_table').on('click', '[name="adgroup"]', function () {
            if (Number($('.doable_count').html())>0) {
                add_adgroup($(this).closest('tr'));
            } else {
                PT.alert('已达到托管数量上限，不能再添加宝贝了！');
            }
        });
        $('#item_table').off('click', '.add_item');
        $('#item_table').on('click', '.add_item', function () {
            $(this).closest('tr').find('[name="item"]').click();
        });
        $('#adgroup_table').off('click', '.add_adgroup');
        $('#adgroup_table').on('click', '.add_adgroup', function () {
            $(this).closest('tr').find('[name="adgroup"]').click();
        });

        // 点击打开选择创意图片框
        $('#item_cart').off('click', '.edit_pen_image');
        $('#item_cart').on('click', '.edit_pen_image', function () {
            var obj=$(this).find('[name=creative_img]');
            var item_id = obj.closest('tr').attr('item_id');
            var no = obj.parent().index();
            $('#modal_select_creative_img').attr({'item_id':item_id, 'no':no});
            $('#creative_img_no').html(no+1);
            var item_imgs = $.map(obj.closest('td').find('[name="item_imgs"] li'), function (li_obj) {
                return $(li_obj).html();
            });
            var html_item_imgs = template.render('item_imgs', {'item_imgs':item_imgs});
            $('#modal_select_creative_img .image_list').html(html_item_imgs);

            if($('.modal-backdrop:visible').length){
               $('#modal_select_creative_img').modal({'backdrop':false});
            }else{
               $('#modal_select_creative_img').modal({'backdrop':'static'});
            }
            $('#modal_select_creative_img').modal().css({
                        'min-width':'400px',
                        'width': 'auto',
                        'margin-left': function () {
                            return -($(this).width() / 2);
                        }
                    });
        });

        //选择推广图片的样式
        $('body').off('click.PT.J_image');
        $('body').on('click.PT.J_image','.J_image',function(e){
            $(this).parent().find('.J_image').not($(this)).removeClass('active');
            $(this).toggleClass('active');
        });

        //提交创意图片
        $('body').off('click.PT.update_creative');
        $('body').on('click.PT.update_creative','#update_creative',function(){
            var item_img = $('#modal_select_creative_img li.active>img').attr('src');
            var item_id = $('#modal_select_creative_img').attr('item_id');
            var no = $('#modal_select_creative_img').attr('no');
            $('#item_cart tr[item_id="'+item_id+'"] [name="creative_img"]:eq('+no+')').replaceWith('<img name="creative_img" src="'+item_img+'" width="100" height="100" title="点击换图" />');
            if (PT.MntAdgBox) {
                $('#mnt_adgroup_table tr[item_id="'+item_id+'"] [name="creative_img"]:eq('+no+')').replaceWith('<img name="creative_img" src="'+item_img+'" width="100" height="100" title="点击换图" />');
                PT.MntAdgBox.check_creative_ismodified(item_id, no);
            }
            $('#modal_select_creative_img').modal('hide');
        });

        // 点击选择创意图片
        // $('#modal_select_creative_img').off('click', '[name="item_img"]');
        // $('#modal_select_creative_img').on('click', '[name="item_img"]', function () {
           //  var item_img = this.src;
           //  var item_id = $('#modal_select_creative_img').attr('item_id');
           //  var no = $('#modal_select_creative_img').attr('no');
           //  $('#item_cart tr[item_id="'+item_id+'"] [name="creative_img"]:eq('+no+')').replaceWith('<img name="creative_img" src="'+item_img+'" width="100" height="100" title="点击换图" />');
           //  if (PT.MntAdgBox) {
              //   $('#mnt_adgroup_table tr[item_id="'+item_id+'"] [name="creative_img"]:eq('+no+')').replaceWith('<img name="creative_img" src="'+item_img+'" width="100" height="100" title="点击换图" />');
              //   PT.MntAdgBox.check_creative_ismodified(item_id, no);
           //  }
           //  $('#modal_select_creative_img').modal('hide');
        // });

        // 取消添加宝贝
        $('#item_cart').off('click', '.undo');
        $('#item_cart').on('click', '.undo', function () {
            var item_id = $(this).closest('tr').attr('item_id');
            var tb = $(this).closest('tr').attr('tb');
            var tr_obj = $('#recycle_bin tr[item_id="'+item_id+'"]');
            if (tb=='0') {
                $('#item_table').prepend(tr_obj);
            } else if (tb=='1') {
                $('#adgroup_table').prepend(tr_obj);
            }
            $(this).closest('tr').remove();
            update_statistic_data();
            sort_adgroup_table();
        });

        // 动态检测添加宝贝的创意标题长度
        $('#item_cart').off('keyup', 'input[name="adg_title"]');
        $('#item_cart').on('keyup', 'input[name="adg_title"]', function () {
            check_adg_title_length($(this).val(), $(this).parent());
        });

        // 确定要添加的宝贝，检查宝贝创意标题长度和宝贝类目
        $('#add_item_box3 .btn_OK').unbind('click');
        $('#add_item_box3 .btn_OK').click(function () {
            if (check_creative_isvalid()) {
                $('#modal_new_item_info .btn_OK2').show();
                $('#modal_new_item_info .into_next_step').hide();
                $('#add_item_box3').modal('hide');
                $('#modal_new_item_info').modal('show');
            }
        });
        $('#modal_new_item_info .btn_OK2').unbind('click');
        $('#modal_new_item_info .btn_OK2').click(function () {
            $('#modal_new_item_info').modal('hide');
            if ($('#mnt_wizard').length) {
                PT.ChooseMntcampaign.into_next_step();
            } else {
                submit_new_item([], {});
            }
        });

        // 打开添加宝贝面板
        $('#add_item').unbind('click');
        $('#add_item').click(function () {
             //$('#add_item_box3.modal').modal({'width':'pct90', 'backdrop':'static'});
             $('#add_item_box3.modal').modal({'width':'1280', 'backdrop':'static'});
            open();
        });

        // 返回添加宝贝面板，以便排除属于限制类目的宝贝
        $('#return_2add_item').unbind('click');
        $('#return_2add_item').click(function () {
            $('#modal_new_item_info').modal('hide');
            $('#add_item').click();
        });

        // 添加新宝贝时过滤掉已加入其他计划的宝贝
        $('#filter_other_camp').unbind('change');
        $('#filter_other_camp').change(function () {
	        if (this.checked) {
		        $('#item_table tbody tr').each(function () {
			        if ($.trim($(this).children(':eq(2)').html())) {
				        $(this).hide();
			        }
		        });
		        $('#item_table').parent().scroll();
	        } else {
		        $('#item_table tbody tr').show();
	        }
	        update_statistic_data();
        });
    }

    return {
        init: function (mode) {
            // console.log('inited dom')
            init_dom(mode);
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
        open: open,
        get_item_list:get_item_list,
//        check_danger_cats: check_danger_cats,
        get_cat_avg_cpc: function (cat_path, danger_descr, avg_cpc, avg_cpc_flag) {
        
            var modal_obj = $('#modal_init_limit_price, #modal_limit_price');
            if (danger_descr) {
                cat_path += '<i class="iconfont f16 ml5 tooltips red" data-original-title="'+danger_descr+'">&#xe62b;</i>';
                modal_obj.find('.cat_path').addClass('danger_cat');
            }
            remove_loading_tag(modal_obj, 'cat_path', cat_path, 1);
            remove_loading_tag(modal_obj, 'cat_avg_cpc', avg_cpc.toFixed(2), 1);
            modal_obj.find('i.tooltips').tooltip();
            if (!avg_cpc_flag) {
                modal_obj.find('[name="cat_avg_cpc"]').prepend('<span class="silver">未获取到</span>，默认为 ');
            }
            // var limit_price_min = avg_cpc;
            // var limit_price_min = avg_cpc*0.8;
            // limit_price_min = Math.min(limit_price_min, 20);
            modal_obj.find('.limit_price_min').html(avg_cpc.toFixed(2));
            var prompt_price = avg_cpc * 1.2;
            $('.prompt_price').html(prompt_price.toFixed(2));
            if ($('#init_limit_price').val() === '') {
                $('#init_limit_price').val(prompt_price.toFixed(2));
            }
            if ($('#adg_limit_price').val() === '') {
                $('#adg_limit_price').val(prompt_price.toFixed(2));
            }
        },
        get_item_list_callback: function (data, has_more, total_count) {
            var table_data = template.render('item_tr', {'data':data, 'camp_dict':camp_dict});
            $('#item_table tbody').append(table_data);
            $('#item_pane .total_count').attr('init_value', total_count);
            $('#item_pane').attr('inited', '1');
            $.map($('#item_cart tbody tr'), function (tr_obj) {
                var item_id = $(tr_obj).attr('item_id');
                $('#item_table tbody tr[item_id="'+item_id+'"]').remove();
            });
            PT.hide_loading();
            item_page_no++;
            // 根据 filter_other_camp 复选框调整其他计划下的宝贝是否显示
            if ($('#filter_other_camp').prop('checked')) {
                $('#item_table tbody tr').each(function () {
                    if ($.trim($(this).children(':eq(2)').html())) {
                        $(this).hide();
                    }
                });
                $('#item_table').parent().scroll();
            }
            update_statistic_data();
            if (has_more && Number($('#item_pane .total_count').html())) {
                $('#item_pane .load_more').show();
            } else {
                $('#item_pane .load_more').hide();
                $('#item_table').off('scroll');
            }
            
        },
        get_adg_list_callback: function (data, has_more, total_count, into_next_step) {
            var table_data = template.render('adgroup_tr', {'data':data});
            $('#adgroup_table tbody').append(table_data);
            $('#adgroup_pane .total_count').attr('init_value', total_count);
            $('#adgroup_pane').attr('inited', '1');
            $.map($('#item_cart tbody tr'), function (tr_obj) {
                var item_id = $(tr_obj).attr('item_id');
                $('#adgroup_table tbody tr[item_id="'+item_id+'"]').remove();
            });
            update_statistic_data();
            if (has_more && Number($('#adgroup_pane .total_count').html())) {
                // 判断中加入 Number($('.total_count').html()) 是为了应付将所有宝贝都托管后，再输入关键词搜索的情况。
                $('#adgroup_pane .load_more').show();
            } else {
                $('#adgroup_pane .load_more').hide();
            }
            PT.hide_loading();
            adg_page_no++;
            if (into_next_step) {
                if (total_count>0) {
                    $('#modal_del_unmnt_adg .into_next_step').show();
                    $('#modal_del_unmnt_adg .btn_OK2').hide();
                    confirm_2del_unmnt_adg();
                } else {
                    $.fancybox.close();
                    PT.ChooseMntcampaign.into_next_step();
                }
            }
            sort_adgroup_table();
        },
//        check_danger_cats_callback: function (cat_id_dict) {
//            if ($.inArray(mnt_type, ['1', '2']) != -1) {
//                $('.to_mnt').show();
//            } else {
//                $('.to_mnt').hide();
//            }
//            $.map(cat_id_dict, function (danger_descr, cat_id) {
//                var tr_obj = $('#item_pane tr[cat_id="'+cat_id+'"]');
//                if (!tr_obj.hasClass('danger_cat')) {
//                  tr_obj.addClass('danger_cat');
//                  tr_obj.find('[name="cat_path"]').append('<i class="icon-warning-sign tooltips r_color large marl_6" data-original-title="'+danger_descr+'"></i>');
//                  tr_obj.find('i.tooltips').tooltip();
//                }
//            });
//            update_statistic_data();
//            $.fancybox.close();
//            $('#modal_new_item_info').modal('show');
//        },
//        generate_adg_title_callback: function (adg_title, item_id) {
//            var tr_obj = $('#item_cart tr[item_id="'+item_id+'"]');
//            tr_obj.find('.adg_title1>.loading_tag').remove();
//            tr_obj.find('.adg_title1>input').val(adg_title).show();
//            check_adg_title_length(adg_title, tr_obj);
//            tr_obj.find('[name="length_prompt"]').show();
//        },
        // TODO 双标题
        getorcreate_adg_title_list_callback: function (adg_title_list, item_id, type) {
            var tr_obj = $('#item_cart tr[item_id="'+item_id+'"]');
            var adg_title_obj = tr_obj.find('.adg_title');
            adg_title_obj.children('.loading_tag').remove();
            if (type==0) {
                for (var i in adg_title_list) {
                    adg_title_obj.children('[name="adg_title"]:eq('+i+')').val(adg_title_list[i]).show();
                    check_adg_title_length(adg_title_list[i], adg_title_obj.eq(i));
                };
                adg_title_obj.children('[name="length_prompt"]').show();
            } else if (type==1) {
                var creative_obj = adg_title_list[0], new_adg_title = adg_title_list[1];
                if ($.isPlainObject(creative_obj) && !$.isEmptyObject(creative_obj)) {
                    var i = 0;
                    for (var creative_id in creative_obj) {
                        var creative_title = creative_obj[creative_id][0], creative_img = creative_obj[creative_id][1];
                        adg_title_obj.eq(i).addClass('current').children('[name="adg_title"]').attr({'creative_id':creative_id, 'org_value':creative_title, 'org_img':creative_img, 'no':i}).val(creative_title).show();
                        tr_obj.find('[name="creative_img"]:eq('+i+')').replaceWith('<img name="creative_img" src="'+creative_img+'_80x80.jpg" width="80" height="80" title="点击换图" />');
                        check_adg_title_length(creative_title, adg_title_obj.eq(i));
                        i++;
                    }
                    if (i==1) {
                        adg_title_obj.eq(1).addClass('new').children('[name="adg_title"]').val(new_adg_title).show();
                        adg_title_obj.eq(1).children().first().html('新增创意2');
                        check_adg_title_length(new_adg_title, adg_title_obj.eq(1));
                    }
                    adg_title_obj.children('[name="length_prompt"]').show();
                } else {
                    adg_title_obj.hide();
                    tr_obj.find('.error_list').html('<i class="icon-warning-sign large marr_3"></i>获取创意失败，请先尝试同步直通车结构数据').show();
                }
            }
        },
//        get_cat_path_callback: function (item_cat_dict) {
//            for (var item_id in item_cat_dict) {
//              var tr_obj = $('#item_cart tr[item_id="'+item_id+'"]');
//              var cat_path = item_cat_dict[item_id][0];
//              var danger_descr = item_cat_dict[item_id][1];
//              if (danger_descr && !tr_obj.hasClass('danger_cat')) {
//                  cat_path += '<i class="icon-warning-sign tooltips r_color large marl_6" data-original-title="'+danger_descr+'"></i>';
//                  tr_obj.addClass('danger_cat');
//              }
//              remove_loading_tag(tr_obj, 'cat_path', cat_path);
//              tr_obj.find('i.tooltips').tooltip();
//            }
//            update_statistic_data();
//        },
        get_cat_path_callback: function (cat_dict) {
            var tr_objs = $('#item_cart tbody tr');

            $(tr_objs).each(function(){
                if(!cat_list[$(this).attr('cat_id')]){
                    // 把每次获取的类型存到全局变量中，防止多次获取类型后，前面获取的类型丢失
                    cat_list[$(this).attr('cat_id')] = cat_dict[$(this).attr('cat_id')]
                }
                var cat_info = cat_list[$(this).attr('cat_id')];
                var cat_path, danger_descr;
                if (cat_info) {
                    cat_path = cat_info[0];
                    danger_descr = cat_info[1];
                }else {
                    cat_path = '未获取到值';
                    danger_descr = '';
                }
                if (danger_descr && !$(this).hasClass('danger_cat')) {
                    cat_path += '<i class="iconfont f16 ml5 tooltips red" data-original-title="'+danger_descr+'">&#xe62b;</i>';
                    $(this).addClass('danger_cat');
                }
                remove_loading_tag($(this), 'cat_path', cat_path);
                $(this).find('i.tooltips').tooltip();
            });
            update_statistic_data();
        },
        submit_new_item: submit_new_item,
        submit_mnt_adg: submit_mnt_adg,
        add_items_callback: function (result, fail_msg, msg) {
            PT.hide_loading();
//            var init_adgroup_table = function (mnt_type) {
//              $('#item_pane .total_count').html('---');
//                var rpt_days = $('[name="last_day"]').val() || '1';
//                if (mnt_type=='0') {
//                    PT.Adgroup_list.select_call_back(rpt_days);
//                } else if (mnt_type=='1' || mnt_type=='2') {
//                    PT.MntAdg.select_call_back(rpt_days);
//                }
//            }
            if (result==0) {
                PT.alert('宝贝添加失败：'+fail_msg);
            } else {
                if($.isPlainObject(fail_msg) && !$.isEmptyObject(fail_msg)){
                    msg += '<br/>' + template.render('add_item_fail_msg', {'fail_msg':fail_msg});
                }
                init_tables();
                get_item_list();
                PT.alert(msg, null, PT.Adgroup_list.get_adgs, [1], null, 0);
            }
        },
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
                    'limit_price':Number($('#init_limit_price').val()).toFixed(2)
                };
            });
            update_mnt_adgroup_table(data);
            sort_adgroup_table()
        },
        check_creative_isvalid:check_creative_isvalid
    }
}();
