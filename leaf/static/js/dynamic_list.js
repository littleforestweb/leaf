/*
    Created on : 26 Jun 2022, 08:49:12
    Author     : joao
*/

async function publishList() {
    await populateUserList();
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

async function populateEditDynamicListDialog(accountId, reference, type, itemToSelect = false, userId = false) {

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
    let jsonConfig = await $.get("/api/get_list_configuration/" + accountId + "/" + reference, function (result) {
        return result;
    });

    var values = jsonConfig.columns;

    if (values && values[0]) {

        var fields = values[0][4].split(';');
        for (var field in fields) {
            $('#s-fields option[value="' + fields[field] + '"]').attr("selected", "selected");
        }

        var mfields = [];
        if (values[0][2]) {
            mfields = values[0][2].split(',');
        }
    }

    $.ajax({
        type: "GET",
        url: "/api/settings/" + accountId,
        success: async function (allAccountSettings) {
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
                        var spanId = spans[x].getAttribute("id").split('_pos_')[0].toLowerCase();
                        var thisFieldItem = allAccountSettings[f][2].toLowerCase();
                        if (allAccountSettings[f][1] === reference && thisFieldItem === spanId) {

                            if (allAccountSettings[f][3] === '-_leaf_users_-') {
                                let thisValue = escapeHtml(spans[x].textContent.replace(/__BACKSLASH__TO_REPLACE__/g, "\\").replace(/&comma;/g, ','));
                                let getUserDetails = await getUserDetailsByValue(thisValue, allAccountSettings[f][5]);
                                let thisLabel = getUserDetails.user[0][allAccountSettings[f][5]];

                                if (type === 'edit') {
                                    $('#e-' + spanId).attr('disabled', true);
                                    if ($('#e-' + spanId).val() === '') {
                                        $('#e-' + spanId).val(thisLabel).removeAttr('id', 'e-' + spanId).attr('id', 'eRobot-' + spanId).attr('class', 'form-control eRobot-field');
                                        $('#eRobot-' + spanId).parent().append('<input id="e-' + spanId + '" type="hidden" value="' + userId + '" />');
                                    }
                                } else {
                                    $('#a-' + spanId).attr('disabled', true);
                                }

                            } else if (allAccountSettings[f][6] && (allAccountSettings[f][6] === "select" || allAccountSettings[f][6] === "multiselect" || allAccountSettings[f][6] === "multi_checkbox")) {

                                $.ajax({
                                    type: "GET",
                                    url: "/api/get_value_columns_with_index/" + accountId + "/" + allAccountSettings[f][3] + "/" + allAccountSettings[f][4] + "/" + allAccountSettings[f][5] + "/" + x + "/" + f,
                                    success: function (allFieldsResponse) {
                                        indexToKeep = allFieldsResponse.indexToKeep;
                                        indexToKeepForAccountSettings = allFieldsResponse.indexToKeepForAccountSettings;
                                        allFieldsResponse = allFieldsResponse.columns;

                                        var thisSpanList = (spans[indexToKeep] ? spans[indexToKeep].getAttribute("id").split('_pos_')[0] : '');
                                        var thisSpanId = (spans[indexToKeep] ? spans[indexToKeep].getAttribute("id").split('_pos_')[1] : '');

                                        var mandatoryClass = '';
                                        for (var mfield in mfields) {
                                            if (mfields[mfield] === thisSpanList) {
                                                mandatoryClass = 'mandatoryField';
                                            }
                                        }

                                        var thisFieldValue = "";
                                        if (type === 'edit') {
                                            thisFieldValue = $('#' + thisSpanList + '_pos_' + thisSpanId).text();
                                        }

                                        if (allAccountSettings[indexToKeepForAccountSettings] && allAccountSettings[indexToKeepForAccountSettings][6] !== "select") {
                                            if (type === 'edit') {
                                                var fieldsDropdown = '<select name="e-' + thisSpanList + '" class="form-select form-select-md toCapitalize" id="e-' + thisSpanList + '"' + (allAccountSettings[indexToKeepForAccountSettings][6] === "multiselect" ? 'multiple' : '') + '>' + (thisFieldValue && thisFieldValue.length > 0 ? "" : '<option value="" disabled selected>Select option</option>') + '</select>';
                                                $('#e-' + thisSpanList).replaceWith(fieldsDropdown);
                                            } else {
                                                var fieldsDropdown = '<select name="a-' + thisSpanList + '" class="form-select form-select-md toCapitalize" id="a-' + thisSpanList + '"' + (allAccountSettings[indexToKeepForAccountSettings][6] === "multiselect" ? 'multiple' : '') + '>' + (thisFieldValue && thisFieldValue.length > 0 ? "" : '<option value="" disabled selected>Select option</option>') + '</select>';
                                                $('#a-' + thisSpanList).replaceWith(fieldsDropdown);
                                            }

                                        } else if (allAccountSettings[indexToKeepForAccountSettings] && allAccountSettings[indexToKeepForAccountSettings][6] === "multi_checkbox") {
                                            if (type === 'edit') {
                                                var fieldsDropdown = (($('#e-search_items_' + thisSpanList).length === 0) ? '<input type="search" onkeyup="filterItems(event, this, \'e-' + thisSpanList + '\')" class="form-control form-search form-select-md multi_checkbox" placeholder="search ' + thisSpanList + '..." id="e-search_items_' + thisSpanList + '" />' : '') + '<div name="e-' + thisSpanList + '-selected-container" class="selected-container toCapitalize" id="e-' + thisSpanList + '-selected-container"></div>' + '<div name="e-' + thisSpanList + '" class="form-select form-select-md toCapitalize" id="e-' + thisSpanList + '"' + (allAccountSettings[indexToKeepForAccountSettings][6] === "multi_checkbox" ? 'multiple_checkbox' : '') + '>' + (thisFieldValue && thisFieldValue.length > 0 ? "" : '') + '</div>';
                                                $('#e-' + thisSpanList).replaceWith(fieldsDropdown);
                                            } else {
                                                var fieldsDropdown = (($('#a-search_items_' + thisSpanList).length === 0) ? '<input type="search" onkeyup="filterItems(event, this, \'a-' + thisSpanList + '\')" class="form-control form-search form-select-md multi_checkbox" placeholder="search ' + thisSpanList + '..." id="a-search_items_' + thisSpanList + '" />' : '') + '<div name="a-' + thisSpanList + '-selected-container" class="selected-container toCapitalize" id="a-' + thisSpanList + '-selected-container"></div>' + '<div name="a-' + thisSpanList + '" class="form-select form-select-md toCapitalize" id="a-' + thisSpanList + '"' + (allAccountSettings[indexToKeepForAccountSettings][6] === "multi_checkbox" ? 'multiple_checkbox' : '') + '>' + (thisFieldValue && thisFieldValue.length > 0 ? "" : '') + '</div>';
                                                $('#a-' + thisSpanList).replaceWith(fieldsDropdown);
                                            }
                                        }

                                        var arrayToCompare = [];
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
                                                            $('select#e-' + thisSpanList).append('<option value="' + thisValue + '">' + thisLabel + '</option>');
                                                        } else {
                                                            $('select#a-' + thisSpanList).append('<option value="' + thisValue + '">' + thisLabel + '</option>');
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
                                                            $('select#e-' + thisSpanList).addClass(mandatoryClass).append('<option value="' + thisValue + '">' + thisLabel + '</option>');
                                                        } else {
                                                            $('select#a-' + thisSpanList).addClass(mandatoryClass).append('<option value="' + thisValue + '">' + thisLabel + '</option>');
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
                                                        $('div#e-' + thisSpanList).addClass(mandatoryClass).append('<div class="mb-3 form-checkbox-containers"><input onclick="clickIt(\'' + thisSpanList + '\', \'' + thisValue.replace(/ /g, '_') + '\', \'' + thisLabel + '\', \'' + type + '\')" type="checkbox" value="' + thisValue.replace(/ /g, '_') + '" /><label for="' + thisValue.replace(/ /g, '_') + '">' + thisLabel + '</label></div>');
                                                    } else {
                                                        $('div#a-' + thisSpanList).addClass(mandatoryClass).append('<div class="mb-3 form-checkbox-containers"><input onclick="clickIt(\'' + thisSpanList + '\', \'' + thisValue.replace(/ /g, '_') + '\', \'' + thisLabel + '\', \'' + type + '\')" type="checkbox" value="' + thisValue.replace(/ /g, '_') + '" /><label for="' + thisValue.replace(/ /g, '_') + '">' + thisLabel + '</label></div>');
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
                                                            $('select#e-' + thisSpanList).addClass(mandatoryClass).append('<option value="' + thisValue + '">' + thisLabel + '</option>');
                                                        } else {
                                                            $('select#a-' + thisSpanList).addClass(mandatoryClass).append('<option value="' + thisValue + '">' + thisLabel + '</option>');
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
                                                            $('div#e-' + thisSpanList).addClass(mandatoryClass).append('<div class="mb-3 form-checkbox-containers"><input onclick="clickIt(\'' + thisSpanList + '\', \'' + thisValue.replace(/ /g, '_') + '\', \'' + thisValueBeautified + '\', \'' + type + '\')" type="checkbox" value="' + thisValue.replace(/ /g, '_') + '" /><label for="' + thisValue.replace(/ /g, '_') + '">' + thisLabel + '</label></div>');
                                                        } else {
                                                            $('div#a-' + thisSpanList).addClass(mandatoryClass).append('<div class="mb-3 form-checkbox-containers"><input onclick="clickIt(\'' + thisSpanList + '\', \'' + thisValue.replace(/ /g, '_') + '\', \'' + thisValueBeautified + '\', \'' + type + '\')" type="checkbox" value="' + thisValue.replace(/ /g, '_') + '" /><label for="' + thisValue.replace(/ /g, '_') + '">' + thisLabel + '</label></div>');
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
                                                var thisValue = escapeHtml(thisFieldValue[i].trim().toLowerCase());
                                                if (thisFieldValue[i].includes('__BACKSLASH__TO_REPLACE__')) {
                                                    thisValue = thisFieldValue[i].substring(thisFieldValue[i].lastIndexOf('__BACKSLASH__TO_REPLACE__') + 25);
                                                }
                                                if (thisFieldValue[i].includes('\\')) {
                                                    thisValue = thisValue.substring(thisValue.lastIndexOf('\\') + 1);
                                                } else {
                                                    thisValue = thisValue.substring(thisValue.lastIndexOf('/') + 1);
                                                }
                                                $('select#e-' + thisSpanList + ' option[value="' + thisValue + '"]').attr("selected", "selected");
                                            }
                                        } else if (type === 'edit' && allAccountSettings[indexToKeepForAccountSettings] && allAccountSettings[indexToKeepForAccountSettings][6] === "multi_checkbox") {
                                            thisFieldValue = thisFieldValue.replace(/&amp;comma;/g, ',').split(';');
                                            splitArray = thisFieldValue.map(element => element.trim());
                                            var uniqueSet = new Set(splitArray);
                                            thisFieldValue = [...uniqueSet];
                                            for (var i = 0; i < thisFieldValue.length; i++) {
                                                var thisValue = escapeHtml(thisFieldValue[i].trim().toLowerCase());
                                                var thisValueBeautified = escapeHtml($('div#e-' + thisSpanList).find('input[value="' + thisValue.replace(/ /g, '_') + '"]').parent().find('label').text());
                                                if (thisFieldValue[i].includes('__BACKSLASH__TO_REPLACE__')) {
                                                    thisValue = thisFieldValue[i].substring(thisFieldValue[i].lastIndexOf('__BACKSLASH__TO_REPLACE__') + 25);
                                                }
                                                if (thisFieldValue[i].includes('\\')) {
                                                    thisValue = thisValue.substring(thisValue.lastIndexOf('\\') + 1);
                                                } else {
                                                    thisValue = thisValue.substring(thisValue.lastIndexOf('/') + 1);
                                                }

                                                $('div#e-' + thisSpanList + ' input[value="' + thisValue.replace(/ /g, '_') + '"]').prop('checked', true);

                                                if (type === 'edit' && thisValue !== '' && thisValueBeautified) {
                                                    $('div#e-' + thisSpanList + '-selected-container').append('<span onclick="unclickIt(\'' + thisSpanList + '\', \'' + thisValue.replace(/ /g, '_') + '\', \'' + type + '\')" class="added-item-to-multi-checkbox" id="e-added-' + thisValue.replace(/ /g, '_') + '"><button type="button" id="e-remove-' + thisValue.replace(/ /g, '_') + '" class="btn btn-close"></button>' + thisValueBeautified + '<span>');
                                                }
                                            }
                                        } else if ((type === 'edit') && (allAccountSettings[indexToKeepForAccountSettings] && allAccountSettings[indexToKeepForAccountSettings][6] !== "multiselect" && allAccountSettings[indexToKeepForAccountSettings][6] !== "multi_checkbox")) {
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
                                                $('select#e-' + thisSpanList).val(thisValue);
                                            }
                                        }
                                    },
                                    error: function (XMLHttpRequest, textStatus, errorThrown) {
                                        $('#errorModal').modal('show');
                                    }
                                });
                            } else {

                                var thisSpanList = spans[x].getAttribute("id").split('_pos_')[0];

                                var mandatoryClass = '';
                                for (var mfield in mfields) {
                                    if (mfields[mfield] === thisSpanList) {
                                        mandatoryClass = 'mandatoryField';
                                    }
                                }

                                // Populate edit fields
                                let site_dynamic_list = escapeHtml(spans[x].textContent.replace(/__BACKSLASH__TO_REPLACE__/g, "\\").replace(/&comma;/g, ','));

                                if (allAccountSettings[f][6] && allAccountSettings[f][6] === "textarea") {
                                    var attrs = {};

                                    $.each($('#e-' + spanId).attributes, function () {
                                        attrs[this.name] = this.value;
                                    });

                                    $('#e-' + spanId).replaceWith($('<textarea name="e-' + spanId + '" class="form-control ' + mandatoryClass + '" id="e-' + spanId + '"></textarea>'));
                                    $('#a-' + spanId).replaceWith($('<textarea name="a-' + spanId + '" class="form-control ' + mandatoryClass + '" id="a-' + spanId + '"></textarea>'));
                                    if (type === 'edit') {
                                        $('#e-' + spanId).val(site_dynamic_list);
                                    }

                                } else if (allAccountSettings[f][6] && allAccountSettings[f][6] === "input") {
                                    if (type === 'edit') {
                                        $('#e-' + spanId).addClass(mandatoryClass).val(site_dynamic_list);
                                    } else {
                                        $('#a-' + spanId).addClass(mandatoryClass);
                                    }

                                } else if (allAccountSettings[f][6] && allAccountSettings[f][6] === "wysiwyg") {

                                    if (type === 'edit') {
                                        $('#e-' + spanId).parent().find("div.ck-editor").remove();
                                        $('#e-' + spanId).replaceWith($('<textarea name="e-' + spanId + '" class="form-control text-editor ' + mandatoryClass + '" id="e-' + spanId + '"></textarea>'));

                                        document.getElementById('e-' + spanId).innerHTML = site_dynamic_list;

                                        CKEDITOR.replace(document.querySelector('#e-' + spanId), {
                                            fullPage: false,
                                            allowedContent: true,
                                            // on: {
                                            //     instanceReady: function (ev) {
                                            //         ev.editor.setData(site_dynamic_list);
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
                                        var formatFound = getFormat(site_dynamic_list);
                                        // if(formatFound !==null){
                                        //    console.log(formatFound);
                                        // }

                                        $('#e-' + spanId).addClass(mandatoryClass).val(site_dynamic_list);
                                        $('#e-' + spanId).datepicker({dateFormat: 'yy-mm-dd', endDate: "today", maxDate: todaysDate});
                                    } else {
                                        $('#a-' + spanId).addClass(mandatoryClass).val();
                                        $('#a-' + spanId).datepicker({dateFormat: 'yy-mm-dd', endDate: "today", maxDate: todaysDate});
                                    }
                                } else if (allAccountSettings[f][6] && allAccountSettings[f][6] === "password") {
                                    if (type === 'edit') {
                                        $('#e-' + spanId).addClass(mandatoryClass).val(site_dynamic_list).get(0).type = 'password';
                                    } else {
                                        $('#a-' + spanId).addClass(mandatoryClass).get(0).type = 'password';
                                    }
                                } else if (allAccountSettings[f][6] && allAccountSettings[f][6] === "hidde-it") {
                                    if (type === 'edit') {
                                        $('#e-' + spanId).addClass(mandatoryClass).parent().addClass('hide');
                                        $('#e-' + spanId).val(site_dynamic_list).get(0).type = 'hidden';
                                    }
                                    if (type === 'add') {
                                        $('#a-' + spanId).addClass(mandatoryClass).parent().addClass('hide');
                                        $('#a-' + spanId).val(site_dynamic_list).get(0).type = 'hidden';
                                    }
                                } else if (allAccountSettings[f][6] && allAccountSettings[f][6] === "autoGenerated") {
                                    if (type === 'edit') {
                                        $('#e-' + spanId).addClass(mandatoryClass).parent().addClass('hide').addClass('autoGenerated');
                                        $('#e-' + spanId).val(site_dynamic_list).get(0).type = 'hidden';
                                    } else {
                                        $('#a-' + spanId).addClass(mandatoryClass).parent().addClass('hide').addClass('autoGenerated');
                                        $('#a-' + spanId).get(0).type = 'hidden';
                                    }
                                } else if (allAccountSettings[f][6] && allAccountSettings[f][6] === "disabledField") {
                                    if (type === 'edit') {
                                        $('#e-' + spanId).addClass(mandatoryClass).parent().addClass('disabledField');
                                        $('#e-' + spanId).val(site_dynamic_list).attr('disabled', true);
                                    } else {
                                        $('#a-' + spanId).addClass(mandatoryClass).parent().addClass('disabledField');
                                        $('#a-' + spanId).attr('disabled', true);
                                    }
                                } else if (allAccountSettings[f][6] && allAccountSettings[f][6] === "pdf" || allAccountSettings[f][6] && allAccountSettings[f][6] === "image") {
                                    if (type === 'edit') {
                                        if (site_dynamic_list) {
                                            site_dynamic_list = site_dynamic_list.replace('JPG', 'jpg').replace('JPEG', 'jpeg').replace('PNG', 'png').replace('PDF', 'pdf').replace('GIF', 'gif');
                                            var lastIndexOfFileName = site_dynamic_list.substring(site_dynamic_list.lastIndexOf('/') + 1);
                                            if (site_dynamic_list.toLowerCase().includes('static')) {
                                                var srcVal = site_dynamic_list.toLowerCase();
                                            } else {
                                                if (allAccountSettings[f][6] === 'pdf') {
                                                    if (site_dynamic_list.toLowerCase().includes('http')) {
                                                        var srcVal = site_dynamic_list;
                                                    } else {
                                                        var srcVal = original_images_webpath + site_dynamic_list;
                                                    }
                                                } else {

                                                    if (site_dynamic_list.toLowerCase().includes('http')) {
                                                        var srcVal = site_dynamic_list;
                                                    } else {
                                                        var srcVal = original_images_webpath + site_dynamic_list;
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

                                            $('#e-' + spanId).parent().append('<input type="hidden" class="hidden-field" name="e-' + spanId + '-side" id="e-' + spanId + '-side" value="' + site_dynamic_list + '" />');
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
                                        $('#e-' + spanId).addClass(mandatoryClass).val(site_dynamic_list);
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

async function publishDynamicList(accountId, reference, env, preview_server, dynamic_path, thisTemplate, thisParameters, fieldsToLink, justPreview, lastEntry, thisCountry = false, thisButton, userId = false) {

    accountId = escapeHtml(accountId);
    reference = escapeHtml(reference);
    env = escapeHtml(env);
    preview_server = escapeHtml(preview_server);
    dynamic_path = escapeHtml(dynamic_path);
    thisTemplate = escapeHtml(thisTemplate);
    thisParameters = escapeHtml(thisParameters);
    fieldsToLink = escapeHtml(fieldsToLink);
    lastEntry = escapeHtml(lastEntry);

    $(".previewButton").prop('disabled', true);

    var selectedItem = '';
    // Get list configuration
    let jsonConfig = await $.get("/api/get_list_configuration/" + accountId + "/" + reference, function (result) {
        return result;
    });
    var values = jsonConfig.columns;

    let jsonAllTemplate = await $.get("/api/get_list_template/" + accountId + "/" + reference, function (result) {
        return result;
    });
    jsonAllTemplate = jsonAllTemplate.columns;

    let jsonColumns = await $.get("/api/get_list_columns_with_properties/" + accountId + "/" + reference, function (result) {
        return result;
    });

    var headColumns = jsonColumns.columns;

    var thisTemplate = '';
    var listTemplateId = '';
    if (jsonAllTemplate && jsonAllTemplate[0]) {
        thisTemplate = jsonAllTemplate[0][3];
        listTemplateId = jsonAllTemplate[0][0];
    }

    const regex = /{([^{}]+)}/g;
    const matches = [];
    let match;

    while ((match = regex.exec(thisTemplate)) !== null) {
        matches.push(match[1]);
    }

    publication_names = ['pubdate', 'pub-date', 'pub_date', 'publication_date', 'publication-date', 'publicationdate']
    var fieldsToLink = thisTemplate;
    var thisValId = '';
    for (var field in matches) {
        thisValId = escapeHtml($('input[type="checkbox"]:checked').val());
        if (!thisValId) {
            thisValId = escapeHtml($('#e-id').val());
        }
        var singleField = $('span#' + matches[field] + '_pos_' + thisValId).html();
        if (matches[field] === "year" || matches[field] === "month" || matches[field] === "day") {
            let matchingColumn = null;

            for (const column of headColumns) {
                if (publication_names.includes(column[2].toLowerCase())) {
                    matchingColumn = column;
                    break;
                }
            }
            singleField = $('span#' + matchingColumn[2].toLowerCase() + '_pos_' + thisValId).html();
            singleField = extractMonthAndDay(singleField, matches[field]);
            singleField = singleField.toString();
        }
        singleField = singleField.split('/');
        singleField = singleField[singleField.length - 1];
        fieldsToLink = fieldsToLink.replace("{" + matches[field] + "}", singleField);

        selectedItem = thisValId;
    }

    var checkCountryField = $('.table_' + reference + ' input[type="checkbox"]:checked').parent().parent().find('span.country pre .hidden');
    if (!thisCountry && checkCountryField.length > 0) {
        thisCountry = $('.table_' + reference + ' input[type="checkbox"]:checked').parent().parent().find('span.country pre .hidden').html().trim();
        thisCountry = thisCountry.replace(/,/g, ';');
    }

    $.ajax({
        type: "POST",
        url: "/publish/account_" + accountId + "_list_" + reference + '/' + accountId + '/' + reference + '/' + env,
        data: JSON.stringify({
            "country_to_update": thisCountry,
            "file_url_path": fieldsToLink + page_extension,
            "list_template_id": listTemplateId,
            "list_item_id": selectedItem
        }),
        contentType: 'application/json',
        dataType: 'json',
        cache: false,
        processData: false,
        success: function (updated) {

            $('#publishDynamicListSuccessNotification').toast('show');

            if ((env !== 'saveOnly' && env !== 'save')) {
                if (thisTemplate !== '') {
                    openInNewTab(preview_server + fieldsToLink + page_extension);
                } else {
                    alert("There is no preview setting for this List yet. Please add one to preview this type.")
                }
            }

            $('#editDynamicListSuccessNotification').toast('show');
            if (env !== "saveOnly" && env !== "preview" && !justPreview) {
                location.reload(true);
                //doRedrawTable(true, updated.lists, true);
            } else {
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

            $(".previewButton").prop('disabled', false);
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

            $(".previewButton").prop('disabled', false);
        }
    });
}


async function updateDynamicList(accountId, reference, env, preview_server, dynamic_path, justPreview, thisButton, userId = false) {

    accountId = escapeHtml(accountId);
    reference = escapeHtml(reference);
    env = escapeHtml(env);
    preview_server = escapeHtml(preview_server);
    dynamic_path = escapeHtml(dynamic_path);

    // thisButton.classList.add('disabled');
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
            //THIS IS SPECIFIC FOR THE EVERSHEDS PEOPLE LIST
            if (reference === 'people') {
                var forename = escapeHtml($('#e-forename').val());
                if (forename) {
                    forename = forename.replace(/,/g, '&comma;');
                } else {
                    forename = escapeHtml($('#e-firstname').val());
                    if (forename) {
                        forename = forename.replace(/,/g, '&comma;');
                    }
                }
                var surname = escapeHtml($('#e-surname').val());
                if (surname) {
                    surname = surname.replace(/,/g, '&comma;');
                } else {
                    surname = escapeHtml($('#e-lastname').val());
                    if (surname) {
                        surname = surname.replace(/,/g, '&comma;');
                    }
                }

                idToLink = surname.replace(/ /g, '_').replace(/\\t/, '') + '_' + forename.replace(/ /g, '_').replace(/\\t/, '') + '-' + $('#e-id').val();
                idToLink = idToLink.replace(/\'/g, "_").replace(/\"/g, "_").replace(/“/g, "_").replace(/„/g, "_").replace(/:/g, "_").replace(/[^a-zA-Z0-9 ]/, '_').replace(/’/g, "_").replace(/\?/g, "_").replace(/!/g, "_").replace(/¿/g, "_").replace(/¡/g, "_");
                $(this).find('input[type="hidden"]').val(idToLink);
            } else {
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
                autoGen = autoGen.replace(/ /g, '_').replace(/\\t/g, '').replace(/,/g, ''); //  + '-' + $('#e-id').val()
                autoGen = autoGen.replace(/\'/g, "_").replace(/\"/g, "_").replace(/“/g, "_").replace(/„/g, "_").replace(/:/g, "_").replace(/[^a-zA-Z0-9 ]/, '_').replace(/’/g, "_").replace(/\?/g, "_").replace(/!/g, "_").replace(/¿/g, "_").replace(/¡/g, "_");
                $(this).find('input[type="hidden"]').val(autoGen);
            }
        }
    })

    var form_data = await getFormData('edit-' + reference, userId);

    if (!form_data[0] || (form_data[0] && form_data[0].mandatoryFields != true)) {

        // Get list configuration
        let jsonConfig = await $.get("/api/get_list_configuration/" + accountId + "/" + reference, function (result) {
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
        }

        $.ajax({
            type: "POST",
            url: "/update/" + accountId + "/account_" + accountId + "_list_" + reference,
            contentType: 'application/json',
            data: JSON.stringify(form_data),
            dataType: 'json',
            cache: false,
            processData: false,
            success: function (updated) {

                thisCountry = form_data["e-country"];

                if (env === 'preview' && !justPreview || env === 'save' || env === 'saveOnly') {
                    if (thisCountry && thisCountry !== '' && thisCountry.length > 0) {
                        publishDynamicList(accountId, reference, env, preview_server, dynamic_path, thisTemplate, thisParameters, fieldsToLink, false, false, thisCountry, thisButton, userId);
                    } else {
                        publishDynamicList(accountId, reference, env, preview_server, dynamic_path, thisTemplate, thisParameters, fieldsToLink, false, false, false, thisButton, userId);
                    }
                } else {

                    if (thisTemplate !== '') {
                        openInNewTab(linkToPreview);
                    } else {
                        alert("You must have to setup the template in the configuration menu!")
                    }

                    if (env !== "saveOnly" && env !== "preview" && !justPreview) {
                        $('#editDynamicList').modal('hide');
                    }
                    $('#editDynamicListSuccessNotification').toast('show');
                    if (env !== "saveOnly" && env !== "preview" && !justPreview) {
                        location.reload(true);
                        //doRedrawTable(true, updated.lists, true);
                    } else {
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

async function getUserDetailsByValue(id, label) {
    var thisId = id.split(', ');
    thisId = thisId[0];
    let getUserDetails = await $.get("/api/get_single_user_by_value/" + accountId + "/" + thisId, function (result) {
        return result;
    });
    return getUserDetails
}

async function getFormData(formid, userId = false) {
    formid = escapeHtml(formid);
    var form = document.getElementById(formid);

    if (userId) {
        var checkErobotFields = Array.from(form.querySelectorAll('input.eRobot-field')).filter(element => element.id);
        for (const element of checkErobotFields) {
            $(element).parent().find('input[type="hidden"]').val(userId);
        }
    }

    var allFormElements = Array.from(form.querySelectorAll('input:not([type="search"]):not([type="checkbox"]):not(.file-name-reference):not(.clear-btn):not(.ck-hidden):not(.ck-input):not(.hidden-field):not(.document-remover):not(.eRobot-field), select, textarea, div.form-select')).filter(element => element.id);
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

async function addDynamicList(accountId, reference, env, preview_server, dynamic_path, justPreview, thisButton, userId = false) {

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
            //THIS IS SPECIFIC FOR THE EVERSHEDS PEOPLE LIST
            if (reference === 'people') {
                var forename = escapeHtml($('#a-forename').val());
                if (forename) {
                    forename = forename.replace(/,/g, '&comma;');
                } else {
                    forename = escapeHtml($('#a-firstname').val());
                    if (forename) {
                        forename = forename.replace(/,/g, '&comma;');
                    }
                }
                var surname = escapeHtml($('#a-surname').val());
                if (surname) {
                    surname = surname.replace(/,/g, '&comma;');
                } else {
                    surname = escapeHtml($('#a-lastname').val());
                    if (surname) {
                        surname = surname.replace(/,/g, '&comma;');
                    }
                }

                idToLink = surname.replace(/ /g, '_').replace(/\\t/, '') + '_' + forename.replace(/ /g, '_').replace(/\\t/, '') + '_' + $('#a-id').val();
                idToLink = idToLink.replace(/\'/g, "_").replace(/\"/g, "_").replace(/“/g, "_").replace(/„/g, "_").replace(/:/g, "_").replace(/[^a-zA-Z0-9 ]/, '_').replace(/’/g, "_").replace(/\?/g, "_").replace(/!/g, "_").replace(/¿/g, "_").replace(/¡/g, "_");
                $(this).find('input[type="hidden"]').val(idToLink);
            } else {
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
                autoGen = autoGen.replace(/ /g, '_').replace(/\\t/g, '').replace(/,/g, ''); //  + '-' + $('#a-id').val()
                autoGen = autoGen.replace(/\'/g, "_").replace(/\"/g, "_").replace(/“/g, "_").replace(/„/g, "_").replace(/:/g, "_").replace(/[^a-zA-Z0-9 ]/, '_').replace(/’/g, "_").replace(/\?/g, "_").replace(/!/g, "_").replace(/¿/g, "_").replace(/¡/g, "_");
                $(this).find('input[type="hidden"]').val(autoGen);
            }
        }
    })

    var form_data = await getFormData('add-' + reference, userId);

    if (!form_data[0] || (form_data[0] && form_data[0].mandatoryFields != true)) {

        // Get list configuration
        let jsonConfig = await $.get("/api/get_list_configuration/" + accountId + "/" + reference, function (result) {
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

        $.ajax({
            type: "POST",
            url: "/addnew/" + accountId + "/account_" + accountId + "_list_" + reference,
            contentType: 'application/json',
            data: JSON.stringify(form_data),
            dataType: 'json',
            cache: false,
            processData: false,
            success: function (updated) {

                thisCountry = form_data["e-country"];
                if (env === 'preview' && !justPreview || env === 'save' || env === 'saveOnly') {
                    if (thisCountry && thisCountry !== '' && thisCountry.length > 0) {
                        publishDynamicList(accountId, reference, env, preview_server, dynamic_path, thisTemplate, thisParameters, fieldsToLink, false, updated.lastEntry, thisCountry, thisButton, userId);
                    } else {
                        publishDynamicList(accountId, reference, env, preview_server, dynamic_path, thisTemplate, thisParameters, fieldsToLink, false, updated.lastEntry, false, thisButton, userId);
                    }
                } else {

                    if (thisTemplate !== '') {
                        openInNewTab(linkToPreview);
                    } else {
                        alert("You must have to setup the template in the configuration menu!")
                    }

                    if (env !== "saveOnly" && env !== "preview" && !justPreview) {
                        $('#editDynamicList').modal('hide');
                    }
                    $('#editDynamicListSuccessNotification').toast('show');
                    if (env !== "saveOnly" && env !== "preview" && !justPreview) {
                        location.reload(true);
                        //doRedrawTable(true, updated.lists, true);
                    } else {
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

async function deleteDynamicListEntries(accountId, reference, env, preview_server, dynamic_path, thisButton, userId = false) {

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
    let jsonConfig = await $.get("/api/get_list_configuration/" + accountId + "/" + reference, function (result) {
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
        url: "/delete/" + accountId + "/account_" + accountId + "_list_" + reference,
        data: {
            "entries_to_delete": checked_entries_str
        },
        success: function (entry) {

            // We have to check this login on publishing spliting by country
            thisCountry = checked_entries_str["e-country"];

            if (thisCountry && thisCountry !== '' && thisCountry.length > 0) {
                publishDynamicList(accountId, reference, env, preview_server, dynamic_path, thisTemplate, thisParameters, fieldsToLink, false, false, thisCountry, thisButton, userId);
            } else {
                publishDynamicList(accountId, reference, env, preview_server, dynamic_path, thisTemplate, thisParameters, fieldsToLink, false, false, false, thisButton, userId);
            }
        },
        error: function (XMLHttpRequest, textStatus, errorThrown) {
            // Hide Create Modal
            $('#deleteDynamicList').modal('hide');

            // Show Error Modal
            $('#errorDeleteModal').modal('show');
        }
    });
}

async function populateUploadFieldsDynamicListDialog(accountId, reference, fields, isEditing, complexedArray = false) {

    accountId = escapeHtml(accountId);
    reference = escapeHtml(reference);

    $.ajax({
        type: "GET",
        url: "/api/get_all_lists/" + accountId,
        success: function (response) {
            var listsDropdown = [];
            var allLists = response.lists;

            for (let j = 0; j < allLists.length; j++) {
                var listNameToPush = allLists[j][2];

                if (listNameToPush !== "account_" + accountId + "_list_settings") {
                    listNameToPush = listNameToPush.replace("account_" + accountId + "_list_", "");
                    listsDropdown.push(listNameToPush);
                }

                if (allLists.length === (j + 1)) {
                    populateDropdowns(accountId, reference, listsDropdown, fields, isEditing, complexedArray);
                }
            }
        },
        error: function (XMLHttpRequest, textStatus, errorThrown) {
            $('#errorModal').modal('show');
        }
    });
}

async function populateDropdowns(accountId, reference, listsDropdown, fields, isEditing, complexedArray) {

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
            thisElementToEdit.innerHTML = '<div class="row"><div class="form-group col-md-5"><label for="s-' + thisField + '" class="col-form-label">' + thisField + ':</label>' + '<select name="selectItem_' + thisField + '" class="form-select form-select-md connection" id="s-' + thisField + '"><option value="null" selected>Static Field</option></select></div><div class="form-group col-md-4"><label for="typeSelectItem_' + thisField + '" class="col-form-label">Field Type:</label><select name="typeSelectItem_' + thisField + '" id="typeSelectItem_' + thisField + '" class="form-select form-select-md field_type typeSelectItem_Item"><option value="input">Input</option><option value="text_area">Text Area</option><option value="wysiwyg">Wysiwyg Editor</option><option value="password">Password</option><option value="select">Single Select</option><option value="multiselect">Multi Select</option><option value="multi_checkbox">Check Box</option><option value="code">Code</option><option value="date">Date / Time</option><option value="image">Image</option><option value="pdf">PDF</option><option value="hidde-it">Hidden Field</option><option value="autoGenerated">Auto Generated</option><option value="disabledField">Disabled</option></select></div><div class="form-group col-md-3"><label for="displaySettingsItem_' + thisField + '" class="col-form-label">Visible in list:</label><select name="displaySettingsItem_' + thisField + '" id="dsi_' + thisField + '" class="form-select form-select-md"><option value="1">Yes</option><option value="0">No</option></select></div></div>';

            document.getElementById("setField-" + reference).appendChild(thisElementToEdit);

            $('#typeSelectItem_' + thisField).val(fieldType);
            $('#dsi_' + thisField).val(displaySettingsItem);

            $('select#s-' + thisField).append('<option value="-_leaf_users_-">Leaf Users</option>');
            for (var v = 0; v < listsDropdown.length; v++) {
                if (listsDropdown[v] !== reference && listsDropdown[v] !== 'configuration' && listsDropdown[v] !== 'template') {
                    $('select#s-' + thisField).append('<option value="' + escapeHtml(listsDropdown[v]) + '">' + escapeHtml(listsDropdown[v]) + '</option>');
                }

                if (!isEditing && (v + 1) === listsDropdown.length) {
                    if (linkedTable && linkedField && linkedTable !== 'None' && linkedField !== 'None' && linkedTable !== '-_leaf_users_-') {
                        $.ajax({
                            type: "GET",
                            url: "/api/get_list_columns_with_returned_id/" + accountId + "/" + linkedTable + "/" + thisField + "/" + linkedField + "/" + linkedFieldLabel,
                            success: function (allFieldsResponse) {
                                fieldToReturn = allFieldsResponse.fieldToReturn;
                                linkedFieldToReturn = allFieldsResponse.linkedFieldToReturn;
                                linkedFieldLabelToReturn = allFieldsResponse.linkedFieldLabelToReturn;
                                allFieldsResponse = allFieldsResponse.columns;

                                //$('#typeSelectItem_' + fieldToReturn).attr('disabled', 'disabled');

                                $('#s-' + fieldToReturn + '-assignedField').remove();
                                var fieldsDropdown = '<div id="s-' + fieldToReturn + '-assignedFieldRow" class="row"><div class="form-group col-md-6"><label for="s-' + fieldToReturn + '-assignedField" class="col-form-label">Assigned Field:</label><select name="s-' + fieldToReturn + '-assignedField" class="form-select form-select-md" id="s-' + fieldToReturn + '-assignedField"></select></div><div class="form-group col-md-6"><label for="s-' + fieldToReturn + '-assignedFieldLabel" class="col-form-label">Assigned Label:</label><select name="s-' + fieldToReturn + '-assignedFieldLabel" class="form-select form-select-md" id="s-' + fieldToReturn + '-assignedFieldLabel"></select></div></div>';
                                $('.s-' + fieldToReturn + '-container').append(fieldsDropdown);
                                for (var h = 0; h < allFieldsResponse.length; h++) {
                                    // console.log(allFieldsResponse[h][0]);
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
                    } else if (linkedTable === '-_leaf_users_-') {

                        $.ajax({
                            type: "GET",
                            url: "/api/get_list_columns_with_returned_id/" + accountId + "/" + linkedTable + "/" + thisField + "/" + linkedField + "/" + linkedFieldLabel,
                            success: function (allFieldsResponse) {
                                fieldToReturn = allFieldsResponse.fieldToReturn;
                                linkedFieldToReturn = allFieldsResponse.linkedFieldToReturn;
                                linkedFieldLabelToReturn = allFieldsResponse.linkedFieldLabelToReturn;

                                $('#s-' + fieldToReturn + '-assignedField').remove();
                                var fieldsDropdown = '<div id="s-' + fieldToReturn + '-assignedFieldRow" class="row"><div class="form-group col-md-6"><label for="s-' + fieldToReturn + '-assignedField" class="col-form-label">Assigned Field:</label><select name="s-' + fieldToReturn + '-assignedField" class="form-select form-select-md" id="s-' + fieldToReturn + '-assignedField"></select></div><div class="form-group col-md-6"><label for="s-' + fieldToReturn + '-assignedFieldLabel" class="col-form-label">Assigned Label:</label><select name="s-' + fieldToReturn + '-assignedFieldLabel" class="form-select form-select-md" id="s-' + fieldToReturn + '-assignedFieldLabel"></select></div></div>';
                                $('.s-' + fieldToReturn + '-container').append(fieldsDropdown);

                                $('select#s-' + fieldToReturn + '-assignedField').append('<option value="id" ' + (linkedFieldToReturn === 'id' ? "selected" : "") + '>id</option>');
                                $('select#s-' + fieldToReturn + '-assignedField').append('<option value="username" ' + (linkedFieldToReturn === 'username' ? "selected" : "") + '>username</option>');
                                $('select#s-' + fieldToReturn + '-assignedField').append('<option value="email" ' + (linkedFieldToReturn === 'email' ? "selected" : "") + '>email</option>');

                                $('select#s-' + fieldToReturn + '-assignedFieldLabel').append('<option value="id" ' + (linkedFieldLabelToReturn === 'id' ? "selected" : "") + '>id</option>');
                                $('select#s-' + fieldToReturn + '-assignedFieldLabel').append('<option value="username" ' + (linkedFieldLabelToReturn === 'username' ? "selected" : "") + '>username</option>');
                                $('select#s-' + fieldToReturn + '-assignedFieldLabel').append('<option value="email" ' + (linkedFieldLabelToReturn === 'email' ? "selected" : "") + '>email</option>');

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

            if (linkedTable === "-_leaf_users_-") {
                $('#typeSelectItem_' + thisField + ' option').attr('disabled', true);
                $('#typeSelectItem_' + thisField + ' option[value="disabledField"]').removeAttr('disabled');
                $('#typeSelectItem_' + thisField).val("disabledField");
            }
        }
    }

    $('select.form-select.connection').change(function () {
        var thisValue = escapeHtml(this.value);
        var thisId = escapeHtml($(this).attr('id'));
        var thisIdClean = thisId.replace("s-", "");

        if (thisValue !== "null" && thisValue !== "-_leaf_users_-") {
            $.ajax({
                type: "GET",
                url: "/api/get_list_columns/" + accountId + "/" + thisValue,
                success: function (allFieldsResponse) {
                    allFieldsResponse = allFieldsResponse.columns;

                    $('#typeSelectItem_' + thisIdClean + ' option').attr('disabled', true);
                    $('#typeSelectItem_' + thisIdClean + ' option[value="select"]').removeAttr('disabled');
                    $('#typeSelectItem_' + thisIdClean + ' option[value="multiselect"]').removeAttr('disabled');
                    $('#typeSelectItem_' + thisIdClean + ' option[value="multi_checkbox"]').removeAttr('disabled');

                    $('#typeSelectItem_' + thisIdClean).val("multi_checkbox");

                    $('#' + thisId + '-assignedFieldRow').remove();

                    var fieldsDropdownContainer = '<div id="' + thisId + '-assignedFieldRow" class="row"><div class="form-group col-md-6"><label for="' + thisId + '-assignedField" class="col-form-label">Assigned Field:</label><select name="' + thisId + '-assignedField" class="form-select form-select-md" id="' + thisId + '-assignedField"></select></div><div class="form-group col-md-6"><label for="' + thisId + '-assignedFieldLabel" class="col-form-label">Assigned Label:</label><select name="' + thisId + '-assignedFieldLabel" class="form-select form-select-md" id="' + thisId + '-assignedFieldLabel"></select></div></div>';
                    $('.' + thisId + '-container').append(fieldsDropdownContainer);

                    // var fieldsDropdown = '<select name="' + thisId + '-assignedField" class="form-select form-select-md" id="' + thisId + '-assignedField"></select>';
                    // var fieldsDropdownLabel = '<select name="' + thisId + '-assignedFieldLabel" class="form-select form-select-md" id="' + thisId + '-assignedFieldLabel"></select>';

                    // $('.' + thisId + '-container .row#' + thisId + '-assignedFieldRow .form-group:nth-child(1)').append(fieldsDropdown);
                    // $('.' + thisId + '-container .row#' + thisId + '-assignedFieldRow .form-group:nth-child(2)').append(fieldsDropdownLabel);

                    for (var h = 0; h < allFieldsResponse.length; h++) {
                        $('select#' + thisId + '-assignedField').append('<option value="' + allFieldsResponse[h][0] + '" ' + (allFieldsResponse[h][0] === 'id' ? "selected" : "") + '>' + allFieldsResponse[h][0] + '</option>');
                        $('select#' + thisId + '-assignedFieldLabel').append('<option value="' + allFieldsResponse[h][0] + '" ' + (allFieldsResponse[h][0] === 'id' ? "selected" : "") + '>' + allFieldsResponse[h][0] + '</option>');
                    }
                }, error: function (XMLHttpRequest, textStatus, errorThrown) {
                    $('#errorModal').modal('show');
                }
            });

        } else if (thisValue === "-_leaf_users_-") {

            $('#typeSelectItem_' + thisIdClean + ' option').attr('disabled', true);
            $('#typeSelectItem_' + thisIdClean + ' option[value="disabledField"]').removeAttr('disabled');

            $('#typeSelectItem_' + thisIdClean).val("disabledField");

            $('#' + thisId + '-assignedFieldRow').remove();

            var fieldsDropdownContainer = '<div id="' + thisId + '-assignedFieldRow" class="row"><div class="form-group col-md-6"><label for="' + thisId + '-assignedField" class="col-form-label">Assigned Field:</label><select name="' + thisId + '-assignedField" class="form-select form-select-md" id="' + thisId + '-assignedField"></select></div><div class="form-group col-md-6"><label for="' + thisId + '-assignedFieldLabel" class="col-form-label">Assigned Label:</label><select name="' + thisId + '-assignedFieldLabel" class="form-select form-select-md" id="' + thisId + '-assignedFieldLabel"></select></div></div>';
            $('.' + thisId + '-container').append(fieldsDropdownContainer);

            // var fieldsDropdown = '<select name="' + thisId + '-assignedField" class="form-select form-select-md" id="' + thisId + '-assignedField"></select>';
            // var fieldsDropdownLabel = '<select name="' + thisId + '-assignedFieldLabel" class="form-select form-select-md" id="' + thisId + '-assignedFieldLabel"></select>';

            // $('.' + thisId + '-container .row#' + thisId + '-assignedFieldRow .form-group:nth-child(1)').append(fieldsDropdown);
            // $('.' + thisId + '-container .row#' + thisId + '-assignedFieldRow .form-group:nth-child(2)').append(fieldsDropdownLabel);

            $('select#' + thisId + '-assignedField').append('<option value="id" selected>id</option>');
            $('select#' + thisId + '-assignedFieldLabel').append('<option value="id" selected>id</option>');

            $('select#' + thisId + '-assignedField').append('<option value="username">username</option>');
            $('select#' + thisId + '-assignedFieldLabel').append('<option value="username">username</option>');

            $('select#' + thisId + '-assignedField').append('<option value="email">email</option>');
            $('select#' + thisId + '-assignedFieldLabel').append('<option value="email">email</option>');

        } else {
            $('#typeSelectItem_' + thisIdClean + ' option').removeAttr('disabled');
            // $('select#' + thisId + '-assignedField').remove();
            // $('select#' + thisId + '-assignedFieldLabel').remove();
            $('#' + thisId + '-assignedFieldRow').remove();
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

async function uploadSetFieldsDynamicList(accountId, reference, action) {

    accountId = escapeHtml(accountId);
    reference = escapeHtml(reference);

    var form_data = new FormData($('#setField-' + reference)[0]);

    $.ajax({
        type: "POST",
        url: "/upload/create_middle_tables/" + accountId + "/" + reference,
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
}

async function uploadDynamicList(accountId, reference) {

    accountId = escapeHtml(accountId);
    reference = escapeHtml(reference);

    if (document.getElementById("csv_file_to_upload").files.length == 0) {
        $('#uploadFileEmpty').toast('show');
    } else {

        $("#upload-file-btn").addClass("loadingBtn").prop("disabled", true);

        var form_data = new FormData($('#upload-csv-file')[0]);

        $.ajax({
            type: "POST",
            url: "/upload/dynamic_list",
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
    // Get list columns
    let jsonColumns = await $.get("/api/get_list_columns_with_properties/" + accountId + "/" + reference, function (result) {
        return result;
    });

    var headColumns = jsonColumns.columns;
    populateUploadFieldsDynamicListDialog(accountId, reference, headColumns, false, true);
}

async function openConfiguration(accountId, reference) {

    accountId = escapeHtml(accountId);
    reference = escapeHtml(reference);

    dropDownActionsToggle();

    // Get list configuration
    let jsonConfig = await $.get("/api/get_list_configuration/" + accountId + "/" + reference, function (result) {
        return result;
    });

    var values = jsonConfig.columns;

    // Get list columns
    let jsonColumns = await $.get("/api/get_list_columns_with_properties/" + accountId + "/" + reference, function (result) {
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

        if (values[0][2]) {
            var mfields = values[0][2].split(',');
            for (var mfield in mfields) {
                $('#s-mandatory-fields option[value="' + escapeHtml(mfields[mfield]) + '"]').attr("selected", "selected");
            }
        }

        if (values[0][3]) {
            $('#s-save-by-field').val(escapeHtml(values[0][3]));
        }

        if (values[0][4]) {
            var sfields = values[0][4].split(';');
            for (var sfield in sfields) {
                $('#s-field-to-save-by option[value="' + escapeHtml(sfields[sfield]) + '"]').attr("selected", "selected");
            }
        }
    }
}

async function setConfigurationDynamicList(accountId, reference, action) {

    accountId = escapeHtml(accountId);
    reference = escapeHtml(reference);
    action = escapeHtml(action);

    if (action === 'save') {
        var form_data = await getFormData('setConfiguration-' + reference, false);

        $.ajax({
            type: "POST",
            url: "/set/configuration/" + accountId + "/" + reference,
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

async function addTemplateNameToModal() {
    if ($('#s-templates').val() !== 'false') {
        $('#template_to_delete_title').html('<strong>' + $('#s-templates option:selected').text() + '</strong>');
    }
}

async function deleteTemplate(accountId, action) {
    if ($('#s-templates').val() !== 'false') {
        $.ajax({
            type: "POST",
            url: "/delete/template/" + accountId,
            data: {
                "template_to_delete": $('#s-templates').val()
            },
            success: async function (response) {
                $('#deleteTemplate').modal('hide');
                $('#deleteTemplate form input').val('');

                doTemplatesBehaviour(accountId, reference);

                $('#deleteTemplateSuccessNotification').toast('show');
            },
            error: function (XMLHttpRequest, textStatus, errorThrown) {
                $('#errorModal').modal('show');
            }
        });
    } else {
        $('#deleteTemplateErrorNotification').toast('show');
    }
}

async function openTemplate(accountId, reference) {

    accountId = escapeHtml(accountId);
    reference = escapeHtml(reference);

    dropDownActionsToggle();

    doTemplatesBehaviour(accountId, reference);
}

async function doTemplatesBehaviour(accountId, reference) {
    // Get list templates
    let jsonListTemplate = await $.get("/api/get_list_template/" + accountId + "/" + reference, function (result) {
        return result;
    });

    // Get all templates
    let jsonAllTemplate = await $.get("/api/get_all_templates/" + accountId, function (result) {
        return result;
    });

    var availableTemplates = jsonListTemplate.columns;
    var allTemplates = jsonAllTemplate.data;

    $('#setTemplateDynamicList #s-templates').empty();
    $('#setTemplateDynamicList #s-template_location').val("");
    $('#setTemplateDynamicList #s-feed_location').val("");

    if (allTemplates) {

        if (!availableTemplates || (availableTemplates && !availableTemplates[0])) {
            $('#setTemplateDynamicList #s-templates').append('<option value="false">Select Template</option>');
        }
        for (var template in allTemplates) {
            if (availableTemplates && availableTemplates[0] && availableTemplates[0][0] === allTemplates[template][0]) {
                $('#setTemplateDynamicList #s-template_location').val(allTemplates[template][3]);
                $('#setTemplateDynamicList #s-feed_location').val(allTemplates[template][4]);
            }

            $('#setTemplateDynamicList #s-templates').append('<option value="' + allTemplates[template][0] + '" ' + (availableTemplates && availableTemplates[0] && availableTemplates[0][0] === allTemplates[template][0] ? 'selected' : '') + '>' + allTemplates[template][2] + '</option>');
        }
    }

    $('#s-templates').change(function () {
        var thisVal = $(this).val();
        if (thisVal === 'false') {
            $('#setTemplateDynamicList #s-template_location').val("");
            $('#setTemplateDynamicList #s-feed_location').val("");
            $('#s-remove-template').attr('disabled', true);
        } else {
            if (allTemplates) {
                for (var template in allTemplates) {
                    if (parseInt(allTemplates[template][0]) === parseInt(thisVal)) {
                        $('#setTemplateDynamicList #s-template_location').val(allTemplates[template][3]);
                        $('#setTemplateDynamicList #s-feed_location').val(allTemplates[template][4]);
                        $('#s-remove-template').removeAttr('disabled');
                    }
                }
            }
        }
    })

    $('#s-edit-template').on('click', function () {
        window.location.href = "/templates/" + $('#s-templates').val();
    })
}

async function setTemplateDynamicList(accountId, reference, action) {

    accountId = escapeHtml(accountId);
    reference = escapeHtml(reference);
    action = escapeHtml(action);

    if (action === 'save') {
        var form_data = await getFormData('setTemplate-' + reference, false);

        form_data["s-templates_format"] = "select";

        $.ajax({
            type: "POST",
            url: "/set/template/" + accountId + "/" + reference,
            contentType: 'application/json',
            data: JSON.stringify(form_data),
            dataType: 'json',
            cache: false,
            processData: false,
            success: function (response) {
                $('#setTemplateDynamicList').modal('hide');
                $('#setTemplateDynamicList form input:not([type="button"])').val('');

                $('#addDynamicListSuccessNotification').toast('show');

                doRedrawTable(false, false, true);
            },
            error: function (XMLHttpRequest, textStatus, errorThrown) {
                $('#errorModal').modal('show');
            }
        });
    } else {
        $('#setTemplateDynamicList').modal('hide');
        $('#setTemplateDynamicList form input:not([type="button"])').val('');
    }
}

async function getAvailableFields(accountId, reference) {

    accountId = escapeHtml(accountId);
    reference = escapeHtml(reference);

    let jsonColumns = await $.get("/api/get_available_fields/" + accountId + "/" + reference, function (result) {
        return result;
    });

    var headColumns = jsonColumns.columns;

    $(".template_fields_container").html("");
    for (var x = 0; x < headColumns.length; x++) {
        $(".template_fields_container").append('<button type="button" class="btn" val="' + headColumns[x] + '" onclick="addFieldToPattern(\'' + headColumns[x] + '\');">' + headColumns[x] + '</button>');
    }

    dropDownTemplateFieldsToggle();
}

window.addEventListener('DOMContentLoaded', async function main() {
    doRedrawTable(false, false, true);
})

async function doRedrawTable(doSetUpTable = false, responseFields = false, isEditing = false) {
    var localEnv = window.location.hostname;
    var rootPath = window.location;
    rootPath = rootPath.href.split('/list/')[0];

    $('#editDynamicList form .mb-3').html('');
    $('#addDynamicList form .mb-3').html('');
    $('#table.table_' + reference).DataTable().clear().draw();
    $('#table.table_' + reference).DataTable().destroy();

    $('#table.table_' + reference + ' thead .filters').remove();
    $('#table.table_' + reference + ' thead tr').html('<th class="center not_export_col">Select</th>');
    $('#table.table_' + reference + ' tbody').html('');
    $('#table.table_' + reference + ' tfoot tr').html('<th class="center not_export_col">Select</th>');

    // Get list columns
    let jsonColumns = await $.get("/api/get_list_columns/" + accountId + "/" + reference, function (result) {
        return result;
    });
    console.log(jsonColumns);

    let getAccountSettings = await $.get("/api/settings/" + accountId, function (allAccountSettings) {
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
                var isDisabled = false;
                var modifiedFieldLabel = false;
                var thisLabel = "";

                getAccountSettings.settings.filter(async function (e) {

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
                    } else if (headColumns[xx][0] === e[2] && e[6] === 'disabledField') {
                        isDisabled = true;
                    }


                    if (headColumns[xx][0] === e[2] && e[3] === "-_leaf_users_-") {
                        modifiedFieldLabel = true;
                        thisLabel = e[5];
                    }
                })

                $('#table.table_' + reference + " thead tr").append('<th class="' + (headColumns[xx][7] !== 0 ? ((xx === 0 || hideIt === true) ? 'hidden ' : '') : 'hidden ') + 'center sorting the_reference" id="theReferenceHead_' + xx + '">' + headColumns[xx][0] + '</th>');
                $('#table.table_' + reference + " tfoot tr").append('<th class="' + (headColumns[xx][7] !== 0 ? ((xx === 0 || hideIt === true) ? 'hidden ' : '') : 'hidden ') + 'center sorting the_reference" id="theReferenceFoot_' + xx + '">' + headColumns[xx][0] + '</th>');

                var checkHeaderClass = headColumns[xx][0];
                var checkHeaderClassWithDots = headColumns[xx][0].replace(/\./g, "__DOT__");

                if (headColumns[xx][7] !== 0 && xx !== 0) {
                    columnsToAddToShowHide.push(xx + 1);
                }

                allColumns.push({
                    aTargets: [xx + 1],
                    mData: function (source, type, row) {

                        var val = "<i style='color: #CCC;'>No data</i>";
                        var fullVal = (source[xx] ? source[xx] : "").toString();

                        val = (source[xx] ? source[xx] : "").toString();

                        val = val.replace(/__BACKSLASH__TO_REPLACE__/g, "\\");

                        if (modifiedFieldLabel && source[xx] && source[xx] !== "nan") {
                            val = val.split(', ');
                            if (thisLabel === "username") {
                                val = val[1];
                            }
                            if (thisLabel === "email") {
                                val = val[2];
                            }
                        }

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
                                            var fullVal = getAccountSettings.original_images_webpath + fullVal;
                                        } else {
                                            var fullVal = getAccountSettings.original_images_webpath + '/' + fullVal;
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
        sAjaxSource: "/api/get_list/" + accountId + "/" + reference,
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
                    populateEditDynamicListDialog('3', reference, 'edit', itemId);
                }
                $('#editDynamicList .btn.publish-btn').remove();
            } else {
                $('#search_col_index_1').val("");
                $('#search_col_index_1').keyup();
            }

            $(".loadingBg").removeClass("show");

            if (doSetUpTable === true) {
                populateUploadFieldsDynamicListDialog(accountId, reference, responseFields, isEditing, false);
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

function dropDownTemplateFieldsToggle() {
    $('.template_fields_container').toggleClass('hide');
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

function unclickIt(thisSpanList, thisValue, type) {
    thisValue = thisValue.replace(/ /g, '_');
    if (type === 'edit') {
        $('div#e-' + thisSpanList + ' input[value="' + thisValue + '"]').prop('checked', false);
        $('#e-added-' + thisValue).remove();
    }
    if (type === 'add') {
        $('div#a-' + thisSpanList + ' input[value="' + thisValue + '"]').prop('checked', false);
        $('#a-added-' + thisValue).remove();
    }
}

function clickIt(thisSpanList, thisValue, thisValueBeautified, type) {
    if (type === 'edit') {
        if ($('div#e-' + thisSpanList + ' input[value="' + thisValue.replace(/ /g, '_') + '"]').prop('checked')) {
            $('div#e-' + thisSpanList + '-selected-container').append('<span onclick="unclickIt(\'' + thisSpanList + '\', \'' + thisValue + '\', \'' + type + '\')" class="added-item-to-multi-checkbox" id="e-added-' + thisValue + '"><button type="button" id="e-remove-' + thisValue.replace(/ /g, '_') + '" class="btn btn-close"></button>' + thisValueBeautified + '<span>');
        } else {
            $('#e-added-' + thisValue).remove();
        }
    }
    if (type === 'add') {
        if ($('div#a-' + thisSpanList + ' input[value="' + thisValue + '"]').prop('checked')) {
            $('div#a-' + thisSpanList + '-selected-container').append('<span onclick="unclickIt(\'' + thisSpanList + '\', \'' + thisValue + '\', \'' + type + '\')" class="added-item-to-multi-checkbox" id="a-added-' + thisValue.replace(/ /g, '_') + '"><button type="button" id="a-remove-' + thisValue.replace(/ /g, '_') + '" class="btn btn-close"></button>' + thisValueBeautified + '<span>');
        } else {
            $('#a-added-' + thisValue).remove();
        }
    }
}

function addFieldToPattern(field_name) {
    $("#s-template_location").val($("#s-template_location").val() + '{' + field_name + '}');
}

function createPublishTicket(accountId, reference, type, server, path, button) {

    accountId = escapeHtml(accountId);
    reference = escapeHtml(reference);
    type = escapeHtml(type);
    server = escapeHtml(server);
    path = escapeHtml(path);
    button = escapeHtml(button);
    let comments = document.getElementById("publishComments").value

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

    var entryId = $('.table_' + reference).find('input[type="checkbox"]:checked').val();

    form_data = {
        accountId: accountId,
        title: 'List ' + reference + ' submission',
        type: 3,
        priority: 1,
        dueDate: formattedDate,
        listName: reference,
        entryId: entryId,
        comments: comments,
        assignEditor: allSelectedUsers
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

function extractMonthAndDay(dateString, field) {
    let year, month, day;

    if (dateString.includes("-")) { // Check if the date string is in the "YYYY-MM-DD" format
        const [yearStr, monthStr, dayStr] = dateString.split("-");
        year = addLeadingZero(parseInt(yearStr));
        month = addLeadingZero(parseInt(monthStr));
        day = addLeadingZero(parseInt(dayStr));
    } else if (dateString.includes("/")) { // Check if the date string is in the "YYYY/MM/DD" format
        const [yearStr, monthStr, dayStr] = dateString.split("/");
        year = addLeadingZero(parseInt(yearStr));
        month = addLeadingZero(parseInt(monthStr));
        day = addLeadingZero(dayStr);
    } else if (!isNaN(dateString)) { // Check if the date string is a valid epoch time
        const date = new Date(parseInt(dateString) * 1000); // Convert epoch time to milliseconds
        year = addLeadingZero(parseInt(date.getFullYear()));
        month = addLeadingZero(parseInt(date.getMonth() + 1)); // getMonth() returns zero-based month, so we add 1
        day = addLeadingZero(parseInt(date.getDate()));
    } else { // Assume the date string is in the "Day, DD Month YYYY" format
        const parts = dateString.split(" ");
        const dayStr = addLeadingZero(parseInt(parts[1]));
        const monthStr = addLeadingZero(parseInt(parts[2]));
        const yearStr = addLeadingZero(parseInt(parts[3]));

        const monthNames = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
        year = parseInt(yearStr);
        month = monthNames.indexOf(monthStr.substring(0, 3)) + 1;
        day = parseInt(dayStr);
    }

    if (field.toLowerCase() === "year") {
        return year;
    }
    if (field.toLowerCase() === "month") {
        return month;
    }
    if (field.toLowerCase() === "day") {
        return day;
    }
}

const addLeadingZero = (value) => {
    return value < 10 ? '0' + value : value.toString();
};

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