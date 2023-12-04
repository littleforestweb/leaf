CKEDITOR.dialog.add('fileUploadDialog', function (editor) {
    return {
        title: 'File Upload',
        minWidth: 300,
        minHeight: 80,
        contents: [
            {
                id: 'upload',
                label: 'Upload',
                elements: [
                    {
                        type: 'file',
                        id: 'uploadFile',
                        label: 'Select File [JPG, GIF, PNG, JPEG, PDF, DOC, DOCX]',
                        multiple: false,
                        size: 38,
                        validate: function () {
                            // Add validation logic if required
                        },
                        setup: function () {
                            // Initialize the upload file element
                        },
                        commit: function (dialog) {
                            // Handle the uploaded file(s) here
                            var fileInput = dialog.getContentElement('upload', 'uploadFile').getInputElement().$;
                            var file = fileInput.files[0];
                            if (file) {
                                var allowedExtensions = ['jpg', 'gif', 'png', 'jpeg', 'pdf', 'doc', 'docx'];
                                var fileExtension = file.name.split('.').pop().toLowerCase();
                                if (allowedExtensions.indexOf(fileExtension) === -1) {
                                    alert('Please select a file with one of the following extensions: JPG, GIF, PNG, JPEG, PDF', 'DOC', 'DOCX');
                                    return false;
                                }
                                dialog.file = file;
                                return true;
                            } else {
                                return false;
                            }
                        }

                    }
                ]
            }
            // Add additional tabs or content sections as needed
        ],

        onOk: function () {
            var dialog = this;
            let res = dialog.getContentElement('upload', 'uploadFile').commit(dialog);
            if (res === false) {
                return
            }
            var file = dialog.file;
            if (file) {
                var uploadUrl = editor.config.filebrowserUploadUrl;
                var formData = new FormData();
                formData.append('upload', file);
                var xhr = new XMLHttpRequest();
                xhr.open('POST', uploadUrl, true);
                xhr.onload = function () {
                    var response = JSON.parse(xhr.responseText);
                    var uploadedUrl = response.url; // URL of the uploaded file returned by the backend
                    editor.insertHtml('<a target="_blank" href="' + uploadedUrl + '">' + file.name + '</a>');
                };
                xhr.send(formData);
            }
        }
    };
});
