/*
    Created on : 03 May 2022, 17:57
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

window.addEventListener('DOMContentLoaded', async function main() {
    // Reset Table
    $('#table').DataTable().clear().draw();
    $('#table').DataTable().destroy();

    let json = await $.get("/api/get_workflows", function (result) {
        return result;
    });

    // Set dataset
    let dataset = [];
    json = json["workflows"];
    for (let i = 0; i < json.length; i++) {
        let entry = json[i];
        let id = entry["id"];
        let title = entry["title"];
        let startUser = entry["startUser"];
        let assignEditor = entry["assignEditor"];
        let comments = entry["comments"];
        let submittedDate = entry["submittedDate"];
        let dueDate = entry["dueDate"];
        let priority = entry["priority"];
        let attachments = entry["attachments"];
        let status = entry["status"];
        let type = entry["type"];
        let tags = entry["tags"];
        let statusMessage = entry["statusMessage"];

        dataset.push([id, id, title, startUser, assignEditor, comments, submittedDate, dueDate, [id, attachments], tags, type, priority, status, [id, status, statusMessage]]);
    }

    // Setup - add a text input to each header cell
    $('#table thead tr').clone(true).addClass('filters').appendTo('#table thead');
    let searchColumns = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12];

    $('#table').DataTable({
        dom: 'Brtip',
        buttons: {
            buttons: [{text: 'Export', extend: 'csv', filename: 'Workflow Report', className: 'btn-export'}],
            dom: {
                button: {
                    className: 'btn'
                }
            }
        },
        paginate: false,
        language: {"emptyTable": "No data available in table"},
        order: [[1, "desc"]],
        data: dataset,
        autoWidth: false,
        fnDrawCallback: function (oSettings) {
            $('input[type="checkbox"]').on('click', function () {
                $(".deleteButton").prop('disabled', true);
                if ($('input[type="checkbox"]:checked').length > 0) {
                    $(".deleteButton").prop('disabled', false);
                }
                $('input[type="checkbox"]').not(this).prop('checked', false);
            })

        },
        fnRowCallback: function (nRow, mData, iDisplayIndex) {
            if (mData[13] && mData[13][2]) {
                var thisStatusAction = mData[13][2];
                var thisStatusActionColor = "isWhite";
                if (thisStatusAction === 'Overdue') {
                    thisStatusActionColor = "isRed";
                }
                if (thisStatusAction === 'At risk') {
                    thisStatusActionColor = "isOrange";
                }

                if (mData[12] === "Approved" || mData[12] === '6') {
                    thisStatusActionColor = "isGreen";
                }
                if (mData[12] === '7') {
                    thisStatusActionColor = "isYellow";
                }

                $(nRow).addClass(thisStatusActionColor);
            }
        },
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

            $(".loadingBg").removeClass("show");
        }, "columnDefs": [{
            orderable: false, className: "center", "targets": 0, "render": function (data, type, row) {
                return "<input class='dt-checkboxes' id='checkbox_" + data + "' type='checkbox' value='" + data + "' />";
            }
        }, {
            "targets": 1, "render": function (data, type, row) {
                return "<span>" + data + "</span>";
            },
        }, {
            "targets": 2, "render": function (data, type, row) {
                return "<span>" + (data ? data : '<i style="color:#a5a5a5">No title</i>') + "</span>";
            },
        }, {
            "targets": 3, "render": function (data, type, row) {
                return "<span>" + data + "</span>";
            },
        }, {
            "className": "hidden",
            "targets": 4, "render": function (data, type, row) {
                return "<span>" + data + "</span>";
            },
        }, {
            "className": "truncate hidden",
            "targets": 5, "render": function (data, type, row) {
                return "<span>" + data + "</span>";
            },
        }, {
            "targets": 6, "render": function (data, type, row) {
                // var dateObject = new Date(data);
                // var formattedDate = dateObject.toISOString().slice(0, 10);
                const date = new Date(data);
                const formattedDate = date.toLocaleString('en-GB', dateOptions).replace(/ at /g, '<br>').replace(/ am/g, 'am').replace(/ pm/g, 'pm');
                return "<span>" + formattedDate + "</span>";
            },
        }, {
            "className": "hidden",
            "targets": 7, "render": function (data, type, row) {
                var dateObject = new Date(data);
                var formattedDate = dateObject.toISOString().slice(0, 10);
                return "<span>" + formattedDate + "</span>";
            },
        }, {
            "className": "hidden",
            "targets": 8, "render": function (data, type, row) {
                if (data[1]) {
                    dataArray = data[1].split(";");
                }
                var fullItems = '';
                if (data[1]) {
                    for (var item of dataArray) {
                        fullItems += "<span class='table_file_container'><span class='table_file_container_overlay' onclick='doSlideShow(\"" + data[0] + "\", \"" + data[1] + "\")'></span>" + (item ? (item.endsWith('.pdf') ? '<embed style="display: inline-block; margin: 0 auto; float: none;" width="70px" height="100px" src="' + item + '"></embed>' : '<img style="width: 70px;display: inline-block; margin: 0 auto; float: none;" src="' + item + '" />') : '<i style="color:#a5a5a5">No attachments</i>') + "</span>";
                    }
                    return fullItems;
                } else {
                    return '<i style="color:#a5a5a5">No attachments</i>';
                }
            },
        }, {
            "className": "hidden",
            "targets": 9, "render": function (data, type, row) {
                if (data && data.toLowerCase().trim() !== 'none') {
                    return "<span>" + data + "</span>";
                } else {
                    return '<i style="color:#a5a5a5">No tags</i>';
                }
            },
        }, {
            "className": "hidden",
            "targets": 10, "render": function (data, type, row) {
                return "<span>" + (data === 2 ? 'Task' : 'Deployment') + "</span>";
            },
        }, {
            "targets": 11, "render": function (data, type, row) {
                return "<span>" + (data === 2 ? 'Urgent' : 'Standard') + "</span>";
            },
        }, {
            "targets": 12, "render": function (data, type, row) {
                var currentStatus = "New request";
                if (data === "2") {
                    currentStatus = "In progress";
                } else if (data === "3") {
                    currentStatus = "Sent back for clarification";
                } else if (data === "4") {
                    currentStatus = "Send back for review";
                } else if (data === "5") {
                    currentStatus = "Approved and awaiting deployment";
                } else if (data === "Approved" || data === "6") {
                    currentStatus = "Complete";
                } else if (data === "7") {
                    currentStatus = "Waiting to be published";
                } else if (data === "Rejected") {
                    currentStatus = "Rejected";
                }

                return "<span>" + currentStatus + "</span>";
            },
        }, {
            "targets": 13, "render": function (data, type, row) {
                let elem = "<a class='btn btn-sm' href='workflow_details?id=" + data[0] + "'>Review</a><br>";
                // if (data[1] !== "Approved" && data[1] !== "Rejected") {
                //     elem += "<a class='green-link' href='#' onclick='setStatus(\"Approve\", " + data[0] + ")'>Approve</a><br><a class='green-link' href='#' onclick='setStatus(\"Reject\" ," + data[0] + ")'>Reject</a>";
                // }

                return elem
            },
        }]
    });
    $("#table_wrapper > .dt-buttons").appendTo("div.header-btns");
});

let slideIndex = 1;

function doSlideShow(id, attachments) {
    $('.slideshow-container-background').remove();
    var slideShowContainer = '';

    slideShowContainer += '<div id="slideShow_' + id + '" class="slideshow-container-background"><div class="slideshow-container">';

    var attachmentsArray = attachments.split(";");
    for (var item of attachmentsArray) {
        slideShowContainer += '<div class="mySlides">' +
            (item.endsWith('.pdf') ? '<embed src="' + item + '" type="application/pdf"></embed>' : '<img src="' + item + '" />') +
            '</div>';
    }

    slideShowContainer += '<a class="prev" onclick="plusSlides(-1, \'slideShow_' + id + '\')">&#10094;</a>' +
        '<a class="next" onclick="plusSlides(1, \'slideShow_' + id + '\')">&#10095;</a>' +
        '</div>' +
        '<br>' +
        '<div class="dots_container">';

    var countingItems = 0;
    for (var item of attachmentsArray) {
        countingItems = countingItems + 1;
        slideShowContainer += '<span class="dot" onclick="currentSlide(' + countingItems + ', \'slideShow_' + id + '\')"></span>';
    }

    slideShowContainer += '</div></div>';
    document.getElementById('slider_main_container').innerHTML = slideShowContainer;

    showSlides('slideShow_' + id, slideIndex);

    $('.slideshow-container-background').on('click', function () {
        if (event.target.id === "slideShow_" + id) {
            $('.slideshow-container-background').remove();
        }
    })
}

async function deleteWorkflowEntries(accountId, type, thisButton) {
    thisButton.classList.add('disabled');
    let checked_entries = [];
    let checked_entries_str = "";

    $.each($("input.dt-checkboxes:checked"), function (K, V) {
        checked_entries.push(V.value);
        checked_entries_str += V.value + ",";
    });
    checked_entries_str = checked_entries_str.slice(0, -1);

    // Post
    $.ajax({
        type: "POST",
        url: "/workflow/delete",
        data: {
            "entries_to_delete": checked_entries_str
        },
        success: function (entry) {
            location.reload(true);
        },
        error: function (XMLHttpRequest, textStatus, errorThrown) {
            // Hide Create Modal
            $('#deleteDynamicListsModal').modal('hide');
        }
    });
}

function plusSlides(n, id) {
    showSlides(id, slideIndex += n);
}

function currentSlide(n, id) {
    showSlides(id, slideIndex = n);
}

function showSlides(id, n) {
    let slides = document.getElementById(id).getElementsByClassName("mySlides");
    let dots = document.getElementById(id).getElementsByClassName("dot");

    let i;
    if (n > slides.length) {
        slideIndex = 1
    }
    if (n < 1) {
        slideIndex = slides.length
    }
    for (i = 0; i < slides.length; i++) {
        slides[i].style.display = "none";
    }
    for (i = 0; i < dots.length; i++) {
        dots[i].className = dots[i].className.replace(" active", "");
    }
    slides[slideIndex - 1].style.display = "block";
    dots[slideIndex - 1].className += " active";
}

function doRefreshPage() {
    location.reload(true);
}

const dateOptions = {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
    hour: 'numeric',
    minute: 'numeric',
    hour12: true
};
