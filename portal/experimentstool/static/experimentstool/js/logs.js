$status_timeout = null;

function stop_status() {
    if ($status_timeout != null) {
        clearTimeout($status_timeout);
    }
}

$log_timeout = null;

function stop_logs() {
    if ($log_timeout != null) {
        clearTimeout($log_timeout);
    }
}

$progress_timeout = null;

function stop_progress() {
    if ($progress_timeout != null) {
        clearTimeout($progress_timeout)
    }
}

function resetLogBox(log_id, app_log_id) {
    $(log_id + "_light").attr("src", "/static/experimentstool/img/light_grey.png");
    $(log_id).find("textarea").val('');
    $(app_log_id).attr("data", "");
}

function getActiveLogId() {
    active = "";
    tablinks = document.getElementsByClassName("logMenu");
    for (i = 0; i < tablinks.length; i++) {
        if (tablinks[i].classList.contains("active")) {
            active = tablinks[i].id
            break;
        }
    }

    if (active == "") {
        $('#exec_logs').addClass('active');
        active = '#exec_logs';
    }

    return active;
}

function renderStatusData(instance_id, log_id, reset = true) {
    var light = $(log_id + "_light");
    if (reset) {
        light.attr("src", "/static/experimentstool/img/light_grey.png");
        stop_status();
    }

    $.ajax({
        url: '/experimentstool/_get_executions_status',
        data: {
            'instance_id': instance_id
        },
        success: function (data) {
            if (data.redirect !== undefined && data.redirect !== null) {
                redirect(data.redirect);
            } else if (data.error !== undefined && data.error !== null) {
                appendNotification("Couldn't get the operation status: " + data.error, error = true);
            } else {
                // Schedule the next request when the current one's complete
                if (!data.finished) {
                    $status_timeout = setTimeout(
                        function () {
                            renderStatusData(instance_id, log_id, reset = false);
                        },
                        2500);
                    light.attr("src", "/static/experimentstool/img/light_blue.png");
                } else {
                    if (data.status == "ready") {
                        light.attr("src", "/static/experimentstool/img/light_yellow.png");
                    } else if (data.status == "terminated") {
                        light.attr("src", "/static/experimentstool/img/light_green.png");
                    } else {
                        light.attr("src", "/static/experimentstool/img/light_red.png");
                    }
                }
            }
        },
        error: function (jqXHR, status, errorThrown) {
            message = "Couldn't get the operation status: ";
            message += jqXHR.status + ": " + errorThrown
            appendNotification(message, error = true);
        }
    });
}

function renderProgressData(instance_id, progress_id, reset = true) {
    var progress = $(progress_id);
    if (reset) {
        progress.val("");
        stop_progress();
        cleanNotifications();
    }

    $.ajax({
        url: '/experimentstool/_get_progress',
        data: {
            'instance_id': instance_id,
            'reset': reset
        },
        success: function (data) {
            if (data.redirect !== undefined && data.redirect !== null) {
                redirect(data.redirect);
            } else if (data.error !== undefined && data.error !== null) {
                appendNotification("Couldn't monitor the operation: " + data.error, error = true);
            } else {
                if (data.workflow_status != undefined && data.progress !== undefined) {
                    progress.text(data.workflow_status + ": " + data.progress)
                }

                // Schedule the next request when the current one's complete
                if (!data.finished) {
                    $progress_timeout = setTimeout(
                        function () {
                            renderProgressData(instance_id, progress_id, reset = false);
                        },
                        2500);
                }
            }
        },
        error: function (jqXHR, status, errorThrown) {
            message = "Couldn't monitor the operation: ";
            message += jqXHR.status + ": " + errorThrown
            appendNotification(message, error = true);
        }
    });
}

function renderLogData(log_type, selector_id, log_id, app_log_id, reset = true) {
    var deployment_selector = $(selector_id).find("select")
    _renderLogData(log_type,
        deployment_selector.val(),
        log_id,
        app_log_id,
        reset = reset)
}

function _renderLogData(log_type, instance_id, log_id, app_log_id, reset = true) {
    switch (log_type) {
        case "exec_logs":
            _renderExecLogData(instance_id, log_id, reset);
            break;
        case "app_logs":
            _renderAppLogData(instance_id, app_log_id);
            break;
        case "":
            console.log("log type '" + log_type + "' not supported!")
            break;
    }

}

function _renderExecLogData(instance_id, log_id, reset = true) {
    var textarea = $(log_id).find("textarea");
    if (reset) {
        textarea.val("");
        stop_logs();
        cleanNotifications();
    }

    $.ajax({
        url: '/experimentstool/_get_executions_events',
        data: {
            'instance_id': instance_id,
            'reset': reset
        },
        success: function (data) {
            if (data.redirect !== undefined && data.redirect !== null) {
                redirect(data.redirect);
            } else if (data.error !== undefined && data.error !== null) {
                appendNotification("Couldn't monitor the operation: " + data.error, error = true);
            } else {
                if (data.events !== undefined && data.events.logs !== undefined) {
                    // Write events in the textarea
                    textarea.val("");
                    data.events.logs.forEach(function (event) {
                        textarea.val(textarea.val() +
                            "[" + event.generated + "] " +
                            event.message +
                            '\n');
                    });
                }

                // Schedule the next request when the current one's complete
                var light = $(log_id + "_light");
                if (!data.events.finished) {
                    $log_timeout = setTimeout(
                        function () {
                            _renderExecLogData(instance_id, log_id, reset = false);
                        },
                        2500);
                }
            }
        },
        error: function (jqXHR, status, errorThrown) {
            message = "Couldn't monitor the operation: ";
            message += jqXHR.status + ": " + errorThrown
            appendNotification(message, error = true);
        }
    });
}

function _renderAppLogData(instance_id, log_id, reset = true) {
    var textarea = $(log_id).find("textarea");
    if (reset) {
        textarea.val("");
        stop_logs();
        cleanNotifications();
    }

    $.ajax({
        url: '/experimentstool/_get_runjobs_workflowid',
        data: {
            'instance_id': instance_id
        },
        success: function (data) {
            if (data.redirect !== undefined && data.redirect !== null) {
                redirect(data.redirect);
            } else if (data.error !== undefined && data.error !== null) {
                appendNotification("Couldn't monitor the operation: " + data.error, error = true);
            } else {
                if (data.workflowid !== undefined) {
                    $(log_id).attr("data", "http://logging.mso4sc.eu:8080/default/" + data.workflowid);
                } else {
                    $(log_id).attr("data", "http://logging.mso4sc.eu:8080/default/none");
                }
            }
        },
        error: function (jqXHR, status, errorThrown) {
            message = "Couldn't monitor the operation: ";
            message += jqXHR.status + ": " + errorThrown
            appendNotification(message, error = true);
        }
    });
}