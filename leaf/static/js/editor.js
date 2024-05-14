/*
    Created on : 28 Jun 2022, 09:59:17
    Author     : xhico
*/

async function savePage() {
    // Get HTML Code
    let sourceCode = CKEDITOR.instances.htmlCode.getData();

    return $.ajax({
        type: "POST", url: "/api/editor/save", data: {"data": sourceCode, "page_id": page_id}, success: function (entry) {
            console.log("save success");

            let previewBtn = document.getElementById("previewPage");
            previewBtn.href = entry.previewURL;
            previewBtn.target = "_blank";

            startInactivityTimer(page_id);

            // Reset the timer on user actions
            // document.addEventListener('mousemove', function() { startInactivityTimer(page_id); });
            // document.addEventListener('keypress', function() { startInactivityTimer(page_id); });

            $('#savedNotification').toast('show');
        }, error: function (XMLHttpRequest, textStatus, errorThrown) {
            console.log("save error");
        }
    });
}

async function publishPage() {
    console.log("publishPage");
}

window.addEventListener('DOMContentLoaded', async function main() {
    // Load page html code
    let data = await $.get("/editor/getPageCode?page_id=" + page_id, function (htmlContent) {
        return htmlContent;
    });
    data = data.data;

    // Set html code to ckeditor textarea
    document.getElementById("htmlCode").value = data;

    // Add AnchorPlugin Btn
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

    // Add Save Btn
    CKEDITOR.plugins.add("saveBtn", {
        init: function (editor) {
            editor.ui.addButton("SaveBtn", {
                label: "Save",
                command: "saveBtn",
                icon: "save"
            });
            editor.addCommand("saveBtn", {
                exec: async function () {
                    await savePage();
                }
            });
        }
    });

    // Add Publish Btn
    CKEDITOR.plugins.add("publishBtn", {
        init: function (editor) {
            editor.ui.addButton("PublishBtn", {
                label: "Publish",
                command: "publishBtn",
                icon: "checkbox"
            });
            editor.addCommand("publishBtn", {
                exec: async function () {
                    await publishPage();
                }
            });
        }
    });

    // Init CKEditor
    CKEDITOR.replace("htmlCode", {
        toolbar: [
            {name: "clipboard", items: ["Cut", "Copy", "Paste", "PasteText", "PasteFromWord", "-", "Undo", "Redo"]},
            {name: "basicstyles", items: ["Bold", "Italic", "Underline", "Strike"]},
            {name: "paragraph", items: ["NumberedList", "BulletedList", "-", "Outdent", "Indent", "-", "Blockquote", "CreateDiv", "-", "JustifyLeft", "JustifyCenter", "JustifyRight", "JustifyBlock"]},
            {name: "links", items: ["Link", "Unlink", "anchorPluginButton"]},
            {name: "insert", items: ["Image", "Embed", "Table", "HorizontalRule", "SpecialChar", "inserthtml4x"]},
            {name: "styles", items: ["Styles", "Format"]},
            {name: "colors", items: ["TextColor", "BGColor"]},
            {name: "actions", items: ["Source", "Preview", "SaveBtn", "PublishBtn"]}
        ],
        extraPlugins: "anchor, inserthtml4x, embed, saveBtn, pastefromword",
        filebrowserUploadUrl: "/api/upload?name=fileupload",
        embed_provider: '//ckeditor.iframe.ly/api/oembed?url={url}&callback={callback}',
        on: {
            setData: function(event) {
                // Regex to find empty <a> tags
                var emptyAnchorRegex = /<a([^>]*?)>\s*<\/a>/g;
                event.data.dataValue = event.data.dataValue.replace(emptyAnchorRegex, '<a$1>&nbsp;</a>');
            },
            instanceReady: function (evt) {
                // Get the CKEditor instance
                let editor = evt.editor;

                // Define element selectors to be blocked from editing
                let selectorsToBlock = ["head"];
                selectorsToBlock.forEach(function (selector) {
                    let elements = editor.editable().$.querySelectorAll(selector);
                    elements.forEach(function (element) {
                        element.setAttribute("contenteditable", "false");
                    });
                });

                editor.on('beforeCommandExec', function(event) {
                    if (editor.mode === 'wysiwyg') {
                        // Trying to prevent the undo JUMP that breaks the tabs
                    }
                });

                check_if_page_is_locked(page_id);

                var is_locked = false;
                // Usage with CKEditor change event
                editor.on('change', debounce(function() {
                    if (is_locked != true) {
                        lockPage(page_id, "lock");
                        is_locked = true;
                    }
                }, 250)); // Adjust debounce time as necessary
            }
        }
    });

    // Remove loadingBg
    $(".loadingBg").removeClass("show");
});

function debounce(func, wait, immediate) {
    var timeout;
    return function() {
        var context = this, args = arguments;
        var later = function() {
            timeout = null;
            if (!immediate) func.apply(context, args);
        };
        var callNow = immediate && !timeout;
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
        if (callNow) func.apply(context, args);
    };
}

var unlockTimeout;

function startInactivityTimer(page_id) {
    // Clear existing timeout to reset the timer whenever user activity is detected
    clearTimeout(unlockTimeout);

    // Set a new timeout
    unlockTimeout = setTimeout(function() {
        lockPage(page_id, "unlock");
        console.log("Page unlocked due to inactivity.");
    }, 300000); // 300000 milliseconds = 5 minutes
}

window.onbeforeunload = function() {
    let site_id = await $.get("/api/get_site_id?page_id=" + page_id, function (site_id) {
        return site_id;
    });
    // Attempt to notify the server about the closure
    navigator.sendBeacon('/api/lock_unlock_page', JSON.stringify({ page_id: page_id, site_id: site_id, action: "unlock" }));
    return null;
};

async function lockPage(page_id, action) {
    let site_id = await $.get("/api/get_site_id?page_id=" + page_id, function (site_id) {
        return site_id;
    });

    $.ajax({
        url: '/api/lock_unlock_page',  // URL of the Flask route
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({
            page_id: page_id,
            site_id: site_id,
            action: action
        }),
        success: function(response) {
            if (response["is_page_locked"] === true) {
                console.log("Page is now locked!");
            }
        },
        error: function(response) {
            console.log('Error:', response);
            alert('Failed to perform the action: ' + response.responseText);
        }
    });
}

async function check_if_page_is_locked(page_id) {
    let site_id = await $.get("/api/get_site_id?page_id=" + page_id, function (site_id) {
        return site_id;
    });

    $.ajax({
        url: '/api/check_if_page_locked_by_me',  // URL of the Flask route
        type: 'GET',
        data: {
            page_id: page_id,
            site_id: site_id
        },
        success: function(response) {
            if (response && response["locked_by_me"] === true) {
                console.log("Page locked by me! Keep editing..");
            } else if (response && response["user_id"] === false) {
                lockPage(page_id, "unlock");
            } else {
                console.log("Lets make the modal to request to unlock the page");
            } 
        },
        error: function(response) {
            console.log('Error:', response);
            alert('Failed to perform the action: ' + response.responseText);
        }
    });
}
