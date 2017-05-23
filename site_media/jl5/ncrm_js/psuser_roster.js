PT.namespace('PSUserRoster');
PT.PSUserRoster = function() {
	
	var init_sort=function(){
		$('#id_psuser_table').dataTable({
		 	"bPaginate": false,
		 	"bFilter": false,
		 	"bInfo": false,
			"aaSorting": [[ 1, "desc" ]],
			"aoColumns": [
				{ "bSortable": true },
				{ "bSortable": true },
				{ "bSortable": true },
				{ "bSortable": true },
				{ "bSortable": true },
			]
		});
	};
	
    var init_dom = function() {
    	init_sort();
    	
    	$('#id_search_user').click(function(){
    		var search_text = $('#id_search_text').val();
    		var search_obj = $('#id_psuser_table>tbody>tr');
    		var filter_count = 0;
    		if(search_text!=''){
    			search_obj.each(function(){
        			if($(this).text().indexOf(search_text)!=-1){
        				$(this).removeClass('hide');
        				filter_count+=1;
        			}else{
        				$(this).addClass('hide');
        			}
        		});
    		}else{
    			search_obj.each(function(){
    				$(this).removeClass('hide');
    				filter_count+=1;
    			})
    		}
    		$('#id_psuser_count').text(filter_count);
    	});
    };

    return {
        init: function() {
            init_dom();
        },
    }
}();
