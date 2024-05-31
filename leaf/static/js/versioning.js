/*
    Created on : 30 Mar 2024, 15:39:17
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
        $(".reviewChangesBtn").prop('disabled', true);
        if ($('input[type="checkbox"]:checked').length === 2) {
            $(".reviewChangesBtn").prop('disabled', false);
        }
    })
}

function base64Encode(str) {
    // Convert the string to an array of 8-bit unsigned integers
    const uint8Array = new TextEncoder().encode(str);
    // Create a string of bytes
    let binary = '';
    const len = uint8Array.byteLength;
    for (let i = 0; i < len; i++) {
        binary += String.fromCharCode(uint8Array[i]);
    }
    // Convert the binary string to base64
    return btoa(binary);
}

async function compareVersions() {
    let checkboxes = document.querySelectorAll("input[type='checkbox'].dt-checkboxes");
    let checkedCheckboxes = Array.from(checkboxes).filter(checkbox => checkbox.checked);
    let commit_ids = [];
    for (let checkbox of checkedCheckboxes) {
        commit_ids.push(checkbox.value)
    }
    window.location.href = "/versions_diff?file_type=" + file_type + "&file_id=" + file_id + "&commit_id_1=" + commit_ids[0] + "&commit_id_2=" + commit_ids[1];
}

async function revert_commit(file_id, commit) {
    console.log("revert_commit - " + file_id + " - " + commit);
    $.ajax({
        type: "POST",
        url: "/api/version_revert",
        contentType: 'application/json',
        data: JSON.stringify({"file_type": file_type, "file_id": file_id, "commit": commit}),
        dataType: 'json',
        cache: false,
        processData: false,
        success: function (entry) {
            console.log("success");
            document.getElementById("versioningNotification").classList.add("bg-success");
            document.getElementById("versioningNotificationMsg").innerHTML = "<span>Version reverted successfully</span>"
            $('#versioningNotification').toast('show');
        },
        error: function (XMLHttpRequest, textStatus, errorThrown) {
            console.log("ERROR");
            document.getElementById("versioningNotification").classList.add("bg-danger");
            document.getElementById("versioningNotificationMsg").innerHTML = "<span>Failed to revert version</span>"
            $('#versioningNotification').toast('show');
        }
    });
}

async function open_file(file_id, commit) {
    console.log("open_file - " + file_id + " - " + commit);
    $.ajax({
        type: "POST",
        url: "/api/get_file_content_from_commit",
        contentType: 'application/json',
        data: JSON.stringify({"file_type": file_type, "file_id": file_id, "commit_id": commit}),
        dataType: 'json',
        cache: false,
        processData: false,
        success: function (entry) {
            let file_content = entry["file_content"];
            let file_mime_type = entry["file_mime_type"];

            // Parse Mime Types
            if (file_mime_type === "application/json") {
                file_content = "<html><body><pre>" + JSON.stringify(JSON.parse(file_content), null, 2) + "</pre></body></html>"
            }

            // Open Tab
            let newWindow = window.open();
            newWindow.document.write(file_content);
            newWindow.document.close();
        },
        error: function (XMLHttpRequest, textStatus, errorThrown) {
            console.log("ERROR");
            document.getElementById("versioningNotification").classList.add("bg-danger");
            document.getElementById("versioningNotificationMsg").innerHTML = "<span>Couldn't open version</span>"
            $('#versioningNotification').toast('show');
        }
    });
}

window.addEventListener('DOMContentLoaded', async function main() {
    console.log("Starting");
    console.log("Get Versions");

    // Reset Table
    $('#table').DataTable().clear().draw();
    $('#table').DataTable().destroy();

    // Setup - add a text input to each header cell
    $('#table thead tr').clone(true).addClass("filters").appendTo('#table thead');

    let searchColumns = [1, 3, 4, 5];

    $("#table").DataTable({
        dom: "Brtip",
        buttons: {
            buttons: [{
                text: "Export",
                extend: "csv",
                filename: "Page Versions Report",
                className: "btn-export"
            }],
            dom: {
                button: {
                    className: "btn"
                }
            }
        },
        language: {"emptyTable": "No data available"},
        bProcessing: false,
        bServerSide: true,
        sPaginationType: "full_numbers",
        lengthMenu: [[50, 100, 250], [50, 100, 250]],
        sAjaxSource: "/api/versions?file_type=" + file_type + "&file_id=" + file_id,
        autoWidth: false,
        order: [[0, "desc"]],
        stateSave: true,
        aoColumnDefs: [
            {
                aTargets: [0],
                mData: function (source, type, val) {
                    return "<input class='dt-checkboxes' id='checkbox_" + source["version"] + "' value='" + source["commit"] + "' type='checkbox'>";
                }
            },
            {
                aTargets: [1],
                mData: function (source, type, val) {
                    return "<span>" + unescape(source["version"]) + "</span>";
                }
            },
            {
                aTargets: [2],
                mData: function (source, type, val) {
                    return "<a class='green-link' href='#' onclick='open_file(\"" + file_id + "\", \"" + source["commit"] + "\")'>" + file_path + "</a>";
                }
            },
            {
                aTargets: [3],
                mData: function (source, type, val) {
                    return "<span>" + unescape(source["message"]) + "</span>";
                }
            },
            {
                aTargets: [4],
                mData: function (source, type, val) {
                    return "<span>" + unescape(source["author_name"]) + " (" + unescape(source["author_email"]) + ")" + "</span>";
                }
            },
            {
                aTargets: [5],
                mData: function (source, type, val) {
                    return "<span>" + unescape(source["date"]) + "</span>";
                }
            },
            {
                aTargets: [6],
                mData: function (source, type, val) {
                    return "<a onclick='revert_commit(\"" + file_id + "\", \"" + source["commit"] + "\")' class='btn btn-sm btn-red'>Revert</a>";
                }
            }
        ],
        initComplete: function () {
            // For each column
            var api = this.api();
            var state = api.state.loaded();

            if (state) {
                api.columns().eq(0).each(function (colIdx) {
                    // Set the header cell to contain the input element
                    var cell = $(".filters th").eq($(api.column(colIdx).header()).index());
                    if (searchColumns.includes(colIdx)) {
                        $(cell).html('<input id="search_col_index_' + colIdx + '" type="text" oninput="stopPropagation(event)" onclick="stopPropagation(event);" class="form-control form-control-sm" placeholder="Search" />');
                    } else {
                        $(cell).html('<span></span>');
                    }

                    // On every keypress in this input
                    $("input", $('.filters th').eq($(api.column(colIdx).header()).index())).on("keyup", function (e) {
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

                api.columns().eq(0).each(function (colIdx) {
                    var colSearch = state.columns[colIdx].search;

                    if (colSearch.search) {
                        $('input', $('.filters th')[colIdx]).val(colSearch.search);
                    }
                });
            } else {
                api.draw();
            }
        },
        drawCallback: function () {
            // Reapply custom highlighting and modifications here...
            let latestRow = document.querySelector("#checkbox_" + this.api().rows().count()).parentElement.parentElement;
            latestRow.classList.add("isGreen");
            latestRow.children[1].innerText += " (Latest)";
        }
    });

    // Add Header Btns
    $("#table_wrapper > .dt-buttons").appendTo("div.header-btns");
    doMainButtons();

    // Remove Loading
    $(".loadingBg").removeClass("show");
});


