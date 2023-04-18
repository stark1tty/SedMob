$( document ).delegate("#settings", "pageshow", function() {
	var dbdata = window.localStorage.getItem("sedmob-dbdata");
	if (dbdata) {
		var dbconfig = JSON.parse(dbdata);

		$('#phpfile').val(dbconfig.phpfile);
		$('#sqlserver').val(dbconfig.sqlserver);
		$('#sqldatabase').val(dbconfig.sqldatabase);
		$('#sqluser').val(dbconfig.sqluser);
		$('#sqlpass').val(dbconfig.sqlpass);
		$('#sqlport').val(dbconfig.sqlport);
	}

	$('#enhancecontrast').change(function(event) {
		var contrastswitch = $(this);
		var enhance = contrastswitch[0].selectedIndex == 1 ? true:false;
		if (enhance) {
			window.localStorage.setItem("sedmob-theme", "a");
		}
		else {
			window.localStorage.setItem("sedmob-theme", "b");
		}
		theme_refresh ();
	});
});


//change theme
function theme_refresh () {
	//set your new theme letter
	var theme = window.localStorage.getItem("sedmob-theme");

	//reset all the buttons widgets
	$.mobile.activePage.find('.ui-btn')
		.removeClass('ui-btn-up-a ui-btn-up-b ui-btn-up-c ui-btn-up-d ui-btn-up-e ui-btn-hover-a ui-btn-hover-b ui-btn-hover-c ui-btn-hover-d ui-btn-hover-e')
		.addClass('ui-btn-up-' + theme)
		.attr('data-theme', theme);

	//reset the header/footer widgets
	$.mobile.activePage.find('.ui-header, .ui-footer')
		.removeClass('ui-bar-a ui-bar-b ui-bar-c ui-bar-d ui-bar-e')
		.addClass('ui-bar-' + theme)
		.attr('data-theme', theme);

	// formatting the listviews

	$.mobile.activePage.find('.ui-li')
		.removeAttr('data-theme')
        .removeAttr('data-content-theme')
		.removeClass('ui-btn-up-a ui-btn-up-b ui-btn-up-c ui-btn-up-d ui-btn-up-e')
		.addClass('ui-btn-up-d')
		.attr('data-theme', 'b')
		.attr('data-content-theme', 'd');

	//reset the page widget
	$.mobile.activePage.removeClass('ui-body-a ui-body-b ui-body-c ui-body-d ui-body-e')
		.addClass('ui-body-' + theme)
		.attr('data-theme', theme);
}

$(document).on('pagebeforeshow', '[data-role="page"]', function(){
	theme_refresh ();
});

// ==============================================================
// synchronization
function synchronizeDB () {
	if ( ($('#phpfile').val() != '') && ($('#sqlserver').val() != '') && ($('#sqldatabase').val() != '') && ($('#sqluser').val() != '') && ($('#sqlpass').val() != '') && ($('#sqlport').val() != '') ) {
		var dbconfig = { "phpfile": $('#phpfile').val(), "sqlserver": $('#sqlserver').val(), "sqldatabase": $('#sqldatabase').val(), "sqluser": $('#sqluser').val(), "sqlpass": $('#sqlpass').val(), "sqlport": $('#sqlport').val() }; 
		window.localStorage.setItem("sedmob-dbdata", JSON.stringify(dbconfig));
		var storagesynchronize = window.localStorage.getItem("sedmob-synchronize");
		if (storagesynchronize != 'true') {
			backupdbContent(1);
		}
		synchronizedb ();
	} // end if values
	else {
		navigator.notification.alert(
		'The database configuration details should be entered.',
		function (){},         // callback
		'Database configuration ',            // title
		'OK'                  // buttonName
		);
	} // end else
}

// remove file containing sql commands to synchronize
function removefile(){
	window.requestFileSystem(LocalFileSystem.PERSISTENT, 0, function(fileSystem) {
		fileSystem.root.getFile("SedMob/synchronize.txt", null, function (fileEntry){
			fileEntry.remove(function (entry){}, function (error){});
		}, function (error){});
	});
}

// sends sql commands to mysql server
function synchronizedb (datafile) {
	window.requestFileSystem(LocalFileSystem.PERSISTENT, 0, function(fileSystem) {
		// The place where your backup is placed
		fileSystem.root.getFile("SedMob/synchronize.txt", null, function(fileEntry) {
			fileEntry.file(function(file) {
				var reader = new FileReader();
				reader.onloadend = function(evt) {
					var datasent = { sqlserver: $('#sqlserver').val(), sqldatabase: $('#sqldatabase').val(), sqluser: $('#sqluser').val(), sqlpass: $('#sqlpass').val(), sqlport: $('#sqlport').val(), sqldata: evt.target.result };
					$.post($('#phpfile').val(), datasent, function(data) {
						if (data == 'Data synchronized successfully.') {
							window.localStorage.setItem("sedmob-synchronize", "true");
							removefile();
						}
						navigator.notification.alert(
						data,
						function (){},         // callback
						'Synchronize',            // title
						'OK'                  // buttonName
						);
					}); // end $.post
				};
				reader.readAsText(file);
			}, filewritefail);
		}, function (err) {
			navigator.notification.alert(
			'Nothing to synchronize.',
			function (){},         // callback
			'Synchronize',            // title
			'OK'                  // buttonName
			);
		});
	}, filewritefail);
}

// ==============================================

// create sql code for backup
function gettablecontents (tx, result) {
	var tag = '';
	var tableindex=["profiles","beds","typelithology","indexlithology","typestructure","indexstructure","grainclastic","graincarbonate","bioturbation","boundaries"];

	if (result.rows.length > 0) {
		tablename = tableindex[result.rows.item(0).number];
		for (var i=0; i < result.rows.length; i++) {
			var row = result.rows.item(i);
			var tag_temp1 = '';
			var tag_temp2 = '';
			var j=0;
			for (property in row) {
				if (property != 'number') {
					tag_temp1 += property;
					if ( (property == 'id') || (property == 'profileid') || (property == 'position') || (property == 'typeid') ) {
						tag_temp2 += row[property];
					}
					else {
						tag_temp2 += '"'+row[property]+'"';
					}
					if ( j < ( Object.size(result.rows.item(i))-2) ) {
						tag_temp1 += ', ';
						tag_temp2+=', ';
					}
				}
				j++;
			} // end for property
			var tag_temp = 'INSERT INTO '+tablename+' ('+tag_temp1+') VALUES ('+tag_temp2+");\n";
			tag += tag_temp;
		} // end for
	} // end if
	return tag;
}

// backup content of the database
function backupdbContent(ifsynchronize) {
	var tag = '';
	var dbtables=["profiles","beds","bedphotos","typelithology","indexlithology","typestructure","indexstructure","grainclastic","graincarbonate","bioturbation","boundaries"];
sessionStorage.ifsynchronize = ifsynchronize;

	tag += "DROP TABLE IF EXISTS profiles;\n";
	tag += "DROP TABLE IF EXISTS beds;\n";
	tag += "DROP TABLE IF EXISTS typelithology;\n";
	tag += "DROP TABLE IF EXISTS indexlithology;\n";
	tag += "DROP TABLE IF EXISTS typestructure;\n";
	tag += "DROP TABLE IF EXISTS indexstructure;\n";
	tag += "DROP TABLE IF EXISTS grainclastic;\n";
	tag += "DROP TABLE IF EXISTS graincarbonate;\n";
	tag += "DROP TABLE IF EXISTS bioturbation;\n";
	tag += "DROP TABLE IF EXISTS boundaries;\n";

	if (ifsynchronize == 1) {
		tag += "CREATE TABLE IF NOT EXISTS profiles (id INT PRIMARY KEY AUTO_INCREMENT, name VARCHAR(255), description TEXT, direction VARCHAR(10), latitude VARCHAR(255), longitude VARCHAR(255), altitude VARCHAR(255), accuracy VARCHAR(255), altitudeAccuracy VARCHAR(255), photo VARCHAR(255));\n";
		tag += "CREATE TABLE IF NOT EXISTS beds (id INT PRIMARY KEY AUTO_INCREMENT, profileid INT, position INT, name VARCHAR(255), thickness VARCHAR(10), facies VARCHAR(10), notes TEXT, boundary VARCHAR(30), paleocurrent VARCHAR(30), lit1group VARCHAR(30), lit1type VARCHAR(30), lit1percentage VARCHAR(10), lit2group VARCHAR(30), lit2type VARCHAR(30), lit2percentage VARCHAR(10), lit3group VARCHAR(30), lit3type VARCHAR(30), lit3percentage VARCHAR(10), sizeclasticbase VARCHAR(30), phiclasticbase VARCHAR(10), sizeclastictop VARCHAR(30), phiclastictop VARCHAR(10), sizecarbobase VARCHAR(30), phicarbobase VARCHAR(10), sizecarbotop VARCHAR(30), phicarbotop VARCHAR(10), bioturbationtype VARCHAR(30), bioturbationintensity VARCHAR(30), structures VARCHAR(30), bedsymbols VARCHAR(30), audio VARCHAR(255));\n";
		tag += "CREATE TABLE IF NOT EXISTS bedphotos (id INT PRIMARY KEY AUTO_INCREMENT, profileid INT, bedid INT, photo VARCHAR(255), description TEXT);\n";
		tag += "CREATE TABLE IF NOT EXISTS typelithology (id INT PRIMARY KEY AUTO_INCREMENT, name VARCHAR(255));\n";
		tag += "CREATE TABLE IF NOT EXISTS indexlithology (id INT PRIMARY KEY AUTO_INCREMENT, typeid INT, name VARCHAR(255));\n";
		tag += "CREATE TABLE IF NOT EXISTS typestructure (id INT PRIMARY KEY AUTO_INCREMENT, name VARCHAR(255));\n";
		tag += "CREATE TABLE IF NOT EXISTS indexstructure (id INT PRIMARY KEY AUTO_INCREMENT, typeid INT, name VARCHAR(255));\n";
		tag += "CREATE TABLE IF NOT EXISTS grainclastic (name VARCHAR(30), phi VARCHAR(10));\n";
		tag += "CREATE TABLE IF NOT EXISTS graincarbonate (name VARCHAR(30), phi VARCHAR(10));\n";
		tag += "CREATE TABLE IF NOT EXISTS bioturbation (name VARCHAR(30));\n";
		tag += "CREATE TABLE IF NOT EXISTS boundaries (name VARCHAR(30));\n";
	}
	else {
		tag += "CREATE TABLE IF NOT EXISTS profiles (id INTEGER PRIMARY KEY, name, description, direction, latitude, longitude, altitude, accuracy, altitudeAccuracy, photo);\n";
		tag += "CREATE TABLE IF NOT EXISTS beds (id INTEGER PRIMARY KEY, profileid INTEGER, position INTEGER, name, thickness, facies, notes, boundary, paleocurrent, lit1group, lit1type, lit1percentage, lit2group, lit2type, lit2percentage, lit3group, lit3type, lit3percentage, sizeclasticbase, phiclasticbase, sizeclastictop, phiclastictop, sizecarbobase, phicarbobase, sizecarbotop, phicarbotop, bioturbationtype, bioturbationintensity, structures, bedsymbols, audio);\n";
		tag += "CREATE TABLE IF NOT EXISTS bedphotos (id INTEGER PRIMARY KEY, profileid INTEGER, bedid INTEGER, photo, description);\n";
		tag += "CREATE TABLE IF NOT EXISTS typelithology (id INTEGER PRIMARY KEY, name UNIQUE ON CONFLICT IGNORE);\n";
		tag += "CREATE TABLE IF NOT EXISTS indexlithology (id INTEGER PRIMARY KEY, typeid INTEGER, name UNIQUE ON CONFLICT IGNORE);\n";
		tag += "CREATE TABLE IF NOT EXISTS typestructure (id INTEGER PRIMARY KEY, name UNIQUE ON CONFLICT IGNORE);\n";
		tag += "CREATE TABLE IF NOT EXISTS indexstructure (id INTEGER PRIMARY KEY, typeid INTEGER, name UNIQUE ON CONFLICT IGNORE);\n";
		tag += "CREATE TABLE IF NOT EXISTS grainclastic (name, phi);\n";
		tag += "CREATE TABLE IF NOT EXISTS graincarbonate (name, phi);\n";
		tag += "CREATE TABLE IF NOT EXISTS bioturbation (name);\n";
		tag += "CREATE TABLE IF NOT EXISTS boundaries (name);\n";
	}

	sessionStorage.tableindex = 0;
	window.localStorage.setItem("backup", tag);

	db.transaction( function(tx){
		for (var x=0; x<dbtables.length; x++) {
			var statement = 'SELECT *,'+x+' AS number FROM '+dbtables[x];
			tx.executeSql( statement, [], function (tx, result) {
				var oldtag = window.localStorage.getItem("backup");
				var temptag = gettablecontents (tx, result);
				window.localStorage.setItem("backup", oldtag+temptag);
				sessionStorage.tableindex = parseInt(sessionStorage.tableindex)+1;
				if (parseInt(sessionStorage.tableindex) == 9) {
					savesqltofile ();
				}
			});
		} // end for x
	});
}

// save sql queries to a file
function savesqltofile () {
	// create directory
	createdirectory ();

	// write file
	var datafile = '';
	if (sessionStorage.ifsynchronize == 1) {
		datafile = "SedMob/synchronize.txt";
	}
	else {
		datafile = "SedMob/backup.txt";
	}

	window.requestFileSystem(LocalFileSystem.PERSISTENT, 0, function(fileSystem) {
		// the place where the contents of the database will be written
		fileSystem.root.getFile(datafile, {create: true, exclusive: false}, function(fileEntry) {
			fileEntry.createWriter(function(writer) {
				writer.write(window.localStorage.getItem("backup"));
				if (sessionStorage.ifsynchronize == 0) {
				alert ('tutaj');
					$('#popupbackup').popup("open")
  					setTimeout(function() {
  						$('#popupbackup').popup("close");
  					}, 3000);
				}
			}, filewritefail);
		}, filewritefail);
	}, filewritefail);
	sessionStorage.ifsynchronize = 2;
}

// restore content
function restoreContent() {
	navigator.notification.confirm('Do you want to start the restore? The current contents of your database will be erased!', function (buttonIndex) {
		if (buttonIndex == 1) {
			$('#popuprestore').popup("open");

			window.requestFileSystem(LocalFileSystem.PERSISTENT, 0, function(fileSystem) {
				// The place where your backup is placed
				fileSystem.root.getFile("SedMob/backup.txt", null, function(fileEntry) {
					fileEntry.file(function(file) {
						var reader = new FileReader();
						reader.onloadend = function(evt) {
							var lines = evt.target.result.split("\n");
							var errors = 0;
							for (var i=0; i < lines.length; i++) {
								if(lines[i] != '') {
									db.transaction (function(tx) {
										tx.executeSql(lines[i],[], function (tx,result) {}, function (tx, err) {
											$('#popuprestore').popup("close");
											navigator.notification.alert(
											'Backup file is corrupted and cannot be restored.',
											function (){},         // callback
											'Error',            // title
											'OK'                  // buttonName
											);
											errors=1;
										});
									});
								} // end if lines[i] != ''
								if (errors == 1) break;
							}
							$('#popuprestore').html('<p>Database successfully restored.</p>');

							$('#popuprestore')
							setTimeout(function() {
								$('#popuprestore').popup("close");
								$('#popuprestore').html('<p>Database is being restored.</p>');
							}, 2500);
						};
						reader.readAsText(file);
						// console.log("Restore done.");
					}, filewritefail);
				}, filewritefail);
			}, filewritefail);
		} // end if buttonIndex == 1
	}, 'Restore', 'OK,Cancel'); // end confirmation
}

// restore the database contents (wrapper)
function startexportcsv() {
	navigator.notification.confirm('Do you want to start the restore? The current contents of your database will be erased!', function (buttonIndex) {
		if (buttonIndex == 1) {
			restoreContent();
		}
	}, 'Restore', 'OK,Cancel');
}

// =====================================================================


// export single profile to CSV file
function profiletocsv (tx,result,name) {
	var arrayparam = [];

	for (var i=0; i<result.rows.length; i++) {

		var phibase = result.rows.item(i).phiclasticbase;
		var phitop = result.rows.item(i).phiclastictop;
		var sizebase = result.rows.item(i).sizeclasticbase;
		var sizetop = result.rows.item(i).sizeclastictop;
		if (result.rows.item(i).phiclasticbase == '<none>') {
			phibase = result.rows.item(i).phicarbobase;
		}
		if (result.rows.item(i).phiclastictop == '<none>') {
			phitop = result.rows.item(i).phicarbotop;
		}
		if (result.rows.item(i).sizeclasticbase == '') {
			sizebase = result.rows.item(i).sizecarbobase;
		}
		if (result.rows.item(i).sizeclastictop == '') {
			sizetop = result.rows.item(i).sizecarbotop;
		}

		arrayparam[i] = [result.rows.item(i).thickness,
			result.rows.item(i).boundary,
			result.rows.item(i).lit1type,
			result.rows.item(i).lit1percentage,
			result.rows.item(i).lit2type,
			result.rows.item(i).lit2percentage,
			result.rows.item(i).lit3type,
			result.rows.item(i).lit3percentage,
			sizebase,
			phibase,
			sizetop,
			phitop,
			result.rows.item(i).bedsymbols, // bedsymbols,
			result.rows.item(i).structures, // structures,
			result.rows.item(i).notes,
			result.rows.item(i).bioturbationtype,
			result.rows.item(i).bioturbationintensity,
			result.rows.item(i).paleocurrent,
			result.rows.item(i).facies];

	} // end for i

	tx.executeSql( 'SELECT id, name FROM indexstructure', [], function (tx, res) { getstructname (tx, res, name, arrayparam); });

}

// find names of the structures
function getstructname (tx, res, name, arrayparam) {
	var len = res.rows.length;
	var arraystruct = [];
	for (var j=0; j<len; j++) {
		arraystruct[res.rows.item(j).id] = res.rows.item(j).name;
		if (j+1 == len) {
			replacestructname (tx, res, name, arrayparam, arraystruct);
			}
	}
}

// replace structure ids with names
function replacestructname (tx, res, name, arrayparam, arraystruct) {
	var splitted = '';
	var names = '';
	for (var i=0; i<arrayparam.length; i++) {

		// bedsymbols
		if ( (arrayparam[i][12] !== undefined) && (arrayparam[i][12] != '<none>' ) ) {
			splitted = arrayparam[i][12].split(",");
			names = '';
			for (var j=0; j<splitted.length; j++) {
				if (j>0) { names += ','; }
				names += arraystruct[splitted[j]];
			} // end for j
		}
		arrayparam[i][12] = names;

		// structures
		if ( (arrayparam[i][13] !== undefined) && (arrayparam[i][13] != '<none>' ) ) {
			splitted = arrayparam[i][13].split(",");
			names = '';
			for (var j=0; j<splitted.length; j++) {
				if (j>0) { names += ','; }
				names += arraystruct[splitted[j]];
			} // end for j
		}
		arrayparam[i][13] = names;

	} // end for i

	writetocsv (name, arrayparam);
}

// write CSV file
function writetocsv (name, arrayparam) {
//	var tag = "THICKNESS (CM)        BASE BOUNDARY        LITHOLOGY        LITHOLOGY %        LITHOLOGY2        LITHOLOGY2 %        LITHOLOGY3        LITHOLOGY3 %        GRAIN SIZE BASE        PHI VALUES BASE        GRAIN SIZE TOP        PHI VALUES TOP        SYMBOLS IN BED        SYMBOLS/STRUCTURES        NOTES COLUMN        BIOTURBATION TYPE        INTENSITY        PALAEOCURRENT VALUES        FACIES\n";
//	var tag = "THICKNESS (CM),BASE BOUNDARY,LITHOLOGY,LITHOLOGY %,LITHOLOGY2,LITHOLOGY2 %,LITHOLOGY3,LITHOLOGY3 %,GRAIN SIZE BASE,PHI VALUES BASE,GRAIN SIZE TOP,PHI VALUES TOP,SYMBOLS IN BED,SYMBOLS/STRUCTURES,NOTES COLUMN,BIOTURBATION TYPE,INTENSITY,PALAEOCURRENT VALUES,FACIES\r\n";
	var tag = "THICKNESS (CM),BASE BOUNDARY,LITHOLOGY,LITHOLOGY %,LITHOLOGY2,LITHOLOGY2 %,LITHOLOGY3,LITHOLOGY3 %,GRAIN SIZE BASE,PHI VALUES BASE,GRAIN SIZE TOP,PHI VALUES TOP,SYMBOLS IN BED,SYMBOLS/STRUCTURES,NOTES COLUMN,BIOTURBATION TYPE,INTENSITY,PALAEOCURRENT VALUES,FACIES,OTHER1 TEXT,OTHER1 SYMBOL,OTHER2 TEXT,OTHER2 SYMBOL,OTHER3 TEXT,OTHER3 SYMBOL\r\n";

	// replace 'null', 'undefined' and '' with '<none>'
	for (var i=0; i<arrayparam.length; i++) {
		for (var j=0; j<19; j++) {
			if (arrayparam[i][j] == 'null') {
				arrayparam[i][j] = '<none>';
			} // end if
			else if (arrayparam[i][j] == '') {
				arrayparam[i][j] = '<none>';
			} // end else
			else if (arrayparam[i][j] == 'undefined') {
				arrayparam[i][j] = '<none>';
			} // end else
		} // end for j
	} // end for i

	// add values to tag
	for (i=0; i<arrayparam.length; i++) {
		for (var j=0; j<19; j++) {
			if ( (j==12) || (j==13) || (j==14) || (j==17) ) {
				if (arrayparam[i][j] == '<none>') { arrayparam[i][j] = '""'; }
				else { arrayparam[i][j] = '"'+arrayparam[i][j]+'"'; }
			}
			if ( (j==18) && (arrayparam[i][j] == '<none>') ) {
				arrayparam[i][j] = '0';
			}

			tag += arrayparam[i][j];
			if (j<18) {
				tag += ',';
			}
			else {
				tag += ',"","","","","",""'+"\r\n";
			}
		} // end for j
	} // end for i

	// create directory
	createdirectory ();

	// write file
	window.requestFileSystem(LocalFileSystem.PERSISTENT, 0, function(fileSystem) {
		// the place where the contents of the database will be written
		var namereplaced = name;
		namereplaced.replace(/[^A-Za-z]+/g, '');
		fileSystem.root.getFile('SedMob/'+namereplaced+'.csv', {create: true, exclusive: false}, function(fileEntry) {
			fileEntry.createWriter(function(writer) {
				writer.write(tag);
				// success
				if (sessionStorage.selectedprofile != 0) {
					$('#popupexport').html('<p>Profile ' + name + ' successfully saved in CSV file.</p>');
					$('#popupexport').popup("open")
  					setTimeout(function() {
  						$('#popupexport').popup("close");
  					}, 3000);
				}
			}, filewritefail);
		}, filewritefail);
	}, filewritefail);

}


// ==================================================================

// wrapper for an export of all profiles
function exportwrapper (id, name) {
	db.transaction( function(tx){
		tx.executeSql('SELECT * FROM beds WHERE profileid='+id+' ORDER BY position', [], function (tx, result) { profiletocsv(tx, result, name); });
	});
}

// start an export of profile (profiles) to CSV file(s)
function startexportcsv() {
	if (sessionStorage.selectedprofile != 0) {
		db.transaction( function(tx){
			tx.executeSql( 'SELECT * FROM beds WHERE profileid='+sessionStorage.selectedprofile, [], function (tx, result) { profiletocsv(tx, result, $('#inputname').val()); });
		});
	}
	else {
		navigator.notification.confirm('Do you want to export all profiles to CSV files? This may take some time!', function (buttonIndex) {
			if (buttonIndex == 1) {
				db.transaction( function(tx){
					tx.executeSql( 'SELECT id, name FROM profiles', [], function (tx,resultprofile) {
						for (var x=0; x<resultprofile.rows.length; x++) {
							exportwrapper (resultprofile.rows.item(x).id, resultprofile.rows.item(x).name);
						} // end for x
					});
				});

				navigator.notification.alert(
				'All logs were successfully saved in CSV (SedLog) files.',
				function (){},         // callback
				'CSV Export',            // title
				'OK'                  // buttonName
				);

			} // end if buttonindex == 1
		}, 'Restore', 'OK,Cancel');

	} // end else
}
