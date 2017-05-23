/**
 * Created by Administrator on 2015/10/12.
 */
define(['jl6/site_media/widget/alert/alert','jl6/site_media/widget/ajax/ajax',
        'jl6/site_media/widget/lightMsg/lightMsg','jl6/site_media/widget/loading/loading','template'],
    function(alert,ajax,lightMsg,loading,template){

    var loadAdgParams,loadItemParams;
    var mnt_type = 0;//类型
    var adg_counts = 0;//可添加宝贝数
    var cur_counts = 0;//当前已选宝贝数
    var strategy = {};
    var load = '<tr class="load_adg"><td colspan="6"><div class="text-center"><img src="/site_media/jl6/static/images/ajax_loader.gif" alt=""><br><span>请稍候...</span></div></td></tr>';
    var no_more = '<tr class="load_adg"><td colspan="6"><div class="text-center"><span>暂无更多数据</span></div></td></tr>';

    //设置计划相关配置信息
    var setStrategy = function(options){
        strategy = options;
    };

    //初始化
    var init = function(options){
        mnt_type = options.mnt_type?options.mnt_type:0;
        adg_counts = options.adg_counts?options.adg_counts:0;
        cur_counts = options.cur_count?options.cur_count:0;
        if(mnt_type!=0){
            $('.doable_count').html(adg_counts);
        }
        $('.doing_count').html(cur_counts);

        if(mnt_type==0){
            $('.show_doable_count').addClass('hide')
        }

        //获取类目
        //get_seller_cids();

        //上一页
        $('.last_page').click(function(){
            var current_page = $(this).parent().find('.current_page').text();
            if(current_page=='1'){
                if($(this).attr('load_type')=='1'){
                    $('#cur_campaign_adg_table tbody').html(no_more);
                }else{
                    $('#other_adg_table tbody').html(no_more);
                }
                return false;
            }
            if($(this).attr('load_type')=='1'){
                loadAdgParams.page_no = parseInt(current_page)-1;
                loadAdgList(loadAdgParams);
            }else{
                loadItemParams.page_no = parseInt(current_page)-1;
                loadItemList(loadItemParams);
            }
        });

        //下一页
        $('.next_page').click(function(){
            var current_page = $(this).parent().find('.current_page').text();
            var page_count = $(this).parent().find('.next_page').attr('page_no');
            if(current_page==page_count){
                if($(this).attr('load_type')=='1'){
                    $('#cur_campaign_adg_table tbody').html(no_more);
                }else{
                    $('#other_adg_table tbody').html(no_more);
                }
                return false;
            }
            if($(this).attr('load_type')=='1'){
                loadAdgParams.page_no = parseInt(current_page)+1;
                loadAdgList(loadAdgParams);
            }else{
                loadItemParams.page_no = parseInt(current_page)+1;
                loadItemList(loadItemParams);
            }
        });

        //隐藏无图片的宝贝
        $('#hide_adgs').on('change',function(){
            $('.has_campaign').parents('tr').toggleClass('hide');
        });

        //添加当前计划下的宝贝
        $('#cur_campaign_adg_table').on('click','.add_adgroup',function(){
            var tr_objs = $(this).closest('tr');
            if(mnt_type!=0){
                tr_objs = check_adg_count(tr_objs)
            }
            if(tr_objs.length>0){
                add_adgroup(tr_objs, '1');
            }
        });

        //添加其他宝贝
        $('#other_adg_table').on('click','.add_item',function(){
            var tr_objs = $(this).closest('tr');
            if(mnt_type!=0){
                tr_objs = check_adg_count(tr_objs)
            }
            if(tr_objs.length>0){
                add_item(tr_objs, '0');
            }
        });

        //批量添加宝贝
        $('.panel-group').on('click','.batch_add',function(){
            if (Number($('.doable_count').html())>0) {
                var pane_obj = $(this).closest('.panel');
                var tr_objs = pane_obj.find('tbody tr:not(.hide)');
                if(mnt_type!=0){
                    tr_objs = check_adg_count(tr_objs)
                }
                var select_counts = tr_objs.length;
                switch (pane_obj.attr('adg_type')) {
                    case 'other':
                        if(tr_objs.length>0){
                            add_item(tr_objs, '0');
                        }
                        break;
                    case 'current':
                        if(tr_objs.length>0){
                            add_adgroup(tr_objs, '1');
                        }
                        break;
                }

                //实际添加的个数等于选择的个数时需要加载下一页
                if(select_counts==tr_objs.length){
                    $(this).siblings().find('.next_page').click();
                }

            } else {
                //PT.alert('已达到托管数量上限，不能再添加宝贝了！');
                alert.show('可托管宝贝数已达上限！');
            }
        });

        //批量撤销
        $( '.undo_all').on('click', function () {

            $.map($('#item_cart').find('tr'), function (cart_obj) {
                var item_id = $(cart_obj).attr('item_id');
                var tb = $(cart_obj).attr('tb');
                var tr_obj = $('#recycle_bin tr[item_id="'+item_id+'"]');
                if (tb=='0') {
                    $('#other_adg_table').prepend(tr_obj);
                } else if (tb=='1') {
                    $('#cur_campaign_adg_table').prepend(tr_obj);
                }
                cart_obj.remove();
            });

            update_statistic_data();
        });

        //撤销宝贝
        $('#item_cart').on('click', '.undo', function () {
            var item_id = $(this).closest('tr').attr('item_id');
            var tb = $(this).closest('tr').attr('tb');
            var tr_obj = $('#recycle_bin tr[item_id="'+item_id+'"]');
            if (tb=='0') {
                $('#other_adg_table').prepend(tr_obj);
            } else if (tb=='1') {
                $('#cur_campaign_adg_table').prepend(tr_obj);
            }
            $(this).closest('tr').remove();
            update_statistic_data();
        });

        /**
         * 按类目查询，暂时不用
         */
       /* var cur_category = '全部类目'
        $('.category').on('click','.category_title',function(){
            loadItemParams['cids'] = $(this).closest('li').attr('cat_id');
            cur_category = $(this).text();
            loadItemList(loadItemParams);
            $('#collapseOne').collapse('show');
        });

        $('.category').on('change','#search_opt_category',function(){
            $('.category_name').text(cur_category);
            $('.category_title').removeClass('active');
        });*/

        //关键词查询 待选宝贝
        $('#search_btn_left').click(function(){
            var sSearch = $.trim($('#search_val_left').val());
            loadItemParams['sSearch'] = sSearch;
            loadItemParams.page_no = 1;
            loadItemList(loadItemParams);
            if(loadAdgParams){
                loadAdgParams['sSearch'] = sSearch;
                loadAdgParams.page_no = 1;
                loadAdgList(loadAdgParams);
            }
            //$('#collapseOne,#collapseTwo').collapse('show')
        });

        //回车查询
        $('#search_val_left').keyup(function(e){
            if (e.keyCode==13) {
                var sSearch = $.trim($('#search_val_left').val());
                loadItemParams['sSearch'] = sSearch;
                loadItemParams.page_no = 1;
                loadItemList(loadItemParams);
                if(loadAdgParams){
                    loadAdgParams['sSearch'] = sSearch;
                    loadAdgParams.page_no = 1;
                    loadAdgList(loadAdgParams);
                }
                //$('#collapseOne,#collapseTwo').collapse('show')
            }
        });

        $('#collapseOne').on('hidden.bs.collapse', function () {
            $('#collapseTwo').collapse('show')
        });


        //关键词查询 已选宝贝
        $('#search_cart').click(function(){
            var sSearch = $.trim($('#search_cart_val').val());
            var tr_objs = $('#item_cart tr');
            $.map(tr_objs,function(tr_obj){
                var item_title = $(tr_obj).find('[name="item_title"]').text();
                if(item_title.indexOf(sSearch)>-1){
                    $(tr_obj).show();
                }else{
                    $(tr_obj).hide();
                }
            });
        });

        //回车查询
        $('#search_cart_val').keyup(function(e){
            if (e.keyCode==13) {
                var sSearch = $.trim($('#search_cart_val').val());
                var tr_objs = $('#item_cart tr');
                $.map(tr_objs,function(tr_obj){
                    var item_title = $(tr_obj).find('[name="item_title"]').text();
                    if(item_title.indexOf(sSearch)>-1){
                        $(tr_obj).show();
                    }else{
                        $(tr_obj).hide();
                    }
                });
            }
        });

        //修改创意
        $('#item_cart').on('click', '.edit_pen_image', function () {
            var tr_obj = $(this).parents('tr');
            var obj=$(this).find('[name=creative_img]');
            var item_id = obj.closest('tr').attr('item_id');
            var cur_img = obj.attr('src');
            var no = obj.parent().index();
            var item_imgs = $.map(obj.closest('tr').find('[name="item_imgs"] li'), function (li_obj) {
                return $(li_obj).html();
            });

            if(item_imgs.length>0){
                require(['select_item_img'],function(modal){
                    modal.show({'item_id':item_id, 'no':no,'img_no':(no+1),'item_imgs':item_imgs,'cur_img':cur_img,onChange:function(item_img){
                        $('#item_cart tr[item_id="'+item_id+'"] [name="creative_img"]:eq('+no+')').replaceWith('<img name="creative_img" src="'+item_img+'" width="60" height="60" title="点击换图" />');
                    }});
                });
            }else{
                loading.show('正在加载创意图片，请稍候...');
                //获取宝贝图片
                ajax.ajax('get_item_imgs',{'item_id_list':JSON.stringify([item_id]),'context':JSON.stringify({'all_item_list':[item_id]})},function(data){
                    loading.hide();
                    var item_dict =  data.item_dict;
                    var item_imgs = item_dict[item_id];
                    require(['select_item_img'],function(modal){
                        modal.show({'item_id':item_id, 'no':no,'img_no':(no+1),'item_imgs':item_imgs,'cur_img':cur_img,onChange:function(item_img){
                            $('#item_cart tr[item_id="'+item_id+'"] [name="creative_img"]:eq('+no+')').replaceWith('<img name="creative_img" src="'+item_img+'" width="60" height="60" title="点击换图" />');
                        }});
                    });

                    var ul_imgs = tr_obj.find('[name="item_imgs"]');
                    for(var i=0;i<item_imgs.length;i++){
                        ul_imgs.append('<li>'+item_imgs[i]+'</li>');
                    }
                });
            }
        });

        //设置宝贝策略
        $('#item_cart').on('click','.set_adg_cfg',function(){
            loading.show('数据加载中，请稍候...');
            var tr_obj = $(this).parents('tr');
            var cat_id = $(tr_obj).attr('cat_id');
            ajax.ajax('get_cat_avg_cpc',{'cat_id_list':[cat_id]},function(data){
                loading.hide();
                var avg_cpc = data.avg_cpc;
                var options = {
                    mnt_opt_type:$(tr_obj).find(".mnt_opt_type").attr('value'),
                    camp_limit:$(tr_obj).find(".adg_cfg").attr('camp_limit'),
                    default_price_pc:strategy.max_price_pc,
                    default_price_yd:strategy.max_price_yd,
                    customer_price_pc:$(tr_obj).find(".limit_price_pc").attr('value'),
                    customer_price_yd:$(tr_obj).find(".limit_price_yd").attr('value'),
                    onChange:function(config){
                        if(config.use_camp_limit=='1'){
                            $(tr_obj).find('.limit_price_pc').attr('value',parseFloat(strategy.max_price_pc).toFixed(2));
                            $(tr_obj).find('.limit_price_pc').text(parseFloat(strategy.max_price_pc).toFixed(2));
                            $(tr_obj).find('.limit_price_yd').attr('value',parseFloat(strategy.max_price_yd).toFixed(2));
                            $(tr_obj).find('.limit_price_yd').text(parseFloat(strategy.max_price_yd).toFixed(2));
                        }else{
                            $(tr_obj).find('.limit_price_pc').attr('value',parseFloat(config.customer_price_pc).toFixed(2));
                            $(tr_obj).find('.limit_price_pc').text(parseFloat(config.customer_price_pc).toFixed(2));
                            $(tr_obj).find('.limit_price_yd').attr('value',parseFloat(config.customer_price_yd).toFixed(2));
                            $(tr_obj).find('.limit_price_yd').text(parseFloat(config.customer_price_yd).toFixed(2));
                        }
                        $(tr_obj).find('.adg_cfg').attr('camp_limit',config.use_camp_limit);
                        $(tr_obj).find('.mnt_opt_type').attr('value',config.mnt_opt_type);
                        if(config.mnt_opt_type==2){
                            $(tr_obj).find('.mnt_opt_type').text('只改价');
                        }else{
                            $(tr_obj).find('.mnt_opt_type').text('自动优化');
                        }
                    }
                };
                options['avg_price'] = avg_cpc.toFixed(2);
                options['min_price'] = Math.max((avg_cpc*0.3).toFixed(2),0.05);
                if(mnt_type==1 || mnt_type==3){
                    options['suggest_price'] = (avg_cpc* 1.5).toFixed(2)+'~'+(avg_cpc* 2.5).toFixed(2);
                }else{
                    options['suggest_price'] = (avg_cpc* 2).toFixed(2)+'~'+(avg_cpc* 3).toFixed(2);
                }

                options['opt_adgroup'] = false;
                require(['set_adg_cfg'],function(modal){
                    modal.show(options);
                });
            },null,{'url':'/mnt/ajax/'})

        });

        $('#item_cart').on('keyup', 'input[name="adg_title"]', function () {
            check_adg_title_length($(this).val(), $(this).parent());
        });

        $('#hide_no_pic').on('change',function(){
            if($(this).prop('checked')){
                $('tr[has_pic=0]').addClass('hide');
            }else{
                 $('tr[has_pic=0]').removeClass('hide');
            }
        });

        $('#collapseOne,#collapseTwo').on('show.bs.collapse', function () {
            $(this).prev().find('.collapse-icon').toggleClass('hide');
        })

        $('#collapseOne,#collapseTwo').on('hide.bs.collapse', function () {
            $(this).prev().find('.collapse-icon').toggleClass('hide');
        });

    };

    //查询当前计划下宝贝列表数据
    var loadAdgList = function(params){
        $('#cur_campaign_adg_table tbody').html(load);
        ajax.ajax('get_adg_list',params,loadAdgListBack,null,{'url':'/mnt/ajax/'});
        loadAdgParams = params;
    };

    //查询当前计划下宝贝列表数据回调函数
    var loadAdgListBack = function(data){
        var html,
        tpl=__inline("add_item_box.html");
        var datas = data.data;
        var temp_data = [];
        var has_pic = true;
        for(var i=0;i<datas.length;i++){
            if(!$('#item_cart tbody tr[item_id="'+datas[i].item_id+'"]').length){
                temp_data.push(datas[i]);
            }
            if(!datas[i].has_pic){
                has_pic = false;
            }
        }
        if(!has_pic){
            $('.hide_no_pic').removeClass('hide');
        }
        html = template.compile(tpl)({adg_list:temp_data,list_type:0});
        //如果有更多数据，则需要显示分页工具
        if(data.page_count>1){
            $('#more_adgs').removeClass('hide');
            $('#more_adgs').find('.current_page').text(data.current_page);
            $('#more_adgs').find('.page_count').text(data.page_count);
            $('#more_adgs').find('.last_page').attr('page_no',(parseInt(data.current_page)-1));
            if(!data.has_more){
                $('#more_adgs').find('.next_page').attr('page_no',(parseInt(data.current_page)));
            }else{
                $('#more_adgs').find('.next_page').attr('page_no',(parseInt(data.current_page)+1));
            }
        }

        $('#cur_campaign_adg_table tbody').html(html);

    };

    //查询其他宝贝列表
    var loadItemList = function(params){
        $('#other_adg_table tbody').html(load);
        ajax.ajax('get_item_list',params,loadItemListBack,null,{'url':'/mnt/ajax/'});
        loadItemParams = params;
    };

    //查询其他宝贝列表回调函数
    var loadItemListBack = function(data){
        var html,
        tpl=__inline("add_item_box.html");
        var datas = data.data;
        var temp_data = [];
        var has_pic = true;
        for(var i=0;i<datas.length;i++){
            if(!$('#item_cart tbody tr[item_id="'+datas[i].item_id+'"]').length){
                temp_data.push(datas[i]);
            }
            if(!datas[i].has_pic){
                has_pic = false;
            }
        }
        if(!has_pic){
            $('.hide_no_pic').removeClass('hide');
        }
        html = template.compile(tpl)({adg_list:temp_data,list_type:'other'});

        //如果有更多数据，则需要显示分页工具
        $('#more_other_items').find('.current_page').text(data.current_page);
        if(data.has_more){
            $('#more_other_items').removeClass('hide');
            $('#more_other_items').find('.last_page').attr('page_no',(parseInt(data.current_page)-1));
            $('#more_other_items').find('.next_page').attr('page_no',(parseInt(data.current_page)+1));
        }else{
            //如果没有更多数据，则需判断是否在第一页，若在第一页，则不显示分页工具
            if(data.current_page==1){
                $('#more_other_items').addClass('hide');
            }
            $('#more_other_items').find('.next_page').attr('page_no',(parseInt(data.current_page)));
        }
        $('#other_adg_table tbody').html(html);
        $('#hide_adgs').removeAttr('checked');
        $('.adg_camp span').tooltip({html:true});
    };

    // 添加未在当前计划中的宝贝
    var add_item = function (tr_objs,tb) {
        add_to_cart(tr_objs,tb);
    }

    //添加当前计划中的宝贝
    var add_adgroup = function (tr_objs,tb) {
        add_to_cart(tr_objs,tb);
    }

    // 检查并获取宝贝图片
    var add_to_cart = function (tr_objs,tb) {
        var all_item_list = [], to_handle_item_list = [];
        var results = {};
        for(var i = 0;i<tr_objs.length;i++){
            var tr_obj = tr_objs[i];
            if(!$(tr_obj).hasClass('load_adg')){
                var item_id = $(tr_obj).attr('item_id');
                all_item_list.push($(tr_obj).attr('item_id'));
                to_handle_item_list.push(Number($(tr_obj).attr('item_id')));
                var item_imgs = $.map($(tr_obj).find('[name="item_imgs"] li'), function (li_obj) {return $(li_obj).html();});
                var result =  {'adgroup_id': $(tr_obj).attr('adgroup_id'),
                                'item_id': $(tr_obj).attr('item_id'),
                                'title': $(tr_obj).find('[name="item_title"]').html(),
                                'pic_url':$(tr_obj).find('.pic_url').attr('src'),
                                'cat_id': $(tr_obj).attr('cat_id')
                                };
                results[item_id] = result;
            }
        }
        update_mnt_adgroup_table(results,tb,tr_objs);
    };

    //在右侧已选宝贝列表中添加数据
    var update_mnt_adgroup_table = function (data,tb,tr_objs) {
        var html,tpl=__inline("add_item_cart.html");
        html = template.compile(tpl)({'data':data, 'mnt_type':mnt_type,'tb':tb,'strategy':strategy});
        $('#item_cart tbody').prepend(html);

        tr_objs.removeClass('hover');
        $('#recycle_bin').append(tr_objs.clone());
        tr_objs.remove();
        update_statistic_data();
        getorcreate_adg_title_list(data);
    }

    // 生成创意标题
    var getorcreate_adg_title_list = function (datas) {
        for (var i in datas) {
            ajax.ajax('getorcreate_adg_title_list',{item_id:datas[i].item_id,adgroup_id:datas[i]['adgroup_id'] || 0,'title':datas[i].title},function(data){
                var type = data.type;
                var item_id = data.item_id;
                var adg_title_list = eval('('+data.adg_title_list+')');
                var tr_obj = $('#item_cart tr[item_id="'+item_id+'"]');
                var adg_title_obj = tr_obj.find('.adg_title');
                if (type==0) {
                    for (var i in adg_title_list) {
                        adg_title_obj.children('[name="adg_title"]:eq('+i+')').val(adg_title_list[i]).show();
                        check_adg_title_length(adg_title_list[i], adg_title_obj.eq(i));
                    };
                    adg_title_obj.children('[name="length_prompt"]').removeClass('hide');
                } else if (type==1) {

                    var creative_obj = adg_title_list[0], new_adg_title = adg_title_list[1];
                    if ($.isPlainObject(creative_obj) && !$.isEmptyObject(creative_obj)) {
                        var i = 0;
                        for (var creative_id in creative_obj) {
                            var creative_title = creative_obj[creative_id][0], creative_img = creative_obj[creative_id][1];
                            adg_title_obj.eq(i).addClass('current').children('[name="adg_title"]').attr({'creative_id':creative_id, 'org_value':creative_title, 'org_img':creative_img, 'no':i}).val(creative_title).show();
                            tr_obj.find('[name="creative_img"]:eq('+i+')').replaceWith('<img name="creative_img" src="'+creative_img+'_60x60.jpg" title="点击换图" />');
                            check_adg_title_length(creative_title, adg_title_obj.eq(i));
                            i++;
                        }
                        if (i==1) {
                            adg_title_obj.eq(1).addClass('new').children('[name="adg_title"]').val(new_adg_title).show();
                            adg_title_obj.eq(1).children().first().html('新增创意2：');
                            check_adg_title_length(new_adg_title, adg_title_obj.eq(1));
                        }
                        adg_title_obj.children('[name="length_prompt"]').show();
                    } else {
                        adg_title_obj.hide();
                        tr_obj.find('.error_list').html('<i class="icon-warning-sign large marr_3"></i>获取创意失败，请先尝试同步直通车结构数据').show();
                    }
                }
            });
        }
    }

    // 检查创意标题长度
    var check_adg_title_length = function (adg_title, parent_obj) {
        var char_delta = Math.floor(20-bytes_len($.trim(adg_title))/2);
        if (char_delta>=0) {
            parent_obj.find('[name="char_delta"]').html('剩'+Math.abs(char_delta)+'个汉字');
        } else {
            parent_obj.find('[name="char_delta"]').html('<span class="red">超'+Math.abs(char_delta)+'个汉字</span>');
        }

        parent_obj.find('input[name="adg_title"]').attr('char_delta',char_delta);
        return char_delta;
    }

    //获取类目
    var get_seller_cids = function(){
        ajax.ajax('get_seller_cids',{},function(data){
            var html,tpl=__inline("adg_category.html");
                html = template.compile(tpl)({cat_list:data.cat_list});
            $('.category').html(html);
        },null,{'url':'/mnt/ajax/'});
    };

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

    // 处理图片链接
    var handle_img_url = function (img_url) {
        img_url = img_url.replace("_70x70.jpg", "");
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

    //获取选中的计划内的宝贝列表及参数
    var getMntAdgInfo = function(){
        var mnt_adg_dict = {}, update_creative_dict = {}, new_creative_list = [];
        $.map($('#item_cart tbody tr[tb="1"]'), function (tr_obj) {
            var adg_id = Number($(tr_obj).attr('adgroup_id'));
            if (adg_id) {

                var item_obj = {
                    title1: $.trim($(tr_obj).find('[name="adg_title"]:eq(0)').val()),
                    title2: $.trim($(tr_obj).find('[name="adg_title"]:eq(1)').val()),
                    img_url1: handle_img_url($(tr_obj).find('[name="creative_img"]:eq(0)').attr('src')),
                    img_url2: handle_img_url($(tr_obj).find('[name="creative_img"]:eq(1)').attr('src')),
                    limit_price : Number(strategy.limit_price)*100,
                    mobile_limit_price : Number(strategy.limit_price)*100,
                    use_camp_limit:1,
                    mnt_opt_type:1
                }

//                if(mnt_type==2||mnt_type==4){
//                    item_obj['limit_price'] = (Number($(tr_obj).find('.limit_price').text())*100).toFixed(0);
//                    item_obj['use_camp_limit'] = $(tr_obj).find('.adg_cfg').attr('camp_limit');
//                    item_obj['mnt_opt_type'] = $(tr_obj).find('.mnt_opt_type').attr('value');
//                }else{
//                    item_obj['mnt_opt_type'] = strategy.mnt_opt_type;
//                }
                item_obj['limit_price'] = (Number($(tr_obj).find('.limit_price_pc').text())*100).toFixed(0);
                item_obj['mobile_limit_price'] = (Number($(tr_obj).find('.limit_price_yd').text())*100).toFixed(0);
                item_obj['use_camp_limit'] = $(tr_obj).find('.adg_cfg').attr('camp_limit');
                item_obj['mnt_opt_type'] = $(tr_obj).find('.mnt_opt_type').attr('value');
                mnt_adg_dict[adg_id] = item_obj;

                for (var i=0;i<2;i++) {
                    var input_obj = $(tr_obj).find('[name="adg_title"]:eq('+i+')');
                    var img_url = handle_img_url($(tr_obj).find('[name="creative_img"]:eq('+i+')').attr('src'));
                    if (input_obj.parent().hasClass('current')) {
                        var creative_img = handle_img_url($(tr_obj).find('[name="creative_img"]:eq('+i+')').attr('src')).split('.taobaocdn.com/', 2)[1];
                        var org_img = input_obj.attr('org_img').split('.taobaocdn.com/', 2)[1];
                        if (input_obj.val()!=input_obj.attr('org_value') || creative_img!=org_img) {
                            update_creative_dict[Number(input_obj.attr('creative_id'))] = [adg_id, $.trim(input_obj.val()), img_url];
                        }
                    } else if (input_obj.parent().hasClass('new')) {
                        new_creative_list.push([adg_id, $.trim(input_obj.val()), img_url]);
                    }
                }
            }
        });
        return {mnt_adg_dict:mnt_adg_dict, update_creative_dict:update_creative_dict, new_creative_list:new_creative_list};
    };

    //获取新增宝贝列表信息
    var getNewItemDict = function(){
        var new_item_dict = {};
        $.map($('#item_cart tbody tr[tb="0"]'), function (tr_obj) {
            var item_id = $(tr_obj).attr('item_id');
            if (item_id) {
                var item_obj = {
                    title1: $.trim($(tr_obj).find('[name="adg_title"]:eq(0)').val()),
                    title2: $.trim($(tr_obj).find('[name="adg_title"]:eq(1)').val()),
                    img_url1: handle_img_url($(tr_obj).find('[name="creative_img"]:eq(0)').attr('src')),
                    img_url2: handle_img_url($(tr_obj).find('[name="creative_img"]:eq(1)').attr('src')),
                    limit_price : Number(strategy.limit_price)*100,
                    mobile_limit_price : Number(strategy.limit_price)*100,
                    mnt_opt_type:1,
                    use_camp_limit:1
                };

//                if(mnt_type==2||mnt_type==4){
//                    item_obj['limit_price'] = (Number($(tr_obj).find('.limit_price').text())*100).toFixed(0);;
//                    item_obj['use_camp_limit'] = $(tr_obj).find('.adg_cfg').attr('camp_limit');
//                    item_obj['mnt_opt_type'] = $(tr_obj).find('.mnt_opt_type').attr('value');
//                }else{
//                    item_obj['mnt_opt_type'] = strategy.mnt_opt_type;
//                }
                item_obj['limit_price'] = (Number($(tr_obj).find('.limit_price_pc').text())*100).toFixed(0);
                item_obj['mobile_limit_price'] = (Number($(tr_obj).find('.limit_price_yd').text())*100).toFixed(0);
                item_obj['use_camp_limit'] = $(tr_obj).find('.adg_cfg').attr('camp_limit');
                item_obj['mnt_opt_type'] = $(tr_obj).find('.mnt_opt_type').attr('value');
                new_item_dict[item_id] = item_obj;
            }
        });

        return new_item_dict;
    };

    // 更新宝贝个数统计
    var update_statistic_data = function () {
        var doing_count = $('#item_cart tbody tr').length;
        $('.doing_count').text($('#item_cart tbody tr').length);
         if(mnt_type!=0){
            $('.doable_count').html(adg_counts-doing_count);
        }

    }

    //检查已选宝贝个数是否超过上线
    var check_adg_count = function(tr_objs){
        var doing_count = $('#item_cart tbody tr').length;

        if((tr_objs.length+doing_count)>adg_counts){
            alert.show('最多只能托管'+adg_counts+'个宝贝，多出的宝贝将不会添加。');
            tr_objs = tr_objs.slice(0, (adg_counts - doing_count));
        }
        return tr_objs;
    }

    //重新渲染add_item_box
    var reDraw = function(options){
        mnt_type = options.mnt_type?options.mnt_type:0;
        adg_counts = options.adg_counts?options.adg_counts:500;
        cur_counts = options.cur_count?options.cur_count:0;
        if(mnt_type!=0){
            $('.doable_count').html(adg_counts);
        }
        $('.doing_count').html(cur_counts);
        $('#other_adg_table tbody').html('');
        $('#other_adg_table tbody').html('');
        $('#more_other_items tbody').html('');
        $('#item_cart tbody').html('');
    };

    var getSelectCounts = function(){
        return parseInt($('.doing_count').html());
    };

    return {
        init:init,
        loadAdgList:loadAdgList,
        loadItemList:loadItemList,
        getMntAdgInfo:getMntAdgInfo,
        getNewItemDict:getNewItemDict,
        setStrategy:setStrategy,
        getSelectCounts:getSelectCounts,
        reDraw:reDraw
    }
});
