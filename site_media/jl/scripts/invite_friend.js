PT.namespace('InviteFriend');

PT.InviteFriend = function(){

	var init_badu_share=function(){
		window._bd_share_config={
				"common":{"bdSnsKey":{},
					"bdDesc":$('#id_content').val(),
					"bdText":$('#id_content').val(),
					"bdMini":"2",
					"bdMiniList":[],
					"bdPic":"",
					"bdUrl":"http://fuwu.taobao.com/ser/detail.htm?spm=a1z13.1113643.51052018.55.nksCaT&service_code=ts-25811&tracelog=category&scm=1215.1.1.51052018&ppath=&labels=",
					},
				"share":{"bdSize":24}
			};
		with(document)0[(getElementsByTagName('head')[0]||body).appendChild(createElement('script')).src='http://bdimg.share.baidu.com/static/api/js/share.js?v=89860593.js?cdnversion='+~(-new Date()/36e5)];
	}
	
	var init_dom=function(){
		$(document).on('blur','#id_content',function(){
			window._bd_share_config.share.bdText=$(this).val();
		});
	}

	var init_copy=function(){
		clip = new PT.ZeroClipboard.z.Client();
		clip.setHandCursor(true);
		clip.addEventListener('complete', function (client, text) {
			//debugstr("Copied text to clipboard: " + text );
			PT.light_msg('复制成功','您可以使用Ctrl+V 粘贴到其他地方。');
			PT.sendDajax({'function':'web_behavior_only','data':'copy_btn'});
		});
		clip.addEventListener('mouseOver', function (client) {
			clip.setText($('#id_content').val());
		});
		clip.glue('button_copy');
	}
	
	return {
		init:function(){
			//init_dom();
			init_copy();
			//init_badu_share();
		},
	}
	
}();
