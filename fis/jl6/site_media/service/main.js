require(['require','jquery','bootstrap','service/common/common'], function (require,$,bootstrap,common){
    var alias_list=[],
    current_model = $('body').attr('id');

    for (var p in requirejs.s.contexts._.config.paths){
        var modalList= p.split('/');
        if(p.indexOf('service')!=-1&&modalList.slice(-1)==current_model){
            require([p], function(X) {
                X.init();
            });
            break;
        }
    }

    require(['service/common/top_bar_event'],function(topBarEvent){
        topBarEvent.init();
        topBarEvent.baseMain();

        // 动态切换客服旺旺和主旺旺
        var CONSULT_WW = $('#concet_ww').attr('CONSULT_WW');
        if (CONSULT_WW) {
            $.getJSON('http://amos.alicdn.com/muliuserstatus.aw?beginnum=0&site=cntaobao&charset=utf-8&uids='+CONSULT_WW+'&callback=?', function (data) {
                var ww_url;
                if (data.data[0]) {
                    $('#li_pskj_WW').hide();
                    ww_url = 'aliim:sendmsg?uid=cntaobao&siteid=cntaobao&touid=cntaobao'+CONSULT_WW;
                    $('a.a_WW').attr('href', ww_url);
                } else {
                    $('#li_CONSULT_WW').hide();
                }
            });
        }
    });

    require(['service/common/adg_top_bar_event'], function(adgTopBarEvent){
        adgTopBarEvent.init();
    });

    //用户行为分析  add by zhongjinfeng
    // require(['service/hot_zone/hot_zone'],function(hot_zone){
    //     hot_zone.init();
    // });

    require(['service/agent_login/agent_login'],function(agentLogin){
        agentLogin.init();
    });

    //顶部 填写用户手机号 QQ号
    require(['service/common/top_user_info'], function(topUserInfo){
        topUserInfo.init();
    });

    $.ready(function() {
    });
});

