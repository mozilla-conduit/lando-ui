# How to setup Lando UI/API and Transplant

## Prerequisites

- Python 3.5, docker-compose, pyinvoke.

- Clone repo of:
    - https://github.com/mozilla-conduit/lando-ui
    - https://github.com/mozilla-conduit/lando-api
    - https://github.com/mozilla-conduit/conduit-autoland-demo

- You're able to run lando-ui and lando-api separately already. If not, get
that working first.

- A Phabricator API key on the Phabricator instance you want to use. This guide
assumes you are using https://phabricator-dev.allizom.org which works fine
for localdev. (Using the demo phab is harder and not covered).

- An Auth0 developer account. See the lando-ui README.md for instructions on
how to set that up.

- An AWS S3 bucket. You will need to have:
    - The bucket name
    - AWS Access Key
    - AWS Secret Key
    - Whether you use your root key or an IAM profile is up to you. As long as
    you have provide those keys and they allow read and write to the bucket.


## Steps

- **Add `lando-ui.test` to your hosts file. Map it to localhost or your ip
address of the machine running docker**. You cannot access Lando UI via
any other hostname. Do not skip this step and wonder why lando-ui is giving you
a 404 page. You may access all the other services via localhost or IP.
    - lando-api: localhost:8888
    - hgweb: localhost:8101

- Run `docker network create lando`. This will create a unified network for
all the services so we can connect to them by their service name.

- Create a `docker-compose.override.yml` inside the lando-ui repo. Add:
```
version: '2'
services:
  lando-ui:
    environment:
      - LANDO_API_URL=http://lando-api:8888
      - OIDC_DOMAIN=<your auth0 domain, e.g. account.auth0.com>
      - OIDC_CLIENT_ID=<your auth0 client id for lando-ui>
      - OIDC_CLIENT_SECRET=<your auth0 client secret for lando-ui>
      - LANDO_API_OIDC_IDENTIFIER=<your auth0 api identifiier for lando-api>
networks:
  default:
    external:
      name: lando
```

- Create a `docker-compose.override.yml` inside the lando-api repo. Add:
```
version: '2'
services:
  lando-api:
    environment:
      - PATCH_BUCKET_NAME=<your aws patch bucket name>
      - AWS_ACCESS_KEY=<your aws access key>
      - AWS_SECRET_KEY=<your aws secret key>
      - PHABRICATOR_UNPRIVILEGED_API_KEY=<your phabricator-dev api key>
      - TRANSPLANT_URL=http://autoland.transplant-api:8000
      - OIDC_IDENTIFIER=<your auth0 api identifiier for lando-api>
      - OIDC_DOMAIN=<your auth0 domain>
      - LOCALDEV_MOCK_AUTH0_USER=<'default' (no quotes) or another option if you're familar with this>
      - TRANSPLANT_USERNAME=autoland
      - TRANSPLANT_PASSWORD=autoland
      - TRANSPLANT_API_KEY=secret
      - PINGBACK_HOST_URL=http://lando-api
networks:
  default:
    external:
      name: lando
```

- Create a `docker-compose.override.yml` inside the conduit-autoland-demo repo. Add:
```
version: '2'

services:
    autoland.transplant-init:
        environment:
            TREESTATUS_URL: "http://treestatus:${PORT}/%s"
            LANDO_HOST: lando-api
            LANDO_API_KEY: secret
            LANDO_BUCKET: <your aws patch bucket name>
            LANDO_AWS_KEY: <your aws access key>
            LANDO_AWS_SECRET: <your aws secret key>

    autoland.transplant-api:
        environment:
            TREESTATUS_URL: "http://treestatus:${PORT}/%s"
            LANDO_HOST: lando-api
            LANDO_API_KEY: secret
            LANDO_BUCKET: <your aws patch bucket name>
            LANDO_AWS_KEY: <your aws access key>
            LANDO_AWS_SECRET: <your aws secret key>

    autoland.transplant-daemon:
        environment:
            TREESTATUS_URL: "http://treestatus:${PORT}/%s"
            LANDO_HOST: lando-api
            LANDO_API_KEY: secret
            LANDO_BUCKET: <your aws patch bucket name>
            LANDO_AWS_KEY: <your aws access key>
            LANDO_AWS_SECRET: <your aws secret key>

networks:
  default:
    external:
      name: lando
```

- Run `docker-compose up -d --force-recreate` for all 3 repos. `-d` starts the
 services in the background. You can omit this or use `docker-compose logs -f`
 to look at the containers output.

- Go to the conduit-autoland-demo repo and:
    - Run `./clone-repo.py`. There is now a `test-repo` directory with the cloned
    repo.
    - Inside the repo add the following .arcconfig file:
    ```
    {
        "phabricator.uri" : "https://phabricator-dev.allizom.org/",
        "repository.callsign": "LOCALDEV"
    }
    ```
    - Run `arc install-certificate` (inside this test-repo) and enter your
    phabricator-DEV cli key.
    - You can use the .arcconfig file you added as your first commit. Then you
       can run `arc diff` to submit it to phabricator-dev.

- Stop only the lando-api repo with `docker-compose stop` or Ctrl+C.

- Go to the lando-api repo and run `invoke upgrade`.

- Run `docker-compose up` again for lando-api.

- Visit your revision at http://lando-ui.test:7777/revisions/DXXX

- Make sure you are logged in with Auth0 (you can use your Moz account via Google)

- Click land

- View hgweb, your revision should have been landed.
