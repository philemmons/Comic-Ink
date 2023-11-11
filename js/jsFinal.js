/* JavaScript File - careful examining url for '?'*/

function lettersOnly(cs) {
  let str = $(cs).val();

  $(cs + "Error").html("");
  if (/[0-9]+/g.test(str)) {
    displayError(cs, "Letters Only.");
    return false;
  } else $(cs).css("backgroundColor", "");
  return true;
}

function notBlank(field) {
  let str = $(field).val();

  $(field + "Error").html("");
  if (str === "") {
    displayError(field, "Must enter a name.");
    return false;
  } else $(field).css("backgroundColor", "");
  return true;
}

function validateYear(userYear) {
  let thisYear = new Date().getFullYear();
  const pYear = parseInt(userYear);

  if (pYear.length != 4) return false;
  if (!pYear.match(/\d{4}/)) return false;
  if (thisYear + 2 < pYear || pYear < thisYear - 2) return false;
  
  return true;
}

function validateUpdate() {
  if (lettersOnly("#city") && lettersOnly("#state") && notBlank("#conName") && validateYear("#year")) {
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
    return true;
  }
  return false;
}

function displayError(elementId, errorMessage) {
  $(elementId + "Error")
    .css("color", "red")
    .append(errorMessage); //NOTE: +"Error" modifies the element ID!
  $(elementId).css("backgroundColor", "#FFDEDE").focus();
}

/* Use bootstrap validation for insertCon - 11.10.23 */
/*
function validateInsert() {
  $(":input").each(function () {
    if ($(this).val() == "") {
      //alert(this.val());
      //alert($(this).attr('id'))
      let formID = $(this).attr("id");
      $("#" + formID + "Error").html("");
      displayError("#" + formID, "This is a required field.");
     return false;
    }
  });
  return true;
}
*/

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


/* only for conInsert */
function resetFields() {
  $(":input").each(function () {
    let formID = $(this).attr("id");
    $("#" + formID + "Error").html("");
    $("#" + formID).css("backgroundColor", "");
    return false;
  });
  $("#addDisplay").html("");
  return true;
}

/* only for conUpdate */
function myReset(myForm){
  document.getElementById(myForm).reset(); 
}
