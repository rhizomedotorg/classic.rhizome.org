jQuery.noConflict();
(function($) {
    var coverEmulator = {
        'aspectRatio': 1220 / 709,
        'resizeHeight': function(elem) {
            var newHeight = $(elem).parent().width() * (1 / elem.data('aspect-ratio'));
            $(elem).height(newHeight + elem.data('bottom-bleed'));
            $(elem).css({
                'width': '100%',
                'top': '50%', 
                'left': 'auto', 
                'margin-top': -0.5 * newHeight + 'px',
                'margin-left': '0'
            });
        },
        'resizeWidth': function(elem) {
            var newWidth = $(elem).parent().height() * elem.data('aspect-ratio');
            $(elem).width(newWidth);
            $(elem).css({
                'height': 'calc(100% + ' + elem.data('bottom-bleed') + 'px )',
                'top': 'auto', 
                'left': '50%', 
                'margin-top': '0',
                'margin-left': -0.5 * newWidth + 'px'
            });
        },
        'resize': function(elem) {
            if ($(elem).parent().width() / $(elem).parent().height() > elem.data('aspect-ratio')) {
                this.resizeHeight(elem);
            } else {
                this.resizeWidth(elem);
            }
        },
    };

    $(function() {
        var elem = $('.make-cover')
        elem.css({'position': 'absolute'});
        coverEmulator.resize(elem); 
        $(window).resize(function() { coverEmulator.resize(elem); });
});
})(jQuery);