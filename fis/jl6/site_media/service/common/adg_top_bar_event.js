define(['common','../report_detail/report_detail'],function(common,report_detail){

    var inited=false;

    var init=function(){

       	//避免重复执行
        if(inited){
            return false;
        }

        inited=true;

        // 同步宝贝数据
        $('#id_sync_adg_data').on('click', function(){
            common.loading.show("正在同步当前宝贝");
            var adgroup_id =
            common.sendAjax.ajax('sync_current_adg', {'adg_id': parseInt($(this).attr('adg_id')), 'camp_id': parseInt($(this).attr('camp_id'))},
                function (data) {
                    common.loading.hide();
                    if(data.msg!=undefined){
                        common.alert.show({
                            body:data.msg,
                            hidden:function(){
                                window.location.reload();
                            }
                        });
                    }
                }
            )
        });
        
        //宝贝报表明细
        report_detail.init();
        $('#adg_rpt_detail').click(function () {
            report_detail.show('宝贝明细：'+$('#adg_nav .adg_title>a').text(), 'adgroup', $('#shop_id').val(), null, $('#adgroup_id').val());
        });
    }

    return {
        init:init
    }
});
