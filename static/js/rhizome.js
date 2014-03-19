window.addEvent("domready", init);

if(typeof console == "undefined") {
    var console = {
        log: function() {},
        warning: function() {},
        error: function() {}
    };
}


function init() {
    initFlashBanner();
}

// -----------------------------------------------------------------------------
// Mini Profiles
// -----------------------------------------------------------------------------

var RhizomeUsersMiniProfile = new Class({
  Implements: [Events, Options],
  name: "RhizomeUsersMiniProfile",

  defaults: {
  },

  initialize: function(options) {
    //console.log("initialize RhizomeUsersMiniProfile");
    this.setOptions(this.defaults, options);
    this.initElement();
    this.triggers = $$(".miniprofile");
    this.triggers.addEvent("mouseenter", function(evt) {
      evt = new Event(evt);
      var miniprofile = evt.target.getParent(".miniprofile");
      if(miniprofile) {
        this._show(miniprofile.get("rel"), miniprofile);        
      }
    }.bind(this));
    this.element.addEvent("mouseleave", function(evt) {
      evt = new Event(evt);
      this.hide();
    }.bind(this));
  },

  initElement: function() {
    this.element = new Element("div", {
      "id": "rhiz-miniprofile",
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

  _show: function(userId, target) {
    new Request({
      url: "/profile/"+userId+"/miniprofile/",
      onSuccess: function(rtxt, rxml) {
        this.show(rtxt, target);
      }.bind(this)
    }).send();
  },

  show: function(html, target) {
    var pos = target.getPosition();
    this.element.setStyles({
      left: pos.x-12,
      top: pos.y-12
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

// -----------------------------------------------------------------------------
// Banner Toggle
// -----------------------------------------------------------------------------

function initFlashBanner() {
  var fbc = $("flash-banner-close");
  if (fbc) $("flash-banner-close").addEvent("click", function(evt) {
    evt = new Event(evt);
    $("flash-banner").setStyle("display", "none");
  });
}