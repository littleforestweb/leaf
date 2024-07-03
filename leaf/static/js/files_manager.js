/*
    Created on : 18 Apr 2024, 11:10:23
    Author     : joao
*/

async function restoreDeletedAsset(assetId) {
    $.ajax({
        type: "POST",
        url: "/files/restore_deleted_assets",
        data: {"assetId": assetId},
        success: function (entry) {
            window.location.reload();
        },
        error: function (XMLHttpRequest, textStatus, errorThrown) {
            console.log("ERROR");
        }
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

function joinPath(...segments) {
    return segments.map(segment => segment.replace(/(^\/|\/$)/g, '')).join('/');
}

function sanitizeFilePath(filePath) {
    return filePath.replace(/[^a-zA-Z0-9\-._\/]/g, '_').toLowerCase();
}

const validExtensions = ['.xml', '.page', '.html', '.txt', '.jpg', '.png', '.pdf']; // Add more as needed

function getFileNameAndExtension(fileName) {
    // Split the file name by dots to check each part
    const parts = fileName.split('.');
    let name = parts[0];
    let extension = '';

    for (let i = 1; i < parts.length; i++) {
        const part = parts[i];
        const potentialExtension = '.' + part;
        if (validExtensions.includes(potentialExtension.toLowerCase())) {
            name = parts.slice(0, i).join('.');
            extension = parts.slice(i).join('.');
            extension = '.' + extension; // Reconstruct the extension with dots
            break;
        }
    }

    // If no valid extension is found, treat the entire name as the base name
    if (!extension) {
        name = fileName;
    }

    return {name, extension};
}

async function setFull_pathSpan() {
    const folder = sanitizeFilePath(document.getElementById("folder").value);
    const fullFileName = document.getElementById("file").value.split('\\').pop();

    // Get the file name and extension using the helper function
    const {name, extension} = getFileNameAndExtension(fullFileName);
    const final_extension = extension.trim().split(".")[1]

    // Sanitize only the base name part, preserving the original extension
    const sanitizedFileName = sanitizeFilePath(name) + "." + final_extension;
    document.getElementById("full_path").value = joinPath(folder, sanitizedFileName);
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

    $('#users-with-access-search').on('input', function (e) {
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

function upload_file(formData) {
    fetch('/files/fileupload_api', {
        method: 'POST',
        body: formData,
    })
        .then(data => {
            document.getElementById('modal-footer-upload-btn').disabled = true;
            document.getElementById('modal-footer-upload-close').disabled = true;
            document.getElementById('file_upload_result').classList.add("form-control");
            document.getElementById('file_upload_result').classList.remove("is-invalid");
            document.getElementById('file_upload_result').classList.add("is-valid");
            document.getElementById('file_upload_result').textContent = 'Upload successful!';
            console.log(data);
            setTimeout(function () {
                window.location.reload();
            }, 500);
        })
        .catch(error => {
            document.getElementById('file_upload_result').classList.add("form-control");
            document.getElementById('file_upload_result').classList.remove("is-valid");
            document.getElementById('file_upload_result').classList.add("is-invalid");
            document.getElementById('file_upload_result').textContent = 'Upload failed.';
            console.error('Error:', error);
        });
}

async function doActionBtn(action) {
    await populateUserList();
    document.querySelector("#publishModal > div > div > div.modal-footer > button").onclick = function () {
        createTicket(accountId, action);
    }
    $('#publishModal').modal('show');
}

async function doMainButtons() {
    $('table').on('change', 'input[type="checkbox"]', function () {
        var checkboxes = document.querySelectorAll("input[type='checkbox'].dt-checkboxes");
        if (this.checked) {
            for (var i = 0; i < checkboxes.length; i++) {
                if (checkboxes[i] !== this) {
                    checkboxes[i].checked = false;
                }
            }
        }

        $(".publish_file_btn").prop('disabled', true);
        if ($('input[type="checkbox"]:checked').length === 1) {
            $(".publish_file_btn").prop('disabled', false);
        }

        $(".remove_file_btn").prop('disabled', true);
        if ($('input[type="checkbox"]:checked').length === 1) {
            $(".remove_file_btn").prop('disabled', false);
        }
    })
}

async function createTicket(accountId, type = 6) {
    document.querySelector("#publishModal > div > div > div.modal-footer > button").disabled = true;

    accountId = escapeHtml(accountId);

    let allSelectedUsers = [];
    $('.this-user-id:checked').each(function () {
        let thisId = $(this).attr('id');
        thisId = thisId.replace('thisUserId_', '');
        allSelectedUsers.push(thisId);
    })
    allSelectedUsers = allSelectedUsers.join(',');

    var dueDate = new Date();
    dueDate.setDate(dueDate.getDate() + 5);
    var formattedDate = dueDate.toISOString().slice(0, 10);

    var entries = $('#files_table').find('input[type="checkbox"]:checked').map(function () {
        return $(this).val();
    }).get();

    var theTitle = 'New file(s) submission';
    if (type === 7) {
        theTitle = 'New file(s) removal';
    }

    let comments = document.getElementById("publishComments").value

    let form_data = {
        accountId: accountId,
        title: theTitle,
        dueDate: formattedDate,
        priority: 1,
        entryId: entries,
        type: type,
        assignEditor: allSelectedUsers,
        comments: comments,
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
            console.log(entry);
            window.location.replace("/workflow");
        },
        error: function (XMLHttpRequest, textStatus, errorThrown) {
            console.log("ERROR");
            window.location.replace("/workflow");
        }
    });
}

window.addEventListener('DOMContentLoaded', async function main() {

    document.getElementById("file").addEventListener("change", setFull_pathSpan);
    document.getElementById("folder").addEventListener("keyup", setFull_pathSpan);

    $('#files_table').DataTable().clear().draw();
    $('#files_table').DataTable().destroy();

    // Setup - add a text input to each header cell
    $('#files_table thead tr').clone(true).addClass("filters").appendTo('#files_table thead');

    let searchColumns = [1, 2, 3, 4, 5];

    const urlParams = new URLSearchParams(window.location.search);
    const site_id = urlParams.get('siteId');
    const archive = urlParams.get('archive');

    $("#files_table").DataTable({
        dom: "Brtip",
        buttons: {
            buttons: [{text: "Export", extend: "csv", filename: "Site Report", className: "btn-export"}],
            dom: {
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
        sAjaxSource: "/files/list_all_files?id=" + site_id + "&archive=" + archive,
        order: [[3, "asc"]],
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
                sClass: "truncate",
                mData: function (source, type, val) {
                    return '<a class="green-link" target="_blank" href="' + unescape(preview_webserver + source["Path"]) + '">' + unescape(source["Path"]) + '</a>';
                }
            },
            {
                aTargets: [2],
                sClass: "truncate",
                mData: function (source, type, val) {
                    return "<span>" + unescape(source["Filename"]) + "</span>";
                }
            },
            {
                aTargets: [3],
                mData: function (source, type, val) {
                    return "<span>" + source["Mime Type"] + "</span>";
                }
            },
            {
                aTargets: [4],
                mData: function (source, type, val) {
                    var userData = source["Created By"].split(", ");
                    var userName = userData[1];
                    var userEmail = userData[2];
                    var displayName = userEmail;
                    if (userName !== userEmail) {
                        displayName = userName + ' (' + userEmail + ')';
                    }

                    return "<span>" + displayName + "</span>";
                }
            },
            {
                aTargets: [5],
                mData: function (source, type, val) {
                    return "<span>" + source["Created"] + "</span>";
                }
            },
            {
                aTargets: [6],
                mData: function (source, type, val) {
                    let actionsButtons = "<a class='btn btn-sm' href='/versions?file_type=asset&file_id=" + source["id"] + "'>Versions</a>";
                    if (archive && archive === "1") {
                        actionsButtons += "<button onclick='restoreDeletedAsset(" + source["id"] + ")' class='btn btn-sm btn-red' style='margin-left:5px'>Restore</button>";
                    }
                    return actionsButtons;
                }
            }
        ],
        fnDrawCallback: function (oSettings) {
            $('input[type="checkbox"]').on('click', function () {
                $("#remove_file_btn").prop('disabled', true);
                $("#publish_file_btn").prop('disabled', true);
                if ($('input[type="checkbox"]:checked').length > 0) {
                    $("#remove_file_btn").prop('disabled', false);
                    $("#publish_file_btn").prop('disabled', false);
                }
            })

        },
        initComplete: function () {
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
    $("#files_table_wrapper > .dt-buttons").appendTo("div.header-btns");
    $(".loadingBg").removeClass("show");


    var upload_files_form = document.getElementById("upload_files_form");

    upload_files_form.addEventListener('submit', function (event) {
        event.preventDefault();

        const formData = new FormData();
        const fileInput = document.getElementById('file');
        const folder = document.getElementById('folder');

        // Check if any file is selected or not
        if (fileInput.files.length > 0) {
            const fullFileName = document.getElementById("file").value.split('\\').pop();

            // Get the file name and extension using the helper function
            const {name, extension} = getFileNameAndExtension(fullFileName);
            const final_extension = extension.trim().split(".")[1]

            // Sanitize only the base name part, preserving the original extension
            const sanitizedFileName = sanitizeFilePath(name) + "." + final_extension;
            const originalFile = fileInput.files[0];

            // Create a new File object with the desired name
            const newFile = new File([originalFile], sanitizedFileName, {
                type: originalFile.type,
                lastModified: originalFile.lastModified
            });

            formData.append('file', newFile);
            formData.append('folder', folder.value);
            if (site_id.trim() === "") {
                formData.append('site_id', site_id);
            }
            formData.append('account_id', accountId);

            upload_file(formData);

        } else {
            document.getElementById('file_upload_result').classList.add("form-control");
            document.getElementById('file_upload_result').classList.remove("is-valid");
            document.getElementById('file_upload_result').classList.add("is-invalid");
            document.getElementById('file_upload_result').textContent = 'Please select a file to upload.';
        }
    });
});

