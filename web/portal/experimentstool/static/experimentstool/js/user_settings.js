function renderKeyData(container_id) {
    var key_input = $(container_id).find("input");
    $.ajax({
        url: '/experimentstool/_get_ckan_key',
        success: function (data) {
            if (data.error !== undefined && data.error !== null) {
                appendNotification("Couldn't read the inputs: " + data.error, error = true);
            } else if (data.key != undefined) {
                var code = data.key.code
                var blind_code = ""
                for (var i = 0; i < code.length; i++) {
                    if (i < 4) {
                        blind_code += code.charAt(i);
                    } else {
                        blind_code += '*';
                    }
                }
                key_input.val(blind_code);
            }
        },
        error: function (jqXHR, status, errorThrown) {
            message = "Couldn't get ckan key: ";
            message += jqXHR.status + ": " + errorThrown + ": " + jqXHR.responseText
            appendNotification(message, error = true);
        }
    });
}

$("#ckan_key_form").find("button").on('click', function (event) {
    event.preventDefault();
    var ckan_key = $("#ckan_key").val();

    cleanNotifications();
    $.ajax({
        url: '/experimentstool/_update_ckan_key',
        type: "POST",
        data: {
            'ckan_key': ckan_key,
        },
        dataType: 'json',
        beforeSend: function (xhr, settings) {
            $.ajaxSettings.beforeSend(xhr, settings);
            $(".loader").show();
        },
        success: function (data) {
            $(".loader").hide();
            if (data.error !== undefined && data.error !== null) {
                appendNotification("Couldn't update the key: " + data.error, error = true);
            } else {
                appendNotification("Key updated.");
            }
        },
        error: function (jqXHR, status, errorThrown) {
            $(".loader").hide();
            message = "Couldn't update the key: ";
            message += jqXHR.status + ": " + errorThrown + ": " + jqXHR.responseText
            appendNotification(message, error = true);
        }
    });
});