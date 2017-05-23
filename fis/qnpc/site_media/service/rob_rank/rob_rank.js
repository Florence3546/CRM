define(["template", 'jslider', 'widget/jqueryExt/serializeObject', '../../widget/ajax/ajax', 'real_time'], function(template, jslider,jqExt, ajax, real_time) {
    "use strict";

    var tpl = __inline('rob_rank.html'),okHidden;

    var rank_html,rank_tpl = __inline("rank_item.html");

    var rank_desc_dict;

    var show = function(options) {
        var html,
            obj,
            history_setting;

        if (options.start_time&&isNaN(options.start_time)) {
            options.start_time = timeToNum(options.start_time);
        }

        if (options.end_time&&isNaN(options.end_time)) {
            options.end_time = timeToNum(options.end_time);
        }

        html = template.compile(tpl)(options);
        obj = $(html);

        $('body').append(obj);
        obj.modal({backdrop:"static", keyboard:false});

        getStartRankList(options.platform, options.rank_start_desc_map);
        getEndRankList(options.platform, options.rank_end_desc_map);

        bindEvent(obj, options);

        obj.modal('show');

        //绑定事件
        obj.on('hidden.bs.modal', function() {
            hiddenEvent(obj, options);
        });

        //触发查排名
        $('#' + options.keywordId).trigger('get.rank', [function(data) {

            if(options.keyword_id in data.data){
                obj.find('.pc_rank').text(data.data[options.keyword_id]['pc_rank_desc']);
                obj.find('.yd_rank').text(data.data[options.keyword_id]['mobile_rank_desc']).show();
            }else{
                obj.find('.pc_rank').text('获取失败');
                obj.find('.yd_rank').text('获取失败');
            }

            if (data.data[options.keyword_id]['mobile_rank_desc'].indexOf("未投放")>=0) {
                $('input[value=pc]').find('input[value=pc]').attr('checked');
                $('input[value=yd]').attr('disabled', true);
            }
        }]);

        $('.rank_item_start li').each(function(e){
            var value = $(this).find('a').attr('value')
            if(value==$('#rank_start').val()){
                $(this).addClass('active');
            }else{
                $(this).removeClass('active');
            }
        });

        $('.rank_item_end li').each(function(e){
            var value = $(this).find('a').attr('value')
            if(value==$('#rank_end').val()){
                $(this).addClass('active');
            }else{
                $(this).removeClass('active');
            }
        });
    };

    var getStartRankList = function(platform, rank_start_desc_map){
        var rank_list = [];
        rank_desc_dict = rank_start_desc_map[platform];
        for(var id in rank_desc_dict){
            rank_list.push({id: id, name: rank_desc_dict[id]});
        }
         rank_html = template.compile(rank_tpl)({list: rank_list});
        $('.rank_item_start').html(rank_html);

    };

    var getEndRankList = function(platform, rank_end_desc_map){
        var rank_list = [];
        rank_desc_dict = rank_end_desc_map[platform];
        for(var id in rank_desc_dict){
            rank_list.push({id: id, name: rank_desc_dict[id]});
        }
         rank_html = template.compile(rank_tpl)({list: rank_list});
        $('.rank_item_end').html(rank_html);
    };

    /**
     * 绑定各种事件
     */
    var bindEvent = function(obj,options){
        var self = obj;
        //初始化显示滑竿
        $(self).find('.slider input').slider({
            skin: "plastic",
            from: 0,
            to: 1440,
            step: 60,
            calculate: function(value) {
                return numToTime(value);
            }
        });

        $(self).find('.slider').removeClass('vh').addClass('hide');

        //切换方式手动、自动
        $(self).find('input[name=method]').on('change', function() {
            var manual_info = $(self).find('.manual_info'),
                slider = $(self).find('.slider');
            if (this.value == 'auto') {
                slider.css("display","inline-block");
                manual_info.addClass('hide');
            }else{
                slider.css("display","none");
                manual_info.removeClass('hide');
            }
        });

        if (options.method) {
            $(self).find('input[name=method]').trigger('change');
        }

        /**
         * 切换平台
         */
        $(self).on('change', 'input[name=platform]', function() {
            $('.platform_info', self).addClass('hide');

            if (this.value == 'pc' && (options.qscore <= 5)) {
                $('.platform_info', self).removeClass('hide').find('span').text('PC端');
            }

            if (this.value == 'yd' && (options.wirelessQscore <=5)) {
                $('.platform_info', self).removeClass('hide').find('span').text('移动端');
            }

            getStartRankList(this.value, options.rank_start_desc_map);
            getEndRankList(this.value, options.rank_end_desc_map);
            $('.rank_value').val('-3');
            $('.rank_name').text('请选择...');
        });

//        if (options.platform) {
//            $(self).find('input[value=' + options.platform + ']').trigger('change');
//        }

        //点击确定按钮
        $(self).on('click', '.submit', function() {

            var setting,
                errMsg = "";

            setting = $(self).find('form').serializeObject();

            if (!setting.method) {
                errMsg += '请选择抢位方式</br>';
            }

            if (!setting.platform) {
                errMsg += '请选择抢位平台</br>';
            }
            if (setting.rank_end=='-3'||setting.rank_start==-3||Number(setting.rank_end) < Number(setting.rank_start)){
                errMsg += '请正确选择期望排名,后面排名大于或等于前面排名</br>';
            }

            if (!setting.limit || isNaN(setting.limit) || (Number(setting.limit) < 0.05) || (Number(setting.limit) > 99.99)) {
                errMsg += '请正确填写最高限价,限价必须是0.05到99.99的数字</br>';
            }

            if (!setting.nearly_success) {
                errMsg += '请选择抢位不成功出价设置';
            }

            if (errMsg != "") {
                $.alert({title:'错误',closeBtn: false, body: errMsg, okBtn:"确定", height:"60px", backdrop:"static", keyboard:false});
                return false;
            }

            if (setting.method == 'auto') {
                var start_time,
                    end_time;

                start_time = numToTime(Number($('#rob_rank').find('.slider input').val().split(';')[0]));
                end_time = numToTime(Number($('#rob_rank').find('.slider input').val().split(';')[1]));
                /**
                 * 在这里进行提交操作
                 */
                ajax.ajax('auto_rob_rank', {
                    keyword_id: options.keywordId,
                    exp_rank_start: setting.rank_start,
                    exp_rank_end: setting.rank_end,
                    limit_price: parseInt(setting.limit*100+0.5),
                    platform: setting.platform,
                    start_time: start_time,
                    end_time: end_time,
                    nearly_success: setting.nearly_success
                }, function(data) {
                    if (data.limitError != '') {
                        var title,
                            body;

                        if (data.limitError == 'version_limit') {
                            title = 'Sorry!当前版本不支持';
                            body = '亲，您订购的版本不支持自动抢排名哦，请升级到八引擎版吧！&emsp;&emsp;<a href="/web/upgrade_suggest/" target="_blank">立即升级</a></div></div>';
                        }

                        if (data.limitError == 'nums_limit') {
                            title = 'Sorry，自动抢排名关键词个数已达上限';
                            body = '亲，自动抢位的关键词已达到50个上限！';
                        }

                        if (data.limitError == 'others') {
                            title = 'Sorry，自动抢排名失败';
                            body = '亲，请刷新页面重试';
                        }
                        $.alert({title:title,closeBtn: false, body: body, okBtn:"知道了", height:"60px", backdrop:"static", keyboard:false});
                    } else {
                        okHidden = true;
                        $(self).modal('hide');
                    }
                });
                return false
            }
            okHidden = true;
            $(self).modal('hide');
        });

        /**
         * 取消自动强排名
         */
        $(self).on('click', '.rob_cancle', function() {
            var trObj = $('#' + options.keywordId);
            $.confirm({title:'提示',closeBtn: false, body: '您确定取消“' + options.word + '”的自动抢排名吗？', okBtn:"确定", cancelBtn:"取消", height:"60px", backdrop:"static", keyboard:false,
                okHide:function(){
                    ajax.ajax('rob_cancle', {
                        'keyword_id': options.keywordId
                    }, function() {
                        if(options.target=="rank"){
                            //利用对象冒泡可以出发table绑定的事件
                            trObj.trigger('delete_row',[options.keywordId]);
                        }else{
                            trObj.trigger('update.rob_rank', ['nomal']);
                        }
                        okHidden = false;
                        $(self).modal('hide');
                    });
                }
            });
        });
    };

    var hiddenEvent = function(obj, options) {
        if (okHidden) {

            var setting = obj.find('form').serializeObject(),
                trObj = $('#' + options.keywordId);

            options["rank_start_name"] = obj.find('#rank_start').next('.rank_name').html();
            options["rank_end_name"] = obj.find('#rank_end').next('.rank_name').html();

            real_time.show($.extend({}, options, setting));

            if (setting.method == 'auto') {
                if (options.target == 'rank') {
                    trObj.find('.platform_name').text((setting.platform=='pc')?'计算机':'移动　');
                    trObj.find('.exp_rank_start').text(rank_desc_dict[setting.rank_start]);
                    trObj.find('.exp_rank_end').text(rank_desc_dict[setting.rank_end]);
                    trObj.find('.limit_price').text(Number(setting.limit).toFixed(2));
                }else{
                    trObj.trigger('update.rob_rank', ['auto', setting.platform]);
                }
            }
            //保存配置到关键词上
            $('#keyword_table').data('saveOptions.rank', $.extend({}, options, setting));
        }
        okHidden = false;

        $(obj).remove();
    }

    var numToTime = function(num) {
        var hours = Math.floor(num / 60);
        var mins = (num - hours * 60);
        return (hours < 10 ? "0" + hours : hours) + ":" + (mins == 0 ? "00" : mins);
    }

    var timeToNum = function(time) {
        return Number(time.split(':')[0]) * 60 + Number(time.split(':')[1]);
    }

    return {
        show: show
    }
});
