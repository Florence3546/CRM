define("jl6/site_media/widget/ajax/ajax",["jl6/site_media/widget/alert/alert","jl6/site_media/widget/loading/loading"],function(e,t){"use strict";var a=function(a,i){""!=a.errMsg?(t.hide(),e.show(a.errMsg)):i&&i(a)},i=function(i,n,d,r,o){var s={url:"/web/ajax/",type:"post",dataType:"jsonp",data:$.extend({},{"function":i||"undefined"},n),timeout:6e4,cache:!1,success:function(e){a(e,d)},error:r||function(){t.hide(),e.show("获取服务器数据失败，请刷新页面重试，或联系顾问")}};s=$.extend({},s,o),$.ajax(s)};return{ajax:i}});