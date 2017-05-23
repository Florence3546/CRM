define("jl6/site_media/service/auto_rob_rank/auto_rob_rank",["require","jl6/site_media/service/common/top_bar_event","jl6/site_media/service/common/common","jl6/site_media/plugins/artTemplate/template","jl6/site_media/service/keyword/keyword","jl6/site_media/plugins/moment/moment.min","jl6/site_media/plugins/jslider/js/jquery.slider","jl6/site_media/widget/selectSort/selectSort","jl6/site_media/plugins/jquery-pin/jquery.pin.min"],function(t,a,e,s,c,r){"use strict";var o,i,n=r().subtract(7,"days").format("YYYY-MM-DD"),d=r().subtract(1,"days").format("YYYY-MM-DD");c.Row.prototype.setRowUp=function(t,a){this.sortSpan.text(void 0!=a?a:1),$(this.nRow).addClass("top")},c.Row.prototype.setRowDown=function(){this.sortSpan.text(0),$(this.nRow).removeClass("top")},c.Table.prototype.setChecked=function(){},c.Table.prototype.checkCallback=function(){},c.Table.prototype.checkedRow=function(){var t=[];return this.table.find("tbody tr:not(.unsort)").each(function(){t.push($(this))}),t},c.Table.prototype.COLUM_DICT={keyword:2,max_price:3,max_mobile_price:4,rank:5,rob:6,qscore:7,create_days:8,impressions:9,click:10,ctr:11,cost:12,ppc:13,cpm:14,avgpos:15,favcount:16,s_favcount:17,a_favcount:18,favctr:19,favpay:20,carttotal:21,paycount:22,z_paycount:23,j_paycount:24,pay:25,z_pay:26,j_pay:27,conv:28,roi:29,g_pv:30,g_click:31,g_ctr:32,g_coverage:33,g_roi:34,g_cpc:35,g_competition:36,g_paycount:37};var l=function(){e.loading.show("正在获取数据,请稍候..."),e.sendAjax.ajax("keyword_locker_list",{start_date:n,end_date:d,source:$("#data_source button.active").data().source},u)},p=function(){$("#select_keyword_days").on("change",function(){return n=r($(this).daterangepicker("getRange").start).format("YYYY-MM-DD"),d=r($(this).daterangepicker("getRange").end).format("YYYY-MM-DD"),n==d&&0===r(d).diff(new Date,"days")?(e.loading.show("正在获取实时数据,请稍候..."),void e.sendAjax.ajax("get_rankkw_rtrpt",{start_date:n,end_date:d},function(t){e.loading.hide();var a=["impr","click","ctr","cost","cpc","cpm","avgpos","favcount","favshopcount","favitemcount","favctr","favpay","carttotal","paycount","directpaycount","indirectpaycount","pay","directpay","indirectpay","conv","roi"];for(var s in i.keyword_list){var c=i.keyword_list[s];for(var r in a){var o=a[r];c[o]=t.result_dict[c.keyword_id][o]}}u(i)})):void l()}),$("#data_source button").on("click",function(){$("#data_source button.active").removeClass("active btn-primary").addClass("btn-default"),$(this).addClass("active btn-primary"),l()}),$(".alert").on("closed.bs.alert",function(){o.fixHeader.fnUpdate()})},u=function(t){e.loading.hide();var a,r='{{if keywordList.length}}\n<tr class="unsort">\n    <td></td>\n    <td class="hide"></td>\n    <td>\n        <div class="input-group custom_search">\n            <span class="select_warp btn-group" id="search_type">\n                <button type="button" class="tip btn btn-default" data-toggle="dropdown">模糊</button>\n                <ul class="dropdown-menu">\n                    <li data-value="0"><span>模糊</span></li>\n                    <li data-value="1"><span>精准</span></li>\n                </ul>\n            </span>\n            <input type="text" class="form-control search_val" placeholder="输入关键词">\n            <span class="input-group-btn search_btn">\n                <button class="btn btn-default" type="button"><i class="iconfont f16">&#xe618;</i></button>\n            </span>\n        </div>\n    </td>\n    <td></td>\n    <td></td>\n    <td></td>\n    <td></td>\n    <td></td>\n    <td></td>\n    <td></td>\n    <td></td>\n    <td></td>\n    <td></td>\n    <td></td>\n    <td></td>\n    <td></td>\n    <td></td>\n    <td></td>\n    <td></td>\n    <td></td>\n    <td></td>\n    <td></td>\n    <td></td>\n    <td></td>\n    <td></td>\n    <td></td>\n    <td></td>\n    <td></td>\n    <td></td>\n    <td></td>\n    <td></td>\n    <td></td>\n    <td></td>\n    <td></td>\n    <td></td>\n    <td></td>\n    <td></td>\n    <td></td>\n</tr>\n{{each keywordList}}\n<tr id="{{$value.keyword_id}}" data-adgroup_id="{{$value.adgroup_id}}" data-campaign_id="{{$value.campaign_id}}" data-roi="{{$value.roi}}" data-cpc="{{$value.g_cpc | format:\'1,100,2\'}}" data-ctr="{{$value.ctr}}" data-click="{{$value.click}}" data-qscore="{{$value.qscore_dict.qscore}}"\n    data-wireless_qscore="{{$value.qscore_dict.wireless_qscore}}" data-max_price="{{$value.max_price}}" data-max_mobile_price="{{$value.max_mobile_price}}" data-g_click="{{$value.g_click}}" data-match="{{$value.match_scope}}" data-new_price="{{$value.new_price}}" data-new_mobile_price="{{$value.new_mobile_price}}">\n    <td style="padding:2px;" class="img_box tc">\n        {{if $value.mnt_opt_type == 1}}\n        <a href="/mnt/adgroup_data/{{$value.adgroup_id}}/" target="_blank">\n            {{/if}}\n            {{if $value.mnt_opt_type == 2}}\n             <a href="/web/smart_optimize/{{$value.adgroup_id}}/" target="_blank">\n            {{/if}}\n            {{if $value.mnt_opt_type == 0}}\n            <a href="/mnt/adgroup_data/{{$value.adgroup_id}}/" target="_blank">\n            {{/if}}\n            <img  height="60" width="60" src="{{$value.pic_url}}_60x60.jpg_.webp" data-title="{{$value.title}}" data-camp-title="{{$value.camp_title}}" data-price="{{$value.price}}" data-pic-url="{{$value.pic_url}}"></a>\n    </td>\n    <td class="hide  sorting_1">\n        <span class="hide main_sort">{{if $value.new_price>$value.max_price }}2{{/if}}{{if $value.max_price>$value.new_price }}1{{/if}}{{if $value.max_price==$value.new_price }}0{{/if}}</span>\n    </td>\n    <td>\n        <a target="_blank" class="word" href="http://subway.simba.taobao.com/#!/tools/insight/queryresult?kws={{$value.word}}">\n                {{$value.word}}\n            </a> {{if $value.qscore_dict.wireless_matchflag == "2"}}\n        <span class="iconfont" data-toggle="tooltip" data-placement="right" data-trigger="hover" title="移动首屏展示机会:机会在手机淘宝网和淘宝客户端搜索结果中屏展示">&#xe625;</span> {{/if}} {{if $value.qscore_dict.wireless_matchflag == "4"}}\n        <span class="iconfont" data-toggle="tooltip" data-placement="right" data-trigger="hover" title="移动首屏展示机会:有机会在手机淘宝网和淘宝客户端搜索结果第一屏展示">&#xe625;</span> {{/if}} {{if $value.qscore_dict.pc_left_flag}}\n        <span class="iconfont" data-toggle="tooltip" data-placement="right" data-trigger="hover" title="淘宝豆腐块展示机会:有机会在淘宝搜索关键词结果页左侧展示">&#xe626;</span> {{/if}}\n        <i class="iconfont chart">&#xe60c;</i>\n    </td>\n    <td class="sort_custom"><span class="hide max_price">{{$value.max_price}}</span>{{if $value.is_default_price}}<span class="tag tag-gary">默</span>{{/if}}<span class="max_price">{{$value.max_price}}</span></td>\n    <td class="sort_custom"><span class="hide max_mobile_price">{{$value.max_mobile_price}}</span>{{if $value.mobile_is_default_price}}<span class="tag tag-gary">折</span>{{/if}}<span class="max_mobile_price">{{$value.max_mobile_price}}</span></td>\n    <td class="sort_custom ">\n        <span class="hide">0</span>\n        <div class="rank">\n            <span class="pc_rank_desc db pct50 l">--</span>\n            <span class="hide pc_rank"></span>\n            <span class="left_dotted db pct50 l mobile_rank_desc">--</span>\n            <span class="hide mobile_rank"></span>\n        </div>\n    </td>\n    <td class="rob_rank tl" style="text-align:left;">\n        <div>\n            <span class="dib w50 platform">\n                        {{if $value.platform == \'pc\'}}\n                        计算机\n                        {{else}}\n                        移动\n                        {{/if}}\n            </span>\n            <span class="dib w80">限价<span class="limit_price">{{$value.limit_price}}</span>元</span>\n            <span class="r"><a href="javascript:;" class="rob_record">详情</a></span>\n        </div>\n        <div>\n            <span class="exp_rank_start">{{$value.exp_rank_start}}</span>&ensp;-&ensp;<span class="exp_rank_end">{{$value.exp_rank_end}}</span>\n            <span class="r"><a href="javascript:;" class="rob_set">设置</a></span>\n        </div>\n    </td>\n    <td class="qscore sort_custom" pc_qscore="{{$value.qscore_dict.qscore}}" pc_creative_score="{{$value.qscore_dict.creativescore}}" pc_rele_score="{{$value.qscore_dict.kwscore}}" pc_cvr_score="{{$value.qscore_dict.cvrscore}}" yd_qscore="{{$value.qscore_dict.wireless_qscore}}"\n        yd_creative_score="{{$value.qscore_dict.wireless_creativescore}}" yd_rele_score="{{$value.qscore_dict.wireless_relescore}}" yd_cvr_score="{{$value.qscore_dict.wireless_cvrscore}}" matchflag="{{$value.qscore_dict.wireless_matchflag}}" plflag="{{$value.qscore_dict.pc_left_flag}}">\n        <span class="hide">0</span>\n        <span class="pc_qs db pct50 l">{{$value.qscore_dict.qscore}}</span><span class="mobile_qs left_dotted db pct50 l">{{if $value.qscore_dict.wireless_qscore >-1 }}{{$value.qscore_dict.wireless_qscore}}{{else}}--{{/if}}\n            </span>\n\n    </td>\n    <td>{{$value.create_days}}</td>\n    <td class="striped">{{$value.impr}}</td>\n    <td class="striped">{{$value.click}}</td>\n    <td class="striped">{{$value.ctr}}%</td>\n    <td class="striped">{{$value.cost}}</td>\n    <td class="striped">{{$value.cpc}}</td>\n    <td class="striped">{{$value.cpm}}</td>\n    <td class="striped">{{$value.avgpos}}</td>\n    <td>{{$value.favcount}}</td>\n    <td>{{$value.favshopcount}}</td>\n    <td>{{$value.favitemcount}}</td>\n    <td>{{$value.favctr}}%</td>\n    <td>{{$value.favpay}}</td>\n    <td>{{$value.carttotal}}</td>\n    <td>{{$value.paycount}}</td>\n    <td>{{$value.directpaycount}}</td>\n    <td>{{$value.indirectpaycount}}</td>\n    <td>{{$value.pay}}</td>\n    <td>{{$value.directpay}}</td>\n    <td>{{$value.indirectpay}}</td>\n    <td>{{$value.conv}}%</td>\n    <td {{if $value.roi>1}}class="red"{{/if}}>{{$value.roi}}</td>\n    <td class="striped">{{$value.g_pv}}</td>\n    <td class="striped">{{$value.g_click}}</td>\n    <td class="striped">{{$value.g_ctr}}%</td>\n    <td class="striped">{{$value.g_coverage}}%</td>\n    <td class="striped">{{$value.g_roi}}</td>\n    <td class="striped">{{$value.g_cpc | format:\'1,100,2\'}}</td>\n    <td class="striped">{{$value.g_competition}}</td>\n    <td class="striped">{{$value.g_paycount}}</td>\n</tr>\n{{/each}} {{/if}}\n';a=s.compile(r)({keywordList:t.keyword_list}),o&&o.table.fnDestroy(),$("#keyword_table tbody").html(a);var n=t.custom_column,d=n.indexOf("rob");d>=0&&n.splice(d,d),n.push("g_pv"),n.push("g_click"),n.push("g_ctr"),n.push("g_coverage"),n.push("g_roi"),n.push("g_cpc"),n.push("g_competition"),n.push("g_paycount"),o=new c.Table({element:$("#keyword_table"),hideColumn:n,warnPrice:Number($("#warn_price input").val()),headerMarginTop:40,layoutCallback:function(){var t=[];for(var a in this.rowCache)t.push(this.rowCache[a].keywordId);$("#keyword_table tbody").find(".img_box").popoverList({trigger:"hover",placement:"right",html:!0,viewport:"#keyword_table",content:function(){var t=$(this).find("img").data();return s.compile('<div class="p10">\n    <img src="{{picUrl}}_260x260.jpg" width="260" height="260">\n    <div class="text-muted">{{campaignTitle}}</div>\n    <div class="w260">{{itemTitle}}&emsp;{{price}}</div>\n</div>\n')({itemTitle:t.title,campaignTitle:t.campTitle,picUrl:t.picUrl,price:t.price})}}),$('[data-toggle="tooltip"]').tooltip({html:!0})},aoColumns:[{bSortable:!1},{bSortable:!0,sSortDataType:"custom-weird",sType:"custom"},{bSortable:!1},{bSortable:!0,sType:"custom",sSortDataType:"custom-weird",asSorting:["desc","asc"]},{bSortable:!0,sType:"custom",sSortDataType:"custom-weird",asSorting:["desc","asc"]},{bSortable:!1,sType:"custom",sSortDataType:"custom-weird"},{bSortable:!1},{bSortable:!1,sType:"custom",sSortDataType:"custom-weird"},{bSortable:!0,sType:"custom",sSortDataType:"custom-weird",asSorting:["desc","asc"]},{bSortable:!0,sType:"custom",sSortDataType:"custom-weird",asSorting:["desc","asc"]},{bSortable:!0,sType:"custom",sSortDataType:"custom-weird",asSorting:["desc","asc"]},{bSortable:!0,sType:"custom",sSortDataType:"custom-weird",asSorting:["desc","asc"]},{bSortable:!0,sType:"custom",sSortDataType:"custom-weird",asSorting:["desc","asc"]},{bSortable:!0,sType:"custom",sSortDataType:"custom-weird",asSorting:["desc","asc"]},{bSortable:!0,sType:"custom",sSortDataType:"custom-weird",asSorting:["desc","asc"]},{bSortable:!0,sType:"custom",sSortDataType:"custom-weird"},{bSortable:!0,sType:"custom",sSortDataType:"custom-weird",asSorting:["desc","asc"]},{bSortable:!0,sType:"custom",sSortDataType:"custom-weird",asSorting:["desc","asc"]},{bSortable:!0,sType:"custom",sSortDataType:"custom-weird",asSorting:["desc","asc"]},{bSortable:!0,sType:"custom",sSortDataType:"custom-weird",asSorting:["desc","asc"]},{bSortable:!0,sType:"custom",sSortDataType:"custom-weird",asSorting:["desc","asc"]},{bSortable:!0,sType:"custom",sSortDataType:"custom-weird",asSorting:["desc","asc"]},{bSortable:!0,sType:"custom",sSortDataType:"custom-weird",asSorting:["desc","asc"]},{bSortable:!0,sType:"custom",sSortDataType:"custom-weird",asSorting:["desc","asc"]},{bSortable:!0,sType:"custom",sSortDataType:"custom-weird",asSorting:["desc","asc"]},{bSortable:!0,sType:"custom",sSortDataType:"custom-weird",asSorting:["desc","asc"]},{bSortable:!0,sType:"custom",sSortDataType:"custom-weird",asSorting:["desc","asc"]},{bSortable:!0,sType:"custom",sSortDataType:"custom-weird",asSorting:["desc","asc"]},{bSortable:!0,sType:"custom",sSortDataType:"custom-weird",asSorting:["desc","asc"]},{bSortable:!0,sType:"custom",sSortDataType:"custom-weird",asSorting:["desc","asc"]},{bSortable:!0,sType:"custom",sSortDataType:"custom-weird",asSorting:["desc","asc"]},{bSortable:!0,sType:"custom",sSortDataType:"custom-weird",asSorting:["desc","asc"]},{bSortable:!0,sType:"custom",sSortDataType:"custom-weird",asSorting:["desc","asc"]},{bSortable:!0,sType:"custom",sSortDataType:"custom-weird",asSorting:["desc","asc"]},{bSortable:!0,sType:"custom",sSortDataType:"custom-weird",asSorting:["desc","asc"]},{bSortable:!0,sType:"custom",sSortDataType:"custom-weird",asSorting:["desc","asc"]},{bSortable:!0,sType:"custom",sSortDataType:"custom-weird",asSorting:["desc","asc"]},{bSortable:!0,sType:"custom",sSortDataType:"custom-weird",asSorting:["desc","asc"]}]}),o.generateCsvData(t.keyword_list),i=t,$("#operation_bar .line_box").pin({containerSelector:".box"})};return{init:function(){$("#version_limit").length||(l(15),p())}}});