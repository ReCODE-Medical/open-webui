import logging
from qdrant_client import AsyncQdrantClient, QdrantClient as SyncQdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams
from typing import Optional, Any

from open_webui.apps.retrieval.vector.main import VectorItem, SearchResult, GetResult
from open_webui.config import QDRANT_HOST, QDRANT_PORT
from open_webui.env import SRC_LOG_LEVELS

log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["RAG"])

class QdrantClient:
    def __init__(self):
        self.collection_prefix = "open_webui"
        self.async_client = AsyncQdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

    def _convert_to_get_result(self, result: list[models.Record]) -> GetResult:
        ids = []
        documents = []
        metadatas = []

        for record in result:
            ids.append(record.id)
            documents.append(record.payload.get('text', ''))
            metadatas.append(record.payload.get('metadata', {}))

        log.info(f"Get result: ids={ids[:5]}..., documents={documents[:5]}..., metadatas={metadatas[:5]}...")

        return GetResult(
            **{
                "ids": [ids],
                "documents": [documents],
                "metadatas": [metadatas],
            }
        )

    def _convert_to_search_result(self, result: list[list[models.ScoredPoint]]) -> SearchResult:
        ids = []
        distances = []
        documents = []
        metadatas = []

        for match_group in result:
            _ids = []
            _distances = []
            _documents = []
            _metadatas = []

            for item in match_group:
                _ids.append(item.id)
                _distances.append(item.score)
                _documents.append(item.payload.get('text', ''))
                _metadatas.append(item.payload.get('metadata', {}))
            
            ids.append(_ids)
            distances.append(_distances)
            documents.append(_documents)
            metadatas.append(_metadatas)

        log.info(f"Search result: ids={ids[:5]}..., distances={distances[:5]}..., documents={documents[:5]}..., metadatas={metadatas[:5]}...")

        return SearchResult(
            ids=ids,
            distances=distances,
            documents=documents,
            metadatas=metadatas
        )
    
    def _get_collection_name(self, collection_name: str) -> str:
        collection_name = collection_name.replace("-", "_")
        return f"{self.collection_prefix}_{collection_name}"

    async def has_collection(self, collection_name: str) -> bool:
        '''Check if the collection exists'''
        log.info(f"Checking if collection exists: {collection_name}")
        collection_name = self._get_collection_name(collection_name)
        return await self.async_client.collection_exists(collection_name=collection_name)

    async def delete_collection(self, collection_name: str):
        '''Delete the collection'''
        log.info(f"Deleting collection: {collection_name}")
        collection_name = self._get_collection_name(collection_name)
        return await self.async_client.delete_collection(collection_name=collection_name)

    async def search(self, collection_name: str, vectors: list[list[float]], limit: int) -> Optional[SearchResult]:
        '''Search for the nearest neighbor items based on the vectors'''
        log.info(f"Searching for qdrant againt {len(vectors)} query vectors")
        
        # Check if the collection exists
        if not await self.has_collection(collection_name):
            log.info(f"Collection {collection_name} does not exist")
            return None
        
        collection_name = self._get_collection_name(collection_name)
        results = []
        
        for vector in vectors:
            result = await self.async_client.search(
                collection_name=collection_name,
                query_vector=vector,
                limit=limit
            )
            results.append(result)

        log.info(f"Search results: {results}")
        return self._convert_to_search_result(results)

    async def query(self, collection_name: str, filter: dict[str, Any], limit: Optional[int] = None) -> Optional[GetResult]:
        '''
        Query the items from the collection based on the filter
        To filter from a nested value like metadata, do `key="diet[].food"`.
        '''
        log.info(f"Querying qdrant with filter: {filter}")
        
        # Check if the collection exists
        if not await self.has_collection(collection_name):
            log.info(f"Collection {collection_name} does not exist")
            return None
        
        collection_name = self._get_collection_name(collection_name)
        qdrant_filter = models.Filter(
            must=[
                models.FieldCondition(
                    key=f"metadata.{key}",
                    match=models.MatchValue(value=value)
                ) for key, value in filter.items()
            ]
        )
        result = await self.async_client.scroll(
            collection_name=collection_name,
            scroll_filter=qdrant_filter,
            limit=limit or 10000  # Qdrant default limit
        )

        log.info(f"Query result: {result}")
        return self._convert_to_get_result(result[0])

    async def get(self, collection_name: str) -> Optional[GetResult]:
        '''Get all items from the collection'''
        log.info(f"Getting all items from collection: {collection_name}")
        collection_name = self._get_collection_name(collection_name)
        result = await self.async_client.scroll(
            collection_name=collection_name,
            limit=10000  # Adjust as needed
        )
        log.info(f"Got {len(result)} results")
        return self._convert_to_get_result(result[0])

    async def insert(self, collection_name: str, items: list[VectorItem]):
        '''Insert items into the collection and create the collection if it doesn't exist'''
        log.info(f"Inserting {len(items)} items into collection: {collection_name}")
        collection_name = self._get_collection_name(collection_name)
        
        # Convert VectorItems to dicts
        processed_items = []
        for item in items:
            if isinstance(item, VectorItem):
                processed_items.append(item.model_dump())
            else:
                processed_items.append(item)
        items = processed_items
        
        if not await self.has_collection(collection_name):
            await self.async_client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=len(items[0]["vector"]), distance=Distance.COSINE)
            )
        
        # Create the points to insert.
        points = []
        for item in items:
            points.append(models.PointStruct(
                id=item["id"],
                vector=item["vector"],
                payload={'text': item["text"], 'metadata': item["metadata"]}
            ))

        # Insert the points in batches.
        batch_size = 100
        for i in range(0, len(points), batch_size):
            batch = points[i:i+batch_size]
            await self.async_client.upsert(
                collection_name=collection_name,
                points=batch
            )

    async def upsert(self, collection_name: str, items: list[VectorItem]):
        # In Qdrant, insert and upsert are the same operation
        await self.insert(collection_name, items)

    async def delete(self, collection_name: str, ids: Optional[list[str]] = None, filter: Optional[dict[str, Any]] = None):
        log.info(f"Deleting items from collection: {collection_name}")
        collection_name = self._get_collection_name(collection_name)
        if ids:
            await self.async_client.delete(collection_name=collection_name, points_selector=models.PointIdsList(points=ids))
        elif filter:
            qdrant_filter = models.Filter(
                must=[
                    models.FieldCondition(
                        key=f"metadata.{key}",
                        match=models.MatchValue(value=value)
                    ) for key, value in filter.items()
                ]
            )
            await self.async_client.delete(collection_name=collection_name, points_selector=models.FilterSelector(filter=qdrant_filter))

    async def reset(self):
        '''Delete all collections with the prefix'''
        log.info(f"Resetting all collections with prefix: {self.collection_prefix}")
        collections = await self.async_client.get_collections()
        for collection in collections.collections:
            if collection.name.startswith(self.collection_prefix):
                await self.async_client.delete_collection(collection_name=collection.name)
