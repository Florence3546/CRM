var Dajax = {
  	{% for f in dajax_js_functions %}
		{{f.0.0}}_{{f.1}}: function(argv){
			this.dajax_call('{{f.0.1}}','{{f.1}}',argv);
		},
	{% endfor %}
	
	dajax_call: function(app,fun,argv)
	{
		$.post('/{{DAJAX_URL_PREFIX}}/'+app+'.'+fun+'/', argv,
			function(data){
				
				function clear_quotes(arg){
					return arg.replace(new RegExp('"', 'g'),'\\"');
				}
				
				$.each(data, function(i,elem){
					switch(elem.cmd)
					{
						case 'alert':
							alert(elem.val)
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