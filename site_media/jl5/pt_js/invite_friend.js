PT.namespace('InviteFriend');

PT.InviteFriend = function(){

    var init_copy=function(){
        clip = new PT.ZeroClipboard.z.Client();
        clip.setHandCursor(true);
        clip.addEventListener('complete', function (client, text) {
            PT.alert('复制成功','您可以使用Ctrl+V 粘贴到其他地方。');
            PT.sendDajax({'function':'web_behavior_only','data':'copy_btn'});
        });
        clip.addEventListener('mouseOver', function (client) {
            clip.setText($('#id_content').text());
        });
        clip.glue('button_copy');
        $('.tips').tooltip();
        
        $('.btn_shop_copy_0').zclip({
            path:'/site_media/jl5/plugins/zclip/ZeroClipboard.swf',
            copy:function(){  
            	if($('.txt_aliww_0').val() == '')
            		return ''
            	else
            		return $('#id_content').text();	 
            },
            afterCopy:function(){
            	var copy_text = $('.txt_aliww_0').val();
            	if(copy_text == ''){	
            		PT.alert('请先输入店铺掌柜ID！');
        		}else{      
        			PT.sendDajax({
			            'function': 'web_promotion_4shop',
			            'invited_name' :copy_text,
			            'callback': 'PT.InviteFriend.invied_4shop_callback'
			        });
        			$('.txt_aliww_0').attr({"disabled":"disabled"});     		
        		}
            }
        });
        
    }

	var init_event = function(){
	        
        $('#btn_add_new').on('click',function(){            
        	var len = $('#shop_table tr').length;  	       	
            var new_row = '<tr>' +
			                '<td class="pl10">' +
			                '<input type="text" class="span4 mr5 txt_aliww_' + len + '" placeholder="请输入店铺掌柜ID">' +
			                '<button class="btn btn-primary btn_shop_copy_' + len + '" >复制推荐文本</button>' +
			                '<label class="box_r f16 mr20 mt5"></label>' +
			                '</td>' +
			                '</tr>';            
            $('#shop_table tr:first').before(new_row);   
	        $('.btn_shop_copy_' + len).zclip({
	            path:'/site_media/jl5/plugins/zclip/ZeroClipboard.swf',
	            copy:function(){		
	            	if($('.txt_aliww_' + len).val() == '')
	            		return ''
	            	else
	            		return $('#id_content').text();
	            },
	            afterCopy:function(){	            	
	            	var copy_text = $('.txt_aliww_' + len).val();
	            	if(copy_text == ''){	
	            		PT.alert('请先输入店铺掌柜ID！');
            		}else{
	            		PT.sendDajax({
				            'function': 'web_promotion_4shop',
				            'invited_name' :copy_text,
				            'callback': 'PT.InviteFriend.invied_4shop_callback'
				        });
	            		$('.txt_aliww_' + len).attr({"disabled":"disabled"});          			
            		}
	            }
	        });
        });	
	
	}

    return {
        init:function(){
            init_event();
            init_copy();
        },
        invied_4shop_callback:function(json){
         	if (json.error_msg)
                PT.alert(json.error_msg);
            else
        		PT.alert('指定店铺名推荐链接复制成功，赶快发给好友吧，更多优惠等着你。');
        }        
    }

}();
