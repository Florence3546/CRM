APP.controller("routeCtl",function($scope,$timeout){$(document).on("pageInit",function(e,pageId){$timeout(function(){$scope.$emit("qnydCtl."+pageId+"Data")},0),$("#main_bar>a").each(function(){var href=$(this).attr("data-href")||"";-1==href.indexOf(pageId)?($(this).attr("href",$(this).attr("data-href")),$(this).removeClass("active")):($(this).attr("href","#"),$(this).addClass("active"),document.title=$(this).attr("title"))})}),$(document).ready(function(){$(".select_days").each(function(){var self=this;$(this).find("select").on("change",function(){$(self).find(".text").text($(this).find(":checked").text()),$(self).trigger("change",[this.value])})}),$(".page").removeAttr("style"),$.init()})}),!function(){var inited=!1,get_series_4list=function(data){for(var series_list=[],i=0;i<data.length;i++)series_list.push({name:data[i].name,color:data[i].color,data:data[i].value_list});return series_list},drawChart=function(id,category_list,series_cfg_list){$("#"+id).length&&(lalal=new Highcharts.Chart({chart:{renderTo:id,type:"spline"},title:null,credits:{text:null},xAxis:{gridLineColor:"#ddd",gridLineDashStyle:"Dash",gridLineWidth:1,tickPosition:"inside",tickmarkPlacement:"on",labels:{rotation:30},categories:category_list},yAxis:{gridLineColor:"#ddd",gridLineDashStyle:"Dash",min:0,title:null},tooltip:{formatter:function(){for(var obj_list=lalal.series,result=this.x+"日 <br/>",i=0;i<obj_list.length;i++)obj_list[i].visible&&(result=result+obj_list[i].name+" "+obj_list[i].data[this.point.x].y+series_cfg_list[i].unit+"<br/>");return result}},series:get_series_4list(series_cfg_list),legend:{verticalAlign:"top",borderWidth:0}}))};APP.controller("homeCtrl",function($scope,$http,$filter){$scope.balance="--",$scope.$on("homeCtrl.homeData",function(){if(inited)return!1;inited=!0;var num;dateFilter=$filter("date"),$scope.day="0";var hidePreloader=function(){num++,2==num&&$.hidePreloader()};$scope.selectDays=function(day){var endDay=dateFilter(new Date,"yyyy-MM-dd"),startDay=dateFilter(new Date-864e5*Number(day),"yyyy-MM-dd");num=0,$.showPreloader(),$http.post("/qnyd/ajax/",{"function":"account",start_date:startDay,end_date:endDay}).success(function(data){for(var d in data.account_data_dict)$scope[d]=data.account_data_dict[d];hidePreloader()}),$http.post("/qnyd/ajax/",{"function":"show_chart",start_date:startDay,end_date:endDay}).success(function(data){var series_list=[],series_fields=["cost","pay","click","roi"];for(var i in data.chart_data.series_cfg_list){var series_item=data.chart_data.series_cfg_list[i];-1!=series_fields.indexOf(series_item.field_name)&&series_list.push(series_item)}drawChart("account_chart",data.chart_data.category_list,series_list),hidePreloader()}),$http.post("/qnyd/ajax/",{"function":"campaign_list",start_date:startDay,end_date:endDay}).success(function(data){$scope.campaign_list=data.json_campaign_list,hidePreloader()})},$http.post("/qnyd/ajax/",{"function":"balance"}).success(function(data){""==data.errMsg?$scope.balance=data.balance:$.alert(data.errMsg)}),$scope.selectDays(0),$scope.$emit("qnydCtl.getPhone")}),$scope.editCampaign=function(){var self=this,buttons1=[{text:"请选择",label:!0},{text:"修改日限额",bold:!0,onClick:function(){$scope.$emit("qnydCtl.editBudget",self.camp)}},{text:"参与推广",onClick:function(){$.confirm("您确定要参与推广吗？",function(){$http.post("/qnyd/ajax/",{"function":"set_online_status",mode:1,camp_id_list:[self.camp.campaign_id]}).success(function(data){""==data.errMsg?(self.camp.online_status="online",$.toast("操作成功")):$.alert(data.errMsg)})})}},{text:"暂停推广",color:"danger",onClick:function(){$.confirm("您确定要暂停推广吗？",function(){$http.post("/qnyd/ajax/",{"function":"set_online_status",mode:0,camp_id_list:[self.camp.campaign_id]}).success(function(data){""==data.errMsg?(self.camp.online_status="offline",$.toast("操作成功")):$.alert(data.errMsg)})})}}],buttons2=[{text:"取消",bg:"danger"}],groups=[buttons1,buttons2];$.actions(groups)}}),APP.controller("budgetCtl",function($scope,$http,$timeout){$scope.$on("budgetCtl.editBudget",function(event,camp){$.popup(".popup_edit_budget"),$timeout(function(){$scope.budget=camp.budget,$scope.is_smooth=camp.is_smooth,"20000000"==$scope.budget?($scope.is_limit=1,$scope.newBudget=50):($scope.is_limit=0,$scope.newBudget=camp.budget),$scope.submit=function(){var tempBudget;if(Number($scope.is_limit))tempBudget="20000000";else if(tempBudget=Number($scope.newBudget),tempBudget>99999||30>tempBudget)return $.alert("日限额的范围为30~99999"),!1;$http.post("/qnyd/ajax/",{"function":"set_budget",budget:tempBudget,camp_id:camp.campaign_id,use_smooth:0==$scope.is_smooth?!1:!0}).success(function(data){""==data.errMsg?(camp.budget=tempBudget,camp.is_smooth=$scope.is_smooth,$.toast("操作成功")):$.alert(data.errMsg),$.closeModal(".popup_edit_budget")})}},0)})}),APP.controller("phoneCtl",function($scope,$http){$scope.$on("phoneCtl.getPhone",function(){$scope.isneed_phone}),$scope.submit=function(){return isNaN($scope.phone)||!/^1[3|4|5|7|8]\d{9}$/.test($scope.phone)?($.alert("手机号码填写不正确！"),!1):void $http.post("/qnyd/ajax/",{"function":"submit_userinfo",phone:$scope.phone,qq:$scope.qq}).success(function(data){return data.errMsg?($.alert(data.errMsg),!1):($.toast("感谢您的支持"),void $.closeModal(".popup_phone"))})}})}(),!function(){var robSettings,inited=!1;APP.controller("robRankCtrl",function($scope,$http,$filter,$timeout){var refresh=!1;$(document).on("refresh","#rob_rank .pull-to-refresh-content",function(){refresh=!0,inited=!1,$scope.$emit("qnydCtl.rob_rankData",self.kw)}),$scope.$on("robRankCtrl.robRankData",function(){if(inited)return!1;inited=!0;var dateFilter=$filter("date");void 0==$scope.day&&($scope.day="0"),$scope.selectDays=function(day){var endDay=dateFilter(new Date,"yyyy-MM-dd"),startDay=dateFilter(new Date-864e5*Number(day),"yyyy-MM-dd");$scope.day=day,num=0,refresh?refresh=!1:$.showPreloader(),$http.post("/qnyd/ajax/",{"function":"rob_list",start_date:startDay,end_date:endDay}).success(function(data){$scope.keyword_list=data.keyword_list,$scope.errMsg=data.errMsg,$scope.keyword_list.length?$scope.batchRobRank():$.hidePreloader()})},$scope.selectDays($scope.day)}),$scope.$on("robRankCtrl.setInited",function(){inited=!1}),$scope.batchRobRank=function(){if(!$scope.keyword_list.length)return!1;var adgroupId=$scope.keyword_list[0].adgroup_id;keywordIdList=[];for(var i in $scope.keyword_list)keywordIdList.push($scope.keyword_list[i].keyword_id);$http.post("/qnyd/ajax/",{"function":"batch_forecast_rt_rank",adgroup_id:adgroupId,keyword_list:keywordIdList}).success(function(data){for(var i in $scope.keyword_list)$scope.keyword_list[i].rank=data.data[$scope.keyword_list[i].keyword_id];$.hidePreloader(),$.pullToRefreshDone(".pull-to-refresh-content")})},$scope.setKeyword=function(){var self=this,buttons1=[{text:"请选择",label:!0},{text:"设置",bold:!0,onClick:function(){$.showPreloader(),$scope.$emit("qnydCtl.setRobRank",self.kw)}},{text:"查看历史",onClick:function(){$scope.$emit("qnydCtl.RobRankHistory",self.kw.keyword_id)}},{text:"取消自动抢排名",color:"danger",onClick:function(){$.confirm("我要取消自动抢排名",function(){$http.post("/qnyd/ajax/",{"function":"rob_cancle",keyword_id:self.kw.keyword_id}).success(function(){$.toast("操作成功"),$timeout(function(){$scope.del(self.kw.keyword_id)},0),$scope.$emit("qnydCtl.cancleRobRank",self.kw.keyword_id)})})}}],buttons2=[{text:"取消",bg:"danger"}],groups=[buttons1,buttons2];$.actions(groups)},$scope.del=function(keyword_id){for(var index in $scope.keyword_list)keyword_id==$scope.keyword_list[index].keyword_id&&$scope.keyword_list.splice(index,1)},$scope.keyword="",$scope.search=function(keyword){$scope.keyword=keyword}}),APP.controller("robRankSetCtl",function($scope,$http,$timeout){$scope.$on("robRankSetCtl.setRobRank",function(event,kw){$http.post("/qnyd/ajax/",{"function":"rob_config",keyword_id:kw.keyword_id,login_from:"qnyd"}).success(function(data){$.popup(".popup_rob_rank"),$.isEmptyObject(data.data)&&(data.data={method:"auto",end_time:"17:00",limit:void 0,nearly_success:1,platform:"pc",start_time:"08:00",rank_start_desc:"",rank_end_desc:""},data.data=angular.extend({},data.data,robSettings)),$timeout(function(){$scope.kw=kw,$scope.max_price=kw.max_price,$scope.max_mobile_price=kw.max_mobile_price,$scope.wireless_qscore=kw.qscore_dict.wireless_qscore,$scope.qscore=kw.qscore_dict.qscore,$scope.mobile_rank=kw.rank.mobile_rank,$scope.mobile_rank_desc=kw.rank.mobile_rank_desc,$scope.pc_rank=kw.rank.pc_rank,$scope.pc_rank_desc=kw.rank.pc_rank_desc;for(var key in data.data)$scope[key]=data.data[key];$scope.rank_start_desc_map=data.rank_start_desc_map,$scope.rank_end_desc_map=data.rank_end_desc_map,$scope.exceptTime=$scope.start_time+" - "+$scope.end_time,$scope.rank_pc=$scope.rank_yd=$scope.rank_start_desc&&$scope.rank_end_desc?$scope.rank_start_desc+" - "+$scope.rank_end_desc:"",$scope.limit&&($scope.limit=($scope.limit/100).toFixed(2)),$scope.initTimePicker($scope.start_time,$scope.end_time),$scope.initRankPicker($scope.rank_start_desc,$scope.rank_end_desc)},0),$.hidePreloader()})}),$scope.submit=function(){var errMsg="",start_time=$scope.exceptTime.split(" - ")[0],end_time=$scope.exceptTime.split(" - ")[1];return $scope.rank_start=$scope.rank_start_desc_map[$scope.platform][$.trim($scope["rank_"+$scope.platform].split("-")[0])],$scope.rank_end=$scope.rank_end_desc_map[$scope.platform][$.trim($scope["rank_"+$scope.platform].split("-")[1])],(void 0==$scope.rank_start||void 0==$scope.rank_end||parseInt($scope.rank_start)>parseInt($scope.rank_end))&&(errMsg+="请正确选择期望排名</br>"),(!$scope.limit||isNaN($scope.limit)||Number($scope.limit)<.05||Number($scope.limit)>99.99)&&(errMsg+="请正确填写最高限价,限价必须是0.05到99.99的整数</br>"),start_time>=end_time&&(errMsg+="自动抢排名结束时间必须大于起始时间"),""!=errMsg?($.alert(errMsg,"错误提示"),!1):("auto"==$scope.method&&$http.post("/qnyd/ajax/",{"function":"auto_rob_rank",keyword_id:$scope.kw.keyword_id,exp_rank_start:$scope.rank_start,exp_rank_end:$scope.rank_end,limit_price:parseInt(100*$scope.limit+.5),platform:$scope.platform,start_time:start_time,end_time:end_time,nearly_success:$scope.nearly_success}).success(function(data){return"nums_limit"==data.limitError?($.alert("亲，自动抢位的关键词已达到50个上限！","错误提示"),!1):"version_limit"==data.limitError?($.alert("亲，请联系顾问修改权限！","错误提示"),!1):"others"==data.limitError?($.alert("亲，请刷新页面重试！","错误提示"),!1):($scope.kw.exp_rank_start=$scope.rank_start,$scope.kw.exp_rank_start_desc=$.trim($scope["rank_"+$scope.platform].split("-")[0]),$scope.kw.exp_rank_end=$scope.rank_end,$scope.kw.exp_rank_end_desc=$.trim($scope["rank_"+$scope.platform].split("-")[1]),$scope.kw.limit_price=$scope.limit,$scope.kw.platform=$scope.platform,$scope.kw.is_locked=1,$.alert("系统将会在您指定的时间段内每30-60分钟自动为关键词抢排名"),$scope.$emit("qnydCtl.setInited"),void $.closeModal(".popup_rob_rank"))}),void("manual"==$scope.method&&$scope.$emit("qnydCtl.manualRobRank",$scope)))},$scope.initTimePicker=function(start_time,end_time){$(".popup_rob_rank .time").picker({value:[start_time,"-",end_time],toolbarTemplate:'<header class="bar bar-nav">                                      <button class="button button-link pull-right close-picker">确定</button>                                      <h1 class="title">请选择抢排名时间</h1>                                  </header>',cols:[{textAlign:"center",values:["00:00","01:00","02:00","03:00","04:00","05:00","06:00","07:00","08:00","09:00","10:00","11:00","12:00","13:00","14:00","15:00","16:00","17:00","18:00","19:00","20:00","21:00","22:00","23:00","24:00"]},{textAlign:"center",values:["-"]},{textAlign:"center",values:["00:00","01:00","02:00","03:00","04:00","05:00","06:00","07:00","08:00","09:00","10:00","11:00","12:00","13:00","14:00","15:00","16:00","17:00","18:00","19:00","20:00","21:00","22:00","23:00","24:00"]}]})},$scope.initRankPicker=function(rank_start_desc,rank_end_desc){var optionsDict={pc:["首页左侧位置","首页右侧第1","首页右侧第2","首页右侧第3","首页(非前三)","第2页","第3页","第4页","第5页","5页以后"],yd:["移动首条","移动前三","移动4~6条","移动7~10条","移动11~15条","移动16~20条","20条以后"]};$(".popup_rob_rank [name=rank_pc]").picker({value:[rank_start_desc,"-",rank_end_desc],cssClass:"min-picker",toolbarTemplate:'<header class="bar bar-nav">                                      <button class="button button-link pull-right close-picker">确定</button>                                      <h1 class="title">请选择PC端期望排名</h1>                                  </header>',cols:[{textAlign:"center",values:optionsDict.pc},{textAlign:"center",values:["-"]},{textAlign:"center",values:optionsDict.pc}]}),$(".popup_rob_rank [name=rank_mobil]").picker({value:[rank_start_desc,"-",rank_end_desc],cssClass:"min-picker",toolbarTemplate:'<header class="bar bar-nav">                                      <button class="button button-link pull-right close-picker">确定</button>                                      <h1 class="title">请选择移动端期望排名</h1>                                  </header>',cols:[{textAlign:"center",values:optionsDict.yd},{textAlign:"center",values:["-"]},{textAlign:"center",values:optionsDict.yd}]}),""===rank_start_desc&&""===rank_end_desc&&($(".popup_rob_rank [name=rank_pc]").picker("setValue",["首页右侧第2","-","首页(非前三)"]),$(".popup_rob_rank [name=rank_mobil]").picker("setValue",["移动前三","-","移动4~6条"]))}}),APP.controller("manualRobRankCtl",function($scope,$http,$timeout){var reset;$scope.keyword_list=[],$scope.info="",$scope.$on("manualRobRankCtl.manualRobRank",function(event,kw){reset=!1,$scope.keyword_list=[],$scope.info="正在手动抢排名...",$.popup(".popup_rob_rank_manual"),robSettings={method:"manual",limit:parseInt(100*kw.limit+.5),rank_start_desc:$.trim(kw["rank_"+kw.platform].split("-")[0]),rank_end_desc:$.trim(kw["rank_"+kw.platform].split("-")[1]),nearly_success:kw.nearly_success},$(".popup_rob_rank_manual").off("opened").on("opened",function(){$scope.startWebSocket(kw)}),$(".popup_rob_rank_manual").off("closed").on("closed",function(){reset&&$scope.$emit("qnydCtl.setRobRank",kw.kw)})}),$scope.startWebSocket=function(kw){var url,ws;url="ws://"+window.location.host+"/websocket/?keyword_id="+kw.kw.keyword_id,ws=new WebSocket(url),ws.onmessage=function(msg){if(""!=msg&&void 0!=msg){if("ready"==msg.data)return $scope.startRobRank(kw),!1;var content=JSON.parse(msg.data);$scope.showRobMsg(kw,content,ws)}else $.alert(msg,"错误提示")}},$scope.startRobRank=function(kw){$http.post("/qnyd/ajax/",{"function":"manual_rob_rank",keyword_id:kw.kw.keyword_id,adgroup_id:kw.kw.adgroup_id,exp_rank_start:kw.rank_start,exp_rank_end:kw.rank_end,limit_price:parseInt(100*kw.limit+.5),platform:kw.platform,nearly_success:kw.nearly_success}).success(function(data){return"others"==data.limitError?($.alert("亲，请刷新页面重试！","错误提示"),!1):void 0})},$scope.showRobMsg=function(kw,content,ws){$timeout(function(){$scope.keyword_list.push({rob_time:content.rob_time,price:Number(content.price).toFixed(2),msg:content.msg}),("ok"==content.result_flag||"nearly_ok"==content.result_flag)&&($scope.info="执行成功",ws.close()),("done"==content.result_flag||"failed"==content.result_flag)&&($scope.info="执行失败",ws.close())},0)},$scope.reset=function(){reset=!0,$.closeModal(".popup_rob_rank")}}),APP.controller("robRankHistoryCtl",function($scope,$http){$scope.info_list=[],$scope.$on("robRankHistoryCtl.RobRankHistory",function(event,keyword_id){$scope.info_list=[],$.showPreloader(),$http.post("/qnyd/ajax/",{"function":"rob_record",keyword_id:keyword_id}).success(function(data){$.hidePreloader(),$.popup(".popup_rob_rank_history");for(var index in data.data[keyword_id])$scope.info_list.push(JSON.parse(data.data[keyword_id][index]))}),$scope.formatDate=function(dt){return dt.slice(5,16)}})})}(),!function(){var getAdgroupList=function(keywordList){var adgroups={},adgroupList=[];for(var i in keywordList){var keyword=keywordList[i];adgroups[keyword.adgroup_id]||(adgroups[keyword.adgroup_id]={adgroup_id:keyword.adgroup_id,pic_url:keyword.pic_url,click:keyword.click,title:keyword.title,camp_title:keyword.camp_title,mnt_opt_type:keyword.mnt_opt_type})}for(var adg_id in adgroups)adgroupList.push(adgroups[adg_id]);return adgroupList};APP.filter("myFilter",function(){return function(input,param){var temp=[],nullInput=!0;for(var i in input)for(var p in param)nullInput&&param[p].length&&(nullInput=!1),param[p]&&input[i].hasOwnProperty(p)&&-1!=$.inArray(input[i][p],param[p])&&temp.push(input[i]);return nullInput?input:temp}}),APP.controller("shopCoreCtrl",function($scope,$http,$filter){var inited=!1,LIMIT_PRICE=5,searchFilter=$filter("filter"),adgroupFilter=$filter("myFilter");$scope.changeNum=0,$scope.mobileChangeNum=0,$scope.limitNum=0,$scope.mobileLimitNum=0,$scope.adgroupIdList=[],$scope.$on("shopCoreCtrl.shopCoreData",function(){if(inited)return!1;inited=!0;var dateFilter=$filter("date");void 0==$scope.day&&($scope.day="0"),$scope.selectDays=function(day){var endDay=dateFilter(new Date,"yyyy-MM-dd"),startDay=dateFilter(new Date-864e5*Number(day),"yyyy-MM-dd");$scope.day=day,num=0,$.showPreloader(),$http.post("/qnyd/ajax/",{"function":"calc_shop_core"}).success(function(data){"doing"==data.condition&&($.hidePreloader(),$scope.keyword_list=[],$scope.errMsg="正在分析核心词，请稍后再来查看或手动刷新该页面（第一次使用时需要下载大量数据，平均每100个宝贝约需要等待6分钟）"),"ok"==data.condition&&$http.post("/qnyd/ajax/",{"function":"shop_core_list",start_date:startDay,end_date:endDay}).success(function(data){for(var i in data.keyword_list)data.keyword_list[i].custum_price=data.keyword_list[i].max_price,data.keyword_list[i].custum_mobiles_price=data.keyword_list[i].max_mobile_price;$scope.keyword_list=data.keyword_list,$scope.errMsg=data.msg,$scope.$emit("qnydCtl.chooseAdgroup",getAdgroupList($scope.keyword_list),$scope),$.hidePreloader()})})},$scope.selectDays($scope.day)}),$scope.$on("shopCoreCtrl.cancleRobRank",function(event,keyword_id){for(var i in $scope.keyword_list)if($scope.keyword_list[i].keyword_id==keyword_id){$scope.keyword_list[i].is_locked=0;break}}),$scope.chooseShopCore=function(){$.popup(".popup_choose_shop_core")},$scope.cancleShopCore=function(){$scope.adgroupIdList=[]},$scope.inputBlur=function(price,type){(isNaN(price)||Number(price)<.05||Number(price)>99.99)&&(1&type&&(this.kw.custum_price=this.kw.max_price),2&type&&(this.kw.custum_mobiles_price=this.kw.max_mobile_price)),1&type&&(this.kw.custum_price=Number(this.kw.custum_price).toFixed(2)),2&type&&(this.kw.custum_mobiles_price=Number(this.kw.custum_mobiles_price).toFixed(2)),$scope.updateStyle.apply(this.kw,[type]),$scope.calcChangeNum()},$scope.updateStyle=function(type){1&type&&(this.up=this.down=this.limit=!1,Number(this.custum_price)>this.max_price&&(this.up=!0),Number(this.custum_price)<this.max_price&&(this.down=!0),Number(this.custum_price)>LIMIT_PRICE&&(this.limit=!0)),2&type&&(this.mobileUp=this.mobileDown=this.mobileLimit=!1,Number(this.custum_mobiles_price)>this.max_mobile_price&&(this.mobileUp=!0),Number(this.custum_mobiles_price)<this.max_mobile_price&&(this.mobileDown=!0),Number(this.custum_mobiles_price)>LIMIT_PRICE&&(this.mobileLimit=!0))},$scope.calcChangeNum=function(){var num=0,mobileNum=0,limitNum=0,mobileLimitNum=0,keywordList=$scope.getKeywordList();for(var i in keywordList){var keyword=keywordList[i];Number(keyword.custum_price)!=keyword.max_price&&(num++,Number(keyword.custum_price)>LIMIT_PRICE&&limitNum++),Number(keyword.custum_mobiles_price)!=keyword.max_mobile_price&&(mobileNum++,Number(keyword.custum_mobiles_price)>LIMIT_PRICE&&mobileLimitNum++)}$scope.changeNum=num,$scope.mobileChangeNum=mobileNum,$scope.limitNum=limitNum,$scope.mobileLimitNum=mobileLimitNum},$scope.commit=function(){var msg;$scope.changeNum||$scope.mobileChangeNum?(msg="您有PC:"+$scope.changeNum+"个,移动:"+$scope.mobileChangeNum+"个关键词做了改变",($scope.limitNum||$scope.mobileLimitNum)&&(msg+=",其中",$scope.limitNum&&(msg+="PC:"+$scope.limitNum+"个"),$scope.mobileLimitNum&&(msg+=",移动:"+$scope.mobileLimitNum+"个"),msg+="超过了"+LIMIT_PRICE+"元"),msg+=",确定提交吗？",$.confirm(msg,"确认提交",function(){var submitKeywordList=[],keywordList=$scope.getKeywordList();for(var i in keywordList){var keyword=keywordList[i];(Number(keyword.custum_price)!=keyword.max_price||Number(keyword.custum_mobiles_price)!=keyword.max_mobile_price)&&submitKeywordList.push({keyword_id:keyword.keyword_id,adgroup_id:keyword.adgroup_id,campaign_id:keyword.campaign_id,word:keyword.word,new_price:keyword.custum_price,max_price:keyword.max_price,match_scope:keyword.match_scope,max_mobile_price:keyword.custum_mobiles_price,mobile_old_price:keyword.max_mobile_price,mobile_is_default_price:0,is_del:!1})}$http.post("/qnyd/ajax/",{"function":"submit_keyword",submit_list:JSON.stringify(submitKeywordList),update_mnt_list:"[]",optm_type:0}).success(function(data){var update_count=data.update_kw.length,failed_count=data.failed_kw.lengthh,msg="修改成功:"+update_count+"个";failed_count&&(msg+="操作失败:"+failed_count+"个");for(var u in data.update_kw)for(var s in keywordList)data.update_kw[u]!=keywordList[s].keyword_id||(keywordList[s].max_price=keywordList[s].custum_price,keywordList[s].max_mobile_price=keywordList[s].custum_mobiles_price,$scope.updateStyle.apply(keywordList[s],[3]));$scope.calcChangeNum(),$.alert(msg)})})):$.toast("没有关键词改变")},$scope.getKeywordList=function(){return adgroupFilter(searchFilter($scope.keyword_list,{word:$scope.keyword}),{adgroup_id:$scope.adgroupIdList})},$scope.search=function(keyword){$scope.keyword=keyword,$scope.calcChangeNum()},$scope.rob_rank=function(){$.showPreloader();var self=this;$http.post("/qnyd/ajax/",{"function":"forecast_rt_rank",keyword_id:this.kw.keyword_id,adgroup_id:this.kw.adgroup_id}).success(function(data){self.kw.pc_rank=data.data.pc_rank,self.kw.pc_rank_desc=data.data.pc_rank_desc,self.kw.mobile_rank=data.data.mobile_rank,self.kw.mobile_rank_desc=data.data.mobile_rank_desc,self.kw.rank={pc_rank:data.data.pc_rank,pc_rank_desc:data.data.pc_rank_desc,mobile_rank:data.data.mobile_rank,mobile_rank_desc:data.data.mobile_rank_desc},$scope.$emit("qnydCtl.setRobRank",self.kw)})}}),APP.controller("chooseShopCoreCtl",function($scope){$scope.$on("chooseShopCoreCtl.chooseAdgroup",function(event,adgroupList,scope){adgroupList.length?($scope.adgroup_list=adgroupList,$scope.scope=scope):$.toast("暂时没有数据")}),$scope.filter=function(){var filterAdg=[];for(var i in $scope.adgroup_list)$scope.adgroup_list[i].check&&filterAdg.push($scope.adgroup_list[i].adgroup_id);$scope.scope.adgroupIdList=filterAdg,$scope.scope.calcChangeNum(),$.closeModal(".popup_choose_shop_core")}})}(),!function(){APP.controller("myCtrl",function($scope,$http){$scope.sync=function(){$.showPreloader("正在同步，请稍后"),$http.post("/qnyd/ajax/",{"function":"sync_data"}).success(function(data){$.hidePreloader(),$.alert(data.msg)})},$scope.contact_ww=function(){TOP.mobile.ww.chat({chatNick:"派生科技",text:"来自千牛移动：",domain_code:"taobao"})},$scope.suggestion=function(){$scope.$emit("qnydCtl.suggestion")}}),APP.controller("suggestionCtl",function($scope,$http){$scope.$on("suggestionCtl.suggestion",function(){$.popup(".popup_suggestion")}),$scope.submit=function(){$.showPreloader("正在提交，请稍后..."),$http.post("/qnyd/ajax/",{"function":"add_suggest",suggest:$scope.suggestions}).success(function(data){return data.errMsg?($.alert(data.errMsg),!1):($.toast("感谢您的反馈"),$.closeModal(".popup_suggestion"),void $.hidePreloader())})}})}();