define("jl6/site_media/widget/select/select",["jl6/site_media/plugins/jquery/jquery.min"],function(t){"use strict";t(document).on("click.data-select.api",".select_warp>ul>li",function(){var e,i,a=t(this).parent().parent();e=t(this).data("value"),i=t(this).text(),a.find(".tip").text(i),a.trigger("change",[e]),t(this).parent().find("li>span").removeClass("active"),t(this).find("span").addClass("active")}),t(document).on("choose.data-select",".select_warp",function(e,i){var a;t(this).find("ul>li>span").removeClass("active"),t(this).find("ul>li").each(function(){return t(this).data("value")==i?(t(this).find("span").addClass("active"),a=t(this).find("span").text(),!1):void 0}),t(this).find(".tip").text(a)})});