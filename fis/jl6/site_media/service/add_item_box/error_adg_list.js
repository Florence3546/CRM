/**
 * Created by Administrator on 2015/10/16.
 */
define(["template"], function(template) {

    var setError = function(obj,options){
        var html,tpl=__inline("error_adg_list.html");
            html = template.compile(tpl)(options);

        var sign_icon = '<a href="javascript:;" class="red" data-container="body" data-toggle="popover" data-placement="top"  id="show_error_msg" data-content="">查看详情</a>';
        obj.html(sign_icon);

        $("#show_error_msg").popover({trigger:'click',html:true,content:html });
    };

    return {
        setError:setError
    }
});