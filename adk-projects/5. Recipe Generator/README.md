# Recipe Bot using Google ADK and Spoonacular API

This project demonstrates how to integrate an external API using **OpenAPI specification** and Google's **Agent Development Kit (ADK)**. The goal was to create an agent that can fetch and suggest recipes — like spaghetti carbonara — from the **Spoonacular API** using OpenAPI tooling.

---

## 🚀 Objective

The initial aim was to:

- Use **OpenAPI Spec** to define available endpoints of the Spoonacular API.
- Auto-generate tools via `OpenAPIToolset` from the spec.
- Register these tools with an `Agent` so it could autonomously choose and call them via `Runner`.

---

## 🧩 What Worked

✅ Auto-generation of tools worked using:

```python
recipe_toolset = OpenAPIToolset(spec_str=openapi_spec_string, spec_str_type="json")
generated_tools_list = recipe_toolset.get_tools()
```

✅ ADK’s Runner and Agent setup executed properly.

✅ Agent could recognize and attempt to call `search_recipes`, `get_recipe_info`, etc., from the OpenAPI spec.

---

## ❌ What Didn't Work

🔐 **Authentication Handling via OpenAPI spec was not intuitive or supported cleanly.**

While the Spoonacular API requires `apiKey` to be passed as a query param, the `OpenAPIToolset` did **not** allow injecting this key easily via the `auth=` argument. Trying:

```python
OpenAPIToolset(..., auth={"apiKey": "..."})
```

led to:

```
TypeError: OpenAPIToolset.__init__() got an unexpected keyword argument 'auth'
```

📛 Even patching the tool execution method using `.execute` or `_execute` (as documented in community examples) did not resolve the problem cleanly. Attempts to inject the API key through tool context state or by monkey-patching failed or broke expected internal behaviors.

---

## 🧠 Insight from Google's Own Examples

Looking into Google ADK examples like their **travel concierge/Places API**, it turns out **they don’t rely on OpenAPI tooling for external APIs either**.

Instead, they:

- Use plain Python `requests.get(...)`
- Build URLs and inject the API key manually
- Wrap this logic in a simple Python service class (e.g., `PlacesService`)
- Then expose this as a `FunctionTool` that the ADK agent can invoke

Example:

```python
params = {
  "input": query,
  "inputtype": "textquery",
  "fields": "place_id,formatted_address",
  "key": os.getenv("GOOGLE_PLACES_API_KEY")
}
response = requests.get("https://maps.googleapis.com/maps/api/place/findplacefromtext/json", params=params)
```

---

## 💡 Conclusion

While **OpenAPI Spec parsing works for tool generation**, it’s currently **not ideal for real-world APIs requiring API keys or more complex authentication** — especially when the auth scheme is embedded as a query parameter.

### ✅ Recommended Approach

For real external APIs like Spoonacular, you should:

1. Use `requests.get()` or `httpx` to call the API directly
2. Manually append the API key
3. Wrap the logic in a Python class (e.g., `SpoonacularService`)
4. Expose the logic as a `FunctionTool` to your ADK agent

This gives you more control, easier debugging, and a production-grade solution without hacking internal tool behavior.

---

## 🔧 To Do

- [ ] Build `SpoonacularService` class with manual API fetches
- [ ] Wrap service methods with `FunctionTool`
- [ ] Register with the ADK agent
- [ ] Replace OpenAPI-based tools entirely for this case

---

## 🙏 Credits

- Built using [Google Agent Development Kit (ADK)](https://github.com/google-deepmind/deepmind-research/tree/master/adk)
- Spoonacular API documentation: [spoonacular.com/food-api](https://spoonacular.com/food-api)
