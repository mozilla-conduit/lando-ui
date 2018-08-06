'use strict';

$.fn.landingPreview = function() {
  return this.each(function() {
    let $landingPreview = $(this);
    let $close = $landingPreview.find('.StackPage-landingPreview-close');
    // Reach outside my component, because I'm a pragmatist.
    let $previewButton = $('.StackPage-preview-button');

    $previewButton.on('click', (e) => {
      e.preventDefault();
      $landingPreview.show();
    });
    $close.on('click', (e) => {
      e.preventDefault();
      $landingPreview.hide();
    });
  });
};
