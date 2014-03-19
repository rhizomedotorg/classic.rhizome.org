window.addEvent("domready", init);

if(typeof console.log == undefined) {
  var console = {
    log : function() {}
  };
}

function init(){
    preload_featured_artwork_images();
    init_rotation();
    init_buttons();
}


function preload_featured_artwork_images(){
  images = [];
  for (i = 0, length = featured_works.length; i < length; ++i) {
    images[i] = new Image();
    images[i].src = featured_works[i].image;
  }
}

function init_rotation(){
    if(window.timer){
        clearInterval(window.timer);
    }
    window.timer = window.setInterval('select_and_rotate()', 10000);
}

function init_buttons(timer) {  
  
  selectWorkButtons().addEvent("click", function(evt) {
    evt = new Event(evt);
    var idx = evt.target.getParent("div").getChildren("button").indexOf(evt.target);
    switch_featured_info(idx); 
    init_rotation();
  });
  
  $$("#featured-nav button.next-work").addEvent("click", function(evt) {
    evt = new Event(evt);
    select_and_rotate();   
    init_rotation();
  });
}

function select_and_rotate() {
    var selected = $$("#featured-nav button.selected")[0],
         buttons = selectWorkButtons(),
         idx = buttons.indexOf(selected),
         idx = (idx + 1) % buttons.length;
    switch_featured_info(idx);
}

function selectWorkButtons() {
    return $$('#featured-nav button.select-work');
}

function switch_featured_info(idx){
    var switched = featured_works[idx];
    $('featured-work-link').set('href', switched.url);
    $('featured-work-link').set('html', switched.title);
    $('featured-artist-link').set('href', switched.artist_url);
    $('featured-artist-link').set('html', switched.artist);     
    $('featured-work-image-link').set('href', switched.url);
    var featured_image_element =  new Element('img', {
                src: switched.image,
                'class': 'image',
                'id': 'featured-work-image',
                width: 950,
            });    
    $('featured-work-image-link').empty();
    $('featured-work-image-link').adopt(featured_image_element);         
    
    var tags_html = [];
    for(var i=0;i<switched.tags.length;i++){
        var tag = switched.tags[i],
            tag_element = new Element('a', {
                href: tag.url,
                'class': 'tag',
                html: tag.name,
            });
        tags_html.push(tag_element);
    };
    $('featured_artwork_tags').empty();
    $('featured_artwork_tags').adopt(tags_html);
    var buttons = selectWorkButtons();
    buttons.removeClass("selected");
    buttons[idx].addClass("selected");
}

/*

function select_and_rotate() {
    var selected = $$("#featured-nav button.selected")[0]
    buttons = selectWorkButtons(),
    idx = buttons.indexOf(selected);
    idx = (idx + 1) % buttons.length;
    fetchArtworkFragment(idx);
}


function init_buttons(timer) {  
  selectWorkButtons().addEvent("click", function(evt) {
    evt = new Event(evt);
    var idx = evt.target.getParent("div").getChildren("button").indexOf(evt.target);
    fetchArtworkFragment(idx); 
    
    init_rotation();
  });
  
  $$("#featured-nav button.next-work").addEvent("click", function(evt) {
    evt = new Event(evt);
    var selected = $$("#featured-nav button.selected")[0];
    var buttons = selectWorkButtons();
    idx = buttons.indexOf(selected);
    idx = (idx + 1) % buttons.length;
    fetchArtworkFragment(idx);
    init_rotation();
  });
}
*/


/*
function fetchArtworkFragment(idx) {
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
*/

