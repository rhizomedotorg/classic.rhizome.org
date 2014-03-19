(function($) {
    $(document).ready(function($) {
        $('#deploy_button').click(function() {
            var $button = $(this);
            if (!$button.hasClass('disabled')) {
                $('#deploy_loading').show();
                $button.addClass('disabled');

                $.ajax({
                    url: '/deploy/',
                    success: function(data) {
                        console.log(data);
                        doPoll($, data, function() {
                            $('#deploy_loading').hide();
                            $button.removeClass('disabled'); 
                        });
                    },
                });
            };
            return false;
        });
    });
})(django.jQuery);

function doPoll($, taskId, callback) {
    setTimeout(function() {
        $.ajax({
            url: '/tasks/' + taskId + '/status/',
            success: function(data) {
                var status = data['task']['status'];

                if (status === 'SUCCESS') {
                    console.log(data['task']);
                    callback();
                } else {
                    console.log(status);
                    doPoll($, taskId, callback);
                }
            },
            error: function(jqXHR, textStatus) {
                console.log(textStatus);
                doPoll($, taskId, callback);
            }
        });
    }, 1000);
}