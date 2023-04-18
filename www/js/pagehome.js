$( document ).delegate("#pagehome", "pageinit", function() {

	$("#buttonnew").on('click', function() {

		sessionStorage.selectedprofile=0;
		$('#inputname').val('');
		$('#inputdescription').val('');
		$('#direction').val('off').trigger("refresh");
		$("#photoshow").attr('src', '');
		$('#listofbeds').empty();
		if (sessionStorage.photopath) {
			sessionStorage.removeItem(photopath);
		}
		$.mobile.changePage($("#addprofile"));

		geolocation();
		$('#labelgeo').html('Latitude: '+ window.localStorage.getItem("latitude")+' Longitude: '+ window.localStorage.getItem("longitude")+' Altitude: '+ window.localStorage.getItem("altitude"));
	});

	$("#listofprofiles").on('click', 'li', function() {
		var selli = $(this).find('a');
		sessionStorage.selectedprofile=selli.attr('id');
		$.mobile.changePage($("#addprofile"));
	});
});

// refreshes homepage by loading the profiles
function homerefresh () {

	db.transaction(function (tx) {
		tx.executeSql('SELECT * FROM profiles',[],showProfiles,errorCB);
	}, errorCB);
	$.mobile.changePage($("#pagehome"));
}

// shows a list of profiles on the homepage
function showProfiles(tx,result){
	$('#listofprofiles').empty();
	var len = result.rows.length;
	for (var i=0; i<len; i++) {
		$('#listofprofiles').append('<li><a id="'+result.rows.item(i).id+'" href="#"><h2>'+result.rows.item(i).name+'</h2><p>'+result.rows.item(i).description+'</p></a></li>');
	}
	$('#listofprofiles').listview('refresh');
}

// load profiles from database
function loadprofileDB(){
	db.transaction(function (tx) {
		tx.executeSql('SELECT * FROM profiles WHERE id='+sessionStorage.selectedprofile,[], function (tx,result) {
		$('#inputname').val(result.rows.item(0).name);
		$('#inputdescription').val(result.rows.item(0).description);

		if (result.rows.item(0).direction == "on") {
			$('#direction').val('on').trigger('refresh');
		}
		else {
			$('#direction').val('off').trigger('refresh');
		}

		if (result.rows.item(0).photo != '') {
			var d = new Date();
			$("#photoshow").attr('src', result.rows.item(0).photo+'?'+d.getTime());
			$(".hidden").show("slow");
		}
		else {
			$("#photoshow").attr('src', '');
			$(".hidden").hide("slow");
		}
		window.localStorage.setItem("latitude", result.rows.item(0).latitude);
		window.localStorage.setItem("longitude", result.rows.item(0).longitude);
		window.localStorage.setItem("altitude", result.rows.item(0).altitude);
		window.localStorage.setItem("accuracy", result.rows.item(0).accuracy);
		window.localStorage.setItem("altitudeAccuracy", result.rows.item(0).altitudeAccuracy);

		$('#labelgeo').html('Latitude: '+ result.rows.item(0).latitude+' Longitude: '+ result.rows.item(0).longitude+' Altitude: '+ result.rows.item(0).altitude);
	}, errorCB);

	sessionStorage.numberofbeds = 0;
	tx.executeSql('SELECT * FROM beds WHERE profileid="'+sessionStorage.selectedprofile+'" ORDER BY position ASC',[], function (tx,result) {
		$('#listofbeds').empty();
		var len = result.rows.length;
		sessionStorage.numberofbeds = len;
		for (var i=0; i<len; i++) {
//			$('#listofbeds').append('<li><a id="'+result.rows.item(i).id+'" href="#">Bed #'+(i+1)+' '+result.rows.item(i).name+' Id: '+result.rows.item(i).id+' Position: '+result.rows.item(i).position+'</a></li>');
						$('#listofbeds').append('<li><a id="'+result.rows.item(i).id+'" href="#">Bed #'+(i+1)+' '+result.rows.item(i).name+'</a></li>');
		}

		$('#listofbeds').listview('refresh');
		}, errorCB);
	}, errorCB); // end of db.transaction
}
    