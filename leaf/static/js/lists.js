/*
    Created on : 22 Jun 2022, 14:09:07
    Author     : joao
*/

async function addList() {
    let list_name = document.getElementById("list-name").value;
    let list_reference = list_name.replace(/\s+/g, '_').toLowerCase();

    // Post
    $.ajax({
        type: "POST",
        url: "/add/list",
        data: {
            "name": list_name,
            "reference": list_reference,
            "accountId": accountId
        },
        success: function (entry) {
            console.log(entry);
            // Add row to Table
            let id = entry[0];
            let name = entry[1];
            let reference = entry[2];
            let created = entry[3];
            let user_with_access = entry[4];
            $('#table').DataTable().row.add([[id, name, user_with_access], [name, created, reference], created, reference]).draw();

            doMainButtons();

            // Hide Create Modal
            $('#addListModal').modal('hide');

            // Show success notification
            $('#addListSuccessNotification').toast('show');

        },
        error: function (XMLHttpRequest, textStatus, errorThrown) {
            // Hide Create Modal
            $('#addListModal').modal('hide');

            // Show Error Modal
            $('#errorModal').modal('show');
        }
    });
}

async function populateEditListModal(accountId) {

    let checked_items = $("input:checked");
    let n_checked_items = checked_items.length;
    let row = checked_items.parent().parent();

    let spans = row.find("span.toEdit");

    let list_name = spans[0].textContent;
    let list_reference = spans[2].textContent;
    let list_created = spans[1].textContent;

    // Populate edit fields
    $('#e-list-name').val(list_name);
    $('#e-list-created').val(list_created);

    // Populate hidden fields (for reference)
    $('#h-e-list-name').val(list_name);
    $('#h-e-list-reference').val(list_reference);

    let listOfUsers = await $.get("/api/get_lfi_users/" + accountId, function (result) {
        return result;
    });

    var list_users_with_access = $("input:checked").parent().find('.users_with_access_list').val();
    list_users_with_access = list_users_with_access.split(',').map(Number);

    $('.users-with-access-container').html('');
    for (var x = 0; x < listOfUsers.users.length; x++) {
        var thisUser = listOfUsers.users[x];
        var userImage = '<span class="logo_image_container"><img class="logo_image" src="' + thisUser["user_image"] + '" onerror="this.style.display=\'none\'" /></span>';
        if (thisUser["user_image"].startsWith('#')) {
            var colorToFillBg = thisUser["user_image"];
            var usernameInitial = (thisUser["username"] ? thisUser["username"] : "SEM_NOME").charAt(0);
            userImage = '<span class="logo_image" style="background-color:' + colorToFillBg + '">' + usernameInitial + '</span>';
        }
        $(".users-with-access-container").prepend('<label for="thisUserId_' + thisUser["id"] + '" class="form-control users-with-access users-with-access_' + thisUser["id"] + '">' + userImage + '<span class="userName">' + thisUser["username"] + '</span><input type="checkbox" class="form-check-input pull-right this-user-id" name="thisUserId_' + thisUser["id"] + '" id="thisUserId_' + thisUser["id"] + '" ' + (list_users_with_access.includes(thisUser["id"]) ? "checked" : "") + '/></span>');
    }

    $('#users-with-access-search').on('keyup', function (e) {
        var tagElems = $('.users-with-access');
        $(tagElems).hide();
        for (var i = 0; i < tagElems.length; i++) {
            var tag = $(tagElems).eq(i);
            if (($(tag).children('span.userName').text().toLowerCase()).indexOf($(this).val().toLowerCase()) !== -1) {
                $(tag).show();
            }
        }
    });
}

async function updateList() {

    $("#update_list_btn").addClass("loadingBtn").prop("disabled", true);

    let e_list_name = document.getElementById("e-list-name").value;
    let e_list_created = document.getElementById("e-list-created").value;
    let h_e_list_name = document.getElementById("h-e-list-name").value;
    let h_e_list_reference = document.getElementById("h-e-list-reference").value;

    if (!h_e_list_reference) {
        h_e_list_reference = e_list_name.replace(/\s+/g, '_').toLowerCase();
    }

    // @J to fix
    var allSelectedUsers = [];
    $('.this-user-id:checked').each(function () {
        var thisId = $(this).attr('id');
        thisId = thisId.replace('thisUserId_', '');
        allSelectedUsers.push(thisId);
    })

    allSelectedUsers = allSelectedUsers.join(',')
    console.log(allSelectedUsers);

    // Post
    $.ajax({
        type: "POST",
        url: "/update/list",
        data: {
            "accountId": accountId,
            "reference": h_e_list_reference,
            "original_list_name": h_e_list_name,
            "new_list_name": e_list_name,
            "user_with_access": allSelectedUsers
        },
        success: function (entry) {

            $('#table').DataTable().draw();

            $("#update_list_btn").removeClass("loadingBtn").prop("disabled", false);

            // Hide Modal
            $('#editListModal').modal('hide');

            // Show success notification
            $('#editListSuccessNotification').toast('show');

            setTimeout(function () {
                location.reload(true);
            }, 1000);

        },
        error: function (XMLHttpRequest, textStatus, errorThrown) {
            // Hide Modal
            $('#editListModal').modal('hide');

            // Show Error Modal
            $('#errorModal').modal('show');
        }
    });
}

async function deleteLists() {

    $("#delete_list_btn").addClass("loadingBtn").prop("disabled", true);

    let checked_lists = [];
    let checked_lists_str = "";

    //console.log("Before");
    $.each($("input:checked"), function (K, V) {
        checked_lists.push(V.value);
        checked_lists_str += V.value + ",";
    });

    checked_lists_str = checked_lists_str.slice(0, -1);

    // Post
    $.ajax({
        type: "POST",
        url: "/delete/lists",
        data: {
            "accountId": accountId,
            "lists_to_delete": checked_lists_str
        },
        success: function (entry) {
            $('#table').DataTable().draw();

            $("#delete_list_btn").removeClass("loadingBtn").prop("disabled", false);

            // Hide Modal
            $('#deleteListModal').modal('hide');

            // Show success notification
            $('#deleteListSuccessNotification').toast('show');

            setTimeout(function () {
                location.reload(true);
            }, 1000);

        },
        error: function (XMLHttpRequest, textStatus, errorThrown) {
            // Hide Create Modal
            $('#deleteListModal').modal('hide');

            // Show Error Modal
            $('#deleteErrorModal').modal('show');

        }
    });
}


window.addEventListener('DOMContentLoaded', async function main() {

    // Reset pagesTable
    $('#table').DataTable().clear().draw();
    $('#table').DataTable().destroy();

    // Get pagesJSON
    let json = await $.get("/api/get_lists/" + accountId + "/" + userId + "/" + isAdmin, function (result) {
        return result;
    });

    // Set dataset
    let dataset = [];
    json = json["lists"];
    for (let i = 0; i < json.length; i++) {
        let entry = json[i];
        let id = entry["id"];
        let name = entry["name"];
        let reference = entry["reference"];
        let created = entry["created"];
        let user_with_access = entry["user_with_access"];
        dataset.push([[id, name, user_with_access], [name, reference, created], reference, created]);
    }

    // Setup - add a text input to each header cell
    $('#table thead tr').clone(true).addClass('filters').appendTo('#table thead');
    let searchColumns = [1, 2, 3, 4];

    $('#table').DataTable({
        dom: 'Brtip',
        buttons: {
            buttons: [
                {
                    text: 'Export',
                    extend: 'csv',
                    filename: 'Lists Report',
                    className: 'btn-export'
                }
            ],
            dom: {
                button: {
                    className: 'btn'
                }
            }
        },
        paginate: false,
        language: {"emptyTable": "No data available in table"},
        order: [[2, "desc"]],
        data: dataset,
        initComplete: function () {
            // For each column
            var api = this.api();
            api.columns().eq(0).each(function (colIdx) {
                // Set the header cell to contain the input element
                var cell = $('.filters th').eq($(api.column(colIdx).header()).index());
                if (searchColumns.includes(colIdx)) {
                    $(cell).html('<input type="text" type="text" oninput="stopPropagation(event)" onclick="stopPropagation(event);" class="form-control form-control-sm" placeholder="Search" />');
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

            doMainButtons();
            $(".loadingBg").removeClass("show");

        },
        autoWidth: false,
        columnDefs: [
            {
                width: "5%",
                orderable: false,
                className: "center",
                targets: 0,
                render: function (data, type, row) {
                    return "<input type='checkbox' id='" + data[0] + "' value='" + data[1] + "' ><input class='users_with_access_list hide' value='" + data[2] + "' />";
                },
            },
            {
                width: "50%",
                targets: 1,
                render: function (data, type, row) {
                    return '<a href="/list/' + data[2] + '"><span class="toEdit">' + data[0] + '</span></a>';
                },
            },
            {
                width: "30%",
                targets: 2,
                render: function (data, type, row) {
                    return '<span class="hidden">' + Date.parse(data) + "</span><span class='toEdit'>" + data + "</span>";
                },
            },
            {
                width: "20%",
                targets: 3,
                render: function (data, type, row) {
                    return '<a href="/list/' + data + '">View</a><span class="hidden toEdit">' + data + '</span>';
                },
            }
        ]
    });
    $("#table_wrapper > .dt-buttons").appendTo("div.header-btns");
});

function stopPropagation(evt) {
    sanitizeInput(evt);
    if (evt.stopPropagation !== undefined) {
        evt.preventDefault();
        evt.stopPropagation();
    } else {
        evt.cancelBubble = true;
    }
}

function doMainButtons() {
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
}
