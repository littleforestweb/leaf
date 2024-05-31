/*
    Created on : 30 Mar 2024, 20:16:19
    Author     : xhico
*/

window.addEventListener('DOMContentLoaded', async function main() {
    console.log("Starting");
    console.log("Get Page Diff");
    console.log(page_id, commit_id_1, commit_id_2);

    // Get Diff Text
    $.ajax({
        type: "POST",
        url: "/api/versions_diff",
        contentType: 'application/json',
        data: JSON.stringify({"page_id": page_id, "commit_id_1": commit_id_1, "commit_id_2": commit_id_2}),
        dataType: 'json',
        cache: false,
        processData: false,
        success: function (entry) {
            let diff_text = entry["diff_text"];
            let targetElement = document.getElementById("diff_text_div");
            let configuration = {drawFileList: true, matching: 'lines'};
            let diff2htmlUi = new Diff2HtmlUI(targetElement, diff_text, configuration);
            diff2htmlUi.draw();
            $(".loadingBg").removeClass("show");
        },
        error: function (XMLHttpRequest, textStatus, errorThrown) {
            $(".loadingBg").removeClass("show");
            console.log("ERROR");
            document.getElementById("versioningNotification").classList.add("bg-danger");
            document.getElementById("versioningNotificationMsg").innerHTML = "<span>Failed to get version changes</span>"
            $('#versioningNotification').toast('show');
        }
    });
});


