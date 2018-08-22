$('#show_analytics').click(function() {
  $("#analytics").toggle();
});
$("#analytics").hide();

$('#run_analytics_bt').click(function() {
  $("#load_tab").toggle();
  $("#analytics").hide();
  $("#run_analysis_bt").toggle();
});
$("#load_tab").hide();

function isNumberKey(evt){
  var charCode = (evt.which) ? evt.which : event.keyCode
  if (charCode > 31 && (charCode < 48 || charCode > 57))
      return false;
  return true;
}