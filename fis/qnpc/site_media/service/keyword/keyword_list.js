define(['require','../common/common','template','moment', 'dataTable', '../../widget/ajax/ajax', '../../widget/loading/loading','json'],
    function(require,common,template,moment, dataTable, ajax, loading, _) {
    "use strict"

    var keyword_table;

    var start_date = moment().subtract(7, 'days').format('YYYY-MM-DD'),
        end_date = moment().subtract(1, 'days').format('YYYY-MM-DD');
    var kwIdList=[];
    var listType = '';
    var pcAddKws = [], pcCutKws = [], ydAddKws = [], ydCutKws = [], changeKw = {};

    var init_dom=function(type){
        listType = type;
        /**
         * 注册查排名事件
         */
        $('#keyword_table tbody').on('get.rank', 'tr', function(e, callBack) {
            var adgroup_id = $(this).data('adgroup_id');
            var keyword_id = $(this).attr('id');
            var keywordList = [keyword_id];
            ajax.ajax('batch_forecast_rt_rank', {'keyword_list': keywordList, 'adgroup_id': adgroup_id}, function(data){
                callBack && callBack(data);
            });
        });

        /**
         * 注册更新排名事件
         */
        $('#keyword_table tbody').on('update.rank', 'tr', function(e, pc_rank, mobile_rank) {
            $(this).find('.pc_rank').text(pc_rank);
            $(this).find('.mobile_rank').text(mobile_rank);
        });

        /**
         * 注册手动抢排名事件
         */
        $('#keyword_table tbody').on('update.rob_rank', 'tr', function(e, type, maxPrice, platform) {
            var html;

            $(this).data('locked', 0);

            if (type == "nomal") {
                html = '<a href="javascript:;" class="rob_set">抢</a>';
            }

            if (type == "fail") {
                html = '<a href="javascript:;" class="rob_record">手动抢失败</a>&emsp;<a href="javascript:;" class="rob_set ml5">再抢</a>';
            }

            if (type == "success") {
                if(platform=='pc'){
                    $(this).find('.max_price').text(maxPrice);
                    $(this).find('.sort_max_price').text(maxPrice);
                    $(this).find('.new_price').val(maxPrice);
                    $(this).find('.new_price').data('old',maxPrice);
                }else{
                    $(this).find('.max_mobile_price').text(maxPrice);
                    $(this).find('.sort_max_mobile_price').text(maxPrice);
                    $(this).find('.new_mobile_price').val(maxPrice);
                    $(this).find('.new_mobile_price').data('old',maxPrice);
                }

                html = '<a href="javascript:;" class="rob_record">手动抢成功</a>&emsp;<a href="javascript:;" class="rob_set ml5">再抢</a>';
            }

            if (type == "auto") {
                $(this).data('locked', 1);
                html = '<a href="javascript:;" class="rob_record">已设为自动</a>&emsp;<a href="javascript:;" class="rob_set ml5">设置</a>';
            }

            if (type == "doing") {
                html = '<a href="javascript:;" class="rob_doing">正在抢排名，请稍候</a>';
            }

            $(this).find('.rob_rank').html(html);
        });

        /**
         * 注册设置事件
         */
        $('#keyword_table tbody').on('get.rob_set', 'tr', function(e, options) {
            var trObj = $(this);
            var avgs = {
                keywordId: trObj.attr('id'),
                adgroupId: trObj.data('adgroup_id'),
                word: trObj.find('.word').text(),
                maxPrice: Number(trObj.find('.max_price').text()),
                maxMobilePrice: Number(trObj.find('.max_mobile_price').text()),
                qscore: trObj.find('.qscore').attr('pc_qscore'),
                wirelessQscore: trObj.find('.qscore').attr('yd_qscore'),
                target: listType
            };
            avgs = $.extend({}, avgs, options);
            require(['../rob_rank/rob_rank'], function(modal) {
                modal.show(avgs);
            });
            return false;
        });

        //桥接删除行
        $('#keyword_table tbody').on('delete_row', 'tr', function() {

            var index = $('#keyword_table tbody tr').index($(this));
            keyword_table.fnDeleteRow(index);
            $(this).remove();
            $('#keywords_count').text(keyword_table.fnGetData().length);
        });

        /**
         * 点击查排名
         */
        $('#keyword_table').on('click', '.rank', function() {
            var trObj = $(this).closest('tr');
            var img = $('<img src=' + __uri("/site_media/static/images/small_ajax.gif") + '>');
            $(this).replaceWith(img);
            var keyword_id = trObj.attr('id');
            trObj.trigger("get.rank", function(data){
                img.remove();
                if(keyword_id in data.data){
                   trObj.find('.pc_rank').attr('colspan', 1).text(data.data[keyword_id]['pc_rank_desc']);
                   trObj.find('.mobile_rank').text(data.data[keyword_id]['mobile_rank_desc']).show();
                }else{
                    trObj.find('.pc_rank').attr('colspan', 1).text('获取失败');
                    trObj.find('.mobile_rank').text('获取失败').show();
                }
            });
        });

        /**
         * 查看排名记录
         */
        // $('#keyword_table').on('click', '.rob_record', function() {
        //     var keyword_id = $(this).closest('tr').attr('id');
        //     ajax.ajax('rob_record', {'keyword_id':keyword_id}, function(data){
        //         var html = '';
        //         if (data.data[keyword_id].length){
        //             for (var i in data.data[keyword_id]) {
        //                 var obj = $.evalJSON(data.data[keyword_id][i]);
        //                 html += '<tr><td class="w100">' + obj.rob_time + '</td><td class="w100">' + Number(obj.price).toFixed(2) + '</td><td>' + obj.msg + '</td></tr>'
        //             }
        //         } else {
        //             html = '<tr><td colspan="3" style="text-align:center">暂无数据</td></tr>';
        //         }
        //         $('#rankDetailModal table tbody').html(html);
        //         $('#rankDetailModal').modal('show');
        //     });
        // });

        $('#keyword_table').on('click', '.rob_record', function() {
            var keyword_id = $(this).closest('tr').attr('id');
            require(['../rob_rank/rob_record'], function(modal) {
                modal.show({
                    keywordId: keyword_id
                });
            });
            return false;
        });

        /**
         * 抢排名设置
         */
        $('#keyword_table').on('click', '.rob_set',function(){

            var tr = $(this).closest('tr');
            var keyword_id = $(this).closest('tr').attr('id');
            ajax.ajax('rob_config', {'keyword_id': keyword_id}, function(data) {
                var options = {},
                    setting = $('#keyword_table').data('saveOptions.rank'),
                    args;
                var rank_start_desc_map = data.rank_start_desc_map;
                var rank_end_desc_map = data.rank_end_desc_map;
                if(data.data.platform){
                    var rank_start_name, rank_end_name;
                    rank_start_name = rank_start_desc_map[data.data.platform][data.data.rank_start];
                    rank_end_name = rank_end_desc_map[data.data.platform][data.data.rank_end];
                    options = {
                        method: 'auto',
                        keyword_id:keyword_id,
                        platform: data.data.platform,
                        rank_start: data.data.rank_start,
                        rank_start_name: rank_start_name,
                        rank_end: data.data.rank_end,
                        rank_end_name: rank_end_name,
                        limit: (data.data.limit / 100).toFixed(2),
                        nearly_success: data.data.nearly_success,
                        start_time: data.data.start_time,
                        end_time: data.data.end_time,
                        rank_start_desc_map: rank_start_desc_map,
                        rank_end_desc_map: rank_end_desc_map
                    }

                    args=$.extend({},options);
                }else{
                    options = {
                        method: '',
                        limit: '',
                        keyword_id:keyword_id,
                        rank_start_desc_map: rank_start_desc_map,
                        rank_end_desc_map: rank_end_desc_map
                    }
                    args=$.extend({},options,setting);
                }


                tr.trigger('get.rob_set', args);
            });
        });

        /**
         * 点击撤销
         */
        $('#keyword_table').on('click', '.undo', function() {
            var input = $(this).prev();
            input.val(input.data('old'));
            input.change();
        });

        /**
         * 修改出价
         */
        $('#keyword_table').on('change', '.edit_price', function() {

            var trObj = $(this).closest('tr');
            var keyword_id = trObj.attr('id');
            var adgroup_id = trObj.data('adgroup_id');
            var campaign_id = trObj.data('campaign_id');

            var new_value = trObj.find('.new_price').val();
            var old_value = parseFloat(trObj.find('.new_price').data('old')).toFixed(2);

            var new_mobile_price = trObj.find('.new_mobile_price').val();
            var old_mobile_price = parseFloat(trObj.find('.new_mobile_price').data('old')).toFixed(2);

            if (!isValidInput(new_value)||!isValidInput(new_mobile_price)) {
                if($(this).hasClass('new_price')){
                    $(this).val(old_value);
                }else{
                    $(this).val(old_mobile_price);
                }
                return;
            }else{
                var sort_value = parseFloat($(this).val()).toFixed(2);
                new_value = parseFloat(new_value).toFixed(2);
                new_mobile_price = parseFloat(new_mobile_price).toFixed(2);
                trObj.find('.new_price').val(new_value);
                trObj.find('.new_mobile_price').val(new_mobile_price);
                $(this).closest('td').find('.sort_price').text(sort_value);
                changeKw[keyword_id] = {
                    keyword_id:keyword_id,
                    adgroup_id: adgroup_id,
                    campaign_id: campaign_id,
                    word: trObj.find('.word').text(),
                    max_price: old_value,
                    new_price: new_value,
                    is_del: 0,
                    match_scope: trObj.data('match'),
                    mobile_old_price: old_mobile_price,
                    max_mobile_price:new_mobile_price,
                    mobile_is_default_price: trObj.data('mobile_match')
                };
                choseCurrentRank(trObj);
            }

            if(new_value>old_value){
                if($.inArray(keyword_id, pcCutKws)>-1){
                    pcCutKws.splice($.inArray(keyword_id, pcCutKws),1);
                }
                if($.inArray(keyword_id, pcAddKws)==-1){
                    pcAddKws.push(keyword_id);
                }
            }else if(new_value<old_value){
                if($.inArray(keyword_id, pcAddKws)>-1){
                    pcAddKws.splice($.inArray(keyword_id, pcAddKws),1);
                }
                if($.inArray(keyword_id, pcCutKws)==-1){
                    pcCutKws.push(keyword_id);
                }
            }else{
                if($.inArray(keyword_id, pcCutKws)>-1){
                    pcCutKws.splice($.inArray(keyword_id, pcCutKws),1);
                }
                if($.inArray(keyword_id, pcAddKws)>-1){
                    pcAddKws.splice($.inArray(keyword_id, pcAddKws),1);
                }
            }

            if(new_mobile_price>old_mobile_price){
                if($.inArray(keyword_id, ydCutKws)>-1){
                    ydCutKws.splice($.inArray(keyword_id, ydCutKws),1);
                }
                if($.inArray(keyword_id, ydAddKws)==-1){
                    ydAddKws.push(keyword_id);
                }
            }else if(new_mobile_price<old_mobile_price){
                if($.inArray(keyword_id, ydAddKws)>-1){
                    ydAddKws.splice($.inArray(keyword_id, ydAddKws),1);
                }
                if($.inArray(keyword_id, ydCutKws)==-1){
                    ydCutKws.push(keyword_id);
                }
            }else{
                if($.inArray(keyword_id, ydCutKws)>-1){
                    ydCutKws.splice($.inArray(keyword_id, ydCutKws),1);
                }
                if($.inArray(keyword_id, ydAddKws)>-1){
                    ydAddKws.splice($.inArray(keyword_id, ydAddKws),1);
                }
            }

            if(new_mobile_price!=old_mobile_price){
                changeKw[keyword_id]['mobile_is_default_price'] = 0;
            }

            if(new_mobile_price == old_mobile_price&&new_value==old_value&&$.inArray(keyword_id, changeKw)>-1){
                 delete changeKw[keyword_id];
            }

            $('#pc_add_count').text(pcAddKws.length);
            $('#pc_cut_count').text(pcCutKws.length);
            $('#yd_add_count').text(ydAddKws.length);
            $('#yd_cut_count').text(ydCutKws.length);
        });

        /**
         * 预估排名
         */
        $("#keyword_table tbody").on('click','.forecast', function(){
            setForcast($(this));
        });

        //刷新当前出价
        $('#refresh_list').on('click.sync_max_price',function(){
            ajax.ajax('keyword_attr',{kw_id_list:kwIdList,attr_list:['max_price']},function(data){
                for (var i in data.data){
                    $('#'+i).find('.max_price').text((data.data[i].max_price/100).toFixed(2));
                }
            });
        });

        /**
         * 预估排名联动价格
         */
        $("#keyword_table tbody").on('change', '.forecast_select', function() {
            var trObj = $(this).closest('tr');
            var newPrice;

            //跳转到说明页面
            if (this.value.indexOf('reason') != -1) {
                var tpl = __inline('forecast_fail_reason.html'),
                    obj;

                obj = $(tpl)
                $("body").append(obj);
                obj.modal();
                return false;
            }

            newPrice = Number(this.value.split('-')[0]);
            if (isValidInput(newPrice)) {
                trObj.find('.new_price').val(newPrice.toFixed(2));
                trObj.find('.new_price').change();
            } else {
                trObj.find('.new_price').val(trObj.find('.new_price').data('old'));
            }
        });

        /**
         * 重新预估
         */
        $("#keyword_table tbody").on('change', '.forecast_fail', function() {
            if ($(this).val() == '1') {
                setForcast($(this));
            }
        });

        /**
         * 改价提交到直通车
         */
         $('#submit_list').click(function(){
            var submit_list = [];
            for (var kw in changeKw) {
              submit_list.push(changeKw[kw]);
            }
            if(submit_list.length>0&&(pcAddKws.length>0||pcCutKws.length>0||ydAddKws.length>0||ydCutKws.length>0)){
                $.confirm({title:'提示',closeBtn: false, body: 'PC: 加价'+pcAddKws.length+'个，降价'+pcCutKws.length+'个；<br>' +
                    '移动: 加价'+ydAddKws.length+'个，降价'+ydCutKws.length+'个。<br>您确定要提交吗？', okBtn:"确定", cancelBtn:"取消", height:"60px", backdrop:"static", keyboard:false,
                    okHide:function(){
                        ajax.ajax('submit_keyword', { 'submit_list': $.toJSON(submit_list)},function(data) {
                             var update_count = data.update_kw.length,
                                failed_count = data.failed_kw.length;
                             var msg = '修改成功:' + update_count + '个，失败:' + failed_count + '个';
                             $.alert({title:'提示',hasfoot: false, body: msg, height:20});
                            for(var index in data.update_kw){
                                var kw_id = data.update_kw[index];
                                var keyword = changeKw[kw_id];
                                var trObj = $("#"+kw_id);
                                trObj.find('.sort_max_price').text(keyword['new_price']);
                                trObj.find('.new_price').data('old',keyword['new_price']);
                                trObj.find('.max_price').text(keyword['new_price']);

                                trObj.find('.sort_max_mobile_price').text(keyword['max_mobile_price']);
                                trObj.find('.new_mobile_price').data('old',keyword['max_mobile_price']);
                                trObj.find('.max_mobile_price').text(keyword['max_mobile_price']);
                            }
                            for(var index in data.failed_kw){
                                var kw_id = data.failed_kw[index];
                                var trObj = $("#"+kw_id);
                                trObj.find('.new_price').val(trObj.find('.new_price').data('old'));
                                trObj.find('.new_mobile_price').val(trObj.find('.new_mobile_price').data('old'));
                            }
                            $('#pc_add_count').text(0);
                            $('#pc_cut_count').text(0);
                            $('#yd_add_count').text(0);
                            $('#yd_cut_count').text(0);
                            changeKw = {};
                            pcAddKws = [];
                            pcCutKws = [];
                            ydAddKws = [];
                            ydCutKws = [];
                        });
                    }
                });
            }else{
                $.alert({title:'提示',hasfoot: false, body: '没有修改任何关键词！', height:20});
            }
         });
    };


    //获取关键词列表数据
    var getKeywordList=function(start, end) {
        var func = 'rob_list';
        if(listType=="core"){
            func = 'shop_core_list';
        }
        loading.show('数据加载中，请稍候...');
        ajax.ajax(func,{'start_date':start, 'end_date':end},function(data){
            getKeywordListCallBack(data);
            loading.hide();
        });
    };

    //获取关键词 回调
    var getKeywordListCallBack = function(data){
        var html, tpl;
        if(listType=="rank"){
            tpl = __inline("keyword_list_rank.html");
        }else if(listType=="core"){
            tpl = __inline("keyword_list_core.html");
        }
        html = template.compile(tpl)({keywordList: data.keyword_list});
        if (keyword_table) {
            keyword_table.fnClearTable();
            keyword_table.fnDestroy();
        }
        var msg = "暂无数据";
        if(data.msg){
            msg = data.msg;
        }
        $('#keywords_count').text(data.keyword_list.length);
        $('#keyword_table tbody').html(html);

        for (var i in data.keyword_list) {
            var obj = data.keyword_list[i];
            kwIdList.push(obj.keyword_id);
        }

        keyword_table = $('#keyword_table').dataTable({
            "bRetrieve": true, //允许重新初始化表格
            "bPaginate": false,
            "bDestroy": true,
            "bFilter": true,
            "bInfo": false,
            "bAutoWidth": false,//禁止自动计算宽度
            "sDom": '',
            "language": {"emptyTable": "<div style='text-align:center'>"+msg+"</div>"},
            "aoColumns": getSortColumn()
        });
        $('.show_tooltip').tooltip();
    };

     /**
      * 校验价格
      * @param str
      * @returns {boolean}
      */
    var isValidInput = function(str) {
        if (isNaN(str) || str < 0.05 || str > 99.99) {
            return false;
        }
        return true;
    }

    /**
     * 预估排名
     * @param trObj
     */
    var setForcast = function(obj){
        var trObj = obj.closest('tr');
        var keyword_id = trObj.attr('id');
        var forecast_success_tpl,
            forecast_fail_tpl,
            html,
            img;

        forecast_success_tpl = __inline("forecast_success.html");
        forecast_fail_tpl = __inline("forecast_fail.html");
        img = $('<img src=' + __uri("../../static/images/small_ajax.gif") + '>');

        obj.replaceWith(img);

        ajax.ajax('forecast_rank', {
            keyword_id: keyword_id
        }, function(data) {
            if ($.isArray(data.data) && data.data.length > 0) {
                if (data.data[99] == 9999) {
                    html = template.compile(forecast_fail_tpl)({
                        errMsg: "出价到99.99元也无法获得排名"
                    });
                } else {
                    html = template.compile(forecast_success_tpl)({
                        data: handleRankData(data.data)
                    });
                }
            } else {
                var errMsg = data.data.length > 0 ? data.data : '淘宝返回预估排名数据为空';
                html = template.compile(forecast_fail_tpl)({
                    errMsg: errMsg
                });
            }
            img.replaceWith(html);
            choseCurrentRank(trObj);
        });
    };

    /**
     * 预估排名解析函数
     * @param rank_data
     * @returns {Array}
     */
    var handleRankData = function(rank_data) {
        var result = [],
            page_data = [],
            page_data_rt = [],
            page_data_rb = [],
            page_data_b = [],
            page_pos = 17,
            position = 0,
            page_no, price, max_price, min_price, page_str;

        //分页处理
        for (var i = 0; i < Math.ceil(rank_data.length / page_pos); i++) {
            page_no = i + 1;
            page_data = rank_data.slice(i * page_pos, (i + 1) * page_pos);
            page_str = page_no > 1 ? '第' + page_no + '页' : '';
            //页面区域划分
            if (page_no < 3) {
                page_data_rt = page_data.slice(0, 4);
                page_data_rb = page_data.slice(4, 12);
                page_data_b = page_data.slice(12, 17);
            } else {
                page_data_rt = [];
                page_data_rb = page_data.slice(0, 12);
                page_data_b = page_data.slice(12, 17);
            }
            //右侧前四位(第3页以后为0)
            for (var j in page_data_rt) {
                price = (page_data_rt[j] / 100).toFixed(2);
                result.push([page_str + '第' + (Number(j) + 1) + '名：' + price + '元', price]);
            }
            //右侧后八位(第3页以后为12)
            if (page_data_rb.length > 0) {
                var rank_h = page_data_rt.length + 1,
                    rank_l = page_data_rt.length + page_data_rb.length;
                if (page_data_rb.length == 1) {
                    price = (page_data_rb[0] / 100).toFixed(2);
                    result.push([page_str + '第' + rank_h + '名：' + price + '元', price]);
                } else {
                    max_price = (page_data_rb[0] / 100).toFixed(2);
                    min_price = (page_data_rb[page_data_rb.length - 1] / 100).toFixed(2);
                    result.push([page_str + '第' + rank_h + '~' + rank_l + '名：' + max_price + '~' + min_price + '元', max_price + '-' + min_price]);
                }
            }
            //底部五位
            if (page_data_b.length > 0) {
                if (page_data_b.length == 1) {
                    price = (page_data_b[0] / 100).toFixed(2);
                    result.push(['第' + page_no + '页底部：' + price + '元', price]);
                } else {
                    max_price = (page_data_b[0] / 100).toFixed(2);
                    min_price = (page_data_b[page_data_b.length - 1] / 100).toFixed(2);
                    result.push(['第' + page_no + '页底部：' + max_price + '~' + min_price + '元', max_price + '-' + min_price]);
                }
            }
        }
        result.push([rank_data.length + '名以后：' + (min_price - 0.01).toFixed(2) + '元', (min_price - 0.01).toFixed(2)]);
        return result;
    };

    /**
     * 根据当前出价选中预估排名
     */
    var choseCurrentRank = function(trObj) {
        var selectObj = trObj.find('.forecast_select');
        if (selectObj.length == 0) return;
        var newPrice = trObj.find('.new_price').val(),
            matchPrice = null;

        selectObj.find('option').each(function() {
            var temp = Number(this.value.split('-').slice(-1)[0]);
            if (temp && newPrice >= temp) {
                matchPrice = this.value;
                return false;
            }
        });

        if (!matchPrice) {
            matchPrice = selectObj.find('option:last').prev().val();
        }

        selectObj.val(matchPrice);
    }

    //设置开始时间和结束时间
    var setQueryDate = function(start,end){
        start_date = start;
        end_date = end;
    }

        /**
         *
         */
    var getSortColumn = function(){
        if(listType=="rank"){
            return [
                {"bSortable": false},
                {"bSortable": true},
                {"bSortable": true,
                    "sType": 'custom',
                    "sSortDataType": "custom-text"
                },
                {"bSortable": true,
                    "sType": 'custom',
                    "sSortDataType": "custom-text"
                },
                {"bSortable": false},
                {"bSortable": false},
                {"bSortable": true},
                {"bSortable": true,
                    "sType": 'custom',
                    "sSortDataType": "custom-text"
                },
                {"bSortable": true},
                {"bSortable": true},
                {"bSortable": true},
                {"bSortable": true},
                {"bSortable": true},
                {"bSortable": true},
                {"bSortable": true}
            ];
        }else{
            return [
                {"bSortable": false},
                {"bSortable": true},
                {"bSortable": true},
                {"bSortable": true,
                    "sType": 'custom',
                    "sSortDataType": "custom-text"
                },
                {"bSortable": true},
                {"bSortable": true,
                    "sType": 'custom',
                    "sSortDataType": "custom-text"
                },
                {"bSortable": false},
                {"bSortable": false},
                {"bSortable": false},
                {"bSortable": true},
                {"bSortable": true,
                    "sType": 'custom',
                    "sSortDataType": "custom-text"
                },
                {"bSortable": true},
                {"bSortable": true},
                {"bSortable": true},
                {"bSortable": true},
                {"bSortable": true},
                {"bSortable": true},
                {"bSortable": true}
            ];
        }
    }

    return {
        init:init_dom,
        setQueryDate:setQueryDate,
        getKeywordList:getKeywordList
    }
});
