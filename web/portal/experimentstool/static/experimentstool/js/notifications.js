function cleanNotifications() {
    $("#experiments_notification_container").empty();
}

function appendNotification(message, error = false) {
    var _title = "Success"
    var _class = "dialog_success";
    if (error) {
        _title = "Error"
        _class = "dialog_failure";
    }

    message_box = $(document.createElement('div')).text(message)

    $("#experiments_notification_container").append(message_box)

    message_box.dialog({
        title: _title,
        dialogClass: _class,
        position: {
            my: "center",
            at: "center"
        },
        clickOutside: true
    })
}