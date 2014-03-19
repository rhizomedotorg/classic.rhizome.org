window.addEvent("domready", initRanking);
 
var propoosals, _clone;

function initRanking() {
  propoosals = new Sortables("#finalists", {
    constrain: true,
    clone: true,
    handle: ".ranking-finalist",
    revert: { duration: 1500, transition: 'elastic:out' },
    onStart: function(element, clone) {
      _clone = clone;
      clone.addClass("clone");
    },
    onComplete: function(element) {
      _clone.removeClass("clone");
      _clone.destroy();
      var container = $$("#finalists")[0],
          xs = container.getElements(".ranking-finalist"),
          ids = xs.map(function(x, i) {
            return x.get("id");
          });
      $("id_rankings").set("value", ids.join(" "));
      
      if($("ranking-saved-notice")){
           $("ranking-saved-notice").setStyle("display", "none");
      }
      
      $("quick-save").setStyle("display", "block");
    }
  });
}
