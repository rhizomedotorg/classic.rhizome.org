window.addEvent("domready", init);
 
var artworks, _clone;

function init() {
  artworks = new Sortables("ul#reorder-works", {
    constrain: true,
    clone: true,
    handle: ".handle",
    revert: { duration: 1500, transition: 'elastic:out' },
    onStart: function(element, clone) {
      _clone = clone;
      clone.addClass("clone");
    },
    onComplete: function(element) {
      _clone.removeClass("clone");
      _clone.destroy();
      var ul = $$("ul#reorder-works")[0],
          xs = ul.getElements("li"),
          ids = xs.map(function(x, i) {
            return x.get("rel");
          });
      $("id_artworks").set("value", ids.join(" "));
    }
  });
}