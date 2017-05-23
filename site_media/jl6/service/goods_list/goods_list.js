define("jl6/site_media/service/goods_list/goods_list",["require","jl6/site_media/plugins/artTemplate/template","jl6/site_media/service/page_tool/page_tool","jl6/site_media/plugins/data-tables/dataTableExt","jl6/site_media/widget/ajax/ajax","jl6/site_media/widget/loading/loading","jl6/site_media/service/goods_list/select_tool","jl6/site_media/service/report_detail/report_detail","jl6/site_media/widget/lightMsg/lightMsg","jl6/site_media/widget/alert/alert"],function(t,a,e,i,s,n,d,o,l,_){"use strict";var p,r={checkbox:0,img:1,title:2,impressions:3,click:4,ctr:5,cost:6,ppc:7,favcount:8,carttotal:9,paycount:10,conv:11,pay:12,roi:13,online_status:14,mnt_opt_type:15,opt:16},c="pay",u=-1,m="desc",f={},g=1,h=function(t,a,e,i){f={search_type:"all",PAGE_NO:1,PAGE_SIZE:50,CONSULT_WW:$("#CONSULT_WW").val(),page_type:parseInt($("#page_type").val()),start_date:a,end_date:e,last_day:7,adgroup_table:null,camp_id:i,search_word:$("#search_val").val(),opt_type:-1,status_type:"",max_num:parseInt($("#mnt_max_num").val()),mnt_type:parseInt($("#mnt_type").val()),sort:"pay_-1",list_type:t,is_follow:-1},b(),v()},v=function(){$("#show_subdivide_all").on("click",function(){if(!$(this).data("is_lock")){$(this).data("is_lock",1);var t=$(this).data("is_showing");$.map($("#goods_table .show_subdivide"),function(a){$(a).data("is_showing")==t&&$(a).click()}),t?delete $(this).data().is_showing:$(this).data("is_showing",1),delete $(this).data().is_lock}}),$("#goods_table").on("click",".show_subdivide",function(){if(!$(this).data("is_lock")){$(this).data("is_lock",1);var t,e,i,n,d,o='<tr class="hover_non_color">\n    <td rowspan="4" colspan="2"></td>\n    <td rowspan="2"  style="padding: 0px;">\n        <table class="table">\n            <tr>\n                <td rowspan="2"  style="border-top: none"  class="brd">计算机&emsp;</td>\n                <td  style="border-top: none">站内</td>\n            </tr>\n            <tr>\n                <td >站外</td>\n            </tr>\n        </table>\n    </td>\n    {{ if pcin }}\n    <td>{{ pcin.impr}}</td>\n    <td>{{ pcin.click}}</td>\n    <td>{{ pcin.ctr}}%</td>\n    <td>￥{{ pcin.cost}}</td>\n    <td>￥{{ pcin.cpc}}</td>\n    <td>{{ pcin.favcount}}</td>\n    <td>{{ pcin.carttotal}}</td>\n    <td>{{ pcin.paycount}}</td>\n    <td>{{ pcin.conv}}%</td>\n    <td>￥{{ pcin.pay}}</td>\n    <td>{{ pcin.roi}}</td>\n    {{ else }}\n    <td class="tc item_base" colspan="11">暂无数据</td>\n    {{ /if }}\n    <td rowspan="4" colspan="3"></td>\n</tr>\n<tr class="hover_non_color">\n    {{ if pcout }}\n    <td>{{pcout.impr}}</td>\n    <td>{{pcout.click}}</td>\n    <td>{{pcout.ctr}}%</td>\n    <td>￥{{pcout.cost}}</td>\n    <td>￥{{pcout.cpc}}</td>\n    <td>{{pcout.favcount}}</td>\n    <td>{{ pcout.carttotal}}</td>\n    <td>{{pcout.paycount}}</td>\n    <td>{{pcout.conv}}%</td>\n    <td>￥{{pcout.pay}}</td>\n    <td>{{pcout.roi}}</td>\n    {{ else }}\n    <td class="tc item_base" colspan="11">暂无数据</td>\n    {{ /if }}\n</tr>\n<tr class="hover_non_color">\n    <td rowspan="2"  style="padding: 0px;">\n        <table class="table">\n            <tr>\n                <td rowspan="2"  style="border-top: none"  class="brd">移动设备</td>\n                <td  style="border-top: none">站内</td>\n            </tr>\n            <tr>\n                <td >站外</td>\n            </tr>\n        </table>\n    </td>\n    {{ if ydin }}\n    <td>{{ydin.impr}}</td>\n    <td>{{ydin.click}}</td>\n    <td>{{ydin.ctr}}%</td>\n    <td>￥{{ydin.cost}}</td>\n    <td>￥{{ydin.cpc}}</td>\n    <td>{{ydin.favcount}}</td>\n    <td>{{ ydin.carttotal}}</td>\n    <td>{{ydin.paycount}}</td>\n    <td>{{ydin.conv}}%</td>\n    <td>￥{{ydin.pay}}</td>\n    <td>{{ydin.roi}}</td>\n    {{ else }}\n        <td class="tc item_base" colspan="11">暂无数据</td>\n    {{ /if }}\n</tr>\n<tr class="hover_non_color">\n    {{ if ydout }}\n    <td>{{ydout.impr}}</td>\n    <td>{{ydout.click}}</td>\n    <td>{{ydout.ctr}}%</td>\n    <td>￥{{ydout.cost}}</td>\n    <td>￥{{ydout.cpc}}</td>\n    <td>{{ydout.favcount}}</td>\n    <td>{{ ydout.carttotal}}</td>\n    <td>{{ydout.paycount}}</td>\n    <td>{{ydout.conv}}%</td>\n    <td>￥{{ydout.pay}}</td>\n    <td>{{ydout.roi}}</td>\n    {{ else }}\n    <td class="tc item_base" colspan="11">暂无数据</td>\n    {{ /if }}\n</tr>',l=this;if(n=$(this).closest("tr"),i=$(this).parents("tr").attr("adgroup_id"),d=$(this).parents("tr").attr("campaign_id"),$(this).data("is_showing"))n.data("subdivide").remove(),delete $(this).data().is_showing,delete $(this).data().is_lock;else if(n.data("subdivide")){var e=n.data("subdivide");n.after(e),$(this).data("is_showing",1),delete $(this).data().is_lock}else $(this).data("is_showing",1),s.ajax("get_adg_split_rpt",{adgroup_id:i,camp_id:d,start_date:f.start_date,end_date:f.end_date},function(i){for(var s=i.result,d={id:campaign_id},_=0;_<s.length;_++){var p=s[_];switch(p.source_id){case 1:d.pcin=p;break;case 2:d.pcout=p;break;case 4:d.ydin=p;break;case 5:d.ydout=p}}t=a.compile(o)(d),e=$(t),n.after(e),$(n).data("subdivide",e),$(l).data("is_showing",1),delete $(l).data().is_lock})}}),o.init(),$("#goods_table").on("click",".show_chart",function(){var t,a;t=$(this).closest("tr").find(".title>a").text(),a=$(this).parents("tr").attr("adgroup_id"),o.show("宝贝明细："+t,"adgroup",$("#shop_id").val(),null,a)}),$("#goods_table").on("click",".set_follow_status",function(){var t,a,e,i=$(this).parents("tr");a=i.attr("adgroup_id"),e=i.attr("campaign_id"),t=$(this).attr("value"),t="1"==t?0:1,s.ajax("set_adg_follow",{adgroup_id:a,campaign_id:e,is_follow:t},function(t){i.find(".set_follow_status").attr("value",t.is_follow),t.is_follow?(i.find(".set_follow_status").html("&#xe675;"),i.find(".set_follow_status").attr("data-original-title","点击可取消关注"),l.show({body:"设为关注宝贝成功！"}),i.find(".set_follow_status").removeClass("hover_show")):(i.find(".set_follow_status").html("&#xe674;"),i.find(".set_follow_status").attr("data-original-title","点击可设置为关注宝贝"),i.find(".set_follow_status").addClass("hover_show"),l.show({body:"取消关注宝贝成功！"})),i.find(".set_follow_status").tooltip("show")})}),$("#goods_table").on("click",".switch_status",function(){var a=$(this).parents("tr").attr("adgroup_id"),e=$(this).text();t(["jl6/site_media/widget/confirm/confirm"],function(t){t.show({body:"确定要"+e+"推广该宝贝么？",okHide:function(){"开启"==e?y("start",a):y("stop",a)}})})}),$("#goods_table").on("click",".del_good",function(){var a=$(this).parents("tr").attr("adgroup_id");t(["jl6/site_media/widget/confirm/confirm"],function(t){t.show({body:"确定要删除该宝贝么？",okHide:function(){y("del",a)}})})}),$("#goods_table").on("click",".edit_adg_mobdiscount",function(){var a=$(this).closest("tr").find(".adg_mobdiscount"),e=a.text(),i=$(this).parents("tr").attr("campaign_id"),s=$(this).parents("tr").attr("adgroup_id");t(["jl6/site_media/service/edit_mobdiscount/edit_mobdiscount"],function(t){t.show({value:e,obj:a,campaign_id:i,adgroup_id:s})})}),$("#goods_table").on("click",".change_mnt_type",function(){var a=$(this),e=$(this).closest("tr"),i=e.attr("adgroup_id"),d=e.attr("cat_id"),o=e.attr("campaign_id"),_=e.data("camp_mnt_type"),p=$(this).attr("mnt_opt_type");"0"==$(this).attr("mnt_type")?p=0:""==p&&(p=1);var r=parseFloat(e.data("camp_max_price")).toFixed(2),c=parseFloat(e.data("camp_max_mobile_price")).toFixed(2),u=a.next().find(".limit_price").text(),m=a.next().find(".mobile_limit_price").text();"0.00"==u&&(u=r),"0.00"==m&&(m=c);var f=$(this).attr("use_camp_limit");n.show("数据加载中，请稍候..."),s.ajax("get_cat_avg_cpc",{cat_id_list:[d]},function(e){n.hide();var d=e.avg_cpc,g={default_price_pc:r,default_price_yd:c,customer_price_pc:u,customer_price_yd:m,onChange:function(t){s.ajax("update_single_adg_mnt",{adg_id:i,flag:t.mnt_opt_type,mnt_type:_,camp_id:o,use_camp_limit:t.use_camp_limit,limit_price:t.customer_price_pc,mobile_limit_price:t.customer_price_yd},function(e){l.show({body:"修改成功！"}),j(parseInt(p),parseInt(t.mnt_opt_type)),a.attr("use_camp_limit",t.use_camp_limit);var i="自动优化",s=1;a.attr("mnt_type",t.mnt_opt_type);var n=$(a).closest("tr"),d=$(a).closest("td");if(0==e.flag){if(i="未托管",s=3,a.attr("mnt_type",0),n.find(".mnt_type_true").removeClass("hide"),n.find(".mnt_type_false").addClass("hide"),0==n.find(".onekey").length){var o=n.attr("adgroup_id"),_=n.attr("campaign_id"),u='<a href="javascript:;" class="onekey" adgroup_id="'+o+'" campaign_id="'+_+'"><span><strong>一键优化</strong></span></a>';n.find(".opt_url").append(u)}}else n.find(".mnt_type_false").removeClass("hide"),n.find(".mnt_type_true").addClass("hide"),2==e.flag&&(i="只改价",s=2),n.find(".onekey").remove();a.prev().text(i),d.find(".sort_value").text(s),a.attr("mnt_opt_type",e.flag),0!=t.mnt_opt_type?(a.next().removeClass("hide"),1==t.use_camp_limit?(a.next().find(".limit_price").text(r),a.next().find(".mobile_limit_price").text(c)):(a.next().find(".limit_price").text(parseFloat(t.customer_price_pc).toFixed(2)),a.next().find(".mobile_limit_price").text(parseFloat(t.customer_price_yd).toFixed(2))),a.next(".optm_submit_time").addClass("hide"),d.find(".optm_submit_time").addClass("hide")):(a.next().addClass("hide"),d.find(".optm_submit_time").removeClass("hide"))},null,{url:"/mnt/ajax/"})}};g.avg_price=d.toFixed(2),g.min_price=Math.max((.3*d).toFixed(2),.05),g.suggest_price=1==mnt_type||3==mnt_type?(1.5*d).toFixed(2)+"~"+(2.5*d).toFixed(2):(2*d).toFixed(2)+"~"+(3*d).toFixed(2),g.opt_adgroup=!0,g.mnt_opt_type=p,g.camp_limit=f,t(["jl6/site_media/service/add_item_box/set_adg_cfg"],function(t){t.show(g)})},null,{url:"/mnt/ajax/"})}),$("#goods_table").on("mouseenter",".change_mnt_type_pop",function(){var a=$(this),e=$(a).closest("tr").attr("adgroup_id"),i=$(a).closest("tr").attr("campaign_id"),s=$("#page_type").val(),n=$(a).attr("mnt_opt_type");0==$(a).attr("mnt_type")&&(n=0);var d={adg_id:e,mnt_type:s,camp_id:i,limit_price:0,mnt_opt_type:n};t(["jl6/site_media/service/goods_list/select_mnt_type"],function(t){t.popover(a,d,function(t){l.show({body:"修改成功！"}),a.attr("mnt_type",s),a.attr("mnt_opt_type",t.flag),j(parseInt(n),parseInt(t.flag));var e=$(a).closest("tr"),i=$(a).closest("td");if(1==t.flag)$(a).prev().text("自动优化"),i.find(".sort_value").text(1),e.find(".mnt_type_false").removeClass("hide"),e.find(".mnt_type_true").addClass("hide"),i.find(".optm_submit_time").addClass("hide"),e.find(".onekey").remove();else if(2==t.flag)$(a).prev().text("只改价"),i.find(".sort_value").text(2),e.find(".mnt_type_false").removeClass("hide"),e.find(".mnt_type_true").addClass("hide"),i.find(".optm_submit_time").addClass("hide"),e.find(".onekey").remove();else if($(a).prev().text("未托管"),i.find(".sort_value").text(3),e.find(".mnt_type_true").removeClass("hide"),e.find(".mnt_type_false").addClass("hide"),i.find(".optm_submit_time").removeClass("hide"),0==e.find(".onekey").length){var d=e.attr("adgroup_id"),o=e.attr("campaign_id"),_='<a href="javascript:;" class="onekey" adgroup_id="'+d+'" campaign_id="'+o+'"><span><strong>一键优化</strong></span></a>';e.find(".opt_url").append(_)}$(a).data("popover",0),$(a).popoverList("destroy")})})}),$("#goods_table").on("click",".to_optimize",function(){var t=$(this).closest("tr"),a=t.find(".mnt_opt_type").attr("mnt_type"),e=t.find(".mnt_opt_type").attr("mnt_opt_type"),i=$(this).attr("adgroup_id");"0"==a?window.open("/web/smart_optimize/"+i,"_blank"):"2"==e||"1"==e?window.open("/mnt/adgroup_data/"+i,"_blank"):window.open("/web/smart_optimize/"+i,"_blank")}),$("#goods_table").on("click",".onekey",function(){var a=$(this).attr("adgroup_id"),e=$(this).attr("campaign_id");n.show("系统正在努力分析数据，请稍候..."),s.ajax("get_onekey_optimize",{adgroup_id:a,campaign_id:e},function(a){n.hide(),t(["jl6/site_media/service/goods_list/confirm_win"],function(t){var e=$("#modal_confirm_win");e&&e.remove(),a.update_count+a.del_count+a.add_count>0?t.show({result:a}):_.show("建议观察一段时间再优化或者手动添加关键词!")})})}),$(document).on("click","#submit_onekey",function(){var t=$(this).attr("adgroup_id"),a=$("#chk_update").is(":checked"),i=$("#chk_del").is(":checked"),s=$("#chk_add").is(":checked"),n=0,d=[];if(a){d.push("update");var o=parseInt($("#lbl_update").text());n+=o}if(i){d.push("del");var l=parseInt($("#lbl_del").text());n+=l}if(s){d.push("add");var _=parseInt($("#lbl_add").text());n+=_}0==d.length?$("#error_onekey").text("至少选择一个优化项目").fadeOut(300).fadeIn(500).removeClass("hide"):0==n?$("#error_onekey").text("当前没有优化项目").fadeOut(300).fadeIn(500).removeClass("hide"):($("#chk_update").attr("disabled","disabled"),$("#chk_del").attr("disabled","disabled"),$("#chk_add").attr("disabled","disabled"),$("#submit_onekey").attr("disabled","disabled"),$("#cancel_onekey").addClass("hide"),$("#error_onekey").addClass("hide"),e(t,d))});var e=function(t,a){if(a.length>0){var i=a[0];$("#img_"+i).removeClass("hide"),$("#sp_"+i).addClass("hide"),s.ajax("submit_onekey_optimize",{adgroup_id:t,type:i},function(s){setTimeout(function(){$("#sp_"+i).removeClass("hide").text(s.result),$("#img_"+i).addClass("hide"),a.shift(),e(t,a)},300)})}else s.ajax("finish_onekey_optimize",{adgroup_id:t},function(a){$(".adg_tr[adgroup_id="+t+"]").find(".optm_submit_time").html("<br />"+a.time+"优化过"),$("#submit_onekey").addClass("hide"),$("#finish_onekey").removeClass("hide")})};$("#goods_table thead th").unbind("click").click(function(){g>1&&(c=$(this).data("active"),c&&($(this).attr("class").indexOf("desc")>-1?(u=1,m="asc"):(u=-1,m="desc"),f.sort=c+"_"+u,b()))})},y=function(t,a){s.ajax("update_adg_status",{mode:t,mnt_type:f.mnt_type,campaign_id:f.camp_id,adg_id_list:"["+a+"]"},function(){if(l.show({body:"操作成功！"}),"start"==t)$("#goods_table tr[adgroup_id="+a+"] .lbl_online").html("推广中"),$("#goods_table tr[adgroup_id="+a+"] .switch_status").html("暂停"),$("#goods_table tr[adgroup_id="+a+"] .sort_online").text(1),$("#goods_table tr[adgroup_id="+a+"]").removeClass("gray");else if("stop"==t)$("#goods_table tr[adgroup_id="+a+"] .lbl_online").html("已暂停"),$("#goods_table tr[adgroup_id="+a+"] .switch_status").html("开启"),$("#goods_table tr[adgroup_id="+a+"] .sort_online").text(0),$("#goods_table tr[adgroup_id="+a+"]").addClass("gray");else if("del"==t){var e=$("#goods_table tr[adgroup_id="+a+"]");e.data("subdivide")&&(e.data("subdivide").addClass("hidden"),delete e.data().subdivide,e.nextAll(".hover_non_color").remove()),e.remove();var i=parseInt($(".adgroup_count").html())-1;0>=i&&(i=0),$(".adgroup_count").html(i),d.refreshSelected()}})},b=function(){n.show("数据加载中，请稍候。。。"),s.ajax("get_adgroup_list",{campaign_id:f.camp_id,page_size:f.PAGE_SIZE,page_no:f.PAGE_NO,last_day:f.last_day,start_date:f.start_date,end_date:f.end_date,sSearch:f.search_word,search_type:f.search_type,opt_type:f.opt_type,auto_hide:0,page_type:f.page_type,status_type:f.status_type,offline_type:$("#offline_type").val(),is_follow:f.is_follow,sort:f.sort},w)},w=function(t){g=t.page_info.page_count;var i,s='{{each list}}\n<tr class="adg_tr {{if $value.online_status=="offline"}}gray{{/if}}" data-camp_mnt_type="{{ $value.camp_mnt_type }}" data-camp_max_price="{{ $value.camp_max_price }}" data-camp_max_mobile_price="{{ $value.camp_max_mobile_price }}" data-id="{{$value.campaign_id}}" adgroup_id="{{$value.adgroup_id}}" campaign_id="{{$value.campaign_id}}" is_quick_opered="{{ $value.is_quick_opered }}" cat_id="{{ $value.cat_id }}">\n    <td class="check_column vm"><input type="checkbox" class="kid_check" value="{{$value.adgroup_id}}"></td>\n    <td class="td-img">\n        <a class="item_base" target="_blank" href="http://item.taobao.com/item.htm?id={{$value.item_id}}">\n            {{if $value.item_pic_url != ""}}\n                <img width="70" height="70" src="{{$value.item_pic_url}}_70x70.jpg"/>\n            {{ else }}\n                <img width="70" height="70" src=""/>\n            {{/if}}\n        </a>\n    </td>\n    <td class="item_dark">\n        {{ if list_type==-1 }}\n        <div>\n            <span class="w240 l">\n                {{if $value.camp_mnt_type == 0}}\n                  <span class="label label-default">手动</span>\n                 {{else if $value.camp_mnt_type == 1}}\n                 <span class="label label-primary">长尾</span>\n                  {{else if $value.camp_mnt_type == 2}}\n                 <span class="label label-primary">重点</span>\n                  {{else if $value.camp_mnt_type == 3}}\n                 <span class="label label-primary">ROI</span>\n                  {{else if $value.camp_mnt_type == 4}}\n                  <span class="label label-primary">无线</span>\n                  {{ /if }}\n                 {{ $value.campaign_title }}</span>\n        </div>\n        {{ /if }}\n        <span class="title w280">\n            <a id="show_title_{{$value.campaign_id}}" class="item_base to_optimize" target="_blank" adgroup_id="{{ $value.adgroup_id }}" href="javascript:;">{{$value.item_title}}</a>\n            &nbsp;￥<span class="item_price">{{$value.item_price}}</span>\n            <span class="badge r count-cr hide mt5">0</span>\n            <span class="badge r count-kw hide mt5 mr5">0</span>\n            <span class="state_opt r mr10">\n                <i class="iconfont mr5 show_chart hover_show">&#xe60c;</i>\n                <i class="iconfont show_subdivide hover_show">&#xe60a;</i>&nbsp;&nbsp;\n                <i class="iconfont set_follow_status {{if $value.is_follow != 1}}hover_show{{ /if }}"\n                    data-toggle="tooltip" data-placement="top"\n                               title="{{if $value.is_follow == 1}}点击可取消关注{{else}}点击可设置为关注宝贝{{ /if }}"\n                   value="{{ $value.is_follow }}">{{if $value.is_follow == 1}}&#xe675;{{else}}&#xe674;{{ /if }}</i>\n            </span>\n        </span>\n    </td>\n    <td><span class="hide">{{$value.impr}}</span>{{$value.impr}}</td>\n    <td><span class="hide">{{$value.click}}</span>{{$value.click}}</td>\n    <td><span class="hide">{{$value.ctr}}</span>{{$value.ctr}}%</td>\n    <td><span class="hide">{{$value.cost}}</span>￥{{$value.cost}}</td>\n    <td><span class="hide">{{$value.cpc}}</span>￥{{$value.cpc}}</td>\n    <td><span class="hide">{{$value.favcount}}</span>{{$value.favcount}}</td>\n    <td><span class="hide">{{$value.carttotal}}</span>{{$value.carttotal}}</td>\n    <td><span class="hide">{{$value.paycount}}</span>{{$value.paycount}}</td>\n    <td><span class="hide">{{$value.conv}}</span>{{$value.conv}}%</td>\n    <td><span class="hide">{{$value.pay}}</span>￥{{$value.pay}}</td>\n    <td><span class="hide">{{$value.roi}}</span>{{$value.roi}}</td>\n    <td class="vt w120">\n        {{ if $value.online_status==\'online\'}}\n        <span class="hide sort_online">1</span>\n        <span class="lbl_online">推广中&nbsp;&nbsp;</span>\n        <a href="javascript:;" class="hover_show switch_status">暂停</a>\n        {{ else }}\n        <span class="hide sort_online">0</span>\n        <span class="lbl_online">已暂停&nbsp;&nbsp;</span>\n        <a href="javascript:;" class="hover_show switch_status">开启</a>\n        {{ /if }}\n        <a href="javascript:;" class="hover_show del_good">删除</a>\n        <br/>\n        移动折扣： <span class="adg_mobdiscount" campaign_id="{{ $value.campaign_id }}">{{$value.mobile_discount}}% </span>\n        <i class="iconfont edit_adg_mobdiscount">&#xe609;</i>\n        {{ if $value.error_descr != "" }}\n        <br/><span class="item_dark">{{ $value.error_descr }}</span>\n        {{ /if }}\n    </td>\n    <td class="vt item_base" style="width: 125px;">\n        {{ if $value.mnt_type != 0 }}\n            {{ if $value.mnt_opt_type ==2 }}\n                <span class="hide sort_value">2</span>\n                <span class="opt_status">只改价</span>\n            {{ else }}\n                <span class="hide sort_value">1</span>\n                <span class="opt_status">自动优化</span>\n            {{ /if }}\n        {{ else }}\n            <span class="hide sort_value">3</span>\n            <span class="opt_status">未托管</span>\n        {{ /if }}\n        {{ if $value.camp_mnt_type != 0 }}\n        <i class="iconfont ml5 mnt_opt_type change_mnt_type" use_camp_limit="{{ $value.use_camp_limit }}" mnt_type="{{ $value.mnt_type }}" page_type="{{ list_type }}"\n             mnt_opt_type="{{ if $value.mnt_type != 0 }}{{ $value.mnt_opt_type }} {{ else }}0{{ /if }}">&#xe609;</i>\n        {{ /if }}\n        <span class="show_limit_price {{ if $value.mnt_type == 0 }} hide {{ /if }}"><br>\n        限价：<span class="limit_price pr5" data-toggle="tooltip" title="PC端限价">{{ $value.limit_price }}</span><span class="mobile_limit_price left_dotted pl5" data-toggle="tooltip" title="移动端限价">{{ $value.mobile_limit_price }}</span></span>\n         <span class="optm_submit_time {{ if $value.mnt_type!=0 }}hide{{ /if }}"><br/>{{ if $value.optm_submit_time }}{{ $value.optm_submit_time }}优化过{{ else }}目前尚未优化过{{ /if }}</span>\n\n    </td>\n    <td class="w90 opt_url">\n        <div class="dropdown">\n            <a class="dropdown-toggle to_optimize" href="javascript:;" adgroup_id="{{ $value.adgroup_id }}">\n                <span class="dropdown-value" ><strong>进入宝贝</strong></span> <span class="caret"></span>\n            </a>\n            <ul class="dropdown-menu">\n              <li class="mnt_type_true {{ if $value.mnt_type != 0 }}hide {{ /if }}"><a href="/web/smart_optimize/{{ $value.adgroup_id }}" target="_blank">智能优化</a></li>\n              <li class="mnt_type_true {{ if $value.mnt_type != 0 }}hide {{ /if }}"><a href="/web/bulk_optimize/{{ $value.adgroup_id }}" target="_blank">批量优化</a></li>\n              <li class="mnt_type_false {{ if $value.mnt_type == 0 }}hide {{ /if }}"><a href="/mnt/adgroup_data/{{ $value.adgroup_id }}" target="_blank">托管详情</a></li>\n              <li><a href="/web/select_keyword/quick?adgroup_id={{ $value.adgroup_id }}" target="_blank">快速选词</a></li>\n              <li><a href="/web/select_keyword/precise?adgroup_id={{ $value.adgroup_id }}" target="_blank">精准淘词</a></li>\n              <li><a href="/web/title_optimize/?adgroup_id={{ $value.adgroup_id }}" target="_blank">标题优化</a></li>\n              <li><a href="/web/image_optimize/{{ $value.adgroup_id }}?t=list" target="_blank">创意优化</a></li>\n            </ul>\n        </div>\n        {{ if $value.mnt_type==0 }}\n        <a href="javascript:;" class="onekey" adgroup_id="{{ $value.adgroup_id }}" campaign_id="{{ $value.campaign_id }}">\n            <span class="dropdown-value" ><strong>一键优化</strong></span>\n        </a>\n        {{ /if }}\n    </td>\n</tr>\n{{/each}}\n';i=a.compile(s)({list:t.adg_list,list_type:f.list_type}),t.mnt_info.is_mnt&&($(".mnt_num").text(t.mnt_info.mnt_num),$(".new_num").text(parseInt($("#mnt_max_num").val())-t.mnt_info.mnt_num)),p&&(p.fnClearTable(),p.fnDestroy()),$("#goods_table tbody").html(i),n.hide();var o={page_row:t.page_info.page,page_list:t.page_info.page_xrange,page_count:t.page_info.page_count,page_size:50};e.init(o,x),$(".adgroup_count").html(t.page_info.record_count),d.fixPosition(),t.adg_list.length>0?(e.show(),d.show()):(e.hide(),d.hide()),d.setSelected(0),k(),$('[data-toggle="tooltip"]').tooltip({html:!0})},x=function(t){f.PAGE_NO=t,b()},k=function(){p=$("#goods_table").dataTable({bRetrieve:!0,bPaginate:!1,aaSorting:[[r[c],m]],bFilter:!1,bInfo:!1,bAutoWidth:!1,language:{emptyTable:"没有数据"},aoColumns:[{bSortable:!1},{bSortable:!1},{bSortable:!1},{bSortable:!0,sType:"custom",sSortDataType:"custom-text"},{bSortable:!0,sType:"custom",sSortDataType:"custom-text"},{bSortable:!0,sType:"custom",sSortDataType:"custom-text"},{bSortable:!0,sType:"custom",sSortDataType:"custom-text"},{bSortable:!0,sType:"custom",sSortDataType:"custom-text"},{bSortable:!0,sType:"custom",sSortDataType:"custom-text"},{bSortable:!0,sType:"custom",sSortDataType:"custom-text"},{bSortable:!0,sType:"custom",sSortDataType:"custom-text"},{bSortable:!0,sType:"custom",sSortDataType:"custom-text"},{bSortable:!0,sType:"custom",sSortDataType:"custom-text"},{bSortable:!0,sType:"custom",sSortDataType:"custom-text"},{bSortable:!1},{bSortable:!1},{bSortable:!1}],fnDrawCallback:function(){delete $("#show_subdivide_all").data().is_showing,$.map($("#goods_table .show_subdivide"),function(t){delete $(t).data().is_showing})},initComplete:function(){$.fn.dataTableExt.afnSortData["custom-text"]=function(t,a){return $.map(t.oApi._fnGetTrNodes(t),function(e,i){var s=t.oApi._fnGetTdNodes(t,i)[a],n=Number($(s).find("span:first").text());return g>1?0:n})}}}),new FixedHeader(p)},C=function(t,a,e,i,s,n,d){f.camp_id=e,f.start_date=t,f.end_date=a,f.search_word=i,f.PAGE_NO=1,f.opt_type=s,f.status_type=n,f.is_follow=d,b()},j=function(t,a){var e=parseInt($(".mnt_num").text()),i=parseInt($(".new_num").text());t&&!a&&($(".mnt_num").text(e-1),$(".new_num").text(i+1)),!t&&a&&($(".mnt_num").text(e+1),$(".new_num").text(i-1))};return{init:h,getPageData:x,filterData:C}});