window.addEvent('domready', function() {
    var EditAccordion = new Fx.Accordion($('accordion'), '.section-object-header', '.edit-section', {
		display: -1,
		alwaysHide: 1, 
		onActive: function(toggler, element){
			toggler.setStyle('border-bottom-color', '#787c80');
			toggler.setStyle('border-bottom-style', 'solid');
			toggler.setStyle('color', 'black');
			toggler.getElement('.edit-section-header-h2').setStyle('color', 'black');
			toggler.getElement('.edit-section-header-arrow').setStyle('background-position', '0 -111px');
			toggler.addEvents({
				mouseenter: function(){
					this.setStyle('color', 'black');
					this.setStyle('border-bottom-color', '#787c80');
					this.setStyle('border-bottom-style', 'solid');
					this.getElement('.edit-section-header-h2').setStyle('color', 'black');		
                    this.getElement('.edit-section-header-arrow').setStyle('background-position', '0 -111px');
				},
				mouseleave: function(){
					this.setStyle('color', 'black');
					this.setStyle('border-bottom-color', '#787c80');
					this.setStyle('border-bottom-style', 'solid');
					this.getElement('.edit-section-header-h2').setStyle('color', 'black');		
				    this.getElement('.edit-section-header-arrow').setStyle('background-position', '0 -111px');

				}
	   		})
		},
		onBackground: function(toggler, element){
			toggler.setStyle('color', 'black');
			toggler.setStyle('border-bottom-color', '#6494B2');
			toggler.setStyle('border-bottom-style', 'solid');
			toggler.setStyle('border-bottom-width-bottom', '1px');
			toggler.getElement('.edit-section-header-h2').setStyle('color', '#6494B2');	
			toggler.getElement('.edit-section-header-arrow').setStyle('background-position', '0 -12px');
			toggler.addEvents({
				mouseenter: function(){
					this.setStyle('border-bottom-color', 'black');
					this.setStyle('border-bottom-style', 'solid');
					this.setStyle('border-bottom-width', '1px');						
					this.getElement('.edit-section-header-h2').setStyle('color', 'black');	
                    this.getElement('.edit-section-header-arrow').setStyle('background-position', '0 -100px');

				},
				mouseleave: function(){
	    			this.setStyle('border-bottom-color', '#6494B2');
					this.setStyle('border-bottom-style', 'solid');
					this.setStyle('border-bottom-width', '1px');
					this.getElement('.edit-section-header-h2').setStyle('color', '#6494B2');	
                    this.getElement('.edit-section-header-arrow').setStyle('background-position', '0 -12px');
				}
	   		})
	   }
   });	
});	