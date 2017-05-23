require(['require','site_media/plugins/jquery/jquery.min','site_media/plugins/sui/js/sui.min'], function(require, $, sm) {

    var current_model = $('.page').attr('id');

    for (var p in requirejs.s.contexts._.config.paths){

        var modalList= p.split('/');
        if(p.indexOf('service')!=-1&&modalList.slice(-1)==current_model){

            require([p], function(X) {
                X.init();
            });
            break;
        }
    }

    $(document).ready(function() {
        require(['site_media/service/common/common'], function(common) {
            common.init();
        });

        require(['site_media/service/common/topEvent'], function(topEvent){
            topEvent.init();
        });

        require(['site_media/plugins/qn'],function(QN){
            $('.call_wangwang').on('click',function(){
                var nick="派生科技";
                QN.wangwang.invoke({
                     category: 'wangwang',
                     cmd: 'chat',
                     param: {'uid':"cntaobao"+nick},
                     success: function (rsp) {
                        QN.wangwang.invoke({
                            "cmd": "insertText2Inputbox",
                            "param": {
                               uid:"cntaobao"+nick,
                               text:"\\C0x0000ff\\T来自千牛pc版：",
                               type:1
                            }
                        });
                         return false;
                     },
                     error: function (msg) {
                        PT.alert('打开失败,请联系['+nick+']');
                     }
                 });
            });

            if (typeof(workbench)==='undefined'){
              $('.dashboard-date-range').css('backgroundColor','#74b9e1');
              $('.btn.custom').css('backgroundColor','#74b9e1');
              $('#main-nav').css('background','url(http://gtms04.alicdn.com/tps/i4/T17w5xFr4dXXXt9EcX-1200-800.jpg) #74b9e1 0px -30px no-repeat');
            }else{
              QN.initTheme();
            }
        });

    });
});
