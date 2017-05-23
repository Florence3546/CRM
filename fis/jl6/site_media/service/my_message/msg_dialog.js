define(["require","template",'widget/alert/alert','widget/ajax/ajax','widget/templateExt/templateExt','../common/poster_store'], function(require,template,alert,ajax,_,store) {
    "use strict";

    var modalTpl,
        tableTpl,
        obj;

    modalTpl = __inline('msg_dialog.html');
    tableTpl = __inline('msg_list.html');

    var show=function(){
        var html = template.compile(modalTpl)();
        template.config('escape', false);
        obj=$(html);
        $('body').append(obj);
        obj.modal();
        obj.on('shown.bs.modal',function(){
            getData(1);
        });
        obj.on('hidden.bs.modal',function(){
            obj.remove();
        });
        obj.on('click','.close_msg',function(){
            var obj = $(this);
            var msg_id = obj.attr("data");
            ajax.ajax('read_message',{msg_id:msg_id},function(data){
                if(data.errMsg == ''){
                    $('#lbl_read_' + msg_id).removeClass('label-primary').addClass('label-default').text('已读');
                    var msg_count = parseInt($('#msg_count').text());
                    if(msg_count > 0){
                        msg_count --;
                        $('#msg_count').text(msg_count);
                        obj.removeClass('close_msg');
                        store.setUnreadCount(msg_count);
                    }
                }
            });
        });
    }

    var getData=function(page){
        ajax.ajax('get_message_list',{page:page},function(data){
            layoutTable(data.msg_list);
            layoutPageBar(data.page_info);
        });
    }

    var layoutTable = function(data){
        var html = template.compile(tableTpl)({list:data});
        obj.find('.content').html(html);
    }

    var layoutPageBar = function(data){
        require(['widget/pageBar/pageBar'],function(pageBar){
            var dom = pageBar.show({
                data:data,
                onChange:function(page){
                    getData(page)
                }
            });
            if(data.record_count>0)
                obj.find('.page').html(dom);
            else
                obj.find('.page').html('<span>暂无私信</span>');
        });
    }

    return {
        show: show
    }
});
