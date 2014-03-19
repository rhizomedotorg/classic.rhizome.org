jQuery.noConflict();
(function($) {
    $(function() {
        $('.share-btn-cover').click(function() {
            $(this).hide();
            $(this).find('.share-btn').css({'display': 'inline-block'});
            return false;
        });
    });
})(jQuery);