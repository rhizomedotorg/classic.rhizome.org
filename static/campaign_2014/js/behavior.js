$(function() {
    $('#amount-form').submit(function(event) {
        event.preventDefault();
        var amount = $('#amount-field').val();
        var qstring = '?amount=' + amount;

        if (amount >= 1000) {
            qstring += '&gift=Sara Ludy print';
        } else if (amount >= 500) {
            qstring += '&gift=Custom Embroidered Rhizome Hat, Bunny Rogers %26 Filip Olszewski sculpture';
        } else if (amount >= 150) {
            qstring += '&gift=Sara Ludy print';
        } else if (amount >= 50) {
            qstring += '&gift=Custom Embroidered Rhizome Hat';
        }

        window.location = '/support/donate/confirm_donation/' + qstring;
    });

    var campaignEndpoint = window.location.protocol + '//' + window.location.host + '/api/v1/campaign/?format=json&year=2014';
    $.ajax({
        url: campaignEndpoint,
        type: 'GET',
    }).done(function(data) {
        var campaign = data.objects[0];
        // update readout
        $('span#goal').html(campaign.formatted_amount_goal);
        $('span#deadline').html(campaign.days_left);
        $('span#amount-raised').html(campaign.formatted_amount_raised);

        // update progress bar
        $('.progress-bar').attr('aria-valuenow', campaign.percent_raised);
        $('.progress-bar').css('width', campaign.percent_raised + '%');
        $('.progress-bar .sr-only').html(campaign.percent_raised + '% Complete')
    }).fail(function(data) {
        console.log(data);
    });

    var appealEndpoint = window.location.protocol + '//' + window.location.host + '/api/v1/block/?format=json&ident=2014%20appeal';
    $.ajax({
        url: appealEndpoint,
        type: 'GET',
    }).done(function(data) {
        var block = data.objects[0];
        $('#appeal').html(block.text);
    }).fail(function(data) {
        console.log(data);
    });
});