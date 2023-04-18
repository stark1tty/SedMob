$( document ).delegate("#edit", "pageinit", function() {

	loadeditmenu ();

	$('#editsel').change(function() {
		loadeditmenu ();
	});

	$('#editsymbol').change(function() {
		fillinputs ();
	});

});

// add lithology, symbol or group of lithologies or symbols
function butaddsymbol () {
	var addparameters = [];

	switch ($('#editsel').val()) {
		case 'ed_litgroups':
			addparameters[0] = 'INSERT INTO typelithology (name) VALUES ("'+$('#newsymbol').val()+'")';
			addparameters[1] = 'Lithology group';
			break;

		case 'ed_lithologies':
			addparameters[0] = 'INSERT INTO indexlithology (typeid, name) VALUES ('+$('#addtogroup').val()+', "'+$('#newsymbol').val()+'")';
			addparameters[1] = 'Lithology';
			break;

		case 'ed_symgroups':
			addparameters[0] = 'INSERT INTO typestructure (name) VALUES ("'+$('#newsymbol').val()+'")';
			addparameters[1] = 'Symbol group';
			break;

		case 'ed_symbols':
			addparameters[0] = 'INSERT INTO indexstructure (typeid, name) VALUES ('+$('#addtogroup').val()+', "'+$('#newsymbol').val()+'")';
			addparameters[1] = 'Symbol';
			break;
	} // end switch

	addsymbolDB (addparameters);
}

// add lithology or symbol to the database
function addsymbolDB (addparameters) {
	var onlyletters = /^[a-zA-Z0-9 ]*$/.test($('#newsymbol').val());
	if ( ($('#newsymbol').val() != '') && (onlyletters == true) ) {
		db.transaction( function(tx){

			tx.executeSql(addparameters[0],[], function (tx,result) {}, errorCB);

			var if_exists = 0;
			$('#editsymbol option').each(function(){
				var newsymbol_splitted = $(this).text().split(" > ");
   				if (newsymbol_splitted[newsymbol_splitted.length-1] == $('#newsymbol').val()) {
       				if_exists = 1;
       				return false;
   				}
			});

			if (!if_exists) {
				savetofile (addparameters[0]);
				$('#popupadd').html('<p>'+addparameters[1]+' "'+$('#newsymbol').val()+'" added.</p>');
			}
			else {
				$('#popupadd').html('<p>'+addparameters[1]+' "'+$('#newsymbol').val()+'" already exists. Choose different name.</p>');
			} // end if
			$('#popupadd').popup("open")
			setTimeout(function() {
				$('#popupadd').popup("close");
			}, 3500);

			$('#newsymbol').val('');
			loadeditmenu ();
		}, errorCB );
	}
	else if ( ($('#newsymbol').val() != '') && (onlyletters == false) ) {
		$('#popupadd').html('<p>Element name should contain only characters, digits and whitespaces.</p>');
		$('#popupadd').popup("open")
		setTimeout(function() {
			$('#popupadd').popup("close");
		}, 3500);
	}
}

// delete lithology, symbol or group of lithologies or symbols
function butdelsymbol () {
	var deleteparameters = [];

	switch ($('#editsel').val()) {
		case 'ed_litgroups':
			deleteparameters[0] = 'Are you sure that you want to delete this lithology group?';
			deleteparameters[1] = 'There are lithologies saved under this lithology group. Are you sure that you want to delete them all?';
			deleteparameters[2] = 1; // check if there are lithologies or symbols saved under a group that will be deleted
			deleteparameters[3] = 'DELETE FROM typelithology WHERE id='+$('#editsymbol').val(); // delete element
			deleteparameters[4] = 'DELETE FROM indexlithology WHERE typeid='+$('#editsymbol').val(); // delete elements that are saved under this group
			deleteparameters[5] = 'Lithology group';
			deleteparameters[6] = 'SELECT * FROM indexlithology WHERE typeid='+$('#editsymbol').val(); // SQL statement to check if there are lithologies or symbols saved under a group that will be deleted
			break;

		case 'ed_lithologies':
			deleteparameters[0] = 'Are you sure that you want to delete this lithology?';
			deleteparameters[1] = '';
			deleteparameters[2] = 0; // check if there are lithologies or symbols saved under a group that will be deleted
			deleteparameters[3] = 'DELETE FROM indexlithology WHERE id='+$('#editsymbol').val(); // delete element
			deleteparameters[4] = ''; // delete elements that are saved under this group
			deleteparameters[5] = 'Lithology';
			deleteparameters[6] = ''; // SQL statement to check if there are lithologies or symbols saved under a group that will be deleted
			break;

		case 'ed_symgroups':
			deleteparameters[0] = 'Are you sure that you want to delete this symbol group?';
			deleteparameters[1] = 'There are symbols saved under this symbol group. Are you sure that you want to delete them all?';
			deleteparameters[2] = 1; // check if there are lithologies or symbols saved under a group that will be deleted
			deleteparameters[3] = 'DELETE FROM typestructure WHERE id='+$('#editsymbol').val(); // delete element
			deleteparameters[4] = 'DELETE FROM indexstructure WHERE typeid='+$('#editsymbol').val(); // delete elements that are saved under this group
			deleteparameters[5] = 'Symbol group';
			deleteparameters[6] = 'SELECT * FROM indexstructure WHERE typeid='+$('#editsymbol').val(); // SQL statement to check if there are lithologies or symbols saved under a group that will be deleted
			break;

		case 'ed_symbols':
			deleteparameters[0] = 'Are you sure that you want to delete this symbol?';
			deleteparameters[1] = '';
			deleteparameters[2] = 0; // check if there are lithologies or symbols saved under a group that will be deleted
			deleteparameters[3] = 'DELETE FROM indexstructure WHERE id='+$('#editsymbol').val(); // delete element
			deleteparameters[4] = ''; // delete elements that are saved under this group
			deleteparameters[5] = 'Symbol';
			deleteparameters[6] = ''; // SQL statement to check if there are lithologies or symbols saved under a group that will be deleted
			break;
	} // end switch

	deletesymbolDB (deleteparameters);
}

// delete lithology or symbol from the database
function deletesymbolDB (deleteparameters) {
	var message = deleteparameters[0];
	var ifsymbols = 0;
	if (deleteparameters[2]) {
		db.transaction( function(tx){
			tx.executeSql(deleteparameters[6],[], function (tx,result) {
				savetofile (deleteparameters[6]);
				if (result.rows.length > 0) {
					ifsymbols = 1;
					message = deleteparameters[1];
				}
			}, errorCB);
		}, errorCB );
	} // end if

	navigator.notification.confirm(
	message,  // message
	function (buttonIndex) {
		if (buttonIndex == 1) {
			db.transaction( function(tx){
				tx.executeSql(deleteparameters[3]);
				savetofile (deleteparameters[3]);
				if (ifsymbols) {
					tx.executeSql(deleteparameters[4]);
					savetofile (deleteparameters[4]);
				}
				loadeditmenu ();
				$('#popupdelete').html('<p>'+deleteparameters[5]+' "'+$('#editsymbol option:selected').text()+'" deleted.</p>');
				$('#popupdelete').popup("open")
				setTimeout(function() {
					$('#popupdelete').popup("close");
				}, 2500);
			}, errorCB );
		}
	},
	'Delete '+deleteparameters[5],            // title
	'Yes,No'          // buttonLabels
	);
}

// edit and save lithology, symbol or group of lithologies or symbols
function butsavesymbol () {
	var editparameters = [];

	switch ($('#editsel').val()) {
		case 'ed_litgroups':
			editparameters[0] = 'typelithology';
			editparameters[1] = 'Lithology group';
			break;

		case 'ed_lithologies':
			editparameters[0] = 'indexlithology';
			editparameters[1] = 'Lithology';
			break;

		case 'ed_symgroups':
			editparameters[0] = 'typestructure';
			editparameters[1] = 'Symbol group';
			break;

		case 'ed_symbols':
			editparameters[0] = 'indexstructure';
			editparameters[1] = 'Symbol';
			break;
	} // end switch

	db.transaction( function(tx){ editsymbolDB (tx,editparameters)}, errorCB);
}

// edit lithology or symbol from the database
function editsymbolDB (tx,editparameters) {
	var elementsplitted = $('#editsymbol option:selected').text().split(" > ");

	if ( ($('#existingsymbol').val() != elementsplitted[elementsplitted.length-1]) && ($('#existingsymbol').val() != '') ) {
		var tag = 'UPDATE '+editparameters[0]+' SET name="'+$('#existingsymbol').val()+'" WHERE id='+$('#editsymbol option:selected').val();
		tx.executeSql(tag,[], function (tx,result) { }, errorCB );

		var if_exists = 0;
		$('#editsymbol option').each(function(){
			var newsymbol_splitted = $(this).text().split(" > ");
			if (newsymbol_splitted[newsymbol_splitted.length-1] == $('#existingsymbol').val()) {
				if_exists = 1;
				return false;
			}
		});

		savetofile (tag);
		$('#popupadd').html('<p>'+editparameters[1]+' "'+$('#existingsymbol').val()+'" edited.</p>');
		$('#popupadd').popup("open")
		setTimeout(function() {
			$('#popupadd').popup("close");
		}, 3500);

		$('#existingsymbol').val('');
		loadeditmenu ();
	}
}

function fillinputs () {
	var elementsplitted = $('#editsymbol option:selected').text().split(" > ");
	$('#existingsymbol').val(elementsplitted[elementsplitted.length-1]);
}

// populate editing menus
function loadeditmenu () {
	switch ($('#editsel').val()) {
		case 'ed_litgroups':
			$('#collapseaddnew .ui-collapsible-heading .ui-btn-text').text('Add new lithology group');
			$('#collapseeditexisting .ui-collapsible-heading .ui-btn-text').text('Edit existing lithology group');
			db.transaction( function(tx){ loadeditdataDB(tx, 'typelithology', 0) }, errorCB );
			break;

		case 'ed_lithologies':
			$('#collapseaddnew .ui-collapsible-heading .ui-btn-text').text('Add new lithology');
			$('#collapseeditexisting .ui-collapsible-heading .ui-btn-text').text('Edit existing lithology');
			db.transaction( function(tx){ loadeditdataDB(tx, 'indexlithology', 'typelithology') }, errorCB );
			break;

		case 'ed_symgroups':
			$('#collapseaddnew .ui-collapsible-heading .ui-btn-text').text('Add new symbol group');
			$('#collapseeditexisting .ui-collapsible-heading .ui-btn-text').text('Edit existing symbol group');
			db.transaction( function(tx){ loadeditdataDB(tx, 'typestructure', 0) }, errorCB );
			break;

		case 'ed_symbols':
			$('#collapseaddnew .ui-collapsible-heading .ui-btn-text').text('Add new symbol');
			$('#collapseeditexisting .ui-collapsible-heading .ui-btn-text').text('Edit existing symbol');
			db.transaction( function(tx){ loadeditdataDB(tx, 'indexstructure', 'typestructure') }, errorCB );
			break;
	} // end switch
}

// load edit data from database
function loadeditdataDB(tx, databasetable, nested) {
	if (nested) {
		var statement = 'SELECT '+databasetable+'.id AS id, '+databasetable+'.name AS name, '+nested+'.id AS typeid, '+nested+'.name AS typename FROM '+databasetable+' INNER JOIN '+nested+' ON '+nested+'.id='+databasetable+'.typeid';
	}
	else {
		var statement = 'SELECT * FROM '+databasetable;
	}

	tx.executeSql(statement,[], function (tx,result) {
		var len = result.rows.length;
		$('#editsymbol').empty();
		$('#editsymbol').html('').selectmenu('refresh');
		if (nested) {
			$(".hide").show("slow");
			$('#addtogroup').empty();
			$('#addtogroup').selectmenu("refresh",true);
		}
		else {
			$(".hide").hide("slow");
		}

		for (var i=0; i<len; i++) {
			if (nested) {
				$('#editsymbol').append('<option value="'+result.rows.item(i).id+'">'+result.rows.item(i).typename+' &gt; '+result.rows.item(i).name+'</option>').selectmenu('refresh');
			}
			else {
				$('#editsymbol').append('<option value="'+result.rows.item(i).id+'">'+result.rows.item(i).name+'</option>').selectmenu('refresh');
			}
		} // end for

		if (nested) {
			tx.executeSql('SELECT * FROM '+nested,[], function (tx,result) {
				for (var j=0; j<result.rows.length; j++) {
					$('#addtogroup').append('<option value="'+result.rows.item(j).id+'">'+result.rows.item(j).name+'</option>').selectmenu('refresh');
				} // end for
			}, errorCB);
		} // end if
		fillinputs ();
	}, errorCB);
}
