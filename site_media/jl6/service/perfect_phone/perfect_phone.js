define("jl6/site_media/service/perfect_phone/perfect_phone",["require","jl6/site_media/plugins/artTemplate/template","jl6/site_media/widget/alert/alert","jl6/site_media/widget/lightMsg/lightMsg","jl6/site_media/widget/ajax/ajax","jl6/site_media/widget/vaildata/vaildata"],function(a,n,e,i,l){"use strict";var t,o;t='<div class="modal fade">\n  <div class="modal-dialog">\n    <div class="modal-content">\n      <div class="modal-header">\n        <button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span></button>\n        <h4 class="modal-title">激活会员中心</h4>\n      </div>\n      <div class="modal-body">\n        {{if type== \'init\'}}\n        <div class="red mb20">亲，您尚未激活会员特权！现在激活，立享多项会员特权，更有500积分相送！。</div>\n        {{/if}}\n        <form class="form-horizontal">\n          <div class="form-group">\n            <label for="receiver" class="col-sm-2 p0 control-label">手机号</label>\n            <div class="col-sm-6 pr5">\n              <input type="text" data-rule="phone require" class="form-control" name="phone">\n            </div>\n            <div class="col-sm-2 p0 red mt5">*</div>\n          </div>\n          <div class="form-group">\n            <label for="receiver_phone" class="col-sm-2 p0 control-label">QQ号</label>\n            <div class="col-sm-6 pr5">\n              <input type="text" data-rule="digital" class="form-control" name="qq">\n            </div>\n          </div>\n          <div class="form-group">\n            <div class="col-sm-offset-2 col-sm-10">\n              <button type="submit" class="btn btn-primary">提交</button>\n              <button type="button" class="btn btn-default" data-dismiss="modal">取消</button>\n            </div>\n          </div>\n        </form>\n      </div>\n    </div>\n  </div>\n</div>\n';var s=function(a){var e;e=n.compile(t)(a),o=$(e),$("body").append(o),o.find("form").vaildata({placement:"right",callBack:function(a){var n,e;n=$(a).find("[name=phone]").val(),e=$(a).find("[name=qq]").val(),l.ajax("submit_userinfo",{phone:n,qq:e},function(){i.show("激活成功")}),o.modal("hide")}}),o.on("show.bs.modal",function(){l.ajax("customer_info",{},function(a){o.find("[name=phone]").val(a.data[0].phone),o.find("[name=qq]").val(a.data[0].qq)})}),o.on("hidden.bs.modal",function(){o.remove()}),o.modal()};return{show:s}});