/*
    Created on : 15 Mar 2022, 16:30:17
    Author     : xhico
*/

window.addEventListener('DOMContentLoaded', async function main() {
    console.log("Starting");
    console.log("Get Deployments");

    // Reset pagesTable
    $('#table').DataTable().clear().draw();
    $('#table').DataTable().destroy();

    // Get pagesJSON
    let deploymentsJSON = await $.get("/api/deployments", function (result) {
        return result;
    });

    // Set dataset
    let dataset = [];
    deploymentsJSON = deploymentsJSON["deployments"];
    for (let i = 0; i < deploymentsJSON.length; i++) {
        let entry = deploymentsJSON[i];
        let deployment_number = entry["deployment_number"];
        let deployment_user = entry["deployment_user"];
        let submitted_timestamp = entry["submitted_timestamp"];
        let source_files = entry["source_files"];
        let destination_location = entry["destination_location"];
        let status = entry["status"];
        let deployment_log = entry["deployment_log"];
        dataset.push([deployment_number, deployment_number, deployment_user, submitted_timestamp, source_files, destination_location, status, deployment_log]);
    }

    // Setup - add a text input to each header cell
    $('#table thead tr').clone(true).addClass('filters').appendTo('#table thead');
    let searchColumns = [2, 3, 4, 5, 6];

    // Initialize Errors Table
    $('#table').DataTable({
        dom: 'Brtip', buttons: {
            buttons: [{text: 'Export', extend: 'csv', filename: 'Deployments Report', className: 'btn-export'}], dom: {
                button: {
                    className: 'btn'
                }
            }
        }, paginate: false,
        "language": {"emptyTable": "No data available in table"}, "order": [[2, "desc"]], data: dataset,
        initComplete: function () {
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

            $('input[type="checkbox"]').on('click', function() {
                $(".deleteButton").prop('disabled', true);
                if ($('input[type="checkbox"]:checked').length === 1) {
                    $(".deleteButton").prop('disabled', false);
                }

                $(".editButton").prop('disabled', true);
                if ($('input[type="checkbox"]:checked').length === 1) {
                    $(".editButton").prop('disabled', false);
                }
            })

            $(".loadingBg").removeClass("show");

        }, "autoWidth": false, "columnDefs": [{
            "width": "5%", orderable: false, className: "center", "targets": 0, "render": function (data, type, row) {
                return "<input type='checkbox' id='" + data + "' value='" + data + "'>";
            },
        }, {
            "width": "5%", "targets": 1, "render": function (data, type, row) {
                return "<span>" + data + "</span>";
            },
        }, {
            "width": "5%", "targets": 2, "render": function (data, type, row) {
                return "<span>" + data + "</span>";
            },
        }, {
            "width": "20%", "targets": 3, "render": function (data, type, row) {
                return "<span>" + data + "</span>";
            },
        }, {
            "width": "20%", "targets": 4, "render": function (data, type, row) {
                return "<span>" + data + "</span>";
            },
        }, {
            "width": "10%", "targets": 5, "render": function (data, type, row) {
                return "<span>" + data + "</span>";
            },
        }, {
            "width": "10%", "targets": 6, "render": function (data, type, row) {
                let colorClass = "";
                if (data === "progress") {
                    colorClass = " class='dataOrange'"
                } else if (data === "failed") {
                    colorClass = " class='dataRed'"
                } else if (data === "completed") {
                    colorClass = " class='dataGreen'"
                } else if (data === "pending") {
                    colorClass = " class='dataBlue'"
                }
                return "<span" + colorClass + ">" + data + "</span>";
            },
        }, {
            "width": "5%", "targets": 7, "render": function (data, type, row) {
                return "<a class='green-link' onclick='viewLog(\"" + encodeURI(data) + "\")' href='javascript:void(0);'>View</a>";
            },
        }]
    });
    $("#table_wrapper > .dt-buttons").appendTo("div.header-btns");
});

async function viewLog(logContent) {
    logContent = decodeURI(logContent);
    document.getElementById("deployment-log-text").innerText = logContent;
    $('#deploymentLogModal').modal('show');
}

async function deleteDeployments() {

    console.log("deleteDeployments() : START");

    checked_deployments = [];
    checked_deployments_str = "";

    $.each($("input:checked"), function (K, V) {
        checked_deployments.push(V.value);

        checked_deployments_str += V.value + ",";

        //console.log("deleteDeployments() : END");
    });

    checked_deployments_str = checked_deployments_str.slice(0, -1);

    console.log("checked_deployments_str() = " + checked_deployments_str);

    // Post
    $.ajax({
        type: "POST", url: "/delete/deployments", data: {
            "deployments_to_delete": checked_deployments_str
        }, success: function (entry) {
            // Remove row from Table (was "Add row to table")
            //let deployment_name = entry["name"];
            //let deployment_display_name = entry["display_name"];
            //let deployment_description = entry["description"];
            //$('#table').DataTable().row.add(["", deployment_name, deployment_display_name, deployment_description, "NO_DEPLOYMENT"]).order([0, 'desc']).draw();

            // Hide Create Modal
            //$('#addDeploymentModal').modal('hide');

            // Show success notification
            $('#deleteDeploymentSuccessNotification').toast('show');
            //
            // Refresh page
            setTimeout(function () {
                location.reload(true);
            }, 2000);
        }, error: function (XMLHttpRequest, textStatus, errorThrown) {
            // Hide Create Modal
            $('#addDeploymentModal').modal('hide');

            // Show Error Modal
            $('#errorModal').modal('show');

        }
    });

    console.log("deleteDeployments() : END");

}

async function pauseDeployments() {
    console.log("pauseDeployments() : START");

    checked_deployments = [];
    checked_deployments_str = "";

    $.each($("input:checked"), function (K, V) {
        checked_deployments.push(V.value);

        checked_deployments_str += V.value + ",";

        //console.log("deleteDeployments() : END");
    });

    checked_deployments_str = checked_deployments_str.slice(0, -1);

    console.log("checked_deployments_str() = " + checked_deployments_str);

    // Post
    $.ajax({
        type: "POST", url: "/pause/deployments", data: {
            "deployments_to_pause": checked_deployments_str
        }, success: function (entry) {
            // Remove row from Table (was "Add row to table")
            //let deployment_name = entry["name"];
            //let deployment_display_name = entry["display_name"];
            //let deployment_description = entry["description"];
            //$('#table').DataTable().row.add(["", deployment_name, deployment_display_name, deployment_description, "NO_DEPLOYMENT"]).order([0, 'desc']).draw();

            // Hide Create Modal
            //$('#addDeploymentModal').modal('hide');

            // Show success notification
            $('#pauseDeploymentSuccessNotification').toast('show');
            //
            // Refresh page
            setTimeout(function () {
                location.reload(true);
            }, 2000);
        }, error: function (XMLHttpRequest, textStatus, errorThrown) {
            // Hide Create Modal
            $('#addDeploymentModal').modal('hide');

            // Show Error Modal
            $('#errorModal').modal('show');

        }
    });

    console.log("pauseDeployments() : END");
}

async function populateEditDeploymentModal() {
    console.log("populateEditDeploymentModal() START");

    checked_items = $("input:checked");
    n_checked_items = checked_items.length;

    row = checked_items.parent().parent();

    console.log("n checked_items = " + checked_items.length);

    console.log("row html = " + row.html());
    console.log("row text = " + row.text());

    spans = row.find("span");

    console.log("spans = " + spans.length);

    console.log(spans.text());

    console.log("spans[0].textContent : " + spans[0].textContent);
    console.log("spans[1].textContent : " + spans[1].textContent);
    console.log("spans[2].textContent : " + spans[2].textContent);
    console.log("spans[3].textContent : " + spans[3].textContent);
    console.log("spans[4].textContent : " + spans[4].textContent);
    console.log("spans[5].textContent : " + spans[5].textContent);
    console.log("spans[6].textContent : " + spans[6].textContent);

    deployment_number = spans[0].textContent;
    deployment_user = spans[1].textContent;
    submitted_datetime = submitted_timestamp = spans[2].textContent;
    source_files = spans[3].textContent;
    destination_location = spans[4].textContent;
    completed = spans[5].textContent;
    deployment_status = spans[6].textContent;

    console.log("deployment_number : " + deployment_number);
    console.log("deployment_user : " + deployment_user);
    console.log("submitted_datetime : " + submitted_datetime);
    console.log("submitted_timestamp : " + submitted_timestamp);
    console.log("source_files : " + source_files);
    console.log("destination_location : " + destination_location);
    console.log("completed : " + completed);
    console.log("deployment_status : " + deployment_status);

    // Populate edit fields
    $('#e-deployment-source-server').val("127.0.0.1");
    $('#e-deployment-source-path').val(source_files);
    $('#e-deployment-target-server').val("127.0.0.1");
    $('#e-deployment-target-path').val(destination_location);

    // Populate hidden fields (for reference)
    $('#h-e-deployment-source-server').val("127.0.0.1");
    $('#h-e-deployment-source-path').val(source_files);
    $('#h-e-deployment-target-server').val("127.0.0.1");
    $('#h-e-deployment-target-path').val(destination_location);
    $('#h-e-deployment-number').val(deployment_number);

    console.log("populateEditDeploymentModal() END");
}

async function updateDeployment() {
    console.log("updateDeployment() : START");

    //alert("updateDeployment()");

    let h_e_deployment_number = document.getElementById("h-e-deployment-number").value;
    let e_deployment_source_server = document.getElementById("e-deployment-source-server").value;
    let e_deployment_source_path = document.getElementById("e-deployment-source-path").value;
    let e_deployment_target_server = document.getElementById("e-deployment-target-server").value;
    let e_deployment_target_path = document.getElementById("e-deployment-target-path").value;

    console.log("deployment-number : " + h_e_deployment_number);
    console.log("deployment-source-server : " + e_deployment_source_server);
    console.log("deployment-source-path : " + e_deployment_source_path);
    console.log("deployment-target-server : " + e_deployment_target_server);
    console.log("deployment-target-path : " + e_deployment_target_path);

    $.ajax({
        type: "POST", url: "/update/deployment", data: {
            "h_e_deployment_number": h_e_deployment_number, "e_deployment_source_server": e_deployment_source_server, "e_deployment_source_path": e_deployment_source_path, "e_deployment_target_server": e_deployment_target_server, "e_deployment_target_path": e_deployment_target_path
        }, success: function (entry) {
            // Add row to Table
            //let group_name = entry["name"];
            //let group_display_name = entry["display_name"];
            //let group_description = entry["description"];
            //let group_id = entry["id"];
            //$('#table').DataTable().row.add(["", group_name, group_display_name, group_description, group_id]).order([0, 'desc']).draw();

            // Hide Create Modal
            $('#editDeploymentModal').modal('hide');

            // Show success notification
            $('#editDeploymentSuccessNotification').toast('show');

            // Refresh page
            setTimeout(function () {
                location.reload(true);
            }, 2000);
        }, error: function (XMLHttpRequest, textStatus, errorThrown) {
            // Hide Create Modal
            $('#editDeploymentModal').modal('hide');

            // Show Error Modal
            $('#errorModal').modal('show');
        }
    });

    console.log("updateDeployment() : END");
}

async function addDeployment() {

    console.log("addDeployment() start");

    let deployment_name = "STANDARD_DEPLOYMENT";
    let deployment_user_name = "rsync_user";
    let deployment_source_server = document.getElementById("deployment-source-server").value;
    let deployment_source_path = document.getElementById("deployment-source-path").value;
    let deployment_target_server = document.getElementById("deployment-target-server").value;
    let deployment_target_path = document.getElementById("deployment-target-path").value;
    console.log("deployment-name: " + deployment_name);
    console.log("deployment-user-name : " + deployment_user_name);
    console.log("deployment-source-server : " + deployment_source_server);
    console.log("deployment-source-path : " + deployment_source_path);
    console.log("deployment-target-server : " + deployment_target_server);
    console.log("deployment-target-path : " + deployment_target_path);

    // Post
    $.ajax({
        type: "POST", url: "/add/deployment", data: {
            "deployment_user": deployment_user_name, "deployment_name": deployment_name, "source_server_name": deployment_source_server, "source_server_ip": deployment_source_server, "source_files": deployment_source_path, "destination_server_name": deployment_target_server, "destination_server_ip": deployment_target_server, "destination_location": deployment_target_path
        }, success: function (entry) {
            // Add row to Table
            let deployment_number = entry["deployment_number"];
            let deployment_user = entry["deployment_user"];
            let submitted_timestamp = entry["submitted_timestamp"];
            let source_files = entry["source_files"];
            let destination_location = entry["destination_location"];
            let completed_timestamp = entry["completed_timestamp"];
            let status = entry["status"];
            $('#table').DataTable().row.add([deployment_number, deployment_user, submitted_timestamp, source_files, destination_location, completed_timestamp, status]).order([0, 'desc']).draw();

            // Hide Create Modal
            $('#addDeploymentModal').modal('hide');

            // Show success notification
            $('#addDeploymentSuccessNotification').toast('show');
        }, error: function (XMLHttpRequest, textStatus, errorThrown) {
            // Hide Create Modal
            $('#addDeploymentModal').modal('hide');

            // Show Error Modal
            $('#errorModal').modal('show');
        }
    });

    console.log("addDeployment() end");
}





