$(document).ready(function () {
    $("#marketplace").on('load', function () {
        /*
        //$(this).height($(this).contents().find("body").height());
        var valueSize = $(this).offset();
        console.log("offset: " + $(this).offset());
        var totalsize = (valueSize.top * 2) + valueSize.left;
        //style="min-height: 400px"
        $(this).height(totalsize);
        */
        //$(this).css('height', $(this).contents().find('body').height() + 'px')
        //$(this).height($(this).contents().find("body").height());
        //console.log("height: " + $(this).contents().find("body").height());
    });

    $("#dataset_selector").find("select").on('change', function () {
        var dataset = $(this).val();
        var resources_list = $(".dynamic_list");
        resources_list.empty();

        if (dataset != "none") {
            $.ajax({
                url: '/experimentstool/dataset_info',
                data: {
                    'dataset': dataset
                },
                dataType: 'json',
                success: function (data) {
                    if (data.num_resources > 0) {
                        $(data.resources).each(function (index, resource) {
                            resources_list.append(
                                $(document.createElement('div')).attr({
                                    id: "resource_selector_" + resource.name
                                }).append(
                                    $(document.createElement('input')).attr({
                                        id: "resource_" + resource.name,
                                        name: resource.name,
                                        value: resource.name,
                                        type: 'checkbox'
                                    }),
                                    $(document.createElement('label')).attr({
                                        for: "resource_" + resource.name
                                    }).text(resource.name)
                                )
                            )
                        });
                    } else {
                        resources_list.append(
                            $(document.createElement('label')).text("No resources found")
                        );
                    }
                }
            });
        }
    });
});