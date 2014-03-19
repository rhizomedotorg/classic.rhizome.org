window.addEvent("domready", initFeatured);

var spinner;

function getFeaturedList(listType) {
  new Request({
    url: "/artbase/fragments/featured_list/" + listType,
    method: "get",
    onSuccess: function(rtxt, rxml) {
      spinner.hide();
      $("artbase-highlights-content").set("html", rtxt);
    },
    onFailure: function(rtxt) {
    }
  }).send();
}

function initFeatured() {
  spinner = new Spinner($("artbase-highlights-content"), {
    onShow: onSpinnerShow,
    onHide: onSpinnerHide
  });
  $$("#artbase-highlights-tabbar .nav-item").each(function(x, i) {
    x.addEvent("click", function(e) {
      e = new Event(e);
      x.getParent(".mini-nav").getChildren(".nav-item.selected").removeClass("selected");
      x.getParent(".mini-nav").getChildren(".nav-item")[i].addClass("selected");
      spinner.show();
      getFeaturedList(x.get("rel"));
    });
  });
}

function onSpinnerShow() {
  $("artbase-highlights-content").empty();
  $("artbase-highlights-content").addClass("loading");
}

function onSpinnerHide() {
  $("artbase-highlights-content").removeClass("loading");
}