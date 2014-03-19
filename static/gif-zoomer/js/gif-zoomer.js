jQuery.noConflict();
(function($) {
    function preloadImage(src, callback) {
        $('<img />').attr('src', src)
        .load(function(){
            callback(this);
        });
    }

    var frames = ['|', '/', '-', '\\'];
    var frameIndex = 0;

    function nextFrame() {
        frameIndex = frameIndex == frames.length - 1 ? 0 : frameIndex + 1;
        return frames[frameIndex];
    }

    $(document).ready(function() {
        var myTimer = setInterval(function() {
            $('.spinner').html(nextFrame());
        }, 100);

        var src = $('.zoomer-img').data('src');

        preloadImage(src, function(img) {
            clearInterval(myTimer);
            $('.zoomer-loading').hide();
            $('.zoomer-img').css('background-image', 'url(' + src + ')');
        });
    });
})(jQuery);