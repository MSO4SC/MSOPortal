function renderInputsData(selector_id, container_id, type) {
    var pk = $(selector_id).find("select").val();

    if (pk != "-1") {
        $.ajax({
            url: '/experimentstool/_get_inputs',
            type: "POST",
            data: {
                'type': type,
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
                } else if (data.error !== null && data.error !== undefined) {
                    appendNotification("Couldn't read input data: " + data.error, error = true);
                } else {
                    _renderInputsData(container_id, data.inputs, data.infra_config, data.user_config)
                }
            },
            error: function (jqXHR, status, errorThrown) {
                $(".loader").hide();
                message = "Couldn't read the " + type + " inputs: ";
                message += jqXHR.status + ": " + errorThrown
                appendNotification(message, error = true);
            }
        });
    } else {
        $(container_id).empty();
    }
}

function _renderInputsData(container_id, inputs, infra_config, user_config) {
    var inputs_container = $(container_id);
    inputs_container.empty();

    dependencies = {}
    onchange = {}

    $(inputs).each(function (index, tuple) {
        var input_id = tuple[0]
        var input = tuple[1]
        var name = input.name;
        var description = (('description' in input) ? input.description : '');
        var type = input.type;
        var advanced = (('advanced' in input) ? input.advanced : false);
        var can_be_null = (('null' in input) ? input.null : false);

        var register_onchange = false;

        switch (type) {
            case "list":
                var error = ""
                //copy the choices object
                var choices = JSON.parse(JSON.stringify(input.choices));
                if (!Array.isArray(choices)) {
                    if ($.isPlainObject(choices) && 'REPLACE' in choices) {
                        response = replaceTag(
                            choices,
                            infra_config,
                            user_config,
                            dependencies)
                        choices = response[0]
                        register_onchange = response[1]
                    } else {
                        error = "Error parsing input data!";
                    }
                }

                var select = $(document.createElement('select'))
                    .attr({
                        id: "input_" + input_id,
                        name: input_id,
                        title: description
                    });

                inputs_container.append( //list select box
                    $(document.createElement('div')).attr({
                        id: "input_container_" + input_id
                    }).append(
                        $(document.createElement('label'))
                        .attr({
                            for: "input_" + input_id,
                            title: description
                        })
                        .text(name),
                        select
                    )
                );

                if (error == "") {
                    options_list = []
                    if (can_be_null) {
                        options_list.push(
                            $(document.createElement('option'))
                            .attr("value", -1)
                            .text("None"))
                    }

                    for (let i = 0; i < choices.length; i++) {
                        opt = $(document.createElement('option'))
                            .attr("value", i)
                            .text(choices[i].name)
                        if ("default" in choices[i] && choices[i].default) {
                            opt.attr("selected", true)
                        }
                        options_list.push(opt)
                    }

                    select.append(options_list)

                    dependencies[input_id] = input
                    dependencies[input_id]['dom'] = select
                    dependencies[input_id]['options'] = choices
                    if (register_onchange) {
                        register_on_change(input.choices, select, can_be_null, onchange);
                    }
                } else {
                    select.append(
                        $(document.createElement('option'))
                        .attr("value", -1)
                        .text(error));
                }
                break;
            case "resource_list":
                var error = "";
                var register_onchange = false;
                //copy the storage object
                var storage = JSON.parse(JSON.stringify(input.storage));
                if ($.isPlainObject(storage)) {
                    if ('REPLACE' in storage) {
                        response = replaceTag(storage, infra_config, user_config, dependencies)
                        storage = response[0]
                        register_onchange = response[1]
                    } else if (!'type' in storage) {
                        error = "storage doesn't have the 'type' tag";
                    } else if (!'config' in storage) {
                        error = "storage doesn't have the 'config' tag";
                    }
                } else {
                    error = "storage is malformed";
                }

                var select = $(document.createElement('select')).attr({
                    id: "input_" + input_id,
                    name: input_id,
                    title: description
                });

                var choices = $(document.createElement('div'));

                inputs_container.append( //datasets resources
                    $(document.createElement('div')).attr({
                        id: "input_container_" + input_id
                    }).append(
                        $(document.createElement('label')).attr({
                            for: "input_" + input_id,
                            title: description
                        }).text(name),
                        select,
                        choices
                    )
                );

                if (error == "") {
                    renderDatasetsData(select, storage);
                    select.on('change',
                        function () {
                            buildDatasetChoicesCall(
                                select,
                                choices,
                                input_id + ":resource");
                        });
                    if (register_onchange) {
                        register_on_change(input.storage, select, can_be_null, onchange);
                    }
                } else {
                    select.append(
                        $(document.createElement('option'))
                        .attr("value", -1)
                        .text(error));
                }
                break;
            case "dataset_list":
                var error = "";
                var register_onchange = false;
                //copy the storage object
                var storage = JSON.parse(JSON.stringify(input.storage));
                if ($.isPlainObject(storage)) {
                    if ('REPLACE' in storage) {
                        response = replaceTag(storage, infra_config, user_config, dependencies)
                        storage = response[0]
                        register_onchange = response[1]
                    } else if (!'type' in storage) {
                        error = "storage doesn't have the 'type' tag";
                    } else if (!'config' in storage) {
                        error = "storage doesn't have the 'config' tag";
                    }
                } else {
                    error = "storage is malformed";
                }

                var select = $(document.createElement('select')).attr({
                    id: "input_" + input_id,
                    name: input_id,
                    title: description
                })

                inputs_container.append( //datasets
                    $(document.createElement('div')).attr({
                        id: "input_container_" + input_id
                    }).append(
                        $(document.createElement('label')).attr({
                            for: "input_" + input_id,
                            title: description
                        }).text(name),
                        select
                    )
                );

                if (error == "") {
                    renderDatasetsData(select, storage);
                    if (register_onchange) {
                        register_on_change(input.storage, dom, can_be_null, onchange);
                    }
                } else {
                    select.append(
                        $(document.createElement('option'))
                        .attr("value", -1)
                        .text(error));
                }
                break;
            case "file":
                var default_value = (('default' in input) ? input.default : '');
                var text = $(document.createElement('div')).attr({
                    id: "text_container_" + input_id,
                    class: "collapsed"
                }).append(
                    $(document.createElement('textarea')).attr({
                        id: "input_" + input_id,
                        name: input_id,
                        placeholder: description,
                        rows: 25,
                        cols: 50
                    }).text(default_value)
                )
                var label = $(document.createElement('label')).attr({
                    for: "input_" + input_id,
                    title: description,
                    class: "toogle"
                }).html(name + ' &darr;').on('click',
                    function (e) {
                        e.preventDefault();
                        this.expand = !this.expand;
                        $(this).html(this.expand ? name + ' &uarr;' : name + ' &darr;');
                        text.toggleClass(
                            'collapsed expanded');
                    })

                inputs_container.append(
                    $(document.createElement('div')).attr({
                        id: "input_container_" + input_id
                    }).append(
                        label,
                        text
                    )
                );
                break;
            case "bool":
                var default_value = (('default' in input) ? input.default : false);

                if (default_value) {
                    true_doc = $(document.createElement('input')).attr({
                        id: "boolean_input_" + input_id + '_true',
                        name: input_id,
                        value: 1,
                        type: 'radio',
                        checked: "checked",
                        title: description
                    });
                    false_doc = $(document.createElement('input')).attr({
                        id: "boolean_input_" + input_id + '_false',
                        name: input_id,
                        value: 0,
                        type: 'radio',
                        title: description
                    });
                } else {
                    true_doc = $(document.createElement('input')).attr({
                        id: "boolean_input_" + input_id + '_true',
                        name: input_id,
                        value: 1,
                        type: 'radio',
                        title: description
                    });
                    false_doc = $(document.createElement('input')).attr({
                        id: "boolean_input_" + input_id + '_false',
                        name: input_id,
                        value: 0,
                        type: 'radio',
                        checked: "checked",
                        title: description
                    });
                }

                inputs_container.append(
                    $(document.createElement('div')).attr({
                        id: "input_container_" + input_id
                    }).append([
                        $(document.createElement('label')).attr({
                            for: "boolean_input_" + input.name,
                            title: input.description
                        }).text(input.name),
                        $(document.createElement('div')).attr({
                            id: "boolean_input_" + input.name
                        }).append(
                            $(document.createElement('label')).attr({
                                for: "boolean_input_" + input.name + '_true',
                                title: input.description
                            }).text("True"),
                            true_doc,
                            $(document.createElement('label')).attr({
                                for: "boolean_input_" + input.name + '_false',
                                title: input.description
                            }).text("False"),
                            false_doc
                        )
                    ])
                );
                break;
            default: //string, int, float
                var default_value = (('default' in input) ? input.default : '');
                inputs_container.append(
                    $(document.createElement('div')).attr({
                        id: "input_container_" + input_id
                    }).append([
                        $(document.createElement('label')).attr({
                            for: type + "_input_" + input_id,
                            title: description
                        }).text(name),
                        $(document.createElement('input')).attr({
                            id: type + "_input_" + input.id,
                            value: default_value,
                            type: 'text',
                            name: input_id,
                            title: description
                        })
                    ])
                );
        }
    });

    for (var key in onchange) {
        if (key in dependencies) {
            dependencies[key].dom.on('change', buildOnChangeCall(key));
        } else {
            // The dependency is not available
            for (let onchange_index = 0; onchange_index < onchange[key].length; onchange_index++) {
                item = onchange[key][onchange_index]
                item.dom.empty().append(
                    $(document.createElement('option'))
                    .attr("value", -1)
                    .text("No data available"));
            }
        }

    }
}

function replaceTag(tag, infra_config, user_config, dependencies) {
    var register_on_change = false
    keys = tag.REPLACE.split(".");
    if (keys[0] == 'INFRA_CONFIG') {
        tag = infra_config
        for (i = 1; i < keys.length; i++) {
            if (keys[i] in tag) {
                tag = tag[keys[i]];
            } else {
                error = "'" + keys[i] + "' not defined in user infrastructures";
                break;
            }
        }
    } else if (keys[0] == 'USER_CONFIG') {
        tag = user_config
        for (i = 1; i < keys.length; i++) {
            if (keys[i] in tag) {
                tag = tag[keys[i]];
            } else {
                error = "'" + keys[i] + "' not defined in user config";
                break;
            }
        }
    } else {
        dependency_id = "." + keys[0];
        register_on_change = true;
        if (dependency_id in dependencies) {
            dependency = dependencies[dependency_id];
            index = dependency.dom.val();
            if (index != -1) {
                tag = dependency.options[index]
                for (i = 1; i < keys.length; i++) {
                    if (keys[i] in tag) {
                        tag = tag[keys[i]];
                    } else {
                        error = "'" + keys[i] + "' not defined";
                        break;
                    }
                }
            } else {
                tag = []
            }
        } else {
            tag = []
        }
        register_onchange = true;
    }
    return [tag, register_on_change]
}

function register_on_change(tag, dom, can_be_null, onchange) {
    keys = tag.REPLACE.split(".");
    dependency_id = "." + keys[0];
    if (dependency_id in onchange) {
        onchange[dependency_id].push({
            'dom': dom,
            'replace_key': tag.REPLACE,
            'can_be_null': can_be_null
        })
    } else {
        onchange[dependency_id] = [{
            'dom': dom,
            'replace_key': tag.REPLACE,
            'can_be_null': can_be_null
        }]
    }
}

function buildDatasetChoicesCall(selector, container, group_name) {
    var selector_obj = selector;
    var container_obj = container;
    var group_name_obj = group_name;

    function onDatasetCall() {
        renderDatasetChoices(
            selector_obj,
            container_obj,
            group_name_obj);
    }

    return onDatasetCall();
}

function buildOnChangeCall(trigger_key) {
    var key = trigger_key

    function onChangeCall() {
        index = $(this).val();
        for (let onchange_index = 0; onchange_index < onchange[key].length; onchange_index++) {
            item = onchange[key][onchange_index]
            // Get choices
            var error = "";
            var choices = []
            if (index != -1) {
                keys = item.replace_key.split(".");
                // Copy the choices object
                choices = JSON.parse(JSON.stringify(dependencies[key].options[index]));
                for (i = 1; i < keys.length; i++) {
                    if (keys[i] in choices) {
                        choices = choices[keys[i]];
                    } else {
                        error = "No user config defined";
                        break;
                    }
                }
            }

            // Render the options
            if (error == "") {
                options_list = []
                if (item.can_be_null) {
                    options_list.push(
                        $(document.createElement('option'))
                        .attr("value", -1)
                        .text("None"))
                }

                for (i = 0; i < choices.length; i++) {
                    opt = $(document.createElement('option'))
                        .attr("value", i)
                        .text(choices[i].name)
                    if ("default" in choices[i] && choices[i].default) {
                        opt.attr("selected", true)
                    }
                    options_list.push(opt)
                }

                item.dom.empty().append(options_list);
            } else {
                item.dom.empty().append(
                    $(document.createElement('option'))
                    .attr("value", -1)
                    .text("No data available"));
            }
        }
    }

    return onChangeCall;
}

function renderDatasetsData(dataset_selector, storage) {
    dataset_selector.empty();
    dataset_selector.append(
        $(document.createElement('option')).attr("value", "-1").text("Loading..")
    );
    $.ajax({
        method: "POST",
        dataType: "json",
        url: '/experimentstool/_get_datasets',
        data: {
            'storage': JSON.stringify(storage)
        },
        beforeSend: function (xhr, settings) {
            $.ajaxSettings.beforeSend(xhr, settings);
            $(".loader").show();
        },
        success: function (data) {
            $(".loader").hide();
            if (data.error !== undefined && data.error !== null) {
                appendNotification("Couldn't get datasets: " + data.error, error = true);
            } else {
                datasets = data.names;
                dataset_selector.empty();
                dataset_selector.append(
                    $(document.createElement('option')).attr("value", "-1").text("None")
                );
                if (datasets.length > 0) {
                    $.each(datasets, function (index, dataset) {
                        dataset_selector.append(
                            $(document.createElement('option')).attr("value", index).text(
                                dataset)
                        )
                    });
                }
            }
        },
        error: function (jqXHR, status, errorThrown) {
            $(".loader").hide();
            message = "Couldn't get datasets list: ";
            message += jqXHR.status + ": " + errorThrown
            appendNotification(message, error = true);
        }
    });
}

function renderDatasetChoices(selector, resources_container, group_name) {
    var dataset = selector.val();
    resources_container.empty();

    if (parseInt(dataset) >= 0) {
        $.ajax({
            url: '/experimentstool/_get_dataset_info',
            type: "POST",
            data: {
                'dataset': dataset
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
                } else if (data.error !== undefined) {
                    appendNotification("Couldn't read the dataset info: " + data.error, error =
                        true);
                } else if (data.num_resources > 0) {
                    $(data.resources).each(function (index, resource) {
                        resources_container.append(
                            $(document.createElement('div')).attr({
                                id: "resource_choice_" + resource.name
                            }).append(
                                $(document.createElement('input')).attr({
                                    id: "resource_" + resource.name,
                                    name: group_name,
                                    value: index,
                                    type: 'radio'
                                }),
                                $(document.createElement('label')).attr({
                                    for: "resource_" + resource.name
                                }).text(resource.name)
                            )
                        )
                    });
                } else {
                    resources_container.append(
                        $(document.createElement('label')).text("No resources found")
                    );
                }
            },
            error: function (jqXHR, status, errorThrown) {
                $(".loader").hide();
                message = "Couldn't read the dataset info: ";
                message += jqXHR.status + ": " + errorThrown
                appendNotification(message, error = true);
            }
        });
    }
}