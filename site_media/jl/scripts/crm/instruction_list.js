PT.namespace('InstructionList');
PT.InstructionList = function(){
    
    var refresh_table = function(){
         $('#id_instrcn_table').dataTable({
            "bPaginate": false,
            "bFilter": false,
            "bInfo": false,
            "aaSorting": [[ 2, "desc" ]],
            "aoColumns": [
                { "bSortable": false },
                { "bSortable": true },
                { "bSortable": false },
                { "bSortable": true, "sType": "custom","sSortDataType": "custom-text"},
                { "bSortable": false },
                { "bSortable": true, "sSortDataType": "dom-text", "sType": "string"},
                { "bSortable": false }
            ]
        });
    };
    
    var genr_slider = function(){
        $('.scope_slider').slider({from:0, to:5, step:1, skin:'blue', scale:['|','有转化','有点击','有展现','无展现','新词'], round:1, limits:false});
    };
    
    var init_dom = function(){
        
        //refresh_table();
        
        $(document).off('click.PT.save_instrcn').on('click.PT.save_instrcn', '.save_instrcn', function(){
            var name = $(this).parent().parent().attr('tag_name');
            if((name==''|| name==undefined)){//如果是新的，配置项从输入框中取出
                var name = $('#id_new_instrcn').val();
            }
            var input_list = $(this).parent().parent().find('input.instrcn');
            var instruction = new Object();
            for(var i=0;i<input_list.length;i++){
                instruction[$(input_list[i]).attr('key_name')] = $(input_list[i]).val();
            }
            if(name!='' && name!=undefined){
                console.log(instruction);
                PT.sendDajax({'function':'crm_save_instruction', 'name':name, 'instrcn_detail':$.toJSON(instruction)});
            }else{
                PT.alert("指令尚未完整输入！");
                return false;
            }
        });
        
        $(document).off('click.PT.delete_instrcn').on('click.PT.delete_instrcn', '.delete_instrcn', function(){
            var delete_instruction = function(obj){
                var name = $(obj).attr('tag_name');
                if(name!=''&& name!=undefined){
                    var cb_obj = $(obj).find('input[type=checkbox]');
                    if($(cb_obj).attr('checked')=='checked'){
                        $(cb_obj).click();
                    }
                    PT.sendDajax({'function':'crm_delete_instruction', 'name':name});
                }
                $(obj).remove();
                $('#id_instrcn_count').text(parseInt($('#id_instrcn_count').text())-1);
            };
            PT.confirm("确定要删除当前指令吗？", delete_instruction, [$(this).parent().parent()]);
        });
        
        $(document).off('click.PT.add_new_instrcn').on('click.PT.add_new_instrcn', '#add_new_instrcn', function(){
           if($('#id_new_instrcn').length>0){
               return false;
           }
           var html =template.render('id_instruction_template', {'instrcn':{'scope':'0;5'}});
           $('#id_instrcn_table>tbody').prepend(html);
           genr_slider();
        });
        
        $(document).off('keypress.PT.search_instuction').on('keypress.PT.search_instuction', '#id_search_instrcn', function(e){
            var key=e.keyCode||e.which||e.charCode;
            switch(key){
                case 13:
                    var search_text = $(this).val();
                    var instrcn_selector = '#id_instrcn_table>tbody>tr';
                    if(search_text==''||search_text==undefined||search_text==null){
                       $(instrcn_selector).each(function(){
                          $(this).show(); 
                       });
                   }else{
                       $(instrcn_selector).each(function(){
                          if($(this).attr('tag_name').indexOf(search_text)!=-1){
                              $(this).show();
                          }else{
                              $(this).hide();
                          }
                       });
                   }
                   break;
            }
        });
        
        genr_slider();
        
        $(document).off('click.PT.check_instrcn').on('click.PT.check_instrcn', 'input[name=instrcn_checkbox]', function(){
	        if ($('#operate_optimize_keywords').length==0) {
		        $('#id_func_optimize_keywords a.add_operate').click();
	        }
	        var instruction_list = $.trim($('#id_instrcn_list_input').val());
	        instruction_list = instruction_list?$.trim($('#id_instrcn_list_input').val()).split(','):[];
		    var i = $.inArray(this.id, instruction_list);
	        if (this.checked && i==-1) {
			    instruction_list.push(this.id);
	        } else if (!this.checked && i!=-1) {
		        instruction_list.splice(i, 1);
	        }
			$('#id_instrcn_list_input').val(instruction_list.join());
        });
    };
    
    
    var bind_event = function(selector){
        init_dom();
        
        var selector = selector;
        $(document).off('click.PT.check_instrcn').on('click.PT.check_instrcn', 'input[name=instrcn_checkbox]', function(){
            
            function remove_instrcn(tag_name){
                var obj_list = $(editting_obj).find('li');
                for(var i=0;i<obj_list.length;i++){
                    if($(obj_list[i]).text() == tag_name){
                       $(obj_list[i]).remove(); 
                    }
                }
            }
            
            function add_instrcn(tag_name){
                var html = "<li>"+tag_name+"</li>";
                $(editting_obj).append(html);
            }
            
            var tag_name = $(this).attr('id');
            if(tag_name!=''&& tag_name!=undefined){
                var editting_obj = $(selector);
                if(editting_obj.length>0){
                    var is_in = $(editting_obj).text().indexOf(tag_name)!=-1?true:false;
                    if($(this).attr('checked') == 'checked'){
                        if(!is_in){add_instrcn(tag_name);}
                    }
                    else{
                        if(is_in){remove_instrcn(tag_name);}
                    }
                }
            }
        });
        
    };
    
    return {
        bind_event:bind_event,
        init_dom:init_dom,
        persistent_new_instrcn:function(){
            var tag_name = $('#id_new_instrcn').val();
            var obj = $('#id_new_instrcn').parent().parent();
            $(obj).find('td:eq(1) input').remove();
            $(obj).find('td:eq(0) input').attr('id', tag_name);
            $(obj).find('td:eq(1)').text(tag_name);
            $(obj).attr('tag_name', tag_name);
            $('#id_instrcn_count').text(parseInt($('#id_instrcn_count').text())+1);
        }
    };
    
}();
