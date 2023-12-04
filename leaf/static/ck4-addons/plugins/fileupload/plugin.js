CKEDITOR.plugins.add('fileupload', {
    icons: 'fileupload',
    init: function (editor) {
        editor.addCommand('openFileUploadDialog', {
            exec: function (editor) {
                // Open your file upload dialog box here
                editor.openDialog('fileUploadDialog');
            }
        });

        editor.ui.addButton('FileUpload', {
            label: 'File Upload',
            command: 'openFileUploadDialog',
            toolbar: 'insert',
            icon: this.path + 'icons/fileupload.png'
        });

        CKEDITOR.dialog.add('fileUploadDialog', this.path + 'dialogs/fileupload.js');
    }
});
