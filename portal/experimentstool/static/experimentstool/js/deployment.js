function renderDeploymentData(selector_id, log_id, app_log_id) {
    var deployment_selector = $(selector_id).find("select")
    deployment_selector.empty();
    resetLogBox(log_id, app_log_id);
    deployment_selector.append(
        $(document.createElement('option')).attr("value", "-1").text("Loading..")
    );

    $.ajax({
        url: '/experimentstool/_get_deployments',
        beforeSend: function (xhr, settings) {
            $.ajaxSettings.beforeSend(xhr, settings);
            $(".loader").show();
        },
        success: function (data) {
            $(".loader").hide();
            if (data.redirect !== undefined && data.redirect !== null) {
                redirect(data.redirect);
            } else if (data.error !== undefined && data.error !== null) {
                appendNotification("Couldn't read the instances: " + data.error, error = true);
            } else {
                deployment_selector.empty();
                if (data.instance_list.length > 0) {
                    $.each(data.instance_list, function (index, deployment) {
                        deployment_selector.append(
                            $(document.createElement('option'))
                            .attr("value", deployment.id)
                            .text(deployment.name)
                        )
                    });
                    active_id = getActiveLogId();
                    if (active_id == "") {
                        //show exec logs by default exec log
                        $("#exec_logs").click();
                    } else {
                        _renderLogData(
                            active_id,
                            deployment_selector.val(),
                            log_id,
                            app_log_id);
                    }
                } else {
                    deployment_selector.append(
                        $(document.createElement('option')).attr("value", "-1").text(
                            "No instances found")
                    );
                }
            }
        },
        error: function (jqXHR, status, errorThrown) {
            $(".loader").hide();
            message = "Couldn't get instances list: ";
            message += jqXHR.status + ": " + errorThrown
            appendNotification(message, error = true);
        }
    });
}



function runDeployment(selector_id, log_id, force = false) {
    var deployment_id = $(selector_id).find("select").val();
    resetLogBox(log_id);
    cleanNotifications();

    $.ajax({
        method: "POST",
        url: "/experimentstool/_execute_deployment",
        data: {
            'deployment_id': deployment_id
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
                appendNotification("Run error: " + data.error, error = true);
            }
        },
        error: function (jqXHR, status, errorThrown) {
            $(".loader").hide();
            message = "Couldn't run the instance: ";
            message += jqXHR.status + ": " + errorThrown
            appendNotification(message, error = true);
        },
        complete: function () {
            renderLogData(getActiveLogId(),
                "#deployment_selector",
                "#deployment_log",
                "#application_log")
        }
    });
};

function removeDeployment(selector_id, force = false) {
    var deployment_id = $(selector_id).find("select").val();
    cleanNotifications();

    $.ajax({
        method: "POST",
        url: "/experimentstool/_destroy_deployment",
        data: {
            'deployment_id': deployment_id,
            'force': force
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
                appendNotification("Removing error: " + data.error, error = true);
            } else {
                appendNotification("Operation successful.");
            }
        },
        error: function (jqXHR, status, errorThrown) {
            $(".loader").hide();
            message = "Couldn't remove the instance: ";
            message += jqXHR.status + ": " + errorThrown
            appendNotification(message, error = true);
        },
        complete: function () {
            renderDeploymentData("#deployment_selector",
                "#deployment_log",
                "#application_log");
        }
    });
};

$("#application_selector").find("select").on('change', function () {
    renderApplicationInputs("#application_selector", "#application_inputs")
});

$("#deploy_form").find("button").on('click', function (event) {
    event.preventDefault();

    var deployment_id = $("#deployment_id").find("input").val();
    var application_id = $("#application_selector").find("select").val();

    var inputs_dict = {};
    $('input[id^="string_input_"]').each(function (index, input) { // text inputs
        inputs_dict[$(input).attr('name')] = String($(input).val());
    });
    $('input[id^="int_input_"]').each(function (index, input) { // integer inputs
        inputs_dict[$(input).attr('name')] = parseInt($(input).val());
    });
    $('input[id^="float_input_"]').each(function (index, input) { // integer inputs
        inputs_dict[$(input).attr('name')] = parseFloat($(input).val());
    });
    $('input[id^="boolean_input_"]:checked').each(function (index, input) { // boolean inputs
        inputs_dict[$(input).attr('name')] = 1 === parseInt($(input).val());
    });
    $('select[id^="input_"]').each(function (index, input) { // list inputs
        inputs_dict[$(input).attr('name')] = parseInt($(input).val());
    });
    $('input[name^="resource_"]:checked').each(function (index, input) { // resource inputs
        inputs_dict[$(input).attr('name')] = String($(input).val());
    });
    $('textarea[id^="input_"]').each(function (index, input) { // online file inputs
        inputs_dict[$(input).attr('name')] = String($(input).val());
    });
    var deployment_inputs = JSON.stringify(inputs_dict);

    var data = new FormData();
    data.append('deployment_id', deployment_id);
    data.append('application_id', application_id);
    data.append('deployment_inputs', deployment_inputs);

    cleanNotifications();
    $.ajax({
        method: "POST",
        url: '/experimentstool/_deploy_application',
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
                appendNotification("Couldn't create the instance: " + data.error, error =
                    true);
            } else {
                appendNotification("App instance " + data.instance + " created.");
            }
        },
        error: function (jqXHR, status, errorThrown) {
            $(".loader").hide();
            message = "Couldn't create the instance: ";
            message += jqXHR.status + ": " + errorThrown
            appendNotification(message, error = true);
        },
        complete: function () {
            $("#application_inputs").empty()
            renderDeploymentData("#deployment_selector",
                "#deployment_log",
                "#application_log");
        }
    });
});

$("#deployment_selector").find("select").on('change', function () {
    renderLogData(getActiveLogId(),
        "#deployment_selector",
        "#deployment_log",
        "#application_log")
});

$("#run-instance-button").on('click', function (event) {
    event.preventDefault();
    runDeployment("#deployment_selector",
        "#deployment_log")
});

$("#destroy-instance-button").on('click', function (event) {
    event.preventDefault();
    removeDeployment("#deployment_selector");
    renderDeploymentData("#deployment_selector",
        "#deployment_log",
        "#application_log");
});

$("#force-destroy-instance-button").on('click', function (event) {
    event.preventDefault();
    removeDeployment("#deployment_selector", force = true);
});

$('.wrapper').find('.toogle').on('click', function (e) {
    e.preventDefault();
    this.expand = !this.expand;
    $(this).html(this.expand ? "&uarr; Add a new one:" : "&rarr; Add a new one");
    $(this).closest('.wrapper').find('.collapsed, .expanded').toggleClass('collapsed expanded');
});