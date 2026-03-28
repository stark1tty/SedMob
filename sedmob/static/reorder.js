/**
 * Bed drag-and-drop reorder via the existing /profile/<id>/bed/reorder endpoint.
 * Attach to a <tbody id="bed-list" data-profile-id="..."> where each <tr> has data-bed-id.
 */
document.addEventListener('DOMContentLoaded', function () {
    var tbody = document.getElementById('bed-list');
    if (!tbody) return;

    var profileId = tbody.dataset.profileId;
    var dragRow = null;

    tbody.querySelectorAll('tr').forEach(function (row) {
        row.setAttribute('draggable', 'true');

        row.addEventListener('dragstart', function (e) {
            dragRow = row;
            row.style.opacity = '0.4';
            e.dataTransfer.effectAllowed = 'move';
        });

        row.addEventListener('dragend', function () {
            dragRow = null;
            row.style.opacity = '';
            tbody.querySelectorAll('tr').forEach(function (r) {
                r.classList.remove('drag-over');
            });
        });

        row.addEventListener('dragover', function (e) {
            e.preventDefault();
            e.dataTransfer.dropEffect = 'move';
            if (row !== dragRow) {
                row.classList.add('drag-over');
            }
        });

        row.addEventListener('dragleave', function () {
            row.classList.remove('drag-over');
        });

        row.addEventListener('drop', function (e) {
            e.preventDefault();
            row.classList.remove('drag-over');
            if (!dragRow || dragRow === row) return;

            // Insert dragged row before or after the drop target
            var rows = Array.from(tbody.querySelectorAll('tr'));
            var dragIdx = rows.indexOf(dragRow);
            var dropIdx = rows.indexOf(row);
            if (dragIdx < dropIdx) {
                tbody.insertBefore(dragRow, row.nextSibling);
            } else {
                tbody.insertBefore(dragRow, row);
            }

            // Update position numbers and persist
            var order = [];
            tbody.querySelectorAll('tr').forEach(function (r, i) {
                r.querySelector('.bed-pos').textContent = i + 1;
                order.push(parseInt(r.dataset.bedId, 10));
            });

            fetch('/profile/' + profileId + '/bed/reorder', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(order)
            });
        });
    });
});
