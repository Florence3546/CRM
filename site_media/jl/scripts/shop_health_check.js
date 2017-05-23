PT.namespace('HealthCheck');
PT.HealthCheck = function () {

    var init_table = function() {

        /* Formating function for row details */
        function fnFormatDetails ( oTable, nTr )
        {
           /* var aData = oTable.fnGetData( nTr );
            var sOut = '<table>';
            sOut += '<tr><td>Platform(s):</td><td>'+aData[2]+'</td></tr>';
            sOut += '<tr><td>Engine version:</td><td>'+aData[3]+'</td></tr>';
            sOut += '<tr><td>CSS grade:</td><td>'+aData[4]+'</td></tr>';
            sOut += '<tr><td>Others:</td><td>Could provide a link here</td></tr>';
            sOut += '</table>';*/
             
            return 'aaaaa';
        }

        /*
         * Insert a 'details' column to the table
         */
        var nCloneTh = document.createElement( 'th' );
        var nCloneTd = document.createElement( 'td' );
        nCloneTd.innerHTML = '<span class="row-details row-details-close"></span>';
         
        $('#dangerous_items thead tr').each( function () {
            this.insertBefore( nCloneTh, this.childNodes[0] );
        } );
         
        $('#dangerous_items tbody tr').each( function () {
            this.insertBefore(  nCloneTd.cloneNode( true ), this.childNodes[0] );
        } );
         
        /*
         * Initialse DataTables, with no sorting on the 'details' column
         */
        var oTable = $('#dangerous_items').dataTable( {
            "aoColumnDefs": [
                {"bSortable": false, "aTargets": [ 0 ] }
            ],
            "aaSorting": [[1, 'asc']],
             "aLengthMenu": [
                [5, 15, 20, -1],
                [5, 15, 20, "All"] // change per page values here
            ],
            // set the initial value
			// "iDisplayLength": 10,
			"bPaginate":false,
			"bInfo":false,
			"bRetrieve": true,
			"sDom":""
        });
         
        /* Add event listener for opening and closing details
         * Note that the indicator for showing which row is open is not controlled by DataTables,
         * rather it is done here
         */
        $('#dangerous_items').on('click', ' tbody td .row-details', function () {
            var nTr = $(this).parents('tr')[0];
            if ( oTable.fnIsOpen(nTr) )
            {
                /* This row is already open - close it */
                $(this).addClass("row-details-close").removeClass("row-details-open");
                oTable.fnClose( nTr );
            }
            else
            {
                /* Open this row */                
                $(this).addClass("row-details-open").removeClass("row-details-close");
                oTable.fnOpen( nTr, fnFormatDetails(oTable, nTr), 'details' );
            }
        });
    }
	
	var init_health_check = function(){
		$("#link_health_check").on(
			"click",function(){
				$("#shop_report").hide();
				$("#shop_analysis").hide();
				
				
				
				
				
				
				$("#health_check").show();
			}
		)
	}
	
	var init_shop_report = function(){
		$("#link_shop_report").on(
			"click",function(){
				$("#health_check").hide();
				$("#shop_analysis").hide();
				//PT.sendDajax({'function':'web_get_shop_report','shop_id':68131155});
				
				
				
				
				$("#shop_report").show();
			}
		)
	}
	
	var init_shop_analysis = function(){
		$("#link_shop_analysis").on(
			"click",function(){
				$("#health_check").hide();
				$("#shop_report").hide();
				
				
				
				
				
				$("#shop_analysis").show();
			}
		)
	}
	
	var excute_check = function(){
		// 执行健康检查按钮事件
		$("#excute_health_check").on(
			"click",function(){
				$("#welcome_health_check").hide();
				$("#health_check").css("padding-top","0");
				PT.sendDajax({'function':'web_get_health_check','obj_id':$("#shop_id").val(),'check_type':'shop','flag':0});
				$("#show_check_result").hide();
				$("#loading").show();
			}
		)
	}
	
	var init_recheck = function(){
		$("#re_health_check").on(
			"click",function(){
				$("#progress_bar").css('width','0%');
				$("#health_check").css("padding-top","0");
				$("#welcome_health_check").hide();
				$("#progrss_top").html('');			
				PT.sendDajax({'function':'web_get_health_check','obj_id':$("#shop_id").val(),'check_type':'shop','flag':1});
				$("#show_check_result").hide();
				$("#loading").show();
			}
		)	
	}
	
    return {

        //main function to initiate the module
        init: function () {
            
            if (!jQuery().dataTable) {
                return;
            }  
			
			init_health_check();
			init_shop_report();
			init_shop_analysis();
			excute_check();  //立即诊断按钮的监听事件
			
			
			init_recheck();
        },
		set_report_result:function(data){
			$('#shop_health_check').hide();
			rpt_str = ''
			if (data.mng != null){
				rpt_str = '<div><h1>'+data.mng+'</h1></div>';
			} else {
				rpt_str = template.render('rpt_template', data);
			}
			$('#rpt_small_table').html(rpt_str);
			$('#show_shop_report').show();
		},
		set_progress_bar:function(data){
			// 设置进度条进度
			// alert(data.descr);
			$("#load_info").html(data.descr);
			$("#progress_bar").animate({'width':data.range+'%'},150);
			if (data.range != '100'){
				setTimeout(function(){PT.sendDajax({'function':'web_get_progress_size','cache_key':data.cache_key});},100);
			}
		},
		set_progress_top:function(shop_id,data){
			// 设置进度条的上方布局
			var html_content = template.render('progress_top_template', {'data':data});
			$('#progrss_top').html(html_content);
			$("#show_health_check").show();
			PT.sendDajax({'function':'web_get_progress_size','cache_key':'shop_'+shop_id});
		},
		set_check_result:function(data_dict){
			template.isEscape = false;
			$("#progress_bar").animate({'width':'100%'},600);
			$("#loading").hide();
			
			var	total = data_dict.dangerous_items.length + data_dict.safe_items.length;
			// 设置检查总数量及各类型数量
			$("#items_total").text(data_dict.total);
			$("#items_dangerous").text(data_dict.dangerous_items.length);
			$("#items_safe").text(parseInt(data_dict.total)-data_dict.dangerous_items.length);						
			
			// 渲染危险健康检查选项
			if (data_dict.dangerous_items.length > 0){
				$("#no_dangerous_items").hide();
				$("#dangerous_items_div").html(template.render('dangerous_table_template',{"items":data_dict.dangerous_items}));	
				init_table();
			} else {
				$("#no_dangerous_items").show();
			}
			
			// 渲染安全健康检查选项
			temp_html = "";
			for(var i = 0 ; i < data_dict.safe_items.length ; i++){
				temp_html += template.render('safe_items_template',{"item_dict":data_dict.safe_items[i]});
			}
			$("#safe_items_div").html(temp_html);
			
			$("#show_check_result").show();
		},
		show_check_info:function(obj){
			var content_obj = $(obj).parent().parent().next();
			if($(content_obj).is(":hidden")){  
				$(content_obj).show();
				$(obj).children().attr('src','/site_media/assets/img/portlet-collapse-icon.png');
			} else {
				$(content_obj).hide();
				$(obj).children().attr('src','/site_media/assets/img/portlet-expand-icon.png');								
			}
		},
		get_rpt_data:function(){
			alert('get_rpt_data');	
		}
    };

}();

