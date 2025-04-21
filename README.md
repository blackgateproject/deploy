A sorry little attempt at CI/CD, goal is to specifiy the deployment type in the command and have the expected services configured in that way, overriding any and all .env files of the child repos

Configuration is done in `.env.local` or `.env.public`

Local deployment

`docker compose up --env-file .env.local up`

Public deployment

`docker compose up --env-file .env.public up`

> [!WARNING]
> This method of deployment is independent of each child repo, /deploy needs to be in the same dir as the other repos. This is intentional in order to speed up deployment on local/public nodes
