'use strict';

$.fn.revision = function() {
  return this.each(function() {
    let $revision = $(this);
    let $landButton = $revision.find('.RevisionPage-actions button');

    // Format timestamps
    $revision.find('time[data-timestamp]').formatTime();

    // Show/hide of full commit message based on button click
    $revision.find('.show-full-message').on('click', function() {
      $revision.find('.RevisionPage-commit-full').slideToggle();
    });

    // Disable landing button upon click
    $landButton.on('click', function() {
      if($landButton.attr('disabled')) {
        return;
      }

      $landButton.attr({'disabled': true, 'inprogress': true});
      $landButton.find('.RevisionPage-actions-headline').html('Landing Queuing...');
      $landButton.find('.RevisionPage-actions-subtitle').html('Please wait');
    });

    // Enable and disable buttons depending on if all warning checkboxes (if any)
    // are checked or not
    let $warnings = $revision.find('.RevisionPage-warnings input[type=checkbox]');
    $warnings.on('change', function() {
      let checked = $warnings.filter(function() {
        return this.checked;
      });
      
      if(checked.length !== $warnings.length) {
        $landButton.attr('disabled', true);
      }
      else {
        $landButton.removeAttr('disabled');
      }
    });

  });
};
