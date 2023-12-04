/*
    Created on : 05 Jul 2022, 12:15:12
    Author     : joao
*/

async function addUser(accountId) {
    let user_first_name = escapeHtml(document.getElementById("user-first-name").value);
    let user_last_name = escapeHtml(document.getElementById("user-last-name").value);
    let user_password = escapeHtml(document.getElementById("user-password").value);
    let user_email = escapeHtml(document.getElementById("user-email").value);
    let user_admin = escapeHtml(document.getElementById("user-admin").value);
    let user_manager = escapeHtml(document.getElementById("user-manager").value);
    let account_name = escapeHtml(document.getElementById("account-name").value);

    // Post
    $.ajax({
        type: "POST",
        url: "/api/add_lfi_user",
        data: {
            "first_name": user_first_name,
            "last_name": user_last_name,
            "password": user_password,
            "email": user_email,
            "account_id": accountId,
            "account_name": account_name,
            "is_admin": user_admin,
            "is_manager": user_manager
        },
        success: function (entry) {
            // Add row to Table
            let id = entry["id"];
            let first_name = entry["first_name"];
            let last_name = entry["last_name"];
            let fullname = first_name + " " + last_name;
            let image = entry["image"];
            let email = entry["email"];
            let account_id = entry["account_id"];
            let account_name = entry["account_name"];
            let is_admin = entry["is_admin"];
            let is_manager = entry["is_manager"];
            $('#table').DataTable().row.add([id, [image, fullname], fullname, email, [account_id, account_name], is_admin, is_manager]).order([0, 'desc']).draw();

            // Hide Create Modal
            $('#addUserModal').modal('hide');

            // Show success notification
            $('#addUserSuccessNotification').toast('show');

            // Refresh page
            // setTimeout(function () {
            //     location.reload(true);
            // }, 500);
        },
        error: function (XMLHttpRequest, textStatus, errorThrown) {
            // Hide Create Modal
            $('#addUserModal').modal('hide');

            // Show Error Modal
            $('#errorModal').modal('show');
        }
    });
}

async function populateUserListModal() {

    let checked_items = $('input[type="checkbox"]:checked');
    let row = checked_items.parent().parent();
    let spans = row.find("span.toEdit");
    let user_name = escapeHtml(document.getElementById("account-name").value);
    let user_email = escapeHtml(spans[1].textContent);
    let user_is_admin = escapeHtml(spans[3].textContent);
    let user_is_admin_value = user_is_admin === "False" ? "0" : "1"
    let user_is_manager = escapeHtml(spans[4].textContent);
    let user_is_manager_value = user_is_manager === "False" ? "0" : "1"

    // Populate edit fields
    $('#e-user-name').val(user_name);
    $('#e-user-email').val(user_email);
    $('#e-user-admin').val(user_is_admin_value);
    $('#e-user-manager').val(user_is_manager_value);

    // Populate hidden fields (for reference)
    $('#h-e-user-name').val(user_name);
    $('#h-e-user-email').val(user_email);
    $('#h-e-user-admin').val(user_is_admin_value);
    $('#h-e-user-manager').val(user_is_manager_value);
}

async function updateUser(accountId) {

    let e_user_name = escapeHtml(document.getElementById("e-user-name").value);
    let e_user_email = escapeHtml(document.getElementById("e-user-email").value);
    let e_user_admin = escapeHtml(document.getElementById("e-user-admin").value);
    let e_user_manager = escapeHtml(document.getElementById("e-user-manager").value);

    let h_e_user_name = escapeHtml(document.getElementById("h-e-user-name").value);
    let h_e_user_email = escapeHtml(document.getElementById("h-e-user-email").value);
    let h_e_user_admin = escapeHtml(document.getElementById("h-e-user-admin").value);
    let h_e_user_manager = escapeHtml(document.getElementById("h-e-user-manager").value);

    // Post
    $.ajax({
        type: "POST",
        url: "/api/update_lfi_user",
        data: {
            "account_id": accountId,
            "original_user_name": h_e_user_name, "original_email": h_e_user_email, "original_is_admin": h_e_user_admin, "original_is_manager": h_e_user_manager,
            "new_user_name": e_user_name, "new_email": e_user_email, "new_is_admin": e_user_admin, "new_is_manager": e_user_manager
        },
        success: function (entry) {

            // Hide Modal
            $('#editUserModal').modal('hide');

            // Show success notification
            $('#editUserSuccessNotification').toast('show');

            // Refresh page
            setTimeout(function () {
                location.reload(true);
            }, 2000);
        },
        error: function (XMLHttpRequest, textStatus, errorThrown) {
            // Hide Modal
            $('#editUserModal').modal('hide');

            // Show Error Modal
            $('#errorModal').modal('show');
        }
    });
}

async function deleteUsers(accountId) {

    let checked_users = [];
    let checked_users_str = "";

    //console.log("Before");
    $.each($("input.user_checker:checked"), function (K, V) {
        checked_users.push(V.value);
        checked_users_str += V.value + ",";
    });

    checked_users_str = checked_users_str.slice(0, -1);

    // Post
    $.ajax({
        type: "POST",
        url: "/api/delete_lfi_users",
        data: {
            "account_id": accountId,
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
}

window.addEventListener('DOMContentLoaded', async function main() {

    // Reset pagesTable
    $('#table').DataTable().clear().draw();
    $('#table').DataTable().destroy();

    // Get sitesJSON
    let json = await $.get("/api/get_all_users/" + accountId, function (result) {
        return result;
    });

    // Set dataset
    let dataset = [];
    json = json["users"];
    console.log(json);
    for (let i = 0; i < json.length; i++) {
        let entry = json[i];
        let id = entry["id"];
        let image = entry["user_image"];
        let username = entry["username"];
        let email = entry["email"];
        let account_name = entry["account_name"];
        let account_id = entry["account_id"];
        let is_admin = entry["is_admin"];
        let is_manager = entry["is_manager"];
        dataset.push([id, [image, username], username, email, [account_id, account_name], is_admin, is_manager]);
    }

    // Setup - add a text input to each header cell
    $('#table thead tr').clone(true).addClass('filters').appendTo('#table thead');
    let searchColumns = [1, 2, 3, 4, 5, 6];

    // Initialize Errors Table
    $('#table').DataTable({
        dom: 'Brtip',
        buttons: {
            buttons: [{text: 'Export', extend: 'csv', filename: 'Sites Report', className: 'btn-export'}], dom: {
                button: {
                    className: 'btn'
                }
            }
        },
        paginate: false,
        language: {"emptyTable": "No data available in table"},
        order: [[0, "desc"]],
        data: dataset,
        autoWidth: false,
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

            $('input[type="checkbox"]').on('click', function () {
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
        },
        columnDefs: [{
            targets: 0,
            width: "5%",
            orderable: false,
            className: "center",
            render: function (data, type, row) {
                return "<input type='checkbox' class='user_checker' id='" + data + "' value='" + data + "'>";
            }
        }, {
            targets: 1,
            render: function (data, type, row) {
                if (data[0].startsWith('#')) {
                    var colorToFillBg = data[0];
                    var usernameInitial = (data[1] ? data[1] : "SEM_NOME").charAt(0);
                    return '<span class="logo_image" style="background-color:' + colorToFillBg + '">' + usernameInitial + '</span>';
                } else {
                    return '<span class="logo_image_container"><img class="logo_image" src="' + data[0] + '" onerror="this.style.display=\'none\'" /></span>';
                }
            }
        }, {
            targets: 2,
            width: "10%",
            render: function (data, type, row) {
                return "<span class='toEdit' style='max-width: 270px; display: inline-block'>" + data + "</span>";
            }
        }, {
            targets: 3,
            render: function (data, type, row) {
                return "<span class='toEdit' style='max-width: 270px; display: inline-block'>" + data + "</span>";
            }
        }, {
            targets: 4,
            render: function (data, type, row) {
                var accountId = data[0];
                var accountName = data[1];
                return "<span class='toEdit' style='max-width: 270px; display: inline-block'>" + accountName + "</span>";
            }
        }, {
            targets: 5,
            render: function (data, type, row) {
                return "<span class='toEdit' style='max-width: 50px; display: inline-block'>" + (data === 1 ? "True" : "False") + "</span>";
            }
        }, {
            targets: 6,
            render: function (data, type, row) {
                return "<span class='toEdit' style='max-width: 50px; display: inline-block'>" + (data === 1 ? "True" : "False") + "</span>";
            }
        }]
    });
    $("#table_wrapper > .dt-buttons").appendTo("div.header-btns");

    $("#show_hide_password a").on('click', function (event) {
        event.preventDefault();
        if ($('#show_hide_password input').attr("type") == "text") {
            $('#show_hide_password input').attr('type', 'password');
            $('#show_hide_password i').addClass("fa-eye-slash");
            $('#show_hide_password i').removeClass("fa-eye");
        } else if ($('#show_hide_password input').attr("type") == "password") {
            $('#show_hide_password input').attr('type', 'text');
            $('#show_hide_password i').removeClass("fa-eye-slash");
            $('#show_hide_password i').addClass("fa-eye");
        }
    });
});
