define("site_media/service/keyword/keyword_list",["require","site_media/service/common/common","site_media/plugins/artTemplate/template","site_media/plugins/moment/moment.min","site_media/plugins/data-tables/dataTableExt","site_media/widget/ajax/ajax","site_media/widget/loading/loading","site_media/plugins/jquery.json-2.4.min"],function(e,a,t,r,i,s,n){"use strict";var c,o=r().subtract(7,"days").format("YYYY-MM-DD"),l=r().subtract(1,"days").format("YYYY-MM-DD"),d=[],_="",p=[],u=[],m=[],b=[],v={},f=function(a){_=a,$("#keyword_table tbody").on("get.rank","tr",function(e,a){var t=$(this).data("adgroup_id"),r=$(this).attr("id"),i=[r];s.ajax("batch_forecast_rt_rank",{keyword_list:i,adgroup_id:t},function(e){a&&a(e)})}),$("#keyword_table tbody").on("update.rank","tr",function(e,a,t){$(this).find(".pc_rank").text(a),$(this).find(".mobile_rank").text(t)}),$("#keyword_table tbody").on("update.rob_rank","tr",function(e,a,t,r){var i;$(this).data("locked",0),"nomal"==a&&(i='<a href="javascript:;" class="rob_set">抢</a>'),"fail"==a&&(i='<a href="javascript:;" class="rob_record">手动抢失败</a>&emsp;<a href="javascript:;" class="rob_set ml5">再抢</a>'),"success"==a&&("pc"==r?($(this).find(".max_price").text(t),$(this).find(".sort_max_price").text(t),$(this).find(".new_price").val(t),$(this).find(".new_price").data("old",t)):($(this).find(".max_mobile_price").text(t),$(this).find(".sort_max_mobile_price").text(t),$(this).find(".new_mobile_price").val(t),$(this).find(".new_mobile_price").data("old",t)),i='<a href="javascript:;" class="rob_record">手动抢成功</a>&emsp;<a href="javascript:;" class="rob_set ml5">再抢</a>'),"auto"==a&&($(this).data("locked",1),i='<a href="javascript:;" class="rob_record">已设为自动</a>&emsp;<a href="javascript:;" class="rob_set ml5">设置</a>'),"doing"==a&&(i='<a href="javascript:;" class="rob_doing">正在抢排名，请稍候</a>'),$(this).find(".rob_rank").html(i)}),$("#keyword_table tbody").on("get.rob_set","tr",function(a,t){var r=$(this),i={keywordId:r.attr("id"),adgroupId:r.data("adgroup_id"),word:r.find(".word").text(),maxPrice:Number(r.find(".max_price").text()),maxMobilePrice:Number(r.find(".max_mobile_price").text()),qscore:r.find(".qscore").attr("pc_qscore"),wirelessQscore:r.find(".qscore").attr("yd_qscore"),target:_};return i=$.extend({},i,t),e(["site_media/service/rob_rank/rob_rank"],function(e){e.show(i)}),!1}),$("#keyword_table tbody").on("delete_row","tr",function(){var e=$("#keyword_table tbody tr").index($(this));c.fnDeleteRow(e),$(this).remove(),$("#keywords_count").text(c.fnGetData().length)}),$("#keyword_table").on("click",".rank",function(){var e=$(this).closest("tr"),a=$("<img src=/site_media/qnpc6/static/images/small_ajax.gif>");$(this).replaceWith(a);var t=e.attr("id");e.trigger("get.rank",function(r){a.remove(),t in r.data?(e.find(".pc_rank").attr("colspan",1).text(r.data[t].pc_rank_desc),e.find(".mobile_rank").text(r.data[t].mobile_rank_desc).show()):(e.find(".pc_rank").attr("colspan",1).text("获取失败"),e.find(".mobile_rank").text("获取失败").show())})}),$("#keyword_table").on("click",".rob_record",function(){var a=$(this).closest("tr").attr("id");return e(["site_media/service/rob_rank/rob_record"],function(e){e.show({keywordId:a})}),!1}),$("#keyword_table").on("click",".rob_set",function(){var e=$(this).closest("tr"),a=$(this).closest("tr").attr("id");s.ajax("rob_config",{keyword_id:a},function(t){var r,i={},s=$("#keyword_table").data("saveOptions.rank"),n=t.rank_start_desc_map,c=t.rank_end_desc_map;if(t.data.platform){var o,l;o=n[t.data.platform][t.data.rank_start],l=c[t.data.platform][t.data.rank_end],i={method:"auto",keyword_id:a,platform:t.data.platform,rank_start:t.data.rank_start,rank_start_name:o,rank_end:t.data.rank_end,rank_end_name:l,limit:(t.data.limit/100).toFixed(2),nearly_success:t.data.nearly_success,start_time:t.data.start_time,end_time:t.data.end_time,rank_start_desc_map:n,rank_end_desc_map:c},r=$.extend({},i)}else i={method:"",limit:"",keyword_id:a,rank_start_desc_map:n,rank_end_desc_map:c},r=$.extend({},i,s);e.trigger("get.rob_set",r)})}),$("#keyword_table").on("click",".undo",function(){var e=$(this).prev();e.val(e.data("old")),e.change()}),$("#keyword_table").on("change",".edit_price",function(){var e=$(this).closest("tr"),a=e.attr("id"),t=e.data("adgroup_id"),r=e.data("campaign_id"),i=e.find(".new_price").val(),s=parseFloat(e.find(".new_price").data("old")).toFixed(2),n=e.find(".new_mobile_price").val(),c=parseFloat(e.find(".new_mobile_price").data("old")).toFixed(2);if(!w(i)||!w(n))return void $(this).val($(this).hasClass("new_price")?s:c);var o=parseFloat($(this).val()).toFixed(2);i=parseFloat(i).toFixed(2),n=parseFloat(n).toFixed(2),e.find(".new_price").val(i),e.find(".new_mobile_price").val(n),$(this).closest("td").find(".sort_price").text(o),v[a]={keyword_id:a,adgroup_id:t,campaign_id:r,word:e.find(".word").text(),max_price:s,new_price:i,is_del:0,match_scope:e.data("match"),mobile_old_price:c,max_mobile_price:n,mobile_is_default_price:e.data("mobile_match")},k(e),i>s?($.inArray(a,u)>-1&&u.splice($.inArray(a,u),1),-1==$.inArray(a,p)&&p.push(a)):s>i?($.inArray(a,p)>-1&&p.splice($.inArray(a,p),1),-1==$.inArray(a,u)&&u.push(a)):($.inArray(a,u)>-1&&u.splice($.inArray(a,u),1),$.inArray(a,p)>-1&&p.splice($.inArray(a,p),1)),n>c?($.inArray(a,b)>-1&&b.splice($.inArray(a,b),1),-1==$.inArray(a,m)&&m.push(a)):c>n?($.inArray(a,m)>-1&&m.splice($.inArray(a,m),1),-1==$.inArray(a,b)&&b.push(a)):($.inArray(a,b)>-1&&b.splice($.inArray(a,b),1),$.inArray(a,m)>-1&&m.splice($.inArray(a,m),1)),n!=c&&(v[a].mobile_is_default_price=0),n==c&&i==s&&$.inArray(a,v)>-1&&delete v[a],$("#pc_add_count").text(p.length),$("#pc_cut_count").text(u.length),$("#yd_add_count").text(m.length),$("#yd_cut_count").text(b.length)}),$("#keyword_table tbody").on("click",".forecast",function(){x($(this))}),$("#refresh_list").on("click.sync_max_price",function(){s.ajax("keyword_attr",{kw_id_list:d,attr_list:["max_price"]},function(e){for(var a in e.data)$("#"+a).find(".max_price").text((e.data[a].max_price/100).toFixed(2))})}),$("#keyword_table tbody").on("change",".forecast_select",function(){var e,a=$(this).closest("tr");if(-1!=this.value.indexOf("reason")){var t,r='<div tabindex="-1" role="dialog" class="sui-modal hide fade">\n    <div class="modal-dialog">\n        <div class="modal-content">\n            <div class="modal-header">\n                <button type="button" data-dismiss="modal" aria-hidden="true" class="sui-close">×</button>\n                <h4 id="myModalLabel" class="modal-title">提示</h4>\n            </div>\n            <div class="modal-body">\n                   预估排名为0，<a target="_blank" href="https://bbs.taobao.com/catalog/thread/244117-318794824.htm?spm=0.0.0.0.PmcTbm">点击这里查看原因</a>\n            </div>\n            <div class="modal-footer">\n                <button type="button" data-dismiss="modal" class="sui-btn btn-default btn-large">关闭</button>\n            </div>\n        </div>\n    </div>\n</div>\n';return t=$(r),$("body").append(t),t.modal(),!1}e=Number(this.value.split("-")[0]),w(e)?(a.find(".new_price").val(e.toFixed(2)),a.find(".new_price").change()):a.find(".new_price").val(a.find(".new_price").data("old"))}),$("#keyword_table tbody").on("change",".forecast_fail",function(){"1"==$(this).val()&&x($(this))}),$("#submit_list").click(function(){var e=[];for(var a in v)e.push(v[a]);e.length>0&&(p.length>0||u.length>0||m.length>0||b.length>0)?$.confirm({title:"提示",closeBtn:!1,body:"PC: 加价"+p.length+"个，降价"+u.length+"个；<br>移动: 加价"+m.length+"个，降价"+b.length+"个。<br>您确定要提交吗？",okBtn:"确定",cancelBtn:"取消",height:"60px",backdrop:"static",keyboard:!1,okHide:function(){s.ajax("submit_keyword",{submit_list:$.toJSON(e)},function(e){var a=e.update_kw.length,t=e.failed_kw.length,r="修改成功:"+a+"个，失败:"+t+"个";$.alert({title:"提示",hasfoot:!1,body:r,height:20});for(var i in e.update_kw){var s=e.update_kw[i],n=v[s],c=$("#"+s);c.find(".sort_max_price").text(n.new_price),c.find(".new_price").data("old",n.new_price),c.find(".max_price").text(n.new_price),c.find(".sort_max_mobile_price").text(n.max_mobile_price),c.find(".new_mobile_price").data("old",n.max_mobile_price),c.find(".max_mobile_price").text(n.max_mobile_price)}for(var i in e.failed_kw){var s=e.failed_kw[i],c=$("#"+s);c.find(".new_price").val(c.find(".new_price").data("old")),c.find(".new_mobile_price").val(c.find(".new_mobile_price").data("old"))}$("#pc_add_count").text(0),$("#pc_cut_count").text(0),$("#yd_add_count").text(0),$("#yd_cut_count").text(0),v={},p=[],u=[],m=[],b=[]})}}):$.alert({title:"提示",hasfoot:!1,body:"没有修改任何关键词！",height:20})})},h=function(e,a){var t="rob_list";"core"==_&&(t="shop_core_list"),n.show("数据加载中，请稍候..."),s.ajax(t,{start_date:e,end_date:a},function(e){g(e),n.hide()})},g=function(e){var a,r;"rank"==_?r='{{if keywordList.length}}\n    {{each keywordList}}\n    <tr id="{{$value.keyword_id}}" data-adgroup_id="{{$value.adgroup_id}}" data-campaign_id="{{$value.campaign_id}}" data-match="{{$value.match_scope}}">\n        <td style="padding:2px; width:60px;" class="img_box">\n            <img  height="60" width="60" src="{{$value.pic_url}}_60x60.jpg_.webp" data-title="{{$value.title}}" data-camp-title="{{$value.camp_title}}" data-price="{{$value.price}}" data-pic-url="{{$value.pic_url}}"  data-locked="{{$value.is_locked}}"></a>\n        </td>\n        <td class="tl">\n            <span class="word">{{$value.word}}</span>\n            {{if $value.qscore_dict.wireless_matchflag == "2" || $value.qscore_dict.wireless_matchflag == "4"}}\n                <span class="iconfont show_tooltip"  data-placement="right" data-trigger="hover" data-title="移动首屏展示机会:有机会在手机淘宝网和淘宝客户端搜索结果中屏展示">&#xe605;</span>\n            {{/if}}\n            {{if $value.qscore_dict.pc_left_flag}}\n                <span class="iconfont show_tooltip" data-placement="right" data-trigger="hover" data-title="淘宝豆腐块展示机会:有机会在淘宝搜索关键词结果页左侧展示">&#xe606;</span>\n            {{/if}}\n        </td>\n        <td class="max_price">{{$value.max_price}}</td>\n        <td class="max_mobile_price">{{$value.max_mobile_price}}</td>\n        <td colspan="2" class="pc_rank">\n            <a class="rank w200" href="javascript:;">查</a>\n        </td>\n        <td style="display: none" class="mobile_rank"></td>\n        <td class="rob_rank">\n                <span class="dib w200 platform">\n                    <span class="platform_name w60">{{if $value.platform == \'pc\'}}计算机{{else}} 移动&emsp;{{/if}}</span>&nbsp;&nbsp;&nbsp;&nbsp;\n                    <span class="dib">限价<span class="limit_price">{{$value.limit_price}}</span>元</span>\n                </span>\n                <a href="javascript:;" class="rob_record">详情</a><br/>\n                <span class="dib w200 platform">\n                    <span class="exp_rank_start">{{$value.exp_rank_start_desc}}</span> - <span class="exp_rank_end">{{$value.exp_rank_end_desc}}</span>\n                </span>\n                <a href="javascript:;" class="rob_set">设置</a>\n        </td>\n        <td class="pc_qs">\n            <span class="pc_qs">{{$value.qscore_dict.qscore}}</span>\n        </td>\n        <td class="mobile_qs sort_custom qscore" pc_qscore="{{$value.qscore_dict.qscore}}" pc_creative_score="{{$value.qscore_dict.creativescore}}" pc_rele_score="{{$value.qscore_dict.kwscore}}" pc_cvr_score="{{$value.qscore_dict.cvrscore}}" yd_qscore="{{$value.qscore_dict.wireless_qscore}}" yd_creative_score="{{$value.qscore_dict.wireless_creativescore}}" yd_rele_score="{{$value.qscore_dict.wireless_relescore}}" yd_cvr_score="{{$value.qscore_dict.wireless_cvrscore}}" matchflag="{{$value.qscore_dict.wireless_matchflag}}" plflag="{{$value.qscore_dict.pc_left_flag}}">\n            {{if $value.qscore_dict.wireless_qscore >-1 }}\n                <span class="hide">{{$value.qscore_dict.wireless_qscore}}</span>\n                {{$value.qscore_dict.wireless_qscore}}\n            {{ else }}<span class="hide">0</span>--{{/if}}\n        </td>\n        <td class="striped">{{$value.impr}}</td>\n        <td class="striped">{{$value.click}}</td>\n        <td class="striped">{{$value.ctr}}%</td>\n        <td class="striped">{{$value.cost}}</td>\n        <td class="striped">{{$value.cpc}}</td>\n        <td>{{$value.conv}}%</td>\n        <td {{if $value.roi>1}}class="red"{{/if}}>{{$value.roi}}</td>\n    </tr>\n    {{/each}}\n{{/if}}\n':"core"==_&&(r='{{if keywordList.length}}\n    {{each keywordList}}\n    <tr id="{{$value.keyword_id}}" data-adgroup_id="{{$value.adgroup_id}}" data-campaign_id="{{$value.campaign_id}}" data-match="{{$value.match_scope}}" data-mobile_match="{{$value.mobile_is_default_price}}" >\n        <td style="padding:2px; width:60px;" class="img_box">\n            <img  height="60" width="60" src="{{$value.pic_url}}_60x60.jpg_.webp" data-title="{{$value.title}}" data-camp-title="{{$value.camp_title}}" data-price="{{$value.price}}" data-pic-url="{{$value.pic_url}}"></a>\n        </td>\n        <td class="tl">\n            <span class="word">{{$value.word}}</span>\n            {{if $value.qscore_dict.wireless_matchflag == "2" || $value.qscore_dict.wireless_matchflag == "4"}}\n                <span class="iconfont show_tooltip" data-placement="right" data-trigger="hover" data-title="移动首屏展示机会:有机会在手机淘宝网和淘宝客户端搜索结果中屏展示">&#xe605;</span>\n            {{/if}}\n            {{if $value.qscore_dict.pc_left_flag}}\n            <span class="iconfont show_tooltip" data-placement="right" data-trigger="hover" data-title="淘宝豆腐块展示机会:有机会在淘宝搜索关键词结果页左侧展示">&#xe606;</span>\n            {{/if}}\n        </td>\n        <td class="max_price">{{$value.max_price}}</td>\n        <td class="sort_custom">\n            <span class="hide sort_price sort_max_price">{{$value.max_price}}</span>\n            <form class="sui-form rank-form">\n                <input type="text" data-old="{{ $value.max_price }}" placeholder="{{$value.max_price}}" maxlength="5" value="{{$value.max_price}}" class="input-mini new_price edit_price">\n                <i class="iconfont undo">&#xe608;</i>\n            </form>\n        </td>\n        <td class="max_mobile_price">{{$value.max_mobile_price}}</td>\n        <td class="sort_custom">\n            <span class="hide sort_price sort_max_mobile_price">{{$value.max_mobile_price}}</span>\n            <form class="sui-form rank-form">\n                <input type="text" data-old="{{ $value.max_mobile_price }}" placeholder="{{$value.max_mobile_price}}" maxlength="5" value="{{$value.max_mobile_price}}" class="input-mini new_mobile_price edit_price">\n                <i class="iconfont undo">&#xe608;</i>\n            </form>\n        </td>\n        <td class="rob_rank">\n            {{if $value.is_locked}}\n                <a href="javascript:;" class="rob_record">已设为自动</a>&emsp;<a href="javascript:;" class="rob_set ml5">设置</a>\n            {{else}}\n                <a class="rob_set" href="javascript:;">抢</a>\n            {{/if}}\n        </td>\n        <td colspan="2" class="pc_rank">\n            <a class="rank" href="javascript:;">查</a>\n        </td>\n        <td style="display: none" class="mobile_rank"></td>\n        <td class="pc_qs">\n            <span class="pc_qs">{{$value.qscore_dict.qscore}}</span>\n        </td>\n        <td class="mobile_qs sort_custom qscore" pc_qscore="{{$value.qscore_dict.qscore}}" pc_creative_score="{{$value.qscore_dict.creativescore}}" pc_rele_score="{{$value.qscore_dict.kwscore}}" pc_cvr_score="{{$value.qscore_dict.cvrscore}}" yd_qscore="{{$value.qscore_dict.wireless_qscore}}" yd_creative_score="{{$value.qscore_dict.wireless_creativescore}}" yd_rele_score="{{$value.qscore_dict.wireless_relescore}}" yd_cvr_score="{{$value.qscore_dict.wireless_cvrscore}}" matchflag="{{$value.qscore_dict.wireless_matchflag}}" plflag="{{$value.qscore_dict.pc_left_flag}}">\n            {{if $value.qscore_dict.wireless_qscore >-1 }}\n                <span class="hide">{{$value.qscore_dict.wireless_qscore}}</span>\n                {{$value.qscore_dict.wireless_qscore}}\n            {{ else }}<span class="hide">0</span>--{{/if}}\n        </td>\n        <td class="striped">{{$value.impr}}</td>\n        <td class="striped">{{$value.click}}</td>\n        <td class="striped">{{$value.ctr}}%</td>\n        <td class="striped">{{$value.cost}}</td>\n        <td class="striped">{{$value.cpc}}</td>\n        <td>{{$value.conv}}%</td>\n        <td {{if $value.roi>1}}class="red"{{/if}}>{{$value.roi}}</td>\n    </tr>\n    {{/each}}\n{{/if}}\n'),a=t.compile(r)({keywordList:e.keyword_list}),c&&(c.fnClearTable(),c.fnDestroy());var i="暂无数据";e.msg&&(i=e.msg),$("#keywords_count").text(e.keyword_list.length),$("#keyword_table tbody").html(a);for(var s in e.keyword_list){var n=e.keyword_list[s];d.push(n.keyword_id)}c=$("#keyword_table").dataTable({bRetrieve:!0,bPaginate:!1,bDestroy:!0,bFilter:!0,bInfo:!1,bAutoWidth:!1,sDom:"",language:{emptyTable:"<div style='text-align:center'>"+i+"</div>"},aoColumns:S()}),$(".show_tooltip").tooltip()},w=function(e){return isNaN(e)||.05>e||e>99.99?!1:!0},x=function(e){var a,r,i,n,c=e.closest("tr"),o=c.attr("id");a='<select class="forecast_select" style="width: 120px">\n{{each data}}\n    {{if $value[1]==\'0.00\'}}\n    <option value="{{$value[1]}}" >无左推资格</option>\n    {{else}}\n    <option value="{{$value[1]}}" >{{$value[0]}}</option>\n    {{/if}}\n{{/each}}\n    <option value="reason">预估为0：了解原因</option>\n</select>\n',r='<select class="forecast_fail">\n    <option value="0" selected="selected">{{errMsg}}</option>\n    <option value="1">重新预估</option>\n</select>\n',n=$("<img src=/site_media/qnpc6/static/images/small_ajax.gif>"),e.replaceWith(n),s.ajax("forecast_rank",{keyword_id:o},function(e){if($.isArray(e.data)&&e.data.length>0)i=9999==e.data[99]?t.compile(r)({errMsg:"出价到99.99元也无法获得排名"}):t.compile(a)({data:y(e.data)});else{var s=e.data.length>0?e.data:"淘宝返回预估排名数据为空";i=t.compile(r)({errMsg:s})}n.replaceWith(i),k(c)})},y=function(e){for(var a,t,r,i,s,n=[],c=[],o=[],l=[],d=[],_=17,p=0;p<Math.ceil(e.length/_);p++){a=p+1,c=e.slice(p*_,(p+1)*_),s=a>1?"第"+a+"页":"",3>a?(o=c.slice(0,4),l=c.slice(4,12),d=c.slice(12,17)):(o=[],l=c.slice(0,12),d=c.slice(12,17));for(var u in o)t=(o[u]/100).toFixed(2),n.push([s+"第"+(Number(u)+1)+"名："+t+"元",t]);if(l.length>0){var m=o.length+1,b=o.length+l.length;1==l.length?(t=(l[0]/100).toFixed(2),n.push([s+"第"+m+"名："+t+"元",t])):(r=(l[0]/100).toFixed(2),i=(l[l.length-1]/100).toFixed(2),n.push([s+"第"+m+"~"+b+"名："+r+"~"+i+"元",r+"-"+i]))}d.length>0&&(1==d.length?(t=(d[0]/100).toFixed(2),n.push(["第"+a+"页底部："+t+"元",t])):(r=(d[0]/100).toFixed(2),i=(d[d.length-1]/100).toFixed(2),n.push(["第"+a+"页底部："+r+"~"+i+"元",r+"-"+i])))}return n.push([e.length+"名以后："+(i-.01).toFixed(2)+"元",(i-.01).toFixed(2)]),n},k=function(e){var a=e.find(".forecast_select");if(0!=a.length){var t=e.find(".new_price").val(),r=null;a.find("option").each(function(){var e=Number(this.value.split("-").slice(-1)[0]);return e&&t>=e?(r=this.value,!1):void 0}),r||(r=a.find("option:last").prev().val()),a.val(r)}},q=function(e,a){o=e,l=a},S=function(){return"rank"==_?[{bSortable:!1},{bSortable:!0},{bSortable:!0,sType:"custom",sSortDataType:"custom-text"},{bSortable:!0,sType:"custom",sSortDataType:"custom-text"},{bSortable:!1},{bSortable:!1},{bSortable:!0},{bSortable:!0,sType:"custom",sSortDataType:"custom-text"},{bSortable:!0},{bSortable:!0},{bSortable:!0},{bSortable:!0},{bSortable:!0},{bSortable:!0},{bSortable:!0}]:[{bSortable:!1},{bSortable:!0},{bSortable:!0},{bSortable:!0,sType:"custom",sSortDataType:"custom-text"},{bSortable:!0},{bSortable:!0,sType:"custom",sSortDataType:"custom-text"},{bSortable:!1},{bSortable:!1},{bSortable:!1},{bSortable:!0},{bSortable:!0,sType:"custom",sSortDataType:"custom-text"},{bSortable:!0},{bSortable:!0},{bSortable:!0},{bSortable:!0},{bSortable:!0},{bSortable:!0},{bSortable:!0}]};return{init:f,setQueryDate:q,getKeywordList:h}});