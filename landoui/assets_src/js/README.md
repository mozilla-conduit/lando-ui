# Lando UI JS Structure

Lando UI doesn't use any complicated javascript library for the frontend besides
jQuery. The idea was that our application is very simple, and javascript's main
purpose is to respond to user input.

The app has been designed to work somewhat like Backbone, without actually
using backbone - the idea is that every Page (i.e. route on the server), and
every Component (e.g. the navbar or a reusable widget) has a javascript class
(in the form of a jQuery plugin).

At the end of every Page or Component there is a snippet of js code which
initializes the jQuery plugin for that component if it is present. You can also
choose to not initialize a component this way and instead have a parent Component
or Page initialize the child component in their javascript class.

To pass state or any other data from the server to the browser, use a HTML
data-attribute like `data-state` on the DOM element of the component. In Flask
you can accomplish this with something like:
```html
<div class="MyWidget" data-state='{{ widgetStateDict | tojson }}'>
  ...
</div>
```
and in the JS class load the state with `$widget.data('state');` jQuery will
automatically convert the JSON text into a proper JS object for use. NOTICE: you
must use single quotes instead of double quotes for the data-attribute.

You will not be able to create inline script tags to store data, due to our CSP
policy, so data-attributes are the way to go.

### Example Class for the widget above

```javascript
$.fn.landoWidget = function(){
  return this.each(function(){
    let $widget = $(this);
    let state = $widget.data('state');

    $widget.... //bind events and whatever else
  });
};
```


# Browser Compatibility

Lando UI doesn't transpile es6 javascript into es5 and so it depends on the
browser's native ability to execute that code. Mainly from the es6 spec we depend
on: classes, the let & const operators, arrow functions, and template literals.

Any recent version of Firefox, Chrome, Edge, Android Browser, Opera, and Safari
will work fine. Notable browsers that won't work: IE11, iOS9 browser.


# Dependencies

Lando UI doesn't have any dependency resolver built it, so there's no way to
'require' a js file in another one. You will have to rely on that js file being
loaded before the one that depends on it.

Our load order is manually defined in the `assets_src/assets.yml` file. For the
most part Lando UI is simple enough that there won't be many dependencies, but,
if there are you must manually specify the js files that come first in the
`assets.yml` file mentioned.
