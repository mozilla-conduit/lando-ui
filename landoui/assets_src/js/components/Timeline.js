'use strict';

$.fn.timeline = function() {
  return this.each(function() {
    let $timeline = $(this);

    // Format timestamps
    $timeline.find('time[data-timestamp]').formatTime();
  });
};

$('button.cancel-landing-job').on('click', function(e) {
    var button = $(this);
    var landing_job_id = this.dataset.landing_job_id;

    button.addClass("is-loading");
    fetch(`/landing_jobs/${landing_job_id}`, {
        method: 'PUT',
        body: JSON.stringify({"status": "CANCELLED"}),
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        },
    }).then(response => {
        if (response.status == 200) {
            window.location.reload();
        } else if (response.status == 400) {
            button.prop("disabled", true);
            button.removeClass("is-danger").removeClass("is-loading").addClass("is-warning");
            button.html("Could not cancel landing request");
        } else {
            button.prop("disabled", true);
            button.removeClass("is-danger").removeClass("is-loading").addClass("is-warning");
            button.html("An unknown error occurred");
        }
    });
});
