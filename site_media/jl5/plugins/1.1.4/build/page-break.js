define("kg/editor-plugins/1.1.4/page-break",["editor","./fake-objects","./button","node"],function(e,t,a){function n(){}var o=e("editor"),r=e("./fake-objects");e("./button");var s=e("node"),i="ke_pagebreak",d="div",l='<div style="page-break-after: always; "><span style="DISPLAY:none">&nbsp;</span></div>';n.prototype={pluginRenderUI:function(e){r.init(e);var t=e.htmlDataProcessor,a=t&&t.dataFilter;a.addRules({tags:{div:function(e){var a,n=e.getAttribute("style");if(n)for(var o=e.childNodes,r=0;r<o.length;r++)1===o[r].nodeType&&(a=o[r]);var s=a&&"span"===a.nodeName&&a.getAttribute("style");return s&&/page-break-after\s*:\s*always/i.test(n)&&/display\s*:\s*none/i.test(s)?t.createFakeParserElement(e,i,d):void 0}}}),e.addButton("pageBreak",{tooltip:"分页",listeners:{click:function(){var t=s(l,e.get("document")[0]),a=e.createFakeElement(t,i,d,!1,l);e.focus();var n=e.getSelection(),o=n&&n.getRanges()[0];if(o){e.execCommand("save");for(var r=o.startContainer,p=r;"body"!==r.nodeName();)p=r,r=r.parent();o.collapse(!0),o.splitElement(p),a.insertAfter(p),e.execCommand("save")}}},mode:o.Mode.WYSIWYG_MODE})}},a.exports=n});