﻿var Dajax = {
//		send_dajax:function(model,argv){
//			this.dajax_call(model,'route_dajax',argv);
//	},
	dajax_call: function(app,fun,argv){
		if(typeof(PTQN)=='undefined'){
			argv.csrfmiddlewaretoken = $.cookie('csrftoken');
		}else{
			argv.csrfmiddlewaretoken = PTQN.cookie('csrftoken');
		}
		$.post('/dajax/'+app+'.'+fun+'/', argv, function(data){ 
			function clear_quotes(arg){
				return arg.replace(new RegExp('"', 'g'),'\\"');
			} 
			
			$.each(data, function(i,elem){
				switch(elem.cmd){
					case 'alert':
						alert(elem.val);
					break;

					case 'data':
						eval( elem.fun+"(elem.val);" );
					break;

					case 'as': 
						elem.val = clear_quotes(elem.val);
						eval( "jQuery.each($(\""+elem.id+"\"),function(){ this."+elem.prop+" = \""+elem.val+"\";});");
					break;

					case 'addcc':
						jQuery.each(elem.val,function(){
				 			eval( "$('"+elem.id+"').addClass(\""+this+"\");" );
						});
					break;
					
					case 'remcc':
						jQuery.each(elem.val,function(){
				 			eval( "$('"+elem.id+"').removeClass(\""+this+"\");" );
						});
					break;
					
					case 'ap':
						elem.val = clear_quotes(elem.val);
						eval( "jQuery.each($(\""+elem.id+"\"),function(){ this."+elem.prop+" += \""+elem.val+"\";});");
					break;
					
					case 'pp':
						elem.val = clear_quotes(elem.val);
						eval( "jQuery.each($(\""+elem.id+"\"),function(){ this."+elem.prop+" = \""+elem.val+"\" + this."+elem.prop+";});");
					break;
					
					case 'clr':
						eval( "jQuery.each($(\""+elem.id+"\"),function(){ this."+elem.prop+" = \"\";});");
					break;
					
					case 'red':
				 		window.setTimeout('window.location="'+elem.url+'";',elem.delay);
					break;
					
					case 'js': 
				 		eval(elem.val);
					break;
					
					case 'rm':
				 		eval( "$(\""+elem.id+"\").remove();");
					break;
					
					default:
						alert('Unknown action!');
				}
			});
		}, "json");
	}
};