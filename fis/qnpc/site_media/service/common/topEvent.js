define([ '../../widget/ajax/ajax', '../../widget/loading/loading'], function(ajax, loading){

    var init = function(){
        $('.open_qnpc_feedback_dialog').click(function(){
            $('#feedback_modal_dialog').modal("show");
        });

        /**
         * 全店数据下载
         */
        $('#sync_increase_data').click(function() {
            loading.show('正在下载全店数据，请稍候...');
            ajax.ajax('sync_data',{}, function(){
                loading.hide();
                $.confirm({
                    title:'提示',
                    body: '数据下载成功，即将刷新页面',
                    okBtn: '确定',
                    cancelBtn : '取消',
                    okHide:function(){
                        window.location.reload();
                    }
                })
            });
        });

        /**
         * 提交意见反馈
         */
        $('#submit_suggest').click(function(){
            var content = $('#id_content').val();
            if(content&&content.trim()!=''){
                $('#feedback_modal_dialog').modal("hide");
                loading.show('请稍候...');
                ajax.ajax('add_suggest',{'suggest':content.trim() }, function(){
                    loading.hide();
                    $.alert({
                        title:'精灵提醒',
                        body: '提交成功，感谢您的参与！我们会及时处理您的意见！',
                        hasfoot:false
                    })
                });
            }else{
                $.alert({
                    title:'精灵提醒',
                    body: '亲!还未输入反馈内容!',
                    hasfoot:false
                })
            }
        });
    };

    return {
        init: init
    }
});