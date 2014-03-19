document.addEvent('domready' , function() {  
  var techCats = $$(".tech-cat"),
      techSelectCurrent = $$('.tech-select-current'),
      techCategoriesList = $('tech-categories-list');

    if(techCats){
      techCats.addEvent('click', function() {
        techCats.removeClass("selected");
        this.addClass("selected");
        $$('#tech-type-list .tech-list-container')[0].empty();
        $$("#tech-version-list .tech-list-container")[0].empty();
        updateTypesList(this.get("data-value"));
      });
   }
  
  var addTechButton = $('add-tech');
  if(addTechButton){
    addTechButton.addEvent('click', function() {
        var selection = {
          category: getSelectedCategory(),
          type: getSelectedType(),
          version: getSelectedVersion()
        };
        var techId = validate(selection);
        if(techId) {
          updateSelectedTechList(techId, selection);
          updateSelectedTechListFormField();
          getDeleteButtons();
        }
      });
     getDeleteButtons();
    }

});



function updateSelectedTechList(id, selection) {
  var techSelectClone = $$(".tech-selection").getLast().clone(true,true).inject($('tech-selected'),'top');
  techSelectClone.set("id", "tech-"+id);
  if(!$("tech-selected").hasClass("has-tech")) {
    $("tech-selected").addClass("has-tech");
  }
  var techText = [selection.type, (selection.version || "")].join(" ");
  techSelectClone.getElement("span").set("text", techText);
}

function selectedTechIds() {
  return $$(".tech-selection").filter(function(x) {
    return x.get("id") != "no-tech-selected";
  }).map(function(x) {
    return x.get("id").split("-")[1];
  });
}

function updateSelectedTechListFormField() {
  $('artwork-technologies').empty();
  selectedTechIds().each(function(id, i) {
    var el = new Element("input", {
      id: 'id_artworkstub-technologies_'+i,
      type: "hidden",
      name: "artworkstub-technologies",
      value: id
    });
    el.inject($('artwork-technologies'), 'top');
  });
}

function getDeleteButtons(){
    var delete_buttons =  $$('#tech-selected .delete');
    delete_buttons.each(function(button) {
        button.addEvent('click', deleteTechnology);
     });
     //delete_buttons.addEvent('click', deleteTechnology);
}

function deleteTechnology(evt) {
  var el = evt.target.getParent("li").dispose();
  updateSelectedTechListFormField();
}

function getSelectedCategory() {
  return $("tech-category-list").getElement(".selected").get("text");
}

function getSelectedType() {
  var s = $("tech-type-list").getElement(".selected");
  if(s) return s.get("text");
  return null;
}

function getSelectedVersion() {
  var s = $("tech-version-list").getElement(".selected");
  if(s) return s.get("text");
  return null;
}

// returns eithe the tech id or false
function validate(selection) {
  var cat = tech_data[selection.category];
  if(!cat) return false;
  var type = cat[selection.type];
  if(!type) return false;
  if(!(type instanceof Object)) return type;
  var version = type[selection.version];
  if(!version) return false;
  return version;
}

function updateTypesList(category) {
  new Request({
    url: "/artbase/get_tech_types/?category="+category,
    method: "get",
    onSuccess: function(rtxt, rxml) {
      var techTypesListContainer = $$('#tech-type-list .tech-list-container')[0];
      techTypesListContainer.set("html", rtxt);
      var techTypes = techTypesListContainer.getElements(".tech-type");
      techTypes.addEvent('click', function(evt) {
        techTypes.removeClass("selected");
        this.addClass("selected");
        updateVersionsList(this.get("data-value"));
      });
    },
    onFailure: function(rtxt) {
      $$('#tech-type-list .tech-list-container')[0].empty();
    }
  }).send();
}

function updateVersionsList(version) {
  new Request({
    url: "/artbase/get_tech_versions/?type="+version,
    method: "get",
    onSuccess: function(rtxt, rxml) {
      var techVersionsListContainer = $$('#tech-version-list .tech-list-container')[0];
      techVersionsListContainer.set("html", rtxt);
      var techVersions = techVersionsListContainer.getElements(".tech-version");
      techVersions.addEvent('click', function(evt) {
        techVersions.removeClass("selected");
        this.addClass("selected");
      });
    },
    onFailure: function(rtxt) {
      $$('#tech-version-list .tech-list-container')[0].empty();
    }
  }).send();
}


