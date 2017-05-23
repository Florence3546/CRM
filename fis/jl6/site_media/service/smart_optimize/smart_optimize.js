define(['require', '../common/top_bar_event', '../common/common', "template", "../keyword/keyword", "moment", "jslider","pin"], function(require, topBarEvent, common, template, keywordManage,moment) {
    "use strict"

    var campaign_id,
        adgroup_id,
        item_id,
        KM,
        startDate=moment().subtract(7, 'days').format('YYYY-MM-DD'),
        endDate=moment().subtract(1, 'days').format('YYYY-MM-DD'),
        stgy='default';

    var setInitData = function() {
        campaign_id = $('#campaign_id').val();
        adgroup_id = $('#adgroup_id').val();
        item_id = $('#item_id').val();
    }

    var getData = function(rpt_days) {
        common.loading.show('正在获取数据,请稍候...');
        common.sendAjax.ajax('adgroup_optimize', {
            adgroup_id: adgroup_id,
            campaign_id: campaign_id,
            start_date: startDate,
            end_date: endDate,
            stgy:stgy,
            source:$('#data_source button.active').data().source
        }, layoutKeywordList);
    }

    var bindEvent = function() {
        //切换日期
        $('#select_keyword_days').on('change', function(e, value) {
            startDate = moment($(this).daterangepicker('getRange').start).format('YYYY-MM-DD');
            endDate = moment($(this).daterangepicker('getRange').end).format('YYYY-MM-DD');
            getData();
        });

        //数据来源切换
        $('#data_source button').on('click',function(){
            $('#data_source button.active').removeClass('active btn-primary').addClass('btn-default');
            $(this).addClass('active btn-primary');
            getData();
        });

        //滑杆
        $('#set_percent input').slider({
            from: 30,
            to: 300,
            skin: 'power',
            callback: function(value) {
                for (var row in KM.rowCache) {
                    var obj = KM.rowCache[row],
                        newPrice,
                        changePrice;


                    //如果系统推荐出价小于当前出价（滑杆只适合例行优化和降价省油）
                    // if((obj.data.new_price<obj.maxPrice && stgy == 'plus')||(obj.data.new_price>obj.maxPrice && stgy == 'fall')){
                    //     continue;
                    // }

                    changePrice = ((obj.data.new_price - obj.maxPrice) * value) / 100;

                    if (changePrice > 0 && changePrice < 0.01){
                        changePrice = 0.01;
                    } else if (changePrice < 0 && changePrice > -0.01) {
                        changePrice = -0.01;
                    }

                    newPrice = (changePrice + obj.maxPrice).toFixed(2);

                    if (newPrice < 0.05) {
                        newPrice = 0.05;
                    }

                    if (newPrice > 99.99) {
                        newPrice = 99.99;
                    }

                    obj.newPriceInput.val(newPrice);
                    obj.updateStyle();
                }

                for (var row in KM.rowCache) {
                    var obj = KM.rowCache[row],
                        newPrice,
                        changePrice;


                    //如果系统推荐出价小于当前出价（滑杆只适合例行优化和降价省油）
                    // if((obj.data.new_mobile_price<obj.maxMobilePrice && stgy == 'plus')||(obj.data.new_mobile_price>obj.maxMobilePrice && stgy == 'fall')){
                    //     continue;
                    // }

                    changePrice = ((obj.data.new_mobile_price - obj.maxMobilePrice) * value) / 100;

                    if (changePrice > 0 && changePrice < 0.01){
                        changePrice = 0.01;
                    } else if (changePrice < 0 && changePrice > -0.01) {
                        changePrice = -0.01;
                    }

                    newPrice = (changePrice + obj.maxMobilePrice).toFixed(2);

                    if (newPrice < 0.05) {
                        newPrice = 0.05;
                    }

                    if (newPrice > 99.99) {
                        newPrice = 99.99;
                    }

                    obj.newMobilePriceInput.val(newPrice);
                    obj.updateStyle();
                }
            }
        });

        //调整优化类型
        $('#smart_optimize_select').on('change',function(e,value){
            stgy=value;
            getData();
        });
    }

    //填充数据
    var layoutKeywordList = function(data) {
        common.loading.hide();
        var html,
            tpl = __inline('../bulk_optimize/keyword_list.html');

        html = template.compile(tpl)({
            keywordList: data.keyword_list,
            adg_nosch: data.nosearch_rpt,
            set_mnt_flag: data.set_mnt_flag,
            userNewPrice: true,
            adgroup_id:adgroup_id
        });

        if (KM) {
            KM.table.fnDestroy();
        }

        $('#keyword_table tbody').html(html);

        // if(!data.keyword_list.length){
        //     return;
        // }

        KM = new keywordManage.Table({
            element: $('#keyword_table'),
            hideColumn: data.custom_column,
            warnPrice: Number($('#warn_price input').val()),
            mobileWarnPrice: Number($('#mobile_warn_price input').val()),
            headerMarginTop:50,
            layoutCallback: function() {
                for (var row in this.rowCache) {
                    if(this.rowCache[row].data.optm_type==1){
                        this.rowCache[row].del=true;
                    }
                    this.rowCache[row].updateStyle();

                    if(this.rowCache[row].up||this.rowCache[row].down||this.rowCache[row].del){
                        this.rowCache[row].checkboxInput[0].checked = true;
                    }else{
                        this.rowCache[row].checkboxInput[0].checked = false;
                    }
                }
                this.calcChangeNum();
                this.checkCallback();
                //显示所有提示
                $('[data-toggle="tooltip"]').tooltip({html:true});
            }
        });

        KM.generateCsvData(data.keyword_list);

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

            topBarEvent.adgMain();

            //设置初始数据
            setInitData();

            if(!adgroup_id){
                return;
            }

            //获取初始数据
            getData(15);

            //绑定事件
            bindEvent();
        }
    }
});
