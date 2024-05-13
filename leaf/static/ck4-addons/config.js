/**
 * @license Copyright (c) 2003-2023, CKSource Holding sp. z o.o. All rights reserved.
 * For licensing, see https://ckeditor.com/legal/ckeditor-oss-license
 */

CKEDITOR.editorConfig = function (config) {
    // Disable content filtering - NOT recommended for security reasons.
    // WARNING: This can expose your application to XSS attacks.
    config.allowedContent = true;

    // Allow full-page editing.
    // WARNING: This opens up significant security risks.
    config.fullPage = true;

    // You can uncomment these lines if you want to remove protection for anchor tags.
    // WARNING: This can expose your application to XSS attacks if not properly handled.
    config.protectedSource.push(/<a[\s\S]*?\>/g);
    config.protectedSource.push(/<\/a[\s\S]*?\>/g);

    // Allow pasting images as inline images.
    config.pasteImageInline = true;

    // Allow auto-embedding of widgets, assuming 'customEmbed' is a valid widget.
    config.autoEmbed_widget = 'customEmbed';

    // Set sandbox attributes for iframes to restrict their behavior.
    config.iframe_attributes = {
        sandbox: 'allow-scripts allow-same-origin'
    };
};
