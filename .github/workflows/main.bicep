param REPOSITORY_OWNER string

@secure()
param READ_PACKAGES_PAT string

@secure()
param DISCORD_TOKEN string
@secure()
param DISCORD_CHANNEL_ID string
@secure()
param DISCORD_REQUEST_COMMAND_NAME string

@secure()
param AZURE_RESOURCE_GROUP string
@secure()
param AZURE_CONTAINER_NAME string
@secure()
param AZURE_SUBSCRIPTION_ID string
@secure()
param AZURE_TENANT_ID string
@secure()
param AZURE_CLIENT_ID string
@secure()
param AZURE_CLIENT_SECRET string

param LOCATION string = resourceGroup().location

resource containerGroup 'Microsoft.ContainerInstance/containerGroups@2021-03-01' = {
  name: 'discord-music-bot'
  location: LOCATION
  properties: {
    sku: 'Standard'
    containers: [
      {
          name: 'discord-music-bot'
          properties: {
              image: 'ghcr.io/${REPOSITORY_OWNER}/discord-music-bot:latest'
              ports: []
              environmentVariables: [
                  {
                    name: 'DISCORD_TOKEN'
                    secureValue: DISCORD_TOKEN
                  }
                  {
                    name: 'DISCORD_CHANNEL_ID'
                    secureValue: DISCORD_CHANNEL_ID
                  }
                  {
                    name: 'DISCORD_REQUEST_COMMAND_NAME'
                    secureValue: DISCORD_REQUEST_COMMAND_NAME
                  }
                  {
                    name: 'AZURE_RESOURCE_GROUP'
                    secureValue: AZURE_RESOURCE_GROUP
                  }
                  {
                    name: 'AZURE_CONTAINER_NAME'
                    secureValue: AZURE_CONTAINER_NAME
                  }
                  {
                    name: 'AZURE_SUBSCRIPTION_ID'
                    secureValue: AZURE_SUBSCRIPTION_ID
                  }
                  {
                    name: 'AZURE_TENANT_ID'
                    secureValue: AZURE_TENANT_ID
                  }
                  {
                    name: 'AZURE_CLIENT_ID'
                    secureValue: AZURE_CLIENT_ID
                  }
                  {
                    name: 'AZURE_CLIENT_SECRET'
                    secureValue: AZURE_CLIENT_SECRET
                  }
              ]
              resources: {
                  requests: {
                      memoryInGB: json('0.5')
                      cpu: 1
                  }
              }
          }
      }
    ]
    initContainers: []
    imageRegistryCredentials: [
        {
            server: 'ghcr.io'
            username: REPOSITORY_OWNER
            password: READ_PACKAGES_PAT
        }
    ]
    restartPolicy: 'Never'
    osType: 'Linux'
  }
}
