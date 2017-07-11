'use strict';

$.fn.landoRevisionPage = function() {
  return this.each(function() {
    let $page = $(this);
    let state = $page.data('state');
    $page.find('.RevisionPage-collapseLink').landoRevisionPageCollapsible();
  });
};

$.fn.landoRevisionPageCollapsible = function() {
  const iconClassSelectors = '.fa-chevron-circle-right, .fa-chevron-circle-down';
  const iconClassToggle = 'fa-chevron-circle-right, fa-chevron-circle-down';

  return this.each(function() {
    let $revision = $(this).closest('.RevisionPage-parentRevision').first();

    $(this).on('click', function() {
      $revision.find(iconClassSelectors).toggleClass(iconClassToggle);
      $revision.find('.RevisionPage-parentRevisionBody').toggle(200);
    });
  });
};
