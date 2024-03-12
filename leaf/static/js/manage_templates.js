/*
    Created on : 23 Fev 2024, 09:21:19
    Author     : joao
*/

async function addTemplate(action) {

    accountId = escapeHtml(accountId);
    action = escapeHtml(action);

    if (action === 'save') {
        var form_data = await getFormData('setTemplate-no_list');

        $.ajax({
            type: "POST",
            url: "/set/template/" + accountId + "/____no_list_selected____",
            contentType: 'application/json',
            data: JSON.stringify(form_data),
            dataType: 'json',
            cache: false,
            processData: false,
            success: function (response) {
                $('#addTemplateModal').modal('hide');
                $('#addTemplateModal form input:not([type="button"])').val('');

                $('#addTemplateSuccessNotification').toast('show');

                location.reload(true);
            },
            error: function (XMLHttpRequest, textStatus, errorThrown) {
                // Hide Create Modal
                $('#addTemplateModal').modal('hide');

                // Show Error Modal
                $('#errorModal').modal('show');
            }
        });
    } else {
        $('#addTemplateModal').modal('hide');
        $('#addTemplateModal form input:not([type="button"])').val('');
    }
}

async function deleteTemplate(accountId, action) {

    let checked_entries = [];
    let checked_entries_str = "";

    $.each($("input:checked"), function (K, V) {
        checked_entries.push(escapeHtml(V.value));
        checked_entries_str += escapeHtml(V.value) + ",";
    });
    checked_entries_str = checked_entries_str.slice(0, -1);

    $.ajax({
        type: "POST",
        url: "/delete/template/" + accountId,
        data: {
            "template_to_delete": checked_entries_str
        },
        success: function (response) {
            $('#table').DataTable().draw();

            $("#delete_template_btn").removeClass("loadingBtn").prop("disabled", false);

            // Hide Modal
            $('#deleteTemplateModal').modal('hide');

            // Show success notification
            $('#deleteTemplateSuccessNotification').toast('show');

            setTimeout(function () {
                location.reload(true);
            }, 1000);
        },
        error: function (XMLHttpRequest, textStatus, errorThrown) {
            $('#errorModal').modal('show');
        }
    });
}


window.addEventListener('DOMContentLoaded', async function main() {

    // Reset pagesTable
    $('#table').DataTable().clear().draw();
    $('#table').DataTable().destroy();

    // Get pagesJSON
    let jsonAllTemplate = await $.get("/api/get_all_templates/" + accountId, function (result) {
        return result;
    });

    // Set dataset
    let dataset = [];
    json = jsonAllTemplate.columns;
    for (let i = 0; i < json.length; i++) {
        let entry = json[i];
        let id = entry[0];
        let in_lists = entry[1];
        let template = entry[2];
        let template_location = entry[3];
        let created_by = entry[4];
        let created = entry[5];
        let modified = entry[6];
        dataset.push([[id, template], [id, template, created, modified], template_location, in_lists, created_by, created, modified, id]);
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
                    filename: 'Templates Report',
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
                    return "<input type='checkbox' value='" + data[0] + "' >";
                },
            },
            {
                width: "50%",
                targets: 1,
                render: function (data, type, row) {
                    return '<a href="/templates/' + data[0] + '"><span class="toEdit">' + data[1] + '</span></a>';
                },
            },
            {
                width: "50%",
                targets: 2,
                render: function (data, type, row) {
                    return data;
                },
            },
            {
                width: "50%",
                targets: 3,
                render: function (data, type, row) {
                    return data;
                },
            },
            {
                width: "50%",
                targets: 4,
                render: function (data, type, row) {
                    return data;
                },
            },
            {
                width: "30%",
                targets: 5,
                render: function (data, type, row) {
                    return '<span class="hidden">' + Date.parse(data) + "</span><span class='toEdit'>" + data + "</span>";
                },
            },
            {
                width: "30%",
                targets: 6,
                render: function (data, type, row) {
                    return '<span class="hidden">' + Date.parse(data) + "</span><span class='toEdit'>" + data + "</span>";
                },
            },
            {
                width: "20%",
                targets: 7,
                render: function (data, type, row) {
                    return '<a href="/templates/' + data + '">View</a>';
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

async function getFormData(formid) {

    formid = escapeHtml(formid);

    var form = document.getElementById(formid);

    var allFormElements = Array.from(form.querySelectorAll('input:not([type="search"]):not([type="checkbox"]):not(.file-name-reference):not(.clear-btn):not(.ck-hidden):not(.ck-input):not(.hidden-field):not(.document-remover), select, textarea, div.form-select')).filter(element => element.id);
    let formdata = {};

    var mandatoryElementsNotCompleted = [];

    for (const element of allFormElements) {
        if (element.classList.value.includes('mandatoryField') || (element.closest('textarea') && element.closest('textarea').classList.value.includes('mandatoryField'))) {
            mandatoryElementsNotCompleted.push(element.id);
        }

        if (!element.type) {

            var yourArray = [];
            var allChildNodes = $(element)[0].childNodes;
            for (const childElement of allChildNodes) {
                if ($(childElement).find('input[type=checkbox]:checked').length > 0) {
                    yourArray.push($(childElement).find('input').val().replace(/,/g, '&comma;').replace(/\'/g, "’"));
                }
            }

            formdata[element.id] = yourArray;

        } else if (element.classList.contains('text-editor')) {
            formdata[element.name] = CKEDITOR.instances[element.id].getData().replace(/,/g, '&comma;').replace(/\\/g, "__BACKSLASH__TO_REPLACE_ON_WEB__").replace(/\'/g, "’").replace(/\xA0/g, '');
            formdata[element.name] = formdata[element.name].replace(/<[^>]+style="[^"]*"[^>]*>/g, function(match) {
                return match.replace(/style="[^"]*"/g, '');
            });
        } else if (element.type === 'checkbox') {
            formdata[element.name] = escapeHtml(element.checked);
        } else if (element.type === 'file') {

            if (element.files.length > 0) {
                var form_data_single_file = new FormData();
                form_data_single_file.append("files[]", element.files[0]);

                var lastIndexOfFileName = $(element).parent().find('.file-name-reference').text();
                var lastIndexOfFileNamePath = $(element).parent().find('#mb3_img-document').attr('src');

                if (lastIndexOfFileName) {
                    lastIndexOfFileName = lastIndexOfFileName.substring(lastIndexOfFileName.lastIndexOf('/') + 1);
                } else {
                    lastIndexOfFileName = '';
                }

                if (lastIndexOfFileNamePath) {
                    lastIndexOfFileNamePath = lastIndexOfFileNamePath.substring(0, lastIndexOfFileNamePath.indexOf(lastIndexOfFileName));
                } else {
                    lastIndexOfFileNamePath = '';
                }

                form_data_single_file.append('lastIndexOfFileName', lastIndexOfFileName);
                form_data_single_file.append('lastIndexOfFileNamePath', lastIndexOfFileNamePath);

                var returnedElement = await uploadSingleFile(form_data_single_file);
                formdata[element.name] = returnedElement.url;
            } else {
                if (element.parentNode.querySelector('.hidden-field')) {
                    formdata[element.name] = element.parentNode.querySelector('.hidden-field').value;
                } else {
                    formdata[element.name] = '';
                }
            }

        } else if (element.options) {
            var selected = [...element.selectedOptions].map(option => option.value);
            //var selected = [...element.options].filter(option => option.selected).map(option => option.value);
            if (selected.length > 1) {
                formdata[element.name] = escapeHtml(selected);
            } else {
                formdata[element.name] = escapeHtml(element.value);
            }

        } else {
            formdata[element.name] = escapeHtml(element.value.replace(/,/g, '&comma;').replace(/\\/g, "__BACKSLASH__TO_REPLACE_ON_WEB__").replace(/\'/g, "’"));
        }
    }

    var mandatoryElementsNotCompletedToReturn = [];
    if (mandatoryElementsNotCompleted.length > 0) {
        for (var key of mandatoryElementsNotCompleted) {
            if (
                (typeof 'string' && formdata[key] === "") ||
                (typeof 'object' && formdata[key].length < 1) ||
                (typeof 'string' && formdata[key] === '<p class="ck-placeholder" data-placeholder="Start typing.."><br data-cke-filler="true"></p>')
            ) {
                mandatoryElementsNotCompletedToReturn.push(key);
            }
        }
    }

    if (mandatoryElementsNotCompletedToReturn.length > 0) {
        return [{'mandatoryFields': true, mandatoryElementsNotCompletedToReturn}];
    } else {
        return formdata;
    }
}

async function goToEditTemplate(accountId) {
    let checked_entries = [];
    let checked_entries_str = "";

    $.each($("input:checked"), function (K, V) {
        checked_entries.push(escapeHtml(V.value));
        checked_entries_str += escapeHtml(V.value) + ",";
    });
    checked_entries_str = checked_entries_str.slice(0, -1);

    window.location.href = '/templates/' + checked_entries_str;
}

async function getAvailableFields(accountId, reference = false) {
    if (reference) {
        let jsonAvailableFields = await $.get("/api/get_available_fields/" + accountId + "/" + reference, function (result) {
            return result;
        });
    } else {
        // Getting logic ready
    }
    
    jsonAvailableFields = jsonAvailableFields.columns;

    return jsonAvailableFields;
}
