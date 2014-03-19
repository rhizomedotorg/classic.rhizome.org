window.addEvent("domready", init);

function init() {
    new UnsaveArtworkHandler($$('.unsave-artwork-form'));
}

var UnsaveArtworkHandler = new Class({
    Implements: [Events, Options],
    
    defaults: {},
    
    initialize: function(el) {
        this.trigger = el;
        this.attachEvents();
    },
  
    attachEvents: function(args) {
        this.trigger.addEvent('submit', function(e){
            e.stop();
            new Request({
                method: 'POST',
                url: this.get('action'),
                onSuccess: function(rtxt,rxml) { 
                    var artwork_button = $('unsave-artwork-button');
                    alert (artwork_button)
                    if (rtxt == "removed"){
                        artwork_button.set("html", "REMOVED");
                    }
                    if (rtxt == "saved"){
                        artwork_button.set("html", "SAVED");
                    }

                }
            }).send(this);
        });    
    },
});   