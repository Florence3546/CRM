PT.namespace("SysDefaultBind")
PT.SysDefaultBind = function(){
	// 加载fancybox取消事件
	$('.fancybox_cancel').click(function(){
		$.fancybox.close();
	});
	
	return {
	}	
}();
