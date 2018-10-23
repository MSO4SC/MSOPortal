function renderTunnelData(container_id, select = true, clear_notifications = true) {
    var tunnel_container = $(container_id);
    if (select) {
        tunnel_container = tunnel_container.find("select");
    }
    tunnel_container.empty();
    if (clear_notifications) {
        cleanNotifications();
    }

    $.ajax({
        url: '/experimentstool/_get_tunnel_list',
        beforeSend: function (xhr, settings) {
            $.ajaxSettings.beforeSend(xhr, settings);
            $(".loader").show();
        },
        success: function (data) {
            $(".loader").hide();
            if (data.redirect !== undefined && data.redirect !== null) {
                redirect(data.redirect);
            } else if (data.error !== undefined && data.error !== null) {
                message = "Couldn't get tunnel list: " + data.error;
                appendNotification(message, error = true);
            } else {
                if (select) {
                    tunnel_container.append(
                        $(document.createElement('option'))
                        .attr("value", -1)
                        .text("None")
                    )
                }
                var tunnel_list = data.tunnel_list;
                if (tunnel_list.length > 0) {
                    $.each(tunnel_list, function (index, tunnel) {
                        if (select) {
                            tunnel_container.append(
                                $(document.createElement('option'))
                                .attr("value", tunnel.id)
                                .text(tunnel.name)
                            )
                        } else {
                            tunnel_container.append(
                                $(document.createElement('div')).attr("id", "tunnel_block_" +
                                    tunnel.id).attr("class",
                                    "margin computing_settings_block").append(
                                    $(document.createElement('div')).attr("class",
                                        "s-12 m-6 l-8").append(
                                        $(document.createElement('div')).attr("class",
                                            "l-9 left").append(
                                            $(document.createElement('div')).append(
                                                $(document.createElement('span')).attr(
                                                    "class",
                                                    "computing_label computing_label_name")
                                                .text('Name: '),
                                                $(document.createElement('span')).text(
                                                    tunnel.name),
                                            ),
                                            $(document.createElement('div')).append(
                                                $(document.createElement('span')).attr(
                                                    "class", "computing_label").text(
                                                    'Host: '),
                                                $(document.createElement('span')).text(
                                                    tunnel.host),
                                            ),
                                            $(document.createElement('div')).append(
                                                $(document.createElement('span')).attr(
                                                    "class", "computing_label").text(
                                                    'User: '),
                                                $(document.createElement('span')).text(
                                                    tunnel.user),
                                            )
                                        ),
                                        $(document.createElement('div')).attr("class",
                                            "l-3 right").append(
                                            $(document.createElement('button')).attr("id",
                                                "del_tunnel_" + tunnel.id).text('Delete')
                                        )
                                    )
                                )
                            );
                            setTunnelEditButtonsHandler(
                                "#del_tunnel_" + tunnel.id,
                                tunnel.id,
                                refresh_function = function () {
                                    renderTunnelData(container_id,
                                        select = false,
                                        clear_notifications = false);
                                }
                            );
                        }
                    });
                } else {
                    if (!select) {
                        tunnel_container.append(
                            $(document.createElement('div'))
                            .attr("id", "no_tunnel_list")
                            .text("No Tunnel infrastructures found")
                        )
                    }
                }
            }
        },
        error: function (jqXHR, status, errorThrown) {
            $(".loader").hide();
            message = "Couldn't get tunnel list: ";
            message += jqXHR.status + ": " + errorThrown
            appendNotification(message, error = true);
        }
    });
}

function setTunnelEditButtonsHandler(button_id, pk, refresh_function) {
    $(button_id).on('click', function (event) {
        event.preventDefault();
        $.ajax({
            method: "POST",
            url: '/experimentstool/_delete_tunnel',
            data: {
                'pk': pk
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
                    appendNotification("Couldn't delete the tunnel: " + data.error, error =
                        true);
                } else {
                    appendNotification("Tunnel " + data.tunnel.name + " removed.");
                }
            },
            error: function (jqXHR, status, errorThrown) {
                $(".loader").hide();
                message = "Couldn't remove the tunnel: ";
                message += jqXHR.status + ": " + errorThrown
                appendNotification(message, error = true);
            },
            complete: refresh_function
        });
    });
}

function renderInfraData(container_id, select = true, clear_notifications = true) {
    var infra_container = $(container_id);
    if (select) {
        infra_container = infra_container.find("select");
    }
    infra_container.empty();
    if (clear_notifications) {
        cleanNotifications();
    }

    $.ajax({
        url: '/experimentstool/_get_infra_list',
        beforeSend: function (xhr, settings) {
            $.ajaxSettings.beforeSend(xhr, settings);
            $(".loader").show();
        },
        success: function (data) {
            $(".loader").hide();
            if (data.redirect !== undefined && data.redirect !== null) {
                redirect(data.redirect);
            } else if (data.error !== undefined && data.error !== null) {
                message = "Couldn't get infra list: " + data.error;
                appendNotification(message, error = true);
            } else {
                var infra_list = data.infra_list;
                if (infra_list.length > 0) {
                    if (select) {
                        infra_container.append(
                            $(document.createElement('option'))
                            .attr("value", "-1")
                            .text("Choose...")
                        )
                    }
                    $.each(infra_list, function (index, infra) {
                        if (select) {
                            infra_container.append(
                                $(document.createElement('option'))
                                .attr("value", infra.id)
                                .text(infra.name + " (" + infra.infra_type + ")")
                            )
                        } else {
                            var edit_button;
                            if (infra.owned) {
                                edit_button = $(document.createElement('div')).
                                attr("class", "l-3 right").
                                append(
                                    $(document.createElement('button')).attr("id",
                                        "del_infra_" + infra.id).text('Delete')
                                )
                            } else {
                                edit_button = $(document.createElement('div')).
                                attr("class", "l-3 right")
                            }
                            infra_container.append(
                                $(document.createElement('div')).attr("id", "infra_block_" +
                                    infra.id).attr("class",
                                    "margin computing_settings_block").append(
                                    $(document.createElement('div')).attr("class",
                                        "s-12 m-6 l-8").append(
                                        $(document.createElement('div')).attr("class",
                                            "l-9 left").append(
                                            $(document.createElement('div')).append(
                                                $(document.createElement('span')).attr(
                                                    "class",
                                                    "computing_label computing_label_name")
                                                .text('Name: '),
                                                $(document.createElement('a')).attr("href",
                                                    infra.about_url).attr("target",
                                                    "_blank").text(infra.name),
                                            ),
                                            $(document.createElement('div')).append(
                                                $(document.createElement('span')).attr(
                                                    "class", "computing_label").text(
                                                    'Type: '),
                                                $(document.createElement('span')).text(
                                                    infra.infra_type),
                                            ),
                                            $(document.createElement('div')).append(
                                                $(document.createElement('span')).attr(
                                                    "class", "computing_label").text('WM: '),
                                                $(document.createElement('span')).text(
                                                    infra.manager),
                                            ),
                                            $(document.createElement('div')).append(
                                                $(document.createElement('span')).attr(
                                                    "class", "computing_label").text(
                                                    'Definition: '),
                                                $(document.createElement('span')).text(
                                                    infra.definition),
                                            ),
                                        ),
                                        edit_button,
                                    )
                                )
                            );
                            if (infra.owned) {
                                setInfraEditButtonsHandler(
                                    '/experimentstool/_delete_infra',
                                    "#del_infra_" + infra.id,
                                    infra.id,
                                    refresh_function = function () {
                                        renderInfraData(
                                            container_id,
                                            select = false,
                                            clear_notifications = false);
                                    }
                                );
                            }
                        }
                    });
                } else {
                    if (!select) {
                        infra_container.append(
                            $(document.createElement('div')).attr("id", "no_infra_list").text(
                                "No definitions found")
                        )
                    }
                }
            }
        },
        error: function (jqXHR, status, errorThrown) {
            $(".loader").hide();
            message = "Couldn't get infra list: ";
            message += jqXHR.status + ": " + errorThrown
            appendNotification(message, error = true);
        }
    });
}

function renderComputingData(container_id, select = true, clear_notifications = true) {
    var computing_container = $(container_id);
    if (select) {
        computing_container = computing_container.find("select");
    }
    computing_container.empty();
    if (clear_notifications) {
        cleanNotifications();
    }

    $.ajax({
        url: '/experimentstool/_get_computing_list',
        beforeSend: function (xhr, settings) {
            $.ajaxSettings.beforeSend(xhr, settings);
            $(".loader").show();
        },
        success: function (data) {
            $(".loader").hide();
            if (data.redirect !== undefined && data.redirect !== null) {
                redirect(data.redirect);
            } else if (data.error !== undefined && data.error !== null) {
                message = "Couldn't get computing list: " + data.error;
                appendNotification(message, error = true);
            } else {
                var computing_list = data.computing_list;
                if (computing_list.length > 0) {
                    $.each(computing_list, function (index, computing) {
                        if (select) {
                            computing_container.append(
                                $(document.createElement('option'))
                                .attr("value", computing.id)
                                .text(computing.name)
                            )
                        } else {
                            console.log(computing[0]);
                            computing_container.append(
                                $(document.createElement('div')).attr("id",
                                    "computing_block_" + computing.id).attr("class",
                                    "margin computing_settings_block").append(
                                    $(document.createElement('div')).attr("class",
                                        "s-12 m-6 l-8").append(
                                        $(document.createElement('div')).attr("class",
                                            "l-9 left").append(
                                            $(document.createElement('div')).append(
                                                $(document.createElement('span')).attr(
                                                    "class",
                                                    "computing_label computing_label_name")
                                                .text('Name: '),
                                                $(document.createElement('span')).text(
                                                    computing.name),
                                            ),
                                            $(document.createElement('div')).append(
                                                $(document.createElement('span')).attr(
                                                    "class", "computing_label").text(
                                                    'Infrastructure: '),
                                                $(document.createElement('span')).text(
                                                    computing.infrastructure),
                                            ),
                                            $(document.createElement('div')).append(
                                                $(document.createElement('span')).attr(
                                                    "class", "computing_label").text(
                                                    'Definition: '),
                                                $(document.createElement('span')).text(
                                                    computing.definition),
                                            ),
                                        ),
                                        $(document.createElement('div')).attr("class",
                                            "l-3 right").append(
                                            $(document.createElement('button')).attr("id",
                                                "del_computing_" + computing.id).text(
                                                'Delete')
                                        )
                                    )
                                )
                            );
                            setInfraEditButtonsHandler(
                                '/experimentstool/_delete_computing',
                                "#del_computing_" + computing.id,
                                computing.id,
                                refresh_function = function () {
                                    renderComputingData(
                                        container_id,
                                        select = false,
                                        clear_notifications = false);
                                }
                            );
                        }
                    });
                } else {
                    if (!select) {
                        computing_container.append(
                            $(document.createElement('div')).attr("id", "no_computing_list").text(
                                "No HPC infrastructures found")
                        )
                    }
                }
            }
        },
        error: function (jqXHR, status, errorThrown) {
            $(".loader").hide();
            message = "Couldn't get computing list: ";
            message += jqXHR.status + ": " + errorThrown
            appendNotification(message, error = true);
        }
    });
}

function setInfraEditButtonsHandler(ajax_url, button_id, pk, refresh_function) {
    $(button_id).on('click', function (event) {
        event.preventDefault();
        $.ajax({
            method: "POST",
            url: ajax_url,
            data: {
                'pk': pk
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
                    appendNotification("Couldn't delete the computing: " + data.error, error =
                        true);
                } else {
                    if (data.infra != undefined) {
                        appendNotification("Infrastructure " + data.infra.name + " removed.");
                    } else {
                        appendNotification("Computing infra " + data.computing.name + " removed.");
                    }

                }
            },
            error: function (jqXHR, status, errorThrown) {
                $(".loader").hide();
                message = "Couldn't remove the computing: ";
                message += jqXHR.status + ": " + errorThrown
                appendNotification(message, error = true);
            },
            complete: refresh_function
        });
    });
}

$("#add_infra").find("button").on('click', function (event) {
    event.preventDefault();
    if (!window.File || !window.FileReader || !window.FileList || !window.Blob) {
        appendNotification('The File APIs are not fully supported in this browser.', error = true);
    }

    var name = $("#add_infra_name").val();
    var about = $("#add_infra_about").val();
    var infra_type = $("#add_infra_type").val();
    var manager = $("#add_infra_manager").val();
    var def_file = $("#add_infra_definition")[0]

    var definition = null
    if (def_file && def_file.files && def_file.files[0]) {
        definition = def_file.files[0]
    }

    cleanNotifications();
    if (name != '' && about != '' && def_file != null && def_file != '') {
        var data = new FormData();
        data.append('name', name);
        data.append('about', about);
        data.append('infra_type', infra_type);
        data.append('manager', manager);
        data.append('definition', definition);

        $.ajax({
            url: '/experimentstool/_add_infra',
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
                    appendNotification("Couldn't add the infrastructure: " + data.error,
                        error =
                        true);
                } else {
                    appendNotification("Infrastructure " + data.infra.name + " added.");
                }
            },
            error: function (jqXHR, status, errorThrown) {
                $(".loader").hide();
                message = "Couldn't add the infrastructure: ";
                message += jqXHR.status + ": " + errorThrown
                appendNotification(message, error = true);
            },
            complete: function () {
                renderInfraData("#infra_list", selector = false, clean = false);
            }
        });
    }
});

$("#add_computing").find("button").on('click', function (event) {
    event.preventDefault();
    if (!window.File || !window.FileReader || !window.FileList || !window.Blob) {
        appendNotification('The File APIs are not fully supported in this browser.', error = true);
    }

    var name = $("#add_computing_name").val();
    var infra = $("#infra_selector").find("select").val();

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
        inputs_dict[$(input).attr('id')] = 1 === parseInt($(input).val());
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
    var json_inputs = JSON.stringify(inputs_dict);

    cleanNotifications();

    var data = new FormData();
    data.append('name', name);
    data.append('infra', infra);
    data.append('inputs', json_inputs);
    $.ajax({
        url: '/experimentstool/_add_computing',
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
                appendNotification("Couldn't add the computing infrastructure: " + data
                    .error,
                    error = true);
            } else {
                appendNotification("Computing infrastructure " + data.computing.name +
                    " added.");
            }
        },
        error: function (jqXHR, status, errorThrown) {
            $(".loader").hide();
            message = "Couldn't add the computing infrastructure: ";
            message += jqXHR.status + ": " + errorThrown
            appendNotification(message, error = true);
        },
        complete: function () {
            renderComputingData("#computing_instance_list", selector = false, clean =
                false);
        }
    });
});

$("#infra_selector").find("select").on('change', function () {
    renderInputsData(
        '#infra_selector',
        "#infra_inputs",
        "infra")
});