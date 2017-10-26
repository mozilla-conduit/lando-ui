'use strict';

$.fn.revision = function() {
  return this.each(function() {
    var $revision = $(this);
    // Format timestamps
    $revision.find('time[data-timestamp]').formatTime();

    // Show/hide of full commit message based on button click
    $revision.find('.show-full-message').on('click', function() {
      $revision.find('.RevisionPage-commit-full').slideToggle();
    });
  });
};
