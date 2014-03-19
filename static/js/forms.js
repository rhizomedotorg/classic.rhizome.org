jQuery.noConflict();
(function($) {
    function getCookie(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie != '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = jQuery.trim(cookies[i]);
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) == (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    function csrfSafeMethod(method) {
        // these HTTP methods do not require CSRF protection
        return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
    }

    var RZForm = {
        errFieldHTML: '<ul class="errorlist"><li>This field is required.</li></ul>',
        errListSelector: 'ul.errorlist',
    }
    RZForm.submitHandler = function(event) {
        event.preventDefault();
        form = event.target;
        var endpoint = window.location.protocol + '//' + window.location.host + $(form).data('endpoint');
        var nextURL = $(form).data('next');
        var errFields = RZForm.validate(form);

        if (errFields.length == 0) {
            $.ajax({
                url: endpoint,
                type: 'POST',
                dataType: 'text',
                contentType: 'application/json', // send as JSON
                data: JSON.stringify(RZForm.serializeForm(form)),
            }).done(function(data) {
                window.location.replace(nextURL);
            }).fail(function(data) {
                var errMsg = JSON.parse(data.responseText).donation;
                RZForm.displayErrors(form, errFields, errMsg);
            });
        } else {
            RZForm.displayErrors(form, errFields, null);
        }
    };
    RZForm.serializeForm = function(form) {
        var myjson = {}; 
        var fields = $(form).find('input, textarea, select');
        $(fields).each(function() {
            myjson[this.name] = $(this).val();
        });
        return myjson;
    };
    RZForm.validate = function(form) {
        var fields = $(form).find('input, textarea, select');
        var errFields = [];

        $(fields).each(function() {
            if ($(this).val() == '') {
                errFields.push(this);
            }
        });
        return errFields;
    };
    RZForm.displayErrors = function(form, errFields, topMsg) {
        $(RZForm.errListSelector).remove(); // clear first

        $(errFields).each(function() {
            $(RZForm.errFieldHTML).insertAfter($(this));
        });

        if (topMsg) {
            $(form).prepend('<ul class="errorlist"><li>' + topMsg + '</li></ul>');
        }
    }

    $(function() {
        var csrftoken = getCookie('csrftoken');

        $.ajaxSetup({
            crossDomain: false, // obviates need for sameOrigin test
            beforeSend: function(xhr, settings) {
                if (!csrfSafeMethod(settings.type)) {
                    xhr.setRequestHeader('X-CSRFToken', csrftoken);
                }
            }
        });

        var $loading = $('#loading-indicator');
        $(document).ajaxStart(function() {
            $loading.show();
        })
        .ajaxStop(function() {
            $loading.hide();
        });

        $('.rz-form').submit(RZForm.submitHandler);
    });
})(jQuery);
