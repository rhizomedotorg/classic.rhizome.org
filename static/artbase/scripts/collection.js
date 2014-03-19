window.addEvent('domready', function(){

    $$('.work-cover').addEvents({
        mouseenter: function() {
            this.set('tween', {duration: 160}).fade(.8);
        },
        mouseleave: function() {
            this.set('tween', {duration: 160}).fade(.001);
        },
        click: function(){
            var current_focused = $$(".current"),
            new_focused = $('focus-' + this.getParent().id);
            current_focused.removeClass('current');
            console.log(current_focused);
            console.log(new_focused);
            new_focused.addClass('current');
        }
    });         
        
    var statement_content = new Carousel({
		container: 'focus-statement-wrap',
		distance: 1,
	    previous: $('statement-back'),
	    next: $('statement-forward'),
		mode: 'horizontal', 
        scroll: 1, 
		fx: {
            duration: 300,
            transition: Fx.Transitions.Quart.easeInOut
        }
    });
        
    function hide_back_nav() {
        statement_content.addEvent('complete', function(){
            if (statement_content.current == 0) {
                $("statement-back").setStyle('visibility', 'hidden');
            } else {
                $("statement-back").setStyle('visibility', 'visible');
            }
        });
    }

    function hide_forward_nav() {
        statement_content.addEvent('complete', function(){
            if (statement_content.current == (statement_content.elements.length - 1)) {
                $("statement-forward").setStyle('visibility', 'hidden');
            } else {
                $("statement-forward").setStyle('visibility', 'visible');
            }
        });
    }
            
    $$('.statement-scroll').addEvents({click: hide_back_nav, change: hide_back_nav});
    $$('.statement-scroll').addEvents({click: hide_forward_nav, change: hide_forward_nav});
    
    var collections_preview = new Carousel({
		container: 'collection-carousel',
		distance: 2,
        scroll: 5, 
	    previous: $('preview-previous'),
	    next: $('preview-next'),
		mode: 'horizontal', 
		fx: {
            duration: 300,
            transition: Fx.Transitions.Quad.easeInOut
        }
    });
   
});
    
