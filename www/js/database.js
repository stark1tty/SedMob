
// Populate the database
function populateDB(tx) {
	tx.executeSql('CREATE TABLE IF NOT EXISTS profiles (id INTEGER PRIMARY KEY, name, description, direction, latitude, longitude, altitude, accuracy, altitudeAccuracy, photo)');
	tx.executeSql('CREATE TABLE IF NOT EXISTS beds (id INTEGER PRIMARY KEY, profileid INTEGER, position INTEGER, name, thickness, facies, notes, boundary, paleocurrent, lit1group, lit1type, lit1percentage, lit2group, lit2type, lit2percentage, lit3group, lit3type, lit3percentage, sizeclasticbase, phiclasticbase, sizeclastictop, phiclastictop, sizecarbobase, phicarbobase, sizecarbotop, phicarbotop, bioturbationtype, bioturbationintensity, structures, bedsymbols, audio)');
	tx.executeSql('CREATE TABLE IF NOT EXISTS bedphotos (id INTEGER PRIMARY KEY, profileid INTEGER, bedid INTEGER, photo, description)');
	tx.executeSql('CREATE TABLE IF NOT EXISTS typelithology (id INTEGER PRIMARY KEY, name UNIQUE ON CONFLICT IGNORE)');
	tx.executeSql('CREATE TABLE IF NOT EXISTS indexlithology (id INTEGER PRIMARY KEY, typeid INTEGER, name UNIQUE ON CONFLICT IGNORE)');
	tx.executeSql('CREATE TABLE IF NOT EXISTS typestructure (id INTEGER PRIMARY KEY, name UNIQUE ON CONFLICT IGNORE)');
	tx.executeSql('CREATE TABLE IF NOT EXISTS indexstructure (id INTEGER PRIMARY KEY, typeid INTEGER, name UNIQUE ON CONFLICT IGNORE)');
	tx.executeSql('CREATE TABLE IF NOT EXISTS grainclastic (name, phi)');
	tx.executeSql('CREATE TABLE IF NOT EXISTS graincarbonate (name, phi)');
	tx.executeSql('CREATE TABLE IF NOT EXISTS bioturbation (name)');
	tx.executeSql('CREATE TABLE IF NOT EXISTS boundaries (name)');

	tx.executeSql('SELECT * FROM typelithology',[], function (tx,result) {
		if (result.rows.length == 0) {
			tx.executeSql('INSERT INTO typelithology (id, name) VALUES (1, "Basic")');
			tx.executeSql('INSERT INTO typelithology (id, name) VALUES (2, "Carbonates")');
			tx.executeSql('INSERT INTO typelithology (id, name) VALUES (3, "Other")');
		}
	}, errorCB);


	tx.executeSql('SELECT * FROM indexlithology',[], function (tx,result) {
		if (result.rows.length == 0) {
			tx.executeSql('INSERT INTO indexlithology (id, typeid, name) VALUES (1, 1, "Mudstone")');
			tx.executeSql('INSERT INTO indexlithology (id, typeid, name) VALUES (2, 1, "Claystone")');
			tx.executeSql('INSERT INTO indexlithology (id, typeid, name) VALUES (3, 1, "Shale")');
			tx.executeSql('INSERT INTO indexlithology (id, typeid, name) VALUES (4, 1, "Siltstone")');
			tx.executeSql('INSERT INTO indexlithology (id, typeid, name) VALUES (5, 1, "Sandstone")');
			tx.executeSql('INSERT INTO indexlithology (id, typeid, name) VALUES (6, 1, "Conglomerate")');
			tx.executeSql('INSERT INTO indexlithology (id, typeid, name) VALUES (7, 1, "Coal")');
			tx.executeSql('INSERT INTO indexlithology (id, typeid, name) VALUES (8, 1, "Limestone")');
			tx.executeSql('INSERT INTO indexlithology (id, typeid, name) VALUES (9, 1, "Chert")');
			tx.executeSql('INSERT INTO indexlithology (id, typeid, name) VALUES (10, 1, "Volcaniclastic")');
			tx.executeSql('INSERT INTO indexlithology (id, typeid, name) VALUES (11, 2, "Lime mudstone")');
			tx.executeSql('INSERT INTO indexlithology (id, typeid, name) VALUES (12, 2, "Wackestone")');
			tx.executeSql('INSERT INTO indexlithology (id, typeid, name) VALUES (13, 2, "Packstone")');
			tx.executeSql('INSERT INTO indexlithology (id, typeid, name) VALUES (14, 2, "Grainstone")');
			tx.executeSql('INSERT INTO indexlithology (id, typeid, name) VALUES (15, 2, "Halite")');
			tx.executeSql('INSERT INTO indexlithology (id, typeid, name) VALUES (16, 2, "Gypsum/Anhydrite")');
			tx.executeSql('INSERT INTO indexlithology (id, typeid, name) VALUES (17, 2, "Dolomite")');
			tx.executeSql('INSERT INTO indexlithology (id, typeid, name) VALUES (18, 3, "Breccia")');
			tx.executeSql('INSERT INTO indexlithology (id, typeid, name) VALUES (19, 3, "Matrix-supported conglomerate")');
			tx.executeSql('INSERT INTO indexlithology (id, typeid, name) VALUES (20, 3, "Clast-supported conglomerate")');
			tx.executeSql('INSERT INTO indexlithology (id, typeid, name) VALUES (21, 3, "Lava")');
			tx.executeSql('INSERT INTO indexlithology (id, typeid, name) VALUES (22, 3, "Fine ash")');
			tx.executeSql('INSERT INTO indexlithology (id, typeid, name) VALUES (23, 3, "Coarse ash")');
		}
	}, errorCB);

	tx.executeSql('SELECT * FROM typestructure',[], function (tx,result) {
		if (result.rows.length == 0) {
			tx.executeSql('INSERT INTO typestructure (id, name) VALUES (1, "Sedimentary structures")');
			tx.executeSql('INSERT INTO typestructure (id, name) VALUES (2, "Fossils")');
			tx.executeSql('INSERT INTO typestructure (id, name) VALUES (3, "Trace fossils")');
			tx.executeSql('INSERT INTO typestructure (id, name) VALUES (4, "Other")');
		}
	}, errorCB);

	tx.executeSql('SELECT * FROM indexstructure',[], function (tx,result) {
		if (result.rows.length == 0) {
			tx.executeSql('INSERT INTO indexstructure (id, typeid, name) VALUES (1, 1, "Current ripple cross-lamination")');
			tx.executeSql('INSERT INTO indexstructure (id, typeid, name) VALUES (2, 1, "Wave ripple cross-lamination")');
			tx.executeSql('INSERT INTO indexstructure (id, typeid, name) VALUES (3, 1, "Planar cross bedding")');
			tx.executeSql('INSERT INTO indexstructure (id, typeid, name) VALUES (4, 1, "Trough cross bedding")');
			tx.executeSql('INSERT INTO indexstructure (id, typeid, name) VALUES (5, 1, "Horizontal planar lamination")');
			tx.executeSql('INSERT INTO indexstructure (id, typeid, name) VALUES (6, 1, "Hummocky cross stratification")');
			tx.executeSql('INSERT INTO indexstructure (id, typeid, name) VALUES (7, 1, "Swaley cross stratification")');
			tx.executeSql('INSERT INTO indexstructure (id, typeid, name) VALUES (8, 1, "Mudcracks")');
			tx.executeSql('INSERT INTO indexstructure (id, typeid, name) VALUES (9, 1, "Synaeresis cracks")');
			tx.executeSql('INSERT INTO indexstructure (id, typeid, name) VALUES (10, 1, "Convolute lamination")');
			tx.executeSql('INSERT INTO indexstructure (id, typeid, name) VALUES (11, 1, "Load casts")');
			tx.executeSql('INSERT INTO indexstructure (id, typeid, name) VALUES (12, 1, "Water structures")');
			tx.executeSql('INSERT INTO indexstructure (id, typeid, name) VALUES (13, 1, "Herring-bone cross bedding")');
			tx.executeSql('INSERT INTO indexstructure (id, typeid, name) VALUES (14, 2, "Shells")');
			tx.executeSql('INSERT INTO indexstructure (id, typeid, name) VALUES (15, 2, "Bivalves")');
			tx.executeSql('INSERT INTO indexstructure (id, typeid, name) VALUES (16, 2, "Gastropods")');
			tx.executeSql('INSERT INTO indexstructure (id, typeid, name) VALUES (17, 2, "Cephalopods")');
			tx.executeSql('INSERT INTO indexstructure (id, typeid, name) VALUES (18, 2, "Brachiopods")');
			tx.executeSql('INSERT INTO indexstructure (id, typeid, name) VALUES (19, 2, "Echinoids")');
			tx.executeSql('INSERT INTO indexstructure (id, typeid, name) VALUES (20, 2, "Crinoids")');
			tx.executeSql('INSERT INTO indexstructure (id, typeid, name) VALUES (21, 2, "Solitary corals")');
			tx.executeSql('INSERT INTO indexstructure (id, typeid, name) VALUES (22, 2, "Colonial corals")');
			tx.executeSql('INSERT INTO indexstructure (id, typeid, name) VALUES (23, 2, "Foraminifera")');
			tx.executeSql('INSERT INTO indexstructure (id, typeid, name) VALUES (24, 2, "Algae")');
			tx.executeSql('INSERT INTO indexstructure (id, typeid, name) VALUES (25, 2, "Bryozoa")');
			tx.executeSql('INSERT INTO indexstructure (id, typeid, name) VALUES (26, 2, "Stromatolites")');
			tx.executeSql('INSERT INTO indexstructure (id, typeid, name) VALUES (27, 2, "Vertebrates")');
			tx.executeSql('INSERT INTO indexstructure (id, typeid, name) VALUES (28, 2, "Plant material")');
			tx.executeSql('INSERT INTO indexstructure (id, typeid, name) VALUES (29, 2, "Roots")');
			tx.executeSql('INSERT INTO indexstructure (id, typeid, name) VALUES (30, 2, "Logs")');
			tx.executeSql('INSERT INTO indexstructure (id, typeid, name) VALUES (31, 2, "Tree stumps")');
			tx.executeSql('INSERT INTO indexstructure (id, typeid, name) VALUES (32, 2, "Ostracods")');
			tx.executeSql('INSERT INTO indexstructure (id, typeid, name) VALUES (33, 2, "Radiolaria")');
			tx.executeSql('INSERT INTO indexstructure (id, typeid, name) VALUES (34, 2, "Sponges")');
			tx.executeSql('INSERT INTO indexstructure (id, typeid, name) VALUES (35, 3, "Minor bioturbation")');
			tx.executeSql('INSERT INTO indexstructure (id, typeid, name) VALUES (36, 3, "Moderate bioturbation")');
			tx.executeSql('INSERT INTO indexstructure (id, typeid, name) VALUES (37, 3, "Intense bioturbation")');
			tx.executeSql('INSERT INTO indexstructure (id, typeid, name) VALUES (38, 3, "Tracks")');
			tx.executeSql('INSERT INTO indexstructure (id, typeid, name) VALUES (39, 3, "Trails")');
			tx.executeSql('INSERT INTO indexstructure (id, typeid, name) VALUES (40, 3, "Vertical burrows")');
			tx.executeSql('INSERT INTO indexstructure (id, typeid, name) VALUES (41, 3, "Horizontal burrows")');
			tx.executeSql('INSERT INTO indexstructure (id, typeid, name) VALUES (42, 4, "Nodules and concretions")');
			tx.executeSql('INSERT INTO indexstructure (id, typeid, name) VALUES (43, 4, "Intraclasts")');
			tx.executeSql('INSERT INTO indexstructure (id, typeid, name) VALUES (44, 4, "Mudclasts")');
			tx.executeSql('INSERT INTO indexstructure (id, typeid, name) VALUES (45, 4, "Flute marks")');
			tx.executeSql('INSERT INTO indexstructure (id, typeid, name) VALUES (46, 4, "Groove marks")');
			tx.executeSql('INSERT INTO indexstructure (id, typeid, name) VALUES (47, 4, "Scours")');
		}
	}, errorCB);

	tx.executeSql('SELECT * FROM grainclastic',[], function (tx,result) {
		if (result.rows.length == 0) {
			tx.executeSql('INSERT INTO grainclastic (name, phi) VALUES ("clay", "10.0")');
			tx.executeSql('INSERT INTO grainclastic (name, phi) VALUES ("clay/silt", "8.0")');
			tx.executeSql('INSERT INTO grainclastic (name, phi) VALUES ("silt", "6.0")');
			tx.executeSql('INSERT INTO grainclastic (name, phi) VALUES ("silt/vf", "4.0")');
			tx.executeSql('INSERT INTO grainclastic (name, phi) VALUES ("vf", "3.5")');
			tx.executeSql('INSERT INTO grainclastic (name, phi) VALUES ("vf/f", "3.0")');
			tx.executeSql('INSERT INTO grainclastic (name, phi) VALUES ("f", "2.5")');
			tx.executeSql('INSERT INTO grainclastic (name, phi) VALUES ("f/m", "2.0")');
			tx.executeSql('INSERT INTO grainclastic (name, phi) VALUES ("m", "1.5")');
			tx.executeSql('INSERT INTO grainclastic (name, phi) VALUES ("m/c", "1.0")');
			tx.executeSql('INSERT INTO grainclastic (name, phi) VALUES ("c", "0.5")');
			tx.executeSql('INSERT INTO grainclastic (name, phi) VALUES ("c/vc", "0.0")');
			tx.executeSql('INSERT INTO grainclastic (name, phi) VALUES ("vc", "-0.5")');
			tx.executeSql('INSERT INTO grainclastic (name, phi) VALUES ("vc/granule", "-1.0")');
			tx.executeSql('INSERT INTO grainclastic (name, phi) VALUES ("granule", "-1.5")');
			tx.executeSql('INSERT INTO grainclastic (name, phi) VALUES ("granule/pebble", "-2.3")');
			tx.executeSql('INSERT INTO grainclastic (name, phi) VALUES ("pebble", "-3.0")');
			tx.executeSql('INSERT INTO grainclastic (name, phi) VALUES ("pebble/cobble", "-4.5")');
			tx.executeSql('INSERT INTO grainclastic (name, phi) VALUES ("cobble", "-6.0")');
			tx.executeSql('INSERT INTO grainclastic (name, phi) VALUES ("cobble/boulder", "-8.0")');
			tx.executeSql('INSERT INTO grainclastic (name, phi) VALUES ("boulder", "-10.0")');
		}
	}, errorCB);

	tx.executeSql('SELECT * FROM graincarbonate',[], function (tx,result) {
		if (result.rows.length == 0) {
			tx.executeSql('INSERT INTO graincarbonate (name, phi) VALUES ("mudstone", "6.0")');
			tx.executeSql('INSERT INTO graincarbonate (name, phi) VALUES ("wackestone", "3.5")');
			tx.executeSql('INSERT INTO graincarbonate (name, phi) VALUES ("packstone", "1.5")');
			tx.executeSql('INSERT INTO graincarbonate (name, phi) VALUES ("grainstone", "-0.5")');
			tx.executeSql('INSERT INTO graincarbonate (name, phi) VALUES ("rudstone fine", "-1.5")');
			tx.executeSql('INSERT INTO graincarbonate (name, phi) VALUES ("rudstone medium", "-3.0")');
			tx.executeSql('INSERT INTO graincarbonate (name, phi) VALUES ("rudstone", "-6.0")');
		}
	}, errorCB);

	tx.executeSql('SELECT * FROM bioturbation',[], function (tx,result) {
		if (result.rows.length == 0) {
			tx.executeSql('INSERT INTO bioturbation (name) VALUES ("Minor bioturbation")');
			tx.executeSql('INSERT INTO bioturbation (name) VALUES ("Moderate bioturbation")');
			tx.executeSql('INSERT INTO bioturbation (name) VALUES ("Intense bioturbation")');
			tx.executeSql('INSERT INTO bioturbation (name) VALUES ("Tracks")');
			tx.executeSql('INSERT INTO bioturbation (name) VALUES ("Trails")');
			tx.executeSql('INSERT INTO bioturbation (name) VALUES ("Vertical burrows")');
			tx.executeSql('INSERT INTO bioturbation (name) VALUES ("Horizontal burrows")');
		}
	}, errorCB);

	tx.executeSql('SELECT * FROM boundaries',[], function (tx,result) {
		if (result.rows.length == 0) {
			tx.executeSql('INSERT INTO boundaries (name) VALUES ("Sharp")');
			tx.executeSql('INSERT INTO boundaries (name) VALUES ("Erosion")');
			tx.executeSql('INSERT INTO boundaries (name) VALUES ("Gradational")');
		}
	}, errorCB);
}

// Transaction error callback
function errorCB(tx, err) {
	alert("Error processing SQL: "+err);
}
