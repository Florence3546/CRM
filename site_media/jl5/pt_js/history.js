PT.namespace('History');
PT.History = function () {
    var extend_node = function (obj) {
	    obj.removeClass('collapse').addClass('extend');
	    obj.nextUntil('.timeline-year').slideDown('slow');
    };
    
    var collapse_node = function (obj) {
        obj.removeClass('extend').addClass('collapse');
        obj.nextUntil('.timeline-year').slideUp('slow');
    };
    
    var init_dom = function () {
	    $('.timeline').on('click', '.timeline-year.collapse .node', function () {extend_node($(this).closest('.timeline-year'));});
	    $('.timeline').on('click', '.timeline-year.extend .node', function () {collapse_node($(this).closest('.timeline-year'));});
    };
    
	var init = function () {
		init_dom();
		extend_node($('.timeline .timeline-year:lt(2)'));
	};
	
	return {
		init: init
	};
}();