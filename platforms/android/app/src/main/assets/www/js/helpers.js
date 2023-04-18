// save current sql command to a file
function savetofile (tag) {
	var storagesynchronize = window.localStorage.getItem("sedmob-synchronize");
	if (storagesynchronize == 'true') {

		// create directory
		createdirectory ();

		// write file
		window.requestFileSystem(LocalFileSystem.PERSISTENT, 0, function(fileSystem) {
			// the place where the sql commands will be written
			fileSystem.root.getFile('SedMob/synchronize.txt', {create: true, exclusive: false}, function(fileEntry) {
				fileEntry.createWriter(function(writer) {
					writer.seek(writer.length);
					writer.write(tag+";\r\n");
				}, filewritefail);
			}, filewritefail);
		}, filewritefail);
	} // end if (storagesynchronize == 'true')
}

// create directory SedMob if it doesn't exist
function createdirectory () {
	window.requestFileSystem(LocalFileSystem.PERSISTENT, 0, function (fileSystem) {
		var entry=fileSystem.root; 
		entry.getDirectory("SedMob", {create: true, exclusive: false}, function (dir) {}, function (error){}); 
	}, null);
}

// file fail function
function filewritefail(err) {
	navigator.notification.alert(
		'Backup file cannot be created or restored. Please make sure the SD card is mounted in your device.',
		function (){},         // callback
		'Error',            // title
		'OK'                  // buttonName
	);
}

// size of Javascript object

Object.size = function(obj) {
	var size = 0, key;
	for (key in obj) {
		if (obj.hasOwnProperty(key)) size++;
	}
	return size;
};
