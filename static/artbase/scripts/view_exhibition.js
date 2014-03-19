window.addEvent("domready", init_view_exhibition_js);

function init_view_exhibition_js() {  
  $$("#exhibition-tab span").each(function(x, i) {
    x.addEvent("click", function(evt) {
      evt = new Event(evt);
      $$("#exhibition-tab span").removeClass("selected");
      x.addClass("selected");
      $$("#exhibition-tab-content > div").removeClass("selected");
      $$("#exhibition-tab-content > div")[i].addClass("selected");
    });
  });
}