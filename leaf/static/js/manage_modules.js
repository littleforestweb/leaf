/*
    Created on : 23 Jul 2024, 19:11:23
    Author     : joao
*/

async function populateEditModuleModal() {
    $('#editModuleModal form .mb-3 input#e-module_name').val('');
    $('#editModuleModal form .mb-3 textarea#e-html_content').val('');

    let checked_items = $('input[type="checkbox"]:checked');

    const baseUrl = `${window.location.protocol}//${window.location.host}`;
    let item_data = await $.get(`${baseUrl}/api/modules/${checked_items[0].value}?id=${site_id}`, function (result) {
        return result;
    });
    $('#editModuleModal form .mb-3 input#e-module_name').val(item_data[1]);
    $('#editModuleModal form .mb-3 textarea#e-html_content').val(item_data[2]);
}

async function addModule(action) {
    const baseUrl = `${window.location.protocol}//${window.location.host}`;
    accountId = escapeHtml(accountId);
    action = escapeHtml(action);

    if (action === 'save') {
        var form_data = await getFormData('setModule');

        $.ajax({
            type: "POST",
            url: baseUrl + "/set/module?id=" + site_id,
            contentType: 'application/json',
            data: JSON.stringify(form_data),
            dataType: 'json',
            cache: false,
            processData: false,
            success: function (response) {
                $('#addModuleModal').modal('hide');
                $('#addModuleModal form input:not([type="button"])').val('');

                $('#addModuleSuccessNotification').toast('show');

                setTimeout(function () {
                    location.reload(true);
                }, 500);
            },
            error: function (XMLHttpRequest, textStatus, errorThrown) {
                // Hide Create Modal
                $('#addModuleModal').modal('hide');

                // Show Error Modal
                $('#errorModal').modal('show');
            }
        });
    } else {
        $('#addModuleModal').modal('hide');
        $('#addModuleModal form input:not([type="button"])').val('');
    }
}

async function editModule(action) {
    const baseUrl = `${window.location.protocol}//${window.location.host}`;
    accountId = escapeHtml(accountId);
    action = escapeHtml(action);

    if (action === 'edit') {
        var form_data = await getFormData('updateModule');

        let checked_items = $('input[type="checkbox"]:checked');

        fetch(`${baseUrl}/edit/module/${checked_items[0].value}?id=${site_id}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(form_data)
        })
        .then(response => response.json())
        .then(data => {
            $('#editModuleModal').modal('hide');
            $('#editModuleModal form input:not([type="button"])').val('');

            $('#editModuleSuccessNotification').toast('show');

            setTimeout(function () {
                location.reload(true);
            }, 500);
        })
        .catch(error => {
            console.error('Error updating module:', error);
        });

        
    } else {
        $('#addModuleModal').modal('hide');
        $('#addModuleModal form input:not([type="button"])').val('');
    }
}

async function deleteModule(accountId, action) {
    const baseUrl = `${window.location.protocol}//${window.location.host}`;
    let checked_entries = [];
    let checked_entries_str = "";

    $.each($("input:checked"), function (K, V) {
        checked_entries.push(escapeHtml(V.value));
        checked_entries_str += escapeHtml(V.value) + ",";
    });
    checked_entries_str = checked_entries_str.slice(0, -1);

    $.ajax({
        type: "DELETE",
        url: baseUrl + "/delete/modules?id=" + site_id,
        contentType: 'application/json',
        data: JSON.stringify({"module_to_delete": checked_entries_str}),
        dataType: 'json',
        cache: false,
        processData: false,
        success: function (response) {
            $('#table').DataTable().draw();

            $("#delete_module_btn").removeClass("loadingBtn").prop("disabled", false);

            // Hide Modal
            $('#deleteModuleModal').modal('hide');

            // Show success notification
            $('#deleteModuleSuccessNotification').toast('show');

            setTimeout(function () {
                location.reload(true);
            }, 500);
        },
        error: function (XMLHttpRequest, textStatus, errorThrown) {
            $('#errorModal').modal('show');
        }
    });
}


window.addEventListener('DOMContentLoaded', async function main() {
    const baseUrl = `${window.location.protocol}//${window.location.host}`;
    // Reset pagesTable
    $('#table').DataTable().clear().draw();
    $('#table').DataTable().destroy();

    $('#table thead tr').clone(true).addClass('filters').appendTo('#table thead');
    let searchColumns = [1, 2, 3];

    $('#table').DataTable({
        bProcessing: false,
        bServerSide: true,
        sAjaxSource: baseUrl + "/api/modules?id=" + site_id,
        aoColumns: [
            {
                aTargets: [0],
                mData: function (source, type, row) {
                    return "<input type='checkbox' value='" + source[0] + "' >";
                },
                width: "5%",
                orderable: false,
                defaultContent: "<i style='color: #CCC;'>No data</i>",
                sClass: "center"
            },
            {
                aTargets: [1],
                mData: function (source, type, row) {
                    return '<span class="toEdit">' + source[1] + '</span>';
                },
                width: "50%",
                defaultContent: "<i style='color: #CCC;'>No data</i>"
            },
            {
                aTargets: [2],
                mData: function (source, type, row) {
                    if (source[2] !== null) {
                       val = source[2].split(', ');
                        if (val[1] === val[2]) {
                            val = val[1];
                        } else {
                            val = val[1] + "(" + val[2] + ")";
                        } 
                    } else {
                        val = "-";
                    }
                    
                    return val;
                },
                width: "50%",
                defaultContent: "<i style='color: #CCC;'>No data</i>"
            },
            {
                aTargets: [3],
                mData: function (source, type, row) {
                    return '<span class="hidden">' + Date.parse(source[3]) + "</span><span class='toEdit'>" + source[3] + "</span>";
                },
                width: "30%",
                defaultContent: "<i style='color: #CCC;'>No data</i>"
            }
        ],
        dom: 'Brtip',
        language: {"emptyTable": "No data available"},
        order: [3, "asc"],
        pageLength: 100,
        aLengthMenu: [[50, 100, 200], [50, 100, 200]],
        autoWidth: true,
        stateSave: true,
        buttons: {
            buttons: [
                {
                    text: 'Export',
                    extend: 'csv',
                    filename: 'Modules Report',
                    className: 'btn-export'
                }
            ],
            dom: {
                button: {
                    className: 'btn'
                }
            }
        },
        header: function (html, idx, node) {
            return $('input', node).attr('placeholder');
        },
        stateSaveParams: function (settings, data) {
            //console.log(data);
            //delete data.search;
        },
        fnDrawCallback: function (oSettings) {

            $('input[type="checkbox"]').on('click', function () {
                $(".deleteButton").prop('disabled', true);
                $(".previewButton").prop('disabled', true);
                if ($('input[type="checkbox"]:checked').length > 0) {
                    $(".deleteButton").prop('disabled', false);
                    $(".previewButton").prop('disabled', false);
                }

                $(".editButton").prop('disabled', true);
                $('input[type="checkbox"]').not(this).prop('checked', false);
                $(".editButton").prop('disabled', false);
            })

        },
        initComplete: function () {
            // For each column
            var api = this.api();
            api.columns().eq(0).each(function (colIdx) {
                // Set the header cell to contain the input element
                var cell = $('.filters th').eq($(api.column(colIdx).header()).index());
                if (searchColumns.includes(colIdx)) {
                    $(cell).html('<input id="search_col_index_' + colIdx + '" type="text" oninput="stopPropagation(event)" onclick="stopPropagation(event);" class="form-control form-control-sm" placeholder="Search" />');
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

            var api = this.api();
            var state = api.state.loaded();
            if (state) {
                api.columns().eq(0).each(function (colIdx) {
                    var colSearch = state.columns[colIdx].search;

                    if (colSearch.search) {
                        $('input', $('.filters th')[colIdx]).val(colSearch.search.replace('((((', '').slice(0, -4));
                    }
                });
                api.draw();
            }

            doMainButtons();
            $(".loadingBg").removeClass("show");

        }
    });
    $("#table_wrapper > .dt-buttons").appendTo("div.header-btns");

    // $('#table_wrapper > .dt-buttons').appendTo("div.header-btns .actions_container");
    // if ($("div.header-btns .dataTables_length").length > 0) {
    //     $("div.header-btns .dataTables_length").remove();
    // }

    // $(".dataTables_length").addClass('btn pull-right').appendTo('div.header-btns');
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
            formdata[element.name] = formdata[element.name].replace(/<[^>]+style="[^"]*"[^>]*>/g, function (match) {
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
