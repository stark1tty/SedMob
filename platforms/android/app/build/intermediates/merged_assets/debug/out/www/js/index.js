
var app = {
	// Application Constructor
	initialize: function() {
		this.bindEvents();
	},
	// Bind Event Listeners
	//
	// Bind any events that are required on startup. Common events are:
	// 'load', 'deviceready', 'offline', and 'online'.
	bindEvents: function() {
		document.addEventListener('deviceready', this.onDeviceReady, false);
	},
	// deviceready Event Handler
	//
	// The scope of 'this' is the event. In order to call the 'receivedEvent'
	// function, we must explicity call 'app.receivedEvent(...);'
	onDeviceReady: function() {
		app.receivedEvent('deviceready');
	},
	// Update DOM on a Received Event
	receivedEvent: function(id) {
		StartDatabase();
	}
};

// starting database, loading profiles

function StartDatabase() {
	sessionStorage.selectedprofile=0;

	var theme = window.localStorage.getItem("sedmob-theme");
	if ( (theme != 'a') && (theme != 'b') ) {
		window.localStorage.setItem("sedmob-theme", "b");
		theme_refresh ();
	}

	db = window.openDatabase("Sedmob", "1.0", "Logs", 10000000);
    
	var storagefirstrun = window.localStorage.getItem("sedmob-firstrun");
	if (storagefirstrun != 'true') {
		navigator.notification.alert(
		'SedMob is run for the first time. A database will be populated. It may take some time.',  // message
		function (){},         // callback
		'First run',            // title
		'OK'                  // buttonName
		);
		db.transaction(populateDB, errorCB);
		window.localStorage.setItem("sedmob-firstrun", "true");
	}

	homerefresh ();
}
