PT.namespace('Point');
PT.Point = function(){

//    var get_praise=function(){
//		PT.sendDajax({
//            'function': 'web_get_praise',
//            'callback': 'PT.Point.get_praise_callback'
//        });
//    }

    var init_dom=function() {
		$('#show_history_praise').zclip({
            path:'/site_media/jl5/plugins/zclip/ZeroClipboard.swf',
            copy:function(){
            	var temp;
				$.ajax({
					type:'post',
					async:false,
					url:'/dajax/web.route_dajax/',
					data:{'function':"get_praise",'auto_hide':0},
					dataType:'json',
					success:function(data){
						temp= $.parseJSON(data[0].val).data;
					}
				});				
			  	$('#div_msg').show();
        		$('#show_history_praise').html('换一条评语');
        		$('#div_content').html('"' + temp + '"');
				return temp;
			},
            afterCopy:function(){            
            	//PT.light_msg('复制成功','马上到后台全5分好评吧！');
            }
        });          		
    }
    
    return {
        init:function(){
        	init_dom();
        }
//        ,get_praise_callback:function(data){
//            if(data.msg!=''){                 
//            	PT.light_msg('精灵提示', data.msg);
//            }else{    
//	            $('#div_msg').show();
//				$('#show_history_praise').html('换一条评语');
//				$('#div_content').html(data.data);
//            }
//        }
    }

}();

