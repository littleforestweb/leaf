/*
    Created on : 28 Jun 2022, 09:59:17
    Author     : xhico
*/

async function savePage() {
    // Get HTML Code
    let sourceCode = CKEDITOR.instances.htmlCode.getData();

    return $.ajax({
        type: "POST",
        url: "/api/editor/save",
        data: {
            "data": sourceCode,
            "page_id": page_id
        },
        success: function (entry) {
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
        codeSnippet_theme: 'prism',
        filebrowserUploadUrl: "/api/upload?name=fileupload",
        embed_provider: '//ckeditor.iframe.ly/api/oembed?url={url}&callback={callback}',
        on: {
            setData: async function (event) {
                // Regex to find empty <a> tags
                var emptyAnchorRegex = /<a([^>]*?)>\s*<\/a>/g;
                event.data.dataValue = event.data.dataValue.replace(emptyAnchorRegex, '<a$1>&nbsp;</a>');
            },
            instanceReady: async function (evt) {
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

                editor.on('beforeCommandExec', function (event) {
                    if (editor.mode === 'wysiwyg') {
                        // Trying to prevent the undo JUMP that breaks the tabs
                    }
                });

                await check_if_page_is_locked(page_id);

                var is_locked = false;
                // Usage with CKEditor change event
                editor.on('change', debounce(function () {
                    if (is_locked != true) {
                        lockPage(page_id, "lock");
                        is_locked = true;
                    }
                }, 250)); // Adjust debounce time as necessary

                window.addEventListener('beforeunload', async function (event) {
                    // Perform any necessary actions before showing the confirmation dialog
                    console.log('User attempted to leave the page.');
                    
                    // Show a confirmation dialog
                    event.preventDefault();
                    event.returnValue = ''; // This triggers the default confirmation dialog in most browsers

                    if (page_is_locked_by_me) {

                        let site_id = await $.get("/api/get_site_id?page_id=" + page_id, function (site_id) {
                            return site_id;
                        });

                        // Data to be sent to the server
                        var data = JSON.stringify({
                            page_id: page_id,
                            site_id: site_id,
                            action: "unlock"
                        });

                        fetch('/api/lock_unlock_page', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: data,
                            keepalive: true // This is important to allow the request to complete
                        });
                        return null;
                    }
                });
            }
        }
    });

    // Remove loadingBg
    $(".loadingBg").removeClass("show");
});

function debounce(func, wait, immediate) {
    var timeout;
    return function () {
        var context = this, args = arguments;
        var later = function () {
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
    unlockTimeout = setTimeout(function () {
        lockPage(page_id, "unlock");
        console.log("Page unlocked due to inactivity.");
    }, 14400000); // 14400000 milliseconds = 3h
}

let isLeavingPage = false;
let page_is_locked_by_me = false;

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
        success: function (response) {
            if (response["is_page_locked"] === true) {
                console.log("Page is now locked!");
                page_is_locked_by_me = true;
            }
        },
        error: function (response) {
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
        success: async function (response) {
            if (response && response["locked_by_me"] === true) {
                page_is_locked_by_me = true;
                console.log("Page locked by me! Keep editing..");
                const queryParams = new URLSearchParams(window.location.search);
                if (queryParams.get("action") === "request_unlock") {
                    $('#unlockSelfModal').modal('show');

                    document.getElementById('unlockAndLeave').addEventListener('click', function () {
                        lockPage(page_id, "unlock");
                        $('#unlockSelfModal').modal('hide');
                    })
                }
            } else if (response && response["user_id"] === false) {
                lockPage(page_id, "unlock");
            } else {
                // Trigger the modal to open
                $('#unlockRequestModal').modal('show');

                let locked_by = await $.get("/api/get_single_user_by_value/" + account_id + "/" + response["user_id"], function (locked_by) {
                    return locked_by;
                });

                let page_details = await $.get("/api/get_page_details?page_id=" + page_id, function (page_details) {
                    return page_details;
                });

                document.getElementById("who_is_locking_this_page").innerHTML = locked_by.user[0]["username"];

                document.getElementById('requestUnlockBtn').addEventListener('click', function () {
                    $.ajax({
                        url: '/api/request_unlock',  // URL to your Python route
                        type: 'POST',
                        data: JSON.stringify({
                            page_id: page_id,
                            site_id: site_id,
                            to_send_user_id: locked_by.user[0]["id"],
                            to_send_user_username: locked_by.user[0]["username"],
                            to_send_user_email: locked_by.user[0]["email"],
                            page_title: page_details['title'],
                            page_url: page_details['url']
                        }),
                        contentType: 'application/json; charset=utf-8',
                        success: function (result) {
                            console.log('Request sent successfully');
                            $('#unlockRequestModal').modal('hide');
                            $('#requestSentModal').modal('show');
                        },
                        error: function (xhr, status, error) {
                            console.log('Error sending request:', error);
                        }
                    });
                });
            }
        },
        error: function (response) {
            console.log('Error:', response);
            alert('Failed to perform the action: ' + response.responseText);
        }
    });
}
