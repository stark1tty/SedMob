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

  function fillPosition(position) {
    var coords = position.coords;
    latitudeInput.value = coords.latitude;
    longitudeInput.value = coords.longitude;
    altitudeInput.value = coords.altitude != null ? coords.altitude : "No data";
    accuracyInput.value = coords.accuracy;
    altitudeAccuracyInput.value =
      coords.altitudeAccuracy != null ? coords.altitudeAccuracy : "No data";
    geoStatus.textContent = "Location acquired";
    btnGps.disabled = false;
  }

  function handleError(error) {
    var message;
    switch (error.code) {
      case 1:
        message = "Location permission denied. Enter coordinates manually.";
        break;
      case 2:
        message = "Location unavailable. Enter coordinates manually.";
        break;
      case 3:
        message = "Location request timed out. Try again or enter manually.";
        break;
      default:
        message = "An unknown error occurred. Enter coordinates manually.";
    }
    geoStatus.textContent = message;
    btnGps.disabled = false;
  }

  function requestPosition() {
    navigator.geolocation.getCurrentPosition(fillPosition, handleError, {
      enableHighAccuracy: true,
      timeout: 15000,
      maximumAge: 0,
    });
  }

  btnGps.addEventListener("click", function () {
    btnGps.disabled = true;
    geoStatus.textContent = "Acquiring location\u2026";

    /* Use Permissions API to check/request before calling geolocation.
       This triggers the browser prompt proactively on supporting browsers. */
    if (navigator.permissions && navigator.permissions.query) {
      navigator.permissions
        .query({ name: "geolocation" })
        .then(function (result) {
          if (result.state === "granted" || result.state === "prompt") {
            requestPosition();
          } else {
            /* denied */
            geoStatus.textContent =
              "Location permission is blocked. Please enable it in your browser or device settings, then try again.";
            btnGps.disabled = false;
          }
        })
        .catch(function () {
          /* Permissions API not fully supported, fall through */
          requestPosition();
        });
    } else {
      /* No Permissions API (older browsers, some WebViews) — just try directly */
      requestPosition();
    }
  });
});
