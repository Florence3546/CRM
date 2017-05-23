/* ===========================================================
 * @version         0.0.1
 * @since           2014.10.30
 * @author          钟进峰
 * @function        右下角弹出广告
 * @package         jQuery.js,common.js
 */

! function($) {

    "use strict";

    var template=function(options){
      var TPL='<div class="rightDownAd <%size%>">'
            +'<button type="button" data-dismiss="RightDownAd" aria-hidden="true" class="close <%autoclose%> abs t0 r0 mr3">×</button>'
              +'<div class="rightDownAd-body">'
              +'</div>'
            +'</div>';

      var element=$(TPL.replace('<%size%>',options.size)
                       .replace('<%autoclose%>',options.autoclose?'':'hide'));

    $('body').append(element);
    return element;
    }

    var defaults = {
        dealy: 3000,
        during: 12000,
        body: null,
        size: 'large',  //nomal: 250*300 large: 300*420
        autoclose:true    //是否允许用户关闭
    }

    var RightDownAd=window.RightDownAd = function(options) {
        var that = this;

        this.options = $.extend({}, defaults, options);
        this.element = template(this.options)
        this.$element = $(this.element);

        this.$element.delegate('[data-dismiss="RightDownAd"]', 'click.dismiss.RightDownAd', $.proxy(this.hide, this));

        if (this.options.body) {
            this.$element.find('.rightDownAd-body').html(this.options.body);
        }

        setTimeout(function() {
            that.show();
        }, that.options.dealy);
    }

    RightDownAd.prototype = {
        constructor: RightDownAd,
        show: function() {
            var that = this;

            if ($.support.transition) {
                this.$element.addClass('show');
            } else {
                this.$element.animate({
                    'marginBottom': 0
                }, 600);
            }

            // PT.set_habit({'RightDownAd',[this.cycle,'']);

            setTimeout(function() {
                that.hide();
            }, that.options.during);
        },
        hide: function() {
            var that=this;
            if ($.support.transition) {
                this.$element.removeClass('show');
            } else {
                this.$element.animate({
                    'marginBottom': -this.$element.height()
                }, 600);
            }
        }
    }
}(window.jQuery)
