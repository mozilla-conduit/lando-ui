'use strict';

$.fn.landingPreview = function() {
  return this.each(function() {
    let $landingPreview = $(this);
    let $close = $landingPreview.find('.StackPage-landingPreview-close');
    let $warnings = $landingPreview.find('.StackPage-landingPreview-warnings input[type=checkbox]');
    let $blocker = $landingPreview.find('.StackPage-landingPreview-blocker');
    let $landButton = $landingPreview.find('.StackPage-landingPreview-land');

    // Reach outside my component, because I'm a pragmatist.
    let $previewButton = $('.StackPage-preview-button');

    let calculateButtonState = () => {
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
    $previewButton.on('click', (e) => {
      e.preventDefault();
      calculateButtonState();
      $landingPreview.show();
    });
    $close.on('click', (e) => {
      e.preventDefault();
      $landingPreview.hide();
    });
    $warnings.on('change', () => {
      calculateButtonState();
    });
  });
};
