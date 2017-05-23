PT.namespace('WorkBenchSaler');
PT.WorkBenchSaler = function() {

	var init_dom = function() {
   	
    	$('.show_more_content').click(function(){
    		var pos = parseInt($(this).attr('position'));
    		if(pos>0){
    			$(this).siblings().removeClass('hide');
    			$(this).text('收起');
    			$(this).attr('position', -1);
    		}else{
    			$(this).siblings().addClass('hide');
    			$(this).text('展开');
    			$(this).attr('position', 1);
    		}
    	});
    	
        $('.tips').tooltip();
    };

    return {
        init: function() {
            init_dom();
        },
    }
}();
