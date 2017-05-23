define(['require', '../common/top_bar_event', '../common/common', "template", "../keyword/keyword", "moment", "store", "jslider", "widget/selectSort/selectSort","pin"], function(require, topBarEvent, common, template, keywordManage, moment, store) {
    "use strict"

    var KM,
        startDate = moment().subtract(7, 'days').format('YYYY-MM-DD'),
        endDate = moment().subtract(1, 'days').format('YYYY-MM-DD'),
        lastData;

    keywordManage.Table.prototype.COLUM_DICT = {
        'keyword': 3,
        'max_price': 4,
        'new_price': 5,
        'max_mobile_price': 6,
        'new_mobile_price': 7,
        'rank': 8,
        'rob': 9,
        'qscore': 10,
        'create_days': 11,
        'impressions': 12,
        'click': 13,
        'ctr': 14,
        'cost': 15,
        'ppc': 16,
        'cpm': 17,
        'avgpos': 18,
        'favcount': 19,
        's_favcount': 20,
        'a_favcount': 21,
        'favctr': 22,
        'favpay': 23,
        'carttotal': 24,
        'paycount': 25,
        'z_paycount': 26,
        'j_paycount': 27,
        'pay': 28,
        'z_pay': 29,
        'j_pay': 30,
        'conv': 31,
        'roi': 32,
        'g_pv': 33,
        'g_click': 34,
        'g_ctr': 35,
        'g_coverage': 36,
        'g_roi': 37,
        'g_cpc': 38,
        'g_competition': 39,
        'g_paycount': 40
    };


    var getData = function(rpt_days) {
        common.loading.show('正在获取数据,请稍候...');
        common.sendAjax.ajax('get_shop_core_kwlist', {
            start_date: startDate,
            end_date: endDate,
            source:$('#data_source button.active').data().source
        }, layoutKeywordList);
    }

    var bindEvent = function() {
        //切换日期
        $('#select_keyword_days').on('change', function(e, value) {
            startDate = moment($(this).daterangepicker('getRange').start).format('YYYY-MM-DD');
            endDate = moment($(this).daterangepicker('getRange').end).format('YYYY-MM-DD');

            //取实时数据
            /*
            if (startDate == endDate && moment(endDate).diff(new Date(), 'days') === 0) {
                common.loading.show('正在获取实时数据,请稍候...');
                common.sendAjax.ajax('get_corekw_rtrpt', {
                    start_date: startDate,
                    end_date: endDate,
                }, function(data) {
                    common.loading.hide();

                    var updateList = ['impr', 'click', 'ctr', 'cost', 'cpc', 'cpm', 'avgpos', 'favcount', 'favshopcount', 'favitemcount', 'favctr', 'favpay', 'carttotal', 'paycount', 'directpaycount', 'indirectpaycount', 'pay', 'directpay', 'indirectpay', 'conv', 'roi']

                    for (var i in lastData.keyword_list) {
                        var kwData = lastData.keyword_list[i];
                        for (var a in updateList) {
                            var attr = updateList[a];
                            kwData[attr] = data.result_dict[kwData.keyword_id][attr];
                        }
                    }

                    layoutKeywordList(lastData);
                });
                return;
            }*/

            getData();
        });

        //数据来源切换
        $('#data_source button').on('click',function(){
            $('#data_source button.active').removeClass('active btn-primary').addClass('btn-default');
            $(this).addClass('active btn-primary');
            getData();
        });

        $('#select_class').on('change', function(e, value) {
            store.set('shop_core_class', value);

            //不分类
            if (value == "0") {
                KM.setWeirdSwitch(false);
                KM.closeWeirdClass();
                return false;
            }

            //按计划分类
            if (value == "1") {
                KM.options.classDict = KM.config.classDict;
                KM.options.classBase = KM.config.classBase;
                KM.setWeirdSwitch(true);
            }

            //报表分类
            if (value == "2") {
                var classDict = {},
                    calssLength = 2,
                    temp = 1;

                for (var row in KM.rowCache) {
                    classDict[KM.rowCache[row].data.campaign_id] = [0, 0, KM.rowCache[row].data.camp_title];
                }

                for (var i in classDict) {
                    calssLength++;
                }

                for (var i in classDict) {
                    classDict[i][0] = (calssLength - temp) * 1000000000;
                    classDict[i][1] = temp * 1000000000;
                    temp++;
                }

                KM.options.classDict = classDict;
                KM.options.classBase = 'data-campaign_id';
                KM.setWeirdSwitch(true);
            }

            KM.setSortfalg();

            KM.table.fnSort([
                [1, 'desc']
            ]);

            KM.startWeirdClass();
        });

        //修复fixheader
        $('.alert').on('closed.bs.alert', function() {
            KM.fixHeader.fnUpdate();
        });
    }

    //填充数据
    var layoutKeywordList = function(data) {
        common.loading.hide();
        var html,
            options,
            tpl = __inline('shop_core.html');

        html = template.compile(tpl)({
            keywordList: data.keyword_list
        });

        if (KM) {
            KM.setWeirdSwitch(false);
            KM.table.fnDestroy();
        }

        $('#keyword_table tbody').html(html);

        options = {
            element: $('#keyword_table'),
            hideColumn: data.custom_column,
            warnPrice: Number($('#warn_price input').val()),
            useStore: false,
            headerMarginTop:50,
            layoutCallback: function() {
                var kwIdList = [];
                for (var row in this.rowCache) {
                    kwIdList.push(this.rowCache[row].keywordId);
                    this.rowCache[row].updateStyle();
                }

                //显示图片详情
                $('#keyword_table tbody').find('.img_box').popoverList({
                    trigger: 'hover',
                    placement: 'right',
                    html: true,
                    viewport: '#keyword_table',
                    content: function() {
                        var data = $(this).find('img').data();
                        return template.compile(__inline("img_box.html"))({
                            itemTitle: data.title,
                            campaignTitle: data.campTitle,
                            picUrl: data.picUrl,
                            price: data.price
                        });
                    }
                });

                //显示所有提示
                $('[data-toggle="tooltip"]').tooltip({
                    html: true
                });
            },
            aoColumns: [{
                bSortable: false
            }, {
                bSortable: true,
                "sSortDataType": "custom-weird",
                "sType": "custom",
            }, {
                bSortable: false
            }, {
                bSortable: false
            }, {
                bSortable: true,
                "sType": "custom",
                "sSortDataType": "custom-weird",
                "asSorting": ["desc", "asc"]
            }, {
                bSortable: false,
            }, {
                bSortable: true,
                "sType": "custom",
                "sSortDataType": "custom-weird",
                "asSorting": ["desc", "asc"]
            }, {
                bSortable: false,
            }, {
                bSortable: false,
                "sType": "custom",
                "sSortDataType": "custom-weird"
            }, {
                bSortable: false
            }, {
                bSortable: false,
                "sType": "custom",
                "sSortDataType": "custom-weird"
            }, {
                bSortable: true,
                "sType": "custom",
                "sSortDataType": "custom-weird",
                "asSorting": ["desc", "asc"]
            }, {
                bSortable: true,
                "sType": "custom",
                "sSortDataType": "custom-weird",
                "asSorting": ["desc", "asc"]
            }, {
                bSortable: true,
                "sType": "custom",
                "sSortDataType": "custom-weird",
                "asSorting": ["desc", "asc"]
            }, {
                bSortable: true,
                "sType": "custom",
                "sSortDataType": "custom-weird",
                "asSorting": ["desc", "asc"]
            }, {
                bSortable: true,
                "sType": "custom",
                "sSortDataType": "custom-weird",
                "asSorting": ["desc", "asc"]
            }, {
                bSortable: true,
                "sType": "custom",
                "sSortDataType": "custom-weird",
                "asSorting": ["desc", "asc"]
            }, {
                bSortable: true,
                "sType": "custom",
                "sSortDataType": "custom-weird",
                "asSorting": ["desc", "asc"]
            }, {
                bSortable: true,
                "sType": "custom",
                "sSortDataType": "custom-weird"
            }, {
                bSortable: true,
                "sType": "custom",
                "sSortDataType": "custom-weird",
                "asSorting": ["desc", "asc"]
            }, {
                bSortable: true,
                "sType": "custom",
                "sSortDataType": "custom-weird",
                "asSorting": ["desc", "asc"]
            }, {
                bSortable: true,
                "sType": "custom",
                "sSortDataType": "custom-weird",
                "asSorting": ["desc", "asc"]
            }, {
                bSortable: true,
                "sType": "custom",
                "sSortDataType": "custom-weird",
                "asSorting": ["desc", "asc"]
            }, {
                bSortable: true,
                "sType": "custom",
                "sSortDataType": "custom-weird",
                "asSorting": ["desc", "asc"]
            }, {
                bSortable: true,
                "sType": "custom",
                "sSortDataType": "custom-weird",
                "asSorting": ["desc", "asc"]
            }, {
                bSortable: true,
                "sType": "custom",
                "sSortDataType": "custom-weird",
                "asSorting": ["desc", "asc"]
            }, {
                bSortable: true,
                "sType": "custom",
                "sSortDataType": "custom-weird",
                "asSorting": ["desc", "asc"]
            }, {
                bSortable: true,
                "sType": "custom",
                "sSortDataType": "custom-weird",
                "asSorting": ["desc", "asc"]
            }, {
                bSortable: true,
                "sType": "custom",
                "sSortDataType": "custom-weird",
                "asSorting": ["desc", "asc"]
            }, {
                bSortable: true,
                "sType": "custom",
                "sSortDataType": "custom-weird",
                "asSorting": ["desc", "asc"]
            }, {
                bSortable: true,
                "sType": "custom",
                "sSortDataType": "custom-weird",
                "asSorting": ["desc", "asc"]
            }, {
                bSortable: true,
                "sType": "custom",
                "sSortDataType": "custom-weird",
                "asSorting": ["desc", "asc"]
            }, {
                bSortable: true,
                "sType": "custom",
                "sSortDataType": "custom-weird",
                "asSorting": ["desc", "asc"]
            }, {
                bSortable: true,
                "sType": "custom",
                "sSortDataType": "custom-weird",
                "asSorting": ["desc", "asc"]
            }, {
                bSortable: true,
                "sType": "custom",
                "sSortDataType": "custom-weird",
                "asSorting": ["desc", "asc"]
            }, {
                bSortable: true,
                "sType": "custom",
                "sSortDataType": "custom-weird",
                "asSorting": ["desc", "asc"]
            }, {
                bSortable: true,
                "sType": "custom",
                "sSortDataType": "custom-weird",
                "asSorting": ["desc", "asc"]
            }, {
                bSortable: true,
                "sType": "custom",
                "sSortDataType": "custom-weird",
                "asSorting": ["desc", "asc"]
            }, {
                bSortable: true,
                "sType": "custom",
                "sSortDataType": "custom-weird",
                "asSorting": ["desc", "asc"]
            }, {
                bSortable: true,
                "sType": "custom",
                "sSortDataType": "custom-weird",
                "asSorting": ["desc", "asc"]
            }, {
                bSortable: true,
                "sType": "custom",
                "sSortDataType": "custom-weird",
                "asSorting": ["desc", "asc"]
            }]
        };


        KM = new keywordManage.Table(options);

        if (data.keyword_list.length) {
            $('#select_class').trigger('change', [$('#select_class span.active').parent().data().value]);
            KM.generateCsvData(data.keyword_list);
        }

        lastData = data;

        //固定操作栏
        $('.operate').pin({
            containerSelector: ".box",
            padding:{
                bottom:-40
            }
        });
    }

    return {
        init: function() {
            if ($('#keyword_table').length) {

                //设置用户默认分类
                $('#select_class').trigger('choose.data-select', [store.get('shop_core_class', '0')]);

                //获取初始数据
                getData(15);

                //绑定事件
                bindEvent();
            }
        }
    }
});
