# Synth Definition

The Synth Definition is a YAML configuration file that defines the structure and behavior of a Synth state machine system.
The entire SynthDefinition is defined: [`synth_machine/SynthDefinition.py`](./synth_machine/SynthDefinition.py)

## Top-level Fields

- `initial_memory` (optional): `Dict[str, Any]` The initial memory state of the system.
- `initial_state` (required): `str` The name of the initial state to start the conversation.
- `states` (required): `states` A list of states in the system.
- `transitions` (required): `transitions` A list of transitions between states.
- `default_model_config` (optional): `model_config` The default model configuration to use for the synth.
- `default_rag_config` (optional): `rag_config` The default RAG configuration.

## `states`

A state represents a specific point in the conversation flow.

- `name` (required): `str` The name of the state.
- `interface` (optional): `list[dict]` A list of user interfaces associated with the state.
  - `componentName` (required): `str` The name of the UI component.
  - `key` (required): `str` A unique identifier for the interface.
  - `ui_params` (optional): `dict[str, Any]` Additional parameters for the UI component.

## `transitions`

A transition defines the movement between states based on triggers and conditions.

- `after` (optional): `str` The trigger to wait for before transitioning to the next state.
- `default` (optional): `str` Indicates if this is the default transition.
- `dest` (required): `str` The destination state to transition to.
- `inputs` (optional): `List[dict]` A list of inputs required for the transition.
  - `description` (optional): `str` A description of the input.
  - `examples` (optional): `List[str]` Example values for the input.
  - `key` (required): `str` A unique identifier for the input.
  - `schema` (optional): `JsonSchema` The schema definition for the input.
  - `ui_params` (optional): `dict[str, Any]` Additional parameters for the input UI.
  - `ui_type` (optional): `string` The type of UI element for the input.
- `outputs` (optional): `List[dict]` A list of outputs produced by the transition.
  - `append` (optional): `List[str]` A list of memory keys to append to the output.
  - `input_name_map` (optional): `dict[str, str]` A mapping of input names to output keys for use in tools.
  - `key` (required): `str` A unique identifier for the output.
  - `model_config` (optional): `model_config` The model configuration to use for the output.
  - `prompt` (optional): `str` The prompt to generate the output.
  - `reset` (optional): `bool` Indicates if the output should reset the memory state.
  - `schema` (optional): `JsonSchema` The schema definition for the output.
  - `system_prompt` (optional): `str` The system prompt to use for the output.
  - `tool` (optional): `str` The tool to use for generating the output.
  - `loop` (optional): `dict` A loop configuration for generating multiple outputs.
    - `matrix` (required): `List[str]` A list of dictionaries representing the loop iterations.
- `source` (required): `str` The source state of the transition.
- `trigger` (required): `str` The trigger that initiates the transition.
- `model_config` (optional): `model_config` The model configuration to use for the transition.

## `model_config`
- `executor` (optional - default: "togetherai"): `str` The LLM provider to use
- `llm_name` (optional - default: "mistralai/Mixtral-8x7B-Instruct-v0.1"): `str` The LLM to use.
- `max_tokens` (optional - default: 1024): `int` The maximum number of tokens in a generated response
- `temperature` (optional - default: 0.8): `float` The LLM temperature
- `stop` (optional): `List[str]` List of stop sequences to stop generation 
**Anthropic exucutor only**
- `assistant_partial` (optional): `str` AI Assistant partial response    
- `partial_input` : `str` Override for any input token difference required between `assistant_partial` and the continued generated response
- `tool_use` (optional - default: false): `bool` To use anthropic model tool use
- `tool_options` (optional) : `List[dict]` Potential tools defined as a list of `JSONSchema`. If `tool_use : true` and `tool_options` not set, then tool_option will be the output `schema`.   

## Validation

The Synth Definition includes validation checks to ensure the consistency and correctness of the configuration:

- The `initial_state` must be a valid state name defined in the `states` list.
- If a transition has an `after` value, it must be a valid trigger defined in the `transitions` list.
- If a transition output has a `prompt` or `system_prompt`, it must also have a `schema` defined.
