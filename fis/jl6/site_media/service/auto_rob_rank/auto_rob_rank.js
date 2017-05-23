define(['require', '../common/top_bar_event', '../common/common', "template", "../keyword/keyword", "moment", "jslider","widget/selectSort/selectSort","pin"], function(require, topBarEvent, common, template, keywordManage,moment) {
    "use strict"

    var KM,
        startDate=moment().subtract(7, 'days').format('YYYY-MM-DD'),
        endDate=moment().subtract(1, 'days').format('YYYY-MM-DD'),
        stgy='default',
        lastData;

    keywordManage.Row.prototype.setRowUp = function(checked, num) {
        num != undefined ? this.sortSpan.text(num) : this.sortSpan.text(1);
        $(this.nRow).addClass('top');
    }

    keywordManage.Row.prototype.setRowDown = function(checked) {
        this.sortSpan.text(0);
        $(this.nRow).removeClass('top');
    }

    keywordManage.Table.prototype.setChecked=function(){}

    keywordManage.Table.prototype.checkCallback=function(){}

    keywordManage.Table.prototype.checkedRow = function() {
        var rowList = [];
        this.table.find('tbody tr:not(.unsort)').each(function() {
            rowList.push($(this));
        });
        return rowList;
    }

    keywordManage.Table.prototype.COLUM_DICT = {
        'keyword': 2,
        'max_price': 3,
        'max_mobile_price': 4,
        'rank': 5,
        'rob': 6,
        'qscore': 7,
        'create_days': 8,
        'impressions': 9,
        'click': 10,
        'ctr': 11,
        'cost': 12,
        'ppc': 13,
        'cpm': 14,
        'avgpos': 15,
        'favcount': 16,
        's_favcount': 17,
        'a_favcount': 18,
        'favctr': 19,
        'favpay': 20,
        'carttotal': 21,
        'paycount': 22,
        'z_paycount': 23,
        'j_paycount': 24,
        'pay': 25,
        'z_pay': 26,
        'j_pay': 27,
        'conv': 28,
        'roi': 29,
        'g_pv': 30,
        'g_click': 31,
        'g_ctr': 32,
        'g_coverage': 33,
        'g_roi': 34,
        'g_cpc': 35,
        'g_competition': 36,
        'g_paycount': 37
    };

    var getData=function(rpt_days){
        common.loading.show('正在获取数据,请稍候...');
        common.sendAjax.ajax('keyword_locker_list', {
            start_date: startDate,
            end_date: endDate,
            source:$('#data_source button.active').data().source
        }, layoutKeywordList);
    }

    var bindEvent=function(){
        //切换日期
        $('#select_keyword_days').on('change', function(e, value) {
            startDate = moment($(this).daterangepicker('getRange').start).format('YYYY-MM-DD');
            endDate = moment($(this).daterangepicker('getRange').end).format('YYYY-MM-DD');

            //取实时数据
            if (startDate == endDate && moment(endDate).diff(new Date(), 'days') === 0) {
                common.loading.show('正在获取实时数据,请稍候...');
                common.sendAjax.ajax('get_rankkw_rtrpt', {
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
            }

            getData();
        });

        //数据来源切换
        $('#data_source button').on('click',function(){
            $('#data_source button.active').removeClass('active btn-primary').addClass('btn-default');
            $(this).addClass('active btn-primary');
            getData();
        });

        //修复fixheader
        $('.alert').on('closed.bs.alert',function(){
            KM.fixHeader.fnUpdate();
        });
    }

    //填充数据
    var layoutKeywordList=function(data){
        common.loading.hide();
        var html,
            tpl=__inline('auto_rob_rank.html');

        html = template.compile(tpl)({
            keywordList: data.keyword_list
        });

        if(KM){
            KM.table.fnDestroy();
        }

        // keywordManage.filter({
        //     element:$('#filter'),
        //     data:data.bulk_search_list
        // });

        $('#keyword_table tbody').html(html);

        // if(!data.keyword_list.length){
        //     return;
        // }

        var hideColumn = data.custom_column;
        var rob_index = hideColumn.indexOf('rob');
        if (rob_index >= 0) {
            hideColumn.splice(rob_index, rob_index);
        }
        hideColumn.push('g_pv');
        hideColumn.push('g_click');
        hideColumn.push('g_ctr');
        hideColumn.push('g_coverage');
        hideColumn.push('g_roi');
        hideColumn.push('g_cpc');
        hideColumn.push('g_competition');
        hideColumn.push('g_paycount');

        KM = new keywordManage.Table({
            element: $('#keyword_table'),
            hideColumn: hideColumn,
            warnPrice: Number($('#warn_price input').val()),
            headerMarginTop:40,
            layoutCallback:function(){
                var kwIdList=[];
                for (var row in this.rowCache) {
                    kwIdList.push(this.rowCache[row].keywordId);
                }

                //显示图片详情
                $('#keyword_table tbody').find('.img_box').popoverList({
                    trigger: 'hover',
                    placement: 'right',
                    html: true,
                    viewport: '#keyword_table',
                    content: function() {
                        var data=$(this).find('img').data();
                        return template.compile(__inline("img_box.html"))({
                            itemTitle:data.title,
                            campaignTitle:data.campTitle,
                            picUrl:data.picUrl,
                            price:data.price
                        });
                    }
                });

                //刷新当前出价
                // $('#rank_all').off('click.sync_max_price').on('click.sync_max_price',function(){
                //     common.sendAjax.ajax('keyword_attr',{kw_id_list:kwIdList,attr_list:['max_price','mobile_price']},function(data){
                //         for (var i in data.data){
                //             $('#'+i).find('.max_price').text((data.data[i].max_price/100).toFixed(2));
                //             $('#'+i).find('.max_mobile_price').text((data.data[i].mobile_price/100).toFixed(2));
                //         }
                //     });
                // });

                //显示所有提示
                $('[data-toggle="tooltip"]').tooltip({html:true});
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
        });

        KM.generateCsvData(data.keyword_list);

        lastData=data;

        //固定操作栏
        $('#operation_bar .line_box').pin({
            containerSelector: ".box"
        });
    }

    return {
        init:function(){
            if(!$('#version_limit').length){
                //获取初始数据
                getData(15);

                //绑定事件
                bindEvent();
            }
        }
    }
});
