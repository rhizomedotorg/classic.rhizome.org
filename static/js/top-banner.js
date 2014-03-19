jQuery.noConflict();
(function($) {
   $(function() {
        $('.top-banner .close').click(function(e) {
            $('body').removeClass('with-top-banner');
            $('.top-banner').remove();
        })
    });
})(jQuery);