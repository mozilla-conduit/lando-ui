'use strict';

$.fn.formatTime = function() {
  return this.each(function() {
    var time = $(this).data('timestamp');
    var date = new Date(0);
    date.setUTCSeconds(time);

    $(this).text(date.toLocaleString(navigator.language, {
      weekday: 'short',
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      timeZoneName: 'short',
      hour: 'numeric',
      minute: 'numeric'
    }));
  });
};
