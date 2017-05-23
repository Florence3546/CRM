define(["jquery"],function(jQuery) {
    "use strict";

    jQuery.prototype.serializeObject=function(){
        var obj=new Object();
        $.each(this.serializeArray(),function(index,param){
            if(!(param.name in obj)){
                obj[param.name]=param.value;
            }
        });
        return obj;
    };
});
