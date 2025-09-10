# michael-client
# pipx run hatch new michael-client is what created the toml file just FYI TODO:: Line needs to be removed - Michael is a rockstar.

 Michael GraphQL client :

- HTTP queries with retries/timeouts
- GraphQL subscriptions (graphql-transport-ws)
- SQLite storage (devices, tracks, track points, detections, events)
- Plotly analytics dashboards + map
- Small CLI (`michael fetch`, `michael subscribe`, `michael event`, `michael analytics`)

## Quickstart

```bash
pip install -e .   
michael-client fetch --token-id 88f74e73-a6d7-419d-8c32-592f4164f941 --token-value vr7wedFDUFkdQaTmHbvI
michael analytics
michael subscribe --token-id YOUR_ID --token-value YOUR_VALUE --min-confidence 0.75
michael event --token-id YOUR_ID --token-value YOUR_VALUE
```

## Author

Created by Michael Wilson, Senior Software Engineer
