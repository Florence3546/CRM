modulex.add("scroll-view/plugin/scrollbar",["xtemplate/runtime","ua","util","component/control","event-dom/gesture/basic","event-dom/gesture/pan","feature","base"],function(e,t,r){var a,s,l,n,o=e("xtemplate/runtime"),i=e("ua"),c=e("util"),d=e("component/control"),u=e("event-dom/gesture/basic"),g=e("event-dom/gesture/pan"),p=e("feature"),h=e("base");a=function(e){var t=e=function a(e){{var t,a=this,r=a.root,s=a.buffer,l=a.scope,n=(a.runtime,a.name,a.pos),o=l.data,i=l.affix,c=r.nativeCommands,d=r.utils,u=d.callFn;d.callCommand,c.range,c.foreach,c.forin,c.each,c["with"],c["if"],c.set,c.include,c.parse,c.extend,c.block,c.macro,c["debugger"]}s.data+='<div class="';var g=(t=i.axis)!==e?t:(t=o.axis)!==e?t:l.resolveLooseUp(["axis"]),p=g;p=g+"-arrow-up arrow-up";var h;h=u(a,l,{escape:1,params:[p]},s,["getBaseCssClasses"]),s=s.writeEscaped(h),s.data+='">\r\n    <a href="javascript:void(\'up\')">up</a>\r\n</div>\r\n<div class="',n.line=4;var v=(t=i.axis)!==e?t:(t=o.axis)!==e?t:l.resolveLooseUp(["axis"]),f=v;f=v+"-arrow-down arrow-down";var w;w=u(a,l,{escape:1,params:[f]},s,["getBaseCssClasses"]),s=s.writeEscaped(w),s.data+='">\r\n    <a href="javascript:void(\'down\')">down</a>\r\n</div>\r\n<div class="',n.line=7;var m=(t=i.axis)!==e?t:(t=o.axis)!==e?t:l.resolveLooseUp(["axis"]),x=m;x=m+"-track track";var y;y=u(a,l,{escape:1,params:[x]},s,["getBaseCssClasses"]),s=s.writeEscaped(y),s.data+='">\r\n<div class="',n.line=8;var E=(t=i.axis)!==e?t:(t=o.axis)!==e?t:l.resolveLooseUp(["axis"]),B=E;B=E+"-drag drag";var T;T=u(a,l,{escape:1,params:[B]},s,["getBaseCssClasses"]),s=s.writeEscaped(T),s.data+='">\r\n<div class="',n.line=9;var S=(t=i.axis)!==e?t:(t=o.axis)!==e?t:l.resolveLooseUp(["axis"]),C=S;C=S+"-drag-top";var b;b=u(a,l,{escape:1,params:[C]},s,["getBaseCssClasses"]),s=s.writeEscaped(b),s.data+='">\r\n</div>\r\n<div class="',n.line=11;var L=(t=i.axis)!==e?t:(t=o.axis)!==e?t:l.resolveLooseUp(["axis"]),P=L;P=L+"-drag-center";var H;H=u(a,l,{escape:1,params:[P]},s,["getBaseCssClasses"]),s=s.writeEscaped(H),s.data+='">\r\n</div>\r\n<div class="',n.line=13;var V=(t=i.axis)!==e?t:(t=o.axis)!==e?t:l.resolveLooseUp(["axis"]),k=V;k=V+"-drag-bottom";var $;return $=u(a,l,{escape:1,params:[k]},s,["getBaseCssClasses"]),s=s.writeEscaped($),s.data+='">\r\n</div>\r\n</div>\r\n</div>',s};return t.TPL_NAME=r.id||r.name,e}(),s=function(e){var t=a,r=o,s=new r(t);return e=function(){return s.render.apply(s,arguments)}}(),l=function(e){function t(e){e.preventDefault()}function r(e){e.halt();var t=this;t.startScroll=t.scrollView.get(t.scrollProperty)}function a(e){var t=this,r="pageX"===t.pageXyProperty?e.deltaX:e.deltaY,a=t.scrollView,s=t.scrollType,l={};l[s]=t.startScroll+r/t.trackElSize*t.scrollLength,a.scrollToWithBounds(l),e.halt()}function l(){var e,t,r,a=this,s=a.scrollView,l=a.trackEl,n=a.scrollWHProperty,o=a.whProperty,i=a.clientWHProperty,c=a.dragWHProperty;s.allowScroll[a.scrollType]?(a.scrollLength=s[n],t=a.trackElSize="width"===o?l.offsetWidth:l.offsetHeight,e=s[i]/a.scrollLength,r=e*t,a.set(c,r),a.barSize=r,m(a),a.set("visible",!0)):a.set("visible",!1)}function n(e){this.set("disabled",e.newVal)}function o(){var e=this;e.hideFn&&x(e)}function h(){var e=this,t=e.scrollView;t.allowScroll[e.scrollType]&&(y(e),e.set("visible",!0),e.hideFn&&!t.isScrolling&&x(e),m(e))}function v(e){function t(){var e={};e[l]=a.get(s)+i*n,a.scrollToWithBounds(e)}e.halt();var r=this,a=r.scrollView,s=r.scrollProperty,l=r.scrollType,n=a.getScrollStep()[r.scrollType],o=e.target,i=o===r.downBtn||r.$downBtn.contains(o)?1:-1;clearInterval(r.mouseInterval),r.mouseInterval=setInterval(t,100),t()}function f(e){var t=this,r=e.target,a=t.dragEl,s=t.$dragEl;if(a!==r&&!s.contains(r)){var l=t.scrollType,n=t.pageXyProperty,o=t.$trackEl,i=t.scrollView,c=Math.max(0,(e[n]-o.offset()[l]-t.barSize/2)/t.trackElSize),d={};d[l]=c*t.scrollLength,i.scrollToWithBounds(d),e.halt()}}function w(){clearInterval(this.mouseInterval)}function m(e){var t,r=e.scrollType,a=e.scrollView,s=e.dragLTProperty,l=e.dragWHProperty,n=e.trackElSize,o=e.barSize,i=e.scrollLength,c=a.get(e.scrollProperty),d=a.maxScroll,u=a.minScroll,g=u[r],p=d[r];c>p?(t=p/i*n,e.set(l,o-(c-p)),e.set(s,t+o-e.get(l))):g>c?(t=g/i*n,e.set(l,o-(g-c)),e.set(s,t)):(t=c/i*n,e.set(s,t),e.set(l,o))}function x(e){y(e),e.hideTimer=setTimeout(e.hideFn,1e3*e.get("hideDelay"))}function y(e){e.hideTimer&&(clearTimeout(e.hideTimer),e.hideTimer=null)}function E(e){e.halt()}function B(e,s){var l=s?"detach":"on";e.get("autoHide")||(e.$dragEl[l](["dragstart","mousedown"],t)[l](L.PAN_END,E,e)[l](L.PAN_START,r,e)[l](L.PAN,a,e),S.each([e.$downBtn,e.$upBtn],function(t){t[l](b.START,v,e)[l](b.END,w,e)}),e.$trackEl[l](b.START,f,e))}var T=i,S=c,C=d,b=u,L=g,P=s,H=20,V=".ks-scrollbar",k=p,$=k.isTransform3dSupported(),D=k.getCssVendorInfo("transform"),X=!!D,W={initializer:function(){var e=this,t=e.scrollType="x"===e.get("axis")?"left":"top",r=S.ucfirst(t);e.pageXyProperty="left"===t?"pageX":"pageY";var a=e.whProperty="left"===t?"width":"height",s=S.ucfirst(a);e.afterScrollChangeEvent="afterScroll"+r+"Change",e.scrollProperty="scroll"+r,e.dragWHProperty="drag"+s,e.dragLTProperty="drag"+r,e.clientWHProperty="client"+s,e.scrollWHProperty="scroll"+s,e.scrollView=e.get("scrollView")},beforeCreateDom:function(e){e.elCls.push(e.prefixCls+"scrollbar-"+e.axis)},createDom:function(){var e=this;e.$dragEl=e.get("dragEl"),e.$trackEl=e.get("trackEl"),e.$downBtn=e.get("downBtn"),e.$upBtn=e.get("upBtn"),e.dragEl=e.$dragEl[0],e.trackEl=e.$trackEl[0],e.downBtn=e.$downBtn[0],e.upBtn=e.$upBtn[0]},bindUI:function(){var e=this,t=e.get("autoHide"),r=e.scrollView;t&&(e.hideFn=S.bind(e.hide,e)),r.on(e.afterScrollChangeEvent+V,h,e).on("scrollTouchEnd"+V,o,e).on("afterDisabledChange"+V,n,e).on("reflow"+V,l,e),B(e,e.get("disabled"))},syncUI:function(){l.call(this)},_onSetDragHeight:function(e){this.dragEl.style.height=e+"px"},_onSetDragWidth:function(e){this.dragEl.style.width=e+"px"},_onSetDragLeft:function(e){this.dragEl.style.left=e+"px"},_onSetDragTop:function(e){this.dragEl.style.top=e+"px"},_onSetDisabled:function(e){this.callSuper(e),B(this,e)},destructor:function(){this.scrollView.detach(V),y(this)}};if(X){var I=D.propertyName;W._onSetDragLeft=function(e){this.dragEl.style[I]="translateX("+e+"px) translateY("+this.get("dragTop")+"px)"+($?" translateZ(0)":"")},W._onSetDragTop=function(e){this.dragEl.style[I]="translateX("+this.get("dragLeft")+"px) translateY("+e+"px)"+($?" translateZ(0)":"")}}return e=C.extend(W,{ATTRS:{handleGestureEvents:{value:!1},focusable:{value:!1},allowTextSelection:{value:!1},minLength:{value:H},scrollView:{},axis:{render:1},autoHide:{value:T.ios},visible:{valueFn:function(){return!this.get("autoHide")}},hideDelay:{value:.1},dragWidth:{setter:function(e){var t=this.get("minLength");return t>e?t:e},render:1},dragHeight:{setter:function(e){var t=this.get("minLength");return t>e?t:e},render:1},dragLeft:{render:1,value:0},dragTop:{render:1,value:0},dragEl:{selector:function(){return"."+this.getBaseCssClass("drag")}},downBtn:{selector:function(){return"."+this.getBaseCssClass("arrow-down")}},upBtn:{selector:function(){return"."+this.getBaseCssClass("arrow-up")}},trackEl:{selector:function(){return"."+this.getBaseCssClass("track")}},contentTpl:{value:P}},xclass:"scrollbar"})}(),n=function(e){function t(){var e,t=this,r=t.scrollView,s=t.get("minLength"),l=t.get("autoHideX"),n=t.get("autoHideY");!t.scrollBarX&&r.allowScroll.left&&(e={axis:"x",scrollView:r,elBefore:r.$contentEl},void 0!==s&&(e.minLength=s),void 0!==l&&(e.autoHide=l),t.scrollBarX=new a(e).render()),!t.scrollBarY&&r.allowScroll.top&&(e={axis:"y",scrollView:r,elBefore:r.$contentEl},void 0!==s&&(e.minLength=s),void 0!==n&&(e.autoHide=n),t.scrollBarY=new a(e).render())}var r=h,a=l;return e=r.extend({pluginId:this.name,pluginBindUI:function(e){var r=this;r.scrollView=e,e.on("reflow",t,r)},pluginDestructor:function(e){var r=this;r.scrollBarX&&(r.scrollBarX.destroy(),r.scrollBarX=null),r.scrollBarY&&(r.scrollBarY.destroy(),r.scrollBarY=null),e.detach("reflow",t,r)}},{ATTRS:{minLength:{},autoHideX:{},autoHideY:{}}})}(),r.exports=n});