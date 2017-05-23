// JavaScript Document
define(['jquery'],function($){
    $.fn.scrolList = function(options){
        //默认配置
        var defaults = {
            speed:40,  //滚动速度,值越大速度越慢
            rowHeight:24, //每行的高度
            showCount:6 //默认显示多少条
        };

        var opts = $.extend({}, defaults, options),intId = [];
        function marquee(obj, step){
            obj.find("ul").animate({marginTop: '-=1'},0,function(){
                var s = Math.abs(parseInt($(this).css("margin-top")));
                if(s >= step){
                    $(this).find("li").slice(0, 1).appendTo($(this));
                    $(this).css("margin-top", 0);
                }
            });
        }
		$(this).each(function(i){
			var sh = opts["rowHeight"],speed = opts["speed"],_this = $(this);
			intId[i] = setInterval(function(){
				if(this.find('ul li').length<=opts.showCount){
					clearInterval(intId[i]);
				}else{
					marquee(_this, sh);
				}
			}, speed);
		});
	}
});