define([
    'widget/ajax/ajax',
    'widget/alert/alert',
    'widget/confirm/confirm',
    'widget/loading/loading',
    'widget/lightMsg/lightMsg',
    'widget/switch/switch',
    'widget/scrollBar/scrollBar',
    'widget/chart/chart',
    'widget/dtrPicker/dtrPicker',
    'widget/select/select',
    'widget/showMore/showMore',
    'shiftcheckbox',
    'widget/bootstrapExt/popoverList'
    ], function(_ajax,_alert,_confirm,_loading,_lightMsg,_switch,_scrollBar,_chart,_dtrPicker,_select,_showMore,_shiftcheckbox,_popoverList) {
    "use strict"

    $(document).on('click','.hold-on-click',function(e){
        e.stopPropagation();
    });

    $('.jpoptip').on('mouseover',function(){
        $(this).addClass('active');
    });

    $('.jpoptip').on('mouseout',function(){
        $(this).removeClass('active');
    });

    var goto_ztc = function (type, campaign_id, adgroup_id, word) {
        var baseUrl = "http://subway.simba.taobao.com/#!/";
        var url = '';
        switch (type) {
            case 1: //添加计划
                url = baseUrl + 'campaigns/standards/add';
                break;
            case 2: //添加广告组
                url = baseUrl + 'campaigns/standards/adgroups/items/add?campaignId=' + campaign_id;
                break;
            case 3: //添加推广创意
                url = baseUrl + 'campaigns/standards/adgroups/items/creative/add?adGroupId=' + adgroup_id + '&campaignId=' + campaign_id;
                break;
            case 4: //管理推广创意
                url = baseUrl + 'campaigns/standards/adgroups/items/detail?tab=creative&campaignId='+ campaign_id + '&adGroupId=' + adgroup_id;
                break;
            case 5: //关键词流量解析
                url = baseUrl + 'tools/insight/queryresult?kws=' + encodeURIComponent(word);
                break;
            case 6://直通车充值
                url = baseUrl + 'account/recharge';
                break;
        }

        if (url !== ''){
            if (type != 5 && type != 2){
                _alert.show('亲，如果在后台作了修改，请记得同步到精灵哟!');
            }
            window.open(url, '_blank');
        }
    };

    //计算输入的字节长度
    var _true_length = function(str){
        var l = 0;
        for (var i = 0; i < str.length; i++) {
            if (str[i].charCodeAt(0) < 299) {
                l++;
            } else {
                l += 2;
            }
        }
        return l;
    };

    //校验用户是否登录
    var _is_authenticated = function (callback) {
        _ajax.ajax('is_authenticated', {}, function (data) {
            if (data.data) {
                callback();
            }
        })
    }

    //返回首页
    $(document).on('scroll',function(){
        var body_offset = document.body.scrollTop | document.documentElement.scrollTop;
        if(body_offset>200){
            $('#back_top').addClass('active');
        }else{
            $('#back_top').removeClass('active');
        }
    });

    $('#back_top').on('click',function(){$('html,body').animate({scrollTop: 0}, 300);});

    return {
        sendAjax:_ajax,
        alert:_alert,
        confirm:_confirm,
        loading:_loading,
        lightMsg:_lightMsg,
        chart:_chart,
        goto_ztc:goto_ztc,
        true_length:_true_length,
        is_authenticated:_is_authenticated
    }
});
