'use strict';

$.fn.timeline = function() {
  return this.each(function() {
    let $timeline = $(this);

    // Format timestamps
    $timeline.find('time[data-timestamp]').formatTime();
  });
};
