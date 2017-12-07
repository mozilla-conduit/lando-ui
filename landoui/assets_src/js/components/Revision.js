'use strict';

$.fn.revision = function() {
  return this.each(function() {
    let $revision = $(this);
    // Format timestamps
    $revision.find('time[data-timestamp]').formatTime();

    // Show/hide of full commit message based on button click
    $revision.find('.show-full-message').on('click', function() {
      $revision.find('.RevisionPage-commit-full').slideToggle();
    });

    $revision.find('.RevisionPage-actions button:enabled').on('click', function(){
      let $btn = $(this);
      $btn.attr({'disabled': true, 'inprogress': true});
      $btn.find('.RevisionPage-actions-headline').html('Landing Queuing...');
      $btn.find('.RevisionPage-actions-subtitle').html('Please wait');
    });
  });
};
