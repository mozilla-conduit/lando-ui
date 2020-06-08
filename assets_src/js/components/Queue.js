'use strict';

$.fn.queue = function() {
  return this.each(function() {
    let $queue = $(this);
    let $revisions = $queue.find('.QueuePage-revision');
    
    // Click into revision page
    $revisions.on('click', (e) => {
      window.location = $(e.currentTarget).data('revision-tip-url');
    });

    // Show all or just my revisions
    $queue.find('.QueuePage-optionsIsMine a').on('click', (e) => {
      e.preventDefault();
      if($(e.target).data('show') == 'just-mine') {
        $('[data-is-mine="false"]').hide();
      } else {
        $revisions.show();
      }
    });

    // Repository toggle
    $queue.find('.QueuePage-optionsRepo').on('click', (e) => {
      // to be implemented
    });
  });
};
