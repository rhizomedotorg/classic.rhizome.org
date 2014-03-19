window.addEvent('domready', function() {
    var limited_edition = $('id_limited_edition');
    var limited_editions = $$('.register-limited-edition');    
    var amount_input = $('amount')
    var select_amount = $('id_select_amount');    
    var custom_amount = $('id_custom_amount');
        
    //UPDATE THE ACTUAL AMOUNT IF USER CLICKS ON LIMITED EDITION WORK
    limited_editions.each(function(div){
        div.addEvent('click', function(e){
            e.stop()
            amount_input.value = this.get("name");
            select_amount.value = this.get("name");
            limited_edition.value = this.get("rel");

            selected = $$('.selected-edition');    
            if (!selected){
                this.getChildren()[0].addClass('selected-edition');
            } else {
                selected.removeClass('selected-edition');
                this.getChildren()[0].addClass('selected-edition');
            }
        });        
    });

});	