define("jl6/site_media/service/add_item_box/select_item_img",["jl6/site_media/plugins/artTemplate/template","jl6/site_media/widget/alert/alert"],function(i,e){"use strict";var t=function(t){var a,l,n='\n<div class="modal fade" tabindex="-1" role="dialog" aria-hidden="true" id="modal_select_creative_img" item_id="{{ item_id }}" no="{{ no }}">\n    <div class="modal-dialog">\n      <div class="modal-content">\n         <div class="modal-header">\n            <button type="button" class="close"\n               data-dismiss="modal" aria-hidden="true">\n                  &times;\n            </button>\n            <h4 class="modal-title b">\n               点击选择创意图片<span id="creative_img_no">{{ img_no }}</span>\n            </h4>\n         </div>\n         <div class="modal-body pt20 pl30 pr30 pt10">\n               <div class="tc image_list pl10">\n                   <ul class="ul_line h160">\n                      {{ each item_imgs as img_url index}}\n                        <li class="bdd mr10 mt10 rel {{ if cur_img == img_url }}active{{ /if }}" fix-ie="hover">\n                          <img src="{{ img_url }}_160x160.jpg" width="160" height="160">\n                          <i class="iconfont select">&#xe656;</i>\n                        </li>\n                      {{ /each }}\n                    </ul>\n               </div>\n         </div>\n         <div class="modal-footer tc">\n             <button class="btn r" data-dismiss="modal" aria-hidden="true">取消</button>\n            <button class="btn btn-primary r mr10" id="update_creative">确定</button>\n         </div>\n      </div>\n    </div>\n</div>\n';a=i.compile(n)(t),l=$(a),$("body").append(l),l.modal(),$("#modal_select_creative_img").on("click","#update_creative",function(){{var i=$("#modal_select_creative_img li.active>img").attr("src");$("#modal_select_creative_img").attr("item_id"),$("#modal_select_creative_img").attr("no")}return i?(t.onChange(i),$("#modal_select_creative_img").modal("hide"),void l.modal("hide")):(e.show("还未选择创意图片!"),!1)}),$("#modal_select_creative_img .ul_line").on("click","li",function(){$("#modal_select_creative_img .ul_line").find("li").removeClass("active"),$(this).addClass("active")}),l.on("hidden.bs.modal",function(){l.remove()})};return{show:t}});