define(["template"], function(template) {
    "use strict";

    var config, tpl,count=0;

    tpl = __inline('tpl.html');

    config = {
        title:'提醒',
        style: 'default',
        body:null,
        timeout: 5000,
        close:false
    }

    var lithtMsg = function(options) {
        if ("string" == typeof options) {
            this.options = $.extend({}, config, {
                body: options
            });
        } else {
            this.options = $.extend({}, config, options);
        }
    }

    lithtMsg.prototype.show=function(){
        var html,obj,is_show=true;
        template.config('escape', false);
        html = template.compile(tpl)(this.options);
        obj=$(html);

        if(this.options.style=='bottom'){
            obj.css('marginBottom',count*(57+20));
        }else{
            obj.css('marginTop',count*(57+20));
        }


        count++;

        $('body').append(obj);

        obj.focus();

        obj.addClass('active');

        if(!this.options.close){
            setTimeout(function(){
                is_show=false;
                obj.removeClass('active');
            },this.options.timeout);
        }

        obj.on($.support.transition.end,function(){
            if(is_show==false){
                count--;
                obj&&obj.remove();
            }
        });

        obj.on('click','.close_light_msg',function(){
            is_show=false;
            obj.removeClass('active');
        });
    }

    var show=function(options){
        var lm=new lithtMsg(options);
        lm.show();
    }

    return {
        show:show
    }
});
