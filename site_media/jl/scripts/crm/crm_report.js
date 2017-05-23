PT.namespace('CrmReport');
PT.CrmReport = function () {

	var init_dom=function(){
		$('#base_cat_id').change( function(){
		  var cat_id=$(this).val();
		  PT.sendDajax({'function':'crm_get_group_8catid','cat_id':cat_id,'back_str':'CrmReport.'});
		});
		
		$('#base_consult_group_id').change( function(){
		  var group_id=$(this).val();
		  if (group_id>0) {
		  	$('#assign_consult').parent().show();
		  } else {
		  	$('#assign_consult').parent().hide();
		  }
		  // PT.sendDajax({'function':'crm_get_consult_8groupid','group_id':group_id,'back_str':'CrmReport.'});
		});
	}

	return {
		init:function(){
			PT.Base.set_nav_activ(5);
			init_dom();
			$('#base_cat_id').change();
		},
		get_group_back:function (group_list) {
		  var obj = $('#base_consult_group_id'),option_str="<option value=''>---------</option><option value='0'>未分配</option>";
		  for(var i=0;i<group_list.length;i++) {
		    option_str+="<option value='"+group_list[i]['id']+"'>"+group_list[i]['name']+"</option>";
		  }
		  $(obj).html('').prepend(option_str).val('').change();
		},
		
		get_consult_back:function (consult_list,cat_dict) {
		  var obj = $('#base_consult_id'),option_str="<option value=''>---------</option>",tips="",consult_val=0;
		  for(var i=0;i<consult_list.length;i++) {
			if(i==0){
				option_str+="<option value='0'>未分配</option>"
			}
			option_str+="<option value='"+consult_list[i]['id']+"'>"+consult_list[i]['name']+"</option>";
		  }
		  $(obj).html('').prepend(option_str).val('');
		  for(var k in cat_dict){
		    tips+="<div class='tal'>"+cat_dict[k]+'</div>';
		  }
		  $('#group_tips').attr('data-original-title',tips);
		  App.initTooltips();
		}
	}
}()