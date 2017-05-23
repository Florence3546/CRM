define(["template", 'widget/ajax/ajax', 'widget/alert/alert', 'widget/confirm/confirm', 'real_time', 'store', 'widget/jqueryExt/serializeObject', 'jslider', 'widget/templateExt/templateExt'], function(template, ajax, alert, confirm, real_time, store) {
    "use strict";

    var tpl,
        tpl = __inline('rob_rank.html'),
        okHidden;

    var show = function(options) {

        okHidden = false
            // options = $.extend({}, store.get('rob_setting'),options);

        var itemTitle = $('#item_title').text(),
            campaignTitle = $('#campaign_title').text(),
            picUrl = $('#adg_nav .adg_img_warp>img:eq(0)').attr('src');

        //判断从哪里触发的，页面上有宝贝标题和计划名称就是关键词详情，否则来自店铺核心词
        if (itemTitle == "" || campaignTitle == "") {
            var kw_info = $('#' + options.keywordId).find('.img_box img').data();

            itemTitle = kw_info.title;
            campaignTitle = kw_info.campTitle;
            picUrl = kw_info.picUrl;
        }

        options = $.extend({}, options, {
            itemTitle: itemTitle,
            campaignTitle: campaignTitle,
            picUrl: picUrl,
            target: document.body.id
        });

        layout(options);
    }

    var layout = function(options) {
        var html,
            obj,
            history_setting;

        if (options.start_time && isNaN(options.start_time)) {
            options.start_time = timeToNum(options.start_time);
        }

        if (options.end_time && isNaN(options.end_time)) {
            options.end_time = timeToNum(options.end_time);
        }

        html = template.compile(tpl)(options);

        obj = $(html);

        $('body').append(obj);
        obj.modal();

        //绑定事件
        obj.on('shown.bs.modal', function() {
            bindEvent.apply(this, [options]);
        });

        //绑定后续事件
        obj.on('hidden.bs.modal', function() {
            bindHiddenEvent.apply(this, [options]);
        });
    }

    var layoutSelect = function(obj, selectName, optionDict, current) {

        var optionStr = '<option value="">--请选择--</option>';
        for (var i in optionDict) {
            optionStr += '<option value="' + i + '" ' + ((current == i) ? 'selected' : '') + '>' + optionDict[i] + '</option>';
        }

        $(obj).find('select[name=' + selectName + ']').html(optionStr);
    }

    var bindEvent = function(options) {
        var self = this;

        //当排名更新后更新当前弹窗的排名
        $(document).on('batch_rt_kw_rank',function(e,data){
            $(self).find('.pc_rank').text(data[options.keywordId]['pc_rank_desc']);
            $(self).find('.yd_rank').text(data[options.keywordId]['mobile_rank_desc']);
        });

        //显示滑竿
        $(this).find('.slider input').slider({
            skin: "plastic",
            from: 0,
            to: 1440,
            step: 15,
            calculate: function(value) {
                return numToTime(value);
            }
        });

        $(this).find('.slider').removeClass('vh').addClass('hide');

        //切换方式
        $(this).find('input[name=method]').on('change', function() {
            var manual_info = $(self).find('.manual_info'),
                slider = $(self).find('.slider');

            if (this.value == 'auto') {
                slider.removeClass('hide');
                manual_info.addClass('hide');
            } else {
                slider.addClass('hide');
                manual_info.removeClass('hide');
            }
        });


        //当有默认配置时控制显示
        if (options.method == 'auto') {
            $(this).find('.slider').removeClass('hide');
        }
        if (options.method == 'manual') {
            $(this).find('.manual_info').removeClass('hide');
        }

        //切换平台
        $(this).find('input[name=platform]').on('change', function() {
            $('.platform_info', self).addClass('hide');

            if (this.value == 'pc') {
                layoutSelect(self, 'rank_start', options.rank_desc_map.pc_start, options.rank_start);
                layoutSelect(self, 'rank_end', options.rank_desc_map.pc_end, options.rank_end);

                if (options.qscore <= 5) {
                    $('.platform_info', self).removeClass('hide').find('span').text('PC端');
                }
            }

            if (this.value == 'yd') {
                layoutSelect(self, 'rank_start', options.rank_desc_map.yd_start, options.rank_start);
                layoutSelect(self, 'rank_end', options.rank_desc_map.yd_end, options.rank_end);

                if (options.wirelessQscore <= 5) {
                    $('.platform_info', self).removeClass('hide').find('span').text('移动端');
                }
            }

        });

        if (options.platform) {
            $(this).find('input[value=' + options.platform + ']').trigger('change');
        }

        //点击确定按钮
        $(this).find('.submit').on('click.submit', function() {

            var setting,
                errMsg = "";

            setting = $(self).find('form').serializeObject();

            if (!setting.method) {
                errMsg += '请选择抢位方式</br>';
            }

            if (!setting.platform) {
                errMsg += '请选择抢位平台</br>';
            }

            if (setting.rank_start==''||setting.rank_end==''||(Number(setting.rank_end) < Number(setting.rank_start))) {
                errMsg += '请正确填写期望排名,后面排名大于或等于前面排名</br>';
            }

            if (!setting.limit || isNaN(setting.limit) || (Number(setting.limit) < 0.05) || (Number(setting.limit) > 99.99)) {
                errMsg += '请正确填写最高限价,限价必须是0.05到99.99的整数</br>';
            }

            if (!setting.nearly_success) {
                errMsg += '请选择抢位不成功出价设置';
            }

            if (errMsg != "") {
                alert.fixedShow(errMsg);
                return false;
            }

            // store.set('rob_setting', setting);

            if (setting.method == 'auto') {
                var start_time,
                    end_time;

                start_time = numToTime(Number($('#rob_rank').find('.slider input').val().split(';')[0]));
                end_time = numToTime(Number($('#rob_rank').find('.slider input').val().split(';')[1]));

                ajax.ajax('auto_rob_rank', {
                    keyword_id: options.keywordId,
                    exp_rank_start: setting.rank_start,
                    exp_rank_end: setting.rank_end,
                    limit_price: parseInt(setting.limit * 100 + 0.5),
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
                            body = '<div class="f16">亲，您订购的版本不支持自动抢排名哦，请升级到旗舰版吧！</div><div class="tc mt10"><button type="button" class="btn btn-primary" data-dismiss="modal">知道了</button><a class="btn btn-primary ml20" href="/web/upgrade_suggest/" target="_blank">立即升级</a></div></div>';
                        }

                        if (data.limitError == 'nums_limit') {
                            title = 'Sorry，自动抢排名关键词个数已达上限';
                            body = '<div class="f16">亲，自动抢位的关键词已达到50个上限！</div><div class="tc mt10"><button type="button" class="btn btn-primary" data-dismiss="modal">知道了</button></div></div>';
                        }

                        if (data.limitError == 'others') {
                            title = 'Sorry，自动抢排名失败';
                            body = '<div class="f16">亲，请刷新页面重试</div><div class="tc mt10"><button type="button" class="btn btn-primary" data-dismiss="modal">知道了</button></div></div>';
                        }

                        alert.error_show({
                            id: 'alert_modal_fixed',
                            backdrop: false,
                            title: title,
                            footer: false,
                            body: body
                        });

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

        //取消自动抢排名
        $(this).on('click.rob_cancle', '.rob_cancle', function() {
            var trObj = $('#' + options.keywordId);
            confirm.show({
                body: '您确定取消“' + options.word + '”的自动抢排名吗？',
                backdrop: false,
                okHidden: function() {
                    ajax.ajax('rob_cancle', {
                        'keyword_id': options.keywordId
                    }, function() {
                        if (options.target == "auto_rob_rank") {
                            //利用对象冒泡可以触发table绑定的事件
                            trObj.trigger('delete_row', [options.keywordId]);
                            $('.keywords_count').text($('#keyword_table tbody>tr').length);
                        } else {
                            trObj.trigger('update.rob_rank', ['nomal']);
                        }

                        okHidden = false;
                        $(self).modal('hide');
                    });
                }
            });
        });
    }

    var bindHiddenEvent = function(options) {

        //手动抢排名呼出抢排名实时显示弹窗
        if (okHidden) {

            var setting = $(this).find('form').serializeObject(),
                trObj = $('#' + options.keywordId);


            setting.rank_start_name=$('[name=rank_start] option:selected').text();
            setting.rank_end_name=$('[name=rank_end] option:selected').text();

            real_time.show($.extend({}, options, setting));

            if (options.target != "auto_rob_rank") {
                trObj.trigger('update.rob_rank', ['doing']);
            }

            if (setting.method == 'auto') {
                var body;

                if (options.target == 'auto_rob_rank') {
                    trObj.find('.platform').text((setting.platform == 'pc') ? '计算机' : '移动');

                    if(setting.platform == 'pc'){
                        trObj.find('.exp_rank_start').text(options.rank_desc_map.pc_start[setting.rank_start]);
                        trObj.find('.exp_rank_end').text(options.rank_desc_map.pc_end[setting.rank_end]);
                    }else{
                       trObj.find('.exp_rank_start').text(options.rank_desc_map.yd_start[setting.rank_start]);
                       trObj.find('.exp_rank_end').text(options.rank_desc_map.yd_end[setting.rank_end]);
                    }

                    trObj.find('.limit_price').text(Number(setting.limit).toFixed(2));
                } else {
                    trObj.trigger('update.rob_rank', ['auto']);
                }
            }

            //保存配置到关键词上
            trObj.trigger('saveOptions.rank', [setting]);
        }

        $(this).remove();
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
