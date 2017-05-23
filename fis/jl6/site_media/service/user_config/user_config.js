/**
 * Created by Administrator on 2015/10/7.
 */
define(['jl6/site_media/widget/ajax/ajax','jl6/site_media/widget/alert/alert',
       'jl6/site_media/widget/confirm/confirm'],
    function(ajax,alert,confirm){

    var init = function(){

        //点击编辑按钮
        $('.edit_agent').click(function(){
            removeAllClass();
            $(this).addClass('active');
            if($('#id_select_agent option').length>0){
                clear_hint();
                $('#id_name').val($.trim($('#id_select_agent').find("option:selected").text()));
                $('#id_password').val('');
                $('#id_repsd').val('');
                $('#agent_id').val($('#id_select_agent').val());
                $('#id_edit_box').fadeIn('fast');
                $('#id_name').focus();
            }else{
                add_agent($(this));
            }
        });

        //点击删除按钮
        $('.delete_agent').click(function(){
            removeAllClass();
            $(this).addClass('active');
            var name = $.trim($("#id_select_agent").find("option:selected").text());
            confirm.show({
                body:"确定删除您的代理用户["+name+"]吗？",
                okHide: function(){
                    ajax.ajax('delete_agent',{'agent_id':$('#id_select_agent').val()},function(data){
                        alert.show({
                            body:'代理用户删除成功',
                            hidden:function(){
                                window.location.reload();
                            }
                        });
                    });
                }
            });
        });

        //点击添加按钮
        $('.add_agent').click(function(){
            removeAllClass();
            $(this).addClass('active');
            clear_hint();
            $('#id_name').val('');
            $('#id_password').val('');
            $('#id_repsd').val('');
            $('#agent_id').val('');
        //  $('#id_edit_box').removeClass('hide');
            $('#id_edit_box').fadeIn('fast');
            $('#id_name').focus();
        });

        $('.show_msg').on('focus',function(){
            var id = '#'+$(this).attr('id')+'_hint';
            $(id).removeClass('hide');
        });

        $('.submit_agent').click(function(){
            var name = $.trim($("#id_name").val());
            var psd = $.trim($("#id_password").val());
            var repsd = $.trim($("#id_repsd").val());
            var agent_id = $("#agent_id").val();
            function base_check(){
                clear_hint();

                var name_hint = $('#id_name_hint');
                var psd_hint = $('#id_password_hint');
                var repsd_hint = $('#id_repsd_hint');

                if(name=='' || name == null){
                    change_hint(name_hint,0,'*用户名不能为空');
                    return false;
                }else if(len(name,1)<5 || len(name,1)>25){
                    change_hint(name_hint,0,'*代理用户名长度为'+len(name,1)+'，请'+(len(name,1)<5?'增加':'减少')+'字数');
                    return false;
                }else if(psd == null || psd == ''){
                    change_hint(psd_hint,0,'*密码不能为空');
                    return false;
                }else if(len(psd,0)<6 || len(psd,0)>25){
                    change_hint(psd_hint,0,"*密码长度为"+len(psd,0)+"，请"+(len(psd,0)<6?"增加":"减少")+"字数");
                    return false;
                }else if(psd!=repsd){
                    change_hint(repsd_hint,0,'*两次输入的密码不一致');
                    return false;
                }else{
                    return true;
                }
            }
            function new_name_check(){
                if(agent_id==''){
                    var op_list = $('#id_select_agent option');
                    for(var i=0;i<op_list.length;i++){
                        if(name==$(op_list[i]).text()){
                            clear_hint();
                            change_hint(name_hint,0,'*用户名不能和已有用户相同');
                            return false;
                        }
                    }
                    return true;
                }else{
                    return true;
                }
            }

            if(base_check() && new_name_check()){
                ajax.ajax('submit_agent',{'name':name,'password':psd,'agent_id':agent_id},function(data){
                    alert.show({
                        body:data.msg,
                        hidden:function(){
                            window.location.reload();
                        }
                    });
                });
            }
        });

        $('#id_select_agent').on('change',function(){
            $('#id_name').val($('#id_select_agent').find("option:selected").text());
        });
    };

    var removeAllClass = function(){
        $('#id_select_agent').parent().find('a.btn').removeClass('active');
    };

    var clear_hint = function(){
        name_hint = $('#id_name_hint');
        name_hint.addClass('hide');
        name_hint.text('用户名必须是淘宝网账号(5~25个字符)');
        name_hint.css('color','#666');
        psd_hint = $('#id_password_hint');
        psd_hint.addClass('hide');
        psd_hint.text('6~16个字符，建议使用字母加数字或符号的组合密码');
        psd_hint.css('color','#666');
        repsd_hint = $('#id_repsd_hint');
        repsd_hint.addClass('hide');
        repsd_hint.text('再输一次密码');
        repsd_hint.css('color','#666');
    };

    var add_agent = function(obj){
        removeAllClass();
        $(obj).addClass('active');
        clear_hint();
        $('#id_name').val('');
        $('#id_password').val('');
        $('#id_repsd').val('');
        $('#agent_id').val('');
    //  $('#id_edit_box').removeClass('hide');
        $('#id_edit_box').fadeIn('fast');
        $('#id_name').focus();
    }

    var change_hint = function(obj,status,msg){
        $(obj).removeClass('hide');
        $(obj).css('color',status?'#4B4':'#F00');
        $(obj).text(msg);
    }

    var len = function(str,type) {
        var l = 0;
        for(var i=0;i<str.length;i++){
            if(str[i].charCodeAt(0)<299){
                l++;
            }
            else{
                if(type==1){
                    l+=2;
                }
                else{
                    return -1;
                }
            }
        }
        return l;
    }

    return {
        init:function(){
            init();
        }
    }
});