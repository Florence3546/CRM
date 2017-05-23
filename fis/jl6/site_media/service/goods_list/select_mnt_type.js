/**
 * Created by Administrator on 2015/9/22.
 */
define(['jl6/site_media/widget/ajax/ajax','template'],function(ajax,template){

    var popover = function(obj,params,_callback){

        var html, tpl=__inline("select_mnt_type.html");
        var mnt_opt_type = params.mnt_opt_type?params.mnt_opt_type:0;
        html = template.compile(tpl)();
        if(obj.data('popover')){
            obj.popoverList('destroy');
        }
        obj.popoverList({
            trigger:'click',
            placement:'right',
            content:html,
            html:true,
            onChange:function(data){
                if(mnt_opt_type==data.value){
                    return false;
                }
                params.flag = data.value;
                ajax.ajax('update_single_adg_mnt',params,function(result){
                    _callback(result);
                },null,{'url':'/mnt/ajax/'})
            }
        });
        obj.data('popover',1);
        obj.on('shown.bs.popoverList',function(){
            $(obj).find('li').removeClass('active');
            $(obj).find('li[data-value='+mnt_opt_type+']').addClass('active');
        });
    };

    return {
        popover:popover
    }
});