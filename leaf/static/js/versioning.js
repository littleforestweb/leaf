/*
    Created on : 30 Mar 2024, 15:39:17
    Author     : xhico
*/

async function revert_commit(page_id, commit) {
    console.log("revert_commit - " + page_id + " - " + commit);
    $.ajax({
        type: "POST",
        url: "/api/page_revert",
        contentType: 'application/json',
        data: JSON.stringify({"page_id": page_id, "commit": commit}),
        dataType: 'json',
        cache: false,
        processData: false,
        success: function (entry) {
            console.log("success");
            document.getElementById("versioningNotification").classList.add("bg-success");
            document.getElementById("versioningNotificationMsg").innerHTML = "<span>Page Reverted Successfully</span>"
            $('#versioningNotification').toast('show');
        },
        error: function (XMLHttpRequest, textStatus, errorThrown) {
            console.log("ERROR");
            document.getElementById("versioningNotification").classList.add("bg-danger");
            document.getElementById("versioningNotificationMsg").innerHTML = "<span>Failed to Revert Page</span>"
            $('#versioningNotification').toast('show');
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

window.addEventListener('DOMContentLoaded', async function main() {
    console.log("Starting");
    console.log("Get Page Versions");

    // Reset Table
    $('#table').DataTable().clear().draw();
    $('#table').DataTable().destroy();

    // Setup - add a text input to each header cell
    $('#table thead tr').clone(true).addClass("filters").appendTo('#table thead');

    let searchColumns = [0, 1, 2, 3, 4, 5];

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
        sAjaxSource: "/api/page_versions?page_id=" + page_id,
        autoWidth: true,
        order: [[0, "desc"]],
        stateSave: true,
        aoColumnDefs: [
            {
                aTargets: [0],
                mData: function (source, type, val) {
                    return "<span>" + unescape(source["version"]) + "</span>";
                },
                sortable: true
            },
            {
                aTargets: [1],
                mData: function (source, type, val) {
                    return "<span>" + unescape(source["commit"]) + "</span>";
                }
            },
            {
                aTargets: [2],
                mData: function (source, type, val) {
                    return "<span>" + unescape(source["message"]) + "</span>";
                }
            },
            {
                aTargets: [3],
                mData: function (source, type, val) {
                    return "<span>" + unescape(source["author"]) + "</span>";
                }
            },
            {
                aTargets: [4],
                mData: function (source, type, val) {
                    return "<span>" + unescape(source["date"]) + "</span>";
                }
            },
            {
                aTargets: [5],
                mData: function (source, type, val) {
                    return "<a onclick='revert_commit(\"" + page_id + "\", \"" + source["commit"] + "\")' class='btn btn-sm btn-red'>Revert</a>";
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

            $(".loadingBg").removeClass("show");
        }
    });

    // Clean-up
    $("#table_wrapper > .dt-buttons").appendTo("div.header-btns");
    $(".loadingBg").removeClass("show");
});


