/**
 * Created by Administrator on 2015/9/19.
 */
define(['require','template','../page_tool/page_tool','dataTable','jl6/site_media/widget/ajax/ajax',
        'jl6/site_media/widget/loading/loading','select_tool','../report_detail/report_detail',
        'jl6/site_media/widget/lightMsg/lightMsg','jl6/site_media/widget/alert/alert'],
    function(require,template,page_tool,dataTable,ajax,loading,select_tool,report_detail,lightMsg,alert) {
    "use strict"

    var sort_dict = {
        checkbox:0,img:1,title:2,impressions:3,click:4,ctr:5,cost:6,ppc:7,favcount:8,
        carttotal:9,paycount:10,conv:11,pay:12,roi:13,online_status:14,mnt_opt_type:15,opt:16
    };
    var sort_column = 'pay',sort_type= -1,sort_desc = 'desc';
    var condition = {};
    var goods_table;
    var page_count = 1;

    var init_dom=function(_list_type,start_date,end_date,camp_id){
        condition = {
            search_type: 'all',
            PAGE_NO: 1,
            PAGE_SIZE: 50,
            CONSULT_WW: $('#CONSULT_WW').val(),
            page_type: parseInt($('#page_type').val()),
            start_date:start_date,
            end_date:end_date,
            last_day: 7,
            adgroup_table: null,
            camp_id: camp_id,
            search_word: $('#search_val').val(),
            opt_type:-1,
            status_type: '',
            max_num: parseInt($('#mnt_max_num').val()),
            mnt_type: parseInt($('#mnt_type').val()),
            sort: 'pay_-1',
            list_type: _list_type,
            is_follow: -1
        }

        getGoodsList();

        bind_event();
    }

    //绑定计划列表事件
    var bind_event=function(){

        //显示全部细分
        $('#show_subdivide_all').on('click',function(){
            if ($(this).data('is_lock')) {
                return; // 防止连续多次重复点击
            };
            $(this).data('is_lock', 1);
            var is_showing = $(this).data('is_showing');
            $.map($('#goods_table .show_subdivide'),function(obj){
                if($(obj).data('is_showing') == is_showing){
                    $(obj).click();
                }
            });
            if (is_showing){
                delete($(this).data().is_showing);
            }else{
                $(this).data('is_showing', 1);
            }
            delete($(this).data().is_lock);
        });

        //显示细分
        $('#goods_table').on('click','.show_subdivide',function() {
            if ($(this).data('is_lock')) {
                return; // 防止连续多次重复点击
            };
            $(this).data('is_lock', 1);
            var html,obj,adgroup_id,tr_obj,camp_id;
            var tpl=__inline("subdivide.html");
            var that = this;
            tr_obj=$(this).closest('tr');
            adgroup_id = $(this).parents("tr").attr('adgroup_id');
            camp_id = $(this).parents("tr").attr('campaign_id');

            if ($(this).data('is_showing')) {
                tr_obj.data('subdivide').remove();
                delete($(this).data().is_showing); // 一定要删除
                delete($(this).data().is_lock);
            }else if(tr_obj.data('subdivide')) {
                var obj = tr_obj.data('subdivide');
                tr_obj.after(obj);
                $(this).data('is_showing', 1);
                delete($(this).data().is_lock);
            }else{
                $(this).data('is_showing', 1);
                ajax.ajax('get_adg_split_rpt',{adgroup_id:adgroup_id, camp_id:camp_id, 'start_date':condition.start_date,'end_date':condition.end_date},function(data){
                    var result = data.result;
                    var tpl_data = {id:campaign_id}
                    for(var i=0;i<result.length;i++){
                        var temp_result = result[i];
                        switch (temp_result.source_id){
                            case 1:
                                tpl_data['pcin'] = temp_result;
                                break;
                            case 2:
                                tpl_data['pcout'] = temp_result;
                                break;
                            case 4:
                                tpl_data['ydin'] = temp_result;
                                break;
                            case 5:
                                tpl_data['ydout'] = temp_result;
                                break;
                            default:
                                break;
                        }
                    }
                    html = template.compile(tpl)(tpl_data);
                    obj=$(html);
                    tr_obj.after(obj);
                    $(tr_obj).data('subdivide',obj);
                    $(that).data('is_showing', 1);
                    delete($(that).data().is_lock);
                });
            }
        });

        //显示报表
        report_detail.init();
        $('#goods_table').on('click','.show_chart', function() {
            var adg_title, adgroup_id;
            adg_title=$(this).closest('tr').find('.title>a').text();
            adgroup_id = $(this).parents("tr").attr('adgroup_id');
            report_detail.show('宝贝明细：'+adg_title, 'adgroup', $('#shop_id').val(), null, adgroup_id);
        });

        //关注/取消
         $('#goods_table').on('click','.set_follow_status', function() {
             var tr_obj= $(this).parents("tr");
             var follow_status, adgroup_id, campaign_id;
             adgroup_id = tr_obj.attr('adgroup_id');
             campaign_id=tr_obj.attr('campaign_id');
             follow_status = $(this).attr('value');
             if(follow_status=='1'){
                 follow_status = 0;
             }else{
                 follow_status = 1;
             }
             ajax.ajax('set_adg_follow', {
                    'adgroup_id':adgroup_id,
                    'campaign_id':campaign_id,
                    'is_follow':follow_status
              }, function(data){
                    tr_obj.find('.set_follow_status').attr('value', data.is_follow);
                    if(data.is_follow){
                        tr_obj.find('.set_follow_status').html('&#xe675;');
                        tr_obj.find('.set_follow_status').attr('data-original-title', '点击可取消关注');
                        lightMsg.show({body:'设为关注宝贝成功！'});
                        tr_obj.find('.set_follow_status').removeClass('hover_show');
                    }else{
                        tr_obj.find('.set_follow_status').html('&#xe674;');
                        tr_obj.find('.set_follow_status').attr('data-original-title', '点击可设置为关注宝贝');
                        tr_obj.find('.set_follow_status').addClass('hover_show');
                        lightMsg.show({body:'取消关注宝贝成功！'});
                    }
                    tr_obj.find('.set_follow_status').tooltip('show');
              });
        });

        //修改状态
        $('#goods_table').on('click','.switch_status', function() {
            var adgroup_id = $(this).parents("tr").attr('adgroup_id');
            var opt_type = $(this).text();
            //在这里进行切换状态操作
            require(['jl6/site_media/widget/confirm/confirm'],function(confirm){
                confirm.show({'body':'确定要'+opt_type+'推广该宝贝么？','okHide':function(){
                    //在这里进行删除操作

                    if(opt_type=='开启'){
                        update_adg_status('start', adgroup_id);
                    }else{
                        update_adg_status('stop', adgroup_id);
                    }
                }});
            });

        });

        //删除宝贝
        $('#goods_table').on('click','.del_good', function() {
            var adgroup_id = $(this).parents("tr").attr('adgroup_id');
            require(['jl6/site_media/widget/confirm/confirm'],function(confirm){
                confirm.show({'body':'确定要删除该宝贝么？','okHide':function(){
                    //在这里进行删除操作
                    update_adg_status('del', adgroup_id);
                }});
            });
        });

        //修改移动折扣
        $('#goods_table').on('click','.edit_adg_mobdiscount', function() {
            var title_warp = $(this).closest('tr').find('.adg_mobdiscount');
            var org_discount = title_warp.text();
            var campaign_id = $(this).parents("tr").attr('campaign_id');
            var adgroup_id = $(this).parents("tr").attr('adgroup_id');
            require(["../edit_mobdiscount/edit_mobdiscount"],function(modal){
                modal.show({
                    value: org_discount,
                    obj: title_warp,
                    campaign_id: campaign_id,
                    adgroup_id: adgroup_id
                });
            });
        });

        //设置托管状态(重点计划宝贝列表)
        $('#goods_table').on('click','.change_mnt_type',function(){
            var obj = $(this);
            var adg_tr = $(this).closest('tr');
            var adgroup_id=adg_tr.attr('adgroup_id');
            var cat_id=adg_tr.attr('cat_id');
            var camp_id=adg_tr.attr('campaign_id');
            var camp_mnt_type = adg_tr.data('camp_mnt_type');
            var mnt_opt_type = $(this).attr('mnt_opt_type');
            //以下判断是为了兼容旧版数据
            if($(this).attr('mnt_type')=='0'){
                mnt_opt_type=0;
            }else{
                if(mnt_opt_type==''){
                    mnt_opt_type = 1;
                }
            }
            var default_price_pc = parseFloat(adg_tr.data('camp_max_price')).toFixed(2);
            var default_price_yd = parseFloat(adg_tr.data('camp_max_mobile_price')).toFixed(2);
            var customer_price_pc = obj.next().find('.limit_price').text();
            var customer_price_yd = obj.next().find('.mobile_limit_price').text();
            if(customer_price_pc=="0.00"){
                customer_price_pc = default_price_pc;
            }
            if(customer_price_yd=="0.00"){
                customer_price_yd = default_price_yd;
            }
            var use_camp_limit = $(this).attr('use_camp_limit');

            loading.show("数据加载中，请稍候...");
            ajax.ajax('get_cat_avg_cpc',{'cat_id_list':[cat_id]},function(data){
                loading.hide();
                var avg_cpc = data.avg_cpc;
                var options = {
                    default_price_pc: default_price_pc,
                    default_price_yd: default_price_yd,
                    customer_price_pc:customer_price_pc,
                    customer_price_yd:customer_price_yd,
                    onChange:function(config){
                        ajax.ajax('update_single_adg_mnt',
                            {'adg_id':adgroup_id,
                            'flag':config.mnt_opt_type,
                            'mnt_type':camp_mnt_type,
                            'camp_id':camp_id,
                            'use_camp_limit':config.use_camp_limit,
                            'limit_price':config.customer_price_pc,
                            'mobile_limit_price':config.customer_price_yd
                            },function(data){
                                lightMsg.show({body:'修改成功！'});
                                update_mnt_num(parseInt(mnt_opt_type),parseInt(config.mnt_opt_type));
                                obj.attr('use_camp_limit',config.use_camp_limit);
                                var status = '自动优化';
                                var sort_value = 1;
                                obj.attr('mnt_type',config.mnt_opt_type);
                                var tr_obj = $(obj).closest('tr');
                                var td_obj = $(obj).closest('td');
                                if(data.flag==0){
                                    status = '未托管';
                                    sort_value = 3;
                                    obj.attr('mnt_type',0);
                                    tr_obj.find('.mnt_type_true').removeClass('hide');
                                    tr_obj.find('.mnt_type_false').addClass('hide');
                                    //未托管时 有一键优化按钮
                                    if(tr_obj.find('.onekey').length==0){
                                          var adgroup_id = tr_obj.attr('adgroup_id');
                                          var campaign_id = tr_obj.attr('campaign_id');
                                          var onekey = '<a href="javascript:;" class="onekey" adgroup_id="'+adgroup_id+'" campaign_id="'+campaign_id+'"><span><strong>一键优化</strong></span></a>';
                                          tr_obj.find('.opt_url').append(onekey);
                                    }
                                }else{
                                    tr_obj.find('.mnt_type_false').removeClass('hide');
                                    tr_obj.find('.mnt_type_true').addClass('hide');
                                    if(data.flag==2){
                                        status = '只改价';
                                        sort_value = 2;
                                    }
                                    tr_obj.find('.onekey').remove();
                                }
                                obj.prev().text(status);
                                td_obj.find('.sort_value').text(sort_value);
                                obj.attr('mnt_opt_type',data.flag);

                                //当自动优化或改价时要显示限价
                                if(config.mnt_opt_type!=0){
                                    obj.next().removeClass('hide')
                                    if(config.use_camp_limit==1){
                                        obj.next().find('.limit_price').text(default_price_pc);
                                        obj.next().find('.mobile_limit_price').text(default_price_yd);
                                    }else{
                                        obj.next().find('.limit_price').text(parseFloat(config.customer_price_pc).toFixed(2));
                                        obj.next().find('.mobile_limit_price').text(parseFloat(config.customer_price_yd).toFixed(2));
                                    }
                                    obj.next('.optm_submit_time').addClass('hide');
                                    td_obj.find('.optm_submit_time').addClass('hide');
                                }else{
                                    obj.next().addClass('hide')
                                    td_obj.find('.optm_submit_time').removeClass('hide');
                                }

                        },null,{'url':'/mnt/ajax/'});
                    }
                };
                options['avg_price'] = avg_cpc.toFixed(2);
                options['min_price'] = Math.max((avg_cpc*0.3).toFixed(2),0.05);
                if(mnt_type==1 || mnt_type==3){
                    options['suggest_price'] = (avg_cpc* 1.5).toFixed(2)+'~'+(avg_cpc* 2.5).toFixed(2);
                }else{
                    options['suggest_price'] = (avg_cpc* 2).toFixed(2)+'~'+(avg_cpc* 3).toFixed(2);
                }
                options['opt_adgroup'] = true;
                options['mnt_opt_type'] = mnt_opt_type;
                options['camp_limit'] = use_camp_limit;
                require(['../add_item_box/set_adg_cfg'],function(modal){
                    modal.show(options);
                });
            },null,{'url':'/mnt/ajax/'})
        });

        //设置托管状态（长尾计划宝贝列表）
        $('#goods_table').on('mouseenter','.change_mnt_type_pop',function(){
            var obj = $(this);
            var adgroup_id=$(obj).closest('tr').attr('adgroup_id');
            var camp_id=$(obj).closest('tr').attr('campaign_id');
            var mnt_type = $('#page_type').val();
            var mnt_opt_type = $(obj).attr('mnt_opt_type');
            if($(obj).attr('mnt_type')==0){
                mnt_opt_type=0;
            }
            var params = {'adg_id':adgroup_id,
                          'mnt_type':mnt_type,
                          'camp_id':camp_id,
                          'limit_price':0,
                          'mnt_opt_type':mnt_opt_type
                          };
            require(['select_mnt_type'],function(select_mnt_type){
                select_mnt_type.popover(obj,params,function(data){
                    lightMsg.show({body:'修改成功！'});
                    obj.attr('mnt_type',mnt_type);
                    obj.attr('mnt_opt_type',data.flag);

                    update_mnt_num(parseInt(mnt_opt_type),parseInt(data.flag));
                    var tr_obj = $(obj).closest('tr');
                    var td_obj = $(obj).closest('td');
                    if(data.flag==1){
                        $(obj).prev().text('自动优化');
                        td_obj.find('.sort_value').text(1);
                        tr_obj.find('.mnt_type_false').removeClass('hide');
                        tr_obj.find('.mnt_type_true').addClass('hide');
                        td_obj.find('.optm_submit_time').addClass('hide');
                        tr_obj.find('.onekey').remove();
                    }else if(data.flag==2){
                        $(obj).prev().text('只改价');
                        td_obj.find('.sort_value').text(2);
                        tr_obj.find('.mnt_type_false').removeClass('hide');
                        tr_obj.find('.mnt_type_true').addClass('hide');
                        td_obj.find('.optm_submit_time').addClass('hide');
                        tr_obj.find('.onekey').remove();
                    }else{
                        $(obj).prev().text('未托管');
                        td_obj.find('.sort_value').text(3);
                        tr_obj.find('.mnt_type_true').removeClass('hide');
                        tr_obj.find('.mnt_type_false').addClass('hide');
                        td_obj.find('.optm_submit_time').removeClass('hide');

                        if(tr_obj.find('.onekey').length==0){
                              var adgroup_id = tr_obj.attr('adgroup_id');
                              var campaign_id = tr_obj.attr('campaign_id');
                              var onekey = '<a href="javascript:;" class="onekey" adgroup_id="'+adgroup_id+'" campaign_id="'+campaign_id+'"><span><strong>一键优化</strong></span></a>';
                              tr_obj.find('.opt_url').append(onekey);
                        }
                    }

                    $(obj).data('popover',0);
                    $(obj).popoverList('destroy');
                });
            });
        });

        //进入优化根据宝贝优化状态，跳转到不同页面
        $("#goods_table").on('click','.to_optimize',function(){
            var tr_obj = $(this).closest('tr');
            var mnt_type = tr_obj.find('.mnt_opt_type').attr('mnt_type');
            var mnt_opt_type = tr_obj.find('.mnt_opt_type').attr('mnt_opt_type');
            var adgroup_id = $(this).attr('adgroup_id');
            if(mnt_type=='0'){
                //未托管，跳转到只能优化页面
                window.open('/web/smart_optimize/'+adgroup_id,"_blank")
            }else{
                //已托管，跳转到托管详情
                if(mnt_opt_type=='2' || mnt_opt_type=='1'){
                    window.open('/mnt/adgroup_data/'+adgroup_id,"_blank")
                }else{
                    window.open('/web/smart_optimize/'+adgroup_id,"_blank")
                }
            }
        });

        //一键优化
        $('#goods_table').on('click','.onekey', function() {
            var adgroup_id = $(this).attr('adgroup_id');
            var campaign_id = $(this).attr('campaign_id');
            loading.show('系统正在努力分析数据，请稍候...');
            ajax.ajax('get_onekey_optimize', {
                'adgroup_id':adgroup_id,
                'campaign_id':campaign_id
            }, function(data){
                loading.hide();
                require(['confirm_win'],function(modal){
                    var confirm_win = $('#modal_confirm_win');
                    if (confirm_win){
                        confirm_win.remove();
                    }
                    if(data.update_count + data.del_count + data.add_count > 0){
                        modal.show({result: data});
                    }else{
                        alert.show("建议观察一段时间再优化或者手动添加关键词!");
                    }

                });
            });
        });

        //提交一键优化结果
        $(document).on('click','#submit_onekey',function(){
            var adgroup_id = $(this).attr('adgroup_id');
            var is_update = $('#chk_update').is(':checked');
            var is_del = $('#chk_del').is(':checked');
            var is_add = $('#chk_add').is(':checked');
            var temp_count = 0;

            var arr = [];
            if(is_update){
                arr.push('update');
                var update = parseInt($('#lbl_update').text());
                temp_count += update;
            }
            if(is_del){
                arr.push('del');
                var del = parseInt($('#lbl_del').text());
                temp_count += del;
            }
            if(is_add){
                arr.push('add');
                var add = parseInt($('#lbl_add').text());
                temp_count += add;
            }
            if (arr.length == 0){
                $('#error_onekey').text('至少选择一个优化项目').fadeOut(300).fadeIn(500).removeClass('hide');
            }else if(temp_count == 0){
                $('#error_onekey').text('当前没有优化项目').fadeOut(300).fadeIn(500).removeClass('hide');
            }else{
                $('#chk_update').attr('disabled', 'disabled');
                $('#chk_del').attr('disabled', 'disabled');
                $('#chk_add').attr('disabled', 'disabled');
                $('#submit_onekey').attr('disabled', 'disabled');
                $('#cancel_onekey').addClass('hide');
                $('#error_onekey').addClass('hide');
                submit_onekey_optimize(adgroup_id, arr);
            }
        });

        //递规调用ajax向后台提交
        var submit_onekey_optimize = function(adgroup_id, arr){
            if (arr.length > 0){
                var type = arr[0];
                $('#img_' + type).removeClass('hide');
                $('#sp_' + type).addClass('hide');
                ajax.ajax('submit_onekey_optimize', {
                    'adgroup_id':adgroup_id,
                    'type':type
                }, function(result){
                    setTimeout(function (){
                        $('#sp_' + type).removeClass('hide').text(result.result);
                        $('#img_' + type).addClass('hide');
                        arr.shift();
                        submit_onekey_optimize(adgroup_id, arr);
                    }, 300);
                });
            }else{
                ajax.ajax('finish_onekey_optimize', {
                    'adgroup_id':adgroup_id
                },function(result){
                    $('.adg_tr[adgroup_id=' + adgroup_id + ']').find('.optm_submit_time').html('<br />' + result.time + '优化过');
                    $('#submit_onekey').addClass('hide');
                    $('#finish_onekey').removeClass('hide');
                });
            }
        }

        $('#goods_table thead th').unbind('click').click(function(){
            if(page_count>1){
                sort_column = $(this).data('active');
                if(sort_column){
                     //如果是升序，本次查询按升序查，点击后图标变为降序，否则反过来
                    if($(this).attr('class').indexOf('desc')>-1){
                        sort_type = 1;
                        sort_desc = 'asc'
                    }else{
                        sort_type = -1;
                        sort_desc = 'desc'
                    }
                    condition.sort = sort_column+"_"+sort_type;
                    getGoodsList();
                }
            }
        });
    }

    //宝贝开启、推广、暂停
    var update_adg_status = function(mode, adgroup_id){
        ajax.ajax('update_adg_status', {
            'mode':mode,
            'mnt_type':condition.mnt_type,
            'campaign_id':condition.camp_id,
            'adg_id_list':'[' + adgroup_id + ']'
        }, function(result){
            lightMsg.show({body:'操作成功！'});
            if(mode == "start"){
                $('#goods_table tr[adgroup_id=' + adgroup_id + '] .lbl_online').html('推广中');
                $('#goods_table tr[adgroup_id=' + adgroup_id + '] .switch_status').html('暂停');
                $('#goods_table tr[adgroup_id=' + adgroup_id + '] .sort_online').text(1);
                $('#goods_table tr[adgroup_id=' + adgroup_id + ']').removeClass('gray');
            }else if(mode == "stop"){
                $('#goods_table tr[adgroup_id=' + adgroup_id + '] .lbl_online').html('已暂停');
                $('#goods_table tr[adgroup_id=' + adgroup_id + '] .switch_status').html('开启');
                $('#goods_table tr[adgroup_id=' + adgroup_id + '] .sort_online').text(0);
                $('#goods_table tr[adgroup_id=' + adgroup_id + ']').addClass('gray');
            }else if(mode == "del"){
                var tr_obj = $('#goods_table tr[adgroup_id=' + adgroup_id + ']');
                if (tr_obj.data('subdivide')){
                    tr_obj.data('subdivide').addClass('hidden');
                    delete(tr_obj.data().subdivide);
                    tr_obj.nextAll('.hover_non_color').remove();
                }
                tr_obj.remove();
                var adg_count = parseInt($('.adgroup_count').html()) - 1;
                if (adg_count <= 0)
                    adg_count = 0;
                $('.adgroup_count').html(adg_count);
                select_tool.refreshSelected();
            }
        });
    }

    //获取计划列表数据
    var getGoodsList=function(){
        loading.show('数据加载中，请稍候。。。');
        ajax.ajax('get_adgroup_list', {
                'campaign_id':condition.camp_id,
                'page_size':condition.PAGE_SIZE,
                'page_no':condition.PAGE_NO,
                'last_day':condition.last_day,
                'start_date':condition.start_date,
                'end_date':condition.end_date,
                'sSearch':condition.search_word,
                'search_type':condition.search_type,
                'opt_type':condition.opt_type,
                'auto_hide':0,
                'page_type':condition.page_type,
                'status_type':condition.status_type,
                'offline_type':$('#offline_type').val(),
                'is_follow': condition.is_follow,
                'sort':condition.sort
                }, get_adgroup_list_callback);
    }

    //获取计划列表数据的回调
    var get_adgroup_list_callback = function (data){
        page_count = data.page_info.page_count;
        var html, tpl=__inline("goods_list.html");
        html = template.compile(tpl)({list:data.adg_list,list_type:condition.list_type});

        if(data.mnt_info['is_mnt']){
            $('.mnt_num').text(data.mnt_info['mnt_num']);
            $('.new_num').text(parseInt($('#mnt_max_num').val())-data.mnt_info['mnt_num']);
        }

        if(goods_table){
            goods_table.fnClearTable();
            goods_table.fnDestroy();
        }
        $('#goods_table tbody').html(html);
        loading.hide();
        var page_info = {
            page_row: data.page_info.page,
            page_list: data.page_info.page_xrange,
            page_count: data.page_info.page_count,
            page_size: 50
        }
        page_tool.init(page_info, getPageData);

        //loadPageBar(data.page_info.record_count,data.page_info.page);

        $('.adgroup_count').html(data.page_info.record_count);

        select_tool.fixPosition();

        if(data.adg_list.length>0){
            page_tool.show();
            select_tool.show();
        }else{
            page_tool.hide();
            select_tool.hide();
        }

        select_tool.setSelected(0);
        init_table();

        $('[data-toggle="tooltip"]').tooltip({html:true});
    }

    //加载分页条
    var loadPageBar = function(recordCount,page){

        var startPage = 1,endPage = 1;
        var pageXrange = [],
            pageCount = Math.ceil(recordCount / condition.PAGE_SIZE);

        var HALF_SHOW_PAGE = 3; // 分页显示数量的一半
        var SHOW_PAGE = HALF_SHOW_PAGE * 2 + 1;

        if(pageCount <= SHOW_PAGE || page <= HALF_SHOW_PAGE + 1){
            if(pageCount <= SHOW_PAGE){
                endPage = pageCount+1;
            }else{
                endPage = SHOW_PAGE + 1;
            }
        }else{
            startPage = page - HALF_SHOW_PAGE;
            if(HALF_SHOW_PAGE > pageCount){
                endPage = pageCount;
            }else{
               endPage = page + HALF_SHOW_PAGE + 1
            }
        }

        if((page + 3) > pageCount && pageCount > SHOW_PAGE){
            startPage = pageCount - SHOW_PAGE + 1;
            endPage = pageCount+1;
        }

        for (var i = startPage; i < endPage; i++) {
            pageXrange.push(i);
        }
        require(['widget/pageBar/pageBar'], function(pageBar) {
            var dom = pageBar.show({
                data: {
                    record_count: recordCount,
                    page_xrange: pageXrange,
                    page_count: pageCount,
                    page: page
                },
                onChange: function(_page) {
                    getPageData(_page);
                }
            });

            $('.page-tool').html(dom);
        });
    }

    //查询分页数据
    var getPageData = function(pIndex){
        condition.PAGE_NO = pIndex
        getGoodsList();
    };

    //初始化表格
    var init_table = function(){
        goods_table = $('#goods_table').dataTable({
            "bRetrieve": true, //允许重新初始化表格
            "bPaginate": false,
            "aaSorting": [[sort_dict[sort_column],sort_desc]],
            "bFilter": false,
            "bInfo": false,
            "bAutoWidth":false,//禁止自动计算宽度
            "language": {"emptyTable": "没有数据"},
            "aoColumns": [
                {"bSortable": false},
                {"bSortable": false},
                {"bSortable": false},
                {"bSortable": true,
                 "sType":'custom',
                 "sSortDataType":"custom-text"
                },
                {"bSortable": true,
                 "sType":'custom',
                 "sSortDataType":"custom-text"
                },
                {"bSortable": true,
                 "sType":'custom',
                 "sSortDataType":"custom-text"
                },
                {"bSortable": true,
                 "sType":'custom',
                 "sSortDataType":"custom-text"
                },
                {"bSortable": true,
                 "sType":'custom',
                 "sSortDataType":"custom-text"
                },
                {"bSortable": true,
                 "sType":'custom',
                 "sSortDataType":"custom-text"
                },
                {"bSortable": true,
                 "sType":'custom',
                 "sSortDataType":"custom-text"
                },
                {"bSortable": true,
                 "sType":'custom',
                 "sSortDataType":"custom-text"
                },
                {"bSortable": true,
                 "sType":'custom',
                 "sSortDataType":"custom-text"
                },
                {"bSortable": true,
                 "sType":'custom',
                 "sSortDataType":"custom-text"
                },
                {"bSortable": true,
                 "sType":'custom',
                 "sSortDataType":"custom-text"
                },
                {"bSortable": false},
                {"bSortable": false},
                {"bSortable": false}
            ],
            "fnDrawCallback": function(oSettings) {
                delete($('#show_subdivide_all').data().is_showing);
                $.map($('#goods_table .show_subdivide'),function(obj){
                        delete($(obj).data().is_showing);
                });
            },
            "initComplete": function () {
                /**
                 * 结合th的点击事件，单页时前端排序，多页时，后端排序
                 */
                $.fn.dataTableExt.afnSortData['custom-text'] = function(oSettings, iColumn) {
                    return $.map(oSettings.oApi._fnGetTrNodes(oSettings), function(tr, i) {
                        var td = oSettings.oApi._fnGetTdNodes(oSettings, i)[iColumn],
                        val=Number($(td).find('span:first').text());
                        if (page_count>1) {
                            return 0;
                        } else {
                            return val;
                        }
                    });
                };
            }
        });

        new FixedHeader(goods_table);
    }

    var filterData=function(start_date, end_date,campaign_id,search_word,opt_type,status_type,is_follow){
        condition.camp_id = campaign_id;
        condition.start_date = start_date;
        condition.end_date = end_date;
        condition.search_word = search_word;
        condition.PAGE_NO = 1;
        condition.opt_type = opt_type;
        condition.status_type = status_type;
        condition.is_follow = is_follow;
        getGoodsList();
    }

    //更新托管宝贝数
    var update_mnt_num = function(old_opt_type,new_opt_type){
        var mnt_num = parseInt($('.mnt_num').text());
        var new_num = parseInt($('.new_num').text());

        //取消托管时 mnt_num-1，new_num+1
        if(old_opt_type&&!new_opt_type){
            $('.mnt_num').text(mnt_num-1);
            $('.new_num').text(new_num+1);
        }

        //新加托管时 mnt_num+1，new_num-1
        if(!old_opt_type&&new_opt_type){
            $('.mnt_num').text(mnt_num+1);
            $('.new_num').text(new_num-1);
        }

    }
    return {
        init:init_dom,
        getPageData:getPageData,
        filterData:filterData
    }
});
