define("jl6/site_media/service/edit_mobdiscount/edit_mobdiscount",["jl6/site_media/plugins/artTemplate/template","jl6/site_media/widget/ajax/ajax","jl6/site_media/widget/lightMsg/lightMsg"],function(i,t,n){"use strict";var o;o='<div class="modal fade">\n    <div class="modal-dialog" style="width:600px;">\n        <div class="modal-content">\n            <div class="modal-header">\n                <button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span></button>\n                <h4 class="modal-title">设置广告组的移动折扣</h4>\n            </div>\n            <div class="modal-body">\n                <div class="form-inline">\n                  <div class="form-group">\n                    <div class="input-group">\n                      <input type="text" class="form-control" style="width: 80px;" value="{{ value }}">\n                      <div class="input-group-addon"><strong>%</strong></div>\n                    </div>\n                    <div class="input-group">\n                        <span class="gray ml20">移动折扣介于1%~400%之间</span>\n                        <a href="javascript:void(0);" class="f12 ml5" id="use_camp_mobdiscount">使用计划折扣</a>\n                    </div>\n                  </div>\n                </div>\n            </div>\n            <div class="modal-footer">\n                <button type="button" class="btn btn-primary">确定</button>\n                <button type="button" class="btn btn-default" data-dismiss="modal">取消</button>\n            </div>\n        </div>\n    </div>\n</div>\n';var a=function(a){var d,s;d=i.compile(o)({value:a.value}),s=$(d),$("body").append(s),s.modal(),s.find(".btn-primary").on("click",function(){var i=s.find("input").val();return i==a.value?(s.modal("hide"),!1):Number(i)?(i=parseInt(i),i>400||1>i?(s.find(".form-control").tooltip({title:"移动折扣介于1%~400%之间！",placement:"top",trigger:"manual"}),s.find(".form-control").tooltip("show"),!1):(s.modal("hide"),void t.ajax("set_adg_mobdiscount",{campaign_id:a.campaign_id,adgroup_id:a.adgroup_id,discount:i},function(i){n.show({body:"修改移动折扣成功！"}),a.obj.text(i.discount)}))):(s.find(".form-control").tooltip({title:"移动折扣格式不正确，请输入正整数！",placement:"top",trigger:"manual"}),s.find(".form-control").tooltip("show"),!1)}),s.on("hidden.bs.modal",function(){s.remove()}),s.find("#use_camp_mobdiscount").on("click",function(){s.modal("hide"),t.ajax("delete_adg_mobdiscount",{campaign_id:a.campaign_id,adgroup_id:a.adgroup_id},function(i){n.show({body:"修改移动折扣成功！"}),a.obj.text(i.discount)})}),s.find("input").focus(function(){s.find(".form-control").tooltip("hide")})};return{show:a}});