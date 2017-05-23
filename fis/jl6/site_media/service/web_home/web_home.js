define(['require','moment','../common/common','../campaign_list/campaign_list',
        'top_banner','mr_window','mc_window','right_notice','../common/poster_store','jl6/site_media/widget/alert/alert',
        'jl6/site_media/widget/confirm/confirm','jl6/site_media/widget/lightMsg/lightMsg','jl6/site_media/widget/ajax/ajax',
        'jl6/site_media/widget/loading/loading','template','../report_detail/report_detail'],
    function(require,moment,common,campaign_list,top_banner,mr_window,
              mc_window,right_notice,ad_store,alert,confirm,lightMsg,ajax,loading,template,report_detail) {
    "use strict"

    /**
     * 获取账户报表数据
     * @param start_date
     * @param end_date
     * @param rt_flag
     * @param update
     */
    var getAccountRpt=function(start_date, end_date){
	    loading.show('数据加载中，请稍候...');
        ajax.ajax('get_account',{'start_date':start_date, 'end_date':end_date},function(data){
            var tpl, html, wrap;
            tpl = __inline('sum_report.html');
            wrap = $('.total_rpt');
            loading.hide();
            if (data.chart_data) {
                common.chart.draw('account_char',data.chart_data.category_list, data.chart_data.series_cfg_list);
            };
            html = template.compile(tpl)(data.account_data_dict);
            wrap.html(html);
            $('[data-toggle="tooltip"]').tooltip({html: true});
        });
    };

    /**
     * 获取账户实时数据
     * @returns {boolean}
     */
    var getAccountRtData = function(update_cache){
         ajax.ajax('get_account_rtdata',{'update_cache':update_cache},function(data){
            var tpl, html, wrap;
            tpl = __inline('rt_report.html');
            wrap = $('.rt_rpt');
            html = template.compile(tpl)(data.account_data_dict);
            wrap.html(html);
            $('[data-toggle="tooltip"]').tooltip({html: true});
        });
    };

    var init=function(){
        //第一次进入时，发送请求当天实时的账户数据
	    getAccountRtData();

        setInterval(function () {
	        getAccountRtData(1);
        }, 5*60*1000);

        //如果用户点击小时钟，在立即刷新实时数据
        $('.rt_rpt').on('click','.update_cache',function(){
            getAccountRtData(1);
        });

        //第一次进入时，发送请求昨日的账户数据
        var start_date = moment().subtract(7, 'days').format('YYYY-MM-DD'),
            end_date = moment().subtract(1, 'days').format('YYYY-MM-DD');
        getAccountRpt(start_date, end_date);

        //账户明细弹出层
        $('#account_detail').on('click',function(){
            report_detail.show('账户明细：'+$('#a_nick').text(), 'account', $('#shop_id').val());
            //$("#account_detial_modal").modal();
        });

        //账户选择天数
        $('#select_account_days').on('change',function(e,v){
            var start_date, end_date;
            start_date = moment($(this).daterangepicker('getRange').start).format('YYYY-MM-DD');
            end_date = moment($(this).daterangepicker('getRange').end).format('YYYY-MM-DD');
            getAccountRpt(start_date, end_date);

        });

        //计划报表选择天数
        $('#select_campaign_days').on('change',function(e,v){
            var start_date, end_date;
            start_date = moment($(this).daterangepicker('getRange').start).format('YYYY-MM-DD');
            end_date = moment($(this).daterangepicker('getRange').end).format('YYYY-MM-DD');
            campaign_list.setQueryDate(start_date,end_date);
            campaign_list.getCampaignList(start_date,end_date);
        });

        //主区横条的浏览及点击事件
        var main_ad_event;
        var ad_id = $('#main_banner_content').attr('ad_id');
        var ad_frequency = $('#main_banner_content').attr('ad_frequency');
        //判断此次访问是否需要显示该广告
        if(ad_store.getStoreAd(ad_id,ad_frequency)){
            return false;
        }else{
            $("#show_main_banner").show();
        }

        if(ad_id){
            main_ad_event = require('../common/main_poster_event');
            //如果有主区横条广告，则要将该广告的浏览事件加1
            main_ad_event.addViewTimes(ad_id);

            //广告显示后，存在前端，下次刷新页面是调用
            var main_banner_ad = {'ad_frequency':$('#main_banner_content').attr('ad_frequency'),'last_show_time':new Date()};
            ad_store.setStoreAd(ad_id,main_banner_ad);
        }

        //点击主区广告后，需要将广告的点击事件加1
        $('#main_banner_content').click(function(){
            main_ad_event.addClickTimes(ad_id);
        });

        $("#hide_main_banner").click(function(){
            $("#show_main_banner").animate({height:0,margin:0,padding:0},300,function(){
                $("#show_main_banner").remove();
            });
        });

        //显示所有提示
        $('[data-toggle="tooltip"]').tooltip();

        //立即充值
        $('#btn_recharge').on('click',function(){
            common.goto_ztc(6,'','','');
        });

        //签到送积分
        $('#sign_point').on('click',function(){
            if ($('#sign_point').hasClass('disabled')) {
                lightMsg.show({
                                body:'今天已经签过了，明天再来吧！'
                            });
                return false;
            }

            $('#sign_point').addClass('disabled');

            ajax.ajax('sign_point',{},function(data){
                $('.point_count').each(function(){
                    var point=Number($(this).text());
                    $(this).text(point+data.data.point);
                });
                $('#sign_point').html('已&thinsp; 签&thinsp; 到').addClass('disabled');
                lightMsg.show({
                    title:'签到成功',
                    body:'赠送积分'+data.data.point+',连续签到'+data.data.attendance_day+'天'
                });
            });
        });

        //新建计划
        $('.js_create_camp').click(function(){
            common.goto_ztc(1,'','','');
        });
    }

    return {
        init:function () {
            //顶部通栏事件
            init();
            report_detail.init();
            campaign_list.init();
            top_banner.init();
            mr_window.init();
            mc_window.init();
            right_notice.init();
            //lottery.init();
        }
    }
});
