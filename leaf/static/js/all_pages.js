/*
    Created on : 02 Mar 2022, 09:59:17
    Author     : xhico
*/

window.addEventListener('DOMContentLoaded', async function main() {
    console.log("Starting");

    console.log("Get All Pages");

    // Reset pagesTable
    $('#table').DataTable().clear().draw();
    $('#table').DataTable().destroy();

    // Get pagesJSON
    let json = await $.get("/api/all_pages", function (result) {
        return result;
    });

    // Set dataset
    let dataset = [];
    json = json["pages"];
    for (let i = 0; i < json.length; i++) {
        let entry = json[i];
        let title = entry["title"];
        let url = entry["url"];
        let status = entry["status"];
        dataset.push([title, url, status, url]);
    }

    // Setup - add a text input to each header cell
    $('#table thead tr').clone(true).addClass('filters').appendTo('#table thead');

    // Initialize Errors Table
    $('#table').DataTable({
        dom: 'Brtip', buttons: {
            buttons: [{text: 'Export', extend: 'csv', filename: 'All Pages Report', className: 'btn-export'}], dom: {
                button: {
                    className: 'btn'
                }
            }
        }, paginate: false,
        "language": {"emptyTable": "No data available in table"},
        "order": [[0, "asc"]],
        data: dataset,
        initComplete: function () {
            var api = this.api();

            // For each column
            api.columns().eq(0).each(function (colIdx) {
                // Set the header cell to contain the input element
                var cell = $('.filters th').eq($(api.column(colIdx).header()).index());
                var title = $(cell).text();
                $(cell).html('<input type="text" placeholder="Search" />');

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
        }, "autoWidth": false, "columnDefs": [{
            "width": "40%", "className": "truncate", "targets": 0, "render": function (data, type, row) {
                data = unescape(data);
                return "<span>" + data + "</span>";
            },
        }, {
            "width": "40%", "className": "truncate", "targets": 1, "render": function (data, type, row) {
                let urlOrigin = new URL(data).origin;
                return "<a class='green-link' target='_blank' href='" + data + "'>" + data.replace(urlOrigin, "") + "</a>";
            },
        }, {
            "width": "10%", "targets": 2, "render": function (data, type, row) {
                let colorClass = "";
                data = data.toString();
                if (data.includes("20")) {
                    colorClass = " class='dataGreen'"
                } else if (data.includes("30")) {
                    colorClass = " class='dataOrange'"
                } else if (data.includes("40") || data.includes("50")) {
                    colorClass = " class='dataRed'"
                } else {
                    data = "Couldn't get status code";
                }
                return "<span" + colorClass + ">" + data + "</span>";
            },
        }, {
            "width": "10%", "targets": 3, "render": function (data, type, row) {
                return "<a class='green-link' target='_blank' href='https://inspector.littleforest.co.uk/InspectorWS/Inspector?url=" + data + "'>Inspect</a>" + " | " + "<a class='green-link' target='_blank' href='https://inspector.littleforest.co.uk/InspectorWS/Inspector?url=" + data + "&edit=true'>Edit</a>" + " | " + "<a class='green-link' target='_blank' href=''>Delete</a>" + " | " + "<a class='green-link' target='_blank' href=''>Publish</a>";
            },
        }]
    });
    $("#table_wrapper > .dt-buttons").appendTo("div.header-btns");
});





