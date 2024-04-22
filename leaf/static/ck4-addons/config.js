/**
 * @license Copyright (c) 2003-2023, CKSource Holding sp. z o.o. All rights reserved.
 * For licensing, see https://ckeditor.com/legal/ckeditor-oss-license
 */

CKEDITOR.editorConfig = function (config) {
    // Define changes to default configuration here. For example:
    config.pasteImageInline = true;
    config.autoEmbed_widget = 'customEmbed';
    config.iframe_attributes = {
        sandbox: 'allow-scripts allow-same-origin'
    };
    config.protectedSource.push(/<a[\s\S]*?\>/g);
    config.protectedSource.push(/<\/a[\s\S]*?\>/g);
};
