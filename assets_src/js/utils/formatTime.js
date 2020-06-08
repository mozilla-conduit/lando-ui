'use strict';

$.fn.formatTime = function() {
  return this.each(function() {
    let time = $(this).data('timestamp');
    let date = new Date(time);

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
