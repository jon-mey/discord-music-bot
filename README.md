A discord music bot with a join-on-demand (activator) script using the Discord Interactions API. The bot runs as an Azure Container Instance and stops automatically after a period of inactivity. The activator script runs on a Cloudflare Worker and starts the container when a user enters a slash command in Discord.

Bot based on [pawel02/music_bot](https://github.com/pawel02/music_bot), but updated to use [yt-dlp](https://github.com/yt-dlp/yt-dlp). \
Activator based on [discord/cloudflare-sample-app](https://github.com/discord/cloudflare-sample-app).