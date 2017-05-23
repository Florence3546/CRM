define("jl6/site_media/service/mnt/mnt_campaign",["require","jl6/site_media/plugins/jquery.json-2.4.min","jl6/site_media/plugins/moment/moment.min","jl6/site_media/service/common/common","jl6/site_media/service/goods_list/goods_table","jl6/site_media/widget/ajax/ajax","jl6/site_media/widget/loading/loading","jl6/site_media/widget/lightMsg/lightMsg","jl6/site_media/widget/alert/alert","jl6/site_media/service/mnt/edit_camp_price","jl6/site_media/widget/confirm/confirm","jl6/site_media/service/add_item_box/add_item_box","jl6/site_media/plugins/artTemplate/template","jl6/site_media/widget/tagEditor/tagEditor","jl6/site_media/service/report_detail/report_detail","jl6/site_media/plugins/jslider/js/jquery.slider"],function(t,a,e,i,n,o,d,r,c,s,_,l,p,m,u){"use strict";var g,h=$("#campaign_id").val(),f=e().subtract(7,"days").format("YYYY-MM-DD"),v=e().subtract(1,"days").format("YYYY-MM-DD"),x=(parseInt($("#mnt_index").val()),parseInt($("#mnt_type").val())),b=(parseInt($("#mnt_opter").val())?parseInt($("#mnt_opter").val()):0,parseFloat($("#max_price_pc").text())),w=parseFloat($("#max_price_yd").text()),y=-1,j="",k=-1,C=!1,M=function(){F(0),setInterval(function(){F(0)},3e5),$(".rt_rpt").on("click",".update_cache",function(){F(1)}),Y(f,v),n.init(x,f,v,h),$("#select_days").on("change",function(){f=e($(this).daterangepicker("getRange").start).format("YYYY-MM-DD"),v=e($(this).daterangepicker("getRange").end).format("YYYY-MM-DD"),Y(f,v),I()});var a=parseFloat($("#mnt_bid_factor").val());$(".jslider-box input").slider({from:0,to:100,skin:"power",onstatechange:function(t){S(t)},callback:function(t){_.show({body:"确定要修改宝贝推广意向吗？",okHide:function(){t!=a&&o.ajax("change_mntcfg_type",{campaign_id:h,mnt_bid_factor:t,mnt_type:x},function(){$("#mnt_bid_factor").val(t),r.show({body:"设置宝贝推广意向成功！"})},null,{url:"/mnt/ajax/"})},cancleHide:function(){$(".jslider-box input").slider("value",a),S(a)}})}}),$("#search_btn").click(function(){I()}),$("#search_val").keyup(function(t){13==t.keyCode&&I()}),$(".edit_platform").on("click",function(){d.show("正在获取计划投放平台"),o.ajax("get_camp_platform",{camp_id:h},function(a){d.hide();var e=a.platform,i=a.can_set_nonsearch;e?t(["jl6/site_media/service/edit_camp_platform/edit_camp_platform"],function(t){t.show({pc_insite_search:e.pc_insite_search,pc_outsite_nonsearch:e.pc_outsite_nonsearch,pc_insite_nonsearch:e.pc_insite_nonsearch,outside_discount:e.outside_discount,yd_outsite:e.yd_outsite,pc_outsite_search:e.pc_outsite_search,mobile_discount:e.mobile_discount,yd_insite:e.yd_insite,can_set_nonsearch:i,onChange:function(t){d.show("正在设置计划投放平台"),o.ajax("update_camp_platform",{camp_id:h,platform_dict:$.toJSON(t)},function(t){d.hide(),t.is_success?r.show({body:"修改计划投放平台成功！"}):c.show("修改计划投放平台失败，请联系客服！")},null,{url:"/web/ajax/"})}})}):c.show("淘宝接口不稳定，请稍后再试")},null,{url:"/web/ajax/"})}),$(".edit_schedule").on("click",function(){d.show("正在获取分时折扣"),o.ajax("get_camp_schedule",{camp_id:h},function(a){d.hide(),a.schedule_str?t(["jl6/site_media/service/edit_camp_schedule/edit_camp_schedule"],function(t){t.show({schedules:a.schedule_str,onChange:function(t){o.ajax("update_camp_schedule",{camp_id:h,schedule_str:t},function(t){d.hide(),""==t.errMsg?r.show({body:"修改计划投放时间成功!"}):c.show("修改计划投放时间失败！")},null,{url:"/web/ajax/"})}})}):c.show("淘宝接口不稳定，请稍后再试")},null,{url:"/web/ajax/"})}),$(".edit_area").on("click",function(){var a=function(t,a){o.ajax("update_camp_area",{camp_id:h,area_ids:t,area_names:a},function(a){if(d.hide(),a.is_success){{$(".edit_area").data("area_ids",t)}r.show({body:"修改计划投放地域成功！"})}else c.show("修改计划投放地域失败！")},null,{url:"/web/ajax/"})};t(["jl6/site_media/service/edit_camp_area/edit_camp_area"],function(t){if($(".edit_area").data("area_ids")){var e=$(".edit_area").data("area_ids");t.show({area_ids:e,onChange:a})}else d.show("正在获取投放地域信息,请稍候..."),o.ajax("get_camp_area",{camp_id:h},function(e){d.hide(),e.area?($(".edit_area").data({is_lock:1,area_ids:e.area}),t.show({area_ids:e.area,onChange:a})):c.show("淘宝接口不稳定，请稍后再试")},null,{url:"/web/ajax/"})})}),u.init(),$("#campaign_detail").click(function(){u.show("计划明细："+$("#campaign_title").text(),"campaign",$("#shop_id").val(),$("#campaign_id").val())}),$(".edit_camp_price").click(function(){var a=$(this).attr("type"),e=$(this);if("budget"==a){var i=$(this).data("smooth"),n=$(this).data("budget");t(["jl6/site_media/service/edit_camp_budget/edit_camp_budget"],function(t){t.show({campaign_id:h,budget:n,is_smooth:i,mnt_type:x,onChange:function(t,a){if(t!=n||a!=i){var d;d="0"==a?"false":"true",o.ajax("modify_camp_budget",{camp_id:h,use_smooth:d,budget:t},function(i){return i.errMsg?void c.show(i.errMsg):($("#budget").text(2e7>t?t+"元":"不限"),e.data("budget",t),e.data("smooth",a),void r.show({body:"修改日限额成功！"}))})}}})})}else if("max_price"==a){var d,_="关键词最高限价",l=.2,p=99.99;d=1==x||3==x?"最低"+l+"元，推荐在"+parseFloat(1.5*g).toFixed(2)+"~"+parseFloat(2.5*g).toFixed(2)+"元之间":"最低"+l+"元，推荐在"+parseFloat(2*g).toFixed(2)+"~"+parseFloat(3*g).toFixed(2)+"元之间";var m=$(this).attr("max_price_pc"),u=$(this).attr("max_price_yd");s.show({title:_,price_desc:d,max_price:p,min_price:l,default_price_pc:m,default_price_yd:u,type:a,onChange:function(t,a){var e=$.toJSON({max_price:t,mobile_max_price:a});o.ajax("update_cfg",{campaign_id:h,submit_data:e,mnt_type:x},function(){$(".edit_camp_price[type=max_price]").attr("max_price_pc",t).attr("max_price_yd",a),$("#max_price_pc").text(t),$("#max_price_yd").text(a),r.show({body:"设置关键词限价成功！"})},null,{url:"/mnt/ajax/"})}})}}),$(document).on("click",".online_status",function(){var t=parseInt($(this).attr("mode")),a=[h],e=t?"启动推广":"暂停推广";_.show({body:"确定"+e+"当前计划吗？",okHide:function(){o.ajax("update_camps_status",{camp_id_list:a,mode:t},function(a){""==a.errMsg?(0==t?($(".lbl_online_status").text("已暂停"),$(".online_status").text("开启").attr("mode",1),$(".quick_oper").addClass("hide")):($(".lbl_online_status").text("推广中"),$(".online_status").text("暂停").attr("mode",0),$(".quick_oper").removeClass("hide")),r.show({body:e+"计划成功！"})):c.show("修改失败：淘宝接口不稳定，请稍后再试")},null,{url:"/web/ajax/"})}})}),$(document).on("click",".mnt_status",function(){var t="确定“取消托管”该计划吗？",a=Number($(this).attr("mnt_days"));a>=-10&&0>a?t="该计划只托管了"+Math.abs(a)+"天，"+t:0==a&&(t="该计划托管不满1天，"+t);var e="<div class='lh25'>1、效果需要一定周期培养，建议不要短期托管或频繁更换策略</div><div class='lh25'>2、系统会停止优化您的宝贝，但不会改变计划和宝贝的推广状态</div><div class='lh25'>3、取消后可以重新开启托管，但需要重新设置计划、宝贝、策略</div>";_.show({title:t,body:e,cancleStr:"不取消托管",okStr:"取消托管",okHide:function(){o.ajax("mnt_campaign_setter",{campaign_id:h,set_flag:0,mnt_type:x},function(){window.location.href="/mnt/mnt_campaign/"+h},null,{url:"/mnt/ajax/"})}})}),$(document).on("click",".mnt_rt",function(){var t=$(this),a=$(this).data("mntrt");a="0"==a?1:0,_.show({body:"确定"+t.text()+"实时优化吗？",okHide:function(){o.ajax("update_rt_engine_status",{campaign_id:h,status:a,mnt_type:x},function(){r.show({body:t.text()+"实时优化成功！"}),t.data("mntrt",a),a?($(".mnt_rt").text("关闭"),$(".lbl_mnt_rt").text("已开启")):($(".mnt_rt").text("开启"),$(".lbl_mnt_rt").text("已关闭"))},null,{url:"/mnt/ajax/"})}})}),$(document).on("click",".quick_oper_long",function(){if(!$(this).hasClass("disabled")){var t=parseInt($(this).attr("stgy")),a="系统会定期自动改价换词，您确定现在就要人工干预吗？";_.show({body:a,okHide:function(){o.ajax("quick_oper",{campaign_id:h,mnt_type:x,stgy:t},function(){$(".sign-oper").attr("data-original-title","今日已调整过，每日只能调整一次"),$(".quick_oper_long").addClass("disabled").addClass("btn-default"),$(".quick_oper_long").removeAttr("stgy"),$(".quick_oper_long").removeClass("quick_oper_long").removeClass("btn-primary")},null,{url:"/mnt/ajax/"})}})}}),$(".add_adgroup").click(function(){if(!C){var t={mnt_type:x,adg_counts:Number($(".new_num").text())||0,cur_counts:0};if("0"!=x&&0==t.adg_counts)return c.show("已达到托管上限，若要继续托管，请先删除一些已托管宝贝！"),!1;var a={max_price_pc:b.toFixed(2),max_price_yd:w.toFixed(2),mnt_opt_type:1};l.setStrategy(a),l.init(t);var e={campaign_id:h,page_no:1,page_size:50,sSearch:"",exclude_existed:1,auto_hide:0};l.loadItemList(e),x&&l.loadAdgList(e),C=!0}$(document.body).css("overflow","hidden"),window.scrollTo(0,0),$(".add_adg_box").show(),$(".add_adg_box").css("height",$(window).height()-88),$(".add_adg_box").animate({top:"88px"},500)}),$(".cancle_add_adgroup").click(function(){$(".add_adg_box").animate({top:$(window).height()},500,function(){$(".add_adg_box").hide(),$(document.body).css("overflow","auto")})}),$(".submit_adgroup").click(function(){q()}),$(window).resize(function(){$(".add_adg_box").css("height",$(window).height()-88)}),$("#to_mnt_main").click(function(){window.location.href="/mnt/mnt_campaign/"+h}),$("[data-toggle='tooltip']").tooltip({html:!0}),o.ajax("get_recommend_price",{campaign_id:h,mnt_type:x},function(t){g=t.cat_cpc}),$("#search_status_type").on("change",function(t,a){j=a,I()}),$("#search_opt_type").on("change",function(t,a){y=a,I()}),$("#search_follow_type").on("change",function(t,a){k=a,I()}),S(parseInt($("#mnt_bid_factor").val()))},I=function(){var t=$("#search_val").val();n.filterData(f,v,h,t,y,j,k)},Y=function(t,a){o.ajax("get_base_rpt",{campaign_id:h,rpt_days:15,start_date:t,end_date:a},function(t){if(""==t.errMsg){var a,e='<tr>\r\n    <td rowspan="4">　　</td>\r\n    <td>总花费　</td>\r\n    <td>展现量　</td>\r\n    <td>点击量　</td>\r\n    <td>点击率　</td>\r\n    <td>PPC&nbsp;<i class="iconfont f14" data-toggle="tooltip" data-placement="top" data-trigger="hover" title="平均点击花费">&#xe61a;</i>　</td>\r\n    <td>购物车总数</td>\r\n</tr>\r\n<tr class="data">\r\n    <td class="b">￥{{ cost }}</td>\r\n    <td>{{ impr }}</td>\r\n    <td>{{ click }}</td>\r\n    <td>{{ ctr }}%</td>\r\n    <td>{{ cpc }}</td>\r\n    <td>{{ carttotal }}</td>\r\n</tr>\r\n<tr>\r\n    <td>成交额</td>\r\n    <td>收藏量</td>\r\n    <td>成交量</td>\r\n    <td>转化率</td>\r\n    <td>ROI&nbsp;<i class="iconfont f14" data-toggle="tooltip" data-placement="top" data-trigger="hover" title="投资回报率">&#xe61a;</i></td>\r\n    <td>成交量单价&nbsp;<i class="iconfont f14" data-toggle="tooltip" data-placement="top" data-trigger="hover" title="成交量单价 = 成交额/成交量">&#xe61a;</i></td>\r\n</tr>\r\n<tr class="data">\r\n    <td class="b"><span data-toggle="tooltip" data-placement="top" data-trigger="hover" title="直接成交金额: {{ directpay }}<br/>间接成交金额: {{ indirectpay }}">￥<span class="pay">{{ pay }}</span></span> </td>\r\n    <td><span data-toggle="tooltip" data-placement="top" data-trigger="hover" title="店铺收藏数: {{ favshopcount }}<br/>宝贝收藏数: {{ favitemcount }}">\r\n      {{ favcount }}\r\n      </span></td>\r\n    <td><span data-toggle="tooltip" data-placement="top" data-trigger="hover" title="直接成交笔数: {{ directpaycount }}<br/>间接成交笔数: {{ indirectpaycount }}">{{ paycount }}</span></td>\r\n    <td>{{ conv }}%</td>\r\n    <td>{{ roi }}</td>\r\n    <td>{{ avg_pay }}</td>\r\n</tr>';a=p.compile(e)(t.result_dict),$(".total_rpt").html(a),$('[data-toggle="tooltip"]').tooltip({html:!0})}},null,{url:"/mnt/ajax/"})},F=function(t){o.ajax("get_rt_rpt",{campaign_id:h,update_cache:t},function(t){if(""==t.errMsg){var a,e='<tr>\r\n    <td>实时数据：</td>\r\n    <td>花费：{{ cost }}元</td>\r\n    <td>展现量：{{ impr }}</td>\r\n    <td>点击量：{{ click }}</td>\r\n    <td>点击率：{{ ctr }}%</td>\r\n    <td>PPC：{{ cpc }}元</td>\r\n    <td>购物车总数：{{ carttotal }}</td>\r\n    <td>成交额：<span data-toggle="tooltip" data-placement="top" data-trigger="hover" title="直接成交金额: {{ directpay }}<br/>间接成交金额: {{ indirectpay }}">{{ pay }}</span>元</td>\r\n    <td>收藏量：<span data-toggle="tooltip" data-placement="top" data-trigger="hover" title="店铺收藏数: {{ favshopcount }}<br/>宝贝收藏数: {{ favitemcount }}">{{ favcount }}</span>次</td>\r\n    <td>成交量：<span data-toggle="tooltip" data-placement="top" data-trigger="hover" title="直接成交笔数: {{ directpaycount }}<br/>间接成交笔数: {{ indirectpaycount }}">{{ paycount }}</span>笔</td>\r\n    <td class="w30 tr">\r\n        <div class="rel update_cache" data-toggle="tooltip" data-placement="top" data-trigger="hover" title="系统每5分钟自动刷新一次，点击图标会立即刷新。<br/>实时数据成交低不要急，有些点击不会马上转化的哦">\r\n	        <i class="iconfont f24 dib lh30 b vh">&#xe64c;</i>\r\n<!-- 	        <i class="iconfont f24 lh30 abs r0 b clock-long-hand">&#xe64e;</i>\r\n	        <i class="iconfont f24 lh30 abs r0 b clock-short-hand">&#xe64b;</i> -->\r\n            <i class="clock-long-hand">&emsp;</i>\r\n            <i class="clock-short-hand">&emsp;</i>\r\n        </div>\r\n    </td>\r\n</tr>\r\n';a=p.compile(e)(t.result),$(".rt_rpt").html(a),$('[data-toggle="tooltip"]').tooltip({html:!0})}})},q=function(){if(!l.getSelectCounts())return c.show("请选择托管宝贝！"),!1;var t=!1;return $('input[name="adg_title"]').each(function(){return 0==$.trim($(this).val()).length||"正在获取..."==$(this).val()?(c.show("创意标题不能为空!"),void(t=!0)):parseInt($(this).attr("char_delta"))<0?(c.show("创意标题的长度不能超过20个汉字!"),void(t=!0)):void 0}),t?!1:($(".opt_btn").addClass("hide"),d.show("数据提交中，请稍候..."),void N())},S=function(t){var a=Math.abs(t-50);50>t?($("#big_factor_name").text("偏向ROI"),$("#big_factor_value").removeClass("hide")):50==t?($("#big_factor_name").text("均衡模式"),$("#big_factor_value").addClass("hide"),$("#big_factor_value").text("0%")):($("#big_factor_name").text("偏向流量"),$("#big_factor_value").removeClass("hide")),$("#big_factor_value").text((a/50*100).toFixed(0)+"%")},D=0,N=function(){var t=l.getMntAdgInfo();o.ajax("update_mnt_adg",{mnt_adg_dict:JSON.stringify(t.mnt_adg_dict),update_creative_dict:JSON.stringify(t.update_creative_dict),new_creative_list:JSON.stringify(t.new_creative_list),camp_id:h,mnt_type:x,flag:2},function(t){O(),D=parseInt(t.success_count)},null,{url:"/mnt/ajax/"})},O=function(){var t=l.getNewItemDict();o.ajax("add_new_item",{new_item_dict:JSON.stringify(t),camp_id:h,mnt_type:x},function(t){if(d.hide(),$(".add_item_box").addClass("hide"),$(".result_box").removeClass("hide"),t.failed_count){var a,e='<div class="error_popover w600 bdd f13" style="overflow-y: auto;">\r\n    {{ each error_list as value}}\r\n    <div class="error_adg bbd  l">\r\n        <div class="l p2 err_img brc">\r\n            <img src="{{ value[0] }}_80x80.jpg"/>\r\n        </div>\r\n        <div class="l p10 err_desc w500">\r\n            <div class="adg_title b">{{ value[1] }}</div>\r\n            <div class="red mt10"><strong>错误信息：</strong>{{ value[2] }}</div>\r\n        </div>\r\n    </div>\r\n    {{ /each }}\r\n</div>';a=p.compile(e)({error_list:t.failed_item_dict}),$(".error_list").html(a),$("#error_msg").removeClass("hide")}$("#item_success_count").text(t.success_count+D),$("#item_failed_count").text(t.failed_count),$(".commit_result").fadeIn(200)},null,{url:"/mnt/ajax/"})};return{init:M}});