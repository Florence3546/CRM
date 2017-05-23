/*!
 * ADD keyword spider
 * by:Zhong JinFeng
 * date:2013/5/21
 */
PT.namespace('aks');
PT.aks.base_src=("https:"==document.location.protocol?"https://":"http://")+'suggest.taobao.com/sug?code=utf-8&_ksTS=1377958014711_11799&k=1&area=c2c&bucketid=7&q=';
PT.aks.data_arr=new Array;
PT.aks.success_count=0;
PT.aks.delay=1000;
PT.aks.keyword_count=0;
PT.aks.fail_over=1;
PT.aks.ajax_count=0;
PT.aks.monitor_time=100;
PT.aks.keyword_list=new Array;
PT.aks.sign='^^';

PT.aks.send_request=function(keyword){
	var sart_url=this.base_src+keyword;
	var that=this,i;
	var data_str='';
	var data_obj={};
	this.ajax_coun++;
	try{
		$.ajax({
		   async:false,
		   url: sart_url,
		   type: "GET",
		   dataType: 'jsonp',
		   timeout: 5000,
		   success: function (json){
			   for(var i=0;i<json.result.length;i++){
			   	   if(json.magic!=undefined){
			   	   	   if(i<json.magic.length){
			   	   		   data_str+=''+json.result[i][0]+':'+json.magic[i]['list']+';';
			   	   		}else{
					   	   data_str+=''+json.result[i][0]+'",';			   	   
			   	   		}
			   	   }else{
					   data_str+=''+json.result[i][0]+'",';			   	   
			   	   }
				}
				data_obj[keyword]=data_str;
				that.data_arr.push(data_obj);
				that.success_count++;
			},
			error: function(xhr){
				throw Error('网络受限制');
			}
		})
	}catch(ex){
		throw Error(ex);
	}
}

PT.aks.monitor=function(){
	this.timer=setInterval(function(){
		var that=PT.aks;
		if(that.success_count>=(that.keyword_count*that.fail_over) || that.keyword_count==0||that.ajax_count>=that.keyword_count){
			that.send_result();
			clearInterval(that.timer);
			return;
		}	
		},this.monitor_time);
}

PT.aks.get_keyword_arr=function(){
	for (i=0;i<this.keyword_count;i++){
		this.send_request(this.keyword_list[i]);
	}
	return this.data_arr;
}

PT.aks.start=function(){
	//获取关键词列表
	//console.log('Spider_start');
	PT.sendDajax({'function':'web_get_new_spider_list'});
}

PT.aks.set_task=function(keyword_list){
	//获取关键词列表
	this.keyword_list=keyword_list;
	this.keyword_count=keyword_list.length;
	if(this.keyword_count==0 || this.keyword_count==undefined){
		return;
	}
	//开始抓词
	this.get_keyword_arr();
	//开启监控
	this.monitor();
}

PT.aks.send_result=function(){

	sendData = [];
	
	//sendData.push({id:2323,item_id:23423})
	for (var i=0,i_end=this.data_arr.length;i<i_end;i++){
		for (k in this.data_arr[i]){
			kw_dict={};
			kw_dict[k]=this.data_arr[i][k];
//			sendData+='"'+k+'":['+this.data_arr[i][k]+'],';
			sendData.push(kw_dict);
			}	
	}
	//sendData='({'+sendData+'})';
	
	PT.sendDajax({'function':'web_get_new_spider_result','data':$.toJSON(sendData)});
}