/////////
//carried over from legacy site - nh 
////////

function toggleCCFields(use_cc_license) {
  //alert(use_cc_license.value);
  updateCCFields(use_cc_license.form, use_cc_license.value != 'Yes');
}

function updateCCFields(form, disabled) {
  //alert( disabled ? 'off' : 'on');
  var fields = new Array('cc_commercial', 'cc_derivative', 'license_select');
  // , 'field_jurisdiction', 'field_format'
  for(var i=0; i < fields.length; i++) {
    var f = fields[i];
    if (false) { // f == 'field_jurisdiction' || f == 'field_format'
      form[f].disabled = disabled;
      //alert(form[f]);
    } else {
      for(var j=0; j < form[f].length; j++) {
        form[f][j].disabled = disabled;
        //alert(form[f][j]);
      }
    }
  }
  
  var licensebox = document.getElementById('licensebox');
  licensebox.style.color = disabled ? '444444' : '000000';
  
  pickLicense();
}

function is_cc_license_disabled() {
  return getRadioValue(document.forms.artwork.use_cc_license) == 'No';
}

function pickLicense() {
  var form = document.forms.artwork;
  form.license_slug.value = '';
  
  if (!is_cc_license_disabled()) {
    for( slug in pickLicense.license_info ) {
      //alert(slug);
      var is_match = true,
          expected_fields = pickLicense.license_info[slug].fields;
      for (key in expected_fields) {
        if (getRadioValue(form['cc_'+key]) != expected_fields[key]) {
          is_match = false;
          break;
        }
      }
      if (is_match) {
        form.license_slug.value = 'cc_' + slug;
        break;
      }
    }
  }
  
  var slug = form.license_slug.value.substr(3);
  if (slug){
    var license_url = pickLicense.license_info[slug].assets["url"];
    var license_image = pickLicense.license_info[slug].assets["image"];
    setSelectValue(form.license_select, slug);
    setLicenseButton(form, slug,license_url,license_image);
  }

}

function setLicenseButton(form, slug,license_url,license_image) {
  if (slug == '') {
    var button = '';
  } else {
    var button = get_template('CC_button_template');
    button = button.replace(/%LICENSE_URL%/g, license_url);
    button = button.replace(/%LICENSE_IMAGE%/g, license_image);    
    button = button.replace(/%CC_NAME%/g, getSelectText(form.license_select));
  }
  
  $('license_button').innerHTML = button;  
}

function setFieldsByLicense(license_select) {
  if(!is_cc_license_disabled()){
    var form = license_select.form,
        slug = license_select[license_select.selectedIndex].value,
        fields = pickLicense.license_info[slug].fields;
    for( f in fields ) {
      setRadioValue(form['cc_'+f], fields[f]);
    }  
    setLicenseButton(form, slug);
  }
}

function setFieldsByLicenseSlug(license_slug) {
  var form = license_slug.form,
      slug = license_slug.value.substr(3);
  //alert('slug: '+slug);    
  if (slug == '') {
    setRadioValue(form.use_cc_license, 'No');
  } else {    
    var fields = pickLicense.license_info[slug].fields;
    
    for( f in fields ) {
      setRadioValue(form['cc_'+f], fields[f]);
    }
    
    setLicenseButton(form, slug);
  }
  
  updateCCFields(form, is_cc_license_disabled() );
}

function getRadioValue(field) {
  for(var i=0; i < field.length; i++) {
    if (field[i].checked) {
      return field[i].value;
    }
  }
  return null;
}

function setRadioValue(field, value) {
  for(var i=0; i < field.length; i++) {
    field[i].checked = field[i].value == value;
  }
}

function setSelectValue(field, value) {
  //alert(field);
  //alert(value);
  for(var i=0; i < field.length; i++) {
    field[i].selected = field[i].value == value;
  }
}

function getSelectText(field) {
  for(var i=0; i < field.length; i++) {
    if (field[i].selected) return field[i].text;
  }
  return null;
}

function get_template(name) {
  return $(name).innerHTML;
}

/*
pickLicense.license_info = {
  'by-nc-sa' : {
    label : 'Attribution-NonCommercial-ShareAlike Creative Commons',
    fields : {
      commercial : 'No',
      derivative : 'SA'
    }
  },
  'by-nc' : {
    label : 'Attribution-NonCommercial Creative Commons',
    fields : {
      commercial : 'No',
      derivative : 'Yes'
    }
  },
  'by-nc-nd' : {
    label : 'Attribution-NonCommercial-NoDerivs Creative Commons',
    fields : {
      commercial : 'No',
      derivative : 'No'
    }
  },
  'by' : {
    label : 'Attribution Creative Commons',
    fields : {
      commercial : 'Yes',
      derivative : 'Yes'
    }
  },
  'by-sa' : {
    label : 'Attribution-ShareAlike Creative Commons',
    fields : {
      commercial : 'Yes',
      derivative  : 'SA'
    }
  },
  'by-nd' : {
    label : 'Attribution-NoDerivs Creative Commons',
    fields : {
      commercial : 'Yes',
      derivative : 'No'
    }
  }
};
*/
function cc_popup(info_type) {
  window.open('http://creativecommons.org/characteristic/' + info_type + '?lang=en', 'characteristic_help', 'width=375,height=300,scrollbars=yes,resizable=yes,toolbar=no,directories=no,location=yes,menubar=no,status=yes');
}
