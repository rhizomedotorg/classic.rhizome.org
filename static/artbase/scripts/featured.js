/* currently unused */

window.addEvent("domready", init_buttons);

if(typeof console.log == undefined) {
  var console = {
    log : function() {}
  };
}

function selectWorkButtons() {
  return $$('#featured-nav button.select-work');
}

function init_buttons() {
  console.log("Init featured carousel");
  
  selectWorkButtons().addEvent("click", function(evt) {
    evt = new Event(evt);
      var idx = evt.target.getParent("div").getChildren("button").indexOf(evt.target);
    fetchArtworkFragment(idx);
  });
  
  $$("#featured-nav button.next-work").addEvent("click", function(evt) {
    evt = new Event(evt);
    var selected = $$("#featured-nav button.selected")[0],
    buttons = selectWorkButtons(),
    idx = buttons.indexOf(selected);
    idx = (idx + 1) % buttons.length;
    fetchArtworkFragment(idx);
  });
}

function fetchArtworkFragment(idx) {
  console.log("fetchArtworkFragment", idx);
  new Request({
    url: "/artbase/fragments/featured_work/" + featured_works[idx].work_id,
    method: "get",
    onSuccess: function(rtxt, rxml) {
      $$('#featured-work img')[0].set("src", featured_works[idx].image);
      $('featured-work-content').set("html", rtxt);
      init_buttons();
      var buttons = selectWorkButtons();
      buttons.removeClass("selected");
      buttons[idx].addClass("selected");
    },
    onFailure: function(rtxt) {
    }
  }).send();
}