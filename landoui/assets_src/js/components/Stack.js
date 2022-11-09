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

var revisionId = $("main")[0].dataset.revision;
var rawHashData = $("main")[0].dataset.hashes;
var hashes = {};
if (rawHashData) {
    hashes = JSON.parse(rawHashData);
}
var new_hashes = {};
var stopCheck = false;

console.log(hashes);

function checkHashes() {
    // Get stack hashes, compare them with stored hashes.
    console.log(stopCheck);
    if (!stopCheck) {
        new_hashes = fetch("/stack_hashes/" + revisionId)
            .then(response => response.json())
            .then(new_hashes => {
                if (new_hashes.timestamps != hashes.timestamps) {
                    hashes = new_hashes;
                    console.log(new_hashes);
                    // $(".StackPage-preview-button").attr("disabled", true);
                    $(".refresh-button").show();
                    stopCheck = true;
                }
            });
    }
}


var sleep = duration => new Promise(resolve => setTimeout(resolve, duration));
var poll = (promiseFn, duration) => promiseFn().then(
                 sleep(duration).then(() => poll(promiseFn, duration)));
poll(() => new Promise(() => checkHashes()), 10000);
$("button.refresh-button").on("click", function(e) {
    window.location.reload();
});
