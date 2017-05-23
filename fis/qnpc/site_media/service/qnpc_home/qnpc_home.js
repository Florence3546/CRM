define(['require', 'highcharts', 'template', '../../widget/chart/chart', 'campaign_list',
        'moment', 'account_detail', '../../widget/ajax/ajax', '../../widget/loading/loading'],
    function (require, _, template, chart, campaignList, moment, accountDetail, ajax) {


        var start_date = moment().subtract(7, 'days').format('YYYY-MM-DD'),
            end_date = moment().subtract(1, 'days').format('YYYY-MM-DD');
        var initDom = function () {
            getAccountRpt(start_date, end_date);
            getChart(start_date, end_date);
            campaignList.init(start_date, end_date);

            /**
             * 全部参与/取消推广
             */
            $('.opt-mnt').click(function () {
                var camp_id_arr = campaignList.getCampaignIdList();
                if (camp_id_arr.length <= 0) {
                    $.alert({title: '注意', body: '请先选择计划!', okBtn: "确定", height: "60px"});
                    return;
                }
                var confirmMsg = "";
                var mode = $(this).data('opt');
                if (mode == "1") {
                    confirmMsg = "确定要推广选中的计划吗?";
                } else {
                    confirmMsg = "确定要将选中的计划暂停推广吗?";
                }

                $.confirm({
                    title: '提示',
                    body: confirmMsg,
                    okBtn: '确定',
                    cancelBtn: '取消',
                    okHide: function () {
                        campaignList.updateCampStatus(mode, camp_id_arr);
                    }
                })
            });

            /**
             * 查看详细数据
             */
            $('#show_detail').click(function () {
                $("#accountDetailModal").modal("show");
                if (!accountDetail.hasInit()) {
                    accountDetail.init();
                }
            });

            /**
             * 按天数选择
             */
            $('#select_date').change(function () {
                var days = Number($(this).val());
                if (days == 0) {
                    start_date = moment().subtract(0, 'days').format('YYYY-MM-DD'),
                        end_date = moment().subtract(0, 'days').format('YYYY-MM-DD');
                } else {
                    start_date = moment().subtract(days, 'days').format('YYYY-MM-DD'),
                        end_date = moment().subtract(1, 'days').format('YYYY-MM-DD');
                }
                getAccountRpt(start_date, end_date);
                campaignList.getCampaignList(start_date, end_date);
            });

            if ($('#get_phone_modal')) {
                $('#inputPhone').tooltip({
                    placement: 'right',
                    title:'请输入正确的手机号',
                    trigger: 'manual'
                });
                $('#inputPhone').focus(function(){
                    $('#inputPhone').tooltip('hide');
                });
                $('#submit_phone').on('click', function () {
                    var phone = $('#inputPhone').val();
                    var qq = $('#inputQQ').val();
                    if (!checkTel(phone)) {
                        $('#inputPhone').tooltip('show');
                    }else{

                        ajax.ajax('submit_userinfo', {phone:phone, qq:qq}, function(data){
                            $('#get_phone_modal').modal('hide');
                            $.alert({title: '提示', body: '提交成功!', okBtn: "确定", height: "60px"});
                        });
                    }
                });

                $('#get_phone_modal').modal({
                    backdrop: true,
                    keyboard: false,
                    okHide: function (e) {

                    }
                });
                $('#get_phone_modal').modal('show');
            }
        };

        /**
         * 校验电话
         * @returns {boolean}
         */
        function checkTel(value) {
            //var isMob = /^((\+?86)|(\(\+86\)))?(13[0123456789][0-9]{8}|15[012356789][0-9]{8}|18[02356789][0-9]{8}|147[0-9]{8}|1349[0-9]{7})$/;
            var isMob = /^((\+?86)|(\(\+86\)))?(13[0-9]|15[012356789]|17[78]|18[0-9]|14[57])[0-9]{8}$/;
            if(isMob.test(value)){
                return true;
            }else {
                return false;
            }
        }

        /**
         * 获取账户报表数据
         * @param start_date
         * @param end_date
         */
        var getAccountRpt = function (start_date, end_date) {

            ajax.ajax('account', {'start_date': start_date, 'end_date': end_date}, function (data) {
                getAccountRptCallBack(data);
            });
        };

        /**
         * 账户报表查询回调韩式
         */
        var getAccountRptCallBack = function (data) {

            var tpl, html, wrap;
            tpl = __inline('sum_report.html');
            wrap = $('.total_rpt');
            html = template.compile(tpl)(data.account_data_dict);

            wrap.html(html);
        };

        /**
         * 查询图表数据
         */
        var getChart = function () {
            ajax.ajax('show_chart', {'start_date': start_date, 'end_date': end_date}, function (data) {
                if (data.chart_data) {
                    chart.draw('account_chart', data.chart_data.category_list, data.chart_data.series_cfg_list);
                }
                ;
            });
        };

        return {
            init: function () {
                initDom();
            }
        }

    });
