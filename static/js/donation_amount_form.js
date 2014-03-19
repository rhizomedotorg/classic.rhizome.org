jQuery.noConflict();
(function($) {
	$(function() {
	    $('#id_select_amount').change(function() {
	        $('#id_custom_amount').val('');
	        $('#id_amount').val($(this).val());
	    });

	    $('#id_custom_amount').change(function() {
	        $('#id_select_amount').val('');
	        $('#id_amount').val($(this).val());
	    });
	});
})(jQuery);