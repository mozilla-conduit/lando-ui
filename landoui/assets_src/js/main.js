'use strict';

$(document).ready(function() {
  let $revision = $('.RevisionPage-revision');
  let $timeline = $('.StackPage-timeline');
  let $landingPreview = $('.StackPage-landingPreview');

  // Initialize components
  $('.Navbar').landoNavbar();
  $revision.revision();
  $timeline.timeline();
  $landingPreview.landingPreview();

  // Update the URL to include diff id, if it doesn't already
  if($revision.length) {
      let revisionId = $revision.data('revision-id');
      let diffId = $revision.data('diff-id');
      let completePath = `/revisions/${revisionId}/${diffId}/`;
      if(window.location.pathname != completePath) {
        history.replaceState({}, `${revisionId}: ${diffId}`, completePath);
      }
  }
});
