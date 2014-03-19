/* window.addEvent("domready", function(){ */
    var palettes = $$('.color_palette');
    var buttons = $$('.bbpalette');  
    
    palettes.each(function(element) {
        element.addEvent('click', function(e){
            e.stopPropagation();
        });
    });
    buttons.each(function(element) {
        element.addEvent('click', function(e){
            e.stopPropagation();
        });
    });
/* }); */

function displayPalette(button){ 
    palette = button.getNext();
    togglePalette(button, palette);    
}

function hidePalettes(){
    var palettes = $$('.color_palette');
    var buttons = $$('.bbpalette');  
    
    palettes.each(function(element) {
        element.style.display = 'none';
    });

    buttons.each(function(element) {
        element.value = 'Color';
    });
}
    
function togglePalette(button, palette, s){    
    if (!s){
        s = (palette.style.display == '' || palette.style.display == 'block') ? -1  : 1;
    }
            
    if (s == 1) {
        palette.style.display = 'block';
        button.value = 'Hide Colors';
        $(document.body).addEvent('click', hidePalettes);
        
        button.addEvent('click', function(e){
            e.stopPropagation();
        });
        
        palette.addEvent('click', function(e){
            e.stopPropagation();
        });

    } else {
        palette.style.display = 'none';
        button.value = 'Color';
        $(document.body).removeEvent('click', hidePalettes);
    }
}
