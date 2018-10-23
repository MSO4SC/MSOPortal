function renderDatasetChoices(selector_id, container_id, group_name) {
    var dataset = $(selector_id).find("select").val();
    var resources_container = $(container_id);
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

function renderApplicationData(selector_id, only_owned = false) {
    var application_selector = $(selector_id).find("select")
    application_selector.empty();
    application_selector.append(
        $(document.createElement('option')).attr("value", "-1").text("Loading..")
    );

    var url = '/experimentstool/_load_applications';
    if (only_owned) {
        url = '/experimentstool/_load_owned_applications';
    }

    $.ajax({
        url: url,
        beforeSend: function (xhr, settings) {
            $.ajaxSettings.beforeSend(xhr, settings);
            $(".loader").show();
        },
        success: function (data) {
            $(".loader").hide();
            application_selector.empty();
            if (data.redirect !== undefined && data.redirect !== null) {
                redirect(data.redirect);
            } else if (data.error !== undefined && data.error !== null) {
                appendNotification("Couldn't read applications: " + data.error, error = true);
                application_selector.append(
                    $(document.createElement('option')).attr("value", "-1").text("Error")
                );
            } else if (data.app_list.length > 0) {
                application_selector.append(
                    $(document.createElement('option')).attr("value", "-1").text("None")
                );
                $.each(data.app_list, function (index, application) {
                    application_selector.append(
                        $(document.createElement('option')).attr("value", application.id)
                        .text(application.name)
                    )
                });
            } else {
                var msg = "No applications found";
                if (only_owned) {
                    msg = "No owned applications found";
                }
                application_selector.append(
                    $(document.createElement('option')).attr("value", "-1")
                    .text(msg)
                );
            }
        },
        error: function (jqXHR, status, errorThrown) {
            $(".loader").hide();
            message = "Couldn't get applications list: ";
            message += jqXHR.status + ": " + errorThrown
            appendNotification(message, error = true);
        }
    });
}

function renderApplicationInputs(selector_id, container_id) {
    var application = $(selector_id).find("select").val();
    var inputs_container = $(container_id);
    inputs_container.empty();

    var computing_pattern = new RegExp("^mso4sc_wm_(.)*$");
    var dataset_pattern = new RegExp("^mso4sc_dataset_(.)*$");
    var outputdataset_pattern = new RegExp('^mso4sc_outdataset_(.)*$')
    var datacatalogue_pattern = new RegExp('^mso4sc_datacatalogue_(.)*$')
    var file_pattern = new RegExp('^mso4sc_file_(.)*$')

    if (parseInt(application) >= 0) {
        $.ajax({
            url: '/experimentstool/_get_application_inputs',
            data: {
                'application_id': application
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
                    appendNotification("Couldn't read the inputs: " + data.error, error = true);
                } else if (data.inputs.length > 0) {
                    data.inputs.sort(function (a, b) {
                        var nameA = a.name.toLowerCase(),
                            nameB = b.name.toLowerCase();
                        if (nameA < nameB) //sort string ascending
                            return -1;
                        if (nameA > nameB)
                            return 1;
                        return 0; //default return value (no sorting)
                    });
                    //First render HPCs inputs
                    $(data.inputs).each(function (index, input) {
                        if (computing_pattern.test(input.name)) {
                            inputs_container.append( //computings
                                $(document.createElement('div')).attr({
                                    id: "input_container_" + input.name
                                }).append(
                                    $(document.createElement('label')).attr({
                                        for: "input_" + input.name,
                                        title: input.description
                                    }).text('HPC: ' + input.name.slice(11)),
                                    $(document.createElement('select')).attr({
                                        id: "input_" + input.name,
                                        name: input.name,
                                        title: input.description
                                    }).append(
                                        $(document.createElement('option'))
                                        .attr("value", -1)
                                        .text("None")
                                    )
                                )
                            );
                            renderComputingData("#input_container_" + input.name);
                        } else if (dataset_pattern.test(input.name)) {
                            inputs_container.append( //datasets
                                $(document.createElement('div')).attr({
                                    id: "input_container_" + input.name
                                }).append(
                                    $(document.createElement('label')).attr({
                                        for: "input_" + input.name,
                                        title: input.description
                                    }).text('Dataset resource: ' + input.name.slice(15)),
                                    $(document.createElement('select')).attr({
                                        id: "input_" + input.name,
                                        name: input.name,
                                        title: input.description
                                    }).append(
                                        $(document.createElement('option')).attr("value", -
                                            1).text("None")
                                    ),
                                    $(document.createElement('div')).attr({
                                        id: "choices_" + input.name
                                    })
                                )
                            );
                            renderDatasetsData("#input_container_" + input.name);
                            $("#input_container_" + input.name).find("select").on('change',
                                function () {
                                    renderDatasetChoices("#input_container_" + input.name,
                                        "#choices_" + input.name,
                                        "resource_" + input.name);
                                });
                        } else if (outputdataset_pattern.test(input.name)) {
                            inputs_container.append( //datasets
                                $(document.createElement('div')).attr({
                                    id: "input_container_" + input.name
                                }).append(
                                    $(document.createElement('label')).attr({
                                        for: "input_" + input.name,
                                        title: input.description
                                    }).text('Output dataset: ' + input.name.slice(18)),
                                    $(document.createElement('select')).attr({
                                        id: "input_" + input.name,
                                        name: input.name,
                                        title: input.description
                                    }).append(
                                        $(document.createElement('option')).attr("value", -
                                            1).text("None")
                                    )
                                )
                            );
                            renderDatasetsData("#input_container_" + input.name);
                        } else if (file_pattern.test(input.name)) {
                            inputs_container.append( //files
                                $(document.createElement('div')).attr({
                                    id: "input_container_" + input.name
                                }).append(
                                    $(document.createElement('label')).attr({
                                        for: "input_" + input.name,
                                        title: input.description,
                                        class: "toogle"
                                    }).html('File: ' + input.name.slice(12) + ' &darr;'),
                                    $(document.createElement('div')).attr({
                                        id: "text_container_" + input.name,
                                        class: "collapsed"
                                    }).append(
                                        $(document.createElement('textarea')).attr({
                                            id: "input_" + input.name,
                                            name: input.name,
                                            placeholder: input.description,
                                            rows: 25,
                                            cols: 50
                                        }).text(input.default)
                                    )
                                )
                            );
                            $("#input_container_" + input.name).find('.toogle').on('click',
                                function (e) {
                                    e.preventDefault();
                                    this.expand = !this.expand;
                                    $(this).html(this.expand ? 'File: ' + input.name.slice(
                                        12) + ' &uarr;' : 'File: ' + input.name.slice(
                                        12) + ' &darr;');
                                    $(this).closest("#input_container_" + input.name).find(
                                        '.collapsed, .expanded').toggleClass(
                                        'collapsed expanded');
                                });
                        } else if (datacatalogue_pattern.test(input.name)) {
                            inputs_container.append( //datasets
                                $(document.createElement('div')).attr({
                                    id: "input_container_" + input.name
                                }).append(
                                    $(document.createElement('input')).attr({
                                        id: "input_" + input.name,
                                        value: "",
                                        type: 'hidden',
                                        name: input.name,
                                        title: input.description
                                    })
                                )
                            );
                        } else {
                            inputs_container.append( //other
                                $(document.createElement('div')).attr({
                                    id: "input_container_" + input.name
                                }).append(
                                    inputToForm(input)
                                )
                            );
                        }
                    });
                } else {
                    inputs_container.append(
                        $(document.createElement('label')).text("No inputs found")
                    );
                }
            },
            error: function (jqXHR, status, errorThrown) {
                $(".loader").hide();
                message = "Couldn't read the inputs: ";
                message += jqXHR.status + ": " + errorThrown
                appendNotification(message, error = true);
            }
        });
    }
}

function inputToForm(input) {
    if (input.type === "string") {
        return [
            $(document.createElement('label')).attr({
                for: "input_" + input.name,
                title: input.description
            }).text(input.name),
            $(document.createElement('input')).attr({
                id: "input_" + input.name,
                value: input.default,
                type: 'text',
                name: input.name,
                title: input.description
            })
        ]
    } else if (input.type === "integer") {
        return [
            $(document.createElement('label')).attr({
                for: "integer_input_" + input.name,
                title: input.description
            }).text(input.name),
            $(document.createElement('input')).attr({
                id: "integer_input_" + input.name,
                value: input.default,
                type: 'text',
                name: input.name,
                title: input.description
            })
        ]
    } else if (input.type === "boolean") {
        if (input.default) {
            true_doc = $(document.createElement('input')).attr({
                id: "boolean_input_" + input.name + '_true',
                name: input.name,
                value: 1,
                type: 'radio',
                checked: "checked",
                title: input.description
            });
            false_doc = $(document.createElement('input')).attr({
                id: "boolean_input_" + input.name + '_false',
                name: input.name,
                value: 0,
                type: 'radio',
                title: input.description
            });
        } else {
            true_doc = $(document.createElement('input')).attr({
                id: "boolean_input_" + input.name + '_true',
                name: input.name,
                value: 1,
                type: 'radio',
                title: input.description
            });
            false_doc = $(document.createElement('input')).attr({
                id: "boolean_input_" + input.name + '_false',
                name: input.name,
                value: 0,
                type: 'radio',
                checked: "checked",
                title: input.description
            });
        }
        return [
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
        ]
    } else if (jQuery.type(input.default) == "array") {
        return [
            $(document.createElement('label')).attr({
                for: "array_input_" + input.name,
                title: input.description
            }).text(input.name),
            $(document.createElement('input')).attr({
                id: "array_input_" + input.name,
                value: input.default,
                type: 'text',
                name: input.name,
                title: input.description
            })
        ]
    } else if (jQuery.type(input.default) == "object") {
        return [
            $(document.createElement('label')).attr({
                for: "dict_input_" + input.name,
                title: input.description
            }).text(input.name),
            $(document.createElement('input')).attr({
                id: "dict_input_" + input.name,
                value: JSON.stringify(input.default),
                type: 'text',
                name: input.name,
                title: input.description
            })
        ]
    } else {
        return [
            $(document.createElement('label')).attr({
                for: "input_" + input.name,
                title: input.description
            }).text(input.name),
            $(document.createElement('input')).attr({
                id: "input_" + input.name,
                value: input.default,
                type: 'text',
                name: input.name,
                title: input.description
            })
        ]
    }
}



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
                    _renderInputsData(container_id, data.inputs)
                }
            },
            error: function (jqXHR, status, errorThrown) {
                $(".loader").hide();
                message = "Couldn't read the " + type + " inputs: ";
                message += jqXHR.status + ": " + errorThrown
                appendNotification(message, error = true);
            }
        });
    }
}

function _renderInputsData(container_id, inputs) {
    var inputs_container = $(container_id);
    inputs_container.empty();

    $(inputs).each(function (index, tuple) {
        var input_id = tuple[0]
        var input = tuple[1]
        var name = input.name;
        var description = (('description' in input) ? input.description : '');
        var type = input.type;
        var advanced = (('advanced' in input) ? input.advanced : false);
        var can_be_null = (('null' in input) ? input.null : false);

        //TODO: REPLACE

        switch (type) {
            case "list":
                break;
            case "resource_list":
                inputs_container.append( //datasets resources
                    $(document.createElement('div')).attr({
                        id: "input_container_" + input_id
                    }).append(
                        $(document.createElement('label')).attr({
                            for: "resource_list_" + input_id,
                            title: description
                        }).text(name),
                        $(document.createElement('select')).attr({
                            id: "resource_list_" + input_id,
                            name: input_id,
                            title: description
                        }).append(
                            $(document.createElement('option')).attr("value", -
                                1).text("None")
                        ),
                        $(document.createElement('div')).attr({
                            id: "choices_" + input.name
                        })
                    )
                );
                renderDatasetsData("#input_container_" + input_id);
                $("#input_container_" + input_id).find("select").on('change',
                    function () {
                        renderDatasetChoices("#input_container_" + input_id,
                            "#choices_" + input_id,
                            "resource_" + input_id);
                    });
                break;
            case "dataset_list":
                inputs_container.append( //datasets
                    $(document.createElement('div')).attr({
                        id: "input_container_" + input_id
                    }).append(
                        $(document.createElement('label')).attr({
                            for: "input_" + input_id,
                            title: description
                        }).text(name),
                        $(document.createElement('select')).attr({
                            id: "input_" + input_id,
                            name: input_id,
                            title: description
                        }).append(
                            $(document.createElement('option')).attr("value", -1)
                            .text("None")
                        )
                    )
                );
                renderDatasetsData("#input_container_" + input_id);
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
                            id: type + "_input_" + input.name,
                            value: default_value,
                            type: 'text',
                            name: input_id,
                            title: description
                        })
                    ])
                );
        }
    });
}

function renderDatasetsData(selector_id) {
    var dataset_selector = $(selector_id).find("select")
    dataset_selector.empty();
    dataset_selector.append(
        $(document.createElement('option')).attr("value", "-1").text("Loading..")
    );
    $.ajax({
        url: '/experimentstool/_get_datasets',
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