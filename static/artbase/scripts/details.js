window.addEvent("domready", init);

/*
  This file defines the logic for adding/deleting subforms to CouchDB forms in the Artwork
  Details form - David
*/

function init() {
  $$(".add-form").addEvent("click", addForm);
  $$(".delete-form").addEvent("click", deleteForm);
}


function updateManagerForm(type) {
  var totalCount = $$("input[name="+type+"-TOTAL_FORMS]")[0],
      n = parseInt(totalCount.get("value"));
  totalCount.set("value", n+1);
}


function addForm(evt) {
  evt = new Event(evt);

  var type = evt.target.get("data-type"),
      formset = $(type+"-formset"),
      forms = formset.getElements("."+type+"-form"),
      clone = forms[0].clone(),
      count = forms.length;

  clone.getElements("input").each(function(x) {
    x.set("name", x.get("name").replace(/-\d+-/, "-"+count+"-"));
    x.set("value", "");
  });

  clone.inject(forms.getLast(), 'after');
  updateManagerForm(type);
}


function deleteForm(evt) {
  evt = new Event(evt);

  var form = evt.target.getParent(".form"),
      type = form.get("data-type"),
      idx = parseInt(form.get("id").split("-").getLast()),
      deleteInput = form.getElement(["#id_"+type, idx, "DELETE"].join("-"));
  
  if(!confirm("Are you want to delete this "+type+"? There is no undo.")) {
    return;
  }

  form.addClass("display-none"); // hide the form

  // mark for deletion
  form.addClass("deleted");
  deleteInput.set("checked", "yes");
}