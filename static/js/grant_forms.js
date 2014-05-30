jQuery.noConflict();
(function($) {
    var GrantForm = {
        errFieldHTML: '<ul class="errorlist"></ul>',
        errListSelector: 'ul.errorlist',
    }

    GrantForm.submitHandler = function(event) {
        form = event.target;
        var errFields = GrantForm.validate(form);

        if (errFields.length !== 0) {
	    event.preventDefault();
            GrantForm.displayErrors(form, errFields, null);
        }
    };

    GrantForm.validate = function(form) {
        var fields = $(form).find('input:not(:hidden), textarea, select');
        var errFields = [];

        $(fields).each(function() {
            if ($(this).val() == '' && $(this).hasClass('optional') === false) {
                errFields.push([this, '<li>This field is required.</li>']);
            }

	    var wordLimit = $(this).data('word-limit');
	    
	    if (wordLimit) {
		if ($(this).val().split(' ').length > wordLimit) {
		    errFields.push([this, '<li>May not exceed ' + wordLimit  + ' words.</li>']);
		}
	    }
        });
        return errFields;
    };

    GrantForm.displayErrors = function(form, errFields, topMsg) {
        $(GrantForm.errListSelector).remove(); // clear first

        $(errFields).each(function() {
            $(GrantForm.errFieldHTML).html($(this)[1]).insertAfter($(this)[0]);
        });

        if (topMsg) {
            $(form).prepend('<ul class="errorlist"><li>' + topMsg + '</li></ul>');
        }
    }

    $(function() {
	$('.rz-form').submit(GrantForm.submitHandler);
    });
})(jQuery);
