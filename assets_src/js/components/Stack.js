'use strict';

$.fn.stack = function() {
  return this.each(function() {
    let $stack = $(this);
    let $radio = $stack.find('.StackPage-revision-land-radio');

    $radio.on('click', (e) => {
      window.location.href = '/' + e.target.id;
      $radio.attr({'disabled': true});
    });
  });
};
