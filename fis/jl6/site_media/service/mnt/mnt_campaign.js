/**
 * Created by Administrator on 2015/9/21.
 */
define(['require','json','moment','../common/common','../goods_list/goods_table',
'jl6/site_media/widget/ajax/ajax','jl6/site_media/widget/loading/loading',
'jl6/site_media/widget/lightMsg/lightMsg','jl6/site_media/widget/alert/alert',
'edit_camp_price','jl6/site_media/widget/confirm/confirm','../add_item_box/add_item_box',
'template',"jl6/site_media/widget/tagEditor/tagEditor",'../report_detail/report_detail','jslider'],
function(require,json,moment,common,goods_table,ajax,loading,lightMsg,alert,edit_camp_price,confirm,add_item_box,template,tagEditor,report_detail) {
    "use strict"

    var camp_id = $('#campaign_id').val(),
        start_date = moment().subtract(7,'days').format('YYYY-MM-DD'),
        end_date = moment().subtract(1,'days').format('YYYY-MM-DD'),
        mnt_index = parseInt($('#mnt_index').val()),
        mnt_type = parseInt($('#mnt_type').val()),
        mnt_opter = parseInt($('#mnt_opter').val())? parseInt($('#mnt_opter').val()): 0,
        max_price_pc =  parseFloat($('#max_price_pc').text()),
        max_price_yd =  parseFloat($('#max_price_yd').text()),
        cat_cpc,
        opt_type = -1,
        status_type = '',
        is_follow = -1;

    var load_add_box = false;

    var init = function(){

        //获取计划实时报表数据
        getRtRpt(0);
        //每隔5分钟，自动获取一次
        setInterval(function () {
	        getRtRpt(0);
        }, 5*60*1000);
        //如果用户点击小时钟，在立即刷新实时数据
        $('.rt_rpt').on('click','.update_cache',function(){
            getRtRpt(1);
        });

        get_base_rpt(start_date,end_date);

        goods_table.init(mnt_type,start_date,end_date,camp_id);

        //选择日期 重新加载数据
        $('#select_days').on('change',function(){
            start_date = moment($(this).daterangepicker('getRange').start).format('YYYY-MM-DD');
            end_date = moment($(this).daterangepicker('getRange').end).format('YYYY-MM-DD');
            get_base_rpt(start_date,end_date);
            filterData();
        });

        //滑杆 调价力度
        var old_bid_factor = parseFloat($('#mnt_bid_factor').val());
        $('.jslider-box input').slider({
            from: 0,
            to: 100,
            skin: 'power',
            onstatechange: function(value){
                setBigFactor(value);
            },
            callback: function(value) {
                confirm.show({
                    'body':'确定要修改宝贝推广意向吗？',
                    okHide:function(){
                       if(value!=old_bid_factor){
                           ajax.ajax('change_mntcfg_type',
                                    {'campaign_id':camp_id,
                                     'mnt_bid_factor': value,
                                     'mnt_type': mnt_type},
                                     function(result){
                                         $('#mnt_bid_factor').val(value);
                                         lightMsg.show({body:'设置宝贝推广意向成功！'});
                                     },null,{'url':'/mnt/ajax/'});
                        }
                    },
                    cancleHide:function(){
                        //还原滚动条
                        $('.jslider-box input').slider('value',old_bid_factor);
                        setBigFactor(old_bid_factor);
                    }
                });
            }
        });

        //搜索栏
        $('#search_btn').click(function (){
            filterData();
        });

        $('#search_val').keyup(function(e){
            if (e.keyCode==13) {
                filterData();
            }
        });

        //设置投放平台
        $('.edit_platform').on('click',function(){
            loading.show('正在获取计划投放平台');
            ajax.ajax('get_camp_platform',{'camp_id':camp_id},function(data){
                loading.hide();
                var platform = data.platform,
                    can_set_nonsearch = data.can_set_nonsearch;
                if (platform) {
                    require(['../edit_camp_platform/edit_camp_platform'],function(modal){
                        modal.show({
                            pc_insite_search: platform.pc_insite_search,
                            pc_outsite_nonsearch: platform.pc_outsite_nonsearch,
                            pc_insite_nonsearch: platform.pc_insite_nonsearch,
                            outside_discount: platform.outside_discount,
                            yd_outsite: platform.yd_outsite,
                            pc_outsite_search: platform.pc_outsite_search,
                            mobile_discount: platform.mobile_discount,
                            yd_insite: platform.yd_insite,
                            can_set_nonsearch: can_set_nonsearch,
                            onChange:function(new_data){
                                loading.show('正在设置计划投放平台');
                                ajax.ajax('update_camp_platform',{ 'camp_id':camp_id,'platform_dict':$.toJSON(new_data)},function(result){
                                    loading.hide();
                                    if (result.is_success) {
                                        lightMsg.show({'body':'修改计划投放平台成功！'})
                                    } else {
                                        alert.show('修改计划投放平台失败，请联系客服！');
                                    }
                                },null,{'url':'/web/ajax/'});
                            }
                        });
                    });
                } else {
                    alert.show('淘宝接口不稳定，请稍后再试');
                }
            },null,{'url':'/web/ajax/'});
        });

        //设置分时折扣
        $('.edit_schedule').on('click',function(){
            loading.show('正在获取分时折扣');
            ajax.ajax('get_camp_schedule',{'camp_id':camp_id},function(data){
                loading.hide();
                if (data.schedule_str) {
                    require(['../edit_camp_schedule/edit_camp_schedule'],function(modal) {
                        modal.show({
                            schedules: data.schedule_str,
                            onChange: function (new_data) {
                                ajax.ajax('update_camp_schedule',{'camp_id':camp_id, 'schedule_str':new_data},function(result){
                                    loading.hide();
                                    if (result.errMsg == "") {
                                        lightMsg.show({'body':'修改计划投放时间成功!'})
                                    } else {
                                        alert.show('修改计划投放时间失败！');
                                    }
                                },null,{'url':'/web/ajax/'})
                            }
                        });
                    });
                } else {
                    alert.show('淘宝接口不稳定，请稍后再试');
                }
            },null,{'url':'/web/ajax/'});
        });

        //设置投放区域
        $('.edit_area').on('click',function(){

            var onChange = function(new_data,area_names){
                ajax.ajax('update_camp_area',{'camp_id':camp_id, 'area_ids':new_data,'area_names':area_names},function(result){
                    loading.hide();
                    if (result.is_success) {
                        var area_ids = $('.edit_area').data('area_ids',new_data);
                        lightMsg.show({'body':'修改计划投放地域成功！'})
                    } else {
                        alert.show('修改计划投放地域失败！');
                    }
                },null,{'url':'/web/ajax/'})
            };
            require(['../edit_camp_area/edit_camp_area'],function(modal){
                if($('.edit_area').data('area_ids')){
                    var area_ids = $('.edit_area').data('area_ids');
                    modal.show({area_ids: area_ids,onChange:onChange});
                }else{
                    loading.show('正在获取投放地域信息,请稍候...');
                    ajax.ajax('get_camp_area',{'camp_id':camp_id},function(data){
                        loading.hide();
                        if (data.area) {
                            $('.edit_area').data({'is_lock': 1, 'area_ids': data.area});
                            modal.show({area_ids: data.area,onChange:onChange});
                        } else {
                            alert.show('淘宝接口不稳定，请稍后再试');
                        }
                    },null,{'url':'/web/ajax/'});
                }

            });

        });

        //查看报表明细
        report_detail.init();
        $('#campaign_detail').click(function(){
            report_detail.show('计划明细：'+$('#campaign_title').text(), 'campaign', $('#shop_id').val(), $('#campaign_id').val());
        });

        //重点算法设置
  /*      $(document).on('change', 'input[name="opt_type"]', function () {
            var mnt_bid_factor = $(this).val();
            ajax.ajax('change_mntcfg_type',
            {'campaign_id':camp_id, 'mnt_bid_factor': mnt_bid_factor, 'mnt_type': mnt_type},
            function(result){
                if(result.errMsg == ''){
                    lightMsg.show({'body':'已经切换到【'+ result.descr + '】'});
                }
            },null,{'url':'/mnt/ajax/'});
        });*/

        //修改限价
        $('.edit_camp_price').click(function(){
            var type = $(this).attr('type');
            var obj = $(this);
            if(type=='budget'){
                var old_is_smooth = $(this).data("smooth");
                var old_budget = $(this).data("budget");
                require(["../edit_camp_budget/edit_camp_budget"],function(modal){
                    modal.show({
                        campaign_id:camp_id,
                        budget:old_budget,
                        is_smooth:old_is_smooth,
                        mnt_type:mnt_type,
                        onChange:function(budget,is_smooth){
                            if(budget == old_budget && is_smooth == old_is_smooth) {
                                return;
                            }
                            var use_smooth;
                            if(is_smooth=='0'){
                                use_smooth='false';
                            }else{
                                use_smooth='true';
                            }

                            ajax.ajax('modify_camp_budget',{'camp_id':camp_id,'use_smooth':use_smooth,'budget':budget},function(data){
                                //title_warp.text(newTitle);
                                if(data.errMsg){
                                    alert.show(data.errMsg);
                                    return;
                                }

                                if(budget<20000000){
                                    $('#budget').text(budget+'元');
                                }else{
                                    $('#budget').text('不限');
                                }
                                obj.data('budget',budget);
                                obj.data('smooth',is_smooth);
                                lightMsg.show({
                                    body:'修改日限额成功！'
                                });
                            });
                        }
                    });
                });
            }else if(type=='max_price'){
                var title = '关键词最高限价',
                min_price = 0.20,
                max_price = 99.99,
                price_desc;
                if(mnt_type==1||mnt_type==3){
                    price_desc = '最低'+min_price+'元，推荐在'+parseFloat(1.5*cat_cpc).toFixed(2)+'~'+parseFloat(2.5*cat_cpc).toFixed(2)+'元之间';
                }else{
                    price_desc = '最低'+min_price+'元，推荐在'+parseFloat(2.0*cat_cpc).toFixed(2)+'~'+parseFloat(3.0*cat_cpc).toFixed(2)+'元之间';
                }
                var default_price_pc = $(this).attr('max_price_pc');
                var default_price_yd = $(this).attr('max_price_yd');

                edit_camp_price.show({
                    title:title,
                    price_desc:price_desc,
                    max_price:max_price,
                    min_price:min_price,
                    default_price_pc:default_price_pc,
                    default_price_yd:default_price_yd,
                    type:type,
                    onChange:function(newPricePc, newPriceYd){
                        var submit_data = $.toJSON({'max_price':newPricePc, 'mobile_max_price': newPriceYd});
                        ajax.ajax('update_cfg', {'campaign_id':camp_id, 'submit_data':submit_data, 'mnt_type':mnt_type}, function(result){
                            $('.edit_camp_price[type=max_price]').attr('max_price_pc',newPricePc).attr('max_price_yd',newPriceYd);
                            $('#max_price_pc').text(newPricePc);
                            $('#max_price_yd').text(newPriceYd);
                            lightMsg.show({body:'设置关键词限价成功！'});
                        }, null, {'url':'/mnt/ajax/'});
                      }
                });
            }
        });

        //计划推广状态 开启 关闭
        $(document).on('click','.online_status',function(){
            var mode = parseInt($(this).attr('mode')),
                camp_id_arr = [camp_id],
                mode_str = mode? '启动推广': '暂停推广';
            confirm.show({
                body:'确定'+mode_str+'当前计划吗？',
                okHide:function(){
                ajax.ajax('update_camps_status',{'camp_id_list':camp_id_arr,'mode':mode},function(data){
                        if (data.errMsg == '') {
                            if(mode == 0){
                                $('.lbl_online_status').text('已暂停');
                                $('.online_status').text('开启').attr('mode',1);
                                $('.quick_oper').addClass('hide');
                            }else{
                                $('.lbl_online_status').text('推广中');
                                $('.online_status').text('暂停').attr('mode',0);
                                $('.quick_oper').removeClass('hide');
                            }
                            lightMsg.show({body: mode_str + '计划成功！'});

                        }else{
                            alert.show('修改失败：淘宝接口不稳定，请稍后再试');
                        }
                    }, null, {'url':'/web/ajax/'});
                }
            });
        });

        //MNT托管状态 开启 关闭
        $(document).on('click','.mnt_status',function(){
            var title = '确定“取消托管”该计划吗？';
            var mnt_days = Number($(this).attr('mnt_days'));
            if(mnt_days>=-10&&mnt_days<0){
                title = "该计划只托管了"+Math.abs(mnt_days)+'天，'+title;
            }else if(mnt_days==0){
                title = "该计划托管不满1天，"+title;
            }
            var body_str="<div class='lh25'>1、效果需要一定周期培养，建议不要短期托管或频繁更换策略</div><div class='lh25'>2、系统会停止优化您的宝贝，但不会改变计划和宝贝的推广状态</div><div class='lh25'>3、取消后可以重新开启托管，但需要重新设置计划、宝贝、策略</div>";
            confirm.show({
                title: title,
                body:body_str,
                cancleStr: "不取消托管",
                okStr: "取消托管",
                okHide:function(){
                    ajax.ajax('mnt_campaign_setter',{'campaign_id':camp_id,'set_flag':0,'mnt_type':mnt_type},function(data){
                        window.location.href='/mnt/mnt_campaign/'+camp_id;
                    },null,{url:'/mnt/ajax/'});
                }
            });
        });

        //宝贝实时优化
        $(document).on('click','.mnt_rt',function(){
            var obj = $(this);
            var status = $(this).data('mntrt');
            if(status=="0"){
                status = 1;
            }else{
                status = 0;
            }
            confirm.show({
                body:'确定'+obj.text()+'实时优化吗？',
                okHide:function(){
                    ajax.ajax('update_rt_engine_status',{campaign_id:camp_id,status:status,mnt_type:mnt_type},function(data){
                        lightMsg.show({body: obj.text()+'实时优化成功！'});
                        obj.data('mntrt',status);
                        if(status){
                            $('.mnt_rt').text("关闭");
                            $('.lbl_mnt_rt').text("已开启");
                        }else{
                            $('.mnt_rt').text("开启");
                            $('.lbl_mnt_rt').text("已关闭");
                        }
                    },null,{'url':'/mnt/ajax/'});
                }
            });

        });

        //加大投入，减少投入
        $(document).on('click','.quick_oper_long',function(){
            if($(this).hasClass('disabled')){
                return;
            }
            var stgy = parseInt($(this).attr('stgy')),
            msg = '系统会定期自动改价换词，您确定现在就要人工干预吗？';
            confirm.show({'body':msg,'okHide':function(){
                ajax.ajax('quick_oper',
                {'campaign_id':camp_id, 'mnt_type':mnt_type, 'stgy':stgy},
                function(data){
                    $('.sign-oper').attr('data-original-title','今日已调整过，每日只能调整一次');
                    $('.quick_oper_long').addClass('disabled').addClass('btn-default');;
                    $('.quick_oper_long').removeAttr('stgy');
                    $('.quick_oper_long').removeClass('quick_oper_long').removeClass('btn-primary');
                },null,{'url':'/mnt/ajax/'});
            }});
        });
        //添加新宝贝
        $('.add_adgroup').click(function(){

            if(!load_add_box){
                var options = {
                    mnt_type:mnt_type,
                    adg_counts:Number($('.new_num').text()) || 0,
                    cur_counts:0
                }
                if(mnt_type!='0'){
                    if(options.adg_counts==0){
                        alert.show('已达到托管上限，若要继续托管，请先删除一些已托管宝贝！');
                        return false;
                    }
                }

                var strategy = {
                    max_price_pc:max_price_pc.toFixed(2),
                    max_price_yd:max_price_yd.toFixed(2),
                    mnt_opt_type:1
                }
                add_item_box.setStrategy(strategy);
                add_item_box.init(options);

                var params = {
                        campaign_id:camp_id,
                        page_no:1,
                        page_size:50,
                        sSearch:'',
                        exclude_existed:1,
                        auto_hide:0
                    };
                add_item_box.loadItemList(params);
                if(mnt_type){
                    add_item_box.loadAdgList(params);
                }
                load_add_box = true;

            }

            $(document.body).css("overflow","hidden");
            window.scrollTo(0,0)
            $('.add_adg_box').show();
            $('.add_adg_box').css('height',$(window).height()-88);
            $('.add_adg_box').animate({top:'88px'},500);
        });

        //取消添加新宝贝
        $('.cancle_add_adgroup').click(function(){

            $('.add_adg_box').animate({top:$(window).height()},500,function(){
                $('.add_adg_box').hide();
                $(document.body).css("overflow","auto");
            });
        });

        //提交新增的宝贝
        $('.submit_adgroup').click(function(){
            submit_item();
        });

        $(window).resize(function(){
            $('.add_adg_box').css('height',$(window).height()-88);
        });


        $('#to_mnt_main').click(function(){
            window.location.href = '/mnt/mnt_campaign/'+camp_id;
        });

        $("[data-toggle='tooltip']").tooltip({html: true});

        //获取行业均价
        ajax.ajax('get_recommend_price',{campaign_id:camp_id,mnt_type:mnt_type},function(data){
            cat_cpc = data.cat_cpc;
        });

        //根据推广状态查询宝贝
        $('#search_status_type').on('change',function(e,value){
            status_type = value;
            filterData();
        });

        //根据优化状态查询宝贝
        $('#search_opt_type').on('change',function(e,value){
            opt_type = value;
            filterData();
        });

        //根据关注状态查询宝贝
        $('#search_follow_type').on('change',function(e,value){
            is_follow = value;
            filterData();
        });

        setBigFactor(parseInt($('#mnt_bid_factor').val()));
    };

    //查询列表
    var filterData = function(){
        var search_word = $('#search_val').val();
        goods_table.filterData(start_date,end_date,camp_id,search_word,opt_type,status_type, is_follow);
    };

    //获取基础报表数据
    var get_base_rpt = function(start_date,end_date){
        ajax.ajax('get_base_rpt',
        {'campaign_id':camp_id,'rpt_days':15,'start_date':start_date,'end_date':end_date},
        function(result){
            if(result.errMsg == ""){
                var html,tpl= __inline('sum_report.html');
                html = template.compile(tpl)(result.result_dict);
                $('.total_rpt').html(html);
                $('[data-toggle="tooltip"]').tooltip({html: true});
            }
        },null,{'url':'/mnt/ajax/'});
    };

    /**
     * 获取计划实时数据报表
     */
    var getRtRpt = function(update){
        ajax.ajax('get_rt_rpt',{'campaign_id':camp_id,'update_cache':update},
                function(data){
                    if(data.errMsg == ""){
                        var html,tpl= __inline('rt_report.html');
                        html = template.compile(tpl)(data.result);
                        $('.rt_rpt').html(html);
                        $('[data-toggle="tooltip"]').tooltip({html: true});
                    }
                });
    }

    //提交新宝贝
    var submit_item = function(){
        if(!add_item_box.getSelectCounts()){
            alert.show('请选择托管宝贝！');
            return false;
        }
        var has_error = false;
        $('input[name="adg_title"]').each(function(){
            if($.trim($(this).val()).length==0||$(this).val()=='正在获取...'){
                alert.show('创意标题不能为空!');
                has_error = true;
                return;
            }
            if(parseInt($(this).attr('char_delta'))<0){
                alert.show('创意标题的长度不能超过20个汉字!');
                has_error = true;
                return;
            }
        });

        if(has_error){
            return false;
        }

        $('.opt_btn').addClass('hide');
        loading.show('数据提交中，请稍候...');
        update_mnt_adg();
    };

    var setBigFactor = function(value){
        var big_factor_value = Math.abs(value-50)
        if(value<50){
            $('#big_factor_name').text('偏向ROI');
            $('#big_factor_value').removeClass('hide');
        }else if(value==50){
            $('#big_factor_name').text('均衡模式');
            $('#big_factor_value').addClass('hide');
            $('#big_factor_value').text('0%')
        }else{
            $('#big_factor_name').text('偏向流量');
            $('#big_factor_value').removeClass('hide');
        }
        $('#big_factor_value').text((big_factor_value/50*100).toFixed(0)+'%');
    }

    //提交计划内的宝贝
    var mnt_count = 0;
    var update_mnt_adg = function(){
        var mnt_adg_info = add_item_box.getMntAdgInfo();
        ajax.ajax('update_mnt_adg',
                    {'mnt_adg_dict':JSON.stringify(mnt_adg_info.mnt_adg_dict),
                     'update_creative_dict': JSON.stringify(mnt_adg_info.update_creative_dict),
                     'new_creative_list': JSON.stringify(mnt_adg_info.new_creative_list),
                     'camp_id':camp_id,
                     'mnt_type':mnt_type,
                     'flag':2
                    },function(data){
                        //如果有提交异常的宝贝，需提示错误信息
                        submit_new_item();
                        mnt_count = parseInt(data.success_count);
                    },null,{'url':'/mnt/ajax/'})
    };

    //提交计划外的宝贝
    var submit_new_item = function(){
        var new_item_dict = add_item_box.getNewItemDict();
        ajax.ajax('add_new_item',
                { 'new_item_dict':JSON.stringify(new_item_dict),
                  'camp_id':camp_id,
                  'mnt_type':mnt_type},
                function(data){
                    loading.hide();
                    $('.add_item_box').addClass('hide');
                    $('.result_box').removeClass('hide');
                    if(data.failed_count){
                        var html,tpl=__inline("../add_item_box/error_adg_list.html");
                            html = template.compile(tpl)({error_list:data.failed_item_dict});
                        $('.error_list').html(html);
                        $('#error_msg').removeClass('hide');
                    }
                    $('#item_success_count').text(data.success_count+mnt_count);
                    $('#item_failed_count').text(data.failed_count);
                    $('.commit_result').fadeIn(200);
                },null,{'url':'/mnt/ajax/'});
    };

    return {
        init:init
    }
});
