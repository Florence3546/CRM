define('jl6/site_media/plugins/data-tables/dataTableExt', ['require', 'exports', 'module', 'jl6/site_media/plugins/jquery/jquery.min', 'jl6/site_media/plugins/data-tables/dataTables.min', 'jl6/site_media/plugins/data-tables/FixedHeader.min', 'jl6/site_media/plugins/data-tables/TableTools'], function(require, exports, module) {

  require('jl6/site_media/plugins/jquery/jquery.min');
  require('jl6/site_media/plugins/data-tables/dataTables.min');
  require('jl6/site_media/plugins/data-tables/FixedHeader.min');
  require('jl6/site_media/plugins/data-tables/TableTools');
  // 自定义扩展
  $.fn.dataTableExt.afnSortData["custom-text"]=function(b,a){return $.map(b.oApi._fnGetTrNodes(b),function(d,c){var e=b.oApi._fnGetTdNodes(b,c)[a];if(d.className.indexOf("unsort")!=-1){return"unsort"}else{return $(e).find("span:first").hasClass("custom")?Number($(e).find("span:first").text()):$(e).text()}})};$.fn.dataTableExt.afnSortData["dom-input"]=function(b,a){return $.map(b.oApi._fnGetTrNodes(b),function(d,c){return $("td:eq("+a+") input",d).val()})};$.fn.dataTableExt.oSort["custom-asc"]=function(a,b){if(a=="unsort"){return -1}if(b=="unsort"){return 1}a=parseFloat(a);b=parseFloat(b);return((a<b)?-1:((a>b)?1:0))};$.fn.dataTableExt.oSort["custom-desc"]=function(a,b){if(a=="unsort"){return -1}if(b=="unsort"){return 1}a=parseFloat(a);b=parseFloat(b);return((a<b)?1:((a>b)?-1:0))};$.fn.dataTableExt.afnSortData["dom-text"]=function(b,a){return $.map(b.oApi._fnGetTrNodes(b),function(d,c){return $("td:eq("+a+") span:eq(0)",d).text()})};$.fn.dataTableExt.afnSortData["td-text"]=function(b,a){return $.map(b.oApi._fnGetTrNodes(b),function(d,c){return $("td:eq("+a+")",d).text()})};$.fn.dataTableExt.afnSortData["dom-checkbox"]=function(b,a){return $.map(b.oApi._fnGetTrNodes(b),function(d,c){return $("td:eq("+a+") input",d).prop("checked")?"1":"0"})};$.fn.dataTableExt.afnSortData["custom-span"]=function(b,a){return $.map(b.oApi._fnGetTrNodes(b),function(d,c){return $("td:eq("+a+")>span:first",d).text()})};$.fn.dataTableExt.oSort['custom-percent-asc']=function(x,y){x=Number(x.replace('%',''));y=Number(y.replace('%',''));return((x<y)?-1:((x>y)?1:0))};$.fn.dataTableExt.oSort['custom-percent-desc']=function(x,y){x=Number(x.replace('%',''));y=Number(y.replace('%',''));return((x<y)?1:((x>y)?-1:0))};

});