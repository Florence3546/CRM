PT.namespace('LoginUsers');
PT.LoginUsers = function() {
    var pad_blank_row = function () {
        if ($('#table_login_users>tbody>tr:visible').length==0) {
            $('#table_login_users>tbody').append('<tr><td colspan="6">暂无未隐藏的用户登录</td></tr>');
        }
    }
    
    var init_dom = function() {
        pad_blank_row();
        //隐藏提醒
        $('#table_login_users').on('click', 'a.hide_record', function () {
            $(this).closest('tr').addClass('hide');
            pad_blank_row();
            PT.sendDajax({
                'function': 'ncrm_hide_login_info',
                'shop_id': $(this).attr('shop_id')
            });
        });
    }

    return {
        init: function() {
            init_dom();
            setInterval(function () {
                PT.sendDajax({
                    'function': 'ncrm_get_login_users',
                    'callback': 'PT.LoginUsers.get_login_users_callback'
                });
            }, 10*60*1000);
        },
        get_login_users_callback: function (result) {
            var html;
            if (result.user_list) {
                html = template.render('login_info_temp', result);
            } else {
                html = '<tr><td colspan="6">暂无用户登录</td></tr>';
            }
            $('#table_login_users>tbody').html(html);
            pad_blank_row();
        }
    }
}();
