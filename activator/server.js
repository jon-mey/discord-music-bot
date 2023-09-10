/**
 * The core server that runs on a Cloudflare worker.
 */

import { Router } from 'itty-router';
import {
  InteractionResponseType,
  InteractionType,
  verifyKey,
} from 'discord-interactions';

class JsonResponse extends Response {
  constructor(body, init) {
    const jsonBody = JSON.stringify(body);
    init = init || {
      headers: {
        'content-type': 'application/json;charset=UTF-8',
      },
    };
    super(jsonBody, init);
  }
}

const router = Router();

/**
 * Main route for all requests sent from Discord.  All incoming messages will
 * include a JSON payload described here:
 * https://discord.com/developers/docs/interactions/receiving-and-responding#interaction-object
 */
router.post('/', async (request, env) => {
  const { isValid, interaction } = await server.verifyDiscordRequest(
    request,
    env,
  );
  if (!isValid || !interaction) {
    return new Response('Bad request signature.', { status: 401 });
  }

  if (interaction.type === InteractionType.PING) {
    // The `PING` message is used during the initial webhook handshake, and is
    // required to configure the webhook in the developer portal.
    return new JsonResponse({
      type: InteractionResponseType.PONG,
    });
  }

  if (interaction.type === InteractionType.APPLICATION_COMMAND) {
    switch (interaction.data.name.toLowerCase()) {
      case `${env.DISCORD_REQUEST_COMMAND_NAME}`: {
        var token = await env.KV_DISCORD_MUSIC_BOT_ACTIVATOR.get("TOKEN");
        if (token === null) {
          console.log('Refreshing token');

          const tokenResponse = await fetch(`https://login.microsoftonline.com/${env.AZURE_TENANT_ID}/oauth2/token`, {
            headers: {
              'content-type': 'application/x-www-form-urlencoded'
            },
            body: new URLSearchParams({
              'grant_type': 'client_credentials',
              'client_id': `${env.AZURE_CLIENT_ID}`,
              'client_secret': `${env.AZURE_CLIENT_SECRET}`,
              'resource': 'https://management.azure.com/'
            }),
            method: 'POST',
          });

          const tokenJson = await tokenResponse.json();
          token = tokenJson.access_token;

          await env.KV_DISCORD_MUSIC_BOT_ACTIVATOR.put("TOKEN", token, {
              expiration: tokenJson.expires_on,
          });
        } else {
          console.log('Using cached token');
        }

        const containerStartUrl = `https://management.azure.com/subscriptions/${env.AZURE_SUBSCRIPTION_ID}/resourceGroups/${env.AZURE_RESOURCE_GROUP}/providers/Microsoft.ContainerInstance/containerGroups/${env.AZURE_CONTAINER_NAME}/start?api-version=2022-09-01`;
        const response = await fetch(containerStartUrl, {
          headers: {
            'content-type': 'application/json',
            'authorization': `bearer ${token}`,
          },
          method: 'POST',
        });

        return new JsonResponse({
          type: InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
          data: {
            content: `Start request sent, bot should join shortly (${response.status})`,
          },
        });
      }
      default:
        return new JsonResponse({ error: 'Unknown Type' }, { status: 400 });
    }
  }

  console.error('Unknown Type');
  return new JsonResponse({ error: 'Unknown Type' }, { status: 400 });
});

router.all('*', () => new Response('Not Found.', { status: 404 }));

async function verifyDiscordRequest(request, env) {
  const signature = request.headers.get('x-signature-ed25519');
  const timestamp = request.headers.get('x-signature-timestamp');
  const body = await request.text();
  const isValidRequest =
    signature &&
    timestamp &&
    verifyKey(body, signature, timestamp, env.DISCORD_PUBLIC_KEY);
  if (!isValidRequest) {
    return { isValid: false };
  }

  return { interaction: JSON.parse(body), isValid: true };
}

const server = {
  verifyDiscordRequest: verifyDiscordRequest,
  fetch: async function (request, env) {
    return router.handle(request, env);
  },
};

export default server;
