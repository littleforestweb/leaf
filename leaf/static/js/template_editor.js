/*
    Created on : 03 Mar 2024, 11:23:05
    Author     : joao
*/

async function save_template() {
    // Get HTML Code
    let sourceCode = CKEDITOR.instances.htmlCode.getData();
    return $.ajax({
        type: "POST",
        url: "/api/templates/save",
        data: {
            "data": sourceCode,
            "template_id": template_id,
            "template_url_pattern": document.getElementById("s-template_location").value,
            "template_feed_url_pattern": document.getElementById("s-feed_location").value,
            "template_name": document.getElementById("s-template_name").value
        },
        success: function (entry) {
            $('#savedNotification').toast('show');
        },
        error: function (XMLHttpRequest, textStatus, errorThrown) {
            console.log("save error");
        }
    });
}

async function show_available_tags() {
    let jsonAllTemplate = await $.get("/api/get_template_by_id/" + accountId + "/" + template_id, function (result) {
        return result;
    });
    jsonAllTemplate = jsonAllTemplate.columns;

    if (jsonAllTemplate && jsonAllTemplate[0] && jsonAllTemplate[0][1]) {
        let jsonAvailableFields = await $.get("/api/get_available_fields/" + accountId + "/" + jsonAllTemplate[0][1], function (result) {
            return result;
        });
        jsonAvailableFields = jsonAvailableFields.columns;

        $(".template_fields_container").html("");
        for (var x = 0; x < jsonAvailableFields.length; x++) {
            $(".template_fields_container").append('<button type="button" class="btn" val="' + jsonAvailableFields[x] + '" onclick="addFieldToPattern(\'' + jsonAvailableFields[x] + '\');">' + jsonAvailableFields[x] + '</button>');
        }

        dropDownTemplateFieldsToggle();
    }
}

function dropDownTemplateFieldsToggle() {
    $('.template_fields_container').toggleClass('hide');
}

function addFieldToPattern(field_name) {
    // Get the CKEditor instance
    let editor = CKEDITOR.instances.htmlCode;

    // Get the current content
    let content = editor.getData();

    // Get the current selection in the editor
    let selection = editor.getSelection();

    // Get the range of the current selection
    let range = selection.getRanges()[0];

    // Get the position where the mouse is in the editor
    let cursorPosition = range.startContainer;

    // Append something to the content
    let insertedContent = '{{' + field_name + '}}';

    // Insert the content at the cursor position
    if (cursorPosition) {
        editor.insertHtml(insertedContent);
    } else {
        // If no cursor position is found, simply append the content to the end
        editor.insertHtml(insertedContent);
    }
}

async function publish_template() {
    console.log("publish_template");
}

window.addEventListener('DOMContentLoaded', async function main() {
    console.log("Starting Template Editor");

    // Load page html code
    let data = await $.get("/api/templates/get_template_id/" + accountId + "/" + template_id, function (htmlContent) {
        return htmlContent;
    });

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
                    await save_template();
                }
            });
        }
    });

    // Add Available Tags Btn
    CKEDITOR.plugins.add("availableTags", {
        init: function (editor) {
            editor.ui.addButton("AvailableTags", {
                label: "Tags",
                command: "availableTags",
                icon: "select"
            });
            editor.addCommand("availableTags", {
                exec: async function () {
                    if (!$(".template_fields_container").length) {
                        $(".cke_button__select_icon").parent().append('<span class="template_fields_container hide"></span>');
                    }
                    await show_available_tags();
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
                    await publish_template();
                }
            });
        }
    });

    // Init CKEditor
    CKEDITOR.replace("htmlCode", {
        fullPage: true,
        allowedContent: true,
        toolbar: [
            {name: "clipboard", items: ["Cut", "Copy", "Paste", "PasteText", "PasteFromWord", "-", "Undo", "Redo"]},
            {name: "basicstyles", items: ["Bold", "Italic", "Underline", "Strike"]},
            {name: "paragraph", items: ["NumberedList", "BulletedList", "-", "Outdent", "Indent", "-", "Blockquote", "CreateDiv", "-", "JustifyLeft", "JustifyCenter", "JustifyRight", "JustifyBlock"]},
            {name: "links", items: ["Link", "Unlink", "anchorPluginButton"]},
            {name: "insert", items: ["Image", "Embed", "Table", "HorizontalRule", "SpecialChar", "inserthtml4x"]},
            {name: "styles", items: ["Styles", "Format"]},
            {name: "colors", items: ["TextColor", "BGColor"]},
            {name: "actions", items: ["Source", "Preview", "SaveBtn", "AvailableTags", "PublishBtn"]}
        ],
        extraPlugins: "anchor, inserthtml4x, embed, saveBtn, availableTags, pastefromword",
        filebrowserUploadUrl: "/api/upload?name=fileupload",
        embed_provider: '//ckeditor.iframe.ly/api/oembed?url={url}&callback={callback}'
    });

    await get_template_by_id(template_id);

    // Remove loadingBg
    $(".loadingBg").removeClass("show");
});

async function get_template_by_id(template_id) {
    let jsonAllTemplate = await $.get("/api/get_template_by_id/" + accountId + "/" + template_id, function (result) {
        return result;
    });
    jsonAllTemplate = jsonAllTemplate.columns;

    document.getElementById("s-template_location").value = jsonAllTemplate[0][3];
    document.getElementById("s-feed_location").value = jsonAllTemplate[0][4];
    document.getElementById("s-template_name").value = jsonAllTemplate[0][2];
}