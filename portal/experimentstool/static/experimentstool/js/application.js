function renderStockData(selector_id, cleanup = true) {
    var product_selector = $(selector_id).find("select")
    product_selector.empty();
    if (cleanup) {
        cleanNotifications();
    }

    $.ajax({
        url: '/experimentstool/_get_new_stock',
        beforeSend: function (xhr, settings) {
            $.ajaxSettings.beforeSend(xhr, settings);
            $(".loader").show();
        },
        success: function (products) {
            $(".loader").hide();
            if (products.redirect !== undefined && products.redirect !== null) {
                redirect(products.redirect);
            } else {
                product_selector.append(
                    $(document.createElement('option'))
                    .attr("value", "-1")
                    .text("Register for all users")
                );
                if (products.length > 0) {
                    $.each(products, function (index, product) {
                        product_selector.append(
                            $(document.createElement('option'))
                            .attr("value", product.id)
                            .text(product.name)
                        )
                    });
                }
            }
        },
        error: function (jqXHR, status, errorThrown) {
            $(".loader").hide();
            message = "Couldn't get stock list: ";
            message += jqXHR.status + ": " + errorThrown
            appendNotification(message, error = true);
        }
    });
}

$("#upload").find("button").on('click', function (event) {
    event.preventDefault();
    if (!window.File || !window.FileReader || !window.FileList || !window.Blob) {
        appendNotification('The File APIs are not fully supported in this browser.', error = true);
        return
    }

    var product = $("#product_selector").find("select").val();
    var mso_id = $("#mso4sc_id").find("input").val();
    var blueprint_package = $("#blueprint_package").find("input")[0];

    cleanNotifications();
    var blueprint = null
    if (blueprint_package && blueprint_package.files && blueprint_package.files[0]) {
        blueprint = blueprint_package.files[0]
    } else {
        appendNotification('No package provided', error = true);
        return
    }

    var data = new FormData();
    data.append('product', product);
    data.append('mso_id', mso_id);
    data.append('blueprint_package', blueprint);
    $.ajax({
        url: '/experimentstool/_upload_application',
        type: "POST",
        data: data,
        dataType: 'json',
        contentType: false,
        processData: false,
        cache: false,
        beforeSend: function (xhr, settings) {
            $.ajaxSettings.beforeSend(xhr, settings);
            $(".loader").show();
        },
        success: function (data) {
            $(".loader").hide();
            if (data.redirect !== undefined && data.redirect !== null) {
                redirect(data.redirect);
            } else if (data.error !== undefined && data.error !== null) {
                appendNotification("Couldn't register the app: " + data.error, error = true);
            } else {
                appendNotification("App " + data.app.name + " registered.");
            }
        },
        error: function (jqXHR, status, errorThrown) {
            $(".loader").hide();
            message = "Couldn't register the app: ";
            message += jqXHR.status + ": " + errorThrown
            appendNotification(message, error = true);
        },
        complete: function () {
            renderStockData("#product_selector", cleanup = false);
            renderApplicationData("#remove_application_selector", only_owned = true);
        }
    });
});

$("#remove").find("button").on('click', function (event) {
    event.preventDefault();
    var application_id = $("#remove_application_selector").find("select").val();

    $.ajax({
        url: '/experimentstool/_remove_application',
        data: {
            'application_id': application_id
        },
        dataType: 'json',
        beforeSend: function (xhr, settings) {
            $.ajaxSettings.beforeSend(xhr, settings);
            $(".loader").show();
        },
        success: function (data) {
            $(".loader").hide();
            if (data.redirect !== undefined && data.redirect !== null) {
                redirect(data.redirect);
            } else if (data.error !== undefined && data.error !== null) {
                appendNotification("Couldn't remove the app: " + data.error, error = true);
            } else {
                appendNotification("App " + data.app.name + " removed.");
            }
        },
        error: function (jqXHR, status, errorThrown) {
            $(".loader").hide();
            message = "Couldn't remove the app: ";
            message += jqXHR.status + ": " + errorThrown
            appendNotification(message, error = true);
        },
        complete: function () {
            renderStockData("#product_selector", cleanup = false);
            renderApplicationData("#remove_application_selector", only_owned = true);
        }
    });
});