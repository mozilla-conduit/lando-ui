'use strict';

var newRepoNoticeForm = $("#newRepoNoticeForm");

newRepoNoticeForm.on("submit", function(e) {
    e.preventDefault();
    var form = e.target;
    var data = new FormData(e.target);

    Array.from(form.elements).forEach(element => {
        element.classList.remove("is-danger");
    });
    data = Object.fromEntries(data.entries());
    fetch("/repos/notices/", {
        method: 'POST',
        body: JSON.stringify(data),
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        },
    }).then(response => {
        if (response.status == 400) {
            window.test = form;
            return response.json();
        } else if (response.status == 201) {
            form.reset();
            window.location.reload();
        } else {
            alert(`An unknown error has occurred with status code ${response.status}`);
        }
    }).then(data => {
        for (const field in data) {
            var element = form.elements.namedItem(field);
            var helpText = element.parentElement.parentElement.getElementsByClassName("help")[0]

            element.classList.add("is-danger");
            helpText.classList.remove("is-info");
            helpText.classList.add("is-danger");
            helpText.innerHTML = data[field][0];
        }
    });
});

$(".archive-notice").on("click", function(e) {
    e.preventDefault();
    var noticeID = e.target.dataset.noticeid;
    fetch(`/repos/notices/${noticeID}`, {
        method: 'DELETE',
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        },
    }).then(response => {
        if (response.status == 200) {
            window.location.reload();
        } else {
            alert(`An unknown error has occurred with status code ${response.status}`);
        }
    })
});
