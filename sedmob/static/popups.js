/* popups.js — Contextual help popups for field labels */

var FIELD_DESCRIPTIONS = {
  // Profile form fields
  "name": "A short identifying name for this log profile (e.g., outcrop name or borehole ID).",
  "description": "Optional notes about this log \u2014 location details, purpose, or context.",
  "direction": "Borehole mode records beds top-down (depth increases). Exposure mode records bottom-up (stratigraphic order).",
  "latitude": "Latitude in decimal degrees (e.g., 52.2297). Use the GPS button to auto-fill.",
  "longitude": "Longitude in decimal degrees (e.g., 21.0122). Use the GPS button to auto-fill.",
  "altitude": "Elevation above sea level in metres. Auto-filled by GPS if available.",
  "accuracy": "Horizontal GPS accuracy in metres. Auto-filled by GPS.",
  "altitude_accuracy": "Vertical GPS accuracy in metres. Auto-filled by GPS.",

  // Bed form fields
  "thickness": "Thickness of this bed in centimetres. Required field.",
  "top": "Depth/height of the top of this bed in metres.",
  "bottom": "Depth/height of the bottom of this bed in metres.",
  "facies": "Facies code or name for this bed (e.g., Sm, Gm, Fl).",
  "notes": "Free-text observations \u2014 anything not captured by other fields.",
  "paleocurrent": "Paleocurrent direction measurement (e.g., azimuth in degrees).",
  "boundary": "Type of contact at the base of this bed (e.g., sharp, gradational, erosional).",

  // Lithology 1-3
  "lit1_group": "Broad lithology category for the primary component (e.g., Siliciclastic, Carbonate).",
  "lit1_type": "Specific lithology for the primary component (e.g., Sandstone, Limestone).",
  "lit1_percentage": "Percentage of this bed composed of lithology 1. The three lithology percentages must sum to 100%.",
  "lit2_group": "Broad lithology category for the second component.",
  "lit2_type": "Specific lithology for the second component.",
  "lit2_percentage": "Percentage of lithology 2. Adjusted automatically to keep the total at 100%.",
  "lit3_group": "Broad lithology category for the third component.",
  "lit3_type": "Specific lithology for the third component.",
  "lit3_percentage": "Percentage of lithology 3. Calculated as the remainder after lithologies 1 and 2.",

  // Grain size
  "phi_clastic_base": "Clastic grain size at the base of this bed (Wentworth scale).",
  "phi_clastic_top": "Clastic grain size at the top of this bed \u2014 use with base to show grading.",
  "phi_carbo_base": "Carbonate grain size at the base (Dunham/Folk classification).",
  "phi_carbo_top": "Carbonate grain size at the top of this bed.",

  // Bioturbation
  "bioturbation_type": "Type or trace fossil name for bioturbation observed in this bed.",
  "bioturbation_intensity": "Intensity of bioturbation (e.g., 0\u20135 ichnofabric index, or descriptive).",

  // Structures & Symbols
  "structures": "Sedimentary structures observed (e.g., cross-bedding, ripples, lamination).",
  "bed_symbols": "Additional symbols or annotations for this bed."
};

/* --- Popup helpers --- */

function removeExistingPopup() {
  var existing = document.querySelector('.field-popup');
  if (existing) existing.remove();
}

function createPopup(text, anchorEl) {
  removeExistingPopup();

  var popup = document.createElement('div');
  popup.className = 'field-popup';
  popup.textContent = text;
  document.body.appendChild(popup);

  // Position below the anchor label
  var rect = anchorEl.getBoundingClientRect();
  var scrollX = window.pageXOffset || document.documentElement.scrollLeft;
  var scrollY = window.pageYOffset || document.documentElement.scrollTop;

  var topPos = rect.bottom + scrollY + 4;
  var leftPos = rect.left + scrollX;

  popup.style.left = leftPos + 'px';
  popup.style.top = topPos + 'px';

  // Measure after placing so we can correct overflow
  var popupRect = popup.getBoundingClientRect();

  // If overflows viewport bottom, reposition above the label
  if (popupRect.bottom > window.innerHeight) {
    topPos = rect.top + scrollY - popupRect.height - 4;
    popup.style.top = topPos + 'px';
  }

  // If overflows right edge, shift left
  if (popupRect.right > window.innerWidth) {
    leftPos = leftPos - (popupRect.right - window.innerWidth) - 8;
    if (leftPos < 0) leftPos = 4;
    popup.style.left = leftPos + 'px';
  }

  return popup;
}

/* --- DOMContentLoaded: scan labels, inject icons, attach listeners --- */

document.addEventListener('DOMContentLoaded', function() {
  var labels = document.querySelectorAll('label[for]');

  labels.forEach(function(label) {
    var fieldId = label.getAttribute('for');
    if (!FIELD_DESCRIPTIONS[fieldId]) return;

    var descText = FIELD_DESCRIPTIONS[fieldId];

    // Append ⓘ icon span
    var icon = document.createElement('span');
    icon.className = 'field-info-icon';
    icon.textContent = '\u24D8';
    icon.setAttribute('role', 'img');
    icon.setAttribute('aria-label', 'Info');
    label.appendChild(icon);

    // --- Desktop hover behavior ---
    var hoverTimeout;

    label.addEventListener('mouseenter', function() {
      clearTimeout(hoverTimeout);
      createPopup(descText, label);
    });

    label.addEventListener('mouseleave', function() {
      hoverTimeout = setTimeout(function() {
        removeExistingPopup();
      }, 80);
    });

    // --- Touch/click behavior on ⓘ icon ---
    icon.addEventListener('click', function(e) {
      e.preventDefault();
      e.stopPropagation();

      // Toggle: if a popup is already open for this label, close it
      var existing = document.querySelector('.field-popup');
      if (existing && existing._fieldId === fieldId) {
        existing.remove();
        return;
      }

      var popup = createPopup(descText, label);
      popup._fieldId = fieldId;
    });
  });

  // Document click listener: dismiss popup when tapping outside
  document.addEventListener('click', function(e) {
    var popup = document.querySelector('.field-popup');
    if (!popup) return;
    // If click is on the popup itself, keep it open
    if (popup.contains(e.target)) return;
    // If click is on an info icon, the icon handler manages it
    if (e.target.classList && e.target.classList.contains('field-info-icon')) return;
    popup.remove();
  });
});
