window.addEvent("domready", overlayInit);

function overlayInit() {
    var forms = $$('#announce_form, #comment_form, #artwork-form, #exhibition-form');
    if(forms){
        forms.each(function(form) {
            form.addEvent('submit', function(e){ 
                createLoadingOverlay();
            });
        });
    }
}

function createLoadingOverlay(x,y){
    var overlay = new Mask();
    loadingTop = window.getScroll().y + (window.innerHeight/2);
    loadingLeft = window.innerWidth/2;
    overlay.element.setStyle("background-position",loadingLeft+"px "+loadingTop+"px");
    overlay.show();
}

function removeLoadingOverlay(){
    $$('.mask').each(function(el) {
        el.setStyle('display', 'none');
    });
}
