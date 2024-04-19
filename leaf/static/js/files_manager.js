/*
    Created on : 18 Apr 2024, 11:10:23
    Author     : joao
*/

window.addEventListener('DOMContentLoaded', async function main() {
    async function joinPath(...segments) {
        return segments.map(segment => segment.replace(/(^\/|\/$)/g, '')).join('/');
    }

    function sanitizeFilePath(filePath) {
        return filePath.replace(/[^a-zA-Z0-9\-._\/]/g, '_');
    }

    async function setFull_pathSpan() {
        let folder = await sanitizeFilePath(document.getElementById("folder").value);
        let filename = await sanitizeFilePath(document.getElementById("file").value.split('\\').pop());
        document.getElementById("full_path").value = await joinPath(folder, filename);
    }

    document.getElementById("file").addEventListener("change", setFull_pathSpan);
    document.getElementById("folder").addEventListener("keyup", setFull_pathSpan);

    $('#files_table').DataTable().clear().draw();
    $('#files_table').DataTable().destroy();

    // Setup - add a text input to each header cell
    $('#files_table thead tr').clone(true).addClass("filters").appendTo('#files_table thead');

    let searchColumns = [1, 2, 3, 4, 5];

    const urlParams = new URLSearchParams(window.location.search);
    const site_id = urlParams.get('siteId');

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
        sAjaxSource: "/files/list_all_files?id=" + site_id,
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
                    return "<span>" + unescape(source["Path"]) + "</span>";
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
            formData.append('file', fileInput.files[0]);
            formData.append('folder', folder.value);
            formData.append('site_id', site_id);
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

function removeFiles(accountId, button) {
    accountId = escapeHtml(accountId);
    var entriesToDelete = $('#files_table').find('input[type="checkbox"]:checked').map(function () {
        return $(this).val();
    }).get();

    form_data = {
        account_id: accountId,
        entries_to_delete: entriesToDelete
    }

    $.ajax({
        type: "POST",
        url: "/files/remove_files",
        contentType: 'application/json',
        data: JSON.stringify(form_data),
        dataType: 'json',
        cache: false,
        processData: false,
        success: function (status) {
            setTimeout(function () {
                window.location.reload();
            }, 500);
        },
        error: function (XMLHttpRequest, textStatus, errorThrown) {
            console.log("ERROR");
            setTimeout(function () {
                window.location.reload();
            }, 500);
        }
    });
}

function createPublishTicket(accountId) {

    accountId = escapeHtml(accountId);

    var dueDate = new Date();
    dueDate.setDate(dueDate.getDate() + 5);
    var formattedDate = dueDate.toISOString().slice(0, 10);

    var entries = $('#files_table').find('input[type="checkbox"]:checked').map(function () {
        return $(this).val();
    }).get();

    form_data = {
        accountId: accountId,
        title: 'New file(s) submition',
        dueDate: formattedDate,
        priority: 1,
        entryId: entries,
        type: 6
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

