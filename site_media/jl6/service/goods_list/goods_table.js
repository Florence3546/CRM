define("jl6/site_media/service/goods_list/goods_table",["jl6/site_media/service/goods_list/goods_list","jl6/site_media/plugins/artTemplate/template","jl6/site_media/service/goods_list/select_tool","jl6/site_media/plugins/data-tables/dataTableExt","jl6/site_media/widget/ajax/ajax"],function(t,e,a,i,d){"use strict";function c(t){if(""==t.errMsg){var e;"keyword"==t.type?e=$("#goods_table").find(".count-kw"):"creative"==t.type&&(e=$("#goods_table").find(".count-cr")),$(e).each(function(){var e=$(this).parents("tr").attr("adgroup_id"),a=0;t.result_dict.hasOwnProperty(e)&&(a=t.result_dict[e]),$(this).html(a),$(this).hasClass("hide")?$(this).removeClass("hide"):$(this).fadeOut(500).fadeIn(500)})}}var s=function(i,s,h,o){var l,r='<table class="table table-bordered icon_hover_show table-hover box_fix_fixedHeader" id="goods_table">\n  <thead>\n      <tr>\n          <th class="choose_column"><input type="checkbox" class="select-all"></th>\n          <th><div>宝贝图片</div></th>\n          <th class="w280">\n            <div>标题\n            <a id="show_subdivide_all" class="r base_color b" href="javascript:;"><i class="iconfont mr5">&#xe60a;</i>细分</a></div>\n          </th>\n          <th data-active="impressions"><div>展现量</div></th>\n          <th data-active="click"><div>点击量</div></th>\n          <th data-active="ctr"><div>点击率</div></th>\n          <th data-active="cost"><div>总花费</div></th>\n          <th data-active="ppc"><div>PPC</div></th>\n          <th data-active="favcount"><div>收藏量</div></th>\n          <th data-active="carttotal"><div>购物车数</div></th>\n          <th data-active="paycount"><div>成交量</div></th>\n          <th data-active="conv"><div>转化率</div></th>\n          <th data-active="pay"><div>成交额</div></th>\n          <th data-active="roi"><div>ROI</div></th>\n          <th class="w120"><div>推广状态</div>\n          </th>\n          <th><div>优化状态</div>\n          </th>\n          <th class="w80">操作</th>\n      </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td colspan="17">\n          <div class="tc">\n            <img src="/site_media/jl6/static/images/ajax_loader.gif" alt=""><br>\n            <span>请稍候...</span>\n          </div>\n      </td>\n    </tr>\n  </tbody>\n</table>\n';l=e.compile(r)(),$(".ad-group-table").html(l),t.init(i,s,h,o);var v=function(){t.getPageData()};a.init(i,o,v),$(document).on("click",".select-all",function(){$(this).prop("checked")?($("body").find(".select-all").prop("checked",!0),$(".kid_check").prop("checked",!0),$(".kid_check").parents("td").addClass("tr-checked"),a.setSelected($(".kid_check").length)):($("body").find(".select-all").prop("checked",!1),$(".kid_check").prop("checked",!1),$(".kid_check").parents("td").removeClass("tr-checked"),a.setSelected(0))}),$("#goods_table").on("change",".kid_check",function(){var t=$("input:checkbox[class=kid_check]:checked").length;a.setSelected(t),t==$(".kid_check").length?$("body").find(".select-all").prop("checked",!0):$("body").find(".select-all").prop("checked",!1),$(this).prop("checked")?$(this).parents("td").addClass("tr-checked"):$(this).parents("td").removeClass("tr-checked")}),setTimeout(n,2e3),$("#show_kw").on("click",function(){$(this).attr("flag","true"),$(this).text("刷新关键词数");var t=[];$("#goods_table").find(".kid_check").each(function(){var e=$(this).parents("tr").attr("adgroup_id");t.push(e)}),d.ajax("get_adg_status",{type:"keyword",adg_id_list:"["+t.toString()+"]"},c)}),$("#show_cr").on("click",function(){$(this).attr("flag","true"),$(this).text("刷新创意数");var t=[];$("#goods_table").find(".kid_check").each(function(){var e=$(this).parents("tr").attr("adgroup_id");t.push(e)}),d.ajax("get_adg_status",{type:"creative",adg_id_list:"["+t.toString()+"]"},c)})},n=function(){$(".width100").animate({width:24},1e3,function(){$(".width100").removeAttr("style"),$(".width100").removeClass("width100"),$(".sign-left>a").addClass("sign-content")})},h=function(e,a,i,d,c,s,n){t.filterData(e,a,i,d,c,s,n)};return{init:s,filterData:h}});