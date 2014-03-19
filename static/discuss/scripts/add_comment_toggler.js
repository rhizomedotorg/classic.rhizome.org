window.addEvent( 'domready', function(){
 $$( '.reply' ).each(function(item){
  var commentSlider = new Fx.Slide( item.getElement( '.add-comment' ), { duration: 400 } );
  commentSlider.toggle();
  item.getElement( '.comment-reply' ).addEvent( 'click', function(){ commentSlider.toggle(); } );
 } );
} );