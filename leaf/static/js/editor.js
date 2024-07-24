/*
    Created on : 28 Jun 2022, 09:59:17
    Author     : xhico
*/

let unlockTimeout;
let isLeavingPage = false;
let page_is_locked_by_me = false;
let anchorPositions = {};

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

function startInactivityTimer(page_id) {
    // Clear existing timeout to reset the timer whenever user activity is detected
    clearTimeout(unlockTimeout);

    // Set a new timeout
    unlockTimeout = setTimeout(function () {
        lockPage(page_id, "unlock");
        console.log("Page unlocked due to inactivity.");
    }, 14400000); // 14400000 milliseconds = 3h
}

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

function adjustDivEditable(editor, addPlaceholder) {
    let editable = editor.editable();
    editable.find('div').toArray().forEach(function(div) {
        let hasDirectText = false;
        div.$.childNodes.forEach(function(node) {
            if (node.nodeType === Node.TEXT_NODE && node.nodeValue.trim() !== "") {
                hasDirectText = true;
            }
        });

        if (addPlaceholder) {
            if (!hasDirectText) {
                div.appendHtml('<p class="editor_placeholder" style="display:inline-block;width:100%;min-height:10px;height:auto;padding:0"> </p>');
            }
        } else {
            div.$.childNodes.forEach(function(node) {
                if (node.nodeType === Node.ELEMENT_NODE && node.classList.contains('editor_placeholder')) {
                    let siblingContent = '';
                    div.$.childNodes.forEach(function(siblingNode) {
                        if (siblingNode !== node && siblingNode.nodeType === Node.TEXT_NODE) {
                            siblingContent += siblingNode.nodeValue;
                            siblingNode.remove();
                        }
                    });
                    node.remove();
                    if (siblingContent.trim() !== '') {
                        div.appendHtml(siblingContent.trim());
                    }
                }
            });
        }
    });
}

function adjustAnchorPosition(editor, itemPosition) {
    let editable = editor.editable();
    editable.find('a').toArray().forEach(function (anchor) {
        if (anchor.getHtml().trim() === "&nbsp;" || anchor.getHtml().trim() === "" || anchor.getHtml().trim() === "Area link. Click here to edit.") {
            if (!itemPosition && anchor.getAttribute("class") && anchor.getAttribute("style")) {
                anchor.setAttribute("class", anchor.getAttribute("class").replace(" leaf_ck_position_defined", ""));
                anchor.setAttribute("style", anchor.getAttribute("style").replace(/ position:relative!important;background:#fff/g, "text-decoration:none;margin:0 0 0 -5px;"));
                anchor.setHtml("&nbsp;");
            } else { // if (anchor.getAttribute("class") && anchor.getAttribute("style"))
                let originalPosition = anchor.getStyle("position");
                anchor.setHtml("Area link. Click here to edit.");
                anchor.setAttribute("style", (anchor.getAttribute("style") ? anchor.getAttribute("style").replace(/text-decoration:none;margin:0 0 0 -5px;/g, "").replace(/text-decoration:none;margin:-5px;/g, "") : "") + " position:relative!important;background:#fff");
                anchor.setAttribute("class", anchor.getAttribute("class") + " leaf_ck_position_defined");
                if (originalPosition.trim() !== "") {
                    anchorPositions[anchor.getOuterHtml()] = originalPosition;
                } else {
                    anchorPositions[anchor.getOuterHtml()] = false;
                }
            }
        }
    });
}

async function savePage() {
    // Adjust Anchor Position
    await adjustAnchorPosition(CKEDITOR.instances.htmlCode, false);
    await adjustDivEditable(CKEDITOR.instances.htmlCode, false);

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

window.addEventListener('DOMContentLoaded', async function main() {
    // Load page html code
    let data = await $.get("/editor/getPageCode?page_id=" + page_id, function (htmlContent) {
        return htmlContent;
    });
    data = data.data;

    let site_id = await $.get("/api/get_site_id?page_id=" + page_id, function (site_id) {
        return site_id;
    });

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

    CKEDITOR.plugins.add('extendedImage2', {
        requires: 'widget,dialog,image2',
        init: function(editor) {
            const captionedImageClass = editor.config.image2_captionedImageClass || 'image-captioned';
            const captionedClass = editor.config.image2_captionedClass || 'caption';
            const alignmentClasses = editor.config.image2_alignClasses || ['align-left', 'align-right', 'align-center'];

            function getCustomClasses(classList, type) {
                let predefinedClasses = ['cke_widget_element'];
                if (type === "figure") {
                    predefinedClasses = [captionedImageClass, 'cke_widget_element'];
                }
                return classList.filter(cls => !predefinedClasses.includes(cls) && !alignmentClasses.includes(cls)).join(' ');
            }

            function getAlignmentClass(classList) {
                return classList.find(cls => alignmentClasses.includes(cls)) || '';
            }

            function getAllClasses(customClasses, alignmentClass, type) {
                if (customClasses) {
                    if (type === "figure") {
                        return [captionedImageClass, alignmentClass, ...customClasses.split(' ')].filter(Boolean).join(' ');
                    } else {
                        return [alignmentClass, ...customClasses.split(' ')].filter(Boolean).join(' ');
                    }
                } else {
                    if (type === "figure") {
                        return [captionedImageClass, alignmentClass].filter(Boolean).join(' ');
                    } else {
                        return [alignmentClass].filter(Boolean).join(' ');
                    }
                }
                
            }

            editor.widgets.add('image', {
                requiredContent: 'figure(img,figcaption)',
                template: '<figure class="image"><img/><figcaption></figcaption></figure>',
                upcast: function(element) {
                    return element.name === 'figure' && element.hasClass(captionedImageClass);
                },
                init: function() {
                    const imgElement = this.element.findOne('img');
                    const captionElement = this.element.findOne('figcaption');

                    if (captionElement) {
                        this.setData('caption', captionElement.getText());
                    }
                    this.setData('src', imgElement.getAttribute('src'));
                },
                data: function() {
                    const imgElement = this.element.findOne('img');
                    const captionElement = this.element.findOne('figcaption');

                    if (this.data.src) {
                        imgElement.setAttribute('src', this.data.src);
                    }
                    if (this.data.caption) {
                        captionElement.setText(this.data.caption);
                    }

                    const element = this.element;
                    const currentClasses = element.getAttribute('class').split(' ');
                    const alignmentClass = getAlignmentClass(currentClasses);
                    const tagName = element.getName();

                    if (this.data.advId) {
                        element.setAttribute('id', this.data.advId);
                    } else {
                        element.removeAttribute('id');
                    }
                    if (this.data.classes && alignmentClass) {
                        const classesStr = Object.keys(this.data.classes).join(' ');
                        element.setAttribute('class', getAllClasses(classesStr, alignmentClass, tagName));
                    } else {
                        element.setAttribute('class', getAllClasses('', alignmentClass, tagName));
                    }

                    if (this.data.advLongDesc) {
                        element.setAttribute('longdesc', this.data.advLongDesc);
                    } else {
                        element.removeAttribute('longdesc');
                    }

                    if (this.data.advStyles) {
                        element.setAttribute('style', this.data.advStyles);
                    } else {
                        element.removeAttribute('style');
                    }

                    if (tagName === "figure" && captionElement) {
                        captionElement.setAttribute('class', captionedClass);
                    }

                    if (this.data.linkUrl) {
                        let parentElement = imgElement.getParent();
                        if (parentElement && parentElement.is('a')) {
                            parentElement.setAttribute('href', this.data.linkUrl);
                            if (this.data.linkTarget) {
                                parentElement.setAttribute('target', this.data.linkTarget);
                            } else {
                                parentElement.removeAttribute('target');
                            }
                        } else {
                            let link = new CKEDITOR.dom.element('a');
                            link.setAttribute('href', this.data.linkUrl);
                            if (this.data.linkTarget) {
                                link.setAttribute('target', this.data.linkTarget);
                            }
                            let newImgElement = imgElement.clone(true);
                            link.append(newImgElement);
                            imgElement.insertBeforeMe(link);
                            imgElement.remove();
                        }
                    } else {
                        let parentElement = imgElement.getParent();
                        if (parentElement && parentElement.is('a')) {
                            let grandParent = parentElement.getParent();
                            parentElement.remove();
                            imgElement.insertBefore(grandParent.findOne('figcaption'));
                        }
                    }
                }
            });

            // Add a listener to capture and commit data on dialog hide
            editor.on('dialogHide', function(evt) {
                const dialog = evt.data;
                if (dialog._.name === 'image2') {
                    const image2Widget = editor.widgets.selected[0];
                    if (image2Widget) {
                        const dialogData = image2Widget.data;

                        dialogData.advId = dialog.getValueOf('advanced', 'advId');
                        dialogData.advClasses = dialog.getValueOf('advanced', 'advClasses');
                        dialogData.advLongDesc = dialog.getValueOf('advanced', 'advLongDesc');
                        dialogData.advStyles = dialog.getValueOf('advanced', 'advStyles');
                        dialogData.linkUrl = dialog.getValueOf('link', 'linkUrl');
                        dialogData.linkTarget = dialog.getValueOf('link', 'linkTarget');

                        image2Widget.setData('advId', dialogData.advId);
                        image2Widget.setData('advClasses', dialogData.advClasses);
                        image2Widget.setData('advLongDesc', dialogData.advLongDesc);
                        image2Widget.setData('advStyles', dialogData.advStyles);
                        image2Widget.setData('linkUrl', dialogData.linkUrl);
                        image2Widget.setData('linkTarget', dialogData.linkTarget);

                        const element = image2Widget.element;
                        const currentClasses = element.getAttribute('class').split(' ');
                        const alignmentClass = getAlignmentClass(currentClasses);

                        if (dialogData.advId) {
                            element.setAttribute('id', dialogData.advId);
                        } else {
                            element.removeAttribute('id');
                        }
                        const tagName = element.getName();
                        if (dialogData.advClasses || alignmentClass) {
                            element.setAttribute('class', getAllClasses(dialogData.advClasses, alignmentClass, tagName));
                        } else {
                            element.setAttribute('class', getAllClasses('', alignmentClass, tagName));
                        }

                        if (dialogData.advLongDesc) {
                            element.setAttribute('longdesc', dialogData.advLongDesc);
                        } else {
                            element.removeAttribute('longdesc');
                        }

                        if (dialogData.advStyles) {
                            element.setAttribute('style', dialogData.advStyles);
                        } else {
                            element.removeAttribute('style');
                        }

                        if (tagName === "figure") {
                            let captionElement = element.findOne('figcaption');
                            if (captionElement) {
                                captionElement.setAttribute('class', captionedClass);
                            }
                        }

                        if (dialogData.linkUrl) {
                            let imgElement = element.findOne('img');
                            if (imgElement) {
                                let parentElement = imgElement.getParent();
                                if (parentElement && parentElement.is('a')) {
                                    parentElement.setAttribute('href', dialogData.linkUrl);
                                    if (dialogData.linkTarget) {
                                        parentElement.setAttribute('target', dialogData.linkTarget);
                                    } else {
                                        parentElement.removeAttribute('target');
                                    }
                                } else {
                                    let link = new CKEDITOR.dom.element('a');
                                    link.setAttribute('href', dialogData.linkUrl);
                                    if (dialogData.linkTarget) {
                                        link.setAttribute('target', dialogData.linkTarget);
                                    }
                                    let newImgElement = imgElement.clone(true);
                                    link.append(newImgElement);
                                    imgElement.insertBeforeMe(link);
                                    imgElement.remove();
                                }
                            }
                        } else {
                            let imgElement = element.findOne('img');
                            if (imgElement) {
                                let anchorElement = imgElement.getParent();
                                if (anchorElement && anchorElement.is('a')) {
                                    let grandParent = anchorElement.getParent();
                                    anchorElement.remove();
                                    let captionElement = grandParent.findOne('figcaption');
                                    imgElement.insertBefore(captionElement);
                                }
                            }
                        }
                    }
                }
            });

            // Modify the dialog definition to include custom fields
            CKEDITOR.on('dialogDefinition', function(ev) {
                var dialogName = ev.data.name;
                var dialogDefinition = ev.data.definition;

                if (dialogName === 'image2') {
                    dialogDefinition.width = 600;

                    // Check if the "Advanced" tab has already been added
                    var alreadyExists = dialogDefinition.contents.some(content => content.id === 'advanced');
                    if (!alreadyExists) {
                        dialogDefinition.addContents({
                            id: 'advanced',
                            label: 'Advanced',
                            elements: [
                                {
                                    type: 'text',
                                    id: 'advId',
                                    label: 'Id',
                                    setup: function(widget) {
                                        this.setValue(widget.element.getAttribute('id') || '');
                                    },
                                    commit: function(widget) {
                                        widget.setData('advId', this.getValue());
                                    }
                                },
                                {
                                    type: 'text',
                                    id: 'advClasses',
                                    label: 'Classes',
                                    setup: function(widget) {
                                        var classList = widget.element.getAttribute('class').split(' ');
                                        var tagName = widget.element.getName();
                                        this.setValue(getCustomClasses(classList, tagName));
                                    },
                                    commit: function(widget) {
                                        widget.setData('advClasses', this.getValue());
                                    }
                                },
                                {
                                    type: 'text',
                                    id: 'advLongDesc',
                                    label: 'Long Description',
                                    setup: function(widget) {
                                        this.setValue(widget.element.getAttribute('longdesc') || '');
                                    },
                                    commit: function(widget) {
                                        widget.setData('advLongDesc', this.getValue());
                                    }
                                },
                                {
                                    type: 'text',
                                    id: 'advStyles',
                                    label: 'Styles',
                                    setup: function(widget) {
                                        this.setValue(widget.element.getAttribute('style') || '');
                                    },
                                    commit: function(widget) {
                                        widget.setData('advStyles', this.getValue());
                                    }
                                }
                            ]
                        });

                        dialogDefinition.addContents({
                            id: 'link',
                            label: 'Link',
                            elements: [
                                {
                                    type: 'text',
                                    id: 'linkUrl',
                                    label: 'URL',
                                    setup: function(widget) {
                                        let link = widget.element.findOne('a');
                                        this.setValue(link && link.is('a') ? link.getAttribute('href') : '');
                                    },
                                    commit: function(widget) {
                                        widget.setData('linkUrl', this.getValue());
                                    }
                                },
                                {
                                    type: 'select',
                                    id: 'linkTarget',
                                    label: 'Target',
                                    items: [
                                        ['None', ''],
                                        ['New Window (_blank)', '_blank'],
                                        ['Same Window (_self)', '_self'],
                                        ['Parent Window (_parent)', '_parent'],
                                        ['Topmost Window (_top)', '_top']
                                    ],
                                    setup: function(widget) {
                                        let link = widget.element.findOne('a');
                                        this.setValue(link && link.is('a') ? link.getAttribute('target') : '');
                                    },
                                    commit: function(widget) {
                                        widget.setData('linkTarget', this.getValue());
                                    }
                                }
                            ]
                        });
                    }
                }
            });

            // Handle data synchronization when switching modes
            editor.on('beforeCommandExec', function(event) {
                if (event.data.name === 'source') {
                    for (var widgetId in editor.widgets.instances) {
                        if (editor.widgets.instances.hasOwnProperty(widgetId)) {
                            var widget = editor.widgets.instances[widgetId];
                            var currentClasses = widget.element.getAttribute('class').split(' ');
                            var tagName = widget.element.getName();
                            widget.setData('advId', widget.element.getAttribute('id') || '');
                            widget.setData('advClasses', getCustomClasses(currentClasses, tagName));
                            widget.setData('advLongDesc', widget.element.getAttribute('longdesc') || '');
                            widget.setData('advStyles', widget.element.getAttribute('style') || '');
                            let link = widget.element.getParent();
                            widget.setData('linkUrl', link && link.is('a') ? link.getAttribute('href') : '');
                            widget.setData('linkTarget', link && link.is('a') ? link.getAttribute('target') : '');
                        }
                    }
                }
            });

            editor.on('afterCommandExec', function(event) {
                if (event.data.name === 'source') {
                    for (var widgetId in editor.widgets.instances) {
                        if (editor.widgets.instances.hasOwnProperty(widgetId)) {
                            var widget = editor.widgets.instances[widgetId];
                            if (widget.element.getAttribute('id')) {
                                widget.setData('advId', widget.element.getAttribute('id'));
                            }
                            if (widget.element.getAttribute('class')) {
                                var tagName = widget.element.getName();
                                var currentClasses = widget.element.getAttribute('class').split(' ');
                                widget.setData('advClasses', getCustomClasses(currentClasses, tagName));
                            }
                            if (widget.element.getAttribute('longdesc')) {
                                widget.setData('advLongDesc', widget.element.getAttribute('longdesc'));
                            }
                            if (widget.element.getAttribute('style')) {
                                widget.setData('advStyles', widget.element.getAttribute('style'));
                            }
                            let link = widget.element.getParent();
                            if (link && link.is('a')) {
                                widget.setData('linkUrl', link.getAttribute('href'));
                                widget.setData('linkTarget', link.getAttribute('target'));
                            } else {
                                widget.setData('linkUrl', '');
                                widget.setData('linkTarget', '');
                            }
                        }
                    }
                }
            });
        }
    });

    CKEDITOR.plugins.add('htmlmodule', {
        icons: 'source',
        init: function (editor) {
            CKEDITOR.dialog.add('htmlModuleDialog', function (editor) {
                return {
                    title: 'Insert HTML Module',
                    minWidth: 400,
                    minHeight: 200,
                    contents: [
                        {
                            id: 'tab1',
                            label: 'Basic Settings',
                            elements: [
                                {
                                    type: 'select',
                                    id: 'htmlModules',
                                    label: 'Choose a module',
                                    items: [], // This will be populated dynamically
                                }
                            ]
                        }
                    ],
                    onShow: function() {
                        const dialog = this;
                        const selectElement = dialog.getContentElement('tab1', 'htmlModules');
                        fetch(`/api/modules?id=${site_id}`)
                            .then(response => {
                                if (!response.ok) {
                                    throw new Error('Network response was not ok ' + response.statusText);
                                }
                                return response.json();
                            })
                            .then(modules => {
                                selectElement.clear();
                                modules.forEach(module => {
                                    selectElement.add(module[1], module[0].toString());
                                });
                            })
                            .catch(error => {
                                console.error('Error fetching modules:', error);
                            });
                    },
                    onOk: function() {
                        const moduleId = this.getValueOf('tab1', 'htmlModules');
                        fetch(`/api/modules/${moduleId}?id=${site_id}`)
                            .then(response => response.json())
                            .then(module => {
                                editor.insertHtml(module[2]);
                            });
                    }
                };
            });

            editor.addCommand('insertHtmlModule', new CKEDITOR.dialogCommand('htmlModuleDialog'));

            editor.ui.addButton('HtmlModule', {
                label: 'Insert HTML Module',
                command: 'insertHtmlModule',
                toolbar: 'insert',
                icon: 'source'
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

    // Init CKEditor
    let ckeditorConfig = {
        allowedContent: true,
        toolbar: [
            {name: "clipboard", items: ["Cut", "Copy", "Paste", "PasteText", "-", "Undo", "Redo"]}, // "PasteFromWord",
            {name: "basicstyles", items: ["Bold", "Italic", "Underline", "Strike", 'Subscript', 'Superscript', "-", "RemoveFormat"]},
            {name: "paragraph", items: ["NumberedList", "BulletedList", "-", "Outdent", "Indent", "-", "Blockquote", "CreateDiv", "-", "JustifyLeft", "JustifyCenter", "JustifyRight", "JustifyBlock"]},
            {name: "links", items: ["Link", "Unlink", "anchorPluginButton"]},
            {name: "insert", items: ["Image", "Embed", "Table", "HorizontalRule", "SpecialChar", "inserthtml4x", "Slideshow", "HtmlModule"]},
            {name: "tools", items: ["ShowBlocks"]},
            {name: "styles", items: ["Styles", "Format"]},
            // {name: "colors", items: ["TextColor", "BGColor"]},
            {name: "actions", items: ["Preview", "SaveBtn", "PublishBtn"]}
        ],
        extraPlugins: "anchor,inserthtml4x,embed,saveBtn,codemirror,image2,extendedImage2,slideshow,htmlmodule", // ,pastefromword
        removePlugins: 'image',
        image2_captionedImageClass: 'uos-component-image',
        image2_captionedClass: 'uos-component-image-caption',
        image2_alignClasses: ['uos-component-image-left', 'uos-component-image-center', 'uos-component-image-right'],
        image2_disableResizer: true,
        codemirror: {
            mode: 'htmlmixed',
            theme: 'default',
            // theme: 'darcula',
            lineNumbers: true,
            lineWrapping: true,
            styleActiveLine: true,
            keyMap: 'sublime'
        },
        codeSnippet_theme: 'prism',
        filebrowserUploadUrl: "/api/upload?name=fileupload",
        embed_provider: '//ckeditor.iframe.ly/api/oembed?url={url}&callback={callback}',
        protectedSource: new RegExp(`<script(?![^>]*src=["'][^"']*(${editor_allow_scripts_regex_patters})[^"']*["'])[^>]*>[\\s\\S]*?(<\\/script>|$)`, 'gi'),
        on: {
            setData: async function (event) {
                // Regex to find any empty tags
                let emptyTagsRegex = /<(?!script)(\w+)([^>]*?)>\s*<\/\1>/gi;
                event.data.dataValue = event.data.dataValue.replace(emptyTagsRegex, '<$1$2>&nbsp;</$1>');
            },
            instanceReady: async function (evt) {
                // Get the CKEditor instance
                let editor = evt.editor;

                editor.on('focus', function () {
                    adjustAnchorPosition(editor, "relative!important");
                    adjustDivEditable(editor, true);
                });
                editor.on('blur', function () {
                    adjustAnchorPosition(editor, false);
                    adjustDivEditable(editor, false);
                });

                editor.on('beforeCommandExec', function () {
                    if (editor.mode === 'wysiwyg') {
                        // Trying to prevent the undo JUMP that breaks the tabs
                    }
                });

                await check_if_page_is_locked(page_id);

                // Usage with CKEditor change event
                let is_locked = false;
                editor.on('change', debounce(function () {
                    if (is_locked !== true) {
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
    };

    // Conditionally add "Source" button if is_source_editor is true
    if (is_source_editor === 1 || is_admin === 1) {
        ckeditorConfig.toolbar.forEach(function (toolbarGroup) {
            if (toolbarGroup.name === "actions") {
                toolbarGroup.items.push("Source");
            }
        });
    }
    CKEDITOR.plugins.addExternal('codemirror', '/static/ck4-addons/plugins/codemirror/', 'plugin.js');

    // Initialize CKEditor with the configuration
    CKEDITOR.replace("htmlCode", ckeditorConfig);

    CKEDITOR.on('instanceReady', function (evt) {
        var editor = evt.editor;
        editor.config.filebrowserBrowseUrl = '/files/browser_img?CKEditorFuncNum=' + editor._.filebrowserFn + '&type=Images&site_id=' + site_id;
        editor.config.filebrowserImageBrowseUrl = '/files/browser_img?CKEditorFuncNum=' + editor._.filebrowserFn + '&type=Images&site_id=' + site_id;
        editor.config.filebrowserLinkBrowseUrl = '/files/browser_all_files?CKEditorFuncNum=' + editor._.filebrowserFn + '&type=Files&site_id=' + site_id;
    
        editor.document.appendStyleText(
            'div > span.cke_widget_wrapper.cke_widget_image {' +
            '    width: 100%;' +
            '}' +
            '.uos-component-image-right figure {' +
            '    float: right;' +
            '}' +
            'div.uos-component-image-right {' +
            '    float: none;' +
            '}' +
            '.uos-component-image-center {' +
            '    width: 100%;' +
            '    float: left;' +
            '    text-align: center;' +
            '}' +
            '.uos-component-image-center figure {' +
            '    float: none' +
            '}'
        );
    });

    CKEDITOR.config.contentsCss = '/static/css/ckeditor_custom_styles.css';

    // Remove loadingBg
    $(".loadingBg").removeClass("show");
});