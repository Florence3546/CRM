define("jl6/site_media/service/point_detial/point_detial",["require","jl6/site_media/plugins/artTemplate/template","jl6/site_media/widget/alert/alert","jl6/site_media/widget/ajax/ajax","jl6/site_media/widget/templateExt/templateExt"],function(n,a,t,e){"use strict";var i,l,s;i='<div class="modal fade">\n    <div class="modal-dialog" style="width:800px;">\n        <div class="modal-content">\n            <div class="modal-header">\n                <button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span></button>\n                <h4 class="modal-title">积分明细</h4>\n            </div>\n            <div class="modal-body">\n                <div class="content">\n                  <div class="text-center">\n                    <img src="/site_media/jl6/static/images/ajax_loader.gif" alt=""><br>\n                    <span>请稍候...</span>\n                  </div>\n                </div>\n                <div class="page mt20 mb20">\n\n                </div>\n            </div>\n        </div>\n    </div>\n</div>\n',l='<table class="pct100 table-bordered m0">\n    <thead>\n        <tr class="h40">\n            <th class="pl20 vm w100">时间</th>\n            <th class="pl20 vm w100">积分变化</th>\n            <th class="pl20 vm w100">积分方式</th>\n            <th class="tl pl20 vm ">描述</th>\n        </tr>\n    </thead>\n    <tbody>\n        {{each list as value index }}\n        <tr class="h40">\n            <td class="pl20 h40 vm">{{value.create_time | dateFormat:\'yyyy-MM-dd\'}}</td>\n            <td class="pl20 h40 vm">\n                 <span class="{{if value.point > 0}}red{{else}}green{{/if}}">\n                    {{if value.point > 0 }}+{{/if}}{{value.point}}\n                </span>\n            </td>\n            <td class="pl20 h40 vm">\n                 <span >\n                    {{value.type_desc}}\n                </span>\n            </td>\n            <td class="pl20 vm ">\n                {{value.desc}}\n\n                {{if value.type == \'gift\' }}\n                    {{if value.logistics_name}}\n                        物流公司：{{value.logistics_name}}\n                    {{/if}}\n\n                    {{if value.logistics_id}}\n                        运单号：{{value.logistics_id}}\n                    {{/if}}\n\n                    {{if value.logistics_state}}\n                        【已发货】\n                    {{else}}\n                        【未发货】\n                    {{/if}}\n                {{/if}}\n\n                {{if value.type == \'virtual\' }}\n                    {{if value.exchange_status}}\n                        【已兑换】\n                    {{else}}\n                        【未兑换】\n                    {{/if}}\n                {{/if}}\n            </td>\n        </tr>\n        {{/each}}\n    </tbody>\n</table>\n';var d=function(){var n;n=a.compile(i)(),s=$(n),$("body").append(s),s.modal(),s.on("shown.bs.modal",function(){o(1)}),s.on("hidden.bs.modal",function(){s.remove()})},o=function(n){e.ajax("point_detial",{page:n},function(n){c(n.data.detial_list),v(n.data.page_info)})},c=function(n){var t;t=a.compile(l)({list:n}),s.find(".content").html(t)},v=function(a){n(["jl6/site_media/widget/pageBar/pageBar"],function(n){var t=n.show({data:a,onChange:function(n){o(n)}});s.find(".page").html(t)})};return{show:d}});