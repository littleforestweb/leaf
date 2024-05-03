/*
    Created on : 02 Mar 2022, 09:59:17
    Author     : xhico
*/

async function populateEditSiteDialog() {
    console.log("populateEditSiteDialog() START");

    let checked_items = $("input:checked");
    let row = checked_items.parent().parent();

    console.log("n checked_items = " + checked_items.length);
    console.log("row html = " + row.html());
    console.log("row text = " + row.text());

    let spans = row.find("span");
    console.log("spans = " + spans.length);
    console.log(spans.text());

    let site_id = escapeHtml(spans[0].textContent);
    let site_url = escapeHtml(spans[1].textContent);
    let site_folder = escapeHtml(spans[2].textContent);

    console.log("site_id : " + site_id);
    console.log("site_url : " + site_url);
    console.log("site_folder : " + site_folder);

    // Populate edit fields
    $('#e-site-id').val(site_id);
    $('#e-site-url').val(site_url);
    $('#e-site-folder').val(site_folder);

    // Populate hidden fields (for reference)
    $('#h-e-site-id').val(site_id);
    $('#h-e-site-url').val(site_url);
    $('#h-e-site-folder').val(site_folder);

    console.log("populateEditSiteDialog() END");
}

async function updateSite() {
    let e_site_id = escapeHtml(document.getElementById("e-site-id").value);
    let e_site_url = escapeHtml(document.getElementById("e-site-url").value);
    let e_site_folder = escapeHtml(document.getElementById("e-site-folder").value);
    let h_e_site_id = escapeHtml(document.getElementById("h-e-site-id").value);
    let h_e_site_url = escapeHtml(document.getElementById("h-e-site-url").value);
    let h_e_site_folder = escapeHtml(document.getElementById("h-e-site-folder").value);

    // Post
    $.ajax({
        type: "POST", url: "/update/site", data: {
            "original_site_id": h_e_site_id, "original_site_url": h_e_site_url, "original_site_folder": h_e_site_folder, "new_site_id": e_site_id, "new_site_url": e_site_url, "new_site_folder": e_site_folder
        }, success: function (entry) {

            $('#editSiteModal').modal('hide');

            // Show success notification
            $('#editSiteSuccessNotification').toast('show');

            // Refresh page
            //setTimeout(function () {
            //    location.reload(true);
            //}, 2000);
        }, error: function (XMLHttpRequest, textStatus, errorThrown) {
            $('#editSiteModal').modal('hide');

            // Show Error Modal
            $('#errorModal').modal('show');
        }
    });
}

async function deleteSites() {
    let checked_sites_str = "";
    $.each($("input:checked"), function (K, V) {
        checked_sites_str += V.value + ",";
    });
    checked_sites_str = checked_sites_str.slice(0, -1);

    // Post
    $.ajax({
        type: "POST", url: "/delete/sites", data: {
            "sites_to_delete": checked_sites_str
        }, success: function (entry) {
            // Show success notification
            $('#deleteSiteSuccessNotification').toast('show');
        }, error: function (XMLHttpRequest, textStatus, errorThrown) {
            // Show Error Modal
            $('#deleteSiteErrorNotification').toast('show');
        }
    });
}

async function addSite() {
    $.ajax({
        type: "POST", url: "/add/site", data: {
            "site_url": escapeHtml(document.getElementById("site_url").value),
            "site_label": escapeHtml(document.getElementById("site_label").value),
            "site_ignore_robots": escapeHtml(document.getElementById("site_ignore_robots").value),
            "site_max_urls": escapeHtml(document.getElementById("site_max_urls").value),
            "site_gen_screenshots": escapeHtml(document.getElementById("site_gen_screenshots").value),
            "site_allowed_domains": escapeHtml(document.getElementById("site_allowed_domains").value),
            "site_reject_paths": escapeHtml(document.getElementById("site_reject_paths").value)
        }, success: function (entry) {
            // Check for failed entry
            if (entry["message"] === "success") {
                // Add row to Table
                let id = entry["id"];
                let base_url = entry["base_url"];
                let base_folder = entry["base_folder"];
                let submitted_datetime = entry["submitted_datetime"].replace("GMT", "").trim();
                let status = entry["status"];
                $('#table').DataTable().row.add(["", id, base_url, base_folder, submitted_datetime, status, id]).order([1, 'desc']).draw();

                // Hide Create Modal
                $('#addSiteModal').modal('hide');

                // Show success notification
                $('#addSiteSuccessNotification').toast('show');
            } else if (entry["message"] === "duplicate") {
                // Hide Create Modal
                $('#addSiteModal').modal('hide');

                // Show success notification
                $('#addSiteDuplicateNotification').toast('show');
            } else {
                // Hide Create Modal
                $('#addSiteModal').modal('hide');

                // Show Error Modal
                $('#addSiteErrorNotification').modal('show');
            }
        }, error: function (XMLHttpRequest, textStatus, errorThrown) {
            // Hide Create Modal
            $('#addSiteModal').modal('hide');

            // Show Error Modal
            $('#addSiteErrorNotification').modal('show');
        }
    });
}

async function viewLog(siteId) {
    console.log(siteId);

    // Get site log
    let json = await $.get("/api/get_site_log?id=" + siteId, function (result) {
        return result;
    });

    document.getElementById("site-log-text").innerText = decodeURI(json["crawlLogTail"]);
    $('#siteLogModal').modal('show');
}

window.addEventListener('DOMContentLoaded', async function main() {
    console.log("Starting");
    console.log("Get All Sites");

    // Reset pagesTable
    $('#table').DataTable().clear().draw();
    $('#table').DataTable().destroy();

    // Get sitesJSON
    let json = await $.get("/api/get_sites/", function (result) {
        return result;
    });
    json = json["sites"];

    // // Redirect to site page if crawl is complete AND if account only has one site
    // if (json.length === 1 && json[0]["status"] === "Complete") {
    //     window.location.href = "/get_site?id=" + json[0]["id"];
    // }

    // Set dataset
    let dataset = [];
    for (let i = 0; i < json.length; i++) {
        let entry = json[i];
        let id = entry["id"];
        let base_url = entry["base_url"];
        let base_folder = entry["base_folder"];
        let submitted_datetime = entry["submitted_datetime"].replace("GMT", "").trim();
        let status = entry["status"];
        dataset.push([id, id, base_url, base_folder, submitted_datetime, status, [id, status]]);
    }

    // Setup - add a text input to each header cell
    $('#table thead tr').clone(true).addClass('filters').appendTo('#table thead');
    let searchColumns = [1, 2, 3, 4, 5];

    // Initialize Errors Table
    $('#table').DataTable({
        dom: 'Brtip', buttons: {
            buttons: [{text: 'Export', extend: 'csv', filename: 'Sites Report', className: 'btn-export'}], dom: {
                button: {
                    className: 'btn'
                }
            }
        }, paginate: false, "language": {"emptyTable": "No data available in table"}, "order": [[1, "desc"]], data: dataset, "autoWidth": false, initComplete: function () {
            // For each column
            var api = this.api();
            api.columns().eq(0).each(function (colIdx) {
                // Set the header cell to contain the input element
                var cell = $('.filters th').eq($(api.column(colIdx).header()).index());
                if (searchColumns.includes(colIdx)) {
                    $(cell).html('<input type="text" oninput="stopPropagation(event)" onclick="stopPropagation(event);" class="form-control form-control-sm" placeholder="Search" />');
                } else {
                    $(cell).html('<span></span>');
                }

                // On every keypress in this input
                $('input', $('.filters th').eq($(api.column(colIdx).header()).index())).off('keyup change').on('keyup change', function (e) {
                    e.stopPropagation();
                    // Get the search value
                    $(this).attr('title', $(this).val());
                    var regexr = '({search})';
                    var cursorPosition = this.selectionStart;

                    // Search the column for that value
                    api.column(colIdx).search(this.value != '' ? regexr.replace('{search}', '(((' + this.value + ')))') : '', this.value != '', this.value == '').draw();
                    $(this).focus()[0].setSelectionRange(cursorPosition, cursorPosition);
                });
            });

            // $('input[type="checkbox"]').on('click', function () {
            //     $(".deleteButton").prop('disabled', true);
            //     if ($('input[type="checkbox"]:checked').length === 1) {
            //         $(".deleteButton").prop('disabled', false);
            //     }
            //
            //     $(".editButton").prop('disabled', true);
            //     if ($('input[type="checkbox"]:checked').length === 1) {
            //         $(".editButton").prop('disabled', false);
            //     }
            // })

            $(".loadingBg").removeClass("show");
        }, "columnDefs": [{
            "width": "5%", orderable: false, className: "center", "targets": 0, "render": function (data, type, row) {
                return "<input type='checkbox' id='" + data + "' value='" + data + "'>";
            },
        }, {
            "width": "5%", "targets": 1, "render": function (data, type, row) {
                return "<span>" + data + "</span>";
            },
        }, {
            "width": "40%", "targets": 2, "render": function (data, type, row) {
                return "<span>" + data + "</span>";
            },
        }, {
            "width": "10%", "targets": 3, "render": function (data, type, row) {
                return "<span>" + data + "</span>";
            },
        }, {
            "width": "20%", "targets": 4, "render": function (data, type, row) {
                return "<span>" + data + "</span>";
            },
        }, {
            "width": "15%", "targets": 5, "render": function (data, type, row) {
                let colorClass = "";
                data = data.toString();
                if (data.includes("complete")) {
                    colorClass = " class='dataGreen'"
                } else if (data.includes("running")) {
                    colorClass = " class='dataBlue'"
                } else if (data.includes("failed")) {
                    colorClass = " class='dataRed'"
                }
                return "<span" + colorClass + ">" + data + "</span>";
            },
        }, {
            "width": "5%", orderable: false, "targets": 6, "render": function (data, type, row) {
                if (data[1] === "Complete") {
                    return "<a class='btn btn-sm' href='/get_site?id=" + data[0] + "'>View</a>";
                } else {
                    return "<a class='btn btn-sm' onclick='viewLog(\"" + data[0] + "\")' href='javascript:void(0);'>View Log</a>"
                }
            },
        }]
    });
    $("#table_wrapper > .dt-buttons").appendTo("div.header-btns");
});

function stopPropagation(evt) {
    if (evt.stopPropagation !== undefined) {
        evt.preventDefault();
        evt.stopPropagation();
    } else {
        evt.cancelBubble = true;
    }
}
