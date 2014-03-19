window.addEvent("domready", init);

function init() {
  new SaveArtworkHandler($('save-artwork-form'));
  new ExhibitionWidget($('add-to-exhibition'));
}

var SaveArtworkHandler = new Class({
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
          var artwork_button = $('save-artwork-button');
          
          if (rtxt == "saved"){
            artwork_button.removeClass("unsaved-artwork");
            artwork_button.addClass("saved-artwork");
            artwork_button.set("html", "Saved!");
          }
          
          if (rtxt == "removed"){
            artwork_button.removeClass("saved-artwork");
            artwork_button.addClass("unsaved-artwork");
            artwork_button.set("html", "Save this");
          }
        }
      }).send(this);
    });    
  },
});    


var ExhibitionWidget = new Class({
  Implements: [Events, Options],

  defaults: {},
  
  initialize: function(el, options) {
    this.setOptions(options);
    this.trigger = el;
    this.createElement();
    this.attachEvents();
  },

  createElement: function() {
    this.element = new Element("div", {
      id: "exhibition-widget",
      'class': 'display-none',
      html: $('exhibition-widget').get("html")
    });
    var s = this.element.getElement("select");
    var prompt = s.getElement("option");
    
    users_exhibitions.each(function(x, i) {
      s.grab(new Element("option", {
        text: x.title,
        value: x.id
      }));
    }, this);

     $(document.body).grab(this.element,'bottom');
        
    this.element.getElement("#add-to").setStyle("display", "block");

    if(users_exhibitions.length == 0) {
      this.element.getElement("#add-to").setStyle("display", "none");
      this.element.getElement("#start-new").set("text", "Start a new exhibition with this work");
      this.element.getElement(".options").setStyle("height", 75);
    } else if (users_exhibitions.length == 1) {
      s.getElement("option").set("text", "Add to your exhibition");
    } else {
      s.getElement("option").set("text", "Add to one of your "+ users_exhibitions.length + " exhibitions");
    }
  },

  attachEvents: function(args) {
    this.trigger.addEvent("click", function(evt) {
      evt = new Event(evt);
      this.show();
    }.bind(this));

    this.element.getElement(".cancel").addEvent("click", function(evt) {
      evt = new Event(evt);
      var tag = evt.target.get("tag");
      if(!['select', 'options'].contains(tag)) this.hide();
    }.bind(this));

    /*
    this.element.addEvent("mouseleave", function(evt) {
      evt = new Event(evt);
      var tag = evt.target.get("tag");
      if(!['select', 'options'].contains(tag)) this.hide();
    }.bind(this));
    */

    this.element.getElement("button.add").addEvent("click", this.createExhibition.bind(this));
    this.element.getElement("input").addEvent("keyup", function(e) {
      var evt = new Event(e);
      if(evt.key == 'enter') this.createExhibition(e);
    }.bind(this));

    this.element.getElement("select").addEvent("change", function(e) {
      var evt = new Event(e);
      this.addToExhibition(e);
    }.bind(this));
  },

  /*
    This function does not actually create an exhibition. It simply opens
    a new window with the exhibition form prepopulated with a couple of
    values.
   */
  createExhibition: function(evt) {
    evt = new Event(evt);
    var action = "/artbase/exhibitions/new?title={title}&id={id}".substitute({
      title: escape(this.element.getElement("#exhibition_name").getProperty("value")),
      id: artwork.work_id
    }); 
    window.open(action);
  },

  /*
    This actually submits a form.
   */
  addToExhibition: function(evt) {
    evt = new Event(evt);
    var id = evt.target.get("value"),
        action = "/artbase/exhibitions/edit/" + id + "/add_work/",
        form = this.element.getElement("form#add-work");
    form.set("action", action);
    form.getElement("#artwork_id").set("value", artwork.work_id);
    form.submit();
  },


  show: function() {
    var pos = this.trigger.getPosition();
    this.element.setStyles({
      left: pos.x,
      top: pos.y
    });
    this.element.removeClass("display-none");
  },


  hide: function() {
    this.element.addClass("display-none");
  }
});