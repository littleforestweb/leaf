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
        var checkboxes = document.querySelectorAll('#table input[type="checkbox"]');
        if (this.checked) {
            for (var i = 0; i < checkboxes.length; i++) {
                if (checkboxes[i] !== this) {
                    checkboxes[i].checked = false;
                }
            }
        }

        $("#addUserBtn").prop('disabled', false);
        if ($('input[type="checkbox"]:checked').length === 1) {
            $("#addUserBtn").prop('disabled', true);
        }

        $("#editUserBtn").prop('disabled', true);
        if ($('input[type="checkbox"]:checked').length === 1) {
            $("#editUserBtn").prop('disabled', false);
        }

        $("#deleteUserBtn").prop('disabled', true);
        if ($('input[type="checkbox"]:checked').length === 1) {
            $("#deleteUserBtn").prop('disabled', false);
        }
    })
}

function showNotification(title, message, color) {
    $('#notificationToast rect').attr("fill", color);
    $('#notificationToast strong').text(title);
    $('#notificationToast .toast-body').text(message);
    $('#notificationToast').toast("show");
}

async function addUser() {
    let user_name = escapeHtml($("#add-user-name").val());
    let user_email = escapeHtml($("#add-user-email").val());
    let user_is_admin = escapeHtml($("#add-user-is-admin").val());
    let user_is_manager = escapeHtml($("#add-user-is-manager").val());
    let user_password = $("#add-user-password").val();

    // Post
    $.ajax({
        type: "POST", url: "/user/add",
        data: {
            "username": user_name,
            "email": user_email,
            "is_admin": user_is_admin,
            "is_mmanager": user_is_manager,
            "password": user_password
        },
        success: function (entry) {
            // Hide Create Modal
            $('#addUserModal').modal('hide');

            // Set notification details based on response
            if (entry.error === "Email already registered") {
                showNotification("Error", entry.error, "red");
            } else {
                showNotification("Success", "User added successfully", "green");
                // Refresh page after a short delay
                setTimeout(() => {
                    location.reload(true);
                }, 500);
            }
        }, error: function (XMLHttpRequest, textStatus, errorThrown) {
            // Hide Create Modal
            $('#addUserModal').modal('hide');

            // Set Success Notification Information
            showNotification("Notification", "There was an error adding user. Please try again.", "red");
        }
    });
}

document.querySelector("#editUserModal").addEventListener("show.bs.modal", event => {
    let selectedCheckbox = $('input[type="checkbox"]:checked:first');
    let row = selectedCheckbox.closest('tr');
    let userName = row.find('td:eq(2)').text().trim();
    let userEmail = row.find('td:eq(3)').text().trim();
    let userIsAdmin = row.find('td:eq(4)').text().trim() === "Yes" ? 1 : 0;
    let userIsManager = row.find('td:eq(5)').text().trim() === "Yes" ? 1 : 0;
    document.querySelector("#edit-user-name").value = userName;
    document.querySelector("#edit-user-email").value = userEmail;
    document.querySelector("#edit-user-is-admin").value = userIsAdmin;
    document.querySelector("#edit-user-is-manager").value = userIsManager;
});

async function editUser() {
    let selectedCheckbox = $('input[type="checkbox"]:checked:first');
    let row = selectedCheckbox.closest('tr');
    let userId = row.find('td:eq(1)').text().trim();
    let userIsAdmin = escapeHtml($("#edit-user-is-admin").val());
    let userIsManager = escapeHtml($("#edit-user-is-manager").val());
    console.log(userId, userIsAdmin, userIsManager)

    // Post
    $.ajax({
        type: "POST", url: "/user/edit",
        data: {
            "user_id": userId,
            "is_admin": userIsAdmin,
            "is_manager": userIsManager,
        },
        success: function (entry) {
            // Hide Create Modal
            $('#editUserModal').modal('hide');

            // Set notification details based on response
            showNotification("Success", "User edited successfully", "green");

            // Refresh page after a short delay
            setTimeout(() => {
                location.reload(true);
            }, 500);
        }, error: function (XMLHttpRequest, textStatus, errorThrown) {
            // Hide Create Modal
            $('#editUserModal').modal('hide');

            // Set Success Notification Information
            showNotification("Notification", "There was an error editing user. Please try again.", "red");
        }
    });
}

async function deleteUser(thisButton) {
    thisButton.classList.add('disabled');
    let user_id = $('input[type="checkbox"]:checked:first').val();

    // Post
    $.ajax({
        type: "POST",
        url: "/user/delete",
        data: {"user_id": user_id},
        success: function (entry) {
            location.reload(true);
        }, error: function (XMLHttpRequest, textStatus, errorThrown) {
            // Hide Delete Modal
            $('#deleteUserModal').modal('hide');

            // Set Success Notification Information
            showNotification("Notification", "There was an error deleting the user. Please try again.", "red");
        }
    });
}

window.addEventListener('DOMContentLoaded', async function main() {
    console.log("Starting");
    console.log("Get Users");

    // Reset pagesTable
    $('#table').DataTable().clear().draw();
    $('#table').DataTable().destroy();

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
        let is_admin = entry["is_admin"] === 1 ? "Yes" : "No";
        let is_manager = entry["is_manager"] === 1 ? "Yes" : "No";
        dataset.push([id, id, name, email, is_admin, is_manager]);
    }

    // Setup - add a text input to each header cell
    $('#table thead tr').clone(true).addClass('filters').appendTo('#table thead');
    let searchColumns = [1, 2, 3, 4, 5];

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
            "width": "35%", "targets": 2, "render": function (data, type, row) {
                return "<span>" + data + "</span>";
            },
        }, {
            "width": "35%", "targets": 3, "render": function (data, type, row) {
                return "<span>" + data + "</span>";
            },
        }, {
            "width": "10%", "targets": 4, "render": function (data, type, row) {
                return "<span>" + data + "</span>";
            },
        }, {
            "width": "10%", "targets": 5, "render": function (data, type, row) {
                return "<span>" + data + "</span>";
            },
        }]
    });
    $("#table_wrapper > .dt-buttons").appendTo("div.header-btns");
});



