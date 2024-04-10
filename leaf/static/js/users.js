/*
    Created on : 22 Mar 2022, 19:14:17
    Author     : xhico
*/

function stopPropagation(evt) {
    if (evt.stopPropagation !== undefined) {
        evt.preventDefault();
        evt.stopPropagation();
    } else {
        evt.cancelBubble = true;
    }
}

async function doMainButtons() {
    $('#table').on('change', 'input[type="checkbox"]', function () {
        var checkboxes = document.querySelectorAll("input[type='checkbox'].dt-checkboxes");
        if (this.checked) {
            for (var i = 0; i < checkboxes.length; i++) {
                if (checkboxes[i] !== this) {
                    checkboxes[i].checked = false;
                }
            }
        }

        $("#deleteUserBtn").prop('disabled', true);
        if ($('input[type="checkbox"]:checked').length === 1) {
            $("#deleteUserBtn").prop('disabled', false);
        }

        $("#editUserBtn").prop('disabled', true);
        if ($('input[type="checkbox"]:checked').length === 1) {
            $("#editUserBtn").prop('disabled', false);
        }
    })
}

async function addUser() {
    let user_name = escapeHtml(document.getElementById("user-name").value);
    let user_email = escapeHtml(document.getElementById("user-email").value);
    let user_master = escapeHtml(document.getElementById("user-master").value);
    let user_display_name = escapeHtml(document.getElementById("user-display-name").value);
    let user_group_name = escapeHtml(document.getElementById("user-group-name").value);

    // Post
    $.ajax({
        type: "POST", url: "/add/user", data: {
            "name": user_name, "email": user_email, "ismaster": user_master, "display_name": user_display_name, 'user_group_name': user_group_name
        }, success: function (entry) {
            // Add row to Table
            let name = entry["name"];
            let email = entry["email"];
            let ismaster = entry["ismaster"];
            let display_name = entry["display_name"];
            $('#table').DataTable().row.add(["", name, email, ismaster, display_name, "NO_GROUP"]).order([0, 'desc']).draw();

            // Hide Create Modal
            $('#addUserModal').modal('hide');

            // Show success notification
            $('#addUserSuccessNotification').toast('show');

            // Refresh page
            setTimeout(function () {
                location.reload(true);
            }, 500);


        }, error: function (XMLHttpRequest, textStatus, errorThrown) {
            // Hide Create Modal
            $('#addUserModal').modal('hide');

            // Show Error Modal
            $('#errorModal').modal('show');
        }
    });
}

async function populateEditUserModal() {
    console.log("populateEditUserModal() START");

    let checked_items = $("input:checked");
    let row = checked_items.parent().parent();
    console.log("n checked_items = " + checked_items.length);
    console.log("row html = " + row.html());
    console.log("row text = " + row.text());

    let spans = row.find("span");
    let user_name = escapeHtml(spans[0].textContent);
    let user_email = escapeHtml(spans[1].textContent);
    let user_is_master = escapeHtml(spans[2].textContent);
    let user_display_name = escapeHtml(spans[2].textContent);

    // Populate edit fields
    $('#e-user-name').val(user_name);
    $('#e-user-email').val(user_email);
    $('#e-user-master').val(user_is_master);
    $('#e-user-display-name').val(user_display_name);

    // Populate hidden fields (for reference)
    $('#h-e-user-name').val(user_name);
    $('#h-e-user-email').val(user_email);
    $('#h-e-user-master').val(user_is_master);
    $('#h-e-user-display-name').val(user_display_name);

    console.log("populateEditUserModal() END");
}

async function updateUser() {
    let e_user_name = escapeHtml(document.getElementById("e-user-name").value);
    let e_user_email = escapeHtml(document.getElementById("e-user-email").value);
    let e_user_master = escapeHtml(document.getElementById("e-user-master").value);
    let e_user_display_name = escapeHtml(document.getElementById("e-user-display-name").value);
    let e_user_group_name = escapeHtml(document.getElementById("e-user-group-name").value);

    let h_e_user_name = escapeHtml(document.getElementById("h-e-user-name").value);
    let h_e_user_email = escapeHtml(document.getElementById("h-e-user-email").value);
    let h_e_user_master = escapeHtml(document.getElementById("h-e-user-master").value);
    let h_e_user_display_name = escapeHtml(document.getElementById("h-e-user-display-name").value);
    let h_e_user_group_name = escapeHtml(document.getElementById("h-e-user-group-name").value);

    // Post
    $.ajax({
        type: "POST", url: "/update/user", data: {
            "original_user_name": h_e_user_name, "original_user_email": h_e_user_email, "original_user_master": h_e_user_master, "original_user_display_name": h_e_user_display_name, "original_user_group_name": h_e_user_group_name,

            "new_user_name": e_user_name, "new_user_email": e_user_email, "new_user_master": e_user_master, "new_user_display_name": e_user_display_name, "new_user_group_name": e_user_group_name

        }, success: function (entry) {

            // Hide Modal
            $('#editUserModal').modal('hide');

            // Show success notification
            $('#editUserSuccessNotification').toast('show');

            // Refresh page
            setTimeout(function () {
                location.reload(true);
            }, 2000);
        }, error: function (XMLHttpRequest, textStatus, errorThrown) {
            // Hide Modal
            $('#editUserModal').modal('hide');

            // Show Error Modal
            $('#errorModal').modal('show');
        }
    });
}

async function deleteUsers() {
    console.log("deleteUsers() : START");

    let checked_users = [];
    let checked_users_str = "";

    $.each($("input:checked"), function (K, V) {
        checked_users.push(V.value);
        checked_users_str += V.value + ",";
    });

    checked_users_str = checked_users_str.slice(0, -1);

    // Post
    $.ajax({
        type: "POST", url: "/delete/users", data: {
            "users_to_delete": checked_users_str
        }, success: function (entry) {
            // Show success notification
            $('#deleteUserSuccessNotification').toast('show');
            // Refresh page
            setTimeout(function () {
                location.reload(true);
            }, 2000);
        }, error: function (XMLHttpRequest, textStatus, errorThrown) {
            // Hide Create Modal
            $('#deleteUserModal').modal('hide');

            // Show Error Modal
            $('#deleteErrorModal').modal('show');

        }
    });

    console.log("deleteUsers() : END");
}

window.addEventListener('DOMContentLoaded', async function main() {
    console.log("Starting");
    console.log("Get Users");

    // Reset pagesTable
    $('#table').DataTable().clear().draw();
    $('#table').DataTable().destroy();

    //console.log("D1");

    // Get pagesJSON
    let json = await $.get("/api/get_users", function (result) {
        return result;
    });


    // Set dataset
    let dataset = [];
    json = json["users"];
    for (let i = 0; i < json.length; i++) {
        let entry = json[i];
        let id = entry["id"];
        let name = entry["name"];
        let email = entry["email"];
        dataset.push([id, id, name, email]);
    }


    // Setup - add a text input to each header cell
    $('#table thead tr').clone(true).addClass('filters').appendTo('#table thead');
    let searchColumns = [1, 2, 3];

    $('#table').DataTable({
        dom: 'Brtip', buttons: {
            buttons: [{text: 'Export', extend: 'csv', filename: 'Users Report', className: 'btn-export'}], dom: {
                button: {
                    className: 'btn'
                }
            }
        }, paginate: false,
        "language": {"emptyTable": "No data available in table"},
        "order": [[1, "asc"]],
        data: dataset,
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

                doMainButtons();
                $(".loadingBg").removeClass("show");
            });
        }, "autoWidth": false, "columnDefs": [{
            "width": "5%", orderable: false, className: "center", "targets": 0, "render": function (data, type, row) {
                return "<input type='checkbox' id='" + data + "' value='" + data + "' >";
            },
        }, {
            "width": "5%", "targets": 1, "render": function (data, type, row) {
                return "<span>" + data + "</span>";
            },
        }, {
            "width": "45%", "targets": 2, "render": function (data, type, row) {
                return "<span>" + data + "</span>";
            },
        }, {
            "width": "45%", "targets": 3, "render": function (data, type, row) {
                return "<span>" + data + "</span>";
            },
        }]
    });
    $("#table_wrapper > .dt-buttons").appendTo("div.header-btns");
});



