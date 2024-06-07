# Synth Machine

[![python](https://img.shields.io/badge/Python-3.12-3776AB.svg?style=flat&logo=python&logoColor=white)](https://www.python.org)
[![tests](https://github.com/HireSynth/synth_machine/actions/workflows/tests.yaml/badge.svg)](https://github.com/HireSynth/synth_machine/actions/workflows/tests.yaml)
[![pre-commit](https://github.com/HireSynth/synth_machine/actions/workflows/precommit.yaml/badge.svg)](https://github.com/HireSynth/synth_machine/actions/workflows/precommit.yaml)


**AI Agents are State Machines not DAGs**

Synth Machines lets users create and run AI agent state machines (`Synth`) by providing a `SynthDefinition` to define a structured AI workflow.  
State machines are a powerful construct as they enable a domain expert to deconstruct the problem into sets of states and transitions.  
Transitions between states can then call an LLM, tool, data process or a mixture of many outputs.  

### Installation

#### API Models
Install the package.
`pip install synth_machine[openai,togetherai,anthropic]`
or
`poetry add synth_machine[openai,togetherai,anthropic] `

Add either setup your API provider environment keys for which 

```
# You only need to set the API providers you want to use.
export OPENAI_API_KUY=secret
export ANTHROPIC_API_KEY=secret
export TOGETHER_API_KEY=secret
```

#### (soon) Local Models
`pip install synth_machine[vllm,llamacpp]`
or
`poetry add synth_machine[vllm,llamacpp]`

You will likely need to setup CUDA, VLLM or Llama.cpp for local use.

Helpful links:
- https://docs.vllm.ai/en/latest/getting_started/installation.html
- https://developer.nvidia.com/cuda-toolkit
- https://github.com/ggerganov/llama.cpp

### Define a Synth
```
agent = Synth(
    config: dict[SynthDefinition], # Synth state machine defining states, transitions and prompts.
    tools=[], # List of tools the agent will use
    memory={}, # Any existing memory to add on top of any model_config.initial_memory
    rag_runner: Optional[RAG] = None # Define a RAG integration for your agent.
    postprocess_functions = [] # Any glue code functions
    store : ObjectStore = ObjectStore(":memory:") # Any files created by tools will automatically go to you object store    

```

The `SynthDefinition` can be found in [SynthDefinition Docs](./synth_definition.md) or [synth_machine/synth_definition.py](synth_machine/synth_definition.py). The Pydantic BaseModels which make up `SynthDefinition` will be the most accurate representation of a `Synth`.  
We expect the specification to have updates between major versions. 

### Agent state and possible triggers

**At any point, you can check the current state and next triggers**
```
# Check state
agent.current_state()

# Triggers
agent.interfaces_for_available_triggers()
```


### Run a Synth


#### Batch
```
await agent.trigger(
    "[trigger_name]",
    params={
        "input_1": "hello"
    }
)

```
Batch transition calls will output any output variable generated in that transition.

### Streaming
```
await agent.streaming_trigger(
    "[trigger_name]",
    params={
        "input_1": "hello"
    }
)
```

Streaming responses yield any of the following events:
```
class YieldTasks(StrEnum):
    CHUNK = "CHUNK"
    MODEL_CONFIG = "MODEL_CONFIG"
    SET_MEMORY = "SET_MEMORY"
    SET_ACTIVE_OUTPUT = "SET_ACTIVE_OUTPUT"

```

- `CHUNK` : LLM generations are sent by chunks one token at a time.
- `MODEL_CONFIG` : Yields which executor is currently being used for any provider specific frontend interfaces.
- `SET_MEMORP` : Sends events setting new memory variables
- `SET_ACTIVE_OUTPUT` : Yields the current transition output trigger.

This lets users experiment using `trigger` and then integrate to real time stream LLM generations to users using Server Side Events (SSE) and `trigger_streaming`.

### LLMs

We offer multiple executors to generate local or API driven LLM chat completions.

#### API Models
- `openai` : https://openai.com/api/pricing/
- `togetherai` : https://docs.together.ai/docs/inference-models
- `anthropic` : https://docs.anthropic.com/en/docs/models-overview
- (soon) `google` : https://cloud.google.com/vertex-ai/generative-ai/docs/multimodal/overview

#### Local (soon)
- `VLLM` : https://github.com/vllm-project/vllm
- `Llama-CPP` : https://github.com/ggerganov/llama.cpp

#### `Model Config`
You can specify the provider and model in either `default-model-config` and the synth base or `model_config` on transition output.

```
ModelConfig:
...
executor: [openai|togetherai|anthropic|vllm|llamacpp]
llm_name: [model_name]

```

### Memory

Agent memory is a dictionary containing all interim variables creates in previous states and human / system inputs.

```
agent.memory
# -> {
#   "[memory_key]": [memory_value]
# }
```

### Tools

Postprocess functions should only be used for basic glue code, all major functionality should be built into Tools.

#### Tools are RestAPIs and can be added by providing a JSON API schema

Go to `"./tools/tofuTool/api.py` to view the functionality.

**Start API**
```
cd tools/tofuTool
poetry install
poetry run uvicorn api:app --port=5001 --reload

```

**Retrieve API spec**
```
curl -X GET http://localhost:5001/openapi.json > openapi_schema.json
```

**Define Tool**

You can define a Tool as such with only the name, API endpoint and tool openapi schema.
```
tofu_tool = Tool(
    name="tofu_tool",
    api_endpoint="http://localhost:5001",
    api_spec=tool_spec
)
```

### Synth Machine RAG

Retrieval augemented generation is a powerful tool to improve LLM responses by providing semantically similar examples or exerts to the material the LLM is attempting to generate.

`synth_machine` is flexibly in such that as long as you inherit from `synth_machine.RAG` and create:
- `embed(documents: List[str])` and
- `query(prompt: str, rag_config: Optional[synth_machine.RAGConfig])`

It is easy to integrate multiple providers and vector databases. Over time there will be supported and community RAG implementations across a wide variety of embeddings providers and vector databases.

#### RAG Example Qdrant & FastEmbed
The following RAG class is ideal for experimenting with local RAG setups on CPU. 
```
pip install qdrant-client, fastembed
```
**Define RAG class**
```
from synth_machine.rag import RAG
from qdrant_client import AsyncQdrantClient
from fastembed import TextEmbedding
from typing import List, Optional
from qdrant_client.models import Distance, VectorParams, PointStruct


class Qdrant(RAG):

    """
    VectorDB: Qdrant - https://github.com/qdrant/qdrant
    Embeddings: FastEmbed - https://github.com/qdrant/fastembed

    This provides fast and lightweight on-device CPU embeddings creation and 
    similarity search using Qdrant in memory.
    """
    
    def __init__(
        self,
        collection_name: str,
        embedding_model: str="BAAI/bge-small-en-v1.5",
        embedding_dimensions: int=384,
        embedding_threads: int=-1,
        qdrant_location: str=":memory:",
    ):
        self.embedding_model = TextEmbedding(
            model_name=embedding_model,
            threads=embedding_threads
        )
        self.embedding_dimensions = embedding_dimensions
        self.qdrant = AsyncQdrantClient(qdrant_location)
        self.collection_name = collection_name
    
    async def create_collection(self) -> bool:
        if await self.qdrant.collection_exists(self.collection_name):
            return True
        else:
            return await self.qdrant.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.embedding_dimensions, # maps to 'BAAI/bge-small-en-v1.5' model dimensions
                    distance=Distance.COSINE
                ) 
            )
    
    async def embed(self, documents: List[str], metadata: Optional[List[dict]]=None):
        if metadata and len(documents) != len(metadata):
            raise ValueError("documents and metadata must be the same length")
        embedding_list = list(
            self.embedding_model.embed(documents)
        )
        upsert_response = await self.qdrant.upsert(
            collection_name=self.collection_name,
            points=[
                PointStruct(
                    id=i,
                    vector=list(vector),
                    payload=metadata[i]
                )
                for i, vector in enumerate(embedding_list)
            ]
        )
        return upsert_response.status
        

    async def query(self, prompt: str, rag_config: RAGConfig) -> List[dict]:
        embedding = next(self.embedding_model.embed([prompt]))
            
        similar_responses = await self.qdrant.search(
            collection_name=self.collection_name,
            query_vector=embedding,
            limit=rag_config.n
        )
        return [
            point.payload for point in similar_responses
        ]
```

**Now initiate the Qdrant class and provide when defining `Synth`.**

```
qdrant = Qdrant(collection_name="tofu_examples")
await qdrant.create_collection()

agent = Synth(
    ...
    rag_runner=Qdrant
)
```

#### **Store**  

Tools can return a variety of different objects. Any file created by a tool will automatically go to your `agent.store`.
We use [ObjectStore](https://pypi.org/project/object-store-python/) for file storage, with `ObjectStore(":memory:")`as the default.

To retrieve a file: `agent.store.get(file_name)`

ObjectStore allowing easy integration to:
- Local file store
- S3
- GCS
- Azure

#### Example GCS object store
```
from synth_machine.machine import ObjectStore

agent = Agent(
    ...
    store=ObjectStore("gs://[bucket_name]/[prefix]))
)
```

### User Defined Functions

Any custom functionality can be defined as a user defined function (UDF).  
These take `Synth.memory`as input and allows you to run custom functionality as part of the `synth-machine`.  

```
# Define postprocess function

from synth_machine.user_defined_functions import udf

@udf
def abc_postprocesss(memory):
    ...
    return memory["variable_key"]

agent = Synth(
  ...
  user_defined_functions = {
    "abc": abc_postprocess
  }
)
```
 
#### Example UDF Transition Config
```
...
- key: trigger_udf
  inputs:
    - key: variable_key
  outputs:
    - key: example_udf
      udf: abc
```

**Note:** Any non trivial functionality should be a tool and not UDF.  