PT.namespace('Vip');
PT.Vip = function () {

    var init_dom = function () {

        $(document).on('click', '.submit_info', function(){
            if($(this).hasClass('disabled')){
                return false;
            }
            var cname = $('#id_cname').val();
            var phone = $('#id_phone').val();
            //var code = $('#id_phone_code').val();

            if(isNaN(phone) || !(/^1[3|4|5|8]\d{9}$/.test(phone))){
                PT.alert("手机号码填写不正确！");
                return false;
            }

            if(!cname) {
                PT.alert("请填写联系人");
                return false;
            }
            /*
            if(!/^[1-9]\d{4}$/.test(code)){
                PT.alert("请输入正确的手机验证码！");
            }*/
            PT.show_loading("正在提交手机号");
            PT.sendDajax({'function':'web_submit_userinfo', 'phone':phone, 'cname':cname, 'source':'vip'});
        });

        $(document).on('click', '.add_point', function () {
            PT.show_loading("正在提交数据");
            PT.sendDajax({'function':'web_add_point'});
        });

        $(document).on('click', '.get_sale_url', function () {
            PT.show_loading('正在获取优惠链接');
            PT.sendDajax({'function':'web_get_sale_url', 'version': $('#version').val()});
        });
    };

    return {
        init: function () {
            init_dom();
        },
        add_point_back: function(result) {
            if (result) {
                PT.alert('<span class="large"><span class="r_color">领取精灵币成功！</span><a href="/web/invite_friend/" target="_blank">立即使用</a></span>');
                $('.add_point').next().show().end().remove();
            } else {
                PT.alert('您已经领取了精灵币');
            }
        }
    };
}();
