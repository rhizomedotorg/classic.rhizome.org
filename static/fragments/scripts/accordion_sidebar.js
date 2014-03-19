window.addEvent('domready', function() {
	var myAccordion = new Fx.Accordion($('accordion-elements'), 'h3.accordion-toggler', 'div.accordion-element-body', {
		display: 0,
		alwaysHide: 1, 
		opacity: true,
		onActive: function(toggler, element){
			toggler.setStyle('color', 'black');
			toggler.addEvents({
					mouseenter: function(){
					this.getParent('.accordion-element').setStyle('color', 'black');
				},		
            })
		},
		onBackground: function(toggler, element){
			toggler.setStyle('color', '#6494B2');
			toggler.addEvents({
				mouseenter: function(){
				    toggler.setStyle('color', 'black');
				},
				mouseleave: function(){
				    toggler.setStyle('color', '#6494B2');
				}
	   		})
	   }
   });	
 });	