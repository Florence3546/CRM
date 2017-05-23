define(['require','template','moment','../common/common','jl6/site_media/widget/dtrPicker/dtrPicker', 'jl6/site_media/widget/ajax/ajax','jl6/site_media/widget/loading/loading','jl6/site_media/widget/alert/alert'],
    function(require, template, moment, common, dtrPicker, ajax, loading, alert) {
    "use strict"

    var init_subdivide_event = function() {

        $('#show_rpt_subdivide_all').off('click');
        $('#show_rpt_subdivide_all').on('click',function(){
            var is_showing = $(this).data('is_showing');
            if(is_showing){
                $(this).parents('table:first').find('.show_subdivide.in').trigger('click');
                delete($(this).data().is_showing);
            }else{
                $(this).parents('table:first').find('.show_subdivide:not(.in)').trigger('click');
                $(this).data('is_showing', 1);
            }
            adjust_th_width();
        });

    };

    var getReportDetail = function (start_date, end_date, type, shop_id, campaign_id, adgroup_id, creative_id, keyword_id) {
        loading.show('数据加载中，请稍候...');
        ajax.ajax(
            'get_rpt_detail',
            {
                'start_date':start_date,
                'end_date':end_date,
                'type':type,
                'shop_id':shop_id,
                'campaign_id':campaign_id,
                'adgroup_id':adgroup_id,
                'creative_id':creative_id,
                'keyword_id':keyword_id,
                'source':$('#data_source button.active').length?$('#data_source button.active').data().source:'all'
            },
            function (data) {
                loading.hide();
                var tpl, html;
                switch (data.data.tpl_type) {
                    case 0:
                        tpl = __inline('modal-body0.html');
                        break;
                    case 1:
                        tpl = __inline('modal-body1.html');
                        break;
                }
                html = template.compile(tpl)({'rpt_list':data.data.rpt_list});
                $('#table_report_detail').remove();
                $('#modal_report_detail .modal-body').html(html);
                // $("#modal_report_detail").data('category_list', data.data.category_list);
                // $("#modal_report_detail").data('series_cfg_list', data.data.series_cfg_list);
                common.chart.draw('chart_report_detail', data.data.category_list, data.data.series_cfg_list);
                $('#table_report_detail [data-toggle=tooltip]').tooltip();
                $('#table_report_detail tr.fixed_tr>th').each(function (i) {
                    $(this).width($('#table_report_detail tr.inner_tr>th:eq('+i+')').width());
                });
                init_subdivide_event();
            }
        );
    }

    var show = function (title, type, shop_id, campaign_id, adgroup_id, creative_id, keyword_id) {
        var start_date, end_date;
        start_date = moment().subtract(7, 'days').format('YYYY-MM-DD');
        end_date = moment().subtract(1, 'days').format('YYYY-MM-DD');
        shop_id = shop_id || '';
        campaign_id = campaign_id || '';
        adgroup_id = adgroup_id || '';
        creative_id = creative_id || '';
        keyword_id = keyword_id || '';
        $('#modal_report_detail .modal-title').html(title);
        $('#modal_report_detail').attr({type:type, shop_id:shop_id, campaign_id:campaign_id, adgroup_id:adgroup_id, creative_id:creative_id, keyword_id:keyword_id}).modal();
        $('#report_detail_days').daterangepicker('setRange', {start:moment(start_date).toDate(), end:moment(end_date).toDate()});
    }

    var adjust_th_width = function () {
        $('#table_report_detail tr.fixed_tr>th').each(function (i) {
            $(this).width($('#table_report_detail tr.inner_tr>th:eq('+i+')').width());
        });
    }

    var init_dom = function (rt_rpt, months) {
        //初始化模态对话框
        if ($('#modal_report_detail').length==0) {
            var html = __inline('modal.html');
            $('body').append(html);
            $('#modal_report_detail').on('shown.bs.modal', function () {
                $(this).find('[data-toggle=tooltip]').tooltip();
                adjust_th_width();
            });
            //初始化日历控件
            rt_rpt = rt_rpt?rt_rpt:0;
            months = months?months:3;
            $('#report_detail_days').attr({rt_rpt:rt_rpt, months:months});
            dtrPicker.init($('#report_detail_days'));
        }

        //修改日期范围事件
        $('#report_detail_days').off('change');
        $('#report_detail_days').on('change', function() {
            var start_date, end_date, type, shop_id, campaign_id, adgroup_id, creative_id, keyword_id;
            start_date = moment($(this).daterangepicker('getRange').start).format('YYYY-MM-DD');
            end_date = moment($(this).daterangepicker('getRange').end).format('YYYY-MM-DD');
            type = $('#modal_report_detail').attr('type');
            shop_id = $('#modal_report_detail').attr('shop_id');
            campaign_id = $('#modal_report_detail').attr('campaign_id');
            adgroup_id = $('#modal_report_detail').attr('adgroup_id');
            creative_id = $('#modal_report_detail').attr('creative_id');
            keyword_id = $('#modal_report_detail').attr('keyword_id');
            getReportDetail(start_date, end_date, type, shop_id, campaign_id, adgroup_id, creative_id, keyword_id);
        });

        //切换每日细分数据
        $('#modal_report_detail').off('click', '.show_subdivide');
        $('#modal_report_detail').on('click', '.show_subdivide', function () {
            if ($(this).hasClass('in')) {
                $(this).closest('tr').nextUntil('tr:not(.hover_non_color)').addClass('hidden');
                $(this).removeClass('in');
            } else {
                $(this).closest('tr').nextUntil('tr:not(.hover_non_color)').removeClass('hidden');
                $(this).addClass('in');
            }
            adjust_th_width();
        });

        $('#modal_report_detail').on('hide.bs.modal', function(){
            $('#report_detail_days').daterangepicker('close');
        })

    }

    return {
        init:init_dom,
        show:show
    }
});
