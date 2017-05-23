define("jl6/site_media/service/mnt/mnt_camp_rpt",["require","jl6/site_media/plugins/artTemplate/template","jl6/site_media/service/common/common"],function(t,a,n){"use strict";var e;e='<div class="modal fade">\r\n    <div class="modal-dialog modal-lg">\r\n        <div class="modal-content">\r\n            <div class="modal-header">\r\n                <button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span></button>\r\n                <h4 class="modal-title">{{title}}&emsp;趋势图</h4>\r\n            </div>\r\n            <div class="modal-body">\r\n                 <div id="mnt_camp_chart">\r\n                      <div class="tc">\r\n                        <img src="/site_media/jl6/static/images/ajax_loader.gif" alt=""><br>\r\n                        <span>请稍候...</span>\r\n                      </div>\r\n                 </div>\r\n                <table class="table table-bordered" class="detailed_table">\r\n                    <thead>\r\n                        <tr>\r\n                          <th><div>日期</div></th>\r\n                          <th><div>展现量</div></th>\r\n                          <th><div>点击量</div></th>\r\n                          <th><div>点击率</div></th>\r\n                          <th><div>PPC<i class="iconfont" data-toggle="tooltip" data-placement="top" data-trigger="hover" title="平均点击花费">&#xe61a;</i>\r\n                          </div></th>\r\n                          <th><div>总花费</div></th>\r\n                          <th><div>成交额</div></th>\r\n                          <th><div>成交笔数</div></th>\r\n                          <th><div>收藏次数</div></th>\r\n                          <th><div>ROI<i class="iconfont" data-toggle="tooltip" data-placement="top" data-trigger="hover" title="投资回报率">&#xe61a;</i>\r\n                          </div></th>\r\n                          <th>转化率</th>\r\n                        </tr>\r\n                    </thead>\r\n                    <tbody>\r\n                    </tbody>\r\n                </table>\r\n            </div>\r\n        </div>\r\n    </div>\r\n</div>';var i=function(t){var i,d;i=a.compile(e)(t),d=$(i),$("body").append(d),d.modal(),d.on("shown.bs.modal",function(){n.chart.draw("mnt_camp_chart",t.category_list,t.series_cfg_list),d.find(".detailed_table").dataTable({bPaginate:!1,bFilter:!1,bInfo:!1,aaSorting:[[0,"desc"]],sDom:"",oLanguage:{sZeroRecords:"暂无数据！",sInfoEmpty:"暂无数据！"},aoColumns:[null,null,null,null,null,null,{sSortDataType:"td-text",sType:"numeric"},{sSortDataType:"td-text",sType:"numeric"},{sSortDataType:"td-text",sType:"numeric"},null,null]})}),d.on("hidden.bs.modal",function(){d.remove()})};return{show:i}});