// Swagger UI 5 renders file arrays as individual inputs behind "Add string
// item". Use its component API for native multi-selection of binary arrays.
function BinaryFileArrayPlugin(system) {
  const isBinaryArray = (schema) => schema?.get("type") === "array" &&
    schema.getIn(["items", "type"]) === "string" &&
    schema.getIn(["items", "format"]) === "binary";
  return {
    wrapComponents: {
      RequestBody: (Original) => (props) => {
        const content = props.requestBody.get("content");
        const mediaType = props.contentType || content.keySeq().first();
        const properties = content.getIn([mediaType, "schema", "properties"]);
        system.React.useEffect(() => {
          // Swagger otherwise sends an empty string part for an unselected
          // optional array; FastAPI correctly rejects strings as UploadFile.
          properties?.forEach((schema, key) => {
            if (isBinaryArray(schema)) props.onChangeIncludeEmpty(key, false);
          });
        }, [properties]);
        return system.React.createElement(Original, props);
      },
      JsonSchema_array: (Original) => (props) => {
        if (!isBinaryArray(props.schema)) {
          return system.React.createElement(Original, props);
        }
        return system.React.createElement(props.getComponent("Input"), {
          type: "file",
          multiple: true,
          "aria-label": props.description,
          disabled: props.disabled,
          onChange: (event) => props.onChange(Array.from(event.target.files)),
        });
      },
    },
  };
}
