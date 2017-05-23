/**
 * Created by Administrator on 2015/11/7.
 */
define(['jquery','jl6/site_media/widget/alert/alert','jl6/site_media/widget/ajax/ajax'],function($,alert,ajax){

    var init = function(){

        $('#agent_login').click(function(){
            if(!$('#username').val().trim()||!$('#password').val().trim()){
                $('#err_msg').text('用户名和密码不能为空！');
                $('.err_alert').removeClass('hide');
                return false;
            }
            $('#login-form').submit();
        });

        var agent_user_id = 0;
        $('#select_agent').change(function(e,value){
            agent_user_id = value;
        });

        $('#agent_user_login').click(function(){
            if(!agent_user_id){
                alert.show('还未选择要登录的开车精灵账户！');
                return false;
            }
            ajax.ajax('agent_login_in',{'user_id':agent_user_id},function(data){
                if(data.login_url){
                        window.location.href=data.login_url;
                }else{
                    alert.show('该用户已经过期或者尚未分配服务器，请联系管理员！');
                }
            });
        });
    };

    return {
        init:init
    }
});