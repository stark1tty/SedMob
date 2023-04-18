$( document ).delegate("#addprofile", "pageshow", function() {
	if (sessionStorage.selectedprofile != 0) {
		loadprofileDB();
	}
	sessionStorage.selectedbed=0;
});

$( document ).delegate("#addprofile", "pageinit", function() {

	$('#direction').change(function(event) {
		db.transaction(function (tx) {
			var tag = 'UPDATE beds SET position='+sessionStorage.numberofbeds+'-position+1';
			tx.executeSql(tag,[], function (tx,result) {}, errorCB);
		}, errorCB);
		savetofile (tag);
	});

	$( "#listofbeds" ).sortable({
		start: function(event, ui) {
			start = ui.item.prevAll().length + 1;
		},
        update: function(event, ui) {
			//console.log(start + " -> " + (ui.item.prevAll().length + 1));
		}
	});

	$( "#listofbeds" ).disableSelection();

	$( "#listofbeds" ).bind( "sortstop", function(event, ui) {
		$('#listofbeds').listview('refresh');
		sessionStorage.startmove = start;
		sessionStorage.endmove = ui.item.prevAll().length + 1;
		var previousposition = $(ui.item).text().split(" ");
		sessionStorage.elementmoved = previousposition[1];
		db.transaction(sortbedsDB, errorCB);
		//console.log(start + " -> " + (ui.item.prevAll().length + 1));
	});

	$("#buttonadd").on('click', function() {
		$.mobile.changePage($("#addbed"));
	});

	$( "#popupPhoto" ).on({
		popupbeforeposition: function() {
			var maxHeight = $( window ).height() - 60 + "px";
			$( "#popupPhoto img" ).css( "max-height", maxHeight );
		}
	});

	$("#listofbeds").on('click', 'li', function() {
		var selli = $(this).find('a');
		sessionStorage.selectedbed=selli.attr('id');
		$.mobile.changePage($("#addbed"));
	});

});

// ===================================================

// save profile button
function butsaveprofile () {
	if ($('#inputname').val() != '') {
		db.transaction( function(tx){ tx.executeSql( 'SELECT name FROM profiles', [], logtitlevalidation) }, errorCB );
	}
}

// log title validation
function logtitlevalidation (tx, result) {
	var flag = 0;
	for (var i=0; i<result.rows.length; i++) {
		if (result.rows.item(i).name == $('#inputname').val()) {flag = 1; break; }
	}
	if ( (flag == 1) && (sessionStorage.selectedprofile == 0) ) {
		$('#popupsave').html('<p>Log ' + $('#inputname').val() + ' already exists.</p>');
		$('#popupsave').popup("open")
		setTimeout(function() {
			$('#popupsave').popup("close");
		}, 3000);
	}
	else {
		db.transaction(addprofileDB, errorCB);
	}
}


// delete profile button
function deleteprofile () {
	navigator.notification.confirm(
	'Are you sure that you want to delete this log?',  // message
	function (buttonIndex) {
		if (buttonIndex == 1) {
			db.transaction(deleteprofileDB, errorCB);
		}
	},
	'Delete profile',            // title
	'Yes,No'          // buttonLabels
	);
}

//save log
function addprofileDB(tx){


	if (sessionStorage.selectedprofile == 0) { geolocation(); }
	var photopath = '';

	if (sessionStorage.photopath) {
		photopath = sessionStorage.photopath;
	}

	var logdirection = "off";
	if ($('#direction').val() == 'on' ) {
		logdirection = "on";
	}

	var tag = '';
	if (sessionStorage.selectedprofile == 0) {
		tag = 'INSERT INTO profiles (name, description, direction, latitude, longitude, altitude, accuracy, altitudeAccuracy, photo) VALUES ("'+$('#inputname').val()+'", "'+$('#inputdescription').val()+'", "'+logdirection+'", "'+window.localStorage.getItem("latitude")+'", "'+window.localStorage.getItem("longitude")+'", "'+window.localStorage.getItem("altitude")+'", "'+window.localStorage.getItem("accuracy")+'", "'+window.localStorage.getItem("accuracyAltitude")+'", "'+photopath+'")';
	}
	else {
		tag = 'UPDATE profiles SET name="'+$('#inputname').val()+'", description="'+$('#inputdescription').val()+'", direction="'+logdirection+'", latitude="'+window.localStorage.getItem("latitude")+'", longitude="'+window.localStorage.getItem("longitude")+'", altitude="'+window.localStorage.getItem("altitude")+'", accuracy="'+window.localStorage.getItem("accuracy")+'", altitudeAccuracy="'+window.localStorage.getItem("accuracyAltitude")+'", photo="'+photopath+'" WHERE id='+sessionStorage.selectedprofile;
	}

	tx.executeSql(tag,[], function (tx,result) {}, errorCB);
	savetofile (tag);

	homerefresh();
	sessionStorage.selectedprofile=0;
}

// delete profile from database
function deleteprofileDB(tx) {
	var tag = 'DELETE FROM beds WHERE profileid='+sessionStorage.selectedprofile;
	tx.executeSql(tag,[], function (tx,result) {}, errorCB);
	savetofile (tag);
	tag = 'DELETE FROM bedphotos WHERE profileid='+sessionStorage.selectedprofile;
	tx.executeSql(tag,[], function (tx,result) {}, errorCB);
	savetofile (tag);
	tag = 'DELETE FROM profiles WHERE id='+sessionStorage.selectedprofile;
	savetofile (tag);
	tx.executeSql(tag,[], function (tx,result) {
		homerefresh();
		sessionStorage.selectedprofile=0;
	}, errorCB);
}

// delete bed from database
function deletebedDB(tx) {
	var tag = 'DELETE FROM beds WHERE id='+sessionStorage.selectedbed;
	savetofile (tag);
	tx.executeSql(tag,[], function (tx,result) {

	tag = 'UPDATE beds SET position=( CASE WHEN position > '+ parseInt(sessionStorage.selectedbedposition) + ' THEN position-1 ELSE position END) WHERE profileid=' + sessionStorage.selectedprofile;
	savetofile (tag);
	tx.executeSql(tag,[], function (tx,result) {}, errorCB);
		sessionStorage.selectedbed=0;
		$.mobile.changePage($("#addprofile"));
	}, errorCB);
	tag = 'DELETE FROM bedphotos WHERE bedid='+sessionStorage.selectedbed;
	tx.executeSql(tag,[], function (tx,result) {}, errorCB);
	savetofile (tag);
}

// get geolocation data
function geolocation (){
	window.localStorage.setItem("latitude", "No data");
	window.localStorage.setItem("longitude", "No data");
	window.localStorage.setItem("altitude", "No data");
	window.localStorage.setItem("accuracy", "No data");
	window.localStorage.setItem("altitudeAccuracy", "No data");

	navigator.geolocation.getCurrentPosition(function (position) {
		window.localStorage.setItem("latitude", position.coords.latitude);
		window.localStorage.setItem("longitude", position.coords.longitude);
		window.localStorage.setItem("altitude", position.coords.altitude);
		window.localStorage.setItem("accuracy", position.coords.accuracy);
		window.localStorage.setItem("altitudeAccuracy", position.coords.altitudeAccuracy);
	}, function(){});
}

// capture an image; an error
function captureError(error) {
	var msg = 'An error occurred during capture: ' + error.code;
	navigator.notification.alert(msg, null, 'Camera error');
}

function captureSuccess(mediaFiles) {
	var namereplaced = $('#inputname').val();
	namereplaced.replace(/[^A-Za-z]+/g, '');
	window.requestFileSystem(LocalFileSystem.PERSISTENT, 0, function (fileSystem) {
		var entry=fileSystem.root; 
		entry.getDirectory("SedMob", {create: true, exclusive: false}, function (dir) {
			window.resolveLocalFileSystemURI(mediaFiles[0].fullPath, function(file) {
				file.moveTo(dir,namereplaced+'.jpg');
				processphoto ();
			}, function (err) { } );
		}, function (error){
			//console.log("Error opening directory "+error.code); 
		}); 
	}, null);
}

// process a photo in new location
function processphoto () {
	var namereplaced = $('#inputname').val();
	namereplaced.replace(/[^A-Za-z]+/g, '');
	// get uri of photo in new location
	window.requestFileSystem(LocalFileSystem.PERSISTENT, 0, function(fileSystem) {
		// the place where the file will be written
		fileSystem.root.getFile('SedMob/'+namereplaced+'.jpg', {create: false, exclusive: false}, function(fileEntry) {

			var uri = fileEntry.toURL();
			var d = new Date();
			$("#photoshow").attr('src', uri+'?'+d.getTime());
			sessionStorage.photopath=uri;
		}, function (err) { } );
	}, filewritefail);

	// show a confirmation
	$('#popupphoto').popup("open")
		setTimeout(function() {
		$('#popupphoto').popup("close");
		}, 2500);
}

// take a photo; wrapper
function takephoto() {
	navigator.device.capture.captureImage(captureSuccess, captureError);
}
    
// update bed order
function sortbedsDB(tx) {
	var updatesql = '';

	if (parseInt(sessionStorage.endmove) < parseInt(sessionStorage.startmove)) {
		var updatesql = 'UPDATE beds SET position=( CASE WHEN position+1 > '+ parseInt(sessionStorage.startmove) + ' THEN ' + parseInt(sessionStorage.endmove) + ' ELSE position+1 END) WHERE profileid=' + sessionStorage.selectedprofile + ' AND position BETWEEN ' + parseInt(sessionStorage.endmove) + ' AND ' + parseInt(sessionStorage.startmove);
	}
	else {
		var updatesql = 'UPDATE beds SET position=( CASE WHEN position-1 < '+ parseInt(sessionStorage.startmove) + ' THEN ' + parseInt(sessionStorage.endmove) + ' ELSE position-1 END) WHERE profileid=' + sessionStorage.selectedprofile + ' AND position BETWEEN ' + parseInt(sessionStorage.startmove) + ' AND ' + parseInt(sessionStorage.endmove);
	}

	tx.executeSql(updatesql,[], function (tx,result) {}, errorCB);
	savetofile (updatesql);
}
