var Dajax = Class.create();
Dajax.prototype = {
	
	initialize: function( pre ){
		this.dajax_prefix = pre;
	},
	
{% for f in dajax_js_functions %}
	{{f.0.0}}_{{f.1}}: function(argv){
		this.dajax_call('{{f.0.1}}','{{f.1}}',argv);
	},
{% endfor %}
	
	dajax_call: function(app,fun,argv)
	{
		new Ajax.Request('/'+this.dajax_prefix+'/'+app+'.'+fun+'/', { method:'post', parameters: argv,
			onSuccess: function(transport){
				a = transport.responseText.evalJSON();
				
				function clear_quotes(arg){
					return arg.replace(new RegExp('"', 'g'),'\\"');
				}
				a.each(function(elem){
				switch(elem.cmd){
				case 'alert':
					alert(elem.val)
				break;
				
				case 'data':
					eval( elem.fun+"(elem.val);" );
				break;

				case 'as':
					elem.val = clear_quotes(elem.val);
					eval( "$$(\""+elem.id+"\").each(function(e){e."+elem.prop+" = \""+elem.val+"\";});");
				break;

				case 'addcc':
					elem.val.each(function(cssclass){
				 		eval( "$$('"+elem.id+"').each(function(e){ e.addClassName(\""+cssclass+"\");});" );
					});
				break;

				case 'remcc':
			 		elem.val.each(function(cssclass){
						eval( "$$('"+elem.id+"').each(function(e){ e.removeClassName(\""+cssclass+"\");});" );
					});
				break;

				case 'ap':
					elem.val = clear_quotes(elem.val);
			 		eval( "$$(\""+elem.id+"\").each(function(e){e."+elem.prop+" += \""+elem.val+"\";});");
				break;

				case 'pp':
					elem.val = clear_quotes(elem.val);
			 		eval( "$$(\""+elem.id+"\").each(function(e){e."+elem.prop+" = \""+elem.val+"\"+e."+elem.prop+";});");
				break;

				case 'clr':
			 		eval( "$$(\""+elem.id+"\").each(function(e){e."+elem.prop+" = \"\";});");
				break;

				case 'red':
			 		window.setTimeout('window.location="'+elem.url+'";',elem.delay);
				break;

				case 'js':
			 		eval(elem.val);
				break;

				case 'rm':
			 		eval( "$$(\""+elem.id+"\").each(function(e){e.remove();});");
				break;

				default:
					alert('Unknown action!');
				}
			}.bind(this));

		},
			onFailure: function(){ alert('Something went wrong...') }
		});
	}
};

Dajax = new Dajax('{{DAJAX_URL_PREFIX}}');
