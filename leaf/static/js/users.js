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
    let user_is_admin = escapeHtml(document.getElementById("user-is-admin").value);
    let user_is_master = escapeHtml(document.getElementById("user-is-master").value);
    let user_password = document.getElementById("user-password").value;

    // Post
    $.ajax({
        type: "POST", url: "/add/user",
        data: {
            "username": user_name,
            "email": user_email,
            "is_admin": user_is_admin,
            "is_master": user_is_master,
            "password": user_password
        },
        success: function (entry) {
            // Hide Create Modal
            $('#addUserModal').modal('hide');

            // Set Success Notification Information
            $('#notificationToast strong').text("Notification");
            $('#notificationToast .toast-body').text("User added successfully");
            $('#notificationToast').toast("show");

            // Refresh page
            setTimeout(function () {
                location.reload(true);
            }, 500);
        }, error: function (XMLHttpRequest, textStatus, errorThrown) {
            // Hide Create Modal
            $('#addUserModal').modal('hide');

            // Set Success Notification Information
            $('#notificationToast strong').text("Notification");
            $('#notificationToast .toast-body').text("There was an error adding user. Please try again.");
            $('#notificationToast').toast("show");
        }
    });
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



