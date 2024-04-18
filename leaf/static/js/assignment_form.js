window.addEventListener('DOMContentLoaded', async function main() {
    $(".loadingBg").removeClass("show");

    $('[data-toggle="tooltip"]').tooltip({
        position: {
            my: "center bottom-5",
            at: "center top"
        }
    });
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
                        var newRange = range.clone();
                        newRange.collapse(true);
                        newRange.insertNode(newElement);
                    }
                }
            });
        }
    });

    $('#job-comments').parent().find("div.ck-editor").remove();
    $('#job-comments').replaceWith($('<textarea name="job-comments" class="form-control text-editor" id="job-comments"></textarea>'));

    CKEDITOR.replace(document.querySelector('#job-comments'), {
        fullPage: false,
        allowedContent: true,
        toolbar: [
            {name: "clipboard", items: ["Cut", "Copy", "Paste", "PasteText", "PasteFromWord", "-", "Undo", "Redo"]},
            {name: "basicstyles", items: ["Bold", "Italic", "Underline", "Strike", "-", "RemoveFormat"]},
            {name: "paragraph", items: ["NumberedList", "BulletedList", "-", "Outdent", "Indent", "-", "Blockquote", "CreateDiv", "-", "JustifyLeft", "JustifyCenter", "JustifyRight", "JustifyBlock"]},
            {name: "links", items: ["Link", "Unlink", "anchorPluginButton"]},
            {name: "insert", items: ["Image", "Embed", "Table", "HorizontalRule", "SpecialChar", "inserthtml4x"]},
            {name: "tools", items: ["ShowBlocks"]},
            {name: "styles", items: ["Styles", "Format"]},
            {name: "document", items: ["Source"]}
        ],
        extraPlugins: "anchor, inserthtml4x, embed, pastefromword",
        filebrowserUploadUrl: "/api/upload?name=fileupload",
        embed_provider: '//ckeditor.iframe.ly/api/oembed?url={url}&callback={callback}'
    });

    var todaysDate = new Date();
    $('#job-dueDate').datepicker({dateFormat: 'yy-mm-dd', endDate: "today", minDate: todaysDate});

    if (thisUserRole === 1) {
        var listOfUsers = await $.get("/api/get_all_users/" + accountId, function (result) {
            return result;
        });
    } else {
        var listOfUsers = await $.get("/api/get_single_user/" + accountId + "/" + thisUserRole + "/" + thisUserId, function (result) {
            return result;
        });
    }

    $('#job-assignEditor').html('');
    for (var x = 0; x < listOfUsers.users.length; x++) {
        var thisUser = listOfUsers.users[x];
        var userImage = '<span class="logo_image_container"><img class="logo_image" src="' + thisUser["user_image"] + '" onerror="this.style.display=\'none\'" /></span>';
        if (thisUser["user_image"].startsWith('#')) {
            var colorToFillBg = thisUser["user_image"];
            var usernameInitial = (thisUser["username"] ? thisUser["username"] : "SEM_NOME").charAt(0);
            userImage = '<span class="logo_image" style="background-color:' + colorToFillBg + '">' + usernameInitial + '</span>';
        }
        $("#job-assignEditor").prepend('<label for="thisUserId_' + thisUser["id"] + '" class="form-control users-with-access users-with-access_' + thisUser["id"] + '">' + userImage + '<span class="userName">' + thisUser["username"] + ' <span style="font-size: 10px">' + (thisUser["is_admin"] === 1 ? '(admin)' : '(editor)') + '</span></span><input type="checkbox" class="form-check-input pull-right this-user-id" name="thisUserId_' + thisUser["id"] + '" id="thisUserId_' + thisUser["id"] + '" value="' + thisUser["id"] + '" onclick="uncheckAll(this, ' + (thisUser["is_admin"] === 1 ? '\'ALLADMINS\'' : '\'ALLEDITORS\'') + ')" /></span>');
    }

    if (thisUserRole === 1) {
        $("#job-assignEditor").prepend('<label for="thisUserId_ALLEDITORS" class="form-control users-with-access users-with-access_ALLEDITORS"><span class="logo_image" style="background-color:#176713">ED</span><span class="userName">All Editors</span><input type="checkbox" class="form-check-input pull-right this-user-id" name="thisUserId_ALLEDITORS" id="thisUserId_ALLEDITORS" value="ALLEDITORS" onclick="uncheckAllExcept(this)" /></span>');
        $("#job-assignEditor").prepend('<label for="thisUserId_ALLADMINS" class="form-control users-with-access users-with-access_ALLADMINS"><span class="logo_image" style="background-color:#176713">PU</span><span class="userName">All Power Users</span><input type="checkbox" class="form-check-input pull-right this-user-id" name="thisUserId_ALLADMINS" id="thisUserId_ALLADMINS" value="ALLADMINS" onclick="uncheckAllExcept(this)" /></span>');

        $('#job-assignEditor-search').on('keyup', function (e) {
            var tagElems = $('.users-with-access');
            $(tagElems).hide();
            for (var i = 0; i < tagElems.length; i++) {
                var tag = $(tagElems).eq(i);
                if (($(tag).children('span.userName').text().toLowerCase()).indexOf($(this).val().toLowerCase()) !== -1) {
                    $(tag).show();
                }
            }
        });
    }
})

function uncheckAllExcept(checkbox) {
    var checkboxes = document.getElementsByClassName("checkbox-container")[0].querySelectorAll("input[type='checkbox']");
    var checkboxALLADMINS = document.getElementById("thisUserId_ALLADMINS");
    var checkboxALLEDITORS = document.getElementById("thisUserId_ALLEDITORS");

    if (checkbox.checked) {
        for (var i = 0; i < checkboxes.length; i++) {
            if (checkboxes[i] !== checkbox && checkboxes[i] !== checkboxALLADMINS && checkboxes[i] !== checkboxALLEDITORS) {
                checkboxes[i].checked = false;
            }
        }
    }
}

function uncheckAll(checkbox, role) {
    var checkboxes = document.getElementsByClassName("checkbox-container")[0].querySelectorAll("input[type='checkbox']");
    var checkboxALLADMINS = document.getElementById("thisUserId_ALLADMINS");
    var checkboxALLEDITORS = document.getElementById("thisUserId_ALLEDITORS");

    if (checkbox.checked) {
        if (role === 'ALLADMINS' && checkboxALLADMINS) {
            checkboxALLADMINS.checked = false;
        } else if (checkboxALLEDITORS) {
            checkboxALLEDITORS.checked = false;
        }
    }
}

async function addJob() {
    var form_data = await getFormData('newJob');
    if (!form_data[0] || (form_data[0] && form_data[0].mandatoryFields != true)) {

        var currentDate = new Date();
        currentDate.setDate(currentDate.getDate() + 1);

        var futureDate = new Date();
        futureDate.setDate(currentDate.getDate() + 5);

        var formattedCurrentDate = currentDate.getFullYear() + '-' + padNumber(currentDate.getMonth() + 1) + '-' + padNumber(currentDate.getDate());
        var formattedFutureDate = futureDate.getFullYear() + '-' + padNumber(futureDate.getMonth() + 1) + '-' + padNumber(futureDate.getDate());

        if (form_data.priority === "1") {
            form_data.dueDate = formattedFutureDate;
        } else {
            form_data.dueDate = formattedCurrentDate;
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
                //console.log(entry);
                window.location.replace("/task_requests");
            },
            error: function (XMLHttpRequest, textStatus, errorThrown) {
                console.log("ERROR");
            }
        });
    } else {
        for (var singleItem in form_data[0]['mandatoryElementsNotCompletedToReturn']) {
            $('#job-' + form_data[0]['mandatoryElementsNotCompletedToReturn'][singleItem]).addClass('warning-not-completed');
            $('#job-' + form_data[0]['mandatoryElementsNotCompletedToReturn'][singleItem]).parent().find('.ck-editor').addClass('warning-not-completed');
        }
        alert("You have to complete all mandatory fields (" + form_data[0]['mandatoryElementsNotCompletedToReturn'].join(", ").replace(/e-/g, '') + ")!");
    }
}

async function getFormData(formid) {

    formid = escapeHtml(formid);

    var form = document.getElementById(formid);

    var allFormElements = Array.from(form.querySelectorAll('input:not([type="search"]):not([type="checkbox"]):not(.file-name-reference):not(.clear-btn):not(.ck-hidden):not(.ck-input):not(.hidden-field):not(.document-remover), select, textarea, div.form-select, .checkbox-container')).filter(element => element.id);
    let formdata = {};

    var mandatoryElementsNotCompleted = [];

    for (const element of allFormElements) {

        if (element.name) {
            var theElementName = element.name.replace('job-', '');
        } else {
            var theElementName = element.id.replace('job-', '');
        }

        if (element.classList.value.includes('mandatoryField') || (element.closest('textarea') && element.closest('textarea').classList.value.includes('mandatoryField'))) {
            mandatoryElementsNotCompleted.push(theElementName.replace('job-', ''));
        }

        if (!element.type) {

            var yourArray = [];
            var allChildNodes = $(element)[0].childNodes;
            for (const childElement of allChildNodes) {
                if ($(childElement).find('input[type=checkbox]:checked') && $(childElement).find('input[type=checkbox]:checked').length > 0) {
                    yourArray.push($(childElement).find('input').val());
                }
            }

            formdata[theElementName] = yourArray;

        } else if (element.classList.contains('text-editor')) {
            formdata[theElementName] = CKEDITOR.instances[element.id].getData().replace(/,/g, '&comma;');
        } else if (element.type === 'checkbox') {
            formdata[theElementName] = escapeHtml(element.checked);
        } else if (element.type === 'file') {

            if (element.files.length > 0) {
                var myElementsArray = [];
                for (var singleElementFile of element.files) {
                    var form_data_single_file = new FormData();
                    form_data_single_file.append("files[]", singleElementFile);

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

                    myElementsArray.push(returnedElement.url);
                }
                formdata[theElementName] = myElementsArray;

            } else {
                if (element.parentNode.querySelector('.hidden-field')) {
                    formdata[theElementName] = element.parentNode.querySelector('.hidden-field').value;
                } else {
                    formdata[theElementName] = '';
                }
            }

        } else if (element.options) {
            var selected = [...element.selectedOptions].map(option => option.value);
            if (selected.length > 1) {
                formdata[theElementName] = escapeHtml(selected);
            } else {
                formdata[theElementName] = escapeHtml(element.value);
            }

        } else {
            formdata[theElementName] = escapeHtml(element.value.replace(/,/g, '&comma;').replace(/\\/g, "__BACKSLASH__TO_REPLACE_ON_WEB__").replace(/\'/g, "’"));
        }
    }

    var mandatoryElementsNotCompletedToReturn = [];
    if (mandatoryElementsNotCompleted.length > 0) {
        for (var key of mandatoryElementsNotCompleted) {
            if (
                (typeof 'string' && formdata[key] === "") ||
                (typeof 'object' && formdata[key] && formdata[key].length < 1) ||
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

// Function to pad numbers with leading zeros if necessary
function padNumber(number) {
    return number.toString().padStart(2, '0');
}

function uploadSingleFile(form_data) {
    return $.ajax({
        type: "POST",
        url: "/api/upload_workflow_attachments",
        data: form_data,
        contentType: false,
        dataType: 'json',
        cache: false,
        processData: false,
        success: function (response) {
            //console.log(response);
        },
        error: function (XMLHttpRequest, textStatus, errorThrown) {
            return errorThrown;
        }
    });
}