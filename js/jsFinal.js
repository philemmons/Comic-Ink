// JavaScript File -- careful !!!!  examine url for '?''

function lettersOnly(cs) {
  let valid = true;
  let str = $(cs).val();

  $(cs + "Error").html("");
  if (/[0-9]+/g.test(str)) {
    displayError(cs, "Letters Only.");
    valid = false;
  } else $(cs).css("backgroundColor", "");
  return valid;
}

function notBlank(field) {
  let valid = true;
  let str = $(field).val();

  $(field + "Error").html("");
  if (str === "") {
    displayError(field, "Must enter a name.");
    valid = false;
  } else $(field).css("backgroundColor", "");
  return valid;
}

function validateUpdate() {
  let isValid = false;
  if (lettersOnly("#city") && lettersOnly("#state") && notBlank("#conName") && validateYear("#year")) {
    isValid = true;

    //javascript - Bootstrap modal show event - Stack Overflow
    //http://jsfiddle.net/BeL2V/1233/
    // set focus when modal is opened
    $("#modal-content").on("shown.bs.modal", function () {
      $("#txtname").focus();
    });

    // show the modal onload
    $("#modal-content").modal({
      show: true,
    });
  }
  return isValid;
}

function displayError(elementId, errorMessage) {
  $(elementId + "Error")
    .css("color", "red")
    .append(errorMessage); //NOTE: +"Error" modifies the element ID!
  $(elementId).css("backgroundColor", "#FFDEDE").focus();
}

function validateInsert() {
  let isValid = true;
  //alert(isValid);
  $(":input[type=text]").each(function () {
    if ($(this).val() == "") {
      //alert(this.val());
      //alert($(this).attr('id'))
      let formID = $(this).attr("id");
      $("#" + formID + "Error").html("");
      displayError("#" + formID, "This is a required field.");
      isValid = false;
    }
  });

  //alert(isValid);
  return isValid;
}

$(document).ready(function () {
  $("#city").change(function () {
    lettersOnly("#city");
  });

  $("#state").change(function () {
    lettersOnly("#state");
  });

  $("#year").change(function () {
    validateYear("#year");
  });

}); //documentReady

function resetFields() {
  $(":input").each(function () {
    let formID = $(this).attr("id");
    $("#" + formID + "Error").html("");
    $("#" + formID).css("backgroundColor", "");
    isValid = false;
  });
  $("#addDisplay").html("");
  return isValid;
}

function validateYear(userYear) {
  let thisYear = new Date().getFullYear();
  const pYear = parseInt(userYear);

  if (pYear.length != 4) return false;
  if (!pYear.match(/\d{4}/)) return false;
  if (thisYear + 2 < pYear || pYear < thisYear - 2) return false;
  
  return true;
}

