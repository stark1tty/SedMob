/**
 * In-browser audio recording using MediaRecorder API.
 * Records from the microphone and POSTs the result to the bed audio upload endpoint.
 */
document.addEventListener('DOMContentLoaded', function () {
    var btn = document.getElementById('btn-record');
    if (!btn) return;

    var status = document.getElementById('record-status');
    var mediaRecorder = null;
    var chunks = [];

    btn.addEventListener('click', function () {
        if (mediaRecorder && mediaRecorder.state === 'recording') {
            mediaRecorder.stop();
            return;
        }

        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            status.textContent = 'Browser does not support audio recording.';
            return;
        }

        status.textContent = 'Requesting microphone…';
        navigator.mediaDevices.getUserMedia({ audio: true }).then(function (stream) {
            chunks = [];
            mediaRecorder = new MediaRecorder(stream);

            mediaRecorder.addEventListener('dataavailable', function (e) {
                if (e.data.size > 0) chunks.push(e.data);
            });

            mediaRecorder.addEventListener('stop', function () {
                stream.getTracks().forEach(function (t) { t.stop(); });
                btn.textContent = 'Record Audio';
                btn.classList.remove('btn-danger');
                btn.classList.add('btn-success');
                status.textContent = 'Uploading…';

                var blob = new Blob(chunks, { type: 'audio/webm' });
                var form = new FormData();
                form.append('audio', blob, 'recording.webm');

                fetch(btn.dataset.uploadUrl, { method: 'POST', body: form })
                    .then(function () { location.reload(); })
                    .catch(function () { status.textContent = 'Upload failed.'; });
            });

            mediaRecorder.start();
            btn.textContent = 'Stop Recording';
            btn.classList.remove('btn-success');
            btn.classList.add('btn-danger');
            status.textContent = 'Recording…';
        }).catch(function (err) {
            status.textContent = 'Microphone access denied.';
        });
    });
});
