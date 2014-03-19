// -----------------------------------------------------------------------------
// CALENDAR WIDGET
// -----------------------------------------------------------------------------
(function() {

window.addEvent("domready", init);

function init() {
  new calendarDayListing();
}

var calendarDayListing = new Class({
  Implements: [Events, Options],
  name: "calendarDayListing",

  defaults: {
  },

  initialize: function(options) {
    this.setOptions(this.defaults, options);
    this.initElement();
    this.triggers = $$(".calendar-lookup-day");
    
    this.triggers.addEvent("mouseenter", function(evt) {
      evt = new Event(evt);
      var day = evt.target;
      if(!day.hasClass("calendar-lookup-day")) {
          day = day.getParent(".calendar-lookup-day");
      }
      if(day) {
        this._show(day.get("rel"), day);       
      }
    }.bind(this));

    this.element.addEvent("mouseleave", function(evt) {
      evt = new Event(evt);
      var related = $(evt.relatedTarget);
      this.hide();
    }.bind(this));
    
    this.triggers.addEvent("mouseleave", function(evt) {
      evt = new Event(evt);
      var related = $(evt.relatedTarget);
      if(related.hasClass("event-count")) return;
      this.hide();
    }.bind(this));
    
  },

  initElement: function() {
    this.element = new Element("div", {
      "id": "widget-listing",
      "class": "display-none"
    });
    this.element.set("tween", {
      duration: 200,
      transition: Fx.Transitions.Cubic.easeIn
    });
    $(document.body).grab(this.element);
  },

  attachEvents: function() {
  },

  _show: function(date, target) {
    new Request({
      url: "/announce/listing/widget/"+date+"/",
      onSuccess: function(rtxt, rxml) {
        this.show(rtxt, target);
      }.bind(this)
    }).send();
  },

  show: function(html, target) {
    var pos = target.getPosition();
    this.element.setStyles({
      left: pos.x+1,
      top: pos.y+27
    });
    this.element.setStyle("opacity", 0);
    this.element.removeClass("display-none");
    this.element.set("html", html);
    this.element.tween("opacity", 1);
    this.attachEvents();
  },

  hide: function() {
    this.element.addClass("display-none");
  }
});

})()