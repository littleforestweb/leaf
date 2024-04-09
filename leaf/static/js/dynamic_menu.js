/*
    Created on : 26 Jun 2022, 08:49:12
    Author     : joao
*/

async function populateEditDynamicMenuDialog(accountId, reference, type, itemToSelect = false) {

    accountId = escapeHtml(accountId);
    reference = escapeHtml(reference);
    type = escapeHtml(type);

    $('#editDynamicList form .mb-3 input').html('');
    $('#editDynamicList form .mb-3 textarea').html('');
    $('#editDynamicList form .mb-3 select').html('');
    $('#editDynamicList form .mb-3 .mb3_img').remove('');
    $('#editDynamicList form .mb-3 .ck-editor').remove('');
    $("#editDynamicList form .mb-3 .hidden-field").remove('');
    $("#editDynamicList form .mb-3 .clear-btn").remove('');
    $("#editDynamicList form .mb-3 .file-name-reference").remove('');
    $('#editDynamicList form .mb-3 .form-control.form-search').remove('');
    $('#editDynamicList form .mb-3 .selected-container').remove('');
    $('input[type="checkbox"]').removeAttr('checked');
    let checked_items = $('input[type="checkbox"]').first();
    if (type === 'edit') {
        checked_items = $('input[type="checkbox"]:checked');
    }

    if (checked_items.length < 1) {
        location.reload(true);
    }

    let n_checked_items = checked_items.length;
    let row = checked_items.parent().parent();

    let spans = row.find("span pre span.hidden");
    let mainRowId = row.find('input[type="checkbox"]');
    mainRowId = escapeHtml(mainRowId.val());

    $.fn.modal.Constructor.prototype._enforceFocus = function () {
        var $modalElement = this.$element;
        $(document).on('focusin.modal', function (e) {
            if ($modalElement && $modalElement.length > 0 && $modalElement[0] !== e.target && !$modalElement.has(e.target).length && $(e.target).parentsUntil('*[role="dialog"]').length === 0) {
                $modalElement.focus();
            }
        });
    };

    // Get list configuration
    let jsonConfig = await $.get("/api_menu/get_menu_configuration/" + accountId + "/" + reference, function (result) {
        return result;
    });

    var values = jsonConfig.columns;

    if (values && values[0]) {
        $("#s-template").val(values[0][2]);
        $("#s-parameters").val(values[0][3]);

        var fields = values[0][4].split(';');
        for (var field in fields) {
            $('#s-fields option[value="' + fields[field] + '"]').attr("selected", "selected");
        }

        var mfields = [];
        if (values[0][5]) {
            mfields = values[0][5].split(',');
        }
    }

    $.ajax({
        type: "GET",
        url: "/api_menu/settings/" + accountId,
        success: function (allAccountSettings) {
            var images_webpath = allAccountSettings.images_webpath;
            var original_images_webpath = allAccountSettings.original_images_webpath;
            allAccountSettings = allAccountSettings.settings;

            $("#e-id").val(mainRowId);
            //$("#e-id").prop( "disabled", true );
            if (type === 'add') {
                $("#a-id").prop("disabled", true);
            }

            CKEDITOR.plugins.add("anchor", {
                init: function (editor) {
                    editor.ui.addButton("anchorPluginButton", {
                        label: "Anchor",
                        command: "anchorPluginCommand",
                        icon: "/static/images/anchor-icon.svg",
                        state: function () {
                            if (editor.mode === 'source') {
                                return CKEDITOR.TRISTATE_DISABLED;
                            }
                            return CKEDITOR.TRISTATE_OFF;
                        }
                    });
                    editor.addCommand("anchorPluginCommand", {
                        exec: function (editor) {
                            var anchorName = prompt('Enter anchor name:'); // Prompt the user for anchor name
                            if (anchorName) {
                                var selectedText = editor.getSelection().getNative().toString().trim();

                                var newElement = new CKEDITOR.dom.element('a');
                                newElement.setText(' ');
                                newElement.setAttribute('name', anchorName);
                                newElement.setAttribute('class', "anchor-item-inline");

                                var range = editor.getSelection().getRanges()[0];
                                // if ((range.endOffset - range.startOffset) > 0) {
                                var newRange = range.clone();
                                newRange.collapse(true);
                                newRange.insertNode(newElement);
                                // range.deleteContents();
                                // range.insertNode(newElement);
                                // } else {
                                //    alert('You have to select some text to be able to create an anchor!');
                                // }
                            }
                        }
                    });
                }
            });

            for (x = 0; x < spans.length; x++) {
                if (allAccountSettings && allAccountSettings.length > 0) {
                    for (var f = 0; f < allAccountSettings.length; f++) {
                        var spanId = spans[x].getAttribute("id").split('_pos_')[0];

                        if (allAccountSettings[f][1] === reference && allAccountSettings[f][2] === spanId) {
                            if (allAccountSettings[f][6] && (allAccountSettings[f][6] === "select" || allAccountSettings[f][6] === "multiselect" || allAccountSettings[f][6] === "multi_checkbox")) {
                                $.ajax({
                                    type: "GET",
                                    url: "/api_menus/get_value_columns_with_index/" + accountId + "/" + allAccountSettings[f][3] + "/" + allAccountSettings[f][4] + "/" + allAccountSettings[f][5] + "/" + x + "/" + f,
                                    success: function (allFieldsResponse) {
                                        indexToKeep = allFieldsResponse.indexToKeep;
                                        indexToKeepForAccountSettings = allFieldsResponse.indexToKeepForAccountSettings;
                                        allFieldsResponse = allFieldsResponse.columns;

                                        var thisSpanMenu = (spans[indexToKeep] ? spans[indexToKeep].getAttribute("id").split('_pos_')[0] : '');
                                        var thisSpanId = (spans[indexToKeep] ? spans[indexToKeep].getAttribute("id").split('_pos_')[1] : '');

                                        var mandatoryClass = '';
                                        for (var mfield in mfields) {
                                            if (mfields[mfield] === thisSpanMenu) {
                                                mandatoryClass = 'mandatoryField';
                                            }
                                        }

                                        var thisFieldValue = "";
                                        if (type === 'edit') {
                                            thisFieldValue = $('#' + thisSpanMenu + '_pos_' + thisSpanId).html();
                                        }

                                        if (allAccountSettings[indexToKeepForAccountSettings] && allAccountSettings[indexToKeepForAccountSettings][6] !== "multi_checkbox") {
                                            if (type === 'edit') {
                                                var fieldsDropdown = '<select name="e-' + thisSpanMenu + '" class="form-select form-select-md toCapitalize" id="e-' + thisSpanMenu + '"' + (allAccountSettings[indexToKeepForAccountSettings][6] === "multiselect" ? 'multiple' : '') + '>' + (thisFieldValue && thisFieldValue.length > 0 ? "" : '<option value="" disabled selected>Select option</option>') + '</select>';
                                                $('#e-' + thisSpanMenu).replaceWith(fieldsDropdown);
                                            } else {
                                                var fieldsDropdown = '<select name="a-' + thisSpanMenu + '" class="form-select form-select-md toCapitalize" id="a-' + thisSpanMenu + '"' + (allAccountSettings[indexToKeepForAccountSettings][6] === "multiselect" ? 'multiple' : '') + '>' + (thisFieldValue && thisFieldValue.length > 0 ? "" : '<option value="" disabled selected>Select option</option>') + '</select>';
                                                $('#a-' + thisSpanMenu).replaceWith(fieldsDropdown);
                                            }

                                        } else if (allAccountSettings[indexToKeepForAccountSettings] && allAccountSettings[indexToKeepForAccountSettings][6] === "multi_checkbox") {
                                            if (type === 'edit') {
                                                var fieldsDropdown = (($('#e-search_items_' + thisSpanMenu).length === 0) ? '<input type="search" onkeyup="filterItems(event, this, \'e-' + thisSpanMenu + '\')" class="form-control form-search form-select-md multi_checkbox" placeholder="search ' + thisSpanMenu + '..." id="e-search_items_' + thisSpanMenu + '" />' : '') + '<div name="e-' + thisSpanMenu + '-selected-container" class="selected-container toCapitalize" id="e-' + thisSpanMenu + '-selected-container"></div>' + '<div name="e-' + thisSpanMenu + '" class="form-select form-select-md toCapitalize" id="e-' + thisSpanMenu + '"' + (allAccountSettings[indexToKeepForAccountSettings][6] === "multi_checkbox" ? 'multiple_checkbox' : '') + '>' + (thisFieldValue && thisFieldValue.length > 0 ? "" : '') + '</div>';
                                                $('#e-' + thisSpanMenu).replaceWith(fieldsDropdown);
                                            } else {
                                                var fieldsDropdown = (($('#a-search_items_' + thisSpanMenu).length === 0) ? '<input type="search" onkeyup="filterItems(event, this, \'a-' + thisSpanMenu + '\')" class="form-control form-search form-select-md multi_checkbox" placeholder="search ' + thisSpanMenu + '..." id="a-search_items_' + thisSpanMenu + '" />' : '') + '<div name="a-' + thisSpanMenu + '-selected-container" class="selected-container toCapitalize" id="a-' + thisSpanMenu + '-selected-container"></div>' + '<div name="a-' + thisSpanMenu + '" class="form-select form-select-md toCapitalize" id="a-' + thisSpanMenu + '"' + (allAccountSettings[indexToKeepForAccountSettings][6] === "multi_checkbox" ? 'multiple_checkbox' : '') + '>' + (thisFieldValue && thisFieldValue.length > 0 ? "" : '') + '</div>';
                                                $('#a-' + thisSpanMenu).replaceWith(fieldsDropdown);
                                            }
                                        }

                                        var arrayToCompare = new Array();
                                        var allFieldsResponseDistinct = [...new Map(allFieldsResponse.map((item) => [(item[1] ? item[1].trim().toLowerCase() : item[0].trim().toLowerCase()), item])).values()];

                                        if (allFieldsResponseDistinct.length > 0 && allFieldsResponseDistinct[0][1]) {
                                            allFieldsResponse = allFieldsResponseDistinct.sort((a, b) => (a[1] !== null ? a[1].localeCompare(b[1]) : a[1]));
                                        } else {
                                            allFieldsResponse = allFieldsResponseDistinct.sort((a, b) => (a[0] !== null ? a[0].localeCompare(b[0]) : a[0]));
                                        }

                                        for (var h = 0; h < allFieldsResponseDistinct.length; h++) {
                                            if (allFieldsResponseDistinct[h][0] && !arrayToCompare.includes(allFieldsResponseDistinct[h][0].trim().toLowerCase())) {
                                                arrayToCompare.push(allFieldsResponseDistinct[h][0].trim().toLowerCase());

                                                if (allAccountSettings[indexToKeepForAccountSettings][6] !== "multi_checkbox") {
                                                    if (allFieldsResponseDistinct[h][0].includes("__BACKSLASH__TO_REPLACE__")) {
                                                        var thisValue = allFieldsResponseDistinct[h][0].substring(allFieldsResponseDistinct[h][0].lastIndexOf('__BACKSLASH__TO_REPLACE__') + 25);
                                                        thisValue = thisValue.substring(thisValue.lastIndexOf('\\') + 1).trim().toLowerCase();

                                                        if (allFieldsResponseDistinct[h][1]) {
                                                            var thisLabel = allFieldsResponseDistinct[h][1].substring(allFieldsResponseDistinct[h][1].lastIndexOf('__BACKSLASH__TO_REPLACE__') + 25);
                                                        } else {
                                                            var thisLabel = allFieldsResponseDistinct[h][0].substring(allFieldsResponseDistinct[h][0].lastIndexOf('__BACKSLASH__TO_REPLACE__') + 25);
                                                        }
                                                        thisLabel = thisLabel.substring(thisLabel.lastIndexOf('\\') + 1).trim().replace(/_/g, ' ').replace(/-/g, ' ').replace(/###/g, ' - ');
                                                        thisLabel = (thisLabel ? thisLabel.replace(/&amp;comma;/g, ",").replace(/&comma;/g, ",") : thisValue.replace(/_/g, ' '));

                                                        if (type === 'edit') {
                                                            $('select#e-' + thisSpanMenu).append('<option value="' + thisValue + '">' + thisLabel + '</option>');
                                                        } else {
                                                            $('select#a-' + thisSpanMenu).append('<option value="' + thisValue + '">' + thisLabel + '</option>');
                                                        }
                                                    } else {
                                                        var thisValue = allFieldsResponseDistinct[h][0].trim().toLowerCase();

                                                        if (allFieldsResponseDistinct[h][1]) {
                                                            var thisLabel = allFieldsResponseDistinct[h][1].trim().replace(/_/g, ' ').replace(/-/g, ' ').replace(/###/g, ' - ');
                                                        } else {
                                                            var thisLabel = allFieldsResponseDistinct[h][0].trim().replace(/_/g, ' ').replace(/-/g, ' ').replace(/###/g, ' - ');
                                                        }
                                                        thisLabel = (thisLabel ? thisLabel.replace(/&amp;comma;/g, ",").replace(/&comma;/g, ",") : thisValue.replace(/_/g, ' '));

                                                        if (type === 'edit') {
                                                            $('select#e-' + thisSpanMenu).addClass(mandatoryClass).append('<option value="' + thisValue + '">' + thisLabel + '</option>');
                                                        } else {
                                                            $('select#a-' + thisSpanMenu).addClass(mandatoryClass).append('<option value="' + thisValue + '">' + thisLabel + '</option>');
                                                        }
                                                    }
                                                } else {

                                                    if (allFieldsResponseDistinct[h][0].includes("__BACKSLASH__TO_REPLACE__")) {
                                                        var thisValue = allFieldsResponseDistinct[h][0].substring(allFieldsResponseDistinct[h][0].lastIndexOf('__BACKSLASH__TO_REPLACE__') + 25);
                                                        thisValue = thisValue.substring(thisValue.lastIndexOf('\\') + 1).trim().toLowerCase();

                                                        if (allFieldsResponseDistinct[h][1]) {
                                                            var thisLabel = allFieldsResponseDistinct[h][1].substring(allFieldsResponseDistinct[h][1].lastIndexOf('__BACKSLASH__TO_REPLACE__') + 25);
                                                        } else {
                                                            var thisLabel = allFieldsResponseDistinct[h][0].substring(allFieldsResponseDistinct[h][1].lastIndexOf('__BACKSLASH__TO_REPLACE__') + 25);
                                                        }
                                                        thisLabel = thisLabel.substring(thisLabel.lastIndexOf('\\') + 1).trim().replace(/_/g, ' ').replace(/-/g, ' ').replace(/###/g, ' - ');
                                                        thisLabel = (thisLabel ? thisLabel.replace(/&amp;comma;/g, ",").replace(/&comma;/g, ",") : thisValue.replace(/_/g, ' '));
                                                    } else {
                                                        var thisValue = allFieldsResponseDistinct[h][0].trim().toLowerCase();

                                                        if (allFieldsResponseDistinct[h][1]) {
                                                            var thisLabel = allFieldsResponseDistinct[h][1].trim().replace(/_/g, ' ').replace(/-/g, ' ').replace(/###/g, ' - ');
                                                        } else {
                                                            var thisLabel = allFieldsResponseDistinct[h][0].trim().replace(/_/g, ' ').replace(/-/g, ' ').replace(/###/g, ' - ');
                                                        }
                                                        thisLabel = (thisLabel ? thisLabel.replace(/&amp;comma;/g, ",").replace(/&comma;/g, ",") : thisValue.replace(/_/g, ' '));
                                                    }

                                                    if (type === 'edit') {
                                                        $('div#e-' + thisSpanMenu).addClass(mandatoryClass).append('<div class="mb-3 form-checkbox-containers"><input onclick="clickIt(\'' + thisSpanMenu + '\', \'' + thisValue.replace(/ /g, '_') + '\', \'' + thisLabel + '\', \'' + type + '\')" type="checkbox" value="' + thisValue.replace(/ /g, '_') + '" /><label for="' + thisValue.replace(/ /g, '_') + '">' + thisLabel + '</label></div>');
                                                    } else {
                                                        $('div#a-' + thisSpanMenu).addClass(mandatoryClass).append('<div class="mb-3 form-checkbox-containers"><input onclick="clickIt(\'' + thisSpanMenu + '\', \'' + thisValue.replace(/ /g, '_') + '\', \'' + thisLabel + '\', \'' + type + '\')" type="checkbox" value="' + thisValue.replace(/ /g, '_') + '" /><label for="' + thisValue.replace(/ /g, '_') + '">' + thisLabel + '</label></div>');
                                                    }
                                                }

                                            } else if (allAccountSettings[indexToKeepForAccountSettings][6] === "multiselect") {
                                                if (allFieldsResponseDistinct[h][0]) {
                                                    var thisValue = allFieldsResponseDistinct[h][0].substring(allFieldsResponseDistinct[h][0].lastIndexOf('__BACKSLASH__TO_REPLACE__') + 25);
                                                    thisValue = thisValue.substring(thisValue.lastIndexOf('\\') + 1).trim().toLowerCase();

                                                    if (allFieldsResponseDistinct[h][1]) {
                                                        var thisLabel = allFieldsResponseDistinct[h][1].substring(allFieldsResponseDistinct[h][1].lastIndexOf('__BACKSLASH__TO_REPLACE__') + 25);
                                                    } else {
                                                        var thisLabel = allFieldsResponseDistinct[h][0].substring(allFieldsResponseDistinct[h][0].lastIndexOf('__BACKSLASH__TO_REPLACE__') + 25);
                                                    }
                                                    thisLabel = thisLabel.substring(thisLabel.lastIndexOf('\\') + 1).trim().replace(/_/g, ' ').replace(/-/g, ' ').replace(/###/g, ' - ');
                                                    thisLabel = (thisLabel ? thisLabel.replace(/&amp;comma;/g, ",").replace(/&comma;/g, ",") : thisValue.replace(/_/g, ' '));
                                                    if (thisValue) {
                                                        if (type === 'edit') {
                                                            $('select#e-' + thisSpanMenu).addClass(mandatoryClass).append('<option value="' + thisValue + '">' + thisLabel + '</option>');
                                                        } else {
                                                            $('select#a-' + thisSpanMenu).addClass(mandatoryClass).append('<option value="' + thisValue + '">' + thisLabel + '</option>');
                                                        }
                                                    }
                                                }
                                            } else if (allAccountSettings[indexToKeepForAccountSettings][6] === "multi_checkbox") {

                                                if (allFieldsResponseDistinct[h][0]) {
                                                    var thisValue = allFieldsResponseDistinct[h][0];
                                                    thisValue = thisValue.substring(thisValue.lastIndexOf('\\') + 1).trim().toLowerCase();

                                                    if (allFieldsResponseDistinct[h][1]) {
                                                        var thisLabel = allFieldsResponseDistinct[h][1];
                                                    } else {
                                                        var thisLabel = allFieldsResponseDistinct[h][0];
                                                    }
                                                    thisLabel = thisLabel.substring(thisLabel.lastIndexOf('\\') + 1).trim().replace(/_/g, ' ').replace(/-/g, ' ').replace(/###/g, ' - ');
                                                    thisLabel = (thisLabel ? thisLabel.replace(/&amp;comma;/g, ",").replace(/&comma;/g, ",") : thisValue.replace(/_/g, ' '));
                                                    if (thisValue) {
                                                        if (type === 'edit') {
                                                            $('div#e-' + thisSpanMenu).addClass(mandatoryClass).append('<div class="mb-3 form-checkbox-containers"><input onclick="clickIt(\'' + thisSpanMenu + '\', \'' + thisValue.replace(/ /g, '_') + '\', \'' + thisValueBeautified + '\', \'' + type + '\')" type="checkbox" value="' + thisValue.replace(/ /g, '_') + '" /><label for="' + thisValue.replace(/ /g, '_') + '">' + thisLabel + '</label></div>');
                                                        } else {
                                                            $('div#a-' + thisSpanMenu).addClass(mandatoryClass).append('<div class="mb-3 form-checkbox-containers"><input onclick="clickIt(\'' + thisSpanMenu + '\', \'' + thisValue.replace(/ /g, '_') + '\', \'' + thisValueBeautified + '\', \'' + type + '\')" type="checkbox" value="' + thisValue.replace(/ /g, '_') + '" /><label for="' + thisValue.replace(/ /g, '_') + '">' + thisLabel + '</label></div>');
                                                        }
                                                    }
                                                }
                                            }
                                        }

                                        if (type === 'edit' && allAccountSettings[indexToKeepForAccountSettings] && allAccountSettings[indexToKeepForAccountSettings][6] === "multiselect") {
                                            thisFieldValue = thisFieldValue.replace(/&amp;comma;/g, ',').split(';');
                                            splitArray = thisFieldValue.map(element => element.trim());
                                            var uniqueSet = new Set(splitArray);
                                            thisFieldValue = [...uniqueSet];
                                            for (var i = 0; i < thisFieldValue.length; i++) {
                                                var thisValue = thisFieldValue[i].trim().toLowerCase();
                                                if (thisFieldValue[i].includes('__BACKSLASH__TO_REPLACE__')) {
                                                    thisValue = thisFieldValue[i].substring(thisFieldValue[i].lastIndexOf('__BACKSLASH__TO_REPLACE__') + 25);
                                                }
                                                if (thisFieldValue[i].includes('\\')) {
                                                    thisValue = thisValue.substring(thisValue.lastIndexOf('\\') + 1);
                                                } else {
                                                    thisValue = thisValue.substring(thisValue.lastIndexOf('/') + 1);
                                                }
                                                $('select#e-' + thisSpanMenu + ' option[value="' + thisValue + '"]').attr("selected", "selected");
                                            }
                                        } else if (type === 'edit' && allAccountSettings[indexToKeepForAccountSettings][6] === "multi_checkbox") {
                                            thisFieldValue = thisFieldValue.replace(/&amp;comma;/g, ',').split(';');
                                            splitArray = thisFieldValue.map(element => element.trim());
                                            var uniqueSet = new Set(splitArray);
                                            thisFieldValue = [...uniqueSet];
                                            for (var i = 0; i < thisFieldValue.length; i++) {
                                                var thisValue = thisFieldValue[i].trim().toLowerCase();
                                                var thisValueBeautified = escapeHtml($('div#e-' + thisSpanMenu).find('input[value="' + thisValue.replace(/ /g, '_') + '"]').parent().find('label').text());
                                                if (thisFieldValue[i].includes('__BACKSLASH__TO_REPLACE__')) {
                                                    thisValue = thisFieldValue[i].substring(thisFieldValue[i].lastIndexOf('__BACKSLASH__TO_REPLACE__') + 25);
                                                }
                                                if (thisFieldValue[i].includes('\\')) {
                                                    thisValue = thisValue.substring(thisValue.lastIndexOf('\\') + 1);
                                                } else {
                                                    thisValue = thisValue.substring(thisValue.lastIndexOf('/') + 1);
                                                }

                                                $('div#e-' + thisSpanMenu + ' input[value="' + thisValue.replace(/ /g, '_') + '"]').prop('checked', true);

                                                if (type === 'edit' && thisValue !== '' && thisValueBeautified) {
                                                    $('div#e-' + thisSpanMenu + '-selected-container').append('<span onclick="unclickIt(\'' + thisSpanMenu + '\', \'' + thisValue.replace(/ /g, '_') + '\', \'' + type + '\')" class="added-item-to-multi-checkbox" id="e-added-' + thisValue.replace(/ /g, '_') + '"><button type="button" id="e-remove-' + thisValue.replace(/ /g, '_') + '" class="btn btn-close"></button>' + thisValueBeautified + '<span>');
                                                }
                                            }
                                        } else if (type === 'edit' && allAccountSettings[indexToKeepForAccountSettings] && allAccountSettings[indexToKeepForAccountSettings][6] === "multi_checkbox") {
                                            if (thisFieldValue && thisFieldValue.length > 0) {
                                                var thisValue = escapeHtml(thisFieldValue.replace(/&amp;comma;/g, ',').trim().toLowerCase());
                                                if (thisFieldValue.includes("__BACKSLASH__TO_REPLACE__")) {
                                                    thisValue = thisFieldValue.substring(thisFieldValue.lastIndexOf('__BACKSLASH__TO_REPLACE__') + 25);
                                                }
                                                if (thisFieldValue.includes('\\')) {
                                                    thisValue = thisValue.substring(thisValue.lastIndexOf('\\') + 1);
                                                } else {
                                                    thisValue = thisValue.substring(thisValue.lastIndexOf('/') + 1);
                                                }
                                                $('select#e-' + thisSpanMenu).val(thisValue);
                                            }
                                        }
                                    },
                                    error: function (XMLHttpRequest, textStatus, errorThrown) {
                                        $('#errorModal').modal('show');
                                    }
                                });
                            } else {

                                var thisSpanMenu = spans[x].getAttribute("id").split('_pos_')[0];

                                var mandatoryClass = '';
                                for (var mfield in mfields) {
                                    if (mfields[mfield] === thisSpanMenu) {
                                        mandatoryClass = 'mandatoryField';
                                    }
                                }

                                // Populate edit fields
                                let site_dynamic_menu = escapeHtml(spans[x].textContent.replace(/__BACKSLASH__TO_REPLACE__/g, "\\").replace(/&comma;/g, ','));

                                if (allAccountSettings[f][6] && allAccountSettings[f][6] === "textarea") {
                                    var attrs = {};

                                    $.each($('#e-' + spanId).attributes, function () {
                                        attrs[this.name] = this.value;
                                    });

                                    $('#e-' + spanId).replaceWith($('<textarea name="e-' + spanId + '" class="form-control ' + mandatoryClass + '" id="e-' + spanId + '"></textarea>'));
                                    $('#a-' + spanId).replaceWith($('<textarea name="a-' + spanId + '" class="form-control ' + mandatoryClass + '" id="a-' + spanId + '"></textarea>'));
                                    if (type === 'edit') {
                                        $('#e-' + spanId).val(site_dynamic_menu);
                                    }

                                } else if (allAccountSettings[f][6] && allAccountSettings[f][6] === "input") {
                                    if (type === 'edit') {
                                        $('#e-' + spanId).addClass(mandatoryClass).val(site_dynamic_menu);
                                    } else {
                                        $('#a-' + spanId).addClass(mandatoryClass);
                                    }

                                } else if (allAccountSettings[f][6] && allAccountSettings[f][6] === "wysiwyg") {

                                    if (type === 'edit') {
                                        $('#e-' + spanId).parent().find("div.ck-editor").remove();
                                        $('#e-' + spanId).replaceWith($('<textarea name="e-' + spanId + '" class="form-control text-editor ' + mandatoryClass + '" id="e-' + spanId + '"></textarea>'));
                                        //const sanitizedHtml = sanitizeScripts(site_dynamic_menu);
                                        document.getElementById('e-' + spanId).innerHTML = site_dynamic_menu;

                                        CKEDITOR.replace(document.querySelector('#e-' + spanId), {
                                            fullPage: false,
                                            allowedContent: true,
                                            // on: {
                                            //     instanceReady: function (ev) {
                                            //         ev.editor.setData(site_dynamic_menu);
                                            //     }
                                            // },
                                            toolbar: [
                                                {name: "clipboard", items: ["Cut", "Copy", "Paste", "PasteText", "-", "Undo", "Redo"]},
                                                {name: "basicstyles", items: ["Bold", "Italic", "Underline", "Strike", "-", "RemoveFormat"]},
                                                {name: "paragraph", items: ["NumberedList", "BulletedList", "-", "Outdent", "Indent", "-", "Blockquote", "CreateDiv", "-", "JustifyLeft", "JustifyCenter", "JustifyRight", "JustifyBlock"]},
                                                {name: "links", items: ["Link", "Unlink", "anchorPluginButton"]},
                                                {name: "insert", items: ["Image", "Embed", "Table", "HorizontalRule", "SpecialChar", "inserthtml4x"]},
                                                {name: "tools", items: ["ShowBlocks"]},
                                                {name: "styles", items: ["Styles", "Format"]},
                                                {name: "document", items: ["Source"]}//, "-", "Preview"
                                            ],
                                            extraPlugins: "anchor, inserthtml4x, embed",
                                            filebrowserUploadUrl: "/api/upload?name=fileupload",
                                            embed_provider: '//ckeditor.iframe.ly/api/oembed?url={url}&callback={callback}'
                                        });
                                    } else {

                                        $('#a-' + spanId).parent().find("div.ck-editor").remove();
                                        $('#a-' + spanId).replaceWith($('<textarea name="a-' + spanId + '" class="form-control text-editor ' + mandatoryClass + '" id="a-' + spanId + '"></textarea>'));

                                        CKEDITOR.replace(document.querySelector('#a-' + spanId), {
                                            fullPage: false,
                                            allowedContent: true,
                                            toolbar: [
                                                {name: "clipboard", items: ["Cut", "Copy", "Paste", "PasteText", "-", "Undo", "Redo"]},
                                                {name: "basicstyles", items: ["Bold", "Italic", "Underline", "Strike", "-", "RemoveFormat"]},
                                                {name: "paragraph", items: ["NumberedList", "BulletedList", "-", "Outdent", "Indent", "-", "Blockquote", "CreateDiv", "-", "JustifyLeft", "JustifyCenter", "JustifyRight", "JustifyBlock"]},
                                                {name: "links", items: ["Link", "Unlink", "anchorPluginButton"]},
                                                {name: "insert", items: ["Image", "Embed", "Table", "HorizontalRule", "SpecialChar", "inserthtml4x"]},
                                                {name: "tools", items: ["ShowBlocks"]},
                                                {name: "styles", items: ["Styles", "Format"]},
                                                {name: "document", items: ["Source"]}
                                            ],
                                            extraPlugins: "anchor, inserthtml4x, embed",
                                            filebrowserUploadUrl: "/api/upload?name=fileupload",
                                            embed_provider: '//ckeditor.iframe.ly/api/oembed?url={url}&callback={callback}'
                                        });
                                    }
                                } else if (allAccountSettings[f][6] && allAccountSettings[f][6] === "date") {
                                    var todaysDate = new Date();
                                    if (type === 'edit') {
                                        var formatFound = getFormat(site_dynamic_menu);
                                        // if(formatFound !==null){
                                        //    console.log(formatFound);
                                        // }

                                        $('#e-' + spanId).addClass(mandatoryClass).val(site_dynamic_menu);
                                        $('#e-' + spanId).datepicker({dateFormat: 'yy-mm-dd', endDate: "today", maxDate: todaysDate});
                                    } else {
                                        $('#a-' + spanId).addClass(mandatoryClass).val();
                                        $('#a-' + spanId).datepicker({dateFormat: 'yy-mm-dd', endDate: "today", maxDate: todaysDate});
                                    }
                                } else if (allAccountSettings[f][6] && allAccountSettings[f][6] === "password") {
                                    if (type === 'edit') {
                                        $('#e-' + spanId).addClass(mandatoryClass).val(site_dynamic_menu).get(0).type = 'password';
                                    } else {
                                        $('#a-' + spanId).addClass(mandatoryClass).get(0).type = 'password';
                                    }
                                } else if (allAccountSettings[f][6] && allAccountSettings[f][6] === "hidde-it") {
                                    if (type === 'edit') {
                                        $('#e-' + spanId).addClass(mandatoryClass).parent().addClass('hide');
                                        $('#e-' + spanId).val(site_dynamic_menu).get(0).type = 'hidden';
                                    }
                                    if (type === 'add') {
                                        $('#a-' + spanId).addClass(mandatoryClass).parent().addClass('hide');
                                        $('#a-' + spanId).val(site_dynamic_menu).get(0).type = 'hidden';
                                    }
                                } else if (allAccountSettings[f][6] && allAccountSettings[f][6] === "autoGenerated") {
                                    if (type === 'edit') {
                                        $('#e-' + spanId).addClass(mandatoryClass).parent().addClass('hide').addClass('autoGenerated');
                                        $('#e-' + spanId).val(site_dynamic_menu).get(0).type = 'hidden';
                                    } else {
                                        $('#a-' + spanId).addClass(mandatoryClass).parent().addClass('hide').addClass('autoGenerated');
                                        $('#a-' + spanId).get(0).type = 'hidden';
                                    }
                                } else if (allAccountSettings[f][6] && allAccountSettings[f][6] === "pdf" || allAccountSettings[f][6] && allAccountSettings[f][6] === "image") {
                                    if (type === 'edit') {
                                        if (site_dynamic_menu) {
                                            site_dynamic_menu = site_dynamic_menu.replace('JPG', 'jpg').replace('JPEG', 'jpeg').replace('PNG', 'png').replace('PDF', 'pdf').replace('GIF', 'gif');
                                            var lastIndexOfFileName = site_dynamic_menu.substring(site_dynamic_menu.lastIndexOf('/') + 1);
                                            if (site_dynamic_menu.toLowerCase().includes('static')) {
                                                var srcVal = site_dynamic_menu.toLowerCase();
                                            } else {
                                                if (allAccountSettings[f][6] === 'pdf') {
                                                    if (site_dynamic_menu.toLowerCase().includes('http')) {
                                                        var srcVal = site_dynamic_menu;
                                                    } else {
                                                        var srcVal = original_images_webpath + site_dynamic_menu;
                                                    }
                                                } else {

                                                    if (site_dynamic_menu.toLowerCase().includes('http')) {
                                                        var srcVal = site_dynamic_menu;
                                                    } else {
                                                        if (site_dynamic_menu.toLowerCase().includes('images')) {
                                                            var srcVal = original_images_webpath + site_dynamic_menu;
                                                        } else {
                                                            var srcVal = original_images_webpath + 'images/' + site_dynamic_menu;
                                                        }
                                                    }
                                                }
                                            }

                                            if (allAccountSettings[f][6] === 'pdf') {
                                                $('#e-' + spanId).parent().append('<embed class="mb3_img" id="mb3_img-' + spanId + '" src="' + srcVal + '" width="90px" height="100px"></embed>');
                                            } else {
                                                $('#e-' + spanId).parent().append('<img class="mb3_img" id="mb3_img-' + spanId + '" src="' + srcVal + '" />');
                                            }
                                            $('#e-' + spanId).parent().append('<span class="file-name-reference">' + lastIndexOfFileName + '</span>');

                                            if (allAccountSettings[f][6] === 'image' || allAccountSettings[f][6] === 'pdf') {
                                                $('#e-' + spanId).parent().append('<input class="btn btn-secondary document-remover" id="remove-' + spanId + '" value="Remove" onclick="removeFileDoc(\'' + spanId + '\')" />');
                                            }

                                            $('#e-' + spanId).parent().append('<input type="hidden" class="hidden-field" name="e-' + spanId + '-side" id="e-' + spanId + '-side" value="' + site_dynamic_menu + '" />');
                                            $('#e-' + spanId).addClass(mandatoryClass).addClass('withImageOnLeft').get(0).type = 'file';

                                        } else {
                                            $('#e-' + spanId).addClass(mandatoryClass).get(0).type = 'file';
                                        }

                                        if (allAccountSettings[f][6] && allAccountSettings[f][6] === "pdf") {
                                            $('#e-' + spanId).attr('accept', '.pdf')
                                        }
                                        if (allAccountSettings[f][6] && allAccountSettings[f][6] === "image") {
                                            $('#e-' + spanId).attr('accept', '.png, .jpg, .jpeg, .gif')
                                        }

                                    } else {
                                        $('#a-' + spanId).addClass(mandatoryClass).get(0).type = 'file';
                                        if (allAccountSettings[f][6] && allAccountSettings[f][6] === "pdf") {
                                            $('#a-' + spanId).attr('accept', '.pdf')
                                        }
                                        if (allAccountSettings[f][6] && allAccountSettings[f][6] === "image") {
                                            $('#a-' + spanId).attr('accept', '.png, .jpg, .jpeg, .gif')
                                        }
                                    }
                                } else {
                                    if (type === 'edit') {
                                        $('#e-' + spanId).addClass(mandatoryClass).val(site_dynamic_menu);
                                    }
                                }
                            }
                        }
                        if ((x + 1) === spans.length && (f + 1) === allAccountSettings.length) {
                            $('#editDynamicList').removeClass('loadingBg');
                        }
                    }
                }
            }
        },
        error: function (XMLHttpRequest, textStatus, errorThrown) {
            $('#editDynamicListModal').modal('hide');
            $('#addDynamicListModal').modal('hide');

            // Show Error Modal
            $('#errorModal').modal('show');
        }
    });
}

async function publishDynamicMenu(accountId, reference, env, preview_server, dynamic_path, thisTemplate, thisParameters, fieldsToLink) {

    accountId = escapeHtml(accountId);
    reference = escapeHtml(reference);
    env = escapeHtml(env);
    preview_server = escapeHtml(preview_server);
    dynamic_path = escapeHtml(dynamic_path);
    thisTemplate = escapeHtml(thisTemplate);
    thisParameters = escapeHtml(thisParameters);
    fieldsToLink = escapeHtml(fieldsToLink);

    $.ajax({
        type: "POST",
        url: "/publish_menu/account_" + accountId + "_menu_" + reference + '/' + accountId + '/' + reference + '/' + env,
        data: {},
        contentType: false,
        cache: false,
        processData: false,
        success: function (updated) {
            $('#publishDynamicListSuccessNotification').toast('show');

            if (env !== 'save') {
                if (thisTemplate !== '') {
                    openInNewTab(preview_server + dynamic_path + thisTemplate + '.html?' + thisParameters + '=' + fieldsToLink);
                } else {
                    alert("There is no preview setting for this Menu yet. Please add one to preview this type.")
                }
            }

            doRedrawTable(true, updated.menus, true);

            var buttons_to_edit_or_add_container = document.getElementById('buttons_to_edit');
            if (!buttons_to_edit_or_add_container) {
                buttons_to_edit_or_add_container = document.getElementById('buttons_to_add');
            }
            const allActionButtons = buttons_to_edit_or_add_container.getElementsByTagName('button');
            for (let i = 0; i < allActionButtons.length; i++) {
                allActionButtons[i].disabled = false;
                allActionButtons[i].classList.remove('disabled');
            }
            var modal_footer_links = document.getElementById('modal-footer-edit');
            if (!modal_footer_links) {
                modal_footer_links = document.getElementById('modal-footer-add')
            }
            const allActionButtonsFooter = modal_footer_links.getElementsByTagName('button');
            for (let i = 0; i < allActionButtonsFooter.length; i++) {
                allActionButtonsFooter[i].disabled = false;
                allActionButtonsFooter[i].classList.remove('disabled');
            }
        },
        error: function (XMLHttpRequest, textStatus, errorThrown) {
            $('#publishDynamicList').modal('hide');
            $('#errorModal').modal('show');

            var buttons_to_edit_or_add_container = document.getElementById('buttons_to_edit');
            if (!buttons_to_edit_or_add_container) {
                buttons_to_edit_or_add_container = document.getElementById('buttons_to_add');
            }
            const allActionButtons = buttons_to_edit_or_add_container.getElementsByTagName('button');
            for (let i = 0; i < allActionButtons.length; i++) {
                allActionButtons[i].disabled = false;
                allActionButtons[i].classList.remove('disabled');
            }
            var modal_footer_links = document.getElementById('modal-footer-edit');
            if (!modal_footer_links) {
                modal_footer_links = document.getElementById('modal-footer-add')
            }
            const allActionButtonsFooter = modal_footer_links.getElementsByTagName('button');
            for (let i = 0; i < allActionButtonsFooter.length; i++) {
                allActionButtonsFooter[i].disabled = false;
                allActionButtonsFooter[i].classList.remove('disabled');
            }
        }
    });
}


async function updateDynamicMenu(accountId, reference, env, preview_server, dynamic_path, thisButton) {

    accountId = escapeHtml(accountId);
    reference = escapeHtml(reference);
    env = escapeHtml(env);
    preview_server = escapeHtml(preview_server);
    dynamic_path = escapeHtml(dynamic_path);

    const buttons_to_edit_container = document.getElementById('buttons_to_edit');
    const allActionButtons = buttons_to_edit_container.getElementsByTagName('button');
    for (let i = 0; i < allActionButtons.length; i++) {
        allActionButtons[i].disabled = true;
        allActionButtons[i].classList.add('disabled');
    }
    const modal_footer_links = document.getElementById('modal-footer-edit');
    const allActionButtonsFooter = modal_footer_links.getElementsByTagName('button');
    for (let i = 0; i < allActionButtonsFooter.length; i++) {
        allActionButtonsFooter[i].disabled = true;
        allActionButtonsFooter[i].classList.add('disabled');
    }
    var idToLink = '';
    $('#edit-' + reference + ' > .mb-3').each(function () {
        if ($(this).hasClass('autoGenerated') && $(this).find('input[type="hidden"]').val().trim() === '') {
            var autoGen = escapeHtml($('#e-name').val());
            if (autoGen) {
                autoGen = autoGen.replace(/,/g, '&comma;');
            }
            if (!autoGen || autoGen === '' || autoGen === null || autoGen === 'null' || autoGen === undefined || autoGen === 'undefined' || autoGen === NaN || autoGen === 'nan') {
                autoGen = escapeHtml($('#e-title').val());
                if (autoGen) {
                    autoGen = autoGen.replace(/,/g, '&comma;');
                }
            }

            if (!autoGen || autoGen === '' || autoGen === null || autoGen === 'null' || autoGen === undefined || autoGen === 'undefined' || autoGen === NaN || autoGen === 'nan') {
                autoGen = reference + '-' + escapeHtml($('#e-id').val().replace(/,/g, '&comma;'));
            }
            autoGen = replaceSpecialCharacters(autoGen.toLowerCase());
            autoGen = autoGen.replace(/ /g, '_').replace(/\\t/g, '').replace(/,/g, ''); //  + '-' + $('#a-id').val()
            autoGen = autoGen.replace(/\'/g, "_").replace(/\"/g, "_").replace(/“/g, "_").replace(/„/g, "_").replace(/:/g, "_").replace(/[^a-zA-Z0-9 ]/, '_').replace(/’/g, "_").replace(/\?/g, "_").replace(/!/g, "_").replace(/¿/g, "_").replace(/¡/g, "_");

            $(this).find('input[type="hidden"]').val(autoGen);
        }
    })

    var form_data = await getFormData('edit-' + reference);

    if (!form_data[0] || (form_data[0] && form_data[0].mandatoryFields != true)) {

        // Get menu configuration
        let jsonConfig = await $.get("/api_menu/get_menu_configuration/" + accountId + "/" + reference, function (result) {
            return result;
        });
        var values = jsonConfig.columns;

        var thisTemplate = '';
        var thisParameters = '';
        var thisFields = '';
        if (values && values[0]) {
            thisTemplate = values[0][2];
            thisParameters = values[0][3];
            thisFields = values[0][4].split(';');
        }

        var fieldsToLink = '';
        var index = 0;
        for (var field in thisFields) {
            var singleField = $('#e-' + thisFields[field]);

            fieldsToLink += singleField.val();
            if (thisFields.length > 1 && thisFields.length === index) {
                fieldsToLink += fieldsToLink + '_';
            }

            index = index + 1;
        }

        var linkToPreview = '';
        if (thisTemplate !== '') {
            linkToPreview = preview_server + dynamic_path + thisTemplate + '.html?' + thisParameters + '=' + fieldsToLink
            // $("#link_to_preview_add").html('<a href="' + linkToPreview + '">' + linkToPreview + '</a>');
            // $("#link_to_preview_edit").html('<a href="' + linkToPreview + '">' + linkToPreview + '</a>');
        }

        $.ajax({
            type: "POST",
            url: "/update_menu/" + accountId + "/account_" + accountId + "_menu_" + reference,
            contentType: 'application/json',
            data: JSON.stringify(form_data),
            dataType: 'json',
            cache: false,
            processData: false,
            success: function (updated) {
                $('#editDynamicList').modal('hide');
                $('#editDynamicListSuccessNotification').toast('show');

                if (env === 'preview' || env === 'save' || env === 'saveOnly') {
                    publishDynamicMenu(accountId, reference, env, preview_server, dynamic_path, thisTemplate, thisParameters, fieldsToLink);
                } else {
                    if (thisTemplate !== '') {
                        openInNewTab(linkToPreview);
                    } else {
                        alert("You must have to setup the template in the configuration menu!")
                    }
                    doRedrawTable(true, updated.menus, true);

                    const buttons_to_edit_container = document.getElementById('buttons_to_edit');
                    const allActionButtons = buttons_to_edit_container.getElementsByTagName('button');
                    for (let i = 0; i < allActionButtons.length; i++) {
                        allActionButtons[i].disabled = false;
                        allActionButtons[i].classList.remove('disabled');
                    }
                    const modal_footer_links = document.getElementById('modal-footer-edit');
                    const allActionButtonsFooter = modal_footer_links.getElementsByTagName('button');
                    for (let i = 0; i < allActionButtonsFooter.length; i++) {
                        allActionButtonsFooter[i].disabled = false;
                        allActionButtonsFooter[i].classList.remove('disabled');
                    }
                }

            },
            error: function (XMLHttpRequest, textStatus, errorThrown) {
                $('#editDynamicList').modal('hide');
                $('#errorModal').modal('show');

                const buttons_to_edit_container = document.getElementById('buttons_to_edit');
                const allActionButtons = buttons_to_edit_container.getElementsByTagName('button');
                for (let i = 0; i < allActionButtons.length; i++) {
                    allActionButtons[i].disabled = false;
                    allActionButtons[i].classList.remove('disabled');
                }
                const modal_footer_links = document.getElementById('modal-footer-edit');
                const allActionButtonsFooter = modal_footer_links.getElementsByTagName('button');
                for (let i = 0; i < allActionButtonsFooter.length; i++) {
                    allActionButtonsFooter[i].disabled = false;
                    allActionButtonsFooter[i].classList.remove('disabled');
                }
            }
        });
    } else {
        for (var singleItem in form_data[0]['mandatoryElementsNotCompletedToReturn']) {
            $('#' + form_data[0]['mandatoryElementsNotCompletedToReturn'][singleItem]).addClass('warning-not-completed');
            $('#' + form_data[0]['mandatoryElementsNotCompletedToReturn'][singleItem]).parent().find('.ck-editor').addClass('warning-not-completed');
        }
        alert("You have to complete all mandatory fields (" + form_data[0]['mandatoryElementsNotCompletedToReturn'].join(", ").replace(/e-/g, '') + ")!");

        const buttons_to_edit_container = document.getElementById('buttons_to_edit');
        const allActionButtons = buttons_to_edit_container.getElementsByTagName('button');
        for (let i = 0; i < allActionButtons.length; i++) {
            allActionButtons[i].disabled = false;
            allActionButtons[i].classList.remove('disabled');
        }
        const modal_footer_links = document.getElementById('modal-footer-edit');
        const allActionButtonsFooter = modal_footer_links.getElementsByTagName('button');
        for (let i = 0; i < allActionButtonsFooter.length; i++) {
            allActionButtonsFooter[i].disabled = false;
            allActionButtonsFooter[i].classList.remove('disabled');
        }
    }
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

function uploadSingleFile(form_data) {

    return $.ajax({
        type: "POST",
        url: "/api/upload",
        data: form_data,
        contentType: false,
        dataType: 'json',
        cache: false,
        processData: false,
        success: function (response) {
            //console.log(response);
        },
        error: function (XMLHttpRequest, textStatus, errorThrown) {
            console.error(errorThrown);
            return errorThrown;
        }
    });
}

async function addDynamicMenu(accountId, reference, env, preview_server, dynamic_path, thisButton) {

    accountId = escapeHtml(accountId);
    reference = escapeHtml(reference);
    env = escapeHtml(env);
    preview_server = escapeHtml(preview_server);
    dynamic_path = escapeHtml(dynamic_path);

    const buttons_to_add_container = document.getElementById('buttons_to_add');
    const allActionButtons = buttons_to_add_container.getElementsByTagName('button');
    for (let i = 0; i < allActionButtons.length; i++) {
        allActionButtons[i].disabled = true;
        allActionButtons[i].classList.add('disabled');
    }
    const modal_footer_links = document.getElementById('modal-footer-add');
    const allActionButtonsFooter = modal_footer_links.getElementsByTagName('button');
    for (let i = 0; i < allActionButtonsFooter.length; i++) {
        allActionButtonsFooter[i].disabled = true;
        allActionButtonsFooter[i].classList.add('disabled');
    }

    var idToLink = '';
    $('#add-' + reference + ' > .mb-3').each(function () {
        if ($(this).hasClass('autoGenerated')) {
            var autoGen = escapeHtml($('#a-name').val());
            if (autoGen) {
                autoGen = autoGen.replace(/,/g, '&comma;');
            }
            if (!autoGen || autoGen === '' || autoGen === null || autoGen === 'null' || autoGen === undefined || autoGen === 'undefined' || autoGen === NaN || autoGen === 'nan') {
                autoGen = escapeHtml($('#a-title').val());
                if (autoGen) {
                    autoGen = autoGen.replace(/,/g, '&comma;');
                }
            }

            if (!autoGen || autoGen === '' || autoGen === null || autoGen === 'null' || autoGen === undefined || autoGen === 'undefined' || autoGen === NaN || autoGen === 'nan') {
                autoGen = reference + '-' + escapeHtml($('#a-id').val().replace(/,/g, '&comma;'));
            }
            autoGen = replaceSpecialCharacters(autoGen.toLowerCase());
            autoGen = autoGen.replace(/ /g, '_').replace(/\\t/g, '').replace(/,/g, ''); //  + '-' + $('#e-id').val()
            autoGen = autoGen.replace(/\'/g, "_").replace(/\"/g, "_").replace(/“/g, "_").replace(/„/g, "_").replace(/:/g, "_").replace(/[^a-zA-Z0-9 ]/, '_').replace(/’/g, "_").replace(/\?/g, "_").replace(/!/g, "_").replace(/¿/g, "_").replace(/¡/g, "_");
            $(this).find('input[type="hidden"]').val(autoGen);
        }
    })

    var form_data = await getFormData('add-' + reference);

    if (!form_data[0] || (form_data[0] && form_data[0].mandatoryFields != true)) {

        // Get menu configuration
        let jsonConfig = await $.get("/api_menu/get_menu_configuration/" + accountId + "/" + reference, function (result) {
            return result;
        });
        var values = jsonConfig.columns;

        var thisTemplate = '';
        var thisParameters = '';
        var thisFields = '';
        if (values && values[0]) {
            thisTemplate = values[0][2];
            thisParameters = values[0][3];
            thisFields = values[0][4].split(';');
        }

        var fieldsToLink = '';
        var index = 0;
        for (var field in thisFields) {
            var singleField = $('#a-' + thisFields[field]);

            fieldsToLink += singleField.val();
            if (thisFields.length > 1 && thisFields.length === index) {
                fieldsToLink += fieldsToLink + '_';
            }

            index = index + 1;
        }

        var linkToPreview = '';
        if (thisTemplate !== '') {
            linkToPreview = preview_server + dynamic_path + thisTemplate + '.html?' + thisParameters + '=' + fieldsToLink
            // $("#link_to_preview_add").html('<a href="' + linkToPreview + '">' + linkToPreview + '</a>');
            // $("#link_to_preview_edit").html('<a href="' + linkToPreview + '">' + linkToPreview + '</a>');
        }

        $.ajax({
            type: "POST",
            url: "/addnew_menu/account_" + accountId + "_menu_" + reference,
            contentType: 'application/json',
            data: JSON.stringify(form_data),
            dataType: 'json',
            cache: false,
            processData: false,
            success: function (updated) {
                $('#addDynamicList').modal('hide');
                $('#addDynamicListSuccessNotification').toast('show');

                if (env === 'preview' || env === 'save' || env === 'saveOnly') {
                    publishDynamicMenu(accountId, reference, env, preview_server, dynamic_path, thisTemplate, thisParameters, fieldsToLink);
                } else {
                    if (thisTemplate !== '') {
                        openInNewTab(linkToPreview);
                    } else {
                        alert("You must have to setup the template in the configuration menu!")
                    }
                    doRedrawTable(true, updated.menus, true);
                }

                const buttons_to_add_container = document.getElementById('buttons_to_add');
                const allActionButtons = buttons_to_add_container.getElementsByTagName('button');
                for (let i = 0; i < allActionButtons.length; i++) {
                    allActionButtons[i].disabled = false;
                    allActionButtons[i].classList.remove('disabled');
                }
                const modal_footer_links = document.getElementById('modal-footer-add');
                const allActionButtonsFooter = modal_footer_links.getElementsByTagName('button');
                for (let i = 0; i < allActionButtonsFooter.length; i++) {
                    allActionButtonsFooter[i].disabled = false;
                    allActionButtonsFooter[i].classList.remove('disabled');
                }

            },
            error: function (XMLHttpRequest, textStatus, errorThrown) {
                $('#addDynamicList').modal('hide');
                $('#errorModal').modal('show');

                const buttons_to_add_container = document.getElementById('buttons_to_add');
                const allActionButtons = buttons_to_add_container.getElementsByTagName('button');
                for (let i = 0; i < allActionButtons.length; i++) {
                    allActionButtons[i].disabled = false;
                    allActionButtons[i].classList.remove('disabled');
                }
                const modal_footer_links = document.getElementById('modal-footer-add');
                const allActionButtonsFooter = modal_footer_links.getElementsByTagName('button');
                for (let i = 0; i < allActionButtonsFooter.length; i++) {
                    allActionButtonsFooter[i].disabled = false;
                    allActionButtonsFooter[i].classList.remove('disabled');
                }
            }
        });
    } else {
        for (var singleItem in form_data[0]['mandatoryElementsNotCompletedToReturn']) {
            $('#' + form_data[0]['mandatoryElementsNotCompletedToReturn'][singleItem]).addClass('warning-not-completed');
            $('#' + form_data[0]['mandatoryElementsNotCompletedToReturn'][singleItem]).parent().find('.ck-editor').addClass('warning-not-completed');
        }
        alert("You have to complete all mandatory fields (" + form_data[0]['mandatoryElementsNotCompletedToReturn'].join(", ").replace(/a-/g, '') + ")!");

        const buttons_to_add_container = document.getElementById('buttons_to_add');
        const allActionButtons = buttons_to_add_container.getElementsByTagName('button');
        for (let i = 0; i < allActionButtons.length; i++) {
            allActionButtons[i].disabled = false;
            allActionButtons[i].classList.remove('disabled');
        }
        const modal_footer_links = document.getElementById('modal-footer-add');
        const allActionButtonsFooter = modal_footer_links.getElementsByTagName('button');
        for (let i = 0; i < allActionButtonsFooter.length; i++) {
            allActionButtonsFooter[i].disabled = false;
            allActionButtonsFooter[i].classList.remove('disabled');
        }
    }
}

async function deleteDynamicMenuEntries(accountId, reference, env, preview_server, dynamic_path, thisButton) {

    accountId = escapeHtml(accountId);
    reference = escapeHtml(reference);
    env = escapeHtml(env);
    preview_server = escapeHtml(preview_server);
    dynamic_path = escapeHtml(dynamic_path);

    thisButton.classList.add('disabled');
    let checked_entries = [];
    let checked_entries_str = "";

    $.each($("input:checked"), function (K, V) {
        checked_entries.push(escapeHtml(V.value));
        checked_entries_str += escapeHtml(V.value) + ",";
    });
    checked_entries_str = checked_entries_str.slice(0, -1);

    // Get list configuration
    let jsonConfig = await $.get("/api_menus/get_menu_configuration/" + accountId + "/" + reference, function (result) {
        return result;
    });
    var values = jsonConfig.columns;

    var thisTemplate = '';
    var thisParameters = '';
    var thisFields = '';
    if (values && values[0]) {
        thisTemplate = values[0][2];
        thisParameters = values[0][3];
        thisFields = values[0][4].split(';');
    }

    var fieldsToLink = '';
    var index = 0;
    for (var field in thisFields) {
        var singleField = $('#a-' + thisFields[field]);

        fieldsToLink += singleField.val();
        if (thisFields.length > 1 && thisFields.length === index) {
            fieldsToLink += fieldsToLink + '_';
        }

        index = index + 1;
    }

    var linkToPreview = '';
    if (thisTemplate !== '') {
        linkToPreview = preview_server + dynamic_path + thisTemplate + '.html?' + thisParameters + '=' + fieldsToLink
    }

    // Post
    $.ajax({
        type: "POST",
        url: "/delete_menu" + accountId + "/account_" + accountId + "_menu_" + reference,
        data: {
            "entries_to_delete": checked_entries_str
        },
        success: function (entry) {

            publishDynamicMenu(accountId, reference, env, preview_server, dynamic_path, thisTemplate, thisParameters, fieldsToLink);

        },
        error: function (XMLHttpRequest, textStatus, errorThrown) {
            // Hide Create Modal
            $('#deleteDynamicListsModal').modal('hide');

            // Show Error Modal
            $('#errorDeleteModal').modal('show');
        }
    });
}

async function populateUploadFieldsDynamicMenuDialog(accountId, reference, fields, isEditing, complexedArray = false) {

    accountId = escapeHtml(accountId);
    reference = escapeHtml(reference);

    $.ajax({
        type: "GET",
        url: "/api_menu/get_all_menus/" + accountId,
        success: function (response) {
            var menusDropdown = [];
            var allMenus = response.menus;

            for (let j = 0; j < allMenus.length; j++) {
                var menuNameToPush = allMenus[j][2];

                if (menuNameToPush !== "account_" + accountId + "_menu_settings") {
                    menuNameToPush = menuNameToPush.replace("account_" + accountId + "_menu_", "");
                    menusDropdown.push(menuNameToPush);
                }

                if (allMenus.length === (j + 1)) {
                    populateDropdowns(accountId, reference, menusDropdown, fields, isEditing, complexedArray);
                }
            }
        },
        error: function (XMLHttpRequest, textStatus, errorThrown) {
            $('#errorModal').modal('show');
        }
    });
}

async function populateDropdowns(accountId, reference, menusDropdown, fields, isEditing, complexedArray) {

    accountId = escapeHtml(accountId);
    reference = escapeHtml(reference);

    if (fields && fields.length > 0) {

        document.getElementById("setField-" + reference).innerHTML = '';

        for (var g = 0; g < fields.length; g++) {

            var linkedTable = false;
            var linkedField = false;
            var fieldType = 'input';
            var displaySettingsItem = 1;
            var linkedFieldLabel = false;

            if (complexedArray) {
                var thisField = (fields[g][2] ? escapeHtml(fields[g][2].trim()) : '');
                linkedTable = (fields[g][3] ? escapeHtml(fields[g][3].trim()) : '');
                linkedField = (fields[g][4] ? escapeHtml(fields[g][4].trim()) : '');
                linkedFieldLabel = (fields[g][5] ? escapeHtml(fields[g][5].trim()) : linkedField);
                fieldType = (fields[g][6] ? escapeHtml(fields[g][6].trim()) : '');
                displaySettingsItem = ((fields[g][7] !== "null" && fields[g][7] !== null) ? escapeHtml(fields[g][7]) : 1);
            } else {
                var thisField = escapeHtml(fields[g].trim());
            }

            var thisElementToEdit = document.createElement('div');
            thisElementToEdit.classList.add('mb-3');
            thisElementToEdit.classList.add('mb-container');
            thisElementToEdit.classList.add('s-' + thisField + '-container');
            thisElementToEdit.innerHTML = '<div class="row"><div class="form-group col-md-5"><label for="s-' + thisField + '" class="col-form-label">' + thisField + ':</label>' + '<select name="selectItem_' + thisField + '" class="form-select form-select-md connection" id="s-' + thisField + '"><option value="null" selected>Static Field</option></select></div><div class="form-group col-md-4"><label for="typeSelectItem_' + thisField + '" class="col-form-label">Field Type:</label><select name="typeSelectItem_' + thisField + '" id="typeSelectItem_' + thisField + '" class="form-select form-select-md field_type typeSelectItem_Item"><option value="input">Input</option><option value="text_area">Text Area</option><option value="wysiwyg">Wysiwyg Editor</option><option value="password">Password</option><option value="select">Single Select</option><option value="multiselect">Multi Select</option><option value="multi_checkbox">Check Box</option><option value="code">Code</option><option value="date">Date / Time</option><option value="image">Image</option><option value="pdf">PDF</option><option value="hidde-it">Hidden Field</option><option value="autoGenerated">Auto Generated</option></select></div><div class="form-group col-md-3"><label for="displaySettingsItem_' + thisField + '" class="col-form-label">Visible in menu:</label><select name="displaySettingsItem_' + thisField + '" id="dsi_' + thisField + '" class="form-select form-select-md"><option value="1">Yes</option><option value="0">No</option></select></div></div>';

            document.getElementById("setField-" + reference).appendChild(thisElementToEdit);

            $('#typeSelectItem_' + thisField).val(fieldType);
            $('#dsi_' + thisField).val(displaySettingsItem);

            for (var v = 0; v < menusDropdown.length; v++) {
                if (menusDropdown[v] !== reference) {
                    $('select#s-' + thisField).append('<option value="' + escapeHtml(menusDropdown[v]) + '">' + escapeHtml(menusDropdown[v]) + '</option>');
                }

                if (!isEditing && (v + 1) === menusDropdown.length) {

                    if (linkedTable && linkedField && linkedTable !== 'None' && linkedField !== 'None') {
                        $.ajax({
                            type: "GET",
                            url: "/api_menu/get_menu_columns_with_returned_id/" + accountId + "/" + linkedTable + "/" + thisField + "/" + linkedField + "/" + linkedFieldLabel,
                            success: function (allFieldsResponse) {
                                fieldToReturn = allFieldsResponse.fieldToReturn;
                                linkedFieldToReturn = allFieldsResponse.linkedFieldToReturn;
                                linkedFieldLabelToReturn = allFieldsResponse.linkedFieldLabelToReturn;
                                allFieldsResponse = allFieldsResponse.columns;

                                //$('#typeSelectItem_' + fieldToReturn).attr('disabled', 'disabled');

                                $('#s-' + fieldToReturn + '-assignedField').remove();

                                var fieldsDropdown = '<div class="row"><div class="form-group col-md-6"><label for="s-' + fieldToReturn + '-assignedField" class="col-form-label">Assigned Field:</label><select name="s-' + fieldToReturn + '-assignedField" class="form-select form-select-md" id="s-' + fieldToReturn + '-assignedField"></select></div><div class="form-group col-md-6"><label for="s-' + fieldToReturn + '-assignedFieldLabel" class="col-form-label">Assigned Label:</label><select name="s-' + fieldToReturn + '-assignedFieldLabel" class="form-select form-select-md" id="s-' + fieldToReturn + '-assignedFieldLabel"></select></div></div>';
                                $('.s-' + fieldToReturn + '-container').append(fieldsDropdown);
                                for (var h = 0; h < allFieldsResponse.length; h++) {
                                    $('select#s-' + fieldToReturn + '-assignedField').append('<option value="' + allFieldsResponse[h][0] + '" ' + (allFieldsResponse[h][0] === 'id' ? "selected" : "") + '>' + allFieldsResponse[h][0] + '</option>');

                                    if ((h + 1) === allFieldsResponse.length) {
                                        $('select#s-' + fieldToReturn + '-assignedField').val(linkedFieldToReturn);
                                    }

                                    $('select#s-' + fieldToReturn + '-assignedFieldLabel').append('<option value="' + allFieldsResponse[h][0] + '" ' + (allFieldsResponse[h][0] === 'id' ? "selected" : "") + '>' + allFieldsResponse[h][0] + '</option>');

                                    if ((h + 1) === allFieldsResponse.length) {
                                        $('select#s-' + fieldToReturn + '-assignedFieldLabel').val(linkedFieldLabelToReturn);
                                    }
                                }
                            }, error: function (XMLHttpRequest, textStatus, errorThrown) {
                                $('#errorModal').modal('show');
                            }
                        });
                    }
                    $("#uploadSetFieldsDynamicList").modal('show');
                }
            }

            if (thisField && fieldType === 'select' || thisField && fieldType === 'multiselect' || thisField && fieldType === 'multi_checkbox') {
                $('select#s-' + thisField).val(linkedTable);

                $('#typeSelectItem_' + thisField + ' option').attr('disabled', true);
                $('#typeSelectItem_' + thisField + ' option[value="select"]').removeAttr('disabled');
                $('#typeSelectItem_' + thisField + ' option[value="multiselect"]').removeAttr('disabled');
                $('#typeSelectItem_' + thisField + ' option[value="multi_checkbox"]').removeAttr('disabled');
            }
        }
    }

    $('select.form-select.connection').change(function () {
        var thisValue = escapeHtml(this.value);
        var thisId = escapeHtml($(this).attr('id'));
        var thisIdClean = thisId.replace("s-", "");

        if (thisValue !== "null") {
            $.ajax({
                type: "GET",
                url: "/api_menu/get_menu_columns/" + accountId + "/" + thisValue,
                success: function (allFieldsResponse) {

                    allFieldsResponse = allFieldsResponse.columns;

                    $('#typeSelectItem_' + thisIdClean + ' option').attr('disabled', true);
                    $('#typeSelectItem_' + thisIdClean + ' option[value="select"]').removeAttr('disabled');
                    $('#typeSelectItem_' + thisIdClean + ' option[value="multiselect"]').removeAttr('disabled');
                    $('#typeSelectItem_' + thisIdClean + ' option[value="multi_checkbox"]').removeAttr('disabled');

                    $('#typeSelectItem_' + thisIdClean).val("multi_checkbox");

                    $('#' + thisId + '-assignedField').remove();

                    var fieldsDropdown = '<div class="mt-1"><select name="' + thisId + '-assignedField" class="form-select form-select-md" id="' + thisId + '-assignedField"></select></div>';
                    $('.' + thisId + '-container').append(fieldsDropdown);
                    for (var h = 0; h < allFieldsResponse.length; h++) {
                        $('select#' + thisId + '-assignedField').append('<option value="' + allFieldsResponse[h][0] + '" ' + (allFieldsResponse[h][0] === 'id' ? "selected" : "") + '>' + allFieldsResponse[h][0] + '</option>');
                    }
                }, error: function (XMLHttpRequest, textStatus, errorThrown) {
                    $('#errorModal').modal('show');
                }
            });
        } else {
            $('#typeSelectItem_' + thisIdClean + ' option').removeAttr('disabled');
            $('select#' + thisId + '-assignedField').remove();
        }
    })

    $(".typeSelectItem_Item").change(function () {
        var thisValue = escapeHtml(this.value);
        var thisId = escapeHtml($(this).attr('id'));
        var thisIdClean = thisId.replace("typeSelectItem_", "");
        if (thisValue !== "select" && thisValue !== "multiselect" && thisValue !== "multi_checkbox") {
            $("#s-" + thisIdClean).val('null');
            $(".mb-3.s-" + thisIdClean + "-container .mt-1").remove();
        }
    })
}

async function uploadSetFieldsDynamicMenu(accountId, reference, action) {

    accountId = escapeHtml(accountId);
    reference = escapeHtml(reference);
    action = escapeHtml(action);

    if (action === 'save') {
        var form_data = new FormData($('#setField-' + reference)[0]);

        $.ajax({
            type: "POST",
            url: "/upload_menu/create_middle_tables/" + accountId + "/" + reference,
            data: form_data,
            contentType: false,
            cache: false,
            processData: false,
            success: function (response) {
                $('#uploadSetFieldsDynamicList').modal('hide');
                $('#uploadSetFieldsDynamicList form').html('<input type="hidden" class="form-control" id="h-s-' + reference + '">');

                $('#addDynamicListSuccessNotification').toast('show');

                setTimeout(function () {
                    location.reload(true);
                }, 400);
                //doRedrawTable(false, false, true);
            },
            error: function (XMLHttpRequest, textStatus, errorThrown) {
                $('#errorModal').modal('show');
            }
        });
    } else {
        $('#uploadSetFieldsDynamicList').modal('hide');
        $('#uploadSetFieldsDynamicList #setField-' + reference).html('<input type="hidden" class="form-control" id="h-s-' + reference + '">');
    }
}

async function uploadDynamicMenu(accountId, reference) {

    accountId = escapeHtml(accountId);
    reference = escapeHtml(reference);

    if (document.getElementById("csv_file_to_upload").files.length == 0) {
        $('#uploadFileEmpty').toast('show');
    } else {

        $("#upload-file-btn").addClass("loadingBtn").prop("disabled", true);

        var form_data = new FormData($('#upload-csv-file')[0]);

        $.ajax({
            type: "POST",
            url: "/upload/dynamic_menu",
            data: form_data,
            contentType: false,
            cache: false,
            processData: false,
            success: function (response) {
                $("#upload-file-btn").removeClass("loadingBtn").prop("disabled", false);
                $('#uploadDynamicList').modal('hide');
                doRedrawTable(true, response, false);
                $('#addDynamicListSuccessNotification').toast('show');
            },
            error: function (XMLHttpRequest, textStatus, errorThrown) {
                $('#errorModal').modal('show');
            }
        });
    }
}

async function populateUploadFieldsForSettings(accountId, reference) {

    accountId = escapeHtml(accountId);
    reference = escapeHtml(reference);

    dropDownActionsToggle();
    // Get menu columns
    let jsonColumns = await $.get("/api_menu/get_menu_columns_with_properties/" + accountId + "/" + reference, function (result) {
        return result;
    });

    var headColumns = jsonColumns.columns;
    populateUploadFieldsDynamicMenuDialog(accountId, reference, headColumns, false, true);
}

async function openConfiguration(accountId, reference) {

    accountId = escapeHtml(accountId);
    reference = escapeHtml(reference);

    dropDownActionsToggle();

    // Get menu configuration
    let jsonConfig = await $.get("/api_menu/get_menu_configuration/" + accountId + "/" + reference, function (result) {
        return result;
    });

    var values = jsonConfig.columns;

    // Get menu columns
    let jsonColumns = await $.get("/api_menu/get_menu_columns_with_properties/" + accountId + "/" + reference, function (result) {
        return result;
    });

    var headColumns = jsonColumns.columns;

    for (var x = 0; x < headColumns.length; x++) {
        $('select#s-fields').append('<option value="' + escapeHtml(headColumns[x][2]) + '">' + escapeHtml(headColumns[x][2]) + '</option>');
    }

    for (var x = 0; x < headColumns.length; x++) {
        $('select#s-mandatory-fields').append('<option value="' + escapeHtml(headColumns[x][2]) + '">' + escapeHtml(headColumns[x][2]) + '</option>');
        $('select#s-field-to-save-by').append('<option value="' + escapeHtml(headColumns[x][2]) + '">' + escapeHtml(headColumns[x][2]) + '</option>');
    }

    if (values && values[0]) {
        $("#s-template").val(escapeHtml(values[0][2]));
        $("#s-parameters").val(escapeHtml(values[0][3]));

        var fields = values[0][4].split(';');
        for (var field in fields) {
            $('#s-fields option[value="' + escapeHtml(fields[field]) + '"]').attr("selected", "selected");
        }

        if (values[0][5]) {
            var mfields = values[0][5].split(',');
            for (var mfield in mfields) {
                $('#s-mandatory-fields option[value="' + escapeHtml(mfields[mfield]) + '"]').attr("selected", "selected");
            }
        }
    }
}

async function setConfigurationDynamicMenu(accountId, reference, action) {

    accountId = escapeHtml(accountId);
    reference = escapeHtml(reference);
    action = escapeHtml(action);

    if (action === 'save') {
        var form_data = await getFormData('setConfiguration-' + reference);

        $.ajax({
            type: "POST",
            url: "/set_menu/configuration/" + accountId + "/" + reference,
            contentType: 'application/json',
            data: JSON.stringify(form_data),
            dataType: 'json',
            cache: false,
            processData: false,
            success: function (response) {
                $('#setConfigurationDynamicList').modal('hide');
                $('#setConfigurationDynamicList form input').val('');

                $('#addDynamicListSuccessNotification').toast('show');

                doRedrawTable(false, false, true);
            },
            error: function (XMLHttpRequest, textStatus, errorThrown) {
                $('#errorModal').modal('show');
            }
        });
    } else {
        $('#setConfigurationDynamicList').modal('hide');
        $('#setConfigurationDynamicList form input').val('');
    }
}

window.addEventListener('DOMContentLoaded', async function main() {
    doRedrawTable(false, false, true);
})

async function doRedrawTable(doSetUpTable = false, responseFields = false, isEditing = false) {
    var localEnv = window.location.hostname;
    var rootPath = window.location;
    rootPath = rootPath.href.split('/menus/')[0];

    $('#editDynamicList form .mb-3').html('');
    $('#addDynamicList form .mb-3').html('');
    $('#table.table_' + reference).DataTable().clear().draw();
    $('#table.table_' + reference).DataTable().destroy();

    $('#table.table_' + reference + ' thead .filters').remove();
    $('#table.table_' + reference + ' thead tr').html('<th class="center not_export_col">Select</th>');
    $('#table.table_' + reference + ' tbody').html('');
    $('#table.table_' + reference + ' tfoot tr').html('<th class="center not_export_col">Select</th>');

    // Get menu columns
    let jsonColumns = await $.get("/api_menu/get_menu_columns/" + accountId + "/" + reference, function (result) {
        return result;
    });

    let getAccountSettings = await $.get("/api_menu/settings/" + accountId, function (allAccountSettings) {
        var images_webpath = allAccountSettings.images_webpath;
        var original_images_webpath = allAccountSettings.original_images_webpath;
        settings = allAccountSettings.settings;

        return [settings, images_webpath, original_images_webpath];
    });

    let allColumns = [{
        aTargets: [0],
        mData: function (source, type, row) {
            return "<input type='checkbox' id='entry_" + escapeHtml(source[0]) + "' value='" + escapeHtml(source[0]) + "' />";
        },
        width: "5%",
        orderable: false,
        sClass: "center"
    }];

    var columnsToAddToShowHide = [];

    var headColumns = jsonColumns.columns;
    for (var x = 0; x < headColumns.length; x++) {

        try {
            throw x
        } catch (xx) {
            setTimeout(function () {

                var hideIt = false;
                var shouldSplitArray = false;
                var autoGenerated = false;
                var isWysiwyg = false;
                var isDocument = false;
                var isImage = false;

                getAccountSettings.settings.filter(function (e) {

                    if (headColumns[xx][0] === e[2]) {
                        headColumns[xx][7] = e[7];
                    }

                    if (headColumns[xx][0] === e[2] && e[6] === 'hidde-it') {
                        hideIt = true;
                    } else if ((headColumns[xx][0] === e[2] && e[6] === 'multiselect') || (headColumns[xx][0] === e[2] && e[6] === 'multi_checkbox')) {
                        shouldSplitArray = true;
                    } else if (headColumns[xx][0] === e[2] && e[6] === 'autoGenerated') {
                        autoGenerated = true;
                    } else if (headColumns[xx][0] === e[2] && e[6] === 'wysiwyg') {
                        isWysiwyg = true;
                    } else if (headColumns[xx][0] === e[2] && e[6] === 'image') {
                        isImage = true;
                    } else if (headColumns[xx][0] === e[2] && e[6] === 'pdf') {
                        isDocument = true;
                    }
                })

                $('#table.table_' + reference + " thead tr").append('<th class="' + (headColumns[xx][7] !== 0 ? ((xx === 0 || hideIt === true) ? 'hidden ' : '') : 'hidden ') + 'center sorting the_reference" id="theReferenceHead_' + xx + '">' + headColumns[xx][0] + '</th>');
                $('#table.table_' + reference + " tfoot tr").append('<th class="' + (headColumns[xx][7] !== 0 ? ((xx === 0 || hideIt === true) ? 'hidden ' : '') : 'hidden ') + 'center sorting the_reference" id="theReferenceFoot_' + xx + '">' + headColumns[xx][0] + '</th>');

                var checkHeaderClass = headColumns[xx][0];
                var checkHeaderClassWithDots = headColumns[xx][0].replace(/\./g, "__DOT__");

                if (headColumns[xx][6] !== 0 && xx !== 0) {
                    columnsToAddToShowHide.push(xx + 1);
                }

                allColumns.push({
                    aTargets: [xx + 1],
                    mData: function (source, type, row) {
                        var val = "<i style='color: #CCC;'>No data</i>";
                        var fullVal = (source[xx] ? source[xx] : "").toString();

                        val = (source[xx] ? source[xx] : "").toString();

                        val = val.replace(/__BACKSLASH__TO_REPLACE__/g, "\\");

                        if (shouldSplitArray && val !== 'nan') {
                            val = val.split(';');
                        }

                        if (!shouldSplitArray && !autoGenerated) {
                            val = val.substring(val.lastIndexOf('\\') + 1).replace(/_/g, ' ');
                        } else if (!shouldSplitArray) {
                            val = val.substring(val.lastIndexOf('\\') + 1);
                        }

                        if (shouldSplitArray && val !== 'nan') {
                            for (var i = 0; i < val.length; i++) {
                                val[i] = val[i].substring(val[i].lastIndexOf('\\') + 1).replace(/_/g, ' ');
                            }
                            val = val.toString();
                            val = val.replace(/,/g, ',<br>');
                        }

                        if (isWysiwyg) {
                            val = htmlencode(val);
                            fullVal = htmlencode(fullVal);
                        }

                        if (!shouldSplitArray && typeof val === 'string' && val.length > 150) {
                            val = val.replace(/<[^>]+>/g, "").substring(0, 150);
                            val = val + "...";
                            fullVal = fullVal.replace(/__BACKSLASH__TO_REPLACE__/g, "\\");
                        }
                        fullVal = fullVal.replace(/&amp;comma;/g, ',').replace(/&comma;/g, ',').replace(/&amp,<br>comma,<br>/g, ',');

                        if ((isDocument || isImage) && source[xx] && source[xx] !== "nan") {
                            fullVal = fullVal.replace('JPG', 'jpg').replace('JPEG', 'jpeg').replace('PNG', 'png').replace('PDF', 'pdf').replace('GIF', 'gif');
                            if (fullVal.toLowerCase().includes('static')) {
                                var fullVal = fullVal; //.toLowerCase()
                            } else {
                                if (isDocument) {
                                    if (!fullVal.toLowerCase().includes('http')) {
                                        var fullVal = getAccountSettings.original_images_webpath + fullVal;
                                    }
                                } else if (isImage) {
                                    if (fullVal.toLowerCase().includes('images') && !fullVal.toLowerCase().includes('http')) {
                                        var fullVal = getAccountSettings.original_images_webpath + fullVal;
                                    } else if (!fullVal.toLowerCase().includes('images') && !fullVal.toLowerCase().includes('http')) {
                                        if (getAccountSettings.original_images_webpath.at(-1) === '/') {
                                            var fullVal = getAccountSettings.original_images_webpath + 'images/' + fullVal;
                                        } else {
                                            var fullVal = getAccountSettings.original_images_webpath + '/images/' + fullVal;
                                        }
                                    }
                                }
                            }
                        }

                        fullVal = fullVal.replace(/:\/\//g, '__FORWARD_SLASH_TO_HOLD__').replace(/\/\//g, '\/').replace(/__FORWARD_SLASH_TO_HOLD__/g, ':\/\/');

                        if (isDocument && source[xx] && source[xx] !== "nan") {
                            val = '<span class="pos_' + xx + ' toContainSize ' + checkHeaderClass + '"><pre><embed class="mb3_img" src="' + fullVal + '" width="90px" height="100px"></embed><span class="hidden" id="' + checkHeaderClass + '_pos_' + source[0] + '">' + fullVal + '</span></pre></span>';
                        } else if (isImage && source[xx] && source[xx] !== "nan") {
                            val = '<span class="pos_' + xx + ' toContainSize ' + checkHeaderClass + '"><pre><img class="mb3_img" src="' + fullVal + '" /></span><span class="hidden" id="' + checkHeaderClass + '_pos_' + source[0] + '">' + fullVal + '</pre></span>';
                        } else if (source[xx] && source[xx] !== "nan") {
                            val = '<span class="pos_' + xx + ' toContainSize ' + checkHeaderClass + '"><pre>' + val + '<span class="hidden" id="' + checkHeaderClass + '_pos_' + source[0] + '">' + fullVal + '</span></pre></span>';
                        } else {
                            val = '<span class="pos_' + xx + ' toContainSize ' + checkHeaderClass + '"><pre><i style="color:#ef7070;">No data</i><span class="hidden" id="' + checkHeaderClass + '_pos_' + source[0] + '"></pre></span>';
                        }
                        return val;
                    },
                    defaultContent: "<i style='color: #CCC;'>No data</i>",
                    sClass: (headColumns[xx][7] !== 0 ? ((xx === 0 || hideIt === true) ? 'hidden ' : '') : 'hidden ') + 'center'
                });

                var thisElementToEdit = document.createElement('div');
                thisElementToEdit.classList.add('mb-3');
                if (checkHeaderClass === "id") {
                    thisElementToEdit.classList.add('hide');
                }
                var thisElementToAdd = document.createElement('div');
                thisElementToAdd.classList.add('mb-3');
                if (checkHeaderClass === "id") {
                    thisElementToAdd.classList.add('hide');
                }

                var removeButtonForFilesAdd = '';
                var removeButtonForFilesEdit = '';

                var scriptForFilesAdd = '';
                var scriptForFilesEdit = '';

                if (isDocument || isImage) {
                    scriptForFilesAdd = "<script type=\"text/javascript\">$('#a-clear-" + checkHeaderClass + "').on('click', function(){$('#a-" + checkHeaderClass + "').val('');})</script>";
                    scriptForFilesEdit = "<script type=\"text/javascript\">$('#e-clear-" + checkHeaderClass + "').on('click', function(){$('#e-" + checkHeaderClass + "').val('');})</script>";

                    removeButtonForFilesAdd = '<input id="a-clear-' + checkHeaderClass + '" class="btn btn-small btn-secondary clear-btn" value="clear" />';
                    removeButtonForFilesEdit = '<input id="e-clear-' + checkHeaderClass + '" class="btn btn-small btn-secondary clear-btn" value="clear" />';
                }

                thisElementToEdit.innerHTML = removeButtonForFilesEdit + '<label for="e-' + checkHeaderClass + '" class="col-form-label">' + checkHeaderClass + ':</label>' + '<input type="text" class="form-control" name="e-' + checkHeaderClass + '" id="e-' + checkHeaderClass + '" value="" onkeyup="sanitizeInput(event)" />';
                thisElementToAdd.innerHTML = removeButtonForFilesAdd + '<label for="a-' + checkHeaderClass + '" class="col-form-label">' + checkHeaderClass + ':</label>' + '<input type="text" class="form-control" name="a-' + checkHeaderClass + '" id="a-' + checkHeaderClass + '" value="" onkeyup="sanitizeInput(event)" />';

                document.getElementById("edit-" + reference).appendChild(thisElementToEdit);
                $("#edit-" + reference + " .mb-3").find("#e-" + checkHeaderClass).parent().append(scriptForFilesEdit);
                document.getElementById("add-" + reference).appendChild(thisElementToAdd);
                $("#add-" + reference + " .mb-3").find("#a-" + checkHeaderClass).parent().append(scriptForFilesAdd);

                if ((xx + 1) === headColumns.length) {
                    getResume(allColumns, accountId, doSetUpTable, responseFields, isEditing, columnsToAddToShowHide);
                }
            }, 1000);
        }
    }
}

async function getResume(allColumns, accountId, doSetUpTable, responseFields, isEditing, columnsToAddToShowHide) {

    // Setup - add a text input to each header cell
    $('#table.table_' + reference + ' thead tr').clone(true).addClass('filters').appendTo('#table.table_' + reference + ' thead');

    let searchColumns = [];
    for (x = 0; x < allColumns.length; x++) {
        if (x != 0) {
            searchColumns.push(x);
        }
    }

    // Initialize Table
    $('#table.table_' + reference).DataTable({
        bProcessing: false,
        bServerSide: true,
        sAjaxSource: "/api_menu/get_menu/" + accountId + "/" + reference,
        aoColumns: allColumns,
        dom: 'Brltip',
        language: {"emptyTable": "No data available"},
        order: [2, "asc"],
        pageLength: 100,
        aLengthMenu: [[50, 100, 200, 300, 500, 1000], [50, 100, 200, 300, 500, 1000]],
        autoWidth: true,
        stateSave: true,
        buttons: {
            buttons: [
                {
                    text: 'Export',
                    extend: 'csv',
                    filename: reference + ' report',
                    className: 'btn-export'
                },
                {
                    extend: 'colvis',
                    text: 'Show / Hide',
                    columns: columnsToAddToShowHide,
                    className: 'showHideColumn btn-default'
                },
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
                if ($('input[type="checkbox"]:checked').length > 0) {
                    $(".deleteButton").prop('disabled', false);
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

            var queryString = window.location.search;
            var urlParams = new URLSearchParams(queryString);
            var itemId = "";
            if (urlParams.get('id')) {
                itemId = parseInt(urlParams.get('id'));
                $('#search_col_index_1').val(itemId);
                $('#search_col_index_1').keyup();
                $('input[type="checkbox"]#entry_' + itemId).prop('checked', true);
                if ($('input[type="checkbox"]#entry_' + itemId + ':checked')) {
                    $('#editDynamicList').modal('show').addClass('loadingBg');
                    populateEditDynamicMenuDialog('3', reference, 'edit', itemId);
                }
                $('#editDynamicList .btn.publish-btn').remove();
            } else {
                $('#search_col_index_1').val("");
                $('#search_col_index_1').keyup();
            }

            $(".loadingBg").removeClass("show");

            if (doSetUpTable === true) {
                populateUploadFieldsDynamicMenuDialog(accountId, reference, responseFields, isEditing, false);
            }
        }
    });
    $('#table_wrapper > .dt-buttons').appendTo("div.header-btns .actions_container");
    if ($("div.header-btns .dataTables_length").length > 0) {
        $("div.header-btns .dataTables_length").remove();
    }

    $(".dataTables_length").addClass('btn pull-right').appendTo('div.header-btns');
}

function filterItems(evt, element, listName) {
    sanitizeInput(evt);
    var value = $(element).val().toLowerCase();
    $(".form-select#" + listName + ' .mb-3.form-checkbox-containers').each(function () {
        var thisCheckBoxValue = $(this).find('input[type="checkbox"]').parent().find('label').text().toLowerCase();
        if (thisCheckBoxValue.includes(value)) {
            $(this).removeClass('hide');
        } else {
            $(this).addClass('hide');
        }
    });
}

function dropDownActionsToggle() {
    $('.actions_container').toggleClass('hide');
}

function htmlencode(str) {
    return str.replace(/[&<>"']/g, function ($0) {
        return "&" + {"&": "amp", "<": "lt", ">": "gt", '"': "quot", "'": "#39"}[$0] + ";";
    });
}

function stopPropagation(evt) {
    sanitizeInput(evt);
    if (evt.stopPropagation !== undefined) {
        evt.preventDefault();
        evt.stopPropagation();
    } else {
        evt.cancelBubble = true;
    }
}

var dateFormats = {
    "iso_int": "YYYY-MM-DD",
    "short_date": "DD/MM/YYYY",
    "iso_date_time": "YYYY-MM-DDTHH:MM:SS",
    "iso_date_time_utc": "YYYY-MM-DDTHH:MM:SSZ"
    //define other well known formats if you want
}

function getFormat(d) {
    for (var prop in dateFormats) {
        if (moment(d, dateFormats[prop], true).isValid()) {
            return dateFormats[prop];
        }
    }
    return null;
}

function openInNewTab(href) {
    Object.assign(document.createElement('a'), {
        target: '_blank',
        rel: 'noopener noreferrer',
        href: href,
    }).click();
}

function UrlExists(url) {
    var http = new XMLHttpRequest();
    http.open('HEAD', url, true);
    http.send();
    if (http.status != 404) {
        return true;
    } else {
        return false;
    }
}

function unclickIt(thisSpanMenu, thisValue, type) {
    thisValue = thisValue.replace(/ /g, '_');
    if (type === 'edit') {
        $('div#e-' + thisSpanMenu + ' input[value="' + thisValue + '"]').prop('checked', false);
        $('#e-added-' + thisValue).remove();
    }
    if (type === 'add') {
        $('div#a-' + thisSpanMenu + ' input[value="' + thisValue + '"]').prop('checked', false);
        $('#a-added-' + thisValue).remove();
    }
}

function clickIt(thisSpanMenu, thisValue, thisValueBeautified, type) {
    if (type === 'edit') {
        if ($('div#e-' + thisSpanMenu + ' input[value="' + thisValue.replace(/ /g, '_') + '"]').prop('checked')) {
            $('div#e-' + thisSpanMenu + '-selected-container').append('<span onclick="unclickIt(\'' + thisSpanMenu + '\', \'' + thisValue + '\', \'' + type + '\')" class="added-item-to-multi-checkbox" id="e-added-' + thisValue + '"><button type="button" id="e-remove-' + thisValue + '" class="btn btn-close"></button>' + thisValueBeautified + '<span>');
        } else {
            $('#e-added-' + thisValue).remove();
        }
    }
    if (type === 'add') {
        if ($('div#a-' + thisSpanMenu + ' input[value="' + thisValue + '"]').prop('checked')) {
            $('div#a-' + thisSpanMenu + '-selected-container').append('<span onclick="unclickIt(\'' + thisSpanMenu + '\', \'' + thisValue + '\', \'' + type + '\')" class="added-item-to-multi-checkbox" id="a-added-' + thisValue + '"><button type="button" id="a-remove-' + thisValue + '" class="btn btn-close"></button>' + thisValueBeautified + '<span>');
        } else {
            $('#a-added-' + thisValue).remove();
        }
    }
}

function createPublishTicket(accountId, reference, type, server, path, button) {

    accountId = escapeHtml(accountId);
    reference = escapeHtml(reference);
    type = escapeHtml(type);
    server = escapeHtml(server);
    path = escapeHtml(path);
    button = escapeHtml(button);

    var dueDate = new Date();
    dueDate.setDate(dueDate.getDate() + 5);
    var formattedDate = dueDate.toISOString().slice(0, 10);

    var entryId = $('.table_' + reference).find('input[type="checkbox"]:checked').val();

    form_data = {
        accountId: accountId,
        title: 'Menu ' + reference + ' submission',
        type: 4,
        priority: 1,
        dueDate: formattedDate,
        listName: reference,
        entryId: entryId
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

function doRefreshPage() {
    // Get the current page URL
    var url = window.location.href;

    // Check if the URL contains a query string
    if (url.indexOf('?') !== -1) {
        // Remove the query string
        var updatedUrl = url.substring(0, url.indexOf('?'));

        // Replace the current URL without the query string
        window.history.replaceState({}, document.title, updatedUrl);
    }

    location.reload(true);
}

function removeFileDoc(thisId) {
    document.getElementById('e-' + thisId + '-side').remove();
    document.getElementById('mb3_img-' + thisId).remove();
    document.getElementById('remove-' + thisId).remove();
}

function UrlExistsCrossDomain(url) {
    var iframe = document.createElement('iframe');
    var iframeError;

    iframe.onload = function () {
        return true;
        clearTimeout(iframeError);
    }

    iframeError = setTimeout(function () {
        return false;
    }, 3000);

    iframe.src = url;
    document.getElementsByTagName("body")[0].appendChild(iframe);
}

function replaceSpecialCharacters(str) {
    // Define the replacements using an object
    const replacements = {
        'á': 'a',
        'é': 'e',
        'í': 'i',
        'ó': 'o',
        'ú': 'u',
        'ç': 'c',
        'ñ': 'n',
        'ã': 'a',
        'õ': 'o',
        // German
        'ä': 'ae',
        'ö': 'oe',
        'ü': 'ue',
        'ß': 'ss',
        // French
        'à': 'a',
        'è': 'e',
        'ù': 'u',
        'â': 'a',
        'ê': 'e',
        'î': 'i',
        'ô': 'o',
        'û': 'u',
        'ë': 'e',
        'ï': 'i',
        // Spanish
        'á': 'a',
        'é': 'e',
        'í': 'i',
        'ó': 'o',
        'ú': 'u',
        'ñ': 'n',
        // Italian
        'à': 'a',
        'è': 'e',
        'ì': 'i',
        'ò': 'o',
        'ù': 'u',
        // Portuguese
        'á': 'a',
        'é': 'e',
        'í': 'i',
        'ó': 'o',
        'ú': 'u',
        'ã': 'a',
        'õ': 'o',
        // Greek
        'α': 'a',
        'β': 'b',
        'γ': 'g',
        'δ': 'd',
        'ε': 'e',
        'ζ': 'z',
        'η': 'i',
        'θ': 'th',
        'ι': 'i',
        'κ': 'k',
        'λ': 'l',
        'μ': 'm',
        'ν': 'n',
        'ξ': 'x',
        'ο': 'o',
        'π': 'p',
        'ρ': 'r',
        'σ': 's',
        'τ': 't',
        'υ': 'u',
        'φ': 'f',
        'χ': 'ch',
        'ψ': 'ps',
        'ω': 'o',
        'ά': 'a',
        'έ': 'e',
        'ή': 'i',
        'ί': 'i',
        'ό': 'o',
        'ύ': 'u',
        'ώ': 'o',
        'ς': 's',
        'ą': 'a',
        'ć': 'c',
        'ę': 'e',
        'ł': 'l',
        'ń': 'n',
        'ó': 'o',
        'ś': 's',
        'ź': 'z',
        'ż': 'z',
        // Czech
        'á': 'a',
        'é': 'e',
        'í': 'i',
        'ó': 'o',
        'ú': 'u',
        'ů': 'u',
        'ý': 'y',
        'č': 'c',
        'ď': 'd',
        'ě': 'e',
        'ň': 'n',
        'ř': 'r',
        'š': 's',
        'ť': 't',
        'ů': 'u',
        'ž': 'z',
        'Á': 'A',
        'É': 'E',
        'Í': 'I',
        'Ó': 'O',
        'Ú': 'U',
        'Ů': 'U',
        'Ý': 'Y',
        'Č': 'C',
        'Ď': 'D',
        'Ě': 'E',
        'Ň': 'N',
        'Ř': 'R',
        'Š': 'S',
        'Ť': 'T',
        'Ů': 'U',
        'Ž': 'Z',
        // Mandarin
        '你': 'ni',
        '好': 'hao',
        '再见': 'zaijian',
        '谢谢': 'xiexie',
        '早上好': 'zaoshanghao',
        '晚安': 'wanan',
        '我爱你': 'woaini',
        '中国': 'zhongguo',
        '北京': 'beijing',
        '上海': 'shanghai',
        '天安门': 'tiananmen',
        '欢迎': 'huanying',
        '喜欢': 'xihuan',
        '学习': 'xuexi',
        '工作': 'gongzuo',
        '音乐': 'yinyue',
        '电影': 'dianying',
        '朋友': 'pengyou',
        '美食': 'meishi',
        '旅行': 'lvxing',
        '生日快乐': 'shengrikuaile',
        '幸福': 'xingfu',
        '成功': 'chenggong',
        '健康': 'jiankang',
        '家庭': 'jiating',
        '父母': 'fumu',
        '婚礼': 'hunli',
        '微笑': 'weixiao',
        '快乐': 'kuaile',
        '梦想': 'mengxiang',
        '努力': 'nuli',
        '勇敢': 'yonggan',
        '希望': 'xiwang',
        '自由': 'ziyou',
        '和平': 'heping',
        '友谊': 'youyi',
        '爱情': 'aiqing',
        '唔該': 'm̀h_goi',
        '謝謝': 'jeh_jeh',
        '早晨': 'jóu_sàhn',
        '晚安': 'màahnōn',
        '我愛你': 'ngóh_ói_néih',
        '中國': 'jūng_gwok',
        '香港': 'hēung_góng',
        '澳門': 'ou_mùhn',
        '廣東話': 'gwóng_dūng_wá',
        '食飯': 'sik_faahn',
        '飲茶': 'yám_chà',
        '唱歌': 'chèung_gō',
        '跳舞': 'tiuh_móuh',
        '節日': 'jit_yàht',
        '生日快樂': 'sāang_yaht_faai_lok',
        '幸福': 'hohng_fūk',
        '成功': 'gìhng_sūng',
        '健康': 'gin_hōng',
        '家庭': 'gā_ting',
        '父母': 'fù_mouh',
        '婚禮': 'fān_léih',
        '微笑': 'mèih_siu',
        '快樂': 'faai_lok',
        '夢想': 'múhng_coeng',
        '努力': 'noh_lihk',
        '勇敢': 'yúng_góng',
        '希望': 'hēi_mong',
        '自由': 'jih_yàuh',
        '和平': 'wòh_pìhng',
        '友誼': 'yáuh_yìh',
        '愛情': 'oi_ching',
        '&': 'and'
    };

    // Create a regular expression pattern using the special characters
    const pattern = new RegExp(Object.keys(replacements).join('|'), 'g');

    // Replace the special characters with their normal letter equivalents
    const result = str.replace(pattern, match => replacements[match]);

    return result;
}