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
    console.log("Starting Editor");

    // Load page html code
    let data = await $.get("/editor/getPageCode?page_id=" + page_id, function (htmlContent) {
        return htmlContent;
    });
    data = data.data;

    // Find if page has carousel
    let parser = new DOMParser();
    let htmlDoc = parser.parseFromString(data, "text/html");
    let linkElems = htmlDoc.getElementsByTagName("link");
    for (const linkElem of linkElems) {
        htmlDoc.getElementsByTagName("head")[0].appendChild(linkElem);
    }
    let serializer = new XMLSerializer();
    data = serializer.serializeToString(htmlDoc);

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
            }
        }
    });

    // Remove loadingBg
    $(".loadingBg").removeClass("show");
});





