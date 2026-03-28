document.addEventListener("DOMContentLoaded", function () {
  var btnGps = document.getElementById("btn-gps");
  var geoStatus = document.getElementById("geo-status");
  var latitudeInput = document.getElementById("latitude");
  var longitudeInput = document.getElementById("longitude");
  var altitudeInput = document.getElementById("altitude");
  var accuracyInput = document.getElementById("accuracy");
  var altitudeAccuracyInput = document.getElementById("altitude_accuracy");

  if (!navigator.geolocation) {
    btnGps.style.display = "none";
    geoStatus.textContent = "Geolocation is not supported by this browser.";
    return;
  }

  btnGps.addEventListener("click", function () {
    btnGps.disabled = true;
    geoStatus.textContent = "Acquiring location\u2026";

    navigator.geolocation.getCurrentPosition(
      function (position) {
        var coords = position.coords;
        latitudeInput.value = coords.latitude;
        longitudeInput.value = coords.longitude;
        altitudeInput.value = coords.altitude != null ? coords.altitude : "No data";
        accuracyInput.value = coords.accuracy;
        altitudeAccuracyInput.value = coords.altitudeAccuracy != null ? coords.altitudeAccuracy : "No data";
        geoStatus.textContent = "Location acquired";
        btnGps.disabled = false;
      },
      function (error) {
        var message;
        switch (error.code) {
          case 1:
            message = "Location permission denied. Enter coordinates manually.";
            break;
          case 2:
            message = "Location unavailable. Enter coordinates manually.";
            break;
          case 3:
            message = "Location request timed out. Try again or enter coordinates manually.";
            break;
          default:
            message = "An unknown error occurred. Enter coordinates manually.";
        }
        geoStatus.textContent = message;
        btnGps.disabled = false;
      }
    );
  });
});
