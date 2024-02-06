/*
    Created on : 12 May 2022, 15:42
    Author     : xhico
*/

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

async function setStatus(status, id, type, listName, accountId) {
    document.getElementById("actionContainer").innerHTML = "<span>Deploying...</span>"

    let jsonConfigSaveByFields = false;
    let jsonConfigFieldsToSaveBy = false;

    if (listName || listName !== "") {
        // Get list configuration
        let jsonConfig = await $.get("/api/get_list_configuration/" + accountId + "/" + listName, function (result) {
            return result;
        });

        if (jsonConfig.columns[0] && jsonConfig.columns[0][6]) {
            jsonConfigSaveByFields = jsonConfig.columns[0][6];
        }
        if (jsonConfig.columns[0] && jsonConfig.columns[0][7]) {
            jsonConfigFieldsToSaveBy = jsonConfig.columns[0][7];
        }
    }

    let dataF = {
        "id": id,
        "status": status,
        "type": type,
        "listName": listName,
        "saveByFields": jsonConfigSaveByFields,
        "fieldsToSaveBy": jsonConfigFieldsToSaveBy
    }

    $.ajax({
        type: "POST",
        url: "/workflow/action",
        data: dataF,
        success: function (entry) {
            document.getElementById("actionContainer").innerHTML = "<span>No Action needed</span>";
            document.getElementById("statusContainer").innerHTML = "<span>" + entry["action"] + "</span>";
            document.getElementById("workflowNotification").classList.add("bg-success");
            document.getElementById("workflowNotificationMsg").innerHTML = "<span>Workflow Completed</span>"
            $('#workflowNotification').toast('show');
        }, error: function (entry, XMLHttpRequest, textStatus, errorThrown) {
            console.log(XMLHttpRequest);
            console.log(textStatus);
            console.log(errorThrown);
            document.getElementById("actionContainer").innerHTML = "<span>No Action needed</span>";
            document.getElementById("statusContainer").innerHTML = "<span>" + entry["action"] + "</span>";
            document.getElementById("workflowNotification").classList.add("bg-success");
            document.getElementById("workflowNotificationMsg").innerHTML = "<span>Workflow Completed</span>"
            $('#workflowNotification').toast('show');
        }
    });
}

async function addNewComment(id, user_to_notify) {
    $('#comments-sections').append('<div class="card-body" id="newCommentBoard"><div id="comment-editor"></div><div class="buttonsContainer float-right margin-top"><button type="button" id="closeNewCommentBtn" class="btn btn-blue" onclick="closeNewComment(\'' + id + '\', \'' + user_to_notify + '\')">Close</button><button type="button" class="btn btn-blue" onclick="saveNewComment(\'' + id + '\', \'' + user_to_notify + '\')">Save</button></div></div>');
    $('#addNewCommentBtn').replaceWith('<button type="button" id="closeNewCommentBtn" class="btn btn-blue float-right" onclick="closeNewComment(\'' + id + '\', \'' + user_to_notify + '\')">Close</button>');

    $('#comment-editor').replaceWith($('<textarea name="job-comments" class="form-control text-editor" id="job-comments"></textarea>'));

    CKEDITOR.replace(document.querySelector('#job-comments'), {
        fullPage: false,
        allowedContent: true,
        toolbar: [
            {name: "clipboard", items: ["Cut", "Copy", "Paste", "PasteText", "PasteFromWord", "-", "Undo", "Redo"]},
            {name: "basicstyles", items: ["Bold", "Italic", "Underline", "Strike", "-", "RemoveFormat"]},
            {name: "paragraph", items: ["NumberedList", "BulletedList", "-", "Outdent", "Indent", "-", "Blockquote", "CreateDiv", "-", "JustifyLeft", "JustifyCenter", "JustifyRight", "JustifyBlock"]},
            {name: "links", items: ["Link", "Unlink", "anchorPluginButton"]},
            {name: "insert", items: ["FileUpload", "Image", "Embed", "Table", "HorizontalRule", "SpecialChar", "inserthtml4x"]},
            {name: "tools", items: ["ShowBlocks"]},
            {name: "styles", items: ["Styles", "Format"]}
        ],
        extraPlugins: "anchor, inserthtml4x, embed, fileupload, pastefromword",
        filebrowserUploadUrl: "/api/upload?name=fileupload",
        embed_provider: '//ckeditor.iframe.ly/api/oembed?url={url}&callback={callback}'
    });

    var target_offset = $("#newCommentBoard").offset();
    var target_top = target_offset.top;
    $('html, body').animate({scrollTop: target_top}, 100, 'easeInSine');
}

async function saveNewComment(id, user_to_notify) {

    var newComment = CKEDITOR.instances['job-comments'].getData().replace(/,/g, '&comma;');

    let dataToSave = {
        "id": id,
        "comments": newComment,
        "user_to_notify": user_to_notify
    }

    $.ajax({
        type: "POST",
        url: "/workflow/add_new_comment",
        data: dataToSave,
        success: function (entry) {
            //console.log(entry);
            location.reload(true);
        }, error: function (entry, XMLHttpRequest, textStatus, errorThrown) {
            console.log(XMLHttpRequest);
            console.log(textStatus);
            console.log(errorThrown);
        }
    });
}

async function closeNewComment(id, user_to_notify) {
    $('#newCommentBoard').remove();
    $('#closeNewCommentBtn').replaceWith('<button type="button" id="addNewCommentBtn" class="btn btn-blue float-right" onclick="addNewComment(\'' + id + '\', \'' + user_to_notify + '\')">Add Comment</button>');
}

async function priorityChange(thisId, accountId) {
    var newPriorityString = document.getElementById("priority-selection").options[document.getElementById("priority-selection").selectedIndex].text;
    var newPriority = document.getElementById("priority-selection").value;

    let dataF = {
        "id": thisId,
        "new_priority": newPriority
    }

    $.ajax({
        type: "POST",
        url: "/workflow/change_priority",
        data: dataF,
        success: function (entry) {
            document.getElementById("workflowNotification").classList.add("bg-success");
            document.getElementById("workflowNotificationMsg").innerHTML = "<span>Priority successefully changed to: <strong style=\"display: block;\">\"" + newPriorityString + "\"</strong></span>"
            $('#workflowNotification').toast('show');
        }, error: function (entry, XMLHttpRequest, textStatus, errorThrown) {
            console.log(XMLHttpRequest);
            console.log(textStatus);
            console.log(errorThrown);
            document.getElementById("workflowNotification").classList.add("bg-success");
            document.getElementById("workflowNotificationMsg").innerHTML = "<span>Priority successefully changed to: <strong style=\"display: block;\">\"" + newPriorityString + "\"</strong></span>"
            $('#workflowNotification').toast('show');
        }
    });
}

async function statusChange(thisId, accountId, user_to_notify) {
    var newStatusString = document.getElementById("status-selection").options[document.getElementById("status-selection").selectedIndex].text;
    var newStatus = document.getElementById("status-selection").value;

    let dataF = {
        "id": thisId,
        "new_status": newStatus,
        "user_to_notify": user_to_notify
    }

    $.ajax({
        type: "POST",
        url: "/workflow/change_status",
        data: dataF,
        success: function (entry) {
            document.getElementById("workflowNotification").classList.add("bg-success");
            document.getElementById("workflowNotificationMsg").innerHTML = "<span>Status successefully changed to: <strong style=\"display: block;\">\"" + newStatusString + "\"</strong></span>"
            $('#workflowNotification').toast('show');
        }, error: function (entry, XMLHttpRequest, textStatus, errorThrown) {
            console.log(XMLHttpRequest);
            console.log(textStatus);
            console.log(errorThrown);
            document.getElementById("workflowNotification").classList.add("bg-success");
            document.getElementById("workflowNotificationMsg").innerHTML = "<span>Status successefully changed to: <strong style=\"display: block;\">\"" + newStatusString + "\"</strong></span>"
            $('#workflowNotification').toast('show');
        }
    });
}

async function dueDateChange(thisId, accountId) {
    var newDueDate = document.getElementById("due-date-selector").value;

    let dataF = {
        "id": thisId,
        "new_due_date": newDueDate
    }

    $.ajax({
        type: "POST",
        url: "/workflow/change_due_date",
        data: dataF,
        success: function (entry) {
            document.getElementById("workflowNotification").classList.add("bg-success");
            document.getElementById("workflowNotificationMsg").innerHTML = "<span>Due Date successefully changed to: <strong style=\"display: block;\">\"" + newDueDate + "\"</strong></span>"
            $('#workflowNotification').toast('show');
        }, error: function (entry, XMLHttpRequest, textStatus, errorThrown) {
            console.log(XMLHttpRequest);
            console.log(textStatus);
            console.log(errorThrown);
            document.getElementById("workflowNotification").classList.add("bg-success");
            document.getElementById("workflowNotificationMsg").innerHTML = "<span>Due Date successefully changed to: <strong style=\"display: block;\">\"" + newDueDate + "\"</strong></span>"
            $('#workflowNotification').toast('show');
        }
    });
}

window.addEventListener('DOMContentLoaded', async function main() {
    if (document.getElementById("priority-selection")) {
        document.getElementById("priority-selection").selectedIndex = parseInt(currentPriority - 1);
    }

    if (currentStatus === "Waiting for review") {
        currentStatus = "1";
    }
    if (document.getElementById("status-selection")) {
        document.getElementById("status-selection").selectedIndex = parseInt(currentStatus - 1);
    }

    var todaysDate = new Date();
    $('#due-date-selector').datepicker({dateFormat: 'yy-mm-dd', endDate: "today", minDate: todaysDate});

    $(".loadingBg").removeClass("show");
});