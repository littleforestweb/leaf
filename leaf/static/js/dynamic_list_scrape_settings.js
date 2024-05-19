async function populateScrapeSettingsDynamicList() {
  dropDownActionsToggle();
	// Get list configuration
  let jsonColumns = await $.get("/api/get_list_columns_with_properties/" + accountId + "/" + reference, function (result) {
		return result;
  });
  var headColumns = jsonColumns.columns;

  let scrapeSettings = await $.get("/api/get_list_scrape_settings/" + accountId + "/" + reference, function (result) {
    return result;
  });

  var jsonScrapeSettings = [];
  if (scrapeSettings["scrape_settings"] && scrapeSettings["scrape_settings"][2]) {
    const unescapedString = unescapeHtml(scrapeSettings["scrape_settings"][2]);
    jsonScrapeSettings = JSON.parse(unescapedString);
  }

  if (unescapeHtml(jsonScrapeSettings["s-folders_to_scrape"]) != undefined) {
    $("#s-folders_to_scrape").val(unescapeHtml(jsonScrapeSettings["s-folders_to_scrape"]));
  }

  $('#available_fields_mapping_container').html("");

  headColumns.forEach(key => {
    const fullKey = `scrape__${key[2]}`;
    if (key[2] !== "modified_by" && key[2] !== "modified" && key[2] !== "created") {
      if (jsonScrapeSettings.hasOwnProperty(fullKey)) {
        const escapedValue = escapeHtmlTags(jsonScrapeSettings[fullKey]);
        $('#available_fields_mapping_container').append(`<div class="mb-3 mb-container s-pub_date-container"><div class="row"><div class="col-auto"><label for="scrape__${key[2]}" class="col-form-label">${key[2]}:</label></div><div class="col"><input type="text" class="form-control" name="scrape__${key[2]}" id="scrape__${key[2]}" value="${escapedValue}" /></div></div></div>`);
      } else {
        console.log(`${key[2]} not found`);
      }
    }
  });
}

async function scrapeSettingsDynamicList(accountId, reference, action) {
	accountId = escapeHtml(accountId);
  reference = escapeHtml(reference);
  action = escapeHtml(action);

  if (action === 'save') {
    var form_data = await getFormData('setScrapeSettings-' + reference, false);

    $.ajax({
      type: "POST",
      url: "/set/scrape_settings/" + accountId + "/" + reference,
      contentType: 'application/json',
      data: JSON.stringify(form_data),
      dataType: 'json',
      cache: false,
      processData: false,
      success: function (response) {
        $('#scrapeSettingsDynamicList').modal('hide');
        $('#scrapeSettingsDynamicList form input').val('');

        $('#scrapeDynamicListSuccessNotification').toast('show');

        doRedrawTable(false, false, true);
      },
      error: function (XMLHttpRequest, textStatus, errorThrown) {
        $('#errorModal').modal('show');
      }
    });
	} else {
    $('#scrapeSettingsDynamicList').modal('hide');
    $('#scrapeSettingsDynamicList form input').val('');
	}
}

async function triggerNewScrape(accountId, reference) {
  accountId = escapeHtml(accountId);
  reference = escapeHtml(reference);

  $.ajax({
    type: "POST",
    url: "/api/trigger_new_scrape",
    data: {
      "accountId": accountId,
      "reference": reference
    },
    success: function (response) {
      if (response.status) {
        $('#scrapeSettingsDynamicList').modal('hide');
        $('#scrapeSettingsDynamicList form input').val('');
        
        $('#scrapeDynamicListSuccessRunningNotification').toast('show');
        doRedrawTable(false, false, true);
      }
    },
    error: function (XMLHttpRequest, textStatus, errorThrown) {
      $('#errorModal').modal('show');
    }
  });
}