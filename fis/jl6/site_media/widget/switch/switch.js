define(['jquery'],function($) {
    "use strict";

    var Switch = function(element, options) {
        this.$element = $(element);
        this.options = $.extend({}, this.$element.data());
    }

    Switch.prototype = {
        constructor: Switch,
        toggle: function() {
            this[!this.$element.hasClass('on') ? 'show' : 'hide']();
        },
        show: function() {
            if (!this.$element.hasClass('on')) {
                this.$element.addClass('on');
                this.$element.trigger('change', [true]);
            }

        },
        hide: function() {
            if (this.$element.hasClass('on')) {
                this.$element.removeClass('on');
                this.$element.trigger('change', [false]);
            }
        }
    }

    $(document).on('click.switch.data-api', '[data-toggle="switch"]', function(e) {
        var $this = $(this),
            data = $this.data('Switch')
        if (!data) $this.data('Switch', (data = new Switch(this)))
        data.toggle();
    })

});
