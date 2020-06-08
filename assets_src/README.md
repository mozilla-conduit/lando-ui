# Lando UI Asset Pipeline

Lando UI uses Flask's default of serving any file in the /static folder as a
static asset. To improve on this Flask Assets is added to the project to allow
us to compile and minify our source SCSS and javascript files.

As stated, any file in the static folder will be served. When Flask Assets
compiles our sources, it emits a folder called `build` which contains
the combined js and css files.

See the `assets.yml` file for an example of how this works. Also checkout
[The Web Assets Docs](https://webassets.readthedocs.io/en/latest/) for
details on how to configure it.

See the js and css folders for more detailed README's about the two.

# Development

When running the development server, you can freely edit the scss and js files
and it will just work the next time you reload the page. The only time you need
to restart the server is if you change the `assets.yml` file.

# Production

The production docker container will serve all static assets in the `static`
folder. In the circle build the dev container is used to build the static assets
and then the production container simply copies them in.

You can manually compile the static assets by running:
`docker-compose run -e FLASK_APP=/app/landoui/assets_app.py lando-ui flask assets build`.
This will spit the files out into the `static/build` folder.
