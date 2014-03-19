jQuery.noConflict();
(function($) {
    $(function() {
        var flashCount = 0;

        function doFlash() {
            $('#new_footer').toggleClass('flash');
            flashCount++;

            if (flashCount < 10) {
                setTimeout(doFlash, 140);
            }
        }

        $(window).load(function() {
            doFlash();
        });
    });
})(jQuery);