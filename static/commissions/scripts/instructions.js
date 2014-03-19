window.addEvent('domready', function() {

    var instructionsSlide = new Fx.Slide('proposal-instructions', {mode: 'vertical'}).hide();
    
    $('proposal-instructions-link').addEvent('click', function(e){
    	e = new Event(e);
    	instructionsSlide.toggle();
    	e.stop();
    });

    $('close').addEvent('click', function(e){
    	e = new Event(e);
    	instructionsSlide.toggle();
    	e.stop();
    });

});	