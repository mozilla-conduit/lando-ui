'use strict';

$.fn.revision = function() {
  return this.each(function() {
    let $revision = $(this);
    let $landButton = $revision.find('.RevisionPage-land-button');
    let $landInfo = $revision.find('.RevisionPage-landing-info');
    let $blockers = $revision.find('.RevisionPage-blockers');
    let $warnings = $revision.find('.RevisionPage-warnings input[type=checkbox]');

    let setLandButtonState = (title, subtitle, disabled, inprogress) => {
      $landButton.attr({'disabled': disabled});
      if(inprogress) $landButton.attr({'inprogress': true});
      if(title) $landButton.find('.RevisionPage-actions-headline').text(title);
      if(subtitle) $landButton.find('.RevisionPage-actions-subtitle').text(subtitle);
    };

    let landingTransition = (e) => {
      e.preventDefault();
      $landButton.unbind('click', landingTransition);

      // Show warnings and blockers and disable button until animation finishes.
      setLandButtonState(null, null, true, false);
      $landInfo.show(400, transitionFinish);
    };

    let transitionFinish = () => {
      let initialTitle = $landButton.find('.RevisionPage-actions-headline').text();

      // Update land button state
      if($blockers.length) {
        setLandButtonState('Landing is blocked', ' ', true, false);
      }
      else if ($warnings.length) {
        setLandButtonState(initialTitle, 'Check off each warning to land', true, false);
      }
      else {
        setLandButtonState('Confirm', 'Ready to Land', false, false);
      }

      // Enable and disable buttons depending on if all warning checkboxes
      // (if any) are checked or not.
      $warnings.on('change', () => {
        let checked = $warnings.filter(function() {
          return this.checked;
        });

        if(checked.length !== $warnings.length) {
          setLandButtonState(initialTitle, 'Check off each warning to land', true, false);
        }
        else {
          setLandButtonState('Confirm', 'Ready to Land', false, false);
        }
      });

      // Disable landing button and submit form upon click
      $landButton.on('click', function(e) {
        e.preventDefault();
        if($landButton.attr('disabled')) {
          return;
        }
        setLandButtonState('Landing Queuing...', 'Please wait', true, true);
        $revision.find(".RevisionPage-form").submit();
      });
    };

    let enhanceCommitMessage = () => {
      const lineHeight = 1.25;
      let $toggleButton = $revision.find('.RevisionPage-commit-expand');
      let $commitMessage = $revision.find('.RevisionPage-commit-message');
      let $seeMore = $revision.find('.RevisionPage-commit-see-more');
      let lines = $commitMessage.text().split(/\r\n|\r|\n/).length;

      // Show the toggle button and more indicator only if the commit message is long.
      if(lines > 8){
        $toggleButton.text('Show all ' + lines + ' lines');
        $toggleButton.css('display', 'inline-block');
        $seeMore.text('... (' + (lines - 8) + ' more lines)');
        $seeMore.css('display', 'block');
      }
      else {
        return;
      }

      // Show/hide of full commit message based on button click
      $toggleButton.on('click', (e) => {
        e.preventDefault();

        if($commitMessage.data('expanded')) {
          $commitMessage.css('max-height', `${lineHeight * 8.5}em`);
          $commitMessage.data('expanded', false);
          $toggleButton.text('Show all ' + lines + ' lines');
          $seeMore.css('display', 'block');
        }
        else {
          $commitMessage.css('max-height', '100000em');
          $commitMessage.data('expanded', true);
          $toggleButton.text('Hide lines');
          $seeMore.css('display', 'none');
        }
      });
    };

    enhanceCommitMessage();

    // Format timestamps
    $revision.find('time[data-timestamp]').formatTime();

    // Transition to attempt a landing on initial click
    $landButton.bind('click', landingTransition);
  });
};
