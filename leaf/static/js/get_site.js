/*
    Created on : 02 Mar 2022, 09:59:17
    Author     : xhico
*/

async function publishSite() {
    await populateUserList();

    // Get all rows that are selected
    let checkedRows = $('#table').DataTable().rows(function (idx, data, node) {
        return $(node).find('.dt-checkboxes:input[type="checkbox"]:checked').val();
    }).data().toArray();

    // Add ids to textarea inside publishModal
    var selectedIdsText = "";
    checkedRows.forEach(function (row) {
        selectedIdsText += row["id"] + ";";
    });

    document.getElementById("selectedIds").innerHTML = selectedIdsText;

    $('#publishModal').modal('show');
}

async function addWorkflow(btn) {
    btn.disabled = true;
    let siteIds = document.getElementById("selectedIds").value;
    let comments = document.getElementById("publishComments").value

    let allSelectedUsers = [];
    $('.this-user-id:checked').each(function () {
        let thisId = $(this).attr('id');
        thisId = thisId.replace('thisUserId_', '');
        allSelectedUsers.push(thisId);
    })
    allSelectedUsers = allSelectedUsers.join(',');

    let form_data = {
        "startUser": userId,
        "assignEditor": allSelectedUsers,
        "siteIds": siteIds,
        "comments": comments,
        "tags": "",
        "type": 1,
        "priority": 2
    }

    $.ajax({
        type: "POST",
        url: "/workflow/add",
        contentType: 'application/json',
        data: JSON.stringify(form_data),
        dataType: 'json',
        cache: false,
        processData: false,
        success: function (entry) {
            document.getElementById("viewWorkflow").href = "/workflow_details?id=" + entry["workflow_id"];
            $('#publishModal').modal("hide");
            $("#viewWorkflowNotification").toast("show");
            btn.disabled = false;
        },
        error: function (XMLHttpRequest, textStatus, errorThrown) {
            console.log("ERROR");
            console.log(XMLHttpRequest, textStatus, errorThrown);
            btn.disabled = false;
        }
    });
}

async function duplicatePage() {
    // Check if user has access to any folder
    if (user_access_folder.length === 0) {
        $(".emptyUserAccessFolderNotification").toast().show();
        $('#renameModal').modal('hide');
        return;
    }

    let checkedRow = $('#table').DataTable().rows(function (idx, data, node) {
        return $(node).find('.dt-checkboxes:input[type="checkbox"]:checked').val();
    }).data().toArray()[0];

    // Set original Title and URL
    let originalPageId = checkedRow["id"];
    let ogTitle = checkedRow["Title"].trim();
    let ogURL = checkedRow["URL"].replace(preview_webserver, "");
    ogURL = !ogURL.startsWith("/") ? "/" + ogURL : ogURL;
    document.getElementById("originalPageId").value = originalPageId;
    document.getElementById("originalTitle").value = ogTitle;
    document.getElementById("originalUrl").value = ogURL;

    $('#renameModal').modal('show');
}

async function addNewDuplicatedPage() {
    let ogPageId = escapeHtml($("#originalPageId").val());
    let ogTitle = escapeHtml($("#originalTitle").val());
    let ogURL = escapeHtml($("#originalUrl").val());
    let newTitle = escapeHtml($("#newTitle").val());
    let newURL = escapeHtml($("#newURL").val());

    // Check user inputs -> Send alert message
    let alertMessageElem = document.getElementById("alertMessage");
    if (newURL === "" || newTitle === "") {
        alertMessageElem.children[0].innerText = "New URL/Title is empty";
        alertMessageElem.hidden = false;
        return;
    }
    if (ogURL === newURL || ogTitle === newTitle) {
        alertMessageElem.children[0].innerText = "New URL/Title is equal to Original URL/Title";
        alertMessageElem.hidden = false;
        return;
    }

    // Check for valid extensions
    const validWebpageExtensions = [".html", ".htm", ".php", ".asp", ".aspx", ".jsp", ".jspx", ".cfm", ".cgi", ".pl", ".py", ".rb", ".page"];
    let isValidExtension = false;
    for (let i = 0; i < validWebpageExtensions.length; i++) {
        if (newURL.endsWith(validWebpageExtensions[i])) {
            isValidExtension = true;
            break;
        }
    }
    if (!isValidExtension) {
        alertMessageElem.children[0].innerText = "New URL doesn't end with a valid extension (" + validWebpageExtensions.join(', ') + ")";
        alertMessageElem.hidden = false;
        return;
    }

    // Check for allowed chars
    let regex = /^[a-zA-Z0-9_\/.\- ;=]+$/;
    if (!regex.test(newURL)) {
        alertMessageElem.children[0].innerText = "New URL has invalid characters. [a-zA-Z0-9_/-;=]";
        alertMessageElem.hidden = false;
        return;
    }

    // Check for allowed user folder
    let startsWithFolder = user_access_folder.some(folder => newURL.startsWith(folder));
    if (!startsWithFolder) {
        alertMessageElem.children[0].innerText = "Permission Denied - New URL does not belong to any authorized folder";
        alertMessageElem.hidden = false;
        return;
    }

    alertMessageElem.hidden = true;
    $.ajax({
        type: "POST", url: "/api/duplicate_page", data: {
            "site_id": site_id, "ogPageId": ogPageId, "ogTitle": ogTitle, "ogURL": ogURL, "newTitle": newTitle, "newURL": newURL
        }, success: function (entry) {
            if (entry["message"] === "file already exists") {
                alertMessageElem.children[0].innerText = "File path already exists.";
                alertMessageElem.hidden = false;
            } else if (entry["message"] === "success") {
                $('#renameModal').modal('hide');
                window.location.reload();
            }
        }, error: function (xhr, textStatus, errorThrown) {
            if (xhr.status === 403) {
                alertMessageElem.children[0].innerText = "Permission Denied - New URL does not belong to any authorized folder";
                alertMessageElem.hidden = false;
            }
            console.log(xhr, textStatus, errorThrown)
        }
    });
}

document.getElementById("userFolderSelect").addEventListener("change", function () {
    // Auto update newURL input with folder selected
    document.getElementById("newURL").value = document.getElementById("userFolderSelect").value;
});

async function deletePage(btn) {
    btn.disabled = true;

    let checkedRow = $('#table').DataTable().rows(function (idx, data, node) {
        return $(node).find('.dt-checkboxes:input[type="checkbox"]:checked').val();
    }).data().toArray()[0];

    $.ajax({
        type: "POST",
        url: "/workflow/add",
        contentType: 'application/json',
        data: JSON.stringify({"startUser": userId, "entryId": checkedRow["id"], "type": 5, "priority": 2}),
        dataType: 'json',
        cache: false,
        processData: false,
        success: function (entry) {
            $("#viewWorkflow").attr("href", "/workflow_details?id=" + entry["workflow_id"]);
            $("#deleteModal").modal("hide");
            $("#viewWorkflowNotification").toast('show');
            btn.disabled = false;
        },
        error: function (XMLHttpRequest, textStatus, errorThrown) {
            console.log("ERROR");
        }
    });
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

        $(".duplicateBtn").prop('disabled', true);
        if ($('input[type="checkbox"]:checked').length === 1) {
            $(".duplicateBtn").prop('disabled', false);
        }

        $(".publishBtn").prop('disabled', true);
        if ($('input[type="checkbox"]:checked').length === 1) {
            $(".publishBtn").prop('disabled', false);
        }

        $(".deleteBtn").prop('disabled', true);
        if ($('input[type="checkbox"]:checked').length === 1) {
            $(".deleteBtn").prop('disabled', false);
        }
    })
}

async function populateUserList() {
    let listOfUsers = await $.get("/api/get_lfi_admin_users/" + accountId, function (result) {
        return result;
    });

    $('.users-with-access-container').html('');
    for (let x = 0; x < listOfUsers.users.length; x++) {
        let thisUser = listOfUsers.users[x];
        let userImage = '<span class="logo_image_container"><img class="logo_image" src="' + thisUser["user_image"] + '" onerror="this.style.display=\'none\'" /></span>';
        if (thisUser["user_image"].startsWith('#')) {
            let colorToFillBg = thisUser["user_image"];
            let usernameInitial = (thisUser["username"] ? thisUser["username"] : "LF").charAt(0);
            userImage = '<span class="logo_image" style="background-color:' + colorToFillBg + '">' + usernameInitial + '</span>';
        }
        $(".users-with-access-container").prepend('<label for="thisUserId_' + thisUser["id"] + '" class="form-control users-with-access users-with-access_' + thisUser["id"] + '">' + userImage + '<span class="userName">' + thisUser["username"] + '</span><input type="checkbox" class="form-check-input pull-right this-user-id" name="thisUserId_' + thisUser["id"] + '" id="thisUserId_' + thisUser["id"] + '" ' + '/></span>');
    }

    // Disable Enter
    $('#users-with-access-search').on('keypress', function (e) {
        if (e.keyCode === 13) {
            e.preventDefault(); // Prevent default behavior of return key
            return false; // Stop further execution
        }
    });

    $('#users-with-access-search').on('keyup', function (e) {
        let tagElems = $('.users-with-access');
        $(tagElems).hide();
        for (let i = 0; i < tagElems.length; i++) {
            let tag = $(tagElems).eq(i);
            if (($(tag).children('span.userName').text().toLowerCase()).indexOf($(this).val().toLowerCase()) !== -1) {
                $(tag).show();
            }
        }
    });


    $('.this-user-id').click(function () {
        $('.this-user-id').not(this).prop("checked", false);
    });
}

function stopPropagation(evt) {
    if (evt.stopPropagation !== undefined) {
        evt.preventDefault();
        evt.stopPropagation();
    } else {
        evt.cancelBubble = true;
    }
}

window.addEventListener('DOMContentLoaded', async function main() {
    console.log("Starting");
    console.log("Get Site");

    // Reset Table
    $('#table').DataTable().clear().draw();
    $('#table').DataTable().destroy();

    // Setup - add a text input to each header cell
    $('#table thead tr').clone(true).addClass("filters").appendTo('#table thead');

    let searchColumns = [2, 3, 4];

    $("#table").DataTable({
        dom: "Brtip",
        buttons: {
            buttons: [{text: "Export", extend: "csv", filename: "Site Report", className: "btn-export"}], dom: {
                button: {
                    className: "btn"
                }
            }
        },
        language: {"emptyTable": "No data available in table or invalid permissions"},
        bProcessing: true,
        bServerSide: true,
        sPaginationType: "full_numbers",
        lengthMenu: [[50, 100, 250], [50, 100, 250]],
        sAjaxSource: "/api/get_site?id=" + site_id,
        order: [[0, "asc"]],
        bAutoWidth: false,
        aoColumnDefs: [
            {
                aTargets: [0],
                sClass: "center",
                mData: function (source, type, val) {
                    return "<input class='dt-checkboxes' id='checkbox_" + source["id"] + "' value='" + source["id"] + "' type='checkbox'>";
                }
            },
            {
                aTargets: [1],
                mData: function (source, type, val) {
                    return "<img class='max100px' src='" + "/get_screenshot?id=" + source["id"] + "' height='auto' alt='Page Screenshot Image'>"
                }
            },
            {
                aTargets: [2],
                sClass: "truncate",
                mData: function (source, type, val) {
                    return "<span>" + unescape(source["Title"]) + "</span>";
                }
            },
            {
                aTargets: [3],
                sClass: "truncate",
                mData: function (source, type, val) {
                    return "<a class='green-link' href='" + source["URL"] + "' target='_blank'>" + source["URL"].replace(preview_webserver, "/").replace(/\/+/g, "/") + "</a>";
                }
            },
            {
                aTargets: [4],
                mData: function (source, type, val) {
                    return "<span>" + source["Modified Date"] + "</span>";
                }
            },
            {
                aTargets: [5],
                mData: function (source, type, val) {
                    return "<a class='btn btn-sm' target='_blank' href='/editor?page_id=" + source["id"] + "'>Edit</a>";
                }
            }
        ], initComplete: function () {
            // For each column
            var api = this.api();
            api.columns().eq(0).each(function (colIdx) {
                // Set the header cell to contain the input element
                var cell = $(".filters th").eq($(api.column(colIdx).header()).index());
                if (searchColumns.includes(colIdx)) {
                    $(cell).html('<input type="text" oninput="stopPropagation(event)" onclick="stopPropagation(event);" class="form-control form-control-sm" placeholder="Search" />');
                } else {
                    $(cell).html('<span></span>');
                }

                // On every keypress in this input
                $("input", $('.filters th').eq($(api.column(colIdx).header()).index())).off("keyup change").on("keyup change", function (e) {
                    e.stopPropagation();
                    // Get the search value
                    $(this).attr("title", $(this).val());
                    var regexr = "{search}";
                    var cursorPosition = this.selectionStart;

                    // Search the column for that value
                    api.column(colIdx).search(this.value != '' ? regexr.replace("{search}", this.value) : "", this.value != "", this.value == "").draw();
                    $(this).focus()[0].setSelectionRange(cursorPosition, cursorPosition);
                });
            });

            doMainButtons();
            $(".loadingBg").removeClass("show");
        }
    });

    // Clean-up
    $("#table_wrapper > .dt-buttons").appendTo("div.header-btns");
    $(".loadingBg").removeClass("show");
})
;