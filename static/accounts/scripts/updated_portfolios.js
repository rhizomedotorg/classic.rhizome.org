function show_updated_portfolios_profiles() {
	var duration = 300;
    links = $$('span.carousel-scroll a');
		
	tab = new Carousel({
		container: 'portfolios',
		distance: 5,
		previous: links.shift(),
		next: links.pop(),
		mode: 'horizontal', 
		fx: {
            duration: 750,
            transition: Fx.Transitions.Quart.easeInOut
        }

    });
}

function show_updated_portfolios_community() {
	var duration = 300;
    links = $$('span.carousel-scroll a');
		
	tab = new Carousel({
		container: 'portfolios',
		distance: 3,
		previous: links.shift(),
		next: links.pop(),
		mode: 'horizontal',
		fx: {
            duration: 750,
            transition: Fx.Transitions.Quart.easeInOut
        }
 
    });
}