var KISSY=function(){function e(e){function t(){var t=o.call(arguments,0);return t.unshift(n),e.apply(this,t)}return t.toString=function(){return e.toString()},t}var n={version:"5.0.0"},o=[].slice;return n.require=modulex.require,n.Env=modulex.Env,n.Config=modulex.Config,n.config=modulex.config,n.log=function(e,n){void 0!==typeof console&&console.log&&console[n&&console[n]?n:"log"](e)},n.error=function(e){if(modulex.Config.debug)throw new Error(e)},n.nodeRequire=modulex.nodeRequire,n.add=function(){for(var n=o.call(arguments,0),t=0,i=n.length;i>t;t++)"function"==typeof n[t]&&(n[t]=e(n[t]));modulex.add.apply(this,n)},n.use=function(){var t=o.call(arguments,0),i=t[1];return"function"==typeof i?t[1]=e(t[1]):i&&i.success&&(i.success=e(i.success)),modulex.use.apply(this,t),n},"undefined"!=typeof module&&(module.exports=n),"undefined"!=typeof global&&(global.KISSY=n),n.modulex=modulex,n}();!function(e){e.use(["util","querystring"],function(e,n,o){n.mix(e,n),e.param=o.stringify,e.unparam=o.parse}),e.add("event",["util","event-dom","event-custom"],function(e,n){var o=e.Event={},t=n("util");return t.mix(o,n("event-dom")),e.EventTarget=o.Target=n("event-custom").Target,e.log("event module is deprecated! please use 'event-dom' and 'event-dom/gesture/*' or 'event-custom' module instead."),o});var n={ua:"UA",json:"JSON",cookie:"Cookie","dom/base":"DOM","anim/timer":"Anim","anim/transition":"Anim",base:"Base"},o={core:{alias:["dom","event","io","anim","base","node","json","ua","cookie"]},io:{afterInit:function(n){e.ajax=e.Ajax=e.io=e.IO=n}},node:{afterInit:function(n){e.Node=e.NodeList=n,e.one=n.one,e.all=n.all}}};for(var t in n)!function(n,t){o[n]={afterInit:function(n){e[t]=e[t]||n}}}(t,n[t]);e.config("modules",o),e.namespace=function(){var n,o,t,i=e.makeArray(arguments),u=i.length,r=null,a=i[u-1]===!0&&u--;for(n=0;u>n;n++)for(t=(""+i[n]).split("."),r=a?window:this,o=window[t[0]]===r?1:0;o<t.length;++o)r=r[t[o]]=r[t[o]]||{};return r},KISSY.use("ua",function(e,n){e.UA=n})}(KISSY);