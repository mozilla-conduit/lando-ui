'use strict';

$.fn.landingPreview = function() {
  return this.each(function() {
    let $landingPreview = $(this);
    let $close = $landingPreview.find('.StackPage-landingPreview-close');
    let $warnings = $landingPreview.find('.StackPage-landingPreview-warnings input[type=checkbox]');
    let $blocker = $landingPreview.find('.StackPage-landingPreview-blocker');
    let $landButton = $landingPreview.find('.StackPage-landingPreview-land');
    let $revisions = $landingPreview.find('.StackPage-landingPreview-revision');
    let $expandAllButton = $landingPreview.find('.StackPage-landingPreview-expandAll');
    let $collapseAllButton = $landingPreview.find('.StackPage-landingPreview-collapseAll');

    // Reach outside my component, because I'm a pragmatist.
    let $previewButton = $('.StackPage-preview-button');

    let calculateLandButtonState = () => {
      if($blocker.length > 0) {
        $landButton.attr({'disabled': true});
        $landButton.text('Landing is blocked');
        return;
      }

      let checked = $warnings.filter(function() {
        return this.checked;
      });
      if(checked.length !== $warnings.length) {
        $landButton.attr({'disabled': true});
        $landButton.text('Acknowledge warnings to land');
      } else {
        $landButton.attr({'disabled': false});
        $landButton.text('Land to ' + $landButton.data('target-repo'));
      }
    };


    $landButton.on('click', () => {
      $landButton.attr({'disabled': true});
      $landButton.text('Landing in progress...');
    });

    let expandCommitMessage = ($commitMessage, $seeMore, $toggleButton, lines) => {
      $commitMessage.css('max-height', 'none');
      $commitMessage.data('expanded', true);
      $toggleButton.text('Hide lines');
      $seeMore.css('display', 'none');
    };

    let collapseCommitMessage = ($commitMessage, $seeMore, $toggleButton, lines) => {
      $commitMessage.css('max-height', '');
      $commitMessage.data('expanded', false);
      $toggleButton.text('Show all ' + lines + ' lines');
      $seeMore.css('display', 'block');
    };

    let toggleCommitMessage = ($commitMessage, $seeMore, $toggleButton, lines) => {
      if($commitMessage.data('expanded')) {
        collapseCommitMessage($commitMessage, $seeMore, $toggleButton, lines);
      } else {
        expandCommitMessage($commitMessage, $seeMore, $toggleButton, lines);
      }
    };

    let longMessages = 0;

    $revisions.each(function () {
      let $revision = $(this);
      let $toggleButton = $revision.find('.StackPage-landingPreview-expand');
      let $commitMessage = $revision.find('.StackPage-landingPreview-commitMessage');
      let $seeMore = $revision.find('.StackPage-landingPreview-seeMore');
      let lines = $commitMessage.text().split(/\r\n|\r|\n/).length;

      if (lines <= 5){
        $toggleButton.hide();
        return;
      }

      longMessages++;

      // Sets up the display of how many lines are hidden:
      // expandCommitMessage and collapseCommitMessage merely toggle this when clicked.
      $toggleButton.text('Show all ' + lines + ' lines');
      $seeMore.text('... (' + (lines - 5) + ' more lines)');

      $toggleButton.on('click', (e) => {
        e.preventDefault();
        toggleCommitMessage($commitMessage, $seeMore, $toggleButton, lines);
      });

      $expandAllButton.on('click', (e) => {
        e.preventDefault();
        expandCommitMessage($commitMessage, $seeMore, $toggleButton, lines);
      });

      $collapseAllButton.on('click', (e) => {
        e.preventDefault();
        collapseCommitMessage($commitMessage, $seeMore, $toggleButton, lines)
      });
    });

    if ($revisions.length === 1 || longMessages === 0) {
      $expandAllButton.css('display', 'none');
      $collapseAllButton.css('display', 'none');
    }


    $previewButton.on('click', (e) => {
      e.preventDefault();
      calculateLandButtonState();
      $landingPreview.show();
    });
    $close.on('click', (e) => {
      e.preventDefault();
      $landingPreview.hide();
    });
    $warnings.on('change', () => {
      calculateLandButtonState();
    });
  });
};
