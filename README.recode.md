## ReCODE v0.1
This represents the first major version of ReCODE Chat that uses a fork of OWUI.

## Build
ReCODE Chat has its own docker compose file: [docker-compose.recode.yaml](./docker-compose.recode.yaml).

### To Bring the Container Up
To build the container and bring it up, run:
```shell
docker-compose -f docker-compose.recode.yaml up
```

This will do the following:
- Build the ReCODE Chat OWUI container
- Pull and bring up all of the other containers and connect them together in the local docker network
- Run the [custom_start.sh](./custom_start.sh) entrypoint within the RC OWUI container, which calls [custom_start.py](./custom_start.py). This upserts all the ReCODE knowledge into the Qdrant DB.
- Deploy the application on your `localhost:8080`


### Take Down the Container
```shell
docker-compose -f docker-compose.recode.yaml down
```

## Enable / Disable Usage Limits
### Backend
ENABLE_USAGE_LIMITS: If `true`, pricing based usage limitation is enabled. See these in [main.py](./backend/open_webui/main.py):
- `ENABLE_USAGE_LIMITS`
- `check_usage_limits`
- `get_user_message_usage`

### Frontend
Set `enableUsageLimits = true` in [./src/lib/components/layout/Sidebar/UserMenu.svelte](./src/lib/components/layout/Sidebar/UserMenu.svelte).

## ReCODE Customizations
This fork includes several customizations specific to ReCODE:

*   **Configuration:** Specific configurations are managed through:
    *   [`recode_config.json`](./recode_config.json)
    *   [`recode_functions.json`](./recode_functions.json)
    *   [`recode_models.json`](./recode_models.json)
    *   [`recode_prompts.json`](./recode_prompts.json)
*   **Knowledge Base:** Custom knowledge sources for the Retrieval-Augmented Generation (RAG) system are stored in [`recode_knowledge/`](./recode_knowledge/). The `custom_start.py` script ingests this data into the Qdrant vector database during startup.
    *   The script looks for `.json` files in `recode_knowledge/`, assuming they contain text chunks, pre-computed embeddings, and metadata.
    *   It registers these files and associated knowledge collections in the OpenWebUI database.
    *   It then uses the [`QdrantClient`](./backend/open_webui/apps/retrieval/vector/dbs/qdrant.py) to populate Qdrant collections (named `open_webui_file-<knowledge_id>`) with the data from these JSON files.
*   **System Prompts:** Tailored system prompts for different modes (e.g., Cardiology, Electrophysiology) are located in [`recode_system_prompts/`](./recode_system_prompts/). These are also loaded by `custom_start.py`.
*   **Custom Functions/Tools:** Integration with external tools or APIs is defined in [`recode_functions/`](./recode_functions/). These are loaded by `custom_start.py` from definitions in `recode_functions.json`.
    *   Example: [`recode-electrophysiology-azure.py`](./recode_functions/recode-electrophysiology-azure.py) defines a pipe that routes requests to a specific Azure OpenAI deployment, configured via environment variables (e.g., `AZURE_OPENAI_ENDPOINT_GPT`, `AZURE_OPENAI_API_KEY_GPT`). This allows certain models to leverage Azure's service.
*   **Branding:** Includes ReCODE specific branding elements like [`recode_tri_logo.jpg`](./recode_tri_logo.jpg) and updates to `favicon.png`. Font files (`Bitter`) have also been added.

## Other Backend Modifications
Beyond the Usage Limits feature, other backend changes include:

*   **RAG System:** Updates to the document retrieval pipeline ([`backend/open_webui/apps/retrieval/`](./backend/open_webui/apps/retrieval/)), including the integration of [Qdrant](./backend/open_webui/apps/retrieval/vector/dbs/qdrant.py) as a vector database option.
    *   The `QdrantClient` class provides async methods for interacting with Qdrant (CRUD operations, search).
    *   It handles mapping between OpenWebUI data structures and Qdrant points/payloads.
    *   The `custom_start.py` script utilizes this client to ingest ReCODE-specific knowledge vectors on startup.
*   **Database:** Migrations ([`backend/open_webui/apps/webui/internal/migrations/`](./backend/open_webui/apps/webui/internal/migrations/)) and model updates ([`backend/open_webui/apps/webui/models/`](./backend/open_webui/apps/webui/models/)) have been applied. These include schema changes for usage limits (`billing.py`) and potentially other adjustments.
*   **Configuration:** Core configuration files ([`config.py`](./backend/open_webui/config.py), [`env.py`](./backend/open_webui/env.py)) have been modified. Check these files and potentially `.env.example` in the upstream repository for new environment variables (e.g., those related to Qdrant or Azure OpenAI).
*   **Dependencies:** Backend dependencies updated in [`backend/requirements.txt`](./backend/requirements.txt), likely adding `qdrant-client`.

## Frontend Modifications
User interface and experience changes include:

*   **Usage Limit Display:** A progress ring component ([`UsageProgressRing.svelte`](./src/lib/components/chat/MessageInput/UsageProgressRing.svelte)) visually represents usage limits.
*   **General UI/UX:** Various components like chat interface, navigation, sidebars, and settings panels have been updated for improved functionality and appearance. See changes within [`src/lib/components/`](./src/lib/components/) and [`src/routes/`](./src/routes/).
*   **API Interaction:** Frontend API calls updated in [`src/lib/apis/index.ts`](./src/lib/apis/index.ts).
*   **Styling:** Global styles ([`app.css`](./src/app.css)) and application shell ([`app.html`](./src/app.html)) have been modified.